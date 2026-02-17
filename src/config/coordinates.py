"""
📍 COORDENATES CONFIG
Responsabilidad: Configuración de coordenadas para OCR
"""

# Nueva Región de búsqueda (ROI) actualizada
ROI_CONFIG = {
    'x': 1534,
    'y': 318, 
    'width': 231,
    'height': 532
}

# Alias para compatibilidad
SEARCH_REGION = (
    ROI_CONFIG['x'],
    ROI_CONFIG['y'],
    ROI_CONFIG['width'],
    ROI_CONFIG['height']
)

# Configuración OCR
OCR_CONFIG = {
    'lang': 'eng',
    'oem': 3,
    'psm': 7,
    'config': '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.,$'
}

# Directorio para debug
DEBUG_DIR = "tr__shh"

# Intervalo de captura (segundos)
CAPTURE_INTERVAL = 5
