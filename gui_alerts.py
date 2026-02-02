"""
🔔 gui_alerts.py - Ventana emergente para señales de trading
"""
import tkinter as tk
from tkinter import ttk
import threading

class TradingAlert:
    def __init__(self, decision, razon, duracion="3-5 MIN", confianza="ALTA"):
        self.root = tk.Tk()
        self.decision = decision.upper()
        self.razon = razon
        self.duracion = duracion
        self.confianza = confianza
        self.setup_ui()

    def setup_ui(self):
        # Configuración de ventana
        self.root.title(f"🤖 SEÑAL IA: {self.decision}")
        self.root.geometry("400x350")
        self.root.attributes("-topmost", True) # Siempre encima
        
        # Colores dinámicos
        bg_color = "#1b5e20" if "CALL" in self.decision or "SUBE" in self.decision else "#b71c1c"
        if "ESPERAR" in self.decision or "NEUTRAL" in self.decision:
            bg_color = "#424242"
            
        self.root.configure(bg=bg_color)

        # 1. Título Gigante (CALL / PUT)
        lbl_action = tk.Label(self.root, text=self.decision, font=("Arial", 40, "bold"), fg="white", bg=bg_color)
        lbl_action.pack(pady=20)

        # 2. Duración
        lbl_time = tk.Label(self.root, text=f"⏱️ TIEMPO: {self.duracion}", font=("Arial", 16), fg="white", bg=bg_color)
        lbl_time.pack(pady=5)

        # 3. Razón (Texto ajustado)
        frame_razon = tk.Frame(self.root, bg="white", padx=10, pady=10)
        frame_razon.pack(fill="both", expand=True, padx=20, pady=20)
        
        lbl_razon = tk.Label(frame_razon, text=self.razon, font=("Arial", 11), fg="black", bg="white", wraplength=350, justify="center")
        lbl_razon.pack()

        # 4. Barra de progreso (Temporizador de cierre)
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=380, mode="determinate")
        self.progress.pack(pady=10)
        
        # Iniciar cuenta regresiva (60 segundos)
        self.remaining = 60
        self.update_timer()

    def update_timer(self):
        if self.remaining > 0:
            self.remaining -= 1
            step = (60 - self.remaining) / 60 * 100
            self.progress['value'] = step
            self.root.after(1000, self.update_timer)
        else:
            self.root.destroy() # Cerrar automáticamente

    def show(self):
        self.root.mainloop()

def mostrar_alerta(decision, razon, duracion="3-5 MIN"):
    """Función helper para llamar desde main.py"""
    app = TradingAlert(decision, razon, duracion)
    app.show()

# Prueba rápida si ejecutas este archivo solo
if __name__ == "__main__":
    mostrar_alerta("CALL (COMPRA)", "Ruptura de resistencia con volumen alto", "5 MIN")