import sqlite3
import csv
import os
import logging
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from auth import AuthManager
from persone import Studente
from database import DatabaseManager

# Corsi attivi dell'istituto: lista di tuple immutabili (nome_corso, anno_accademico)
CORSI_ATTIVI: list[tuple[str, str]] = [
    ("Programmazione Python", "2025/2026"),
    ("Basi di Dati SQL", "2025/2026"),
    ("Sistemi e Reti", "2025/2026"),
    ("Cybersecurity", "2025/2026"),
]


class AppGUI:
    """Interfaccia grafica principale dell'applicazione ITS Manager.

    Costruisce e gestisce, tramite Tkinter/ttk, l'intero ciclo di vita
    della finestra applicativa: schermata di login, dashboard con
    statistiche, gestione di voti e anagrafica in base al ruolo
    dell'utente collegato (Amministratore, Docente, Studente).
    """

    def __init__(self, root: tk.Tk, db_manager: DatabaseManager) -> None:
        """Inizializza la finestra principale, il tema grafico e lo stato di sessione.

        Args:
            root: finestra Tkinter principale su cui costruire l'interfaccia.
            db_manager: gestore del database già inizializzato, da cui viene
                ricavato il percorso del file SQLite utilizzato da AuthManager
                e da tutte le query dell'applicazione.
        """
        self.root = root
        self.db = db_manager
        self.auth = AuthManager(self.db.db_name)
        self.root.title("ITS Manager - Pannello di Controllo e Dashbord")
        
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Palette Cyber Dark / Analytics Enterprise
        self.bg_main = "#0F172A"       
        self.bg_panel = "#1E293B"      
        self.bg_input = "#334155"      
        self.color_accent = "#38BDF8"  
        self.color_success = "#4ADE80" 
        self.color_warning = "#FB923C" 
        self.color_danger = "#F87171"  
        self.text_main = "#F8FAFC"     
        self.text_muted = "#94A3B8"    
        
        self.root.configure(bg=self.bg_main)
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Stile Tabelle adattato alla Dark Mode
        self.style.configure("Treeview", background=self.bg_panel, foreground=self.text_main, rowheight=28, fieldbackground=self.bg_panel, font=("Segoe UI", 10), borderwidth=0)
        self.style.map("Treeview", background=[("selected", self.color_accent)], foreground=[("selected", self.bg_main)])
        self.style.configure("Treeview.Heading", background=self.bg_main, foreground=self.color_accent, font=("Segoe UI", 10, "bold"), borderwidth=0)
        
        self.id_voto_in_modifica = None
        self.id_persona_in_modifica = None
        
        self.utente_connesso = ""      
        self.ruolo_connesso = ""       
        self.nome_reale_connesso = ""  
        
        self.schermata_login()

    def pulisci_finestra(self) -> None:
        """Distrugge tutti i widget figli della finestra principale.

        Utilizzato prima di ridisegnare una nuova schermata (login o
        dashboard), in modo da ripartire sempre da una finestra vuota.
        """
        for widget in self.root.winfo_children():
            widget.destroy()

    def schermata_login(self) -> None:
        """Disegna la schermata di autenticazione iniziale.

        Crea una finestra di dimensioni fisse con i campi per l'inserimento
        di username e password e il pulsante che avvia la procedura di
        login tramite ``esegui_login``.
        """
        self.pulisci_finestra()
        self.root.geometry("440x420")
        self.root.resizable(False, False) 
        
        card = tk.Frame(self.root, bg=self.bg_panel, highlightbackground=self.bg_input, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        tk.Label(card, text="ITS MANAGER", font=("Segoe UI", 18, "bold"), fg=self.color_accent, bg=self.bg_panel).pack(pady=(30, 2))
        tk.Label(card, text="Pannello di Controllo Centralizzato", font=("Segoe UI", 9), fg=self.text_muted, bg=self.bg_panel).pack(pady=(0, 30))

        tk.Label(card, text="Identificativo Utente", font=("Segoe UI", 9, "bold"), fg=self.text_main, bg=self.bg_panel).pack(anchor="w", padx=45)
        self.ent_username = tk.Entry(card, font=("Segoe UI", 11), bg=self.bg_input, fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground=self.bg_input, highlightthickness=1)
        self.ent_username.pack(fill=tk.X, padx=45, pady=(6, 16), ipady=6)

        tk.Label(card, text="Chiave di Autenticazione", font=("Segoe UI", 9, "bold"), fg=self.text_main, bg=self.bg_panel).pack(anchor="w", padx=45)
        self.ent_password = tk.Entry(card, show="*", font=("Segoe UI", 11), bg=self.bg_input, fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground=self.bg_input, highlightthickness=1)
        self.ent_password.pack(fill=tk.X, padx=45, pady=(6, 25), ipady=6)

        btn_login = tk.Button(card, text="Inizializza Sessione", command=self.esegui_login, bg=self.color_accent, fg=self.bg_main, font=("Segoe UI", 11, "bold"), bd=0, cursor="hand2", activebackground=self.text_main, activeforeground=self.bg_main)
        btn_login.pack(fill=tk.X, padx=45, pady=(5, 15), ipady=8)

    def esegui_login(self) -> None:
        """Gestisce il tentativo di login delegando verifica e logging ad AuthManager."""
        username = self.ent_username.get().strip()
        password = self.ent_password.get()

        if not username or not password:
            messagebox.showwarning("Dati Incompleti", "Inserire i parametri di identificazione richiesti.")
            return

        # AuthManager verifica le credenziali e registra il tentativo (OK o fallito) su accessi.log
        successo, ruolo = self.auth.login(username, password)

        if not successo:
            messagebox.showerror("Accesso Negato", "Parametri di sicurezza non validi.")
            return

        self.utente_connesso = username
        self.ruolo_connesso = ruolo

        try:
            with sqlite3.connect(self.db.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nome FROM persone WHERE email = ? OR nome = ?", (username, username))
                persona = cursor.fetchone()
                self.nome_reale_connesso = persona[0].capitalize() if persona else username.capitalize()
        except sqlite3.Error as e:
            messagebox.showerror("Errore Database", str(e))
            self.nome_reale_connesso = username.capitalize()

        self.dashboard_principale()

    def dashboard_principale(self) -> None:
        """Costruisce la schermata principale dell'applicazione dopo il login.

        Disegna, in base al ruolo dell'utente collegato (``self.ruolo_connesso``):
        la barra superiore con nome utente e pulsanti di sessione/esportazione;
        la colonna destra con le statistiche aggregate dell'istituto (numero
        studenti/docenti, media voti, percentuale promossi, ecc.); la colonna
        sinistra con le tabelle interattive di voti e anagrafica e i relativi
        form di inserimento/modifica, visibili solo ai ruoli autorizzati.
        """
        self.pulisci_finestra()
        self.root.geometry("1440x840") 
        self.root.resizable(True, True)

        # Header superiore ad alto contrasto
        top_bar = tk.Frame(self.root, bg=self.bg_panel, height=60)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)
        
        testo_profilo = f" ⚡ Livello di Accesso: {self.ruolo_connesso.capitalize()} ({self.nome_reale_connesso.capitalize()})"
        tk.Label(top_bar, text=testo_profilo, font=("Segoe UI", 10, "bold"), fg=self.color_accent, bg=self.bg_panel).pack(side=tk.LEFT, padx=25)
        tk.Button(top_bar, text="Termina Sessione", command=self.schermata_login, bg=self.bg_input, fg=self.text_main, bd=0, font=("Segoe UI", 9, "bold"), padx=15, pady=6, cursor="hand2", activebackground=self.color_danger, activeforeground=self.bg_main).pack(side=tk.RIGHT, padx=25, pady=14)
        if self.ruolo_connesso in ["Amministratore", "Docente"]:
            tk.Button(top_bar, text="Esporta Report CSV", command=self.esporta_report, bg=self.bg_input, fg=self.color_success, bd=0, font=("Segoe UI", 9, "bold"), padx=15, pady=6, cursor="hand2").pack(side=tk.RIGHT, padx=(0, 10), pady=14)

        # Contenitore Principale a Due Colonne (Sinistra: Tabelle/Form, Destra: Analytics come nel widget di esempio)
        main_container = tk.Frame(self.root, bg=self.bg_main)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        left_column = tk.Frame(main_container, bg=self.bg_main)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        right_column = tk.Frame(main_container, bg=self.bg_panel, width=360, highlightbackground=self.bg_input, highlightthickness=1)
        right_column.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_column.pack_propagate(False)

        # ====================================================
        # COLONNA DESTRA: STATISTICHE ISTITUTO (Dati Reali)
        # ====================================================
        titolo_frame = tk.Frame(right_column, bg=self.bg_panel)
        titolo_frame.pack(fill=tk.X, pady=(20, 15))
        tk.Label(titolo_frame, text="STATISTICHE ISTITUTO", font=("Segoe UI", 11, "bold"), fg=self.color_accent, bg=self.bg_panel).pack()
        
        with sqlite3.connect(self.db.db_name) as conn:
            cur = conn.cursor()
            # Conteggi reali
            n_studenti = cur.execute("SELECT COUNT(*) FROM persone WHERE ruolo_scolastico = 'Studente'").fetchone()[0]
            n_docenti = cur.execute("SELECT COUNT(*) FROM persone WHERE ruolo_scolastico = 'Docente'").fetchone()[0]
            # Media voti
            media = cur.execute("SELECT AVG(voto) FROM voti").fetchone()[0] or 0
            # Esami sostenuti
            n_esami = cur.execute("SELECT COUNT(*) FROM voti").fetchone()[0]
            # Percentuale di studenti promossi (voto >= 18 sul totale delle valutazioni)
            n_promossi = cur.execute("SELECT COUNT(*) FROM voti WHERE voto >= 18").fetchone()[0]
            perc_promossi = (n_promossi / n_esami * 100) if n_esami > 0 else 0
            # Materia con la media voti più alta
            riga_top = cur.execute(
                "SELECT materia, AVG(voto) AS media_materia FROM voti GROUP BY materia ORDER BY media_materia DESC LIMIT 1"
            ).fetchone()
            materia_top = riga_top[0] if riga_top else "N/D"
        
        # Helper per creare i widget di statistica
        def crea_stat(parent: tk.Widget, label: str, valore: str, colore: str) -> None:
            """Crea e impacchetta un piccolo riquadro etichetta/valore nella colonna statistiche.

            Args:
                parent: widget contenitore in cui inserire il riquadro.
                label: didascalia descrittiva della statistica (es. "Esami Sostenuti").
                valore: valore numerico/testuale già formattato da visualizzare.
                colore: colore esadecimale del testo del valore, per evidenziarlo.
            """
            frame = tk.Frame(parent, bg=self.bg_panel)
            frame.pack(fill=tk.X, padx=20, pady=8)
            # Aggiunto wraplength per evitare che il testo esca dal frame
            tk.Label(frame, text=label, font=("Segoe UI", 9), fg=self.text_muted, bg=self.bg_panel, wraplength=320, justify="center").pack()
            tk.Label(frame, text=valore, font=("Segoe UI", 16, "bold"), fg=colore, bg=self.bg_panel).pack(pady=5)

        crea_stat(right_column, "Docenti in Organico", str(n_docenti), self.text_main)
        crea_stat(right_column, "Studenti Registrati", str(n_studenti), self.text_main)
        crea_stat(right_column, "Esami Sostenuti", str(n_esami), self.text_main)
        crea_stat(right_column, "Media Voti Generale", f"{media:.2f}", self.color_success)
        crea_stat(right_column, "% Studenti Promossi", f"{perc_promossi:.1f}%", self.color_accent)
        crea_stat(right_column, "Materia Media Più Alta", materia_top, self.color_success)

        # Bottone di aggiornamento
        tk.Button(right_column, text="Aggiorna Dati", command=self.dashboard_principale, 
                  bg=self.bg_input, fg=self.color_accent, font=("Segoe UI", 9, "bold"), 
                  bd=0, cursor="hand2").pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20, ipady=5)

        # ====================================================
        # COLONNA SINISTRA - SEZIONE 1: REGISTRO VALUTAZIONI
        # ====================================================
        frame_titolo_voti = tk.Frame(left_column, bg=self.bg_main)
        frame_titolo_voti.pack(fill=tk.X, pady=(5, 5))
        tk.Label(frame_titolo_voti, text="📜 Registro Valutazioni Didattiche", font=("Segoe UI", 12, "bold"), fg=self.text_main, bg=self.bg_main).pack(side=tk.LEFT)
        
        if self.ruolo_connesso in ["Amministratore", "Docente"]:
            tk.Button(frame_titolo_voti, text="✕ Elimina Voto", command=self.elimina_voto_selezionato, bg=self.color_danger, fg=self.bg_main, font=("Segoe UI", 9, "bold"), bd=0, padx=12, pady=4, cursor="hand2", activebackground=self.text_main).pack(side=tk.RIGHT)

        self.albero = ttk.Treeview(left_column, columns=("ID", "Studente", "Materia", "Voto"), show="headings", height=5)
        self.albero.heading("ID", text="ID")
        self.albero.heading("Studente", text="Studente")
        self.albero.heading("Materia", text="Materia / Corso")
        self.albero.heading("Voto", text="Valutazione")
        self.albero.column("ID", width=60, anchor=tk.CENTER, stretch=False)
        self.albero.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.albero.bind("<<TreeviewSelect>>", self.carica_voto_selezionato)
        self.aggiorna_tabella_voti()

        if self.ruolo_connesso in ["Amministratore", "Docente"]:
            frame_ins = tk.LabelFrame(left_column, text=" Operazioni Record ", font=("Segoe UI", 9, "bold"), fg=self.color_accent, bg=self.bg_panel, bd=0, highlightbackground=self.bg_input, highlightthickness=1)
            frame_ins.pack(fill=tk.X, pady=(5, 15), ipady=8)
            frame_ins.columnconfigure((1, 3, 5), weight=1)

            tk.Label(frame_ins, text="Studente:", bg=self.bg_panel, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=(15,5), pady=8, sticky="w")
            self.ent_stud = tk.Entry(frame_ins, font=("Segoe UI", 10), bg=self.bg_input, fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground=self.bg_input, highlightthickness=1)
            self.ent_stud.grid(row=0, column=1, padx=5, pady=8, ipady=4, sticky="ew")

            tk.Label(frame_ins, text="Materia:", bg=self.bg_panel, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=(15,5), pady=8, sticky="w")
            # Combobox popolata dalla tupla CORSI_ATTIVI (nome_corso, anno_accademico)
            self.ent_mat = ttk.Combobox(frame_ins, values=[c[0] for c in CORSI_ATTIVI], font=("Segoe UI", 10))
            self.ent_mat.grid(row=0, column=3, padx=5, pady=8, ipady=4, sticky="ew")

            tk.Label(frame_ins, text="Voto:", bg=self.bg_panel, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=0, column=4, padx=(15,5), pady=8, sticky="w")
            self.ent_voto = tk.Entry(frame_ins, font=("Segoe UI", 10), bg=self.bg_input, fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground=self.bg_input, highlightthickness=1)
            self.ent_voto.grid(row=0, column=5, padx=5, pady=8, ipady=4, sticky="ew")

            tk.Button(frame_ins, text="Inserisci", command=self.salva_voto_db, bg=self.color_success, fg=self.bg_main, font=("Segoe UI", 9, "bold"), bd=0, padx=14, cursor="hand2").grid(row=0, column=6, padx=(15, 5), pady=8, ipady=4, sticky="e")
            tk.Button(frame_ins, text="Modifica", command=self.modifica_voto_db, bg=self.color_warning, fg=self.bg_main, font=("Segoe UI", 9, "bold"), bd=0, padx=14, cursor="hand2").grid(row=0, column=7, padx=(5, 15), pady=8, ipady=4, sticky="e")
            tk.Button(frame_ins, text="Calcola Media", command=self.calcola_media_studente, bg=self.color_accent, fg=self.bg_main, font=("Segoe UI", 9, "bold"), bd=0, padx=14, cursor="hand2").grid(row=0, column=8, padx=(5, 15), pady=8, ipady=4, sticky="e")

        # ====================================================
        # COLONNA SINISTRA - SEZIONE 2: ANAGRAFICA ISTITUTO
        # ====================================================
        frame_titolo_pers = tk.Frame(left_column, bg=self.bg_main)
        frame_titolo_pers.pack(fill=tk.X, pady=(5, 5))
        tk.Label(frame_titolo_pers, text="👥 Organigramma e Anagrafica Istituto", font=("Segoe UI", 12, "bold"), fg=self.text_main, bg=self.bg_main).pack(side=tk.LEFT)
        
        if self.ruolo_connesso == "Amministratore":
            tk.Button(frame_titolo_pers, text="✕ Rimuovi Scheda", command=self.elimina_persona_selezionata, bg=self.color_danger, fg=self.bg_main, font=("Segoe UI", 9, "bold"), bd=0, padx=12, pady=4, cursor="hand2", activebackground=self.text_main).pack(side=tk.RIGHT)

        self.albero_persone = ttk.Treeview(left_column, columns=("ID", "Nome", "Qualifica", "Età", "Indirizzo", "Email", "Telefono", "Materia"), show="headings", height=6)
        self.albero_persone.heading("ID", text="ID")
        self.albero_persone.heading("Nome", text="Cognome e Nome")
        self.albero_persone.heading("Qualifica", text="Profilo")
        self.albero_persone.heading("Età", text="Età")
        self.albero_persone.heading("Indirizzo", text="Domicilio")
        self.albero_persone.heading("Email", text="Email")
        self.albero_persone.heading("Telefono", text="Telefono")
        self.albero_persone.heading("Materia", text="Modulo Assegnato")
        
        self.albero_persone.column("ID", width=45, anchor=tk.CENTER, stretch=False)
        self.albero_persone.column("Nome", width=160, stretch=True)
        self.albero_persone.column("Qualifica", width=100, anchor=tk.CENTER, stretch=False)
        self.albero_persone.column("Età", width=45, anchor=tk.CENTER, stretch=False)
        self.albero_persone.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.albero_persone.tag_configure('docente', background='#1E293B', foreground=self.color_accent)  
        self.albero_persone.tag_configure('studente', background='#1E293B', foreground=self.text_main) 
        
        if self.ruolo_connesso == "Amministratore":
            self.albero_persone.bind("<<TreeviewSelect>>", self.carica_persona_selezionata)
        self.aggiorna_tabella_anagrafica()

        if self.ruolo_connesso == "Amministratore":
            frame_pers = tk.LabelFrame(left_column, text=" Configurazione Record Anagrafico ", font=("Segoe UI", 9, "bold"), fg=self.color_accent, bg=self.bg_panel, bd=0, highlightbackground=self.bg_input, highlightthickness=1)
            frame_pers.pack(fill=tk.X, pady=(15, 15), padx=0, ipady=10)
            frame_pers.columnconfigure((1, 3, 5, 7), weight=1)

            tk.Label(frame_pers, text="Nome:", bg=self.bg_panel, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=(15,5), pady=6, sticky="w")
            self.ent_pers_nome = tk.Entry(frame_pers, font=("Segoe UI", 10), bg=self.bg_input, fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground=self.bg_input, highlightthickness=1)
            self.ent_pers_nome.grid(row=0, column=1, padx=5, pady=6, ipady=3, sticky="ew")

            tk.Label(frame_pers, text="Ruolo:", bg=self.bg_panel, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=(15,5), pady=6, sticky="w")
            self.cmb_pers_ruolo = ttk.Combobox(frame_pers, values=["Studente", "Docente"], state="readonly", font=("Segoe UI", 9))
            self.cmb_pers_ruolo.grid(row=0, column=3, padx=5, pady=6, sticky="ew")

            tk.Label(frame_pers, text="Età:", bg=self.bg_panel, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=0, column=4, padx=(15,5), pady=6, sticky="w")
            self.ent_pers_eta = tk.Entry(frame_pers, font=("Segoe UI", 10), bg=self.bg_input, fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground=self.bg_input, highlightthickness=1)
            self.ent_pers_eta.grid(row=0, column=5, padx=5, pady=6, ipady=3, sticky="ew")

            tk.Label(frame_pers, text="Materia:", bg=self.bg_panel, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=0, column=6, padx=(15,5), pady=6, sticky="w")
            self.ent_pers_mat = tk.Entry(frame_pers, font=("Segoe UI", 10), bg=self.bg_input, fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground=self.bg_input, highlightthickness=1)
            self.ent_pers_mat.grid(row=0, column=7, padx=5, pady=6, ipady=3, sticky="ew")

            tk.Label(frame_pers, text="Domicilio:", bg=self.bg_panel, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, padx=(15,5), pady=6, sticky="w")
            self.ent_pers_ind = tk.Entry(frame_pers, font=("Segoe UI", 10), bg=self.bg_input, fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground=self.bg_input, highlightthickness=1)
            self.ent_pers_ind.grid(row=1, column=1, padx=5, pady=6, ipady=3, sticky="ew")

            tk.Label(frame_pers, text="Email:", bg=self.bg_panel, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=1, column=2, padx=(15,5), pady=6, sticky="w")
            self.ent_pers_email = tk.Entry(frame_pers, font=("Segoe UI", 10), bg=self.bg_input, fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground=self.bg_input, highlightthickness=1)
            self.ent_pers_email.grid(row=1, column=3, padx=5, pady=6, ipady=3, sticky="ew")

            tk.Label(frame_pers, text="Tel:", bg=self.bg_panel, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=1, column=4, padx=(15,5), pady=6, sticky="w")
            self.ent_pers_tel = tk.Entry(frame_pers, font=("Segoe UI", 10), bg=self.bg_input, fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground=self.bg_input, highlightthickness=1)
            self.ent_pers_tel.grid(row=1, column=5, padx=5, pady=6, ipady=3, sticky="ew")

            # Allineati esattamente sotto il box "Materia" (stesse colonne 6-7, stessa riga del Tel)
            frame_btn_azioni = tk.Frame(frame_pers, bg=self.bg_panel)
            frame_btn_azioni.grid(row=1, column=6, columnspan=2, padx=15, pady=6, sticky="ew")
            frame_btn_azioni.columnconfigure((0, 1), weight=1)

            tk.Button(frame_btn_azioni, text="+ Aggiungi", command=self.salva_persona_db, bg=self.color_accent, fg=self.bg_main, font=("Segoe UI", 9, "bold"), bd=0, padx=12, pady=4, cursor="hand2").grid(row=0, column=0, padx=(0, 3), sticky="ew")
            tk.Button(frame_btn_azioni, text="⚙ Modifica", command=self.modifica_persona_db, bg=self.color_warning, fg=self.bg_main, font=("Segoe UI", 9, "bold"), bd=0, padx=12, pady=4, cursor="hand2").grid(row=0, column=1, padx=(3, 0), sticky="ew")

    def carica_voto_selezionato(self, event: tk.Event) -> None:
        """Copia il voto selezionato nella tabella nei campi di modifica.

        Args:
            event: evento Tkinter ``<<TreeviewSelect>>`` generato dal click
                dell'utente sulla riga della tabella dei voti.
        """
        item = self.albero.selection()
        if not item: return
        valori = self.albero.item(item, "values")
        self.id_voto_in_modifica = valori[0]
        self.ent_stud.delete(0, tk.END); self.ent_stud.insert(0, valori[1])
        self.ent_mat.delete(0, tk.END); self.ent_mat.insert(0, valori[2])
        self.ent_voto.delete(0, tk.END); self.ent_voto.insert(0, valori[3])

    def carica_persona_selezionata(self, event: tk.Event) -> None:
        """Copia la persona selezionata nella tabella nei campi del form anagrafico.

        Args:
            event: evento Tkinter ``<<TreeviewSelect>>`` generato dal click
                dell'utente sulla riga della tabella anagrafica.
        """
        item = self.albero_persone.selection()
        if not item: return
        valori = self.albero_persone.item(item, "values")
        self.id_persona_in_modifica = valori[0]
        
        self.ent_pers_nome.delete(0, tk.END); self.ent_pers_nome.insert(0, valori[1])
        self.cmb_pers_ruolo.set(valori[2])
        self.ent_pers_eta.delete(0, tk.END); self.ent_pers_eta.insert(0, valori[3])
        self.ent_pers_ind.delete(0, tk.END); self.ent_pers_ind.insert(0, valori[4])
        self.ent_pers_email.delete(0, tk.END); self.ent_pers_email.insert(0, valori[5])
        self.ent_pers_tel.delete(0, tk.END); self.ent_pers_tel.insert(0, valori[6])
        self.ent_pers_mat.delete(0, tk.END); self.ent_pers_mat.insert(0, valori[7])

    def modifica_voto_db(self) -> None:
        """Aggiorna sul database il voto attualmente selezionato in tabella.

        Legge i valori correnti dai campi ``ent_stud``, ``ent_mat`` ed
        ``ent_voto`` e li scrive sulla riga con id ``id_voto_in_modifica``,
        precedentemente impostato da ``carica_voto_selezionato``.
        """
        if not self.id_voto_in_modifica:
            messagebox.showwarning("Interrogazione di Sistema", "Selezionare prima l'entità record target.")
            return
        studente = self.ent_stud.get()
        materia = self.ent_mat.get()
        voto_str = self.ent_voto.get()
        try:
            voto = int(voto_str)
            with sqlite3.connect(self.db.db_name) as conn:
                conn.cursor().execute("UPDATE voti SET studente = ?, materia = ?, voto = ? WHERE id = ?", (studente, materia, voto, self.id_voto_in_modifica))
                conn.commit()
            self.id_voto_in_modifica = None 
            self.aggiorna_tabella_voti()
        except ValueError:
            messagebox.showerror("Errore di Formato", "Il campo valutazione richiede un intero di tipo INT.")

    def modifica_persona_db(self) -> None:
        """Aggiorna sul database l'anagrafica della persona in modifica.

        Legge i valori correnti dai campi del form anagrafico e li scrive
        sulla riga con id ``id_persona_in_modifica``, precedentemente
        impostato da ``carica_persona_selezionata``.
        """
        if not self.id_persona_in_modifica:
            messagebox.showwarning("Interrogazione di Sistema", "Nessuna entità anagrafica selezionata.")
            return
        nome = self.ent_pers_nome.get()
        ruolo = self.cmb_pers_ruolo.get()
        eta = self.ent_pers_eta.get()
        ind = self.ent_pers_ind.get()
        email = self.ent_pers_email.get()
        tel = self.ent_pers_tel.get()
        mat = self.ent_pers_mat.get()
        try:
            with sqlite3.connect(self.db.db_name) as conn:
                conn.cursor().execute("UPDATE persone SET nome = ?, ruolo_scolastico = ?, eta = ?, indirizzo = ?, email = ?, telefono = ?, materia = ? WHERE id = ?", (nome, ruolo, int(eta), ind, email, tel, mat, self.id_persona_in_modifica))
                conn.commit()
            self.id_persona_in_modifica = None
            self.aggiorna_tabella_anagrafica()
            self._pulisci_campi_anagrafica()
        except Exception:
            messagebox.showerror("Esecuzione Interrotta", "Errore strutturale nella modifica dei parametri.")

    def salva_voto_db(self) -> None:
        """Inserisce un nuovo voto nel database a partire dai campi del form.

        Legge studente, materia e voto dai rispettivi campi di input e li
        salva come nuova riga nella tabella ``voti``; in caso di errore di
        formato mostra un messaggio all'utente senza interrompere l'app.
        """
        studente = self.ent_stud.get()
        materia = self.ent_mat.get()
        voto_str = self.ent_voto.get()
        try:
            with sqlite3.connect(self.db.db_name) as conn:
                conn.cursor().execute("INSERT INTO voti (studente, materia, voto) VALUES (?, ?, ?)", (studente, materia, int(voto_str)))
                conn.commit()
            self.aggiorna_tabella_voti()
        except ValueError:
            messagebox.showerror("Errore di Scrittura", "Fallimento dell'operazione di inserimento.")

    def salva_persona_db(self) -> None:
        """Inserisce una nuova persona (studente o docente) nel database.

        Legge tutti i campi del form anagrafico e li salva come nuova riga
        nella tabella ``persone``; il campo materia viene impostato a "-"
        automaticamente se il ruolo selezionato non è "Docente".
        """
        nome = self.ent_pers_nome.get()
        ruolo = self.cmb_pers_ruolo.get()
        eta_str = self.ent_pers_eta.get()
        ind = self.ent_pers_ind.get()
        email = self.ent_pers_email.get()
        tel = self.ent_pers_tel.get()
        mat = self.ent_pers_mat.get() if ruolo == "Docente" else "-"
        try:
            with sqlite3.connect(self.db.db_name) as conn:
                conn.cursor().execute("INSERT INTO persone (nome, ruolo_scolastico, eta, indirizzo, email, telefono, materia) VALUES (?, ?, ?, ?, ?, ?, ?)", (nome, ruolo, int(eta_str), ind, email, tel, mat))
                conn.commit()
            self.aggiorna_tabella_anagrafica()
            self._pulisci_campi_anagrafica()
        except Exception:
            messagebox.showerror("Errore di Scrittura", "Inconsistenza rilevata nell'input dell'istanza.")

    def calcola_media_studente(self) -> None:
        """Calcola la media di uno studente istanziando la classe OOP Studente.

        Legge i voti dello studente indicato nel campo 'Studente' dal database,
        li carica nel dizionario {materia: voto} dell'oggetto Studente
        (persone.py) e ne calcola la media tramite calcola_media().
        """
        nome_studente = self.ent_stud.get().strip()
        if not nome_studente:
            messagebox.showwarning("Dato mancante", "Inserire il nome dello studente nel campo 'Studente'.")
            return

        with sqlite3.connect(self.db.db_name) as conn:
            righe = conn.cursor().execute(
                "SELECT materia, voto FROM voti WHERE studente = ?", (nome_studente,)
            ).fetchall()

        if not righe:
            messagebox.showinfo("Nessun voto", f"Nessuna valutazione trovata per '{nome_studente}'.")
            return

        # Istanzio l'oggetto Studente e popolo il dizionario voti (dato dal DB)
        studente_obj = Studente(nome=nome_studente, eta=0, indirizzo="")
        for materia, voto in righe:
            studente_obj.aggiungi_voto(materia, voto)

        media = studente_obj.calcola_media()
        dettaglio_voti = "\n".join(f"  - {m}: {v}" for m, v in studente_obj.voti.items())
        messagebox.showinfo(
            "Media calcolata",
            f"Studente: {studente_obj.nome}\n\nVoti registrati:\n{dettaglio_voti}\n\nMedia: {media:.2f}",
        )

    def esporta_report(self) -> None:
        """Esporta anagrafica, voti e log accessi in tre file CSV distinti.

        Ogni file contiene una singola tabella con colonne omogenee (stesso
        numero di colonne su ogni riga), così da essere interpretato
        correttamente da qualunque programma di fogli di calcolo senza
        bisogno di un import manuale con scelta del delimitatore.
        Usa ';' come separatore e BOM UTF-8 per compatibilità con Excel ITA.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_anagrafica = f"report_anagrafica_{timestamp}.csv"
        file_voti = f"report_voti_{timestamp}.csv"
        file_accessi = f"report_accessi_{timestamp}.csv"

        try:
            with sqlite3.connect(self.db.db_name) as conn:
                cursor = conn.cursor()
                persone = cursor.execute(
                    "SELECT nome, ruolo_scolastico, eta, email FROM persone ORDER BY ruolo_scolastico, nome"
                ).fetchall()
                voti = cursor.execute("SELECT studente, materia, voto FROM voti").fetchall()

            with open(file_anagrafica, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Nome", "Ruolo", "Eta", "Email"])
                writer.writerows(persone)

            with open(file_voti, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Studente", "Materia", "Voto"])
                writer.writerows(voti)

            with open(file_accessi, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
                writer.writerow(["Data e Ora", "Livello", "Messaggio"])
                try:
                    with open("accessi.log", "r", encoding="utf-8") as log_file:
                        for riga in log_file.readlines()[-20:]:
                            riga = riga.strip()
                            if not riga:
                                continue
                            # Il log ha formato "TIMESTAMP - LIVELLO - MESSAGGIO":
                            # lo dividiamo in 3 colonne omogenee, come per gli altri report
                            parti = riga.split(" - ", 2)
                            while len(parti) < 3:
                                parti.append("")
                            writer.writerow(parti)
                except FileNotFoundError:
                    writer.writerow(["-", "-", "Nessun log accessi disponibile."])

            cartella = os.path.abspath(".")
            messagebox.showinfo(
                "Esportazione completata",
                f"Report salvati in:\n{cartella}\n\n"
                f"- {file_anagrafica}\n- {file_voti}\n- {file_accessi}",
            )
        except Exception as e:
            messagebox.showerror("Errore esportazione", f"Impossibile generare il report: {e}")

    def elimina_voto_selezionato(self) -> None:
        """Elimina dal database il voto attualmente selezionato in tabella.

        Non esegue alcuna operazione se nessuna riga risulta selezionata
        nella Treeview dei voti.
        """
        item = self.albero.selection()
        if not item: return
        id_voto = self.albero.item(item, "values")[0]
        with sqlite3.connect(self.db.db_name) as conn:
            conn.cursor().execute("DELETE FROM voti WHERE id = ?", (id_voto,))
            conn.commit()
        self.aggiorna_tabella_voti()

    def elimina_persona_selezionata(self) -> None:
        """Elimina dal database la persona attualmente selezionata in tabella.

        Non esegue alcuna operazione se nessuna riga risulta selezionata
        nella Treeview dell'anagrafica.
        """
        item = self.albero_persone.selection()
        if not item: return
        valori = self.albero_persone.item(item, "values")
        with sqlite3.connect(self.db.db_name) as conn:
            conn.cursor().execute("DELETE FROM persone WHERE id = ?", (valori[0],))
            conn.commit()
        self.aggiorna_tabella_anagrafica()

    def _pulisci_campi_anagrafica(self) -> None:
        """Svuota tutti i campi del form anagrafico dopo un salvataggio.

        Metodo privato di supporto (prefisso "_"): non fa parte
        dell'interfaccia pubblica della classe AppGUI.
        """
        self.ent_pers_nome.delete(0, tk.END); self.ent_pers_eta.delete(0, tk.END)
        self.ent_pers_ind.delete(0, tk.END); self.ent_pers_email.delete(0, tk.END)
        self.ent_pers_tel.delete(0, tk.END); self.ent_pers_mat.delete(0, tk.END)
        self.cmb_pers_ruolo.set('')

    def aggiorna_tabella_voti(self) -> None:
        """Ricarica la Treeview dei voti con i dati aggiornati dal database.

        Svuota la tabella e la ripopola leggendo tutte le righe correnti
        della tabella ``voti``; va richiamato dopo ogni inserimento,
        modifica o eliminazione di un voto.
        """
        for riga in self.albero.get_children(): self.albero.delete(riga)
        with sqlite3.connect(self.db.db_name) as conn:
            for row in conn.cursor().execute("SELECT id, studente, materia, voto FROM voti").fetchall():
                self.albero.insert("", tk.END, values=row)

    def aggiorna_tabella_anagrafica(self) -> None:
        """Ricarica la Treeview dell'anagrafica applicando il mascheramento GDPR.

        Legge tutte le persone dal database (docenti prima, poi studenti,
        ordinati per id) e, in base al ruolo dell'utente collegato,
        oscura i campi sensibili (indirizzo, email, telefono) delle persone
        diverse dall'utente stesso, secondo la logica descritta nella
        documentazione tecnica del progetto (paragrafo "Mascheramento dei
        dati sensibili").
        """
        for riga in self.albero_persone.get_children(): 
            self.albero_persone.delete(riga)
            
        with sqlite3.connect(self.db.db_name) as conn:
            cursor = conn.cursor()
            # La clausola CASE WHEN permette di forzare l'ordine: Docenti prima, Studenti dopo, e poi ordina per ID
            query = "SELECT id, nome, ruolo_scolastico, eta, indirizzo, email, telefono, materia FROM persone ORDER BY CASE WHEN ruolo_scolastico = 'Docente' THEN 1 ELSE 2 END, id ASC"
            righe_db = cursor.execute(query).fetchall()
            
            for row in righe_db:
                id_p, nome, ruolo, eta, indirizzo, email, telefono, materia = row
                
                # CORREZIONE LOGICA GDPR
                if self.ruolo_connesso == "Docente":
                    # Se sono io, non censuro nulla (saltiamo i controlli)
                    if nome.lower() != self.nome_reale_connesso.lower():
                        if ruolo == "Studente":
                            indirizzo = "Riservato (GDPR)"
                            telefono = "********"
                        elif ruolo == "Docente":
                            # Censuro solo gli ALTRI docenti
                            indirizzo = "Riservato (GDPR)"
                            email = "******@its.it"
                            telefono = "********"
                        
                elif self.ruolo_connesso == "Studente":
                    if nome.lower() != self.nome_reale_connesso.lower():
                        indirizzo = "Riservato (GDPR)"
                        email = "******@its.it"
                        telefono = "********"
                
                riga_filtrata = (id_p, nome, ruolo, eta, indirizzo, email, telefono, materia)
                
                if ruolo == "Docente":
                    self.albero_persone.insert("", tk.END, values=riga_filtrata, tags=('docente',))
                else:
                    self.albero_persone.insert("", tk.END, values=riga_filtrata, tags=('studente',))