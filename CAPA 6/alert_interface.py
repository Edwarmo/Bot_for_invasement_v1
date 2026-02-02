"""
🖥️ CAPA DE INTERFAZ DE ALERTA - PRESENTATION LAYER
Responsabilidad: UI Thread-Safe para alertas de trading con Human-in-the-Loop
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional
from datetime import datetime
import threading
from dataclasses import dataclass

@dataclass
class AlertData:
    """Estructura de datos para una alerta"""
    symbol: str
    prediction: str  # "CALL" o "PUT"
    confidence: float  # 0-100
    current_price: float
    indicators_summary: str
    timestamp: datetime

class AlertPopup:
    """Ventana de alerta thread-safe con temporizador"""
    
    def __init__(self, alert_data: AlertData, on_decision: Optional[Callable] = None):
        self.alert_data = alert_data
        self.on_decision = on_decision
        self.window = None
        self.decision = None
        self.timer_seconds = 60
        self.timer_active = True
        
    def show_alert(self):
        """Muestra la alerta en el hilo principal de UI"""
        if threading.current_thread() != threading.main_thread():
            # Si no estamos en el hilo principal, programar la ejecución
            self._schedule_in_main_thread()
        else:
            self._create_alert_window()
    
    def _schedule_in_main_thread(self):
        """Programa la creación de la ventana en el hilo principal"""
        # Crear una ventana temporal para programar la ejecución
        temp_root = tk.Tk()
        temp_root.withdraw()  # Ocultar ventana temporal
        temp_root.after(0, self._create_alert_window)
        temp_root.after(100, temp_root.destroy)  # Destruir ventana temporal
    
    def _create_alert_window(self):
        """Crea la ventana de alerta"""
        self.window = tk.Toplevel()
        self.window.title("🚨 Alerta de Trading - DSS")
        self.window.geometry("400x350")
        self.window.resizable(False, False)
        
        # Configurar ventana siempre visible
        self.window.attributes('-topmost', True)
        self.window.focus_force()
        
        # Centrar ventana
        self._center_window()
        
        # Configurar cierre de ventana
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Crear contenido
        self._create_content()
        
        # Iniciar temporizador
        self._start_timer()
    
    def _center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (350 // 2)
        self.window.geometry(f"400x350+{x}+{y}")
    
    def _create_content(self):
        """Crea el contenido de la ventana"""
        # Frame principal
        main_frame = tk.Frame(self.window, bg='#2d2d2d', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="🚨 NUEVA SEÑAL DETECTADA",
            font=('Arial', 16, 'bold'),
            fg='#ffffff',
            bg='#2d2d2d'
        )
        title_label.pack(pady=(0, 20))
        
        # Información del activo
        info_frame = tk.Frame(main_frame, bg='#2d2d2d')
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Símbolo
        symbol_label = tk.Label(
            info_frame,
            text=f"📊 Activo: {self.alert_data.symbol}",
            font=('Arial', 12, 'bold'),
            fg='#00ff00',
            bg='#2d2d2d'
        )
        symbol_label.pack(anchor=tk.W)
        
        # Predicción
        prediction_color = '#28a745' if self.alert_data.prediction == 'CALL' else '#dc3545'
        prediction_emoji = '📈' if self.alert_data.prediction == 'CALL' else '📉'
        
        prediction_label = tk.Label(
            info_frame,
            text=f"{prediction_emoji} Predicción: {self.alert_data.prediction}",
            font=('Arial', 14, 'bold'),
            fg=prediction_color,
            bg='#2d2d2d'
        )
        prediction_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Confianza
        confidence_color = '#28a745' if self.alert_data.confidence >= 75 else '#ffc107' if self.alert_data.confidence >= 60 else '#dc3545'
        
        confidence_label = tk.Label(
            info_frame,
            text=f"🎯 Confianza: {self.alert_data.confidence:.1f}%",
            font=('Arial', 12),
            fg=confidence_color,
            bg='#2d2d2d'
        )
        confidence_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Precio actual
        price_label = tk.Label(
            info_frame,
            text=f"💰 Precio: {self.alert_data.current_price:.5f}",
            font=('Arial', 11),
            fg='#ffffff',
            bg='#2d2d2d'
        )
        price_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Indicadores
        indicators_label = tk.Label(
            info_frame,
            text=f"📈 {self.alert_data.indicators_summary}",
            font=('Arial', 9),
            fg='#cccccc',
            bg='#2d2d2d',
            wraplength=350,
            justify=tk.LEFT
        )
        indicators_label.pack(anchor=tk.W, pady=(10, 0))
        
        # Separador
        separator = tk.Frame(main_frame, height=2, bg='#555555')
        separator.pack(fill=tk.X, pady=15)
        
        # Temporizador
        self.timer_label = tk.Label(
            main_frame,
            text=f"⏰ Auto-cierre en: {self.timer_seconds}s",
            font=('Arial', 10),
            fg='#ffc107',
            bg='#2d2d2d'
        )
        self.timer_label.pack(pady=(0, 15))
        
        # Botones
        button_frame = tk.Frame(main_frame, bg='#2d2d2d')
        button_frame.pack(fill=tk.X)
        
        # Botón Ejecutar Manualmente
        execute_btn = tk.Button(
            button_frame,
            text="✅ EJECUTAR MANUALMENTE",
            font=('Arial', 11, 'bold'),
            bg='#28a745',
            fg='white',
            width=20,
            height=2,
            command=self._on_execute_manual
        )
        execute_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón Cerrar/Rechazar
        close_btn = tk.Button(
            button_frame,
            text="❌ CERRAR/RECHAZAR",
            font=('Arial', 11, 'bold'),
            bg='#dc3545',
            fg='white',
            width=20,
            height=2,
            command=self._on_close_reject
        )
        close_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Disclaimer
        disclaimer_label = tk.Label(
            main_frame,
            text="⚠️ DECISIÓN MANUAL REQUERIDA - Sistema de Soporte a la Decisión",
            font=('Arial', 8),
            fg='#888888',
            bg='#2d2d2d',
            wraplength=350
        )
        disclaimer_label.pack(pady=(15, 0))
    
    def _start_timer(self):
        """Inicia el temporizador de auto-cierre"""
        self._update_timer()
    
    def _update_timer(self):
        """Actualiza el temporizador"""
        if not self.timer_active or not self.window:
            return
        
        if self.timer_seconds > 0:
            self.timer_label.config(text=f"⏰ Auto-cierre en: {self.timer_seconds}s")
            self.timer_seconds -= 1
            self.window.after(1000, self._update_timer)
        else:
            self._on_timeout()
    
    def _on_execute_manual(self):
        """Maneja la ejecución manual"""
        self.decision = "EXECUTE"
        self._close_window()
    
    def _on_close_reject(self):
        """Maneja el cierre/rechazo"""
        self.decision = "REJECT"
        self._close_window()
    
    def _on_timeout(self):
        """Maneja el timeout automático"""
        self.decision = "TIMEOUT"
        self._close_window()
    
    def _on_window_close(self):
        """Maneja el cierre de ventana por X"""
        self.decision = "CLOSE"
        self._close_window()
    
    def _close_window(self):
        """Cierra la ventana y notifica la decisión"""
        self.timer_active = False
        
        if self.on_decision:
            try:
                self.on_decision(self.decision, self.alert_data)
            except Exception as e:
                print(f"Error en callback de decisión: {e}")
        
        if self.window:
            self.window.destroy()
            self.window = None

class AlertManager:
    """Gestor de alertas thread-safe"""
    
    def __init__(self):
        self.active_alerts = []
        self.decision_callback = None
        self._lock = threading.Lock()
    
    def set_decision_callback(self, callback: Callable):
        """Establece el callback para decisiones"""
        self.decision_callback = callback
    
    def show_alert(self, alert_data: AlertData):
        """Muestra una nueva alerta"""
        with self._lock:
            # Cerrar alertas anteriores del mismo símbolo
            self._close_alerts_for_symbol(alert_data.symbol)
            
            # Crear nueva alerta
            alert = AlertPopup(alert_data, self._on_alert_decision)
            self.active_alerts.append(alert)
            
            # Mostrar alerta (thread-safe)
            alert.show_alert()
    
    def _close_alerts_for_symbol(self, symbol: str):
        """Cierra alertas activas para un símbolo específico"""
        for alert in self.active_alerts[:]:
            if alert.alert_data.symbol == symbol and alert.window:
                alert._close_window()
                self.active_alerts.remove(alert)
    
    def _on_alert_decision(self, decision: str, alert_data: AlertData):
        """Maneja las decisiones de las alertas"""
        print(f"🎯 Decisión: {decision} para {alert_data.symbol} - {alert_data.prediction}")
        
        # Remover alerta de la lista activa
        with self._lock:
            self.active_alerts = [a for a in self.active_alerts if a.alert_data != alert_data]
        
        # Notificar callback principal
        if self.decision_callback:
            try:
                self.decision_callback(decision, alert_data)
            except Exception as e:
                print(f"Error en callback principal: {e}")
    
    def close_all_alerts(self):
        """Cierra todas las alertas activas"""
        with self._lock:
            for alert in self.active_alerts[:]:
                if alert.window:
                    alert._close_window()
            self.active_alerts.clear()
    
    def get_active_count(self) -> int:
        """Obtiene el número de alertas activas"""
        with self._lock:
            return len(self.active_alerts)