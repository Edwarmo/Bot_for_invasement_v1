import time
from typing import List, Optional
from datetime import datetime

from price import Price
from infrastructure import ScreenCapture, ImageProcessor, OCRService, CSVRepository

class PriceCaptureService:
    """Servicio principal de captura usando lógica de simple_capture"""
    
    def __init__(self, x: int, y: int, width: int, height: int, interval: float = 2.5):
        self.screen_capture = ScreenCapture(x, y, width, height)
        self.image_processor = ImageProcessor()
        self.ocr_service = OCRService()
        self.csv_repository = CSVRepository()
        self.interval = interval
        self.prices_in_memory: List[Price] = []
    
    def capture_and_analyze_once(self) -> Optional[Price]:
        """Ejecuta un ciclo de captura usando lógica simple_capture"""
        # Capturar imagen
        image = self.screen_capture.capture_roi()
        if image is None:
            return None
        
        # Detectar etiqueta blanca
        bbox = self.image_processor.detect_white_label(image)
        if bbox is None:
            return None
        
        # Extraer región del texto
        text_region = self.image_processor.preprocess_for_ocr(image, bbox)
        
        # Aplicar OCR
        text = self.ocr_service.extract_text(text_region)
        print("OCR RAW >>>", repr(text))
        
        # Extraer precio
        price_value = self.ocr_service.extract_price(text)
        if price_value is not None:
            price = Price(value=price_value, timestamp=datetime.now())
            
            # Guardar en memoria y CSV
            self.prices_in_memory.append(price)
            self.csv_repository.save_price(price.value, price.timestamp)
            
            return price
        
        return None
    
    def get_price_count(self) -> int:
        return len(self.prices_in_memory)

class PriceCaptureController:
    """Controlador principal del ciclo de captura"""
    
    def __init__(self, roi_config: dict, interval: float = 2.5):
        self.service = PriceCaptureService(
            x=roi_config['x'],
            y=roi_config['y'], 
            width=roi_config['width'],
            height=roi_config['height'],
            interval=interval
        )
        self.running = False
    
    def start_continuous_capture(self):
        """Inicia el ciclo continuo de captura"""
        self.running = True
        print("Iniciando captura continua de precios...")
        print(f"ROI: {self.service.screen_capture.roi}")
        print(f"Intervalo: {self.service.interval}s")
        print("Presiona Ctrl+C para detener")
        print("=" * 50)
        
        try:
            while self.running:
                price = self.service.capture_and_analyze_once()
                
                if price is not None:
                    print(f"PRECIO: {price.value} | {price.timestamp.strftime('%H:%M:%S')} | Guardado en CSV")
                else:
                    print("No se detectó precio")
                
                time.sleep(self.service.interval)
                    
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Detiene el ciclo de captura"""
        self.running = False
        total_prices = self.service.get_price_count()
        print(f"\nCaptura detenida. Total de precios capturados: {total_prices}")
        print("Datos guardados en prices.csv")