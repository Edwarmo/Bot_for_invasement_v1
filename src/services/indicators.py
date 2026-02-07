"""
📊 INDICATORS SERVICE
Responsabilidad: Cálculos de indicadores técnicos (RSI, Bollinger, Tendencia)
"""

import numpy as np
from typing import Dict, List

def calcular_indicadores_tecnicos(lista_precios: List[float]) -> Dict:
    """Calcula RSI y Bollinger Bands"""
    if len(lista_precios) < 14:
        return {"rsi": 50, "bollinger": "CENTRO"}
    
    # Filtrar precios válidos
    precios_limpios = [p for p in lista_precios if isinstance(p, (int, float)) and 1.0 < p < 2.0]
    
    if len(precios_limpios) < 14:
        return {"rsi": 50, "bollinger": "CENTRO"}
    
    precios = np.array(precios_limpios)
    
    # RSI
    deltas = np.diff(precios)
    ganancias = np.where(deltas > 0, deltas, 0)
    perdidas = np.where(deltas < 0, -deltas, 0)
    
    avg_ganancia = np.mean(ganancias[-14:])
    avg_perdida = np.mean(perdidas[-14:])
    
    if avg_perdida == 0:
        rsi = 100
    else:
        rs = avg_ganancia / avg_perdida
        rsi = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    ventana = min(20, len(precios))
    media = np.mean(precios[-ventana:])
    std = np.std(precios[-ventana:])
    upper = media + (2 * std)
    lower = media - (2 * std)
    ultimo = precios[-1]
    
    estado_bollinger = "CENTRO"
    if ultimo >= upper:
        estado_bollinger = "TECHO (CARO)"
    elif ultimo <= lower:
        estado_bollinger = "PISO (BARATO)"
    
    return {
        "rsi": round(rsi, 2),
        "bollinger": estado_bollinger,
        "precio_actual": ultimo,
        "bb_upper": round(upper, 5),
        "bb_lower": round(lower, 5)
    }

def calcular_tendencia_macro(lista_precios: List[float]) -> str:
    """Calcula tendencia macro simple"""
    if len(lista_precios) < 10:
        return "NEUTRAL"
    
    precios_limpios = [p for p in lista_precios if isinstance(p, (int, float)) and 1.0 < p < 2.0]
    if len(precios_limpios) < 10:
        return "NEUTRAL"
    
    inicio = np.mean(precios_limpios[:5])
    final = np.mean(precios_limpios[-5:])
    
    diferencia_pct = ((final - inicio) / inicio) * 100
    
    if diferencia_pct > 0.02:
        return "ALCISTA"
    elif diferencia_pct < -0.02:
        return "BAJISTA"
    else:
        return "NEUTRAL"
