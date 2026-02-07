#!/usr/bin/env python3
"""
🔌 LM STUDIO CONNECTION TESTER
"""

import asyncio
import aiohttp
import json

async def test_lm_studio():
    """Prueba todas las URLs posibles de LM Studio"""
    
    urls = [
        "http://localhost:1234/v1/chat/completions",
        "http://127.0.0.1:1234/v1/chat/completions", 
        "http://192.168.56.1:1234/v1/chat/completions",
        "http://192.168.1.100:1234/v1/chat/completions"  # IP común en redes domésticas
    ]
    
    test_payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": "Responde solo: OK"},
            {"role": "user", "content": "Test"}
        ],
        "max_tokens": 5,
        "temperature": 0.0,
        "stream": False
    }
    
    print("🔌 Probando conexiones LM Studio...")
    
    for url in urls:
        try:
            print(f"   Probando: {url}")
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=test_payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        print(f"   ✅ CONECTADO: {url}")
                        print(f"   📝 Respuesta: {content}")
                        return url
                    else:
                        print(f"   ❌ HTTP {response.status}")
                        
        except asyncio.TimeoutError:
            print(f"   ⏳ TIMEOUT (>10s)")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ LM Studio no encontrado en ninguna URL")
    print("\n💡 SOLUCIONES:")
    print("   1. Verificar que LM Studio esté ejecutándose")
    print("   2. Verificar que el servidor local esté activo en puerto 1234")
    print("   3. Probar desde LM Studio: Server > Start Server")
    print("   4. Verificar firewall/antivirus")
    
    return None

async def test_simple_trading_prompt():
    """Prueba el prompt de trading simplificado"""
    
    # Encontrar URL funcional
    working_url = await test_lm_studio()
    if not working_url:
        return
    
    print(f"\n🤖 Probando prompt de trading en: {working_url}")
    
    trading_payload = {
        "model": "local-model", 
        "messages": [
            {
                "role": "system",
                "content": "ERES UN MOTOR BINARIO. RECIBES DATOS, DEVUELVES JSON.\nRESPONDE SOLO: {\"d\": \"CALL\"|\"PUT\"|\"N\", \"c\": 0-100}"
            },
            {
                "role": "user", 
                "content": "{\"precio_actual\": 1.08500, \"tendencia\": \"UP\", \"rsi\": 45}"
            }
        ],
        "max_tokens": 20,
        "temperature": 0.0,
        "stream": False
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(working_url, json=trading_payload) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"✅ Respuesta trading: {content}")
                    
                    # Intentar parsear JSON
                    try:
                        parsed = json.loads(content.strip())
                        decision = parsed.get("d", "N")
                        confidence = parsed.get("c", 0)
                        print(f"📊 Decisión: {decision} | Confianza: {confidence}%")
                    except:
                        print("⚠️ Respuesta no es JSON válido")
                        
                else:
                    print(f"❌ Error HTTP: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error en test trading: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_trading_prompt())