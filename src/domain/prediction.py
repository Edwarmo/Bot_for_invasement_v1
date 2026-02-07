"""
🎯 PREDICTION TRACKER - Sistema de validación de predicciones
Responsabilidad: Rastrea y valida predicciones del modelo
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

class PredictionTracker:
    """Rastrea y valida predicciones del modelo"""
    
    def __init__(self, predictions_file: str = "predictions_log.json"):
        self.predictions_file = predictions_file
        self.predictions = self._load_predictions()
    
    def _load_predictions(self) -> List[Dict]:
        """Carga predicciones previas"""
        if os.path.exists(self.predictions_file):
            try:
                with open(self.predictions_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_predictions(self):
        """Guarda predicciones al archivo"""
        with open(self.predictions_file, 'w') as f:
            json.dump(self.predictions, f, indent=2)
    
    def log_prediction(self, decision: str, confidence: int, price_at_prediction: float, reason: str):
        """Registra una nueva predicción"""
        prediction = {
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "confidence": confidence,
            "price_at_prediction": price_at_prediction,
            "reason": reason,
            "validated": False,
            "result": None,
            "price_after_1min": None
        }
        
        self.predictions.append(prediction)
        self._save_predictions()
        print(f"📝 Predicción registrada: {decision} @ {price_at_prediction:.5f}")
    
    def validate_predictions(self, csv_path: str):
        """Valida predicciones pendientes contra datos CSV"""
        if not os.path.exists(csv_path):
            return
        
        try:
            df = pd.read_csv(csv_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            df = df[(df['price'] >= 1.0) & (df['price'] <= 1.3)]
            
            updated = False
            for prediction in self.predictions:
                if prediction['validated']:
                    continue
                
                pred_time = datetime.fromisoformat(prediction['timestamp'])
                target_time = pred_time + timedelta(minutes=1)
                
                future_prices = df[df['timestamp'] >= target_time]
                if not future_prices.empty:
                    price_after = future_prices.iloc[0]['price']
                    price_before = prediction['price_at_prediction']
                    
                    actual_direction = "CALL" if price_after > price_before else "PUT"
                    predicted_direction = prediction['decision']
                    
                    is_correct = actual_direction == predicted_direction
                    
                    prediction['validated'] = True
                    prediction['price_after_1min'] = price_after
                    prediction['result'] = "CORRECT" if is_correct else "WRONG"
                    
                    print(f"✅ Validación: {predicted_direction} -> {actual_direction} = {'✓' if is_correct else '✗'}")
                    updated = True
            
            if updated:
                self._save_predictions()
                self._show_accuracy_stats()
                
        except Exception as e:
            print(f"❌ Error validando predicciones: {e}")
    
    def _show_accuracy_stats(self):
        """Muestra estadísticas de precisión"""
        validated = [p for p in self.predictions if p['validated']]
        if not validated:
            return
        
        correct = len([p for p in validated if p['result'] == 'CORRECT'])
        total = len(validated)
        accuracy = (correct / total) * 100
        
        print(f"📊 PRECISIÓN: {correct}/{total} = {accuracy:.1f}%")
        
        high_conf = [p for p in validated if p['confidence'] > 75]
        if high_conf:
            high_correct = len([p for p in high_conf if p['result'] == 'CORRECT'])
            high_accuracy = (high_correct / len(high_conf)) * 100
            print(f"📈 Confianza >75%: {high_correct}/{len(high_conf)} = {high_accuracy:.1f}%")
    
    def get_learning_context(self) -> str:
        """Genera contexto de aprendizaje para el modelo"""
        recent_predictions = self.predictions[-10:]
        validated = [p for p in recent_predictions if p['validated']]
        
        if not validated:
            return ""
        
        context_parts = []
        for pred in validated[-5:]:
            result_emoji = "✓" if pred['result'] == 'CORRECT' else "✗"
            context_parts.append(f"{pred['decision']} {result_emoji}")
        
        return f"HISTORIAL_RECIENTE: {' | '.join(context_parts)}"
