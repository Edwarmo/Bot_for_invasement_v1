"""
🤖 AI CLIENT SERVICE
Responsabilidad: Cliente LM Studio para análisis de mercado
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
    """Cliente LM Studio para análisis de mercado"""
    
    def __init__(self, api_url: str = "http://192.168.56.1:1234/v1/chat/completions"):
        self.api_url = api_url
        self.session = None
        self._system_prompt_cache = None
        self._json_pattern = re.compile(r'\{[^}]*\}', re.DOTALL)
        self._decision_pattern = re.compile(r'"d":\s*"(CALL|PUT|N)"', re.IGNORECASE)
        self._score_pattern = re.compile(r'"c":\s*(\d+)')
        self._razon_pattern = re.compile(r'"razon":\s*"([^"]+)"', re.IGNORECASE)
    
    def construir_system_prompt(self) -> str:
        """⚡ Motor de Fusión de Datos de Alta Precisión"""
        if self._system_prompt_cache is None:
            self._system_prompt_cache = """MOTOR DE FUSIÓN DE DATOS - ALTA PRECISIÓN

OBJETIVO: Predecir dirección dominante del precio en próximos 60 segundos.

REGLAS DE FUSIÓN PARA PREDICCIÓN 60s:
1. Río↑ + Ola↑ → CALL (90%)
2. Río↓ + Ola↓ → PUT (90%)
3. Río↑ + Ola↓ agotada → CALL (70%)
4. Río↓ + Ola↑ agotada → PUT (70%)
5. Sin confluencia → NEUTRAL

OUTPUT: {"d": "CALL"|"PUT"|"N", "c": confianza, "razon": "..."}"""
        return self._system_prompt_cache
    
    def formatear_datos_mercado(self, input_data: Dict) -> str:
        """📊 Formatea datos para el motor de IA"""
        fusion_data = {
            "symbol": input_data.get('symbol', 'EURUSD'),
            "MACRO_RIO": input_data.get('MACRO_RIO', {}),
            "MICRO_OLA": input_data.get('MICRO_OLA', {}),
            "FUSION_RESULT": input_data.get('FUSION_RESULT', {}),
            "learning_context": input_data.get('learning_context', '')
        }
        return json.dumps(fusion_data, separators=(',', ':'))
    
    async def _make_request(self, messages: list) -> Optional[str]:
        """Realiza petición HTTP al servidor LM Studio"""
        try:
            if self.session is None:
                self.session = aiohttp.ClientSession()
            
            async with self.session.post(
                self.api_url,
                json={"messages": messages, "temperature": 0.3}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                return None
        except Exception as e:
            print(f"❌ Error en petición IA: {e}")
            return None
    
    async def test_connection(self) -> bool:
        """Verifica conexión con LM Studio"""
        try:
            if self.session is None:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(
                self.api_url.replace('/v1/chat/completions', '/models')
            ) as response:
                return response.status == 200
        except:
            return False
    
    async def analizar_mercado(self, input_data: Dict) -> Optional[AIResponse]:
        """🎯 Analiza mercado y devuelve decisión"""
        try:
            messages = [
                {"role": "system", "content": self.construir_system_prompt()},
                {"role": "user", "content": self.formatear_datos_mercado(input_data)}
            ]
            
            response_text = await self._make_request(messages)
            
            if not response_text:
                return None
            
            # Parsear respuesta
            match = self._json_pattern.search(response_text)
            if match:
                json_str = match.group()
                data = json.loads(json_str)
                
                return AIResponse(
                    decision=data.get('d', data.get('decision', 'NEUTRAL')),
                    razon=data.get('razon', response_text),
                    timestamp=datetime.now(),
                    raw_response=response_text
                )
            
            return AIResponse(
                decision='NEUTRAL',
                razon=response_text,
                timestamp=datetime.now(),
                raw_response=response_text
            )
            
        except Exception as e:
            print(f"❌ Error analizando mercado: {e}")
            return None
    
    async def close(self):
        """Cierra sesión HTTP"""
        if self.session:
            await self.session.close()
            self.session = None
