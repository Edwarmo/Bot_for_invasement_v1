"""
📍 COORDENADAS IQ OPTION - CONFIGURACIÓN OCR
Responsabilidad: Coordenadas calibradas para captura de precios
"""

# 🎯 REGIÓN DE BÚSQUEDA PRINCIPAL
SEARCH_REGION = (1560, 520, 90, 40)  # (x, y, width, height)

# 🔧 CONFIGURACIÓN OCR
OCR_CONFIG = '--psm 8 -c tessedit_char_whitelist=0123456789.'

# 📁 DIRECTORIO DE DEBUG
DEBUG_DIR = "debug_captures"

# 📊 CONFIGURACIONES ADICIONALES
PRICE_THRESHOLD_MIN = 0.01
PRICE_THRESHOLD_MAX = 10000.0
CAPTURE_INTERVAL = 5  # segundos

print(f"📍 Coordenadas cargadas: {SEARCH_REGION}")