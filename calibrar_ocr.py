#!/usr/bin/env python3
"""
🎯 CALIBRADOR OCR - Ajusta coordenadas para captura precisa
"""

import cv2
import numpy as np
import mss
import pytesseract
import tkinter as tk
from tkinter import messagebox
import re

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRCalibrator:
    def __init__(self):
        self.current_region = (1560, 520, 90, 40)  # x, y, width, height
        self.root = tk.Tk()
        self.root.title("🎯 Calibrador OCR - IQ Option")
        self.root.geometry("400x300")
        
        # Variables
        self.x_var = tk.IntVar(value=self.current_region[0])
        self.y_var = tk.IntVar(value=self.current_region[1])
        self.w_var = tk.IntVar(value=self.current_region[2])
        self.h_var = tk.IntVar(value=self.current_region[3])
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz"""
        tk.Label(self.root, text="🎯 Calibrador OCR", font=("Arial", 16)).pack(pady=10)
        
        # Coordenadas
        frame = tk.Frame(self.root)
        frame.pack(pady=10)
        
        tk.Label(frame, text="X:").grid(row=0, column=0)
        tk.Entry(frame, textvariable=self.x_var, width=8).grid(row=0, column=1)
        
        tk.Label(frame, text="Y:").grid(row=0, column=2)
        tk.Entry(frame, textvariable=self.y_var, width=8).grid(row=0, column=3)
        
        tk.Label(frame, text="Width:").grid(row=1, column=0)
        tk.Entry(frame, textvariable=self.w_var, width=8).grid(row=1, column=1)
        
        tk.Label(frame, text="Height:").grid(row=1, column=2)
        tk.Entry(frame, textvariable=self.h_var, width=8).grid(row=1, column=3)
        
        # Botones
        tk.Button(self.root, text="📸 Capturar y Probar", command=self.test_capture, bg="lightblue").pack(pady=5)
        tk.Button(self.root, text="💾 Guardar Coordenadas", command=self.save_coordinates, bg="lightgreen").pack(pady=5)
        tk.Button(self.root, text="🔄 Resetear", command=self.reset_coordinates, bg="orange").pack(pady=5)
        
        # Resultado
        self.result_label = tk.Label(self.root, text="Resultado aparecerá aquí", wraplength=350)
        self.result_label.pack(pady=10)
    
    def capture_screen(self):
        """Captura la región especificada"""
        try:
            x, y, w, h = self.x_var.get(), self.y_var.get(), self.w_var.get(), self.h_var.get()
            
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": w, "height": h}
                screenshot = sct.grab(monitor)
                img_array = np.array(screenshot)
                frame = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
                
            return frame
        except Exception as e:
            messagebox.showerror("Error", f"Error capturando pantalla: {e}")
            return None
    
    def process_ocr(self, frame):
        """Procesa OCR en el frame"""
        try:\n            # Convertir a escala de grises\n            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)\n            \n            # Aplicar threshold\n            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)\n            \n            # Redimensionar para mejor OCR\n            resized = cv2.resize(thresh, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)\n            \n            # OCR\n            config = '--psm 8 -c tessedit_char_whitelist=0123456789.'\n            raw_text = pytesseract.image_to_string(resized, config=config)\n            \n            # Limpiar texto\n            cleaned = re.sub(r'[^0-9.]', '', raw_text.strip())\n            \n            # Buscar patrón de precio\n            match = re.search(r'(\\d+\\.\\d+)', cleaned)\n            if match:\n                price = float(match.group(1))\n                if 1.0 <= price <= 2.0:  # Rango válido para EURUSD\n                    return price, \"✅ VÁLIDO\"\n                else:\n                    return price, \"⚠️ FUERA DE RANGO\"\n            else:\n                return 0.0, f\"❌ NO DETECTADO: '{cleaned}'\"\n                \n        except Exception as e:\n            return 0.0, f\"❌ ERROR: {e}\"\n    \n    def test_capture(self):\n        \"\"\"Prueba la captura actual\"\"\"\n        frame = self.capture_screen()\n        if frame is not None:\n            price, status = self.process_ocr(frame)\n            \n            result_text = f\"Precio detectado: {price}\\nEstado: {status}\"\n            self.result_label.config(text=result_text)\n            \n            # Guardar imagen de debug\n            cv2.imwrite(\"debug_capture.png\", frame)\n            print(f\"🔍 Debug: Imagen guardada como debug_capture.png\")\n    \n    def save_coordinates(self):\n        \"\"\"Guarda las coordenadas al archivo\"\"\"\n        try:\n            x, y, w, h = self.x_var.get(), self.y_var.get(), self.w_var.get(), self.h_var.get()\n            \n            config_content = f'''\"\"\"\\n📍 COORDENADAS IQ OPTION - CONFIGURACIÓN OCR\\nResponsabilidad: Configuración de coordenadas para captura de precios\\n\"\"\"\\n\\n# Región de búsqueda por defecto (x, y, width, height)\\nSEARCH_REGION = ({x}, {y}, {w}, {h})\\n\\n# Configuración OCR\\nOCR_CONFIG = {{\\n    'lang': 'eng',\\n    'oem': 3,\\n    'psm': 8,\\n    'config': '--psm 8 -c tessedit_char_whitelist=0123456789.'\\n}}\\n\\n# Directorio para debug (opcional)\\nDEBUG_DIR = \"debug_ocr\"'''\n            \n            with open(\"coordenadas_iq_option.py\", \"w\") as f:\n                f.write(config_content)\n            \n            messagebox.showinfo(\"Éxito\", f\"Coordenadas guardadas:\\nX: {x}, Y: {y}, W: {w}, H: {h}\")\n            \n        except Exception as e:\n            messagebox.showerror(\"Error\", f\"Error guardando: {e}\")\n    \n    def reset_coordinates(self):\n        \"\"\"Resetea a coordenadas por defecto\"\"\"\n        self.x_var.set(1560)\n        self.y_var.set(520)\n        self.w_var.set(90)\n        self.h_var.set(40)\n        self.result_label.config(text=\"Coordenadas reseteadas\")\n    \n    def run(self):\n        \"\"\"Ejecuta el calibrador\"\"\"\n        self.root.mainloop()\n\nif __name__ == \"__main__\":\n    print(\"🎯 Iniciando Calibrador OCR...\")\n    print(\"📋 Instrucciones:\")\n    print(\"   1. Abre IQ Option y ve al gráfico EURUSD\")\n    print(\"   2. Ajusta las coordenadas X, Y, Width, Height\")\n    print(\"   3. Haz clic en 'Capturar y Probar'\")\n    print(\"   4. Si el precio se detecta correctamente, guarda\")\n    \n    calibrator = OCRCalibrator()\n    calibrator.run()