"""
🏛️ CAPA 2: MOTOR DE PROBABILIDADES CUANTITATIVAS
Responsabilidad: Cálculo matemático riguroso de probabilidades de mercado
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from scipy import stats
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

@dataclass
class QuantitativeIndicators:
    """Indicadores cuantitativos calculados"""
    # Tendencia
    ema_fast: float
    ema_slow: float
    ema_signal: float  # -1 a 1
    sma_20: float
    sma_50: float
    trend_strength: float  # 0 a 100
    
    # Momentum
    rsi: float
    rsi_normalized: float  # -1 a 1
    momentum: float
    momentum_normalized: float  # -1 a 1
    roc: float  # Rate of Change
    
    # Mean Reversion
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_position: float  # 0 a 1
    bb_squeeze: float  # 0 a 1
    zscore: float
    
    # Volumen
    volume_sma: float
    volume_ratio: float
    vwap: float
    vwap_signal: float  # -1 a 1
    
    # Volatilidad
    atr: float
    atr_normalized: float
    volatility: float
    volatility_percentile: float
    
    # Estructura
    support_resistance_score: float
    fractal_dimension: float
    hurst_exponent: float

@dataclass
class MarketRegime:
    """Régimen de mercado detectado"""
    primary_trend: str  # 'bullish', 'bearish', 'sideways'
    trend_strength: float  # 0-100
    volatility_regime: str  # 'low', 'medium', 'high'
    volume_regime: str  # 'low', 'medium', 'high'
    market_phase: str  # 'accumulation', 'markup', 'distribution', 'markdown'
    confidence: float  # 0-100

@dataclass
class ProbabilityScore:
    """Score de probabilidad cuantitativo"""
    total_score: float  # 0-100
    direction: str  # 'bullish', 'bearish', 'neutral'
    confidence: float  # 0-100
    
    # Componentes del score
    trend_score: float
    momentum_score: float
    mean_reversion_score: float
    volume_score: float
    volatility_score: float
    structure_score: float
    
    # Probabilidades específicas
    reversal_probability: float  # 0-100
    continuation_probability: float  # 0-100

class QuantitativeProbabilityEngine:
    """Motor de probabilidades cuantitativas institucional"""
    
    def __init__(self, config):
        self.config = config
        
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calcula EMA con precisión institucional"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calcula SMA"""
        return prices.rolling(window=period).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula RSI normalizado"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calcula Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    def calculate_vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calcula VWAP"""
        typical_price = (high + low + close) / 3
        return (typical_price * volume).cumsum() / volume.cumsum()
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calcula ATR normalizado"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()
    
    def calculate_momentum(self, prices: pd.Series, period: int = 10) -> pd.Series:
        """Calcula momentum normalizado"""
        return prices.pct_change(periods=period)
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Calcula volatilidad realizada"""
        returns = prices.pct_change()
        return returns.rolling(window=period).std() * np.sqrt(252)
    
    def calculate_zscore(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Calcula Z-Score para mean reversion"""
        mean = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        return (prices - mean) / std
    
    def calculate_hurst_exponent(self, prices: pd.Series, max_lag: int = 20) -> float:
        """Calcula exponente de Hurst para detectar persistencia"""
        try:
            lags = range(2, max_lag)
            tau = [np.sqrt(np.std(np.subtract(prices[lag:], prices[:-lag]))) for lag in lags]
            poly = np.polyfit(np.log(lags), np.log(tau), 1)
            return poly[0] * 2.0
        except:
            return 0.5  # Movimiento browniano por defecto
    
    def detect_support_resistance(self, df: pd.DataFrame, window: int = 10) -> float:
        """Detecta niveles de soporte y resistencia"""
        try:
            high = df['high']
            low = df['low']
            close = df['close'].iloc[-1]
            
            # Encontrar máximos y mínimos locales
            highs = high.rolling(window=window, center=True).max() == high
            lows = low.rolling(window=window, center=True).min() == low
            
            resistance_levels = high[highs].dropna()
            support_levels = low[lows].dropna()
            
            # Calcular proximidad a niveles clave
            if len(resistance_levels) > 0 and len(support_levels) > 0:
                nearest_resistance = min(abs(close - r) for r in resistance_levels)
                nearest_support = min(abs(close - s) for s in support_levels)
                
                # Score basado en proximidad (menor distancia = mayor score)
                resistance_score = max(0, 100 - (nearest_resistance / close * 10000))
                support_score = max(0, 100 - (nearest_support / close * 10000))
                
                return (resistance_score + support_score) / 2
            
            return 50.0
        except:
            return 50.0
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> QuantitativeIndicators:
        """Calcula todos los indicadores cuantitativos"""
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # Tendencia
        ema_fast = self.calculate_ema(close, self.config.quantitative.ema_fast)
        ema_slow = self.calculate_ema(close, self.config.quantitative.ema_slow)
        sma_20 = self.calculate_sma(close, 20)
        sma_50 = self.calculate_sma(close, 50)
        
        # Señal EMA normalizada
        ema_diff = ema_fast - ema_slow
        ema_signal = np.tanh(ema_diff / close * 1000)  # Normalizar a [-1, 1]
        
        # Fuerza de tendencia
        trend_strength = abs(ema_signal.iloc[-1]) * 100
        
        # Momentum
        rsi = self.calculate_rsi(close, self.config.quantitative.rsi_period)
        rsi_normalized = (rsi - 50) / 50  # Normalizar a [-1, 1]
        
        momentum = self.calculate_momentum(close, self.config.quantitative.momentum_period)
        momentum_normalized = np.tanh(momentum * 100)  # Normalizar a [-1, 1]
        
        roc = close.pct_change(periods=10) * 100
        
        # Mean Reversion
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(close, self.config.quantitative.bb_period)
        bb_position = (close - bb_lower) / (bb_upper - bb_lower)
        bb_squeeze = (bb_upper - bb_lower) / bb_middle  # Medida de volatilidad
        
        zscore = self.calculate_zscore(close, 20)
        
        # Volumen
        volume_sma = volume.rolling(window=self.config.quantitative.volume_period).mean()
        volume_ratio = volume / volume_sma
        
        vwap = self.calculate_vwap(high, low, close, volume)
        vwap_signal = np.tanh((close - vwap) / close * 1000)  # Normalizar a [-1, 1]
        
        # Volatilidad
        atr = self.calculate_atr(high, low, close, self.config.quantitative.atr_period)
        atr_normalized = atr / close  # Normalizar por precio
        
        volatility = self.calculate_volatility(close, self.config.quantitative.volatility_period)
        volatility_percentile = volatility.rolling(window=50).rank(pct=True) * 100
        
        # Estructura
        support_resistance_score = self.detect_support_resistance(df)
        hurst_exponent = self.calculate_hurst_exponent(close.tail(50))
        fractal_dimension = 2 - hurst_exponent
        
        return QuantitativeIndicators(
            # Tendencia
            ema_fast=float(ema_fast.iloc[-1]) if not ema_fast.empty else close.iloc[-1],
            ema_slow=float(ema_slow.iloc[-1]) if not ema_slow.empty else close.iloc[-1],
            ema_signal=float(ema_signal.iloc[-1]) if not ema_signal.empty else 0.0,
            sma_20=float(sma_20.iloc[-1]) if not sma_20.empty else close.iloc[-1],
            sma_50=float(sma_50.iloc[-1]) if not sma_50.empty else close.iloc[-1],
            trend_strength=float(trend_strength) if not np.isnan(trend_strength) else 0.0,
            
            # Momentum
            rsi=float(rsi.iloc[-1]) if not rsi.empty else 50.0,
            rsi_normalized=float(rsi_normalized.iloc[-1]) if not rsi_normalized.empty else 0.0,
            momentum=float(momentum.iloc[-1]) if not momentum.empty else 0.0,
            momentum_normalized=float(momentum_normalized.iloc[-1]) if not momentum_normalized.empty else 0.0,
            roc=float(roc.iloc[-1]) if not roc.empty else 0.0,
            
            # Mean Reversion
            bb_upper=float(bb_upper.iloc[-1]) if not bb_upper.empty else close.iloc[-1],
            bb_middle=float(bb_middle.iloc[-1]) if not bb_middle.empty else close.iloc[-1],
            bb_lower=float(bb_lower.iloc[-1]) if not bb_lower.empty else close.iloc[-1],
            bb_position=float(bb_position.iloc[-1]) if not bb_position.empty else 0.5,
            bb_squeeze=float(bb_squeeze.iloc[-1]) if not bb_squeeze.empty else 0.02,
            zscore=float(zscore.iloc[-1]) if not zscore.empty else 0.0,
            
            # Volumen
            volume_sma=float(volume_sma.iloc[-1]) if not volume_sma.empty else volume.iloc[-1],
            volume_ratio=float(volume_ratio.iloc[-1]) if not volume_ratio.empty else 1.0,
            vwap=float(vwap.iloc[-1]) if not vwap.empty else close.iloc[-1],
            vwap_signal=float(vwap_signal.iloc[-1]) if not vwap_signal.empty else 0.0,
            
            # Volatilidad
            atr=float(atr.iloc[-1]) if not atr.empty else 0.0,
            atr_normalized=float(atr_normalized.iloc[-1]) if not atr_normalized.empty else 0.0,
            volatility=float(volatility.iloc[-1]) if not volatility.empty else 0.0,
            volatility_percentile=float(volatility_percentile.iloc[-1]) if not volatility_percentile.empty else 50.0,
            
            # Estructura
            support_resistance_score=support_resistance_score,
            fractal_dimension=fractal_dimension,
            hurst_exponent=hurst_exponent
        )
    
    def detect_market_regime(self, df: pd.DataFrame, indicators: QuantitativeIndicators) -> MarketRegime:
        """Detecta régimen de mercado usando análisis multi-dimensional"""
        
        # Análisis de tendencia primaria
        trend_signals = [
            indicators.ema_signal,
            indicators.vwap_signal,
            1 if indicators.sma_20 > indicators.sma_50 else -1
        ]
        
        trend_consensus = np.mean(trend_signals)
        
        if trend_consensus > 0.3:
            primary_trend = 'bullish'
        elif trend_consensus < -0.3:
            primary_trend = 'bearish'
        else:
            primary_trend = 'sideways'
        
        # Fuerza de tendencia
        trend_strength = min(abs(trend_consensus) * 100, 100)
        
        # Régimen de volatilidad
        vol_percentile = indicators.volatility_percentile
        if vol_percentile < 30:
            volatility_regime = 'low'
        elif vol_percentile < 70:
            volatility_regime = 'medium'
        else:
            volatility_regime = 'high'
        
        # Régimen de volumen
        if indicators.volume_ratio < 0.8:
            volume_regime = 'low'
        elif indicators.volume_ratio < 1.2:
            volume_regime = 'medium'
        else:
            volume_regime = 'high'
        
        # Fase de mercado basada en precio vs EMAs y volumen
        price = df['close'].iloc[-1]
        if price > indicators.ema_fast > indicators.ema_slow and indicators.volume_ratio > 1.0:
            market_phase = 'markup'
        elif price < indicators.ema_fast < indicators.ema_slow and indicators.volume_ratio > 1.0:
            market_phase = 'markdown'
        elif indicators.volume_ratio < 0.9 and abs(indicators.ema_signal) < 0.2:
            market_phase = 'accumulation'
        else:
            market_phase = 'distribution'
        
        # Confianza basada en coherencia de señales
        confidence = min(trend_strength + (indicators.volume_ratio - 1) * 20, 100)
        confidence = max(confidence, 0)
        
        return MarketRegime(
            primary_trend=primary_trend,
            trend_strength=trend_strength,
            volatility_regime=volatility_regime,
            volume_regime=volume_regime,
            market_phase=market_phase,
            confidence=confidence
        )
    
    def calculate_probability_scores(self, indicators: QuantitativeIndicators, regime: MarketRegime) -> ProbabilityScore:
        """Calcula scores de probabilidad cuantitativos"""
        
        weights = self.config.quantitative.weights
        
        # 1. TREND SCORE (0-100)
        trend_score = 50 + (indicators.ema_signal * 25) + (indicators.vwap_signal * 25)
        trend_score = max(0, min(100, trend_score))
        
        # 2. MOMENTUM SCORE (0-100)
        rsi_momentum = 50 + (indicators.rsi_normalized * 30)
        price_momentum = 50 + (indicators.momentum_normalized * 50)
        momentum_score = (rsi_momentum + price_momentum) / 2
        momentum_score = max(0, min(100, momentum_score))
        
        # 3. MEAN REVERSION SCORE (0-100)
        bb_reversion = abs(indicators.bb_position - 0.5) * 100  # Distancia del centro
        zscore_reversion = min(abs(indicators.zscore) * 20, 50)
        mean_reversion_score = (bb_reversion + zscore_reversion)
        mean_reversion_score = max(0, min(100, mean_reversion_score))
        
        # 4. VOLUME SCORE (0-100)
        volume_confirmation = min(indicators.volume_ratio * 50, 100)
        volume_score = volume_confirmation
        
        # 5. VOLATILITY SCORE (0-100)
        vol_score = 100 - indicators.volatility_percentile  # Menor volatilidad = mayor score
        volatility_score = max(0, min(100, vol_score))
        
        # 6. STRUCTURE SCORE (0-100)
        structure_score = indicators.support_resistance_score
        
        # SCORE TOTAL PONDERADO
        total_score = (
            trend_score * weights["trend"] +
            momentum_score * weights["momentum"] +
            mean_reversion_score * weights["mean_reversion"] +
            volume_score * weights["volume"] +
            volatility_score * weights["volatility"] +
            structure_score * weights["structure"]
        )
        
        # DIRECCIÓN BASADA EN CONSENSO
        direction_signals = [
            indicators.ema_signal,
            indicators.rsi_normalized,
            indicators.momentum_normalized,
            indicators.vwap_signal
        ]
        
        direction_consensus = np.mean(direction_signals)
        
        if direction_consensus > 0.2:
            direction = 'bullish'
        elif direction_consensus < -0.2:
            direction = 'bearish'
        else:
            direction = 'neutral'
        
        # CONFIANZA BASADA EN COHERENCIA
        signal_std = np.std(direction_signals)
        confidence = max(0, min(100, (1 - signal_std) * 100))
        
        # PROBABILIDADES ESPECÍFICAS
        if direction == 'bullish':
            continuation_probability = total_score
            reversal_probability = 100 - total_score
        elif direction == 'bearish':
            continuation_probability = 100 - total_score
            reversal_probability = total_score
        else:
            continuation_probability = 50
            reversal_probability = 50
        
        return ProbabilityScore(
            total_score=total_score,
            direction=direction,
            confidence=confidence,
            trend_score=trend_score,
            momentum_score=momentum_score,
            mean_reversion_score=mean_reversion_score,
            volume_score=volume_score,
            volatility_score=volatility_score,
            structure_score=structure_score,
            reversal_probability=reversal_probability,
            continuation_probability=continuation_probability
        )
    
    def analyze_multi_timeframe(self, symbol: str, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, ProbabilityScore]:
        """Análisis cuantitativo multi-timeframe"""
        results = {}
        
        for timeframe, df in data_dict.items():
            if df is not None and not df.empty:
                indicators = self.calculate_all_indicators(df)
                regime = self.detect_market_regime(df, indicators)
                probability_score = self.calculate_probability_scores(indicators, regime)
                
                results[timeframe] = probability_score
        
        return results