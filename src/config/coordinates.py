"""
📍 COORDENATES CONFIG
Responsabilidad: Configuración de coordenadas para OCR
"""

# Región de búsqueda por defecto (x, y, width, height)
SEARCH_REGION = (1560, 520, 90, 40)

# Configuración OCR
OCR_CONFIG = {
    'lang': 'eng',
    'oem': 3,
    'psm': 8,
    'config': '--psm 8 -c tessedit_char_whitelist=0123456789.'
}

# Directorio para debug
DEBUG_DIR = "debug_ocr"
