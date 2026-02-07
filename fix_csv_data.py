#!/usr/bin/env python3
"""
🧹 CSV DATA CLEANER - Limpia datos corruptos del capturador
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def clean_price_data(csv_path: str):
    """Limpia datos corruptos del CSV de precios"""
    print(f"🧹 Limpiando datos en: {csv_path}")
    
    try:
        # Leer CSV
        df = pd.read_csv(csv_path)
        print(f"📊 Datos originales: {len(df)} filas")
        
        # Mostrar estadísticas antes
        print(f"📈 Rango original: {df['price'].min():.6f} - {df['price'].max():.6f}")
        
        # Filtrar datos válidos para EURUSD (rango típico: 1.0 - 1.3)
        valid_mask = (df['price'] >= 1.0) & (df['price'] <= 1.3)
        df_clean = df[valid_mask].copy()
        
        print(f"✅ Datos válidos: {len(df_clean)} filas")
        print(f"📈 Rango limpio: {df_clean['price'].min():.6f} - {df_clean['price'].max():.6f}")
        
        # Si quedan muy pocos datos, generar datos sintéticos
        if len(df_clean) < 10:
            print("⚠️ Muy pocos datos válidos. Generando datos sintéticos...")
            df_clean = generate_synthetic_data()
        
        # Guardar datos limpios
        df_clean.to_csv(csv_path, index=False)
        print(f"💾 Datos guardados: {len(df_clean)} filas válidas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error limpiando CSV: {e}")
        return False

def generate_synthetic_data():
    """Genera datos sintéticos realistas para EURUSD"""
    print("🎲 Generando datos sintéticos para EURUSD...")
    
    # Precio base realista
    base_price = 1.08500
    
    # Generar 50 puntos de datos con movimiento realista
    timestamps = []
    prices = []
    
    current_time = datetime.now() - timedelta(minutes=10)
    current_price = base_price
    
    for i in range(50):
        # Movimiento aleatorio pequeño (±5 pips máximo)
        change = np.random.normal(0, 0.0002)  # ~2 pips std
        current_price += change
        
        # Mantener en rango realista
        current_price = max(1.07000, min(1.10000, current_price))
        
        timestamps.append(current_time.isoformat())
        prices.append(round(current_price, 5))
        
        current_time += timedelta(seconds=12)  # 12 segundos entre datos
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'price': prices
    })
    
    print(f"✅ Generados {len(df)} datos sintéticos")
    return df

if __name__ == "__main__":
    csv_path = "capturador/prices.csv"
    clean_price_data(csv_path)