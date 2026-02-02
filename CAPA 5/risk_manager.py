"""
🛡️ CAPA 5: GESTOR DE RIESGO SIMPLE
Responsabilidad: Controles de seguridad para evitar operaciones peligrosas
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class RiskManager:
    """🛡️ Gestor de riesgo con controles básicos de seguridad"""
    
    def __init__(self, max_daily_loss: float = 100.0, max_consecutive_losses: int = 3):
        self.max_daily_loss = max_daily_loss
        self.max_consecutive_losses = max_consecutive_losses
        self.trades_file = "daily_trades.json"
        self.daily_stats = self._load_daily_stats()
        
    def _load_daily_stats(self) -> Dict:
        """📂 Carga estadísticas del día"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    data = json.load(f)
                    if data.get('date') == today:
                        return data
            except:
                pass
        
        # Crear nuevo registro diario
        return {
            'date': today,
            'total_loss': 0.0,
            'consecutive_losses': 0,
            'total_trades': 0,
            'blocked_until': None,
            'last_trades': []
        }
    
    def _save_daily_stats(self):
        """💾 Guarda estadísticas del día"""
        try:
            with open(self.trades_file, 'w') as f:
                json.dump(self.daily_stats, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando stats: {e}")
    
    def check_risk_approval(self, ai_decision: str, confidence: float, market_volatility: float) -> Dict:
        """🔍 Evalúa si la operación es segura"""
        
        # 1. Verificar bloqueo temporal
        if self._is_temporarily_blocked():
            return {
                'approved': False,
                'reason': 'Sistema bloqueado por pérdidas consecutivas',
                'risk_level': 'CRITICAL'
            }
        
        # 2. Verificar límite diario
        if self.daily_stats['total_loss'] >= self.max_daily_loss:
            return {
                'approved': False,
                'reason': f'Límite diario alcanzado (${self.daily_stats["total_loss"]:.2f})',
                'risk_level': 'CRITICAL'
            }
        
        # 3. Verificar pérdidas consecutivas
        if self.daily_stats['consecutive_losses'] >= self.max_consecutive_losses:
            self._apply_cooldown()
            return {
                'approved': False,
                'reason': f'{self.max_consecutive_losses} pérdidas consecutivas - Cooldown aplicado',
                'risk_level': 'HIGH'
            }
        
        # 4. Verificar volatilidad extrema
        if market_volatility > 2.0:  # >2% volatilidad
            return {
                'approved': False,
                'reason': f'Volatilidad extrema ({market_volatility:.2f}%)',
                'risk_level': 'HIGH'
            }
        
        # 5. Verificar confianza mínima
        if confidence < 60.0:
            return {
                'approved': False,
                'reason': f'Confianza insuficiente ({confidence:.1f}%)',
                'risk_level': 'MEDIUM'
            }
        
        # 6. Verificar decisión válida
        if ai_decision not in ['CALL', 'PUT']:
            return {
                'approved': False,
                'reason': 'Decisión inválida o HOLD',
                'risk_level': 'LOW'
            }
        
        # ✅ OPERACIÓN APROBADA
        return {
            'approved': True,
            'reason': 'Todos los controles de riesgo pasados',
            'risk_level': 'LOW'
        }
    
    def _is_temporarily_blocked(self) -> bool:
        """⏰ Verifica si hay bloqueo temporal activo"""
        if not self.daily_stats.get('blocked_until'):
            return False
        
        blocked_until = datetime.fromisoformat(self.daily_stats['blocked_until'])
        return datetime.now() < blocked_until
    
    def _apply_cooldown(self, minutes: int = 30):
        """❄️ Aplica cooldown temporal"""
        cooldown_until = datetime.now() + timedelta(minutes=minutes)
        self.daily_stats['blocked_until'] = cooldown_until.isoformat()
        self._save_daily_stats()
        print(f"❄️ Cooldown aplicado hasta {cooldown_until.strftime('%H:%M')}")
    
    def record_trade_result(self, result: str, amount: float = 10.0):
        """📊 Registra resultado de operación"""
        self.daily_stats['total_trades'] += 1
        
        if result == 'LOSS':
            self.daily_stats['total_loss'] += amount
            self.daily_stats['consecutive_losses'] += 1
        else:
            self.daily_stats['consecutive_losses'] = 0  # Reset contador
        
        # Mantener historial de últimas 10 operaciones
        self.daily_stats['last_trades'].append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'result': result,
            'amount': amount
        })
        
        if len(self.daily_stats['last_trades']) > 10:
            self.daily_stats['last_trades'] = self.daily_stats['last_trades'][-10:]
        
        self._save_daily_stats()
    
    def get_risk_summary(self) -> Dict:
        """📋 Resumen del estado de riesgo"""
        return {
            'daily_loss': self.daily_stats['total_loss'],
            'max_daily_loss': self.max_daily_loss,
            'consecutive_losses': self.daily_stats['consecutive_losses'],
            'max_consecutive_losses': self.max_consecutive_losses,
            'total_trades_today': self.daily_stats['total_trades'],
            'is_blocked': self._is_temporarily_blocked(),
            'blocked_until': self.daily_stats.get('blocked_until'),
            'risk_status': self._get_risk_status()
        }
    
    def _get_risk_status(self) -> str:
        """🚦 Estado general de riesgo"""
        if self._is_temporarily_blocked():
            return "🔴 BLOQUEADO"
        elif self.daily_stats['consecutive_losses'] >= 2:
            return "🟡 PRECAUCIÓN"
        elif self.daily_stats['total_loss'] > self.max_daily_loss * 0.7:
            return "🟠 ALERTA"
        else:
            return "🟢 SEGURO"