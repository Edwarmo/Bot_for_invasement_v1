"""
🎯 ORQUESTADOR PRINCIPAL - SISTEMA DSS LIMPIO
Responsabilidad: Controlador central con threading y LM Studio real
"""

import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Agregar paths de las capas
sys.path.append(os.path.join(os.path.dirname(__file__), 'CAPA 1'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'CAPA 2'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'CAPA 3'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'CAPA 6'))

# Importar componentes
from market_data_stream import MarketDataStream, MarketTick
from technical_analyzer import TechnicalAnalyzer, AIDataPacket
from ai_inference_engine import LMStudioClient, AIResponse
from alert_interface import AlertManager, AlertData
from trade_journal import TradeJournal

class TradingDSSOrchestrator:
    """Orquestador principal del sistema DSS limpio"""
    
    def __init__(self, symbols: List[str] = None, capture_region: tuple = None):
        self.symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY"]
        self.capture_region = capture_region or (1280, 690, 260, 120)  # Default region
        
        # Inicializar componentes por capa
        self.data_streams: Dict[str, MarketDataStream] = {}
        self.technical_analyzer = TechnicalAnalyzer()
        self.ai_client = LMStudioClient()
        self.alert_manager = AlertManager()
        self.experiment_logger = TradeJournal()  # 📊 Logger científico
        
        # Estado del sistema
        self.running = False
        self.analysis_thread = None
        self.ai_connected = False
        
        # Configurar callbacks
        self.alert_manager.set_decision_callback(self._on_user_decision)
        
        print(f"🎯 DSS Orquestador inicializado para símbolos: {self.symbols}")
        print(f"📍 Región de captura: {self.capture_region}")
    
    async def start_system(self):
        """Inicia el sistema DSS completo"""
        if self.running:
            print("⚠️ Sistema ya está ejecutándose")
            return
        
        print("🚀 INICIANDO SISTEMA DSS LIMPIO")
        print("=" * 50)
        
        # Test conexión LM Studio
        self.ai_connected = await self.ai_client.test_connection()
        
        self.running = True
        
        # Inicializar streams de datos
        for symbol in self.symbols:
            stream = MarketDataStream(symbol, search_region=self.capture_region)
            stream.add_callback(self._on_new_tick)
            stream.start_stream()
            self.data_streams[symbol] = stream
        
        # Iniciar hilo de análisis
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        
        print("✅ Sistema DSS iniciado correctamente")
        print(f"🤖 LM Studio: {'✅ CONECTADO' if self.ai_connected else '❌ DESCONECTADO'}")
        print("📊 Streams de datos activos")
        print("🔬 Analizador técnico en línea")
        print("🖥️ Interfaz de alertas lista")
        print("=" * 50)
    
    async def stop_system(self):
        """Detiene el sistema DSS"""
        print("🛑 Deteniendo sistema DSS...")
        
        self.running = False
        
        # Detener streams de datos
        for stream in self.data_streams.values():
            stream.stop_stream()
        
        # Cerrar cliente IA
        await self.ai_client.close()
        
        # Cerrar alertas activas
        self.alert_manager.close_all_alerts()
        
        # Esperar a que termine el hilo de análisis
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=2)
        
        print("✅ Sistema DSS detenido correctamente")
    
    def _on_new_tick(self, tick: MarketTick):
        """Callback para nuevos ticks de mercado"""
        pass
    
    def _analysis_loop(self):
        """Bucle principal de análisis (ejecuta en hilo separado)"""
        print("🔬 Iniciando bucle de análisis...")
        
        while self.running:
            try:
                # Analizar cada símbolo
                for symbol, stream in self.data_streams.items():
                    asyncio.run(self._analyze_symbol(symbol, stream))
                
                # Pausa entre análisis (30 segundos)
                time.sleep(30)
                
            except Exception as e:
                print(f"❌ Error en bucle de análisis: {e}")
                time.sleep(5)
    
    async def _analyze_symbol(self, symbol: str, stream: MarketDataStream):
        """Analiza un símbolo específico con Signal Gating y Weekend Mode"""
        try:
            # Obtener datos actuales
            df = stream.get_current_data()
            if df.empty or len(df) < 50:
                return
            
            # Obtener contexto de fin de semana si aplica
            weekend_context = stream.get_weekend_context()
            market_mode = weekend_context.get('market_mode', 'live')
            
            # Preparar datos según el modo
            if market_mode == 'weekend_otc':
                ai_data = self.technical_analyzer.prepare_weekend_ai_data(
                    symbol, df, weekend_context, stream.get_latest_candles(15)
                )
            else:
                ai_data = self.technical_analyzer.prepare_ai_data(
                    symbol, df, stream.get_latest_candles(15)
                )
            
            if not ai_data:
                return
            
            # 🚪 SIGNAL GATING: Verificar si vale la pena despertar la IA
            if market_mode == 'weekend_otc':
                micro_features = getattr(ai_data, 'micro_features', {})
                should_wake = self.technical_analyzer.should_wake_ai_weekend(ai_data.indicators, df, micro_features)
            else:
                should_wake = self.technical_analyzer.should_wake_ai(ai_data.indicators, df)
            
            if not should_wake:
                mode_emoji = "🏠" if market_mode == 'weekend_otc' else "💤"
                print(f"{mode_emoji} {symbol}: Mercado lateral, IA en reposo")
                return
            
            mode_emoji = "⚠️" if market_mode == 'weekend_otc' else "⚡"
            print(f"{mode_emoji} {symbol}: Condiciones interesantes detectadas, despertando IA...")
            
            # Análisis real con LM Studio
            ai_response = await self._get_ai_prediction(ai_data, weekend_context)
            if not ai_response:
                return
            
            # Si la IA genera una señal fuerte, mostrar alerta
            confidence_threshold = 65.0 if market_mode == 'weekend_otc' else 70.0
            if ai_response.confidence >= confidence_threshold:
                self._show_trading_alert(symbol, ai_response, ai_data, market_mode)
            
        except Exception as e:
            print(f"❌ Error analizando {symbol}: {e}")
    
    async def _get_ai_prediction(self, ai_data: AIDataPacket, weekend_context: Dict = None) -> Optional[AIResponse]:
        """Obtiene predicción real de LM Studio con contexto weekend"""
        if not self.ai_connected:
            return None
        
        # Preparar datos base para LM Studio
        market_data = {
            'symbol': ai_data.symbol,
            'price': ai_data.current_price,
            'rsi': ai_data.indicators.rsi,
            'ema_20': ai_data.indicators.ema_20,
            'ema_50': ai_data.indicators.ema_50,
            'bb_position': ai_data.indicators.bb_position,
            'volume_ratio': ai_data.indicators.volume_sma,
            'trend': 'UP' if ai_data.indicators.ema_20 > ai_data.indicators.ema_50 else 'DOWN'
        }
        
        # Añadir contexto de weekend si aplica
        if weekend_context and weekend_context.get('market_mode') == 'weekend_otc':
            market_data.update({
                'market_mode': 'weekend_otc',
                'data_quality': 'screen_ocr_estimated',
                'micro_features': getattr(ai_data, 'micro_features', {})
            })
        
        # Llamada real a LM Studio con memoria de errores
        return await self.ai_client.analyze_market_context_with_memory(market_data)
    
    def _show_trading_alert(self, symbol: str, ai_response: AIResponse, ai_data: AIDataPacket, market_mode: str = 'live'):
        """Muestra alerta de trading al usuario con contexto de modo"""
        # Preparar resumen con modo de mercado
        mode_prefix = "⚠️ MODO OTC | " if market_mode == 'weekend_otc' else ""
        indicators_summary = f"{mode_prefix}{ai_response.reason} | {ai_data.market_summary}"
        
        # Crear datos de alerta
        alert_data = AlertData(
            symbol=symbol,
            prediction=ai_response.action,
            confidence=ai_response.confidence,
            current_price=ai_data.current_price,
            indicators_summary=indicators_summary,
            timestamp=datetime.now()
        )
        
        # Mostrar alerta (thread-safe)
        self.alert_manager.show_alert(alert_data)
        
        mode_emoji = "🏠" if market_mode == 'weekend_otc' else "🚨"
        print(f"{mode_emoji} ALERTA: {symbol} - {ai_response.action} ({ai_response.confidence:.1f}%) - {ai_response.reason}")
    
    def _on_user_decision(self, decision: str, alert_data: AlertData):
        """Maneja las decisiones del usuario con registro científico"""
        print(f"👤 DECISIÓN USUARIO: {decision}")
        print(f"   Símbolo: {alert_data.symbol}")
        print(f"   Predicción: {alert_data.prediction}")
        print(f"   Confianza: {alert_data.confidence:.1f}%")
        print(f"   Timestamp: {alert_data.timestamp.strftime('%H:%M:%S')}")
        
        # 📊 REGISTRO CIENTÍFICO
        # Determinar market_mode y technical_trigger
        market_mode = "live"  # Por defecto, se puede mejorar con contexto
        technical_trigger = self._extract_technical_trigger(alert_data.indicators_summary)
        
        # Mapear decisión
        human_decision = "accepted" if decision == "EXECUTE" else "rejected"
        
        # Registrar señal
        experiment_id = self.experiment_logger.log_signal(
            symbol=alert_data.symbol,
            direction=alert_data.prediction.lower(),
            probability=alert_data.confidence,
            ai_validation=True,
            risk_approved=True,
            risk_score=100 - alert_data.confidence,
            user_action=human_decision,
            notes=f"Trigger: {technical_trigger} | Mode: {market_mode}"
        )
        
        print(f"📊 Experimento registrado: {experiment_id}")
    
    def _extract_technical_trigger(self, indicators_summary: str) -> str:
        """🔍 Extrae el trigger técnico principal"""
        summary_lower = indicators_summary.lower()
        
        if "rsi" in summary_lower and "oversold" in summary_lower:
            return "RSI_Oversold"
        elif "rsi" in summary_lower and "overbought" in summary_lower:
            return "RSI_Overbought"
        elif "bollinger" in summary_lower or "bb" in summary_lower:
            return "Bollinger_Break"
        elif "trend" in summary_lower:
            return "Trend_Signal"
        elif "gap" in summary_lower:
            return "Gap_Signal"
        else:
            return "Mixed_Indicators"
    
    def get_system_status(self) -> Dict:
        """Obtiene el estado actual del sistema"""
        status = {
            'running': self.running,
            'ai_connected': self.ai_connected,
            'symbols': self.symbols,
            'active_streams': len([s for s in self.data_streams.values() if s.running]),
            'active_alerts': self.alert_manager.get_active_count(),
            'buffer_status': {}
        }
        
        # Estado de buffers
        for symbol, stream in self.data_streams.items():
            status['buffer_status'][symbol] = stream.get_buffer_status()
        
        return status
    
    def print_system_status(self):
        """Imprime el estado del sistema"""
        status = self.get_system_status()
        
        print("\n📊 ESTADO DEL SISTEMA DSS")
        print("=" * 40)
        print(f"Estado: {'🟢 ACTIVO' if status['running'] else '🔴 INACTIVO'}")
        print(f"LM Studio: {'🟢 CONECTADO' if status['ai_connected'] else '🔴 DESCONECTADO'}")
        print(f"Símbolos: {', '.join(status['symbols'])}")
        print(f"Streams activos: {status['active_streams']}/{len(status['symbols'])}")
        print(f"Alertas activas: {status['active_alerts']}")
        
        print("\n📈 ESTADO DE BUFFERS:")
        for symbol, buffer_status in status['buffer_status'].items():
            usage = buffer_status['usage_percent']
            print(f"  {symbol}: {buffer_status['size']}/{buffer_status['max_size']} ({usage:.1f}%)")
        print("=" * 40)