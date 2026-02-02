# Configuración del Capturador de Precios

## ROI (Región de Interés)
ROI_X = 1534
ROI_Y = 318
ROI_WIDTH = 231
ROI_HEIGHT = 532

## Timing
CAPTURE_INTERVAL = 2.5  # segundos entre capturas
MAX_MEMORY_PRICES = 1000  # límite de precios en memoria

## OCR Configuración
TESSERACT_CONFIG = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.,'
WHITE_THRESHOLD = 200  # umbral para detectar áreas blancas
MIN_CONTOUR_WIDTH = 20  # ancho mínimo de contorno válido
MIN_CONTOUR_HEIGHT = 10  # alto mínimo de contorno válido

## Procesamiento de imagen
SCALE_FACTOR = 3  # factor de escalado para OCR
BINARY_THRESHOLD = 127  # umbral para binarización

## Archivos
CSV_FILENAME = "prices.csv"