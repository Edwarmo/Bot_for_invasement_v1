"""
🚀 MAIN.PY - VERSIÓN DEFINITIVA (DICCIONARIOS + DEBUG + QA)
"""

import asyncio
import time
import sys
import os
import subprocess
import traceback
import pandas as pd
from datetime import datetime
from pathlib import Path

# Agregar src al path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'src'))

from domain.prediction import PredictionTracker
from data.market_stream import DataFusionHandler
from services.ai_client import LMStudioClient
from services.alerts import mostrar_alerta
from services.indicators import calcular_indicadores_tecnicos, calcular_tendencia_macro

# 🎯 CONFIGURACIÓN
CSV_PATH = "capturador/prices.csv"
SYMBOL = "EURUSD=X"
OBSERVATION_WINDOW = 45  # Balance entre velocidad y datos suficientes
STAGNATION_TIMEOUT = 20  # QA: Segundos sin cambio de precio para detectar estancamiento

# 📊 LOGS DE AUDITORÍA
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
AUDIT_LOG = LOGS_DIR / "decisiones_historia.csv"

# Crear CSV de auditoría si no existe
if not AUDIT_LOG.exists():
    with open(AUDIT_LOG, 'w', encoding='utf-8') as f:
        f.write("timestamp,precio_entrada,decision,confianza,rsi_momento,resultado,precio_salida\n")


def guardar_audit_log(timestamp: str, precio_entrada: float, decision: str, confianza: int, rsi_momento: float = 0.0, resultado: str = "PENDIENTE", precio_salida: float = 0.0):
    """QA: Guarda decisión en log de auditoría"""
    try:
        with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp},{precio_entrada},{decision},{confianza},{rsi_momento:.2f},{resultado},{precio_salida:.5f}\n")
        print(f"📝 Audit log guardado: {decision} @ {precio_entrada}")
    except Exception as e:
        print(f"⚠️ Error guardando audit log: {e}")


def validar_decisiones_pendientes():
    """QA: Valida decisiones pendientes después de 4 minutos"""
    try:
        if not AUDIT_LOG.exists():
            return
        
        # Leer decisiones pendientes
        df = pd.read_csv(AUDIT_LOG)
        pendientes = df[df['resultado'] == 'PENDIENTE']
        
        if pendientes.empty:
            return
        
        # Leer precios actuales del CSV
        if not os.path.exists(CSV_PATH):
            return
        
        df_prices = pd.read_csv(CSV_PATH)
        if df_prices.empty:
            return
        
        ultimo_precio = df_prices['price'].iloc[-1]
        ahora = datetime.now()
        
        for idx, row in pendientes.iterrows():
            try:
                fecha_decision = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
                tiempo_transcurrido = (ahora - fecha_decision).total_seconds()
                
                # Solo validar si pasaron al menos 4 minutos (240 segundos)
                if tiempo_transcurrido >= 240:
                    precio_entrada = row['precio_entrada']
                    decision = row['decision']
                    
                    # Determinar resultado
                    if decision == "CALL" and ultimo_precio > precio_entrada:
                        resultado = "ACERTADO"
                    elif decision == "PUT" and ultimo_precio < precio_entrada:
                        resultado = "ACERTADO"
                    elif decision == "CALL" and ultimo_precio <= precio_entrada:
                        resultado = "FALLIDO"
                    elif decision == "PUT" and ultimo_precio >= precio_entrada:
                        resultado = "FALLIDO"
                    else:
                        resultado = "NINGUNO"
                    
                    # Actualizar CSV
                    df.at[idx, 'resultado'] = resultado
                    df.at[idx, 'precio_salida'] = ultimo_precio
                    print(f"✅ Validado: {decision} @ {precio_entrada} -> {resultado} @ {ultimo_precio:.5f}")
            except Exception as e:
                print(f"⚠️ Error validando decisión: {e}")
        
        # Guardar cambios
        df.to_csv(AUDIT_LOG, index=False)
        
    except Exception as e:
        print(f"⚠️ Error en validación: {e}")


class DataFusionSystem:
    def __init__(self):
        self.fusion_handler = DataFusionHandler()
        self.ai_client = LMStudioClient()
        self.prediction_tracker = PredictionTracker()
        self.running = False
        self.capturador_process = None
        self.contexto_yahoo = None
        self.last_price = None
        self.last_price_time = None

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
        
        # Esperar a que LM Studio esté completamente listo
        print("⏳ Esperando a que LM Studio esté listo...")
        max_retries = 10
        for i in range(max_retries):
            if await self.ai_client.test_connection():
                break
            print(f"   Intento {i+1}/{max_retries} - Esperando 10s...")
            await asyncio.sleep(10)
        
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
                # QA: Validar decisiones pendientes antes de nuevo ciclo
                validar_decisiones_pendientes()
                
                await self._execute_cycle()
                print("\n💤 Enfriamiento de 10s...")
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            print("\n🛑 Apagando...")
        finally:
            self.stop()

    async def _monitor_market(self, duration):
        print(f"\n🕵️ OBSERVANDO MERCADO (Turbo) POR {duration} SEGUNDOS...")
        start_time = time.time()
        collected_prices = []
        last_price = 0
        
        # QA: Detección de estancamiento
        last_price_change_time = time.time()
        stagnation_detected = False
        
        # Optimización: Pre-allocate lista
        collected_prices = [0] * 200  # Pre-allocate para ~200 lecturas
        count = 0
        
        while time.time() - start_time < duration and count < 200:
            try:
                current_price = self.fusion_handler.leer_precio_csv(CSV_PATH)
                
                # QA: Detectar estancamiento (20s sin cambio)
                if current_price != last_price and last_price > 0:
                    time_since_change = time.time() - last_price_change_time
                    if time_since_change > STAGNATION_TIMEOUT and not stagnation_detected:
                        print(f"\n⚠️ ESTANCAMIENTO DETECTADO: {time_since_change:.1f}s sin cambio de precio!")
                        stagnation_detected = True
                    last_price_change_time = time.time()
                
                if current_price > 0 and 1.0 < current_price < 2.0 and current_price != last_price:
                    collected_prices[count] = current_price
                    count += 1
                    if count % 10 == 0:  # Update cada 10 lecturas
                        sys.stdout.write(f"\r   📉 Capturas: {count} | Último: {current_price:.5f}  ")
                        sys.stdout.flush()
                    last_price = current_price
                # Sleep mínimo para captura rápida
                await asyncio.sleep(0.1)
            except:
                await asyncio.sleep(0.1)

        # QA: Verificar si hubo estancamiento
        if stagnation_detected:
            print("\n🚫 OPERACIÓN CANCELADA: Mercado estancado (sin cambios en 20s)")
            return []  # Retornar lista vacía para cancelar operación
        
        # Trim lista al tamaño real
        collected_prices = collected_prices[:count]
        print(f"\n✅ Fin observación. Total datos: {len(collected_prices)}")
        return collected_prices

    async def _execute_cycle(self):
        try:
            # 1. Validar predicciones anteriores
            self.prediction_tracker.validate_predictions(CSV_PATH)
            
            # 2. Observar mercado y calcular métricas de momentum
            recent_prices = await self._monitor_market(OBSERVATION_WINDOW)
            
            if not recent_prices or len(recent_prices) < 5:
                print("⚠️ Pocos datos CSV. Usando solo Yahoo Finance...")
                # FALLBACK: Usar solo Yahoo Finance si no hay datos CSV
                contexto_yahoo = self.fusion_handler.obtener_contexto_yahoo(SYMBOL)
                df_5m = contexto_yahoo.get('df_5m', pd.DataFrame())
                
                if not df_5m.empty:
                    # Usar último precio de Yahoo como fallback
                    current_price = float(df_5m['Close'].iloc[-1])
                    recent_prices = df_5m['Close'].tail(10).tolist()
                    print(f"📊 Fallback Yahoo 5m: {current_price:.5f} con {len(recent_prices)} datos")
                else:
                    print("❌ Sin datos CSV ni Yahoo. Saltando ciclo...")
                    return

            current_price = recent_prices[-1]
            self._last_price = current_price  # Guardar para el tracker
            
            # 3. Obtener contexto Yahoo Finance (MACRO - RÍO)
            contexto_yahoo = self.fusion_handler.obtener_contexto_yahoo(SYMBOL)
            df_5m = contexto_yahoo.get('df_5m', pd.DataFrame())
            df_1h = contexto_yahoo.get('df_1h', pd.DataFrame())
            
            # 4. Construir datos MACRO vs MICRO para IA
            contexto_fusion = self.fusion_handler.construir_prompt_contextual(current_price, df_5m, df_1h, SYMBOL)
            
            # 5. Armar datos para IA con MACRO-MICRO FUSION
            learning_context = self.prediction_tracker.get_learning_context()
            datos_para_ia = {
                'symbol': SYMBOL,
                'MACRO_RIO': contexto_fusion['MACRO_RIO'],
                'MICRO_OLA': contexto_fusion['MICRO_OLA'], 
                'FUSION_RESULT': contexto_fusion['FUSION_RESULT'],
                'learning_context': learning_context
            }
            
            print(f"\n🧠 ENVIANDO A IA (Esto puede tardar 20-40s)...")
            respuesta_ia = await self.ai_client.analizar_mercado(datos_para_ia)

            # --- DEBUG IMPRESCINDIBLE ---
            print(f"\n📬 RESPUESTA CRUDA RECIBIDA: {respuesta_ia}")
            # ---------------------------

            if not respuesta_ia:
                print("❌ La IA devolvió None (Timeout o Error).")
                return

            # 5. GUI
            self._process_decision_gui(respuesta_ia)

        except Exception as e:
            print(f"❌ Error CRÍTICO en ciclo: {e}")
            traceback.print_exc()
    
    def _limpiar_contexto_yahoo(self, df_1m, df_1h):
        """🧹 Convierte DataFrames a diccionarios simples"""
        contexto_limpio = {
            "tendencia_1h": "NEUTRAL",
            "volatilidad": 0.0,
            "ultimo_precio_yahoo": 0.0
        }
        
        try:
            # Procesar 1h para tendencia
            if not df_1h.empty and len(df_1h) >= 2:
                primer_close = float(df_1h['Close'].iloc[0])
                ultimo_close = float(df_1h['Close'].iloc[-1])
                
                if ultimo_close > primer_close * 1.002:
                    contexto_limpio["tendencia_1h"] = "BULLISH"
                elif ultimo_close < primer_close * 0.998:
                    contexto_limpio["tendencia_1h"] = "BEARISH"
                
                contexto_limpio["ultimo_precio_yahoo"] = ultimo_close
            
            # Procesar 1m para volatilidad
            if not df_1m.empty and len(df_1m) >= 5:
                closes = df_1m['Close'].tail(10)
                volatilidad = float(closes.std() / closes.mean() * 100)
                contexto_limpio["volatilidad"] = volatilidad
                
        except Exception as e:
            print(f"⚠️ Error limpiando contexto: {e}")
        
        return contexto_limpio

    def _process_decision_gui(self, data):
        """Maneja objetos AIResponse y lanza la alerta con información de momentum"""
        try:
            # Manejar objeto AIResponse (no diccionario)
            if hasattr(data, 'decision'):
                accion = data.decision.upper()
                razon = data.razon
            else:
                # Fallback para diccionarios
                accion = data.get('direccion', data.get('decision', 'NEUTRAL')).upper()
                razon = data.get('razon', "Análisis de momentum")

            # Extraer confianza de la razón
            confidence = 50  # Default
            try:
                if "Score:" in razon:
                    import re
                    match = re.search(r'Score: (\d+)%', razon)
                    if match:
                        confidence = int(match.group(1))
                elif "Conf:" in razon:
                    import re
                    match = re.search(r'Conf: (\d+)%', razon)
                    if match:
                        confidence = int(match.group(1))
            except Exception as e:
                print(f"⚠️ Error extrayendo confianza: {e}")
                confidence = 50

            # SOLO MOSTRAR SI CONFIANZA > 75%
            if confidence <= 75:
                print(f"🔇 Señal oculta: {accion} (confianza {confidence}% ≤ 75%)")
                return
            
            # Registrar predicción para validación futura
            current_price = getattr(self, '_last_price', 1.17200)  # Precio actual
            self.prediction_tracker.log_prediction(accion, confidence, current_price, razon)

            # QA: GUARDAR EN LOG DE AUDITORÍA
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Calcular RSI简单 (usando datos disponibles o 50 por defecto)
            rsi_momento = 50.0  # Placeholder - se puede mejorar con indicadores
            guardar_audit_log(timestamp, current_price, accion, confidence, rsi_momento)

            # Mapeo de colores y textos para momentum
            if "CALL" in accion:
                display_text = "CALL (SUBE) 🚀"
            elif "PUT" in accion:
                display_text = "PUT (BAJA) 📉"
            else:
                # Si es OCULTAR, NEUTRAL, etc. - no mostrar nada
                print(f"🔇 Señal oculta: {accion} (confianza insuficiente)")
                return

            print("\n" + "█"*60)
            print(f"🚀 LANZANDO POPUP: {display_text}")
            print(f"📊 MOMENTUM: {razon}")
            print("█"*60)

            # Determinar expiración basada en tipo de movimiento
            if "EXPLOSIÓN" in razon:
                expiracion = "1 MINUTO"
            elif "TENDENCIA ORDENADA" in razon:
                expiracion = "3 - 5 MINUTOS"
            else:
                expiracion = "3 - 5 MINUTOS"

            # Lanza la ventana
            mostrar_alerta(display_text, razon, expiracion)

        except Exception as e:
            print(f"❌ Error mostrando ventana: {e}")
            traceback.print_exc()

    def stop(self):
        self.running = False
        if self.capturador_process: 
            self.capturador_process.terminate()
        # Cerrar sesión IA
        if hasattr(self.ai_client, 'session') and self.ai_client.session:
            try:
                # Crear nueva tarea para cerrar sesión
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.ai_client.close())
                loop.close()
            except Exception as e:
                print(f"⚠️ Error cerrando sesión IA: {e}")

async def ciclo_principal():
    """Función que mantiene el bot vivo y maneja reinicios suaves"""
    print("🚀 INICIANDO BOT...")
    
    # Inicializar sistema
    system = DataFusionSystem()
    
    # Bucle infinito controlado
    while True:
        try:
            await system.start()
            
        except Exception as e:
            print(f"⚠️ Error en ciclo principal: {e}")
            print("🔄 Reiniciando en 5 segundos...")
            await asyncio.sleep(5)
            
        # Pequeña pausa entre ciclos
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        # UNA SOLA LLAMADA A RUN
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        asyncio.run(ciclo_principal())
    except KeyboardInterrupt:
        print("\n👋 Bot detenido por usuario.")