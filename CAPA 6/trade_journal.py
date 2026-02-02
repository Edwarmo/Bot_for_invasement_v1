"""
🟪 CAPA 6: AUDITORÍA Y REGISTRO
Responsabilidad: Sistema de persistencia y análisis posterior (Backoffice)
"""

import csv
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import os

@dataclass
class TradeRecord:
    """Registro de una señal/operación"""
    timestamp: datetime
    symbol: str
    direction: str
    probability: float
    ai_validation: bool
    risk_approved: bool
    risk_score: float
    user_action: str  # "accepted", "rejected", "ignored"
    result_pnl: Optional[float] = None
    notes: str = ""

class TradeJournal:
    """Sistema de registro y auditoría de operaciones"""
    
    def __init__(self, journal_file: str = "trading_journal.csv"):
        self.journal_file = journal_file
        self.session_records = []
        self._initialize_journal()
    
    def _initialize_journal(self) -> None:
        """Inicializa el archivo de journal si no existe"""
        try:
            if not os.path.exists(self.journal_file):
                # Crear archivo con headers
                headers = [
                    "timestamp", "symbol", "direction", "probability", 
                    "ai_validation", "risk_approved", "risk_score",
                    "user_action", "result_pnl", "notes"
                ]
                
                with open(self.journal_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                
                print(f"✅ Journal inicializado: {self.journal_file}")
            else:
                print(f"📊 Journal existente cargado: {self.journal_file}")
                
        except Exception as e:
            print(f"❌ Error inicializando journal: {e}")
    
    def log_signal(self, 
                   symbol: str,
                   direction: str, 
                   probability: float,
                   ai_validation: bool,
                   risk_approved: bool,
                   risk_score: float,
                   user_action: str = "pending",
                   notes: str = "") -> str:
        """
        Registra una señal generada por el sistema
        
        Args:
            symbol: Símbolo del activo
            direction: "bullish", "bearish", "neutral"
            probability: Probabilidad de la señal (0-100)
            ai_validation: Si la IA validó la señal
            risk_approved: Si el risk manager aprobó
            risk_score: Score de riesgo (0-100)
            user_action: Acción del usuario
            notes: Notas adicionales
            
        Returns:
            ID del registro
        """
        try:
            record = TradeRecord(
                timestamp=datetime.now(),
                symbol=symbol,
                direction=direction,
                probability=probability,
                ai_validation=ai_validation,
                risk_approved=risk_approved,
                risk_score=risk_score,
                user_action=user_action,
                notes=notes
            )
            
            # Agregar a sesión actual
            self.session_records.append(record)
            
            # Escribir al archivo CSV
            self._write_to_csv(record)
            
            record_id = f"{symbol}_{record.timestamp.strftime('%Y%m%d_%H%M%S')}"
            print(f"📝 Señal registrada: {record_id}")
            
            return record_id
            
        except Exception as e:
            print(f"❌ Error registrando señal: {e}")
            return ""
    
    def update_trade_result(self, record_id: str, pnl: float, user_action: str = "completed") -> bool:
        """
        Actualiza el resultado de una operación
        
        Args:
            record_id: ID del registro a actualizar
            pnl: Ganancia/Pérdida de la operación
            user_action: Acción final del usuario
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Leer archivo actual
            df = pd.read_csv(self.journal_file)
            
            # Buscar registro por timestamp aproximado (últimos registros)
            symbol = record_id.split('_')[0]
            recent_records = df[df['symbol'] == symbol].tail(5)
            
            if not recent_records.empty:
                # Actualizar el registro más reciente que coincida
                last_idx = recent_records.index[-1]
                df.loc[last_idx, 'result_pnl'] = pnl
                df.loc[last_idx, 'user_action'] = user_action
                
                # Guardar archivo actualizado
                df.to_csv(self.journal_file, index=False)
                print(f"📊 Resultado actualizado: {record_id} -> PnL: ${pnl:.2f}")
                return True
            else:
                print(f"⚠️ No se encontró registro: {record_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error actualizando resultado: {e}")
            return False
    
    def _write_to_csv(self, record: TradeRecord) -> None:
        """Escribe un registro al archivo CSV"""
        try:
            with open(self.journal_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    record.timestamp.isoformat(),
                    record.symbol,
                    record.direction,
                    record.probability,
                    record.ai_validation,
                    record.risk_approved,
                    record.risk_score,
                    record.user_action,
                    record.result_pnl,
                    record.notes
                ])
        except Exception as e:
            print(f"❌ Error escribiendo a CSV: {e}")
    
    def get_session_summary(self) -> Dict[str, any]:
        """Genera resumen de la sesión actual"""
        if not self.session_records:
            return {"total_signals": 0}
        
        total = len(self.session_records)
        ai_approved = sum(1 for r in self.session_records if r.ai_validation)
        risk_approved = sum(1 for r in self.session_records if r.risk_approved)
        
        directions = {}
        for record in self.session_records:
            directions[record.direction] = directions.get(record.direction, 0) + 1
        
        avg_probability = sum(r.probability for r in self.session_records) / total
        avg_risk_score = sum(r.risk_score for r in self.session_records) / total
        
        return {
            "total_signals": total,
            "ai_approved": ai_approved,
            "risk_approved": risk_approved,
            "approval_rate": (risk_approved / total * 100) if total > 0 else 0,
            "directions": directions,
            "avg_probability": avg_probability,
            "avg_risk_score": avg_risk_score
        }
    
    def get_daily_analytics(self, date: str = None) -> Dict[str, any]:
        """
        Genera análisis de un día específico
        
        Args:
            date: Fecha en formato YYYY-MM-DD (por defecto hoy)
            
        Returns:
            Diccionario con métricas del día
        """
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            df = pd.read_csv(self.journal_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.strftime("%Y-%m-%d")
            
            # Filtrar por fecha
            day_data = df[df['date'] == date]
            
            if day_data.empty:
                return {"date": date, "total_signals": 0}
            
            # Calcular métricas
            total_signals = len(day_data)
            ai_approved = day_data['ai_validation'].sum()
            risk_approved = day_data['risk_approved'].sum()
            
            # PnL del día (solo registros con resultado)
            completed_trades = day_data[day_data['result_pnl'].notna()]
            total_pnl = completed_trades['result_pnl'].sum() if not completed_trades.empty else 0
            
            # Distribución por símbolo
            symbol_dist = day_data['symbol'].value_counts().to_dict()
            
            # Distribución por dirección
            direction_dist = day_data['direction'].value_counts().to_dict()
            
            return {
                "date": date,
                "total_signals": total_signals,
                "ai_approved": int(ai_approved),
                "risk_approved": int(risk_approved),
                "completed_trades": len(completed_trades),
                "total_pnl": float(total_pnl),
                "avg_probability": float(day_data['probability'].mean()),
                "avg_risk_score": float(day_data['risk_score'].mean()),
                "symbol_distribution": symbol_dist,
                "direction_distribution": direction_dist
            }
            
        except Exception as e:
            print(f"❌ Error en análisis diario: {e}")
            return {"date": date, "error": str(e)}
    
    def export_to_excel(self, filename: str = None) -> bool:
        """
        Exporta el journal a Excel para análisis avanzado
        
        Args:
            filename: Nombre del archivo Excel (opcional)
            
        Returns:
            True si se exportó correctamente
        """
        try:
            if filename is None:
                filename = f"trading_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            df = pd.read_csv(self.journal_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Crear múltiples hojas
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Hoja principal con todos los datos
                df.to_excel(writer, sheet_name='All_Signals', index=False)
                
                # Hoja con resumen diario
                df['date'] = df['timestamp'].dt.strftime("%Y-%m-%d")
                daily_summary = df.groupby('date').agg({
                    'symbol': 'count',
                    'ai_validation': 'sum',
                    'risk_approved': 'sum',
                    'probability': 'mean',
                    'risk_score': 'mean',
                    'result_pnl': 'sum'
                }).rename(columns={'symbol': 'total_signals'})
                
                daily_summary.to_excel(writer, sheet_name='Daily_Summary')
                
                # Hoja con análisis por símbolo
                symbol_analysis = df.groupby('symbol').agg({
                    'timestamp': 'count',
                    'ai_validation': 'sum',
                    'risk_approved': 'sum',
                    'probability': 'mean',
                    'result_pnl': 'sum'
                }).rename(columns={'timestamp': 'total_signals'})
                
                symbol_analysis.to_excel(writer, sheet_name='Symbol_Analysis')
            
            print(f"📊 Journal exportado a Excel: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error exportando a Excel: {e}")
            return False
    
    def cleanup_old_records(self, days_to_keep: int = 30) -> None:
        """
        Limpia registros antiguos del journal
        
        Args:
            days_to_keep: Días de historial a mantener
        """
        try:
            df = pd.read_csv(self.journal_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            cutoff_date = datetime.now() - pd.Timedelta(days=days_to_keep)
            recent_data = df[df['timestamp'] >= cutoff_date]
            
            if len(recent_data) < len(df):
                # Crear backup antes de limpiar
                backup_file = f"journal_backup_{datetime.now().strftime('%Y%m%d')}.csv"
                df.to_csv(backup_file, index=False)
                
                # Guardar solo datos recientes
                recent_data.to_csv(self.journal_file, index=False)
                
                removed_count = len(df) - len(recent_data)
                print(f"🧹 Limpieza completada: {removed_count} registros antiguos removidos")
                print(f"💾 Backup creado: {backup_file}")
            else:
                print("✅ No hay registros antiguos para limpiar")
                
        except Exception as e:
            print(f"❌ Error en limpieza: {e}")