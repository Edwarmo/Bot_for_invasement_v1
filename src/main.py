"""
🚀 DSS TRADING SYSTEM - MAIN
Sistema de Soporte a la Decisión para trading
Arquitectura modular basada en Clean Architecture
"""

import asyncio
import sys
import os
import subprocess
import traceback
import time
import re

# Agregar src al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.domain.prediction import PredictionTracker
from src.data.market_stream import DataFusionHandler
from src.services.ai_client import LMStudioClient, AIResponse
from src.services.alerts import mostrar_alerta
from src.services.indicators import calcular_indicadores_tecnicos

# 📋 CONFIGURACIÓN
CSV_PATH = "capturador/prices.csv"
SYMBOL = "EURUSD=X"
OBSERVATION_WINDOW = 45


class TradingSystem:
    """🤖 Sistema de trading principal"""
    
    def __init__(self):
        self.market_handler = DataFusionHandler()
        self.ai_client = LMStudioClient()
        self.tracker = PredictionTracker()
        self.running = False
        self.capturador_process = None
    
    def _start_price_capture(self):
        """👁️ Inicia el capturador de precios"""
        try:
            print("👁️ Iniciando capturador de precios...")
            capture_path = os.path.join(os.path.dirname(__file__), 'data', 'price_capture.py')
            # El capturador se ejecuta como script independiente
            self.capturador_process = subprocess.Popen(
                [sys.executable, '-c', 'from src.data.price_capture import PriceCaptureService; s = PriceCaptureService(); s.start_continuous_capture()'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except Exception as e:
            print(f"❌ Error iniciando capturador: {e}")
    
    async def start(self):
        """🚀 Inicia el sistema de trading"""
        print("\n" + "="*60)
        print("🚀 INICIANDO DSS TRADING SYSTEM")
        print("="*60)
        
        self._start_price_capture()
        await asyncio.sleep(4)
        
        # Verificar conexión LM Studio
        print("⏳ Esperando a LM Studio...")
        for i in range(10):
            if await self.ai_client.test_connection():
                break
            print(f"   Intento {i+1}/10 - Esperando 10s...")
            await asyncio.sleep(10)
        else:
            print("⚠️ LM Studio no disponible. Continuando...")
        
        # Contexto macro
        print("📊 Obteniendo contexto macro...")
        try:
            contexto_yahoo = self.market_handler.obtener_contexto_yahoo(SYMBOL)
            print("✅ Contexto macro cargado")
        except:
            print("⚠️ Yahoo offline - Modo visual")
            contexto_yahoo = {"trend": "NEUTRAL"}
        
        self.running = True
        try:
            while self.running:
                await self._trading_cycle()
                print("\n💤 Enfriamiento de 10s...")
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            print("\n🛑 Apagando...")
        finally:
            self.stop()
    
    async def _trading_cycle(self):
        """🔄 Ciclo principal de trading"""
        try:
            # 1. Validar predicciones
            self.tracker.validate_predictions(CSV_PATH)
            
            # 2. Observar mercado
            recent_prices = await self._monitor_market()
            
            if not recent_prices or len(recent_prices) < 5:
                print("⚠️ Sin datos suficientes. Saltando ciclo...")
                return
            
            current_price = recent_prices[-1]
            
            # 3. Contexto Yahoo
            contexto_yahoo = self.market_handler.obtener_contexto_yahoo(SYMBOL)
            df_5m = contexto_yahoo.get('df_5m')
            df_1h = contexto_yahoo.get('df_1h')
            
            # 4. Construir prompt contextual
            contexto_fusion = self.market_handler.construir_prompt_contextual(
                current_price, df_5m, df_1h, SYMBOL
            )
            
            # 5. Datos para IA
            learning_context = self.tracker.get_learning_context()
            datos_ia = {
                'symbol': SYMBOL,
                'MACRO_RIO': contexto_fusion['MACRO_RIO'],
                'MICRO_OLA': contexto_fusion['MICRO_OLA'],
                'FUSION_RESULT': contexto_fusion['FUSION_RESULT'],
                'learning_context': learning_context
            }
            
            # 6. Consultar IA
            print(f"\n🧠 Consultando IA...")
            respuesta = await self.ai_client.analizar_mercado(datos_ia)
            
            if respuesta:
                self._process_decision(respuesta, current_price)
            else:
                print("❌ Sin respuesta de IA")
            
        except Exception as e:
            print(f"❌ Error en ciclo: {e}")
            traceback.print_exc()
    
    async def _monitor_market(self, duration: int = None) -> list:
        """👁️ Observa el mercado y recopila precios"""
        duration = duration or OBSERVATION_WINDOW
        print(f"\n🕵️ Observando mercado por {duration}s...")
        
        start_time = time.time()
        collected = []
        last_price = 0
        
        while time.time() - start_time < duration:
            try:
                current = self.market_handler.leer_precio_csv(CSV_PATH)
                if current > 0 and 1.0 < current < 2.0 and current != last_price:
                    collected.append(current)
                    if len(collected) % 10 == 0:
                        sys.stdout.write(f"\r   📈 Capturas: {len(collected)} | Último: {current:.5f}")
                        sys.stdout.flush()
                    last_price = current
                await asyncio.sleep(0.1)
            except:
                await asyncio.sleep(0.1)
        
        print(f"\n✅ Datos recopilados: {len(collected)}")
        return collected
    
    def _process_decision(self, respuesta: AIResponse, current_price: float):
        """🎯 Procesa la decisión de la IA"""
        try:
            # Extraer decisión y confianza
            if hasattr(respuesta, 'decision'):
                accion = respuesta.decision.upper()
                razon = respuesta.razon
            else:
                accion = respuesta.get('decision', 'NEUTRAL').upper()
                razon = respuesta.get('razon', 'Análisis')
            
            # Extraer confianza
            confidence = 50
            if "Score:" in razon:
                match = re.search(r'Score: (\d+)%', razon)
                if match:
                    confidence = int(match.group(1))
            
            # Solo mostrar si confianza > 75%
            if confidence <= 75:
                print(f"🔇 Señal oculta: {accion} (confianza {confidence}%)")
                return
            
            # Registrar predicción
            self.tracker.log_prediction(accion, confidence, current_price, razon)
            
            # Determinar tipo de señal
            if "EXPLOSIÓN" in razon:
                expiracion = "1 MINUTO"
            elif "TENDENCIA ORDENADA" in razon:
                expiracion = "3-5 MINUTOS"
            else:
                expiracion = "3-5 MINUTOS"
            
            # Mostrar alerta
            if "CALL" in accion:
                display = "CALL (SUBE) 🚀"
            elif "PUT" in accion:
                display = "PUT (BAJA) 📉"
            else:
                print(f"🔇 Señal ocultada: {accion}")
                return
            
            print("\n" + "█"*60)
            print(f"🚀 SEÑAL: {display}")
            print(f"📊 RAZÓN: {razon}")
            print("█"*60)
            
            mostrar_alerta(display, razon, expiracion)
            
        except Exception as e:
            print(f"❌ Error procesando decisión: {e}")
    
    def stop(self):
        """🛑 Detiene el sistema"""
        self.running = False
        if self.capturador_process:
            self.capturador_process.terminate()


async def main():
    """🎯 Función principal"""
    print("🚀 INICIANDO DSS TRADING SYSTEM...")
    
    system = TradingSystem()
    
    while True:
        try:
            await system.start()
        except Exception as e:
            print(f"⚠️ Error: {e}")
            print("🔄 Reiniciando en 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Sistema detenido.")
