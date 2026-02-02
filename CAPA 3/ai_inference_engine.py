"""
🤖 CAPA 3: MOTOR DE INFERENCIA IA - FUSIÓN DE DATOS
Responsabilidad: Cliente LM Studio compatible con arquitectura híbrida
"""

import json
import re
import aiohttp
import asyncio
from typing import Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AIResponse:
    """Respuesta estructurada de la IA"""
    decision: str  # "CALL", "PUT", "HOLD"
    razon: str
    timestamp: datetime
    raw_response: str = ""

class LMStudioClient:
    """Cliente LM Studio para arquitectura de fusión de datos"""
    
    def __init__(self, api_url: str = "http://192.168.56.1:1234/v1/chat/completions"):
        self.api_url = api_url
        self.session = None
    
    def construir_system_prompt(self) -> str:
        """🧠 System prompt determinista"""
        return """ROL: Motor matemático determinista.
No opinas.
No aconsejas.
No decides operaciones.

Recibirás estadísticas numéricas.
Evalúa coherencia direccional.

Devuelve SOLO JSON válido:
{
  "direccion": "UP" | "DOWN" | "NEUTRAL",
  "confianza": 0-100
}"""
    
    def formatear_datos_mercado(self, input_data: Union[Dict, str]) -> str:
        """📊 Convierte datos a formato JSON para LLM"""
        if isinstance(input_data, dict):
            return json.dumps(input_data, indent=2)
        else:
            return str(input_data)
    
    async def analizar_mercado(self, input_data: Union[Dict, str]) -> Optional[AIResponse]:
        """🎯 Función principal de análisis compatible con fusión de datos"""
        try:
            # Construir prompts
            system_prompt = self.construir_system_prompt()
            user_prompt = self.formatear_datos_mercado(input_data)
            
            # Enviar a LM Studio
            response = await self._make_request(system_prompt, user_prompt)
            if not response:
                return self._fallback_response()
            
            # Parsear respuesta
            return self._parse_response(response)
            
        except Exception as e:
            print(f"❌ Error análisis IA: {e}")
            return self._fallback_response()
    
    async def _make_request(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """📡 Petición HTTP a LM Studio"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            payload = {
                "model": "local-model",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.0,
                "stream": False
            }
            
            async with self.session.post(
                self.api_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                
                if response.status != 200:
                    print(f"⚠️ LM Studio HTTP {response.status}")
                    return None
                
                result = await response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content.strip()
                
        except Exception as e:
            print(f"❌ Error petición LM Studio: {e}")
            return None
    
    def _parse_response(self, response: str) -> Optional[AIResponse]:
        """🔍 Parsea respuesta JSON determinista"""
        try:
            cleaned = self._clean_json(response)
            data = json.loads(cleaned)
            
            direccion = data.get("direccion", "NEUTRAL").upper()
            confianza = int(data.get("confianza", 50))
            
            if direccion not in ["UP", "DOWN", "NEUTRAL"]:
                direccion = "NEUTRAL"
            
            confianza = max(0, min(100, confianza))
            
            # Mapear a formato legacy para compatibilidad
            decision_map = {"UP": "CALL", "DOWN": "PUT", "NEUTRAL": "HOLD"}
            
            return AIResponse(
                decision=decision_map[direccion],
                razon=f"Dir: {direccion}, Conf: {confianza}%",
                timestamp=datetime.now(),
                raw_response=response
            )
            
        except json.JSONDecodeError:
            print(f"❌ JSON inválido: {response}")
            return self._fallback_response()
        except Exception as e:
            print(f"❌ Error parseando: {e}")
            return self._fallback_response()
    
    def _clean_json(self, response: str) -> str:
        """🧹 Limpia respuesta de alucinaciones"""
        # Remover markdown
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Buscar JSON válido
        json_match = re.search(r'\{[^}]*\}', response)
        if json_match:
            return json_match.group(0)
        
        # Fallback: construir JSON desde patrones
        direccion_match = re.search(r'"direccion":\s*"(UP|DOWN|NEUTRAL)"', response, re.IGNORECASE)
        confianza_match = re.search(r'"confianza":\s*(\d+)', response)
        
        if direccion_match:
            direccion = direccion_match.group(1).upper()
            confianza = confianza_match.group(1) if confianza_match else "50"
            return f'{{"direccion": "{direccion}", "confianza": {confianza}}}'
        
        raise json.JSONDecodeError("No valid JSON found", response, 0)
    
    def _fallback_response(self) -> AIResponse:
        """🔄 Respuesta de respaldo"""
        return AIResponse(
            decision="HOLD",
            razon="Sistema en modo seguro",
            timestamp=datetime.now(),
            raw_response="FALLBACK"
        )
    
    async def test_connection(self) -> bool:
        """🔌 Prueba conexión LM Studio"""
        urls = [
            "http://192.168.56.1:1234/v1/chat/completions",
            "http://localhost:1234/v1/chat/completions",
            "http://127.0.0.1:1234/v1/chat/completions"
        ]
        
        for url in urls:
            try:
                self.api_url = url
                test_data = {
                    'current_price': 1.08500,
                    'source': 'TEST',
                    'market_context': {
                        'trend_1h': 'NEUTRAL',
                        'volatility_1m': 0.5,
                        'last_close_yahoo': 1.08450
                    }
                }
                
                response = await self.analizar_mercado(test_data)
                
                if response and response.decision in ["CALL", "PUT", "HOLD"]:
                    print(f"✅ LM Studio conectado: {url}")
                    return True
                    
            except Exception as e:
                print(f"❌ Falló {url}: {e}")
                continue
        
        print("❌ LM Studio no disponible")
        return False
    
    async def close(self):
        """🔒 Cierra sesión HTTP"""
        if self.session:
            await self.session.close()
            self.session = None
    
