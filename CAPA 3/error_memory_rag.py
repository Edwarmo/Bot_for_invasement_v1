"""
🧠 CAPA 3: MEMORIA DE ERRORES RAG
Responsabilidad: Análisis de patrones de fallo para reducir repetición
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from collections import Counter

class ErrorMemoryRAG:
    """🧠 Sistema RAG para memoria de errores recientes"""
    
    def __init__(self, csv_file: str = "experiment_results.csv", lookback_hours: int = 24):
        self.csv_file = csv_file
        self.lookback_hours = lookback_hours
        self.error_patterns = []
        
    def analyze_recent_errors(self) -> Dict:
        """🔍 Analiza errores recientes y genera memoria RAG"""
        try:
            if not os.path.exists(self.csv_file):
                return {"error_summary": "No hay historial de errores", "risk_factors": []}
            
            df = pd.read_csv(self.csv_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filtrar últimas 24 horas con resultado LOSS
            cutoff_time = datetime.now() - timedelta(hours=self.lookback_hours)
            recent_losses = df[
                (df['timestamp'] >= cutoff_time) & 
                (df['outcome'] == 'LOSS')
            ]
            
            if recent_losses.empty:
                return {
                    "error_summary": "Sin errores recientes en las últimas 24h",
                    "risk_factors": [],
                    "total_recent_losses": 0
                }
            
            # Analizar patrones de error
            error_analysis = self._extract_error_patterns(recent_losses)
            
            return error_analysis
            
        except Exception as e:
            return {
                "error_summary": f"Error analizando memoria: {e}",
                "risk_factors": [],
                "total_recent_losses": 0
            }
    
    def _extract_error_patterns(self, losses_df: pd.DataFrame) -> Dict:
        """🔍 Extrae patrones específicos de errores"""
        total_losses = len(losses_df)
        
        # Análisis por señal
        signal_errors = losses_df['signal'].value_counts()
        
        # Análisis por market_state
        market_errors = losses_df['market_state'].value_counts()
        
        # Análisis por technical_trigger
        trigger_errors = losses_df['technical_trigger'].value_counts()
        
        # Análisis por confianza
        high_conf_errors = len(losses_df[losses_df['ai_confidence'] >= 85])
        
        # Generar advertencias específicas
        warnings = []
        risk_factors = []
        
        # Patrón 1: Repetición de señal específica
        if signal_errors.max() >= 3:
            dominant_signal = signal_errors.index[0]
            count = signal_errors.iloc[0]
            warnings.append(f"ADVERTENCIA: Fallaste {count} veces con señal {dominant_signal} en 24h")
            risk_factors.append(f"repeated_{dominant_signal.lower()}_failures")
        
        # Patrón 2: Problemas en mercado específico
        if 'OTC_ESTIMATED' in market_errors and market_errors['OTC_ESTIMATED'] >= 2:
            count = market_errors['OTC_ESTIMATED']
            warnings.append(f"ADVERTENCIA: {count} fallos en mercado OTC - datos menos confiables")
            risk_factors.append("otc_market_failures")
        
        # Patrón 3: Trigger técnico problemático
        if trigger_errors.max() >= 2:
            problematic_trigger = trigger_errors.index[0]
            count = trigger_errors.iloc[0]
            warnings.append(f"ADVERTENCIA: {count} fallos con {problematic_trigger}")
            risk_factors.append(f"trigger_{problematic_trigger.lower()}_failures")
        
        # Patrón 4: Sobreconfianza
        if high_conf_errors >= 2:
            warnings.append(f"ADVERTENCIA: {high_conf_errors} fallos con alta confianza (≥85%)")
            risk_factors.append("overconfidence_bias")
        
        # Generar resumen
        error_summary = f"MEMORIA DE ERRORES: {total_losses} pérdidas en 24h. " + " | ".join(warnings)
        
        return {
            "error_summary": error_summary,
            "risk_factors": risk_factors,
            "total_recent_losses": total_losses,
            "signal_distribution": signal_errors.to_dict(),
            "market_distribution": market_errors.to_dict(),
            "trigger_distribution": trigger_errors.to_dict(),
            "high_confidence_failures": high_conf_errors
        }
    
    def calculate_risk_adjustment(self, current_context: Dict, error_memory: Dict) -> Dict:
        """⚖️ Calcula ajuste de riesgo basado en memoria de errores"""
        
        base_confidence_penalty = 0
        risk_reasons = []
        
        # Penalización por errores totales recientes
        total_losses = error_memory.get('total_recent_losses', 0)
        if total_losses >= 5:
            base_confidence_penalty += 15
            risk_reasons.append(f"{total_losses} pérdidas recientes")
        elif total_losses >= 3:
            base_confidence_penalty += 10
            risk_reasons.append(f"{total_losses} pérdidas recientes")
        
        # Penalización por repetición de señal
        current_signal = current_context.get('signal', '')
        signal_dist = error_memory.get('signal_distribution', {})
        if current_signal in signal_dist and signal_dist[current_signal] >= 2:
            base_confidence_penalty += 20
            risk_reasons.append(f"repetición señal {current_signal}")
        
        # Penalización por mercado OTC
        current_market = current_context.get('market_state', 'REAL')
        if current_market == 'OTC_ESTIMATED':
            otc_failures = error_memory.get('market_distribution', {}).get('OTC_ESTIMATED', 0)
            if otc_failures >= 2:
                base_confidence_penalty += 15
                risk_reasons.append("fallos previos en OTC")
        
        # Penalización por trigger técnico
        current_trigger = current_context.get('technical_trigger', '')
        trigger_dist = error_memory.get('trigger_distribution', {})
        if current_trigger in trigger_dist and trigger_dist[current_trigger] >= 2:
            base_confidence_penalty += 12
            risk_reasons.append(f"fallos con {current_trigger}")
        
        # Penalización por sobreconfianza
        high_conf_failures = error_memory.get('high_confidence_failures', 0)
        if high_conf_failures >= 2:
            base_confidence_penalty += 8
            risk_reasons.append("sesgo de sobreconfianza")
        
        return {
            "confidence_penalty": min(base_confidence_penalty, 40),  # Máximo 40% penalización
            "risk_reasons": risk_reasons,
            "should_be_neutral": base_confidence_penalty >= 30
        }

class EnhancedAIInferenceEngine:
    """🤖 Motor de IA mejorado con memoria de errores RAG"""
    
    def __init__(self, api_url: str = "http://localhost:1234/v1/chat/completions"):
        self.api_url = api_url
        self.session = None
        self.error_memory = ErrorMemoryRAG()
        self.system_prompt = self._build_enhanced_system_prompt()
    
    def _build_enhanced_system_prompt(self) -> str:
        """System prompt con memoria de errores"""
        return """Eres un Ingeniero de IA Senior especializado en DSS financieros y control de sesgo predictivo.

FUNCIÓN: Analizar mercado y estimar probabilidades, NO ejecutar operaciones.

FORMATO OBLIGATORIO:
{"signal": "CALL|PUT|NEUTRAL", "confidence_score": 0-100, "risk_adjustment_reason": "explicación"}

REGLAS DE MEMORIA DE ERRORES:
- SIEMPRE considera la Memoria de Errores Recientes antes de decidir
- Si el contexto actual se parece a errores recientes: reduce confidence_score o emite NEUTRAL
- Penaliza automáticamente si: mercado OTC, datos estimados, patrones similares a pérdidas

PRINCIPIOS DE SEGURIDAD:
- Prefiere NEUTRAL ante duda razonable
- Función: ayudar a decidir mejor, no acertar siempre
- Prohibido: ignorar errores pasados, compensar siendo más agresivo, lenguaje determinista"""
    
    async def analyze_with_error_memory(self, market_data: Dict) -> Optional[Dict]:
        """🧠 Análisis con memoria de errores RAG"""
        try:
            # Obtener memoria de errores recientes
            error_memory = self.error_memory.analyze_recent_errors()
            
            # Calcular ajuste de riesgo
            risk_adjustment = self.error_memory.calculate_risk_adjustment(market_data, error_memory)
            
            # Construir prompt con memoria
            enhanced_prompt = self._build_enhanced_prompt(market_data, error_memory, risk_adjustment)
            
            # Realizar petición (simulada por ahora)
            response = await self._make_enhanced_request(enhanced_prompt)
            
            if response:
                # Aplicar ajustes de memoria
                return self._apply_memory_adjustments(response, risk_adjustment)
            
            return None
            
        except Exception as e:
            print(f"❌ Error en análisis con memoria: {e}")
            return None
    
    def _build_enhanced_prompt(self, market_data: Dict, error_memory: Dict, risk_adjustment: Dict) -> str:
        """📝 Construye prompt con contexto de memoria"""
        
        base_prompt = f"""CONTEXTO DE MERCADO ACTUAL:
SÍMBOLO: {market_data.get('symbol', 'UNKNOWN')}
PRECIO: {market_data.get('price', 0):.5f}
RSI: {market_data.get('rsi', 50):.1f}
EMA_20: {market_data.get('ema_20', 0):.5f}
EMA_50: {market_data.get('ema_50', 0):.5f}
BB_POSITION: {market_data.get('bb_position', 0.5):.2f}
TENDENCIA: {market_data.get('trend', 'NEUTRAL')}
MARKET_STATE: {market_data.get('market_mode', 'REAL')}"""
        
        # Añadir memoria de errores
        memory_prompt = f"""

MEMORIA DE ERRORES RECIENTES (RAG):
{error_memory.get('error_summary', 'Sin errores recientes')}

AJUSTE DE RIESGO CALCULADO:
Penalización confianza: -{risk_adjustment.get('confidence_penalty', 0)}%
Razones: {', '.join(risk_adjustment.get('risk_reasons', ['ninguna']))}
Recomendar NEUTRAL: {'SÍ' if risk_adjustment.get('should_be_neutral', False) else 'NO'}"""
        
        return base_prompt + memory_prompt + "\n\nResponde SOLO JSON:"
    
    async def _make_enhanced_request(self, prompt: str) -> Optional[Dict]:
        """🔄 Petición simulada (integrar con LM Studio real)"""
        # Por ahora simulamos respuesta basada en el prompt
        # En implementación real, usar aiohttp con LM Studio
        
        # Simulación básica basada en RSI y memoria
        import re
        
        # Extraer RSI del prompt
        rsi_match = re.search(r'RSI: ([\d.]+)', prompt)
        rsi = float(rsi_match.group(1)) if rsi_match else 50
        
        # Extraer penalización
        penalty_match = re.search(r'Penalización confianza: -(\d+)%', prompt)
        penalty = int(penalty_match.group(1)) if penalty_match else 0
        
        # Lógica simulada
        if "Recomendar NEUTRAL: SÍ" in prompt:
            return {
                "signal": "NEUTRAL",
                "confidence_score": 45,
                "risk_adjustment_reason": "Memoria de errores sugiere evitar operación"
            }
        elif rsi > 70:
            base_conf = 75 - penalty
            return {
                "signal": "PUT",
                "confidence_score": max(base_conf, 50),
                "risk_adjustment_reason": f"RSI sobrecompra, ajustado por memoria (-{penalty}%)"
            }
        elif rsi < 30:
            base_conf = 75 - penalty
            return {
                "signal": "CALL", 
                "confidence_score": max(base_conf, 50),
                "risk_adjustment_reason": f"RSI sobreventa, ajustado por memoria (-{penalty}%)"
            }
        else:
            return {
                "signal": "NEUTRAL",
                "confidence_score": 55,
                "risk_adjustment_reason": "Condiciones neutras, sin ventaja clara"
            }
    
    def _apply_memory_adjustments(self, response: Dict, risk_adjustment: Dict) -> Dict:
        """⚖️ Aplica ajustes finales basados en memoria"""
        
        # Aplicar penalización de confianza
        penalty = risk_adjustment.get('confidence_penalty', 0)
        original_confidence = response.get('confidence_score', 50)
        adjusted_confidence = max(original_confidence - penalty, 45)  # Mínimo 45%
        
        # Forzar NEUTRAL si el riesgo es muy alto
        if risk_adjustment.get('should_be_neutral', False):
            response['signal'] = 'NEUTRAL'
            adjusted_confidence = min(adjusted_confidence, 55)
        
        response['confidence_score'] = adjusted_confidence
        
        # Actualizar razón con memoria
        memory_reasons = risk_adjustment.get('risk_reasons', [])
        if memory_reasons:
            original_reason = response.get('risk_adjustment_reason', '')
            response['risk_adjustment_reason'] = f"{original_reason} | Memoria: {', '.join(memory_reasons)}"
        
        return response