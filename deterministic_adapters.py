"""
🔧 ADAPTADORES DETERMINISTAS
Responsabilidad: Desacoplar dependencias externas con fallbacks estables
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

class DeterministicDataProvider:
    """📊 Proveedor de datos determinista con fallback"""
    
    def __init__(self, fusion_handler=None):
        self.fusion_handler = fusion_handler
        self.fallback_data = self._generate_fallback_context()
    
    def _generate_fallback_context(self) -> Dict:
        """🎲 Genera contexto determinista cuando Yahoo falla"""
        base_price = 1.08500
        return {
            'df_1m': pd.DataFrame(),
            'df_1h': self._create_synthetic_candles(base_price, 24),
            'trend': 'NEUTRAL',
            'volatility': 0.5
        }
    
    def _create_synthetic_candles(self, base_price: float, count: int) -> pd.DataFrame:
        """🕯️ Crea velas sintéticas deterministas"""
        data = []
        current_price = base_price
        
        for i in range(count):
            # Movimiento determinista basado en índice
            movement = 0.0001 * (i % 5 - 2)  # Oscila entre -0.0002 y +0.0002
            current_price += movement
            
            data.append({
                'Open': current_price,
                'High': current_price + 0.0001,
                'Low': current_price - 0.0001,
                'Close': current_price,
                'Volume': 1000
            })
        
        return pd.DataFrame(data)
    
    def get_market_context(self, symbol: str) -> Dict:
        """📈 Obtiene contexto con fallback determinista"""
        try:
            if self.fusion_handler:
                context = self.fusion_handler.obtener_contexto_yahoo(symbol)
                if context and not context.get('df_1h', pd.DataFrame()).empty:
                    return context
        except Exception:
            pass
        
        print("📊 Usando contexto determinista (Yahoo no disponible)")
        return self.fallback_data

class DeterministicAIClient:
    """🤖 Cliente IA determinista con fallback"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.decision_patterns = ['CALL', 'PUT', 'HOLD']
    
    async def analyze_market(self, market_data: Dict) -> Optional[object]:
        """🧠 Análisis con fallback determinista"""
        try:
            if self.ai_client:
                response = await self.ai_client.analizar_mercado(market_data)
                if response:
                    return response
        except Exception:
            pass
        
        print("🤖 Usando análisis determinista (IA no disponible)")
        return self._generate_deterministic_decision(market_data)
    
    def _generate_deterministic_decision(self, market_data: Dict) -> object:
        """🎯 Genera decisión determinista basada en datos"""
        
        class DeterministicResponse:
            def __init__(self, decision: str, razon: str):
                self.decision = decision
                self.razon = razon
        
        # Lógica determinista simple
        prices = market_data.get('session_trend', [])
        if len(prices) >= 2:
            trend = prices[-1] - prices[0]
            if trend > 0.0001:
                return DeterministicResponse("CALL", "Tendencia alcista detectada")
            elif trend < -0.0001:
                return DeterministicResponse("PUT", "Tendencia bajista detectada")
        
        return DeterministicResponse("HOLD", "Mercado lateral - sin señal clara")

class DeterministicCapturador:
    """👁️ Capturador determinista con fallback"""
    
    def __init__(self):
        self.base_price = 1.08500
        self.price_counter = 0
    
    def start_capture(self) -> bool:
        """🎯 Inicia captura (siempre exitoso en modo determinista)"""
        print("👁️ Capturador determinista activo")
        return True
    
    def get_current_price(self) -> float:
        """💰 Genera precio determinista"""
        # Patrón determinista: oscilación controlada
        self.price_counter += 1
        movement = 0.00001 * (self.price_counter % 10 - 5)  # -5 a +5 pips
        return self.base_price + movement
    
    def stop_capture(self):
        """⏹️ Detiene captura"""
        print("👁️ Capturador determinista detenido")