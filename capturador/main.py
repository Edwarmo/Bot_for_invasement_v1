#!/usr/bin/env python3
"""
Capturador de Precios - CLONADO de app_laern_how_to_get_price/simple_capture.py
"""

import os
import sys
import time
import re
import signal
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import cv2
import pyautogui
import pytesseract
import pandas as pd

# =====================
# CONFIGURACION - Exacta de simple_capture.py
# =====================
ROI_X = 1534
ROI_Y = 318
ROI_WIDTH = 231
ROI_HEIGHT = 532

ROI_CONFIG = {
    'x': ROI_X,
    'y': ROI_Y, 
    'width': ROI_WIDTH,
    'height': ROI_HEIGHT
}

# OCR Config - EXACTA de simple_capture.py
OCR_CONFIG = '--psm 7 -c tessedit_char_whitelist=0123456789.'

# Threshold para detectar area blanca
WHITE_THRESHOLD = 200

# Intervalo de captura
CAPTURE_INTERVAL = 5

# Rutas
CAPTURADOR_DIR = Path(__file__).parent
PRICES_CSV = CAPTURADOR_DIR / "prices.csv"
DEBUG_DIR = CAPTURADOR_DIR.parent / "tr__shh"
DEBUG_DIR.mkdir(exist_ok=True)

# Log
LOG_FILE = DEBUG_DIR / "debug.log"

# =====================
# LOGGING
# =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PriceCapture:
    """Capturador de precios con OCR - LOGICA EXACTA DE simple_capture.py"""
    
    def __init__(self):
        self.running = False
        self.capture_count = 0
        
        # Configurar pyautogui
        pyautogui.FAILSAFE = False
        
        # Configurar tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        logger.info("Inicializado capturador de precios")
        logger.info(f"ROI: {ROI_CONFIG}")
        logger.info(f"CSV: {PRICES_CSV}")
    
    def capturar_roi(self) -> np.ndarray:
        """Captura la region de interes"""
        try:
            screenshot = pyautogui.screenshot(region=(ROI_X, ROI_Y, ROI_WIDTH, ROI_HEIGHT))
            img_array = np.array(screenshot)
            roi_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            return roi_img
        except Exception as e:
            logger.error(f"Error capturando ROI: {e}")
            return None
    
    def validar_dimensiones(self, img: np.ndarray) -> bool:
        """Valida las dimensiones de la imagen"""
        if img is None:
            return False
        
        h, w = img.shape[:2]
        if w == ROI_WIDTH and h == ROI_HEIGHT:
            return True
        else:
            logger.warning(f"Dimensiones incorrectas: {w}x{h} (esperado: {ROI_WIDTH}x{ROI_HEIGHT})")
            return False
    
    def procesar_ocr(self, roi_img: np.ndarray) -> str:
        """
        LOGICA EXACTA DE simple_capture.py:
        1. Convertir a escala de grises
        2. Threshold 200 para encontrar areas blancas
        3. Encontrar contornos y tomar el mayor
        4. Extraer region del bounding box en ESCALA DE GRISES
        5. Aplicar OCR a la region en gris (NO threshold)
        """
        try:
            # 1. Convertir a escala de grises
            gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
            
            # 2. Threshold 200 para detectar areas blancas (el recuadro del precio)
            _, thresh = cv2.threshold(gray, WHITE_THRESHOLD, 255, cv2.THRESH_BINARY)
            
            # 3. Encontrar contornos
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                logger.warning("No se detecto recuadro")
                return ""
            
            # 4. Tomar el contorno mas grande (el precio)
            largest = max(contours, key=cv2.contourArea)
            x_box, y_box, w_box, h_box = cv2.boundingRect(largest)
            
            # 5. Extraer region del texto en ESCALA DE GRISES (NO threshold)
            text_region = gray[y_box:y_box+h_box, x_box:x_box+w_box]
            
            # 6. Aplicar OCR a la region en gris
            text = pytesseract.image_to_string(text_region, config=OCR_CONFIG)
            
            logger.info(f"OCR RAW >>> {repr(text)}")
            
            # 7. Extraer precio con regex - buscar TODOS los numeros y elegir el mejor
            # Reemplazar comas por puntos y limpiar
            cleaned = text.replace(",", ".").strip()
            
            # Buscar todos los numeros decimales
            all_matches = re.findall(r"\d+\.\d+", cleaned)
            
            if all_matches:
                # Preferir el numero con mas decimales (mas preciso)
                best_price = max(all_matches, key=lambda x: len(x.split('.')[-1]))
                
                # VALIDAR: solo aceptar si tiene al menos 4 decimales (precio valido tipo 1.1923)
                decimal_part = best_price.split('.')[-1]
                if len(decimal_part) >= 4:
                    logger.info(f"PRECIO: {best_price}")
                    return best_price
                else:
                    logger.warning(f"Precio muy corto, probable error OCR: {best_price}")
                    return ""
            
            # Si no hay decimales, buscar entero simple (fallback)
            # Pero SOLO si es un numero de al menos 3 digitos (descartar "4")
            match = re.search(r"\d{3,}", cleaned)
            if match:
                price = match.group()
                logger.info(f"PRECIO (entero): {price}")
                return price
            
            logger.warning("No se detecto precio valido (probable error OCR)")
            return ""
            
        except Exception as e:
            logger.error(f"Error en OCR: {e}")
            return ""
    
    def guardar_csv(self, precio: str):
        """Guarda el precio en el CSV"""
        if not precio:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            linea = f"{timestamp},{precio}\n"
            
            with open(PRICES_CSV, 'a', encoding='utf-8') as f:
                f.write(linea)
            
            logger.info(f"Guardado: {precio}")
            
        except Exception as e:
            logger.error(f"Error guardando CSV: {e}")
    
    def guardar_debug(self, roi_img: np.ndarray, precio: str):
        """Guarda imagen de debug"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = DEBUG_DIR / f"debug_{timestamp}_{precio}.png"
        cv2.imwrite(str(filename), roi_img)
    
    def capturar(self) -> bool:
        """Ejecuta una captura"""
        self.capture_count += 1
        
        roi_img = self.capturar_roi()
        
        if roi_img is None:
            logger.warning(f"Captura {self.capture_count}: Error en captura")
            return False
        
        if not self.validar_dimensiones(roi_img):
            logger.warning(f"Captura {self.capture_count}: Dimensiones incorrectas")
            return False
        
        precio = self.procesar_ocr(roi_img)
        
        if not precio:
            logger.warning(f"Captura {self.capture_count}: Sin precio detectado")
            return False
        
        self.guardar_csv(precio)
        self.guardar_debug(roi_img, precio)
        
        logger.info(f"Captura {self.capture_count}: {precio}")
        return True
    
    def iniciar(self):
        """Inicia el loop de captura"""
        self.running = True
        
        def signal_handler(sig, frame):
            print("\nSenyal de parada recibida")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        
        logger.info("Iniciando loop de captura...")
        logger.info(f"Intervalo: {CAPTURE_INTERVAL}s")
        logger.info("Presiona Ctrl+C para detener")
        
        while self.running:
            try:
                self.capturar()
                time.sleep(CAPTURE_INTERVAL)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error en loop: {e}")
                time.sleep(CAPTURE_INTERVAL)
        
        logger.info("Capturador detenido")


def main():
    """Funcion principal"""
    print("=" * 60)
    print("CAPTURADOR DE PRECIOS - CLONADO DE simple_capture.py")
    print("=" * 60)
    
    capturador = PriceCapture()
    capturador.iniciar()


if __name__ == "__main__":
    main()
