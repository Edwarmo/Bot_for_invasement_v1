"""
🚀 MAIN.PY - VERSIÓN DEFINITIVA (DICCIONARIOS + DEBUG)
"""

import asyncio
import time
import sys
import os
import subprocess
import traceback

# Rutas
base_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(base_dir, 'CAPA 1'))
sys.path.append(os.path.join(base_dir, 'CAPA 3'))
sys.path.append(os.path.join(base_dir, 'capturador'))

# Importaciones
from market_data_stream import DataFusionHandler
from ai_inference_engine import LMStudioClient
from gui_alerts import mostrar_alerta

# 🎯 CONFIGURACIÓN
CSV_PATH = "capturador/prices.csv"
SYMBOL = "EURUSD=X"
OBSERVATION_WINDOW = 60  # Reducido a 60s para pruebas rápidas (puedes subirlo a 180)

class DataFusionSystem:
    def __init__(self):
        self.fusion_handler = DataFusionHandler()
        self.ai_client = LMStudioClient()
        self.running = False
        self.capturador_process = None
        self.contexto_yahoo = None

    def _start_capturador(self):
        try:
            print("👁️ Iniciando ojos del bot (Capturador)...")
            capturador_path = os.path.join(os.path.dirname(__file__), 'capturador', 'main.py')
            self.capturador_process = subprocess.Popen(
                [sys.executable, capturador_path],
                cwd=os.path.join(os.path.dirname(__file__), 'capturador'),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except Exception as e:
            print(f"❌ Error capturador: {e}")

    async def start(self):
        print("\n" + "="*60)
        print(f"🚀 INICIANDO BOT CON GUI ALERT (MODO ROBUSTO)")
        print("="*60)
        
        self._start_capturador()
        await asyncio.sleep(4)
        
        if not await self.ai_client.test_connection():
            print("⚠️ ERROR CRÍTICO: IA no conectada.")
            return

        print("📊 Obteniendo contexto macro (Yahoo Finance)...")
        try:
            self.contexto_yahoo = self.fusion_handler.obtener_contexto_yahoo(SYMBOL)
            print("✅ Contexto macro cargado")
        except:
            print("⚠️ Yahoo offline - Usando modo puramente visual")
            self.contexto_yahoo = {"trend": "NEUTRAL"}

        self.running = True
        try:
            while self.running:
                await self._execute_cycle()
                print("\n💤 Enfriamiento de 10s...")
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            print("\n🛑 Apagando...")
        finally:
            self.stop()

    async def _monitor_market(self, duration):
        print(f"\n🕵️ OBSERVANDO MERCADO POR {duration} SEGUNDOS...")
        start_time = time.time()
        collected_prices = []
        last_price = 0
        
        while time.time() - start_time < duration:
            try:
                current_price = self.fusion_handler.leer_precio_csv(CSV_PATH)
                if current_price > 0:
                    if current_price != last_price:
                        collected_prices.append(current_price)
                        sys.stdout.write(f"\r   📉 Precio: {current_price:.5f} | Datos: {len(collected_prices)}  ")
                        sys.stdout.flush()
                        last_price = current_price
                await asyncio.sleep(1)
            except:
                pass

        print(f"\n✅ Fin observación. Total datos: {len(collected_prices)}")
        return collected_prices

    async def _execute_cycle(self):
        try:
            # 1. Observar
            recent_prices = await self._monitor_market(OBSERVATION_WINDOW)
            
            if not recent_prices or len(recent_prices) < 5:
                print("⚠️ Pocos datos. Reintentando...")
                return

            current_price = recent_prices[-1]
            
            # 2. Consultar IA
            prompt_data = {
                'symbol': SYMBOL,
                'price': current_price,
                'session_trend': "UP" if recent_prices[-1] > recent_prices[0] else "DOWN",
                'macro_context': self.contexto_yahoo
            }
            
            print(f"\n🧠 ENVIANDO A IA (Esto puede tardar 20-40s)...")
            respuesta_ia = await self.ai_client.analizar_mercado(prompt_data)

            # --- DEBUG IMPRESCINDIBLE ---
            print(f"\n📬 RESPUESTA CRUDA RECIBIDA: {respuesta_ia}")
            # ---------------------------

            if not respuesta_ia:
                print("❌ La IA devolvió None (Timeout o Error).")
                return

            # 3. GUI
            self._process_decision_gui(respuesta_ia)

        except Exception as e:
            print(f"❌ Error CRÍTICO en ciclo: {e}")
            traceback.print_exc()

    def _process_decision_gui(self, data):
        """Maneja objetos AIResponse y lanza la alerta"""
        try:
            # Manejar objeto AIResponse (no diccionario)
            if hasattr(data, 'decision'):
                accion = data.decision.upper()
                razon = data.razon
            else:
                # Fallback para diccionarios
                accion = data.get('direccion', data.get('decision', 'NEUTRAL')).upper()
                razon = data.get('razon', "Análisis técnico determinista")

            # Mapeo de colores y textos
            if "UP" in accion or "CALL" in accion or "BULLISH" in accion:
                display_text = "CALL (SUBE) 🟢"
            elif "DOWN" in accion or "PUT" in accion or "BEARISH" in accion:
                display_text = "PUT (BAJA) 🔴"
            else:
                display_text = "NEUTRAL ⚪"

            print("\n" + "█"*60)
            print(f"🚀 LANZANDO POPUP: {display_text}")
            print("█"*60)

            # Lanza la ventana
            mostrar_alerta(display_text, razon, "3 - 5 MINUTOS")

        except Exception as e:
            print(f"❌ Error mostrando ventana: {e}")
            traceback.print_exc()

    def stop(self):
        self.running = False
        if self.capturador_process: self.capturador_process.terminate()

if __name__ == "__main__":
    try:
        asyncio.run(DataFusionSystem().start())
    except KeyboardInterrupt: 
        pass