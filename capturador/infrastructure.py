import cv2
import numpy as np
import pytesseract
import pyautogui
from PIL import Image
import os
import csv
from datetime import datetime
import re

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ScreenCapture:
    """Maneja la captura de pantalla en región específica"""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.roi = (x, y, width, height)
        pyautogui.FAILSAFE = False
    
    def capture_roi(self) -> np.ndarray:
        """Captura la región de interés"""
        try:
            x, y, width, height = self.roi
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            img_array = np.array(screenshot)
            return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        except Exception:
            return None

class ImageProcessor:
    """Procesa imágenes usando lógica de simple_capture"""
    
    @staticmethod
    def detect_white_label(image: np.ndarray):
        """Detecta la etiqueta blanca usando threshold"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest = max(contours, key=cv2.contourArea)
            return cv2.boundingRect(largest)
        return None
    
    @staticmethod
    def preprocess_for_ocr(image: np.ndarray, bbox):
        """Extrae región del texto"""
        x, y, w, h = bbox
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray[y:y+h, x:x+w]

class OCRService:
    """Servicio de OCR optimizado"""
    
    def __init__(self):
        self.config = '--psm 7 -c tessedit_char_whitelist=0123456789.'
    
    def extract_text(self, image: np.ndarray) -> str:
        """Extrae texto usando OCR"""
        try:
            pil_image = Image.fromarray(image)
            text = pytesseract.image_to_string(pil_image, config=self.config)
            return text.strip()
        except Exception:
            return ""
    
    @staticmethod
    def extract_price(text: str):
        """Extrae precio usando regex"""
        match = re.search(r"\d+(\.\d+)?", text.replace(",", "."))
        if match:
            return float(match.group())
        return None

class CSVRepository:
    """Maneja la persistencia en archivo CSV"""
    
    def __init__(self, filename: str = "prices.csv"):
        self.filename = filename
        self._initialize_file()
    
    def _initialize_file(self):
        """Inicializa el archivo CSV con headers si no existe"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['timestamp', 'price'])
    
    def save_price(self, price_value: float, timestamp: datetime):
        """Guarda un precio en el CSV"""
        try:
            with open(self.filename, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([timestamp.isoformat(), price_value])
        except Exception:
            pass