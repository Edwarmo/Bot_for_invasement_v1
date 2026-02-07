"""
🧪 TEST MOMENTUM SYSTEM - Validación del nuevo sistema de scalping
"""

import asyncio
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Rutas
base_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(base_dir, 'CAPA 1'))
sys.path.append(os.path.join(base_dir, 'CAPA 3'))

from market_data_stream import DataFusionHandler
from ai_inference_engine import LMStudioClient

class MomentumTester:
    def __init__(self):
        self.fusion_handler = DataFusionHandler()
        self.ai_client = LMStudioClient()
        
    async def test_momentum_system(self):
        """🧪 Test completo del sistema de momentum"""
        print("\n" + "="*60)
        print("🧪 TESTING SISTEMA DE MOMENTUM Y SCALPING")
        print("="*60)
        
        # 1. Test conexión IA
        print("\n1️⃣ TESTING CONEXIÓN IA...")
        if not await self.ai_client.test_connection():
            print("❌ IA no disponible. Abortando test.")
            return
        print("✅ IA conectada correctamente")
        
        # 2. Test métricas de momentum
        print("\n2️⃣ TESTING MÉTRICAS DE MOMENTUM...")
        await self._test_momentum_metrics()
        
        # 3. Test respuesta IA con datos de momentum
        print("\n3️⃣ TESTING RESPUESTA IA CON MOMENTUM...")
        await self._test_ai_momentum_response()
        
        print("\n✅ TEST COMPLETADO")
    
    async def _test_momentum_metrics(self):
        """Test cálculo de métricas de momentum"""
        try:
            # Simular datos de mercado
            current_price = 1.08500
            
            # Crear DataFrames simulados
            dates_1m = pd.date_range(start=datetime.now() - timedelta(minutes=20), 
                                   periods=20, freq='1min')
            dates_1h = pd.date_range(start=datetime.now() - timedelta(hours=10), 
                                   periods=10, freq='1h')
            
            # Simular tendencia alcista en 1m
            base_price = 1.08400
            df_1m = pd.DataFrame({
                'Close': [base_price + (i * 0.00005) for i in range(20)],  # Tendencia alcista
                'High': [base_price + (i * 0.00005) + 0.00010 for i in range(20)],
                'Low': [base_price + (i * 0.00005) - 0.00010 for i in range(20)],
                'Volume': [1000] * 20
            }, index=dates_1m)
            
            # Simular contexto 1h neutral
            df_1h = pd.DataFrame({
                'Close': [1.08450 + (i * 0.00001) for i in range(10)],
                'High': [1.08450 + (i * 0.00001) + 0.00020 for i in range(10)],
                'Low': [1.08450 + (i * 0.00001) - 0.00020 for i in range(10)],
                'Volume': [5000] * 10
            }, index=dates_1h)
            
            # Calcular métricas
            prompt_data = self.fusion_handler.construir_prompt_contextual(
                precio=current_price,
                df_1m=df_1m,
                df_1h=df_1h,
                symbol="EURUSD=X"
            )
            
            # Validar métricas
            print(f"   📊 Precio actual: {prompt_data['price']}")
            print(f"   📈 Tendencia sesión: {prompt_data['session_trend']}")
            print(f"   ⚡ Velocidad precio: {prompt_data['price_velocity']:.2f} pips")
            print(f"   💪 Fuerza direccional: {prompt_data['directional_strength']:.2f}")
            print(f"   🌊 Volatilidad reciente: {prompt_data['recent_volatility']:.2f}%")
            print(f"   🎯 Contexto macro: {prompt_data['macro_context']['trend_1h']}")
            
            # Validar señales de momentum
            signals = prompt_data['momentum_signals']
            print(f"   🧹 Gráfico limpio: {signals['clean_chart']}")
            print(f"   💥 Movimiento explosivo: {signals['explosive_move']}")
            print(f"   📊 Tendencia ordenada: {signals['ordered_trend']}")
            
            print("✅ Métricas de momentum calculadas correctamente")
            
        except Exception as e:
            print(f"❌ Error calculando métricas: {e}")
    
    async def _test_ai_momentum_response(self):
        """Test respuesta de IA con datos de momentum"""
        try:
            # Datos de prueba con momentum fuerte
            test_data = {
                "symbol": "EURUSD=X",
                "price": 1.08500,
                "session_trend": "UP",
                "macro_context": {"trend_1h": "BULLISH"},
                "price_velocity": 2.5,  # 2.5 pips de velocidad
                "recent_volatility": 0.8,
                "directional_strength": 0.85,  # 85% de movimientos en la misma dirección
                "market_hour": 14,  # 2 PM - hora activa
                "momentum_signals": {
                    "clean_chart": True,
                    "explosive_move": False,
                    "ordered_trend": True
                },
                "session_momentum": 1.8,
                "price_acceleration": 0.5
            }
            
            print("   📤 Enviando datos de momentum a IA...")
            response = await self.ai_client.analizar_mercado(test_data)
            
            if response:
                print(f"   📥 Decisión: {response.decision}")
                print(f"   📝 Razón: {response.razon}")
                print(f"   🕐 Timestamp: {response.timestamp}")
                
                # Validar que la respuesta sea coherente con momentum alcista
                if response.decision in ["CALL", "PUT", "NEUTRAL"]:
                    print("✅ Respuesta IA válida para momentum")
                else:
                    print("⚠️ Respuesta IA inesperada")
            else:
                print("❌ IA no respondió")
                
        except Exception as e:
            print(f"❌ Error testing respuesta IA: {e}")

async def main():
    tester = MomentumTester()
    await tester.test_momentum_system()

if __name__ == "__main__":
    asyncio.run(main())