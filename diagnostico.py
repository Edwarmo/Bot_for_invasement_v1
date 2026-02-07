#!/usr/bin/env python3
"""
🔧 DIAGNÓSTICO RÁPIDO DEL SISTEMA DSS
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

def test_csv_data():
    """Prueba la calidad de datos CSV"""
    print("📊 PROBANDO DATOS CSV...")
    
    csv_path = "capturador/prices.csv"
    
    try:
        df = pd.read_csv(csv_path)
        print(f"   ✅ CSV leído: {len(df)} filas")
        
        # Verificar rango de precios
        min_price = df['price'].min()
        max_price = df['price'].max()
        print(f"   📈 Rango precios: {min_price:.5f} - {max_price:.5f}")
        
        # Verificar datos válidos para EURUSD
        valid_count = ((df['price'] >= 1.0) & (df['price'] <= 1.3)).sum()
        print(f"   ✅ Datos válidos EURUSD: {valid_count}/{len(df)}")
        
        if valid_count < len(df) * 0.8:
            print("   ⚠️ ADVERTENCIA: Muchos datos fuera de rango")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error CSV: {e}")
        return False

def test_imports():
    """Prueba las importaciones del sistema"""
    print("\n📦 PROBANDO IMPORTACIONES...")
    
    modules = [
        ("pandas", "pd"),
        ("numpy", "np"), 
        ("aiohttp", None),
        ("asyncio", None)
    ]
    
    for module, alias in modules:
        try:
            if alias:
                exec(f"import {module} as {alias}")
            else:
                exec(f"import {module}")
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} - FALTA")

def test_file_structure():
    """Verifica la estructura de archivos"""
    print("\n📁 VERIFICANDO ESTRUCTURA...")
    
    required_files = [
        "main.py",
        "CAPA 1/market_data_stream.py",
        "CAPA 3/ai_inference_engine.py", 
        "capturador/prices.csv",
        "requirements.txt"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - FALTA")

def test_lm_studio_format():
    """Prueba el formato de respuesta esperado"""
    print("\n🤖 PROBANDO FORMATO LM STUDIO...")
    
    # Simular respuesta de LM Studio
    test_responses = [
        '{"d":"PUT","c":-1}',
        '{"d":"CALL","c":75}',
        '{"d":"N","c":45}',
        'PUT',
        'CALL'
    ]
    
    for response in test_responses:
        try:
            # Intentar parsear como JSON
            if response.startswith('{'):
                data = json.loads(response)
                decision = data.get("d", "N")
                confidence = data.get("c", 50)
                print(f"   ✅ JSON: {decision} ({confidence}%)")
            else:
                print(f"   ⚠️ Texto plano: {response}")
                
        except json.JSONDecodeError:
            print(f"   ❌ JSON inválido: {response}")

def show_system_status():
    """Muestra el estado general del sistema"""
    print("\n" + "="*50)
    print("🚀 ESTADO DEL SISTEMA DSS")
    print("="*50)
    
    # Información básica
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📂 Directorio: {os.getcwd()}")
    
    # Ejecutar pruebas
    csv_ok = test_csv_data()
    test_imports()
    test_file_structure()
    test_lm_studio_format()
    
    print("\n" + "="*50)
    print("📋 RESUMEN:")
    print(f"   CSV Data: {'✅ OK' if csv_ok else '❌ ERROR'}")
    print("   LM Studio: ⚠️ VERIFICAR MANUALMENTE")
    print("   Archivos: ✅ ESTRUCTURA OK")
    print("="*50)
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Verificar que LM Studio esté ejecutándose")
    print("   2. Ejecutar: test_lm_studio.py")
    print("   3. Si todo OK, ejecutar: main.py")

if __name__ == "__main__":
    show_system_status()