"""
📊 CAPA 1: WEEKEND SURVIVAL MODE - HYBRID FEED
Responsabilidad: Mercado Real (L-V) + Mercado OTC (Fin de semana)
"""

import pandas as pd
import numpy as np
import yfinance as yf
import cv2
import mss
import pytesseract
import threading
import time
import csv
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Callable, Optional
import re
import os
from coordenadas_iq_option import SEARCH_REGION, OCR_CONFIG, DEBUG_DIR
from concurrent.futures import ThreadPoolExecutor

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

@dataclass
class MarketTick:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str = "yfinance"  # "yfinance", "ocr", "friday_cache", "mock_generated"
    data_source_tag: str = "UNKNOWN"  # "OCR_LIVE", "CACHE_FRIDAY", "MOCK_GENERATED"

class MarketSchedule:
    """📅 Detector de horarios de mercado"""
    
    @staticmethod
    def is_market_open() -> bool:
        """Verifica si el mercado Forex está abierto"""
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # Forex cierra viernes 22:00 UTC, abre domingo 22:00 UTC
        if weekday == 5:  # Saturday
            return False
        elif weekday == 6:  # Sunday
            return now.hour >= 22  # Abre domingo 22:00
        elif weekday == 4:  # Friday
            return now.hour < 22   # Cierra viernes 22:00
        else:
            return True  # Monday-Thursday siempre abierto
    
    @staticmethod
    def is_friday_close() -> bool:
        """Detecta si es viernes cerca del cierre"""
        now = datetime.now()
        return now.weekday() == 4 and now.hour >= 21  # Viernes 21:00+

class WeekendCache:
    """💾 Gestor de caché para fin de semana"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.cache_dir = "weekend_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def save_friday_context(self, historical_data: pd.DataFrame):
        """💾 Guarda contexto del viernes"""
        if not historical_data.empty:
            filepath = os.path.join(self.cache_dir, f"{self.symbol}_friday_context.csv")
            historical_data.to_csv(filepath)
            print(f"💾 Contexto viernes guardado: {len(historical_data)} velas")
    
    def load_friday_context(self) -> pd.DataFrame:
        """📂 Carga contexto del viernes"""
        filepath = os.path.join(self.cache_dir, f"{self.symbol}_friday_context.csv")
        if os.path.exists(filepath):
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            print(f"📂 Contexto viernes cargado: {len(df)} velas")
            return df
        return pd.DataFrame()
    
    def save_weekend_buffer(self, weekend_ticks: List[MarketTick]):
        """💾 Guarda buffer de fin de semana"""
        if weekend_ticks:
            data = []
            for tick in weekend_ticks:
                data.append({
                    'timestamp': tick.timestamp,
                    'price': tick.close,
                    'source': tick.source
                })
            
            df = pd.DataFrame(data)
            filepath = os.path.join(self.cache_dir, f"{self.symbol}_weekend_buffer.csv")
            df.to_csv(filepath, index=False)
            print(f"💾 Buffer fin de semana guardado: {len(weekend_ticks)} ticks")

class ScreenPriceTracker:
    """👁️ Tracker thread-safe para modo OTC con Source Tagging"""
    
    def __init__(self, search_region: tuple):
        self.search_region = search_region
        self.last_price = 0.0
        self.last_source = "UNKNOWN"
        self.ocr_config = '--psm 8 -c tessedit_char_whitelist=0123456789.'
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        # Debug captures
        self.debug_dir = "debug_captures"
        os.makedirs(self.debug_dir, exist_ok=True)
        
    def capture_frame(self) -> tuple[Optional[np.ndarray], str]:
        """🎯 Captura frame thread-safe con source tagging"""
        try:
            with mss.mss() as sct:
                monitor = {
                    "top": self.search_region[1],
                    "left": self.search_region[0], 
                    "width": self.search_region[2],
                    "height": self.search_region[3]
                }
                
                screenshot = sct.grab(monitor)
                img_array = np.array(screenshot)
                frame = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
                
                # Guardar imagen de debug
                debug_path = os.path.join(self.debug_dir, "last_seen_price.png")
                cv2.imwrite(debug_path, frame)
                
                return frame, "OCR_LIVE"
                
        except Exception as e:
            print(f"❌ Error captura: {e}")
            return None, "CAPTURE_FAILED"
    
    def process_frame_async(self, frame: np.ndarray, source: str, callback: Callable[[float, str], None]):
        """🔄 Procesa frame async con source"""
        if frame is None:
            callback(0.0, "MOCK_GENERATED")
            return
        
        future = self._executor.submit(self._find_and_read_price, frame, source)
        future.add_done_callback(lambda f: self._on_complete(f, callback))
    
    def _find_and_read_price(self, frame: np.ndarray, source: str) -> tuple[float, str]:
        """🔍 OCR processing con source tracking"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return 0.0, "MOCK_GENERATED"
            
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            if w < 30 or h < 15:
                return 0.0, "MOCK_GENERATED"
            
            price_region = gray[y:y+h, x:x+w]
            price_region = cv2.resize(price_region, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            
            # Guardar región de precio para debug
            debug_path = os.path.join(self.debug_dir, "price_region.png")
            cv2.imwrite(debug_path, price_region)
            
            raw_text = pytesseract.image_to_string(price_region, config=self.ocr_config)
            price = self._parse_price(raw_text)
            
            if price > 0:
                return price, source
            else:
                return 0.0, "MOCK_GENERATED"
            
        except Exception as e:
            print(f"❌ Error OCR: {e}")
            return 0.0, "MOCK_GENERATED"
    
    def _parse_price(self, raw_text: str) -> float:
        """📝 Parse precio"""
        try:
            cleaned = re.sub(r'[^0-9.]', '', raw_text.strip())
            match = re.search(r'(\d+\.\d+)', cleaned)
            
            if match:
                price = float(match.group(1))
                if 0.01 <= price <= 10000.0:
                    return price
            return 0.0
        except:
            return 0.0
    
    def _on_complete(self, future, callback):
        """✅ Callback completion con source"""
        try:
            price, source = future.result()
            self.last_source = source
            if price > 0:
                self.last_price = price
                callback(price, source)
            else:
                # Generar precio mock
                mock_price = self.last_price + np.random.normal(0, 0.0001) if self.last_price > 0 else 1.08450
                callback(mock_price, "MOCK_GENERATED")
        except Exception as e:
            print(f"❌ Error callback: {e}")
            mock_price = 1.08450 + np.random.normal(0, 0.0001)
            callback(mock_price, "MOCK_GENERATED")
    
    def close(self):
        """🔒 Cleanup"""
        self._executor.shutdown(wait=True)

class DataFusionHandler:
    """🔄 Manejador de fusión de datos CSV + Yahoo Finance"""
    
    def leer_precio_csv(self, ruta_csv: str) -> float:
        """📂 Lee el último precio del CSV de manera eficiente"""
        try:
            if not os.path.exists(ruta_csv):
                return 0.0
            
            with open(ruta_csv, 'r', encoding='utf-8') as file:
                # Leer todas las líneas y tomar la última
                lines = file.readlines()
                if len(lines) <= 1:  # Solo header o vacío
                    return 0.0
                
                last_line = lines[-1].strip()
                if last_line:
                    # Parsear CSV: timestamp,price
                    parts = last_line.split(',')
                    if len(parts) >= 2:
                        return float(parts[1])
            
            return 0.0
            
        except (FileNotFoundError, PermissionError, ValueError, IndexError) as e:
            print(f"⚠️ Error leyendo CSV {ruta_csv}: {e}")
            return 0.0
        except Exception as e:
            print(f"❌ Error crítico leyendo CSV: {e}")
            return 0.0
    
    def obtener_contexto_yahoo(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """📊 Descarga contexto de Yahoo Finance"""
        contexto = {'df_1m': pd.DataFrame(), 'df_1h': pd.DataFrame()}
        
        try:
            ticker = yf.Ticker(symbol)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=4)  # 4 horas para obtener suficientes datos
            
            # Obtener velas 1m (últimas 50)
            try:
                hist_1m = ticker.history(
                    start=start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    end=end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    interval='1m'
                )
                if not hist_1m.empty:
                    contexto['df_1m'] = hist_1m.tail(50)
            except Exception as e:
                print(f"⚠️ Error obteniendo 1m para {symbol}: {e}")
            
            # Obtener velas 1h (últimas 50)
            try:
                start_time_1h = end_time - timedelta(days=3)  # 3 días para 1h
                hist_1h = ticker.history(
                    start=start_time_1h.strftime('%Y-%m-%d'),
                    end=end_time.strftime('%Y-%m-%d'),
                    interval='1h'
                )
                if not hist_1h.empty:
                    contexto['df_1h'] = hist_1h.tail(50)
            except Exception as e:
                print(f"⚠️ Error obteniendo 1h para {symbol}: {e}")
                
        except Exception as e:
            print(f"❌ Error conexión Yahoo Finance para {symbol}: {e}")
        
        return contexto
    
    def construir_prompt_contextual(self, precio: float, df_1m: pd.DataFrame, df_1h: pd.DataFrame, symbol: str = "EURUSD") -> Dict:
        """🏗️ Construye JSON contextual para IA"""
        try:
            # Calcular contexto de mercado
            market_context = {
                "trend_1h": "NEUTRAL",
                "volatility_1m": 0.0,
                "last_close_yahoo": 0.0
            }
            
            # Calcular trend 1h si hay datos
            if not df_1h.empty and len(df_1h) >= 2:
                try:
                    first_close = df_1h['Close'].iloc[0]
                    last_close = df_1h['Close'].iloc[-1]
                    if last_close > first_close * 1.001:  # 0.1% threshold
                        market_context["trend_1h"] = "BULLISH"
                    elif last_close < first_close * 0.999:
                        market_context["trend_1h"] = "BEARISH"
                    market_context["last_close_yahoo"] = float(last_close)
                except Exception:
                    pass
            
            # Calcular volatilidad 1m si hay datos
            if not df_1m.empty and len(df_1m) >= 10:
                try:
                    closes = df_1m['Close'].tail(10)
                    volatility = closes.std() / closes.mean() * 100
                    market_context["volatility_1m"] = float(volatility)
                except Exception:
                    pass
            
            # Construir JSON final
            return {
                "symbol": symbol,
                "source": "HYBRID_CSV_API",
                "current_price": float(precio),
                "market_context": market_context
            }
            
        except Exception as e:
            print(f"❌ Error construyendo prompt contextual: {e}")
            return {
                "symbol": symbol,
                "source": "HYBRID_CSV_API",
                "current_price": float(precio),
                "market_context": {
                    "trend_1h": "NEUTRAL",
                    "volatility_1m": 0.0,
                    "last_close_yahoo": 0.0
                }
            }

def obtener_velas(symbol: str, timeframe: str, horas: int = 20) -> pd.DataFrame:
    """📊 Obtiene velas históricas usando yfinance"""
    try:
        # Calcular límites según timeframe
        if timeframe == "1m":
            max_velas = 1200
            interval = "1m"
        elif timeframe == "1h":
            max_velas = 20
            interval = "1h"
        else:
            raise ValueError(f"Timeframe no soportado: {timeframe}")
        
        # Calcular rango de fechas
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=horas)
        
        # Descargar datos de yfinance
        ticker = yf.Ticker(symbol)
        hist_data = ticker.history(
            start=start_time.strftime('%Y-%m-%d'),
            end=end_time.strftime('%Y-%m-%d'),
            interval=interval
        )
        
        if hist_data.empty:
            print(f"📊 {symbol}: 0 velas obtenidas (sin datos disponibles)")
            return pd.DataFrame()
        
        # Limitar cantidad según timeframe
        if len(hist_data) > max_velas:
            hist_data = hist_data.tail(max_velas)
        
        # Preparar DataFrame con columnas obligatorias
        df = pd.DataFrame({
            'timestamp': hist_data.index,
            'open': hist_data['Open'],
            'high': hist_data['High'],
            'low': hist_data['Low'],
            'close': hist_data['Close'],
            'volume': hist_data['Volume']
        })
        
        # Imprimir cantidad obtenida
        print(f"📊 {symbol}: {len(df)} velas obtenidas ({timeframe})")
        
        return df
        
    except Exception as e:
        print(f"❌ Error obteniendo velas para {symbol}: {e}")
        return pd.DataFrame()

class MarketDataStream:
    """🔄 Sistema híbrido con Weekend Survival Mode"""
    
    def __init__(self, symbol: str, search_region: tuple = SEARCH_REGION):
        self.search_region = search_region
        
        # Componentes
        self.price_tracker = ScreenPriceTracker(search_region)
        self.weekend_cache = WeekendCache(symbol)
        self.market_schedule = MarketSchedule()
        
        # Buffers separados (NO mezclar)
        self.historical_buffer = deque(maxlen=1200)  # Solo yfinance
        self.weekend_buffer = deque(maxlen=500)      # Solo OCR
        
        # Estado
        self.running = False
        self.current_price = 0.0
        self.market_mode = "unknown"  # "live", "weekend_otc"
        self.friday_close_price = 0.0
        
        # Threading
        self._lock = threading.Lock()
        self.data_thread = None
        self.callbacks: List[Callable] = []
        
        print(f"🔬 Weekend Survival Mode inicializado para {symbol}")
    
    def add_callback(self, callback: Callable[[MarketTick], None]):
        self.callbacks.append(callback)
    
    def start_stream(self):
        """🚀 Inicia stream híbrido"""
        if self.running:
            return
        
        self.running = True
        self._detect_market_mode()
        
        # Hilo único que maneja ambos modos
        self.data_thread = threading.Thread(target=self._hybrid_data_loop, daemon=True)
        self.data_thread.start()
        
        print(f"🚀 Stream híbrido iniciado - Modo: {self.market_mode}")
    
    def stop_stream(self):
        """⏹️ Detiene stream"""
        self.running = False
        
        if self.data_thread:
            self.data_thread.join(timeout=2)
        
        # Guardar buffer de fin de semana si existe
        if self.market_mode == "weekend_otc" and self.weekend_buffer:
            weekend_ticks = list(self.weekend_buffer)
            self.weekend_cache.save_weekend_buffer(weekend_ticks)
        
        self.price_tracker.close()
        print(f"⏹️ Stream detenido para {self.symbol}")
    
    def _detect_market_mode(self):
        """🔍 Detecta modo de mercado"""
        if self.market_schedule.is_market_open():
            self.market_mode = "live"
            print("📈 MODO: Mercado Real (yfinance)")
        else:
            self.market_mode = "weekend_otc"
            print("🏠 MODO: Weekend OTC (OCR)")
            # Cargar contexto del viernes
            friday_context = self.weekend_cache.load_friday_context()
            if not friday_context.empty:
                self._load_friday_context(friday_context)
    
    def _hybrid_data_loop(self):
        """🔄 Loop híbrido principal"""
        while self.running:
            try:
                if self.market_mode == "live":
                    self._handle_live_market()
                    time.sleep(60)  # Cada minuto para yfinance
                else:
                    self._handle_weekend_otc()
                    time.sleep(5)   # Cada 5s para OCR (menos frecuente)
                    
            except Exception as e:
                print(f"❌ Error en loop híbrido: {e}")
                time.sleep(5)
    
    def _handle_live_market(self):
        """📈 Maneja mercado real"""
        try:
            # Verificar si cambió a fin de semana
            if not self.market_schedule.is_market_open():
                print("🔄 Cambiando a modo Weekend OTC...")
                self.market_mode = "weekend_otc"
                return
            
            # Descargar datos de yfinance
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=20)
            
            ticker = yf.Ticker(self.symbol)
            hist_data = ticker.history(
                start=start_time.strftime('%Y-%m-%d'),
                end=end_time.strftime('%Y-%m-%d'),
                interval='1m'
            )
            
            if not hist_data.empty:
                self._update_historical_buffer(hist_data)
                
                # Si es viernes cerca del cierre, guardar contexto
                if self.market_schedule.is_friday_close():
                    self.weekend_cache.save_friday_context(hist_data)
                    self.friday_close_price = hist_data['Close'].iloc[-1]
                
                print(f"📊 {self.symbol}: Datos live actualizados ({len(hist_data)} velas)")
                
        except Exception as e:
            print(f"❌ Error mercado live: {e}")
    
    def _handle_weekend_otc(self):
        """🏠 Maneja modo OTC fin de semana con source tagging"""
        try:
            # Verificar si volvió el mercado
            if self.market_schedule.is_market_open():
                print("🔄 Cambiando a modo Live...")
                self.market_mode = "live"
                return
            
            # Capturar precio por OCR
            frame, source_tag = self.price_tracker.capture_frame()
            if frame is not None:
                self.price_tracker.process_frame_async(frame, source_tag, self._on_weekend_price)
            else:
                # Generar precio mock si falla captura
                mock_price = self.current_price + np.random.normal(0, 0.0001) if self.current_price > 0 else 1.08450
                self._on_weekend_price(mock_price, "MOCK_GENERATED")
                
        except Exception as e:
            print(f"❌ Error modo OTC: {e}")
            # Fallback a mock
            mock_price = 1.08450 + np.random.normal(0, 0.0001)
            self._on_weekend_price(mock_price, "MOCK_GENERATED")
    
    def _on_weekend_price(self, price: float, source_tag: str):
        """🎯 Callback precio fin de semana con source tagging"""
        with self._lock:
            self.current_price = price
            
            # Log honesto con source tag
            source_emoji = {
                "OCR_LIVE": "👁️",
                "CACHE_FRIDAY": "💾", 
                "MOCK_GENERATED": "⚠️"
            }.get(source_tag, "❓")
            
            print(f"💰 PRECIO: {price:.5f} | 🏷️ ORIGEN: [{source_tag}] {source_emoji}")
            
            # Crear tick OTC con source tag
            weekend_tick = MarketTick(
                symbol=self.symbol,
                timestamp=datetime.now(),
                open=price,
                high=price,
                low=price,
                close=price,
                volume=1,
                source="ocr" if source_tag == "OCR_LIVE" else "mock",
                data_source_tag=source_tag
            )
            
            self.weekend_buffer.append(weekend_tick)
            
            # Notificar callbacks
            for callback in self.callbacks:
                try:
                    callback(weekend_tick)
                except Exception as e:
                    print(f"Error callback: {e}")
    
    def _update_historical_buffer(self, hist_data: pd.DataFrame):
        """📊 Actualiza buffer histórico (solo yfinance)"""
        with self._lock:
            self.historical_buffer.clear()
            
            for timestamp, row in hist_data.iterrows():
                tick = MarketTick(
                    symbol=self.symbol,
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']) if not pd.isna(row['Volume']) else 1000,
                    source="yfinance"
                )
                self.historical_buffer.append(tick)
            
            self.current_price = hist_data['Close'].iloc[-1]
    
    def _load_friday_context(self, friday_df: pd.DataFrame):
        """📂 Carga contexto del viernes con source tagging"""
        with self._lock:
            self.historical_buffer.clear()
            
            for timestamp, row in friday_df.iterrows():
                tick = MarketTick(
                    symbol=self.symbol,
                    timestamp=pd.to_datetime(timestamp),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']),
                    source="friday_cache",
                    data_source_tag="CACHE_FRIDAY"
                )
                self.historical_buffer.append(tick)
            
            self.friday_close_price = friday_df['close'].iloc[-1]
            print(f"💰 PRECIO VIERNES: {self.friday_close_price:.5f} | 🏷️ ORIGEN: [CACHE_FRIDAY] 💾")
    
    def get_current_data(self) -> pd.DataFrame:
        """📊 Obtiene datos para análisis (SEPARADOS)"""
        with self._lock:
            if not self.historical_buffer:
                return pd.DataFrame()
            
            # Solo retornar datos históricos (NO mezclar con OCR)
            data = []
            for tick in self.historical_buffer:
                data.append({
                    'timestamp': tick.timestamp,
                    'open': tick.open,
                    'high': tick.high,
                    'low': tick.low,
                    'close': tick.close,
                    'volume': tick.volume,
                    'source': tick.source
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            return df
    
    def get_weekend_context(self) -> Dict:
        """🏠 Obtiene contexto específico de fin de semana"""
        with self._lock:
            weekend_prices = [tick.close for tick in self.weekend_buffer]
            
            return {
                'market_mode': self.market_mode,
                'current_price': self.current_price,
                'friday_close': self.friday_close_price,
                'weekend_prices': weekend_prices[-10:],  # Últimos 10 precios
                'weekend_count': len(self.weekend_buffer)
            }
    
    def get_latest_candles(self, count: int = 15) -> List[Dict]:
        """📈 Últimas velas (solo históricas)"""
        df = self.get_current_data()
        if df.empty:
            return []
        
        latest_data = df.tail(count)
        return [
            {
                'timestamp': idx.isoformat(),
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'source': row['source']
            }
            for idx, row in latest_data.iterrows()
        ]
    
    def get_buffer_status(self) -> Dict:
        """📊 Estado del sistema híbrido"""
        with self._lock:
            return {
                'symbol': self.symbol,
                'market_mode': self.market_mode,
                'historical_size': len(self.historical_buffer),
                'weekend_size': len(self.weekend_buffer),
                'current_price': self.current_price,
                'friday_close': self.friday_close_price,
                'is_market_open': self.market_schedule.is_market_open()
            }