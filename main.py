"""Punto di ingresso dell'applicazione ITS Manager.

Configura il logging degli accessi, inizializza il database (creandolo e
popolandolo al primo avvio se necessario) e avvia la finestra Tkinter
principale dell'interfaccia grafica (classe AppGUI).
"""

import logging
import tkinter as tk
from database import DatabaseManager
from gui import AppGUI

# Configurazione iniziale del sistema di log degli accessi richiesto
logging.basicConfig(
    filename="accessi.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    # 1. Inizializza il database relazionale ed inserisce i dati iniziali se vuoto
    db_manager = DatabaseManager()
    
    # 2. Avvia la finestra Tkinter principale
    root = tk.Tk()
    
    # 3. Istanzia l'interfaccia grafica passando il gestore del DB
    app = AppGUI(root, db_manager)
    
    # 4. Loop principale di ascolto eventi dell'applicazione desktop
    root.mainloop()