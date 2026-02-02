"""
🔬 CAPA DE PROCESAMIENTO - PROCESSING LAYER
Responsabilidad: Análisis técnico en tiempo real y preparación de datos para IA
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import threading
from dataclasses import dataclass

@dataclass
class TechnicalIndicators:
    """Estructura para indicadores técnicos calculados"""
    rsi: float
    ema_20: float
    ema_50: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_position: float  # Posición dentro de las bandas (0-1)
    volume_sma: float
    price_change_pct: float
    volatility: float

@dataclass
class AIDataPacket:
    """Paquete de datos optimizado para envío a IA"""
    symbol: str
    timestamp: datetime
    current_price: float
    indicators: TechnicalIndicators
    latest_candles: List[Dict]  # Últimas 15 velas OHLC
    market_summary: str  # Resumen textual del estado del mercado

class TechnicalAnalyzer:
    """Analizador técnico optimizado para procesamiento en tiempo real"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.last_analysis = None
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calcula RSI optimizado"""
        if len(prices) < period + 1:
            return 50.0
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0
    
    def calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calcula EMA optimizado"""
        if len(prices) < period:
            return float(prices.mean()) if not prices.empty else 0.0
        
        ema = prices.ewm(span=period, adjust=False).mean()
        return float(ema.iloc[-1])
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> tuple:
        """Calcula Bollinger Bands"""
        if len(prices) < period:
            mean_price = float(prices.mean()) if not prices.empty else 0.0
            return mean_price, mean_price, mean_price
        
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return (
            float(upper.iloc[-1]),
            float(sma.iloc[-1]),
            float(lower.iloc[-1])
        )
    
    def calculate_bb_position(self, current_price: float, bb_upper: float, bb_lower: float) -> float:
        """Calcula posición dentro de las Bollinger Bands (0-1)"""
        if bb_upper == bb_lower:
            return 0.5
        
        position = (current_price - bb_lower) / (bb_upper - bb_lower)
        return max(0.0, min(1.0, position))
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
        """Calcula volatilidad realizada"""
        if len(prices) < 2:
            return 0.0
        
        returns = prices.pct_change().dropna()
        if len(returns) < period:
            return float(returns.std()) if not returns.empty else 0.0
        
        volatility = returns.rolling(window=period).std()
        return float(volatility.iloc[-1]) * 100  # Convertir a porcentaje
    
    def analyze_market_data(self, df: pd.DataFrame) -> Optional[TechnicalIndicators]:
        """Analiza datos de mercado y calcula todos los indicadores"""
        with self._lock:
            try:
                if df.empty or len(df) < 20:
                    return None
                
                close_prices = df['close']
                volume = df['volume']
                
                # Calcular indicadores
                rsi = self.calculate_rsi(close_prices)
                ema_20 = self.calculate_ema(close_prices, 20)
                ema_50 = self.calculate_ema(close_prices, 50)
                
                bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(close_prices)
                bb_position = self.calculate_bb_position(close_prices.iloc[-1], bb_upper, bb_lower)
                
                volume_sma = float(volume.rolling(window=20).mean().iloc[-1]) if len(volume) >= 20 else float(volume.mean())
                
                # Cambio porcentual reciente
                if len(close_prices) >= 2:
                    price_change_pct = ((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100
                else:
                    price_change_pct = 0.0
                
                volatility = self.calculate_volatility(close_prices)
                
                indicators = TechnicalIndicators(
                    rsi=rsi,
                    ema_20=ema_20,
                    ema_50=ema_50,
                    bb_upper=bb_upper,
                    bb_middle=bb_middle,
                    bb_lower=bb_lower,
                    bb_position=bb_position,
                    volume_sma=volume_sma,
                    price_change_pct=price_change_pct,
                    volatility=volatility
                )
                
                self.last_analysis = indicators
                return indicators
                
            except Exception as e:
                print(f"Error en análisis técnico: {e}")
                return self.last_analysis
    
    def prepare_ai_data(self, symbol: str, df: pd.DataFrame, latest_candles: List[Dict]) -> Optional[AIDataPacket]:
        """Prepara datos optimizados para envío a IA externa (LM Studio)"""
        indicators = self.analyze_market_data(df)
        if not indicators:
            return None
        
        current_price = df['close'].iloc[-1] if not df.empty else 0.0
        
        # Generar resumen textual del mercado
        market_summary = self._generate_market_summary(indicators, current_price)
        
        return AIDataPacket(
            symbol=symbol,
            timestamp=datetime.now(),
            current_price=current_price,
            indicators=indicators,
            latest_candles=latest_candles[-15:],  # Solo últimas 15 velas
            market_summary=market_summary
        )
    
    def prepare_weekend_ai_data(self, symbol: str, df: pd.DataFrame, weekend_context: Dict, latest_candles: List[Dict]) -> Optional[AIDataPacket]:
        """🏠 Prepara datos para IA en modo Weekend OTC con features cuantitativas"""
        indicators = self.analyze_market_data(df)
        if not indicators:
            return None
        
        current_price = weekend_context.get('current_price', 0.0)
        friday_close = weekend_context.get('friday_close', 0.0)
        weekend_prices = weekend_context.get('weekend_prices', [])
        
        # 🔬 INGENIERÍA DE FEATURES CUANTITATIVAS
        micro_features = self._calculate_micro_features(weekend_prices, friday_close, current_price)
        
        # Generar resumen con contexto de fin de semana
        market_summary = self._generate_weekend_summary(indicators, current_price, micro_features)
        
        # Crear packet con features adicionales
        ai_packet = AIDataPacket(
            symbol=symbol,
            timestamp=datetime.now(),
            current_price=current_price,
            indicators=indicators,
            latest_candles=latest_candles[-15:],
            market_summary=market_summary
        )
        
        # Agregar features de fin de semana
        ai_packet.micro_features = micro_features
        ai_packet.market_mode = "weekend_otc"
        
        return ai_packet
    
    def _calculate_micro_features(self, weekend_prices: List[float], friday_close: float, current_price: float) -> Dict:
        """🔬 Calcula features cuantitativas para fin de semana"""
        if len(weekend_prices) < 2:
            return {
                'micro_trend': 0.0,
                'micro_volatility': 0.0,
                'gap_friday': 0.0 if friday_close == 0 else ((current_price - friday_close) / friday_close) * 100
            }
        
        prices_array = np.array(weekend_prices)
        
        # Micro trend: Pendiente de los últimos 5 precios
        trend_prices = prices_array[-5:] if len(prices_array) >= 5 else prices_array
        if len(trend_prices) >= 2:
            x = np.arange(len(trend_prices))
            slope, _ = np.polyfit(x, trend_prices, 1)
            micro_trend = slope * 10000  # Normalizar para pips
        else:
            micro_trend = 0.0
        
        # Micro volatility: Desviación estándar de últimos 10 precios
        vol_prices = prices_array[-10:] if len(prices_array) >= 10 else prices_array
        micro_volatility = float(np.std(vol_prices)) * 10000 if len(vol_prices) > 1 else 0.0
        
        # Gap desde viernes
        gap_friday = 0.0
        if friday_close > 0 and current_price > 0:
            gap_friday = ((current_price - friday_close) / friday_close) * 100
        
        return {
            'micro_trend': round(micro_trend, 2),
            'micro_volatility': round(micro_volatility, 2),
            'gap_friday': round(gap_friday, 4)
        }
    
    def _generate_weekend_summary(self, indicators: TechnicalIndicators, current_price: float, micro_features: Dict) -> str:
        """🏠 Genera resumen para modo fin de semana"""
        # Determinar tendencia base
        if indicators.ema_20 > indicators.ema_50:
            trend = "ALCISTA"
        elif indicators.ema_20 < indicators.ema_50:
            trend = "BAJISTA"
        else:
            trend = "LATERAL"
        
        # Condición RSI
        if indicators.rsi > 70:
            rsi_condition = "SOBRECOMPRA"
        elif indicators.rsi < 30:
            rsi_condition = "SOBREVENTA"
        else:
            rsi_condition = "NEUTRAL"
        
        # Micro features
        micro_trend = micro_features.get('micro_trend', 0)
        micro_vol = micro_features.get('micro_volatility', 0)
        gap_friday = micro_features.get('gap_friday', 0)
        
        summary = f"""⚠️ MODO OTC | TENDENCIA: {trend} | RSI: {rsi_condition} ({indicators.rsi:.1f})
MICRO_TREND: {micro_trend:+.2f} pips | MICRO_VOL: {micro_vol:.2f} pips
GAP_VIERNES: {gap_friday:+.4f}% | PRECIO: {current_price:.5f}"""
        
        return summary
    
    def _generate_market_summary(self, indicators: TechnicalIndicators, current_price: float) -> str:
        """Genera resumen textual optimizado para IA"""
        # Determinar tendencia
        if indicators.ema_20 > indicators.ema_50:
            trend = "ALCISTA"
        elif indicators.ema_20 < indicators.ema_50:
            trend = "BAJISTA"
        else:
            trend = "LATERAL"
        
        # Determinar condición RSI
        if indicators.rsi > 70:
            rsi_condition = "SOBRECOMPRA"
        elif indicators.rsi < 30:
            rsi_condition = "SOBREVENTA"
        else:
            rsi_condition = "NEUTRAL"
        
        # Posición en Bollinger Bands
        if indicators.bb_position > 0.8:
            bb_condition = "CERCA_SUPERIOR"
        elif indicators.bb_position < 0.2:
            bb_condition = "CERCA_INFERIOR"
        else:
            bb_condition = "ZONA_MEDIA"
        
        # Volatilidad
        vol_condition = "ALTA" if indicators.volatility > 1.0 else "BAJA"
        
        summary = f"""MERCADO: {trend} | RSI: {rsi_condition} ({indicators.rsi:.1f}) | 
BB: {bb_condition} ({indicators.bb_position:.2f}) | VOL: {vol_condition} ({indicators.volatility:.2f}%) | 
PRECIO: {current_price:.5f} | CAMBIO: {indicators.price_change_pct:+.3f}%"""
        
        return summary
    
    def get_analysis_for_display(self) -> Dict:
        """Obtiene análisis formateado para mostrar en UI"""
        if not self.last_analysis:
            return {}
        
        indicators = self.last_analysis
        
        return {
            'rsi': f"{indicators.rsi:.1f}",
            'rsi_status': self._get_rsi_status(indicators.rsi),
            'trend': self._get_trend_status(indicators.ema_20, indicators.ema_50),
            'bb_position': f"{indicators.bb_position:.2f}",
            'bb_status': self._get_bb_status(indicators.bb_position),
            'volatility': f"{indicators.volatility:.2f}%",
            'price_change': f"{indicators.price_change_pct:+.3f}%"
        }
    
    def _get_rsi_status(self, rsi: float) -> str:
        """Determina estado del RSI"""
        if rsi > 70:
            return "🔴 SOBRECOMPRA"
        elif rsi < 30:
            return "🟢 SOBREVENTA"
        else:
            return "🟡 NEUTRAL"
    
    def _get_trend_status(self, ema_20: float, ema_50: float) -> str:
        """Determina estado de la tendencia"""
        if ema_20 > ema_50:
            return "📈 ALCISTA"
        elif ema_20 < ema_50:
            return "📉 BAJISTA"
        else:
            return "➡️ LATERAL"
    
    def _get_bb_status(self, bb_position: float) -> str:
        """Determina posición en Bollinger Bands"""
        if bb_position > 0.8:
            return "🔴 BANDA SUPERIOR"
        elif bb_position < 0.2:
            return "🟢 BANDA INFERIOR"
        else:
            return "🟡 ZONA MEDIA"
    
    def should_wake_ai(self, indicators: TechnicalIndicators, df: pd.DataFrame) -> bool:
        """Signal Gating: Determina si vale la pena despertar la IA"""
        try:
            # Condición 1: RSI en zona extrema
            rsi_extreme = indicators.rsi > 70 or indicators.rsi < 30
            
            # Condición 2: Precio rompió Bollinger Bands
            current_price = df['close'].iloc[-1]
            bb_breakout = current_price >= indicators.bb_upper or current_price <= indicators.bb_lower
            
            # Condición 3: Pico de volumen inusual (>150% del promedio)
            current_volume = df['volume'].iloc[-1]
            volume_spike = current_volume > (indicators.volume_sma * 1.5)
            
            # Despertar IA si cualquier condición se cumple
            return rsi_extreme or bb_breakout or volume_spike
            
        except Exception as e:
            print(f"Error en Signal Gating: {e}")
            return True  # En caso de error, despertar IA por seguridad
    
    def should_wake_ai_weekend(self, indicators: TechnicalIndicators, df: pd.DataFrame, micro_features: Dict) -> bool:
        """🏠 Signal Gating para modo weekend con filtro de volatilidad"""
        try:
            # 🚫 FILTRO DE VOLATILIDAD INESTABLE
            weekend_volatility_threshold = 15.0  # pips
            micro_volatility = micro_features.get('micro_volatility', 0)
            
            if micro_volatility > weekend_volatility_threshold:
                print(f"🚫 OCR inestable (vol: {micro_volatility:.1f} pips) - Señales congeladas")
                return False
            
            # Condiciones normales pero más restrictivas
            rsi_extreme = indicators.rsi > 75 or indicators.rsi < 25  # Más restrictivo
            
            current_price = df['close'].iloc[-1]
            bb_breakout = current_price >= indicators.bb_upper or current_price <= indicators.bb_lower
            
            # Gap significativo desde viernes
            gap_friday = abs(micro_features.get('gap_friday', 0))
            significant_gap = gap_friday > 0.5  # >0.5% gap
            
            return rsi_extreme or bb_breakout or significant_gap
            
        except Exception as e:
            print(f"Error en Weekend Signal Gating: {e}")
            return False  # En weekend, ser más conservador