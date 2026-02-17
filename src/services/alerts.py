"""
🔔 ALERTS SERVICE
Responsabilidad: UI Thread-Safe para alertas de trading
"""

import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, Callable
import time

# Variable global para rastrear ventana activa
_active_alert_window = None
_active_alert_lock = threading.Lock()

class TradingAlert:
    """Ventana de alerta thread-safe con temporizador"""
    
    def __init__(self, decision: str, razon: str, duracion: str = "3-5 MIN"):
        self.root = tk.Tk()
        self.decision = decision.upper()
        self.razon = razon
        self.duracion = duracion
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de la alerta"""
        self.root.title(f"🤖 SEÑAL IA: {self.decision}")
        self.root.geometry("400x350")
        self.root.attributes("-topmost", True)
        
        # Cerrar con X también limpia la referencia
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Colores dinámicos
        bg_color = "#1b5e20" if "CALL" in self.decision else "#b71c1c"
        if "ESPERAR" in self.decision or "NEUTRAL" in self.decision:
            bg_color = "#424242"
        
        self.root.configure(bg=bg_color)
        
        # Título
        lbl_action = tk.Label(
            self.root, text=self.decision,
            font=("Arial", 40, "bold"),
            fg="white", bg=bg_color
        )
        lbl_action.pack(pady=20)
        
        # Duración
        lbl_time = tk.Label(
            self.root, text=f"⏱️ TIEMPO: {self.duracion}",
            font=("Arial", 16), fg="white", bg=bg_color
        )
        lbl_time.pack(pady=5)
        
        # Razón
        frame_razon = tk.Frame(self.root, bg="white", padx=10, pady=10)
        frame_razon.pack(fill="both", expand=True, padx=20, pady=20)
        
        lbl_razon = tk.Label(
            frame_razon, text=self.razon,
            font=("Arial", 11), fg="black", bg="white",
            wraplength=350, justify="center"
        )
        lbl_razon.pack()
        
        # Barra de progreso
        self.progress = ttk.Progressbar(
            self.root, orient="horizontal", length=380, mode="determinate"
        )
        self.progress.pack(pady=10)
        
        # Temporizador
        self.remaining = 60
        self.update_timer()
    
    def _on_close(self):
        """Maneja el cierre de la ventana"""
        global _active_alert_window
        with _active_alert_lock:
            if _active_alert_window == self:
                _active_alert_window = None
        self.root.destroy()
    
    def update_timer(self):
        """Actualiza la barra de progreso"""
        if self.remaining > 0:
            self.remaining -= 1
            step = (60 - self.remaining) / 60 * 100
            self.progress['value'] = step
            self.root.after(1000, self.update_timer)
        else:
            self._on_close()
    
    def show(self):
        """Muestra la alerta"""
        self.root.mainloop()

def _close_existing_alert():
    """Cierra cualquier ventana de alerta existente"""
    global _active_alert_window
    with _active_alert_lock:
        if _active_alert_window is not None:
            try:
                _active_alert_window.root.destroy()
            except:
                pass
            _active_alert_window = None

def mostrar_alerta(decision: str, razon: str, duracion: str = "3-5 MIN"):
    """Función helper para mostrar alertas desde cualquier hilo"""
    def _show():
        global _active_alert_window
        
        # Cerrar cualquier ventana anterior PRIMERO
        _close_existing_alert()
        
        # Crear y mostrar nueva alerta
        app = TradingAlert(decision, razon, duracion)
        
        with _active_alert_lock:
            _active_alert_window = app
        
        app.show()
        
        # Limpiar referencia cuando termine
        with _active_alert_lock:
            if _active_alert_window == app:
                _active_alert_window = None
    
    # Ejecutar en hilo separado para no bloquear
    thread = threading.Thread(target=_show, daemon=True)
    thread.start()
