import cv2
import numpy as np
import pytesseract
import pyautogui
import time
import re
from datetime import datetime

# Especificar ruta de Tesseract si no está en PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def capture_and_process():
    """Captura, procesa y muestra precio directamente"""
    
    # ROI Config
    x, y, width, height = 1534, 318, 231, 532
    
    print("=== Capturador Simple ===")
    print("Presiona Ctrl+C para detener")
    print("-" * 30)
    
    try:
        while True:
            # Capturar región
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            image = np.array(screenshot)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detectar áreas blancas (recuadro verde contendrá texto blanco/negro)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Tomar el contorno más grande
                largest = max(contours, key=cv2.contourArea)
                x_box, y_box, w_box, h_box = cv2.boundingRect(largest)
                
                # Extraer región del texto
                text_region = gray[y_box:y_box+h_box, x_box:x_box+w_box]
                
                # Aplicar OCR
                config = '--psm 7 -c tessedit_char_whitelist=0123456789.'
                text = pytesseract.image_to_string(text_region, config=config)
                
                print("OCR RAW >>>", repr(text))
                
                # Extraer precio
                match = re.search(r"\d+(\.\d+)?", text.replace(",", "."))
                if match:
                    price = float(match.group())
                    print(f"PRECIO: {price} | {datetime.now().strftime('%H:%M:%S')}")
                else:
                    print("No se detectó precio")
            else:
                print("No se detectó recuadro")
            
            time.sleep(2.5)
            
    except KeyboardInterrupt:
        print("\nCaptura detenida")

if __name__ == "__main__":
    capture_and_process()