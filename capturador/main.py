#!/usr/bin/env python3
"""
Capturador de Precios Dinámicos
Aplicación con arquitectura en capas para capturar y analizar precios desde pantalla
"""

from application import PriceCaptureController

def main():
    """Punto de entrada principal"""
    
    # Configuración de la región de interés (ROI)
    ROI_CONFIG = {
        'x': 1534,
        'y': 318, 
        'width': 231,
        'height': 532
    }
    
    # Intervalo entre capturas (2-3 segundos)
    CAPTURE_INTERVAL = 2.5
    
    print("=== Capturador de Precios Dinámicos ===")
    print("Arquitectura en capas con lógica de simple_capture")
    print()
    
    try:
        # Crear controlador
        controller = PriceCaptureController(
            roi_config=ROI_CONFIG,
            interval=CAPTURE_INTERVAL
        )
        
        # Iniciar captura continua
        controller.start_continuous_capture()
        
    except Exception as e:
        print(f"Error crítico: {e}")
        print("Verifica que:")
        print("- Tesseract esté instalado en C:\\Program Files\\Tesseract-OCR\\")
        print("- Las librerías estén instaladas: pip install -r requirements.txt")

if __name__ == "__main__":
    main()