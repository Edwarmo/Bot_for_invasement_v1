# 🏛️ DSS TRADING SYSTEM v2.0

## 📋 DESCRIPCIÓN

**Sistema de Soporte a la Decisión (DSS)** para trading cuantitativo con arquitectura modular basada en Clean Architecture.

## 🎯 CARACTERÍSTICAS

- **Captura de precios** en tiempo real (OCR)
- **Contexto macro** con Yahoo Finance
- **Inteligencia artificial** local (LM Studio)
- **Alertas GUI** con human-in-the-loop

## 📁 ESTRUCTURA DEL PROYECTO

```
Bot_for_invasement_v1/
├── 📁 src/                          # Código fuente principal
│   ├── __init__.py
│   ├── main.py                      # Punto de entrada
│   │
│   ├── 📁 domain/                   # Entidades y reglas de negocio
│   │   ├── __init__.py
│   │   └── prediction.py            # PredictionTracker
│   │
│   ├── 📁 data/                     # Acceso a datos
│   │   ├── __init__.py
│   │   ├── market_stream.py        # DataFusionHandler
│   │   └── price_capture.py         # OCR + Screen capture
│   │
│   ├── 📁 services/                 # Casos de uso
│   │   ├── __init__.py
│   │   ├── ai_client.py            # LM Studio
│   │   ├── alerts.py               # GUI de alertas
│   │   └── indicators.py           # RSI, Bollinger
│   │
│   └── 📁 config/                   # Configuración
│       ├── __init__.py
│       └── coordinates.py           # Coordenadas OCR
│
├── 📁 tools/                        # Herramientas
│   ├── test_momentum_system.py
│   ├── test_lm_studio.py
│   ├── calibrar_ocr.py
│   ├── diagnostico.py
│   └── fix_csv_data.py
│
├── 📁 cache/                        # Cache
│   └── weekend_cache/
│
├── capturador/
│   └── prices.csv
│
├── requirements.txt
└── README.md
```

## 🚀 USO

### Sistema Principal:
```bash
python src/main.py
```

### Herramientas:
```bash
python tools/test_momentum_system.py
python tools/test_lm_studio.py
python tools/calibrar_ocr.py
```

## 📦 DEPENDENCIAS

```bash
pip install -r requirements.txt
```

## 🔧 CONFIGURACIÓN

- **LM Studio**: Puerto 1234
- **CSV**: `capturador/prices.csv`
- **Símbolo**: `EURUSD=X`

## 📄 LICENCIA

Solo fines educativos.
