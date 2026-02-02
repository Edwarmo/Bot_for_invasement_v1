# Capturador de Precios Dinámicos

Aplicación Python con arquitectura en capas para capturar y analizar precios dinámicos desde pantalla.

## Estructura del Proyecto

```
capturador/
├── main.py              # Presentation Layer - Punto de entrada
├── application.py       # Application Layer - Lógica de negocio
├── price.py            # Domain Layer - Modelo Price
├── infrastructure.py   # Infrastructure Layer - Servicios externos
├── config.py           # Configuración
├── requirements.txt    # Dependencias
├── prices.csv          # Datos capturados (GENERADO)
├── simple_capture.py   # Versión de prueba (OPCIONAL)
└── README.md          # Documentación
```

## Instalación

### 1. Instalar Tesseract OCR

**Windows:**
- Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
- Instalar en: `C:\Program Files\Tesseract-OCR\`

### 2. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

### Salida esperada:
```
=== Capturador de Precios Dinámicos ===
Iniciando captura continua de precios...
OCR RAW >>> ' 1.2345\n'
PRECIO: 1.2345 | 10:45:12 | Guardado en CSV
```

## Archivos Generados

### 📄 `prices.csv`
Contiene todos los precios capturados con timestamp:
```csv
timestamp,price
2026-02-02T10:59:08.203105,1.190985
2026-02-02T10:59:11.296214,1.191165
```

## 🗑️ Limpieza de Archivos

### Archivos para borrar (opcionales):

```bash
# Archivo de prueba (ya no necesario)
del simple_capture.py

# Datos capturados (si quieres empezar limpio)
del prices.csv

# Archivos de configuración alternativos
del requirements-alt.txt
```

### Comando de limpieza completa:
```bash
del simple_capture.py prices.csv requirements-alt.txt
```

## Archivos Principales (NO BORRAR)

- `main.py` - Punto de entrada
- `application.py` - Lógica de negocio  
- `price.py` - Modelo de datos
- `infrastructure.py` - Servicios
- `config.py` - Configuración
- `requirements.txt` - Dependencias
- `README.md` - Documentación

## Troubleshooting

### Error: "Tesseract not found"
- Verificar instalación en `C:\Program Files\Tesseract-OCR\`
- Ajustar ruta en `infrastructure.py` si es necesario

### Error: "No se detecta precio"
- Verificar que la región ROI sea correcta
- Comprobar que hay contraste suficiente en la imagen