"""
🔔 ALERTS SERVICE
Responsabilidad: UI Thread-Safe para alertas de trading
"""

import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, Callable

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
    
    def update_timer(self):
        """Actualiza la barra de progreso"""
        if self.remaining > 0:
            self.remaining -= 1
            step = (60 - self.remaining) / 60 * 100
            self.progress['value'] = step
            self.root.after(1000, self.update_timer)
        else:
            self.root.destroy()
    
    def show(self):
        """Muestra la alerta"""
        self.root.mainloop()

def mostrar_alerta(decision: str, razon: str, duracion: str = "3-5 MIN"):
    """Función helper para mostrar alertas desde cualquier hilo"""
    def _show():
        app = TradingAlert(decision, razon, duracion)
        app.show()
    
    # Ejecutar en hilo separado para no bloquear
    thread = threading.Thread(target=_show, daemon=True)
    thread.start()
