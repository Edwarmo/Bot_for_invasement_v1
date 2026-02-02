# 🏛️ DSS TRADING SYSTEM - FUSIÓN DE DATOS

## 📋 DESCRIPCIÓN DEL PROYECTO

**Sistema de Soporte a la Decisión (DSS)** para trading cuantitativo con arquitectura híbrida que combina:
- **Fusión de datos CSV + Yahoo Finance** para análisis contextual
- **Visión artificial OpenCV** para captura de precios en tiempo real
- **Inteligencia artificial local** (LM Studio) para validación de señales
- **Interfaz humana obligatoria** para cumplimiento regulatorio

## 🎯 ESTADO ACTUAL

### ✅ **FUNCIONALIDADES IMPLEMENTADAS:**
- ✅ **Fusión de datos híbrida**: CSV + Yahoo Finance + OCR
- ✅ **Motor de IA actualizado**: Compatible con nueva arquitectura
- ✅ **Sistema de testing**: Validación automática de integración
- ✅ **Capturador externo**: Sistema independiente de precios
- ✅ **Análisis técnico completo**: RSI, EMA, Bollinger Bands
- ✅ **Interfaz de alertas**: Sistema thread-safe con temporizador

### 🔄 **ARQUITECTURA ACTUAL:**

```
📂 MAIN.PY (Nuevo Sistema de Fusión)
    ↓
📊 DataFusionHandler (CAPA 1)
    ├── CSV Reader (capturador/prices.csv)
    ├── Yahoo Finance API (contexto histórico)
    └── Data Fusion (combinación inteligente)
    ↓
🤖 LMStudioClient (CAPA 3)
    ├── System Prompt optimizado
    ├── Formateo híbrido de datos
    └── Respuestas JSON estructuradas
```

## 🚀 INSTALACIÓN Y USO

### **1. Dependencias:**
```bash
pip install -r requirements.txt
```

### **2. Configuración LM Studio:**
- Instalar LM Studio desde https://lmstudio.ai/
- Cargar modelo de lenguaje (recomendado: Llama 3.2 3B)
- Iniciar servidor local en puerto 1234

### **3. Ejecución:**

#### **Sistema Principal (Fusión de Datos):**
```bash
python main.py
```

#### **Test de Integración:**
```bash
python test_data_fusion.py
```

#### **Capturador Independiente:**
```bash
cd capturador
python main.py
```

## 📁 ESTRUCTURA DE ARCHIVOS

### **🟢 ARCHIVOS PRINCIPALES (MANTENER):**

#### **Core System:**
- `main.py` - Sistema principal de fusión de datos
- `test_data_fusion.py` - Testing de integración
- `requirements.txt` - Dependencias del proyecto

#### **CAPA 1 - Datos:**
- `CAPA 1/market_data_stream.py` - Fusión híbrida + OCR + Yahoo Finance
- `capturador/` - Sistema independiente de captura de precios

#### **CAPA 2 - Análisis:**
- `CAPA 2/technical_analyzer.py` - Indicadores técnicos completos

#### **CAPA 3 - IA:**
- `CAPA 3/ai_inference_engine.py` - Cliente LM Studio actualizado

#### **CAPA 6 - Interfaz:**
- `CAPA 6/alert_interface.py` - Sistema de alertas thread-safe
- `CAPA 6/trade_journal.py` - Registro de experimentos

### **🟡 ARCHIVOS LEGACY (REVISAR):**

#### **Sistema Orquestador Antiguo:**
- `dss_orchestrator_clean.py` - Orquestador complejo (no usado por main.py actual)

#### **Funcionalidades Adicionales:**
- `CAPA 3/error_memory_rag.py` - Sistema RAG de memoria de errores
- `CAPA 2/probability_engine.py` - Motor de probabilidades
- `CAPA 5/risk_manager.py` - Gestor de riesgo

### **🔴 ARCHIVOS A ELIMINAR (REDUNDANTES):**

#### **Configuraciones Obsoletas:**
- `CONFIGURACION_HIBRIDA.py` - Reemplazado por main.py
- `.env.example` - No se usa configuración por archivos
- `generate_academic_report.py` - Funcionalidad no integrada

#### **Carpetas Vacías:**
- `CAPA 4/` - Vacía
- `CAPA 7/` - Vacía

#### **Archivos de Configuración Duplicados:**
- `CAPA 1/config.py` - Configuración duplicada

## 🔧 CONFIGURACIÓN

### **Rutas Importantes:**
- **CSV de precios**: `capturador/prices.csv`
- **Símbolo Yahoo**: `EURUSD=X` (configurable en main.py)
- **Intervalo de análisis**: 60 segundos
- **LM Studio URL**: `http://192.168.56.1:1234/v1/chat/completions`

### **Coordenadas OCR:**
- Archivo: `coordenadas_iq_option.py`
- Región por defecto: `(1560, 520, 90, 40)`
- Calibrar con: `ajustar_mira.py`

## 📊 FLUJO DE OPERACIÓN

### **1. Sistema Principal (main.py):**
```
📂 Lee precio CSV → 📊 Descarga Yahoo Finance → 🏗️ Fusiona datos → 🤖 Envía a IA → 📺 Muestra resultado
```

### **2. Test de Integración:**
```
🧪 3 iteraciones → 💰 Compara CSV vs Yahoo → ✅ Valida coincidencia → 📋 Reporte visual
```

### **3. Capturador Independiente:**
```
👁️ OCR de pantalla → 📝 Guarda en CSV → 🔄 Actualización continua
```

## 🛠️ DESARROLLO

### **Agregar Nuevos Indicadores:**
1. Modificar `CAPA 2/technical_analyzer.py`
2. Actualizar `TechnicalIndicators` dataclass
3. Integrar en `analyze_market_data()`

### **Modificar Prompts de IA:**
1. Editar `construir_system_prompt()` en `ai_inference_engine.py`
2. Ajustar `formatear_datos_mercado()` para nuevos campos

### **Agregar Nuevas Fuentes de Datos:**
1. Extender `DataFusionHandler` en `market_data_stream.py`
2. Implementar nuevos métodos de lectura
3. Integrar en `construir_prompt_contextual()`

## 🐛 TROUBLESHOOTING

### **Problemas Comunes:**

#### **"Sin datos en CSV":**
- Verificar que `capturador/main.py` esté ejecutándose
- Revisar permisos de escritura en carpeta `capturador/`

#### **"LM Studio no disponible":**
- Verificar que LM Studio esté ejecutándose
- Probar URLs alternativas: localhost:1234, 127.0.0.1:1234

#### **"Error de importación":**
- Verificar que todas las dependencias estén instaladas
- Ejecutar desde directorio raíz del proyecto

#### **"Diferencia significativa CSV vs Yahoo":**
- Normal en mercados volátiles
- Verificar calibración OCR con `ajustar_mira.py`

## 📈 MÉTRICAS DE RENDIMIENTO

### **Test de Integración:**
- ✅ **Coincidencia**: Diferencia ≤ 0.01 (1 centavo)
- ⚠️ **Moderada**: Diferencia ≤ 0.05 (5 centavos)
- ❌ **Significativa**: Diferencia > 0.05

### **Sistema Principal:**
- **Ciclo completo**: ~5-10 segundos
- **Latencia IA**: ~2-5 segundos
- **Actualización CSV**: Tiempo real

## 🔒 SEGURIDAD Y COMPLIANCE

### **Principios de Seguridad:**
- ✅ **Human-in-the-loop**: Todas las decisiones requieren confirmación
- ✅ **No ejecución automática**: Sistema no opera sin supervisión
- ✅ **Auditoría completa**: Registro de todas las señales
- ✅ **Datos locales**: No se envían datos a servicios externos

### **Disclaimer Legal:**
⚠️ **SOLO FINES EDUCATIVOS**: Este sistema no constituye asesoramiento financiero. El usuario es completamente responsable de sus decisiones de trading.

## 🚀 ROADMAP FUTURO

### **Próximas Mejoras:**
- [ ] **Multi-timeframe**: Análisis en múltiples marcos temporales
- [ ] **Backtesting**: Motor de pruebas históricas
- [ ] **Dashboard web**: Interfaz Flask para monitoreo
- [ ] **Múltiples activos**: Soporte para más pares de divisas
- [ ] **Machine Learning**: Modelos predictivos locales

### **Optimizaciones Técnicas:**
- [ ] **Base de datos**: PostgreSQL para almacenamiento histórico
- [ ] **Microservicios**: Arquitectura distribuida
- [ ] **APIs de brokers**: Integración con plataformas reales
- [ ] **Alertas móviles**: Notificaciones push

---

## 📞 SOPORTE

Para problemas técnicos o mejoras, revisar:
1. **Logs del sistema** en consola
2. **Test de integración** con `test_data_fusion.py`
3. **Estado de LM Studio** en http://localhost:1234
4. **Archivos CSV** en carpeta `capturador/`

**Versión**: 2.0 - Fusión de Datos Híbrida  
**Última actualización**: Febrero 2026