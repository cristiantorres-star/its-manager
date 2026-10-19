import sqlite3
import hashlib
import logging

class DatabaseManager:
    """Gestisce la creazione e l'inizializzazione del database SQLite dell'applicazione.

    Si occupa di due responsabilità distinte: creare lo schema relazionale
    (tabelle utenti, voti, persone) se non esiste ancora, e popolare il
    database con i dati istituzionali di partenza al primo avvio.
    """

    def __init__(self, db_name: str = "its_manager.db") -> None:
        """Imposta il percorso del database e ne avvia l'inizializzazione.

        Args:
            db_name: nome/percorso del file SQLite da utilizzare. Se il file
                non esiste, viene creato automaticamente.
        """
        self.db_name = db_name
        self.inizializza_database()

    def inizializza_database(self) -> None:
        """Crea le tabelle dell'applicazione se non sono già presenti.

        Crea, tramite istruzioni ``CREATE TABLE IF NOT EXISTS``, le tabelle
        ``utenti`` (credenziali di accesso), ``voti`` (valutazioni degli
        studenti) e ``persone`` (anagrafica di studenti e docenti).
        In caso di successo, invoca ``_inizializza_dati_istituzionali`` per
        popolare il database con i dati di partenza se risulta vuoto.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # 1. TABELLA UTENTI
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS utenti (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    ruolo TEXT NOT NULL
                );
                """)
                
                # 2. TABELLA VOTI
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS voti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    studente TEXT NOT NULL,
                    materia TEXT NOT NULL,
                    voto INTEGER NOT NULL
                );
                """)
                
                # 3. TABELLA ANAGRAFICA PERSONE (Aggiunta colonna materia)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS persone (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    ruolo_scolastico TEXT NOT NULL,
                    eta INTEGER,
                    indirizzo TEXT,
                    email TEXT,       
                    telefono TEXT,
                    materia TEXT       -- Nuova colonna: materia per docenti
                );
                """)
                
                conn.commit()
                logging.info("Tabelle verificate con successo.")
                
                self._inizializza_dati_istituzionali()
                
        except sqlite3.Error as e:
            logging.error(f"Errore inizializzazione database: {e}")

    def _inizializza_dati_istituzionali(self) -> None:
        """Popola il database con i dati istituzionali di partenza, se vuoto.

        Metodo privato di supporto (prefisso "_"), invocato automaticamente
        da ``inizializza_database``. Se la tabella ``utenti`` risulta vuota,
        inserisce in un'unica transazione: le credenziali di accesso (con
        password hashate in SHA-256) di amministratore, docenti e studenti;
        l'anagrafica completa corrispondente in ``persone``; almeno cinque
        valutazioni storiche di esempio nella tabella ``voti``.
        Se la tabella ``utenti`` contiene già dei dati, il metodo non
        effettua alcuna operazione (evita duplicazioni ad ogni riavvio).
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM utenti")
                if cursor.fetchone()[0] == 0:
                    
                    hash_admin = hashlib.sha256("admin123".encode()).hexdigest()
                    hash_docente = hashlib.sha256("docente123".encode()).hexdigest()
                    hash_studente = hashlib.sha256("studente123".encode()).hexdigest()
                    
                    # 1. CREDENZIALI LOGIN
                    utenti_istituzionali = [
                        ("admin", hash_admin, "Amministratore"),
                        ("admin@its.it", hash_admin, "Amministratore"),
                        ("massimo.papa@its.it", hash_docente, "Docente"),
                        ("Massimo Papa", hash_docente, "Docente"),
                        ("elena.verdi@its.it", hash_docente, "Docente"),
                        ("Elena Verdi", hash_docente, "Docente"),
                        ("roberto.bianchi@its.it", hash_docente, "Docente"),
                        ("Roberto Bianchi", hash_docente, "Docente"),
                        ("annamaria.fontana@its.it", hash_docente, "Docente"),
                        ("Annamaria Fontana", hash_docente, "Docente"),
                        ("cristian.torres@its.it", hash_studente, "Studente"),
                        ("Cristian Torres", hash_studente, "Studente"),
                        ("mario.rossi@its.it", hash_studente, "Studente"),
                        ("Mario Rossi", hash_studente, "Studente"),
                        ("laura.bianchi@its.it", hash_studente, "Studente"),
                        ("Laura Bianchi", hash_studente, "Studente"),
                        ("luca.moretti@its.it", hash_studente, "Studente"),
                        ("Luca Moretti", hash_studente, "Studente"),
                        ("sofia.russo@its.it", hash_studente, "Studente"),
                        ("Sofia Russo", hash_studente, "Studente"),
                        ("federico.neri@its.it", hash_studente, "Studente"),
                        ("Federico Neri", hash_studente, "Studente")
                    ]
                    cursor.executemany("INSERT INTO utenti (username, password_hash, ruolo) VALUES (?, ?, ?)", utenti_istituzionali)
                    
                    # 2. ANAGRAFICA PERSONE (Uniformata rigorosamente in COGNOME NOME)
                    anagrafica_istituzionale = [
                        # Docenti
                        ("Papa Massimo", "Docente", 56, "Corso Stati Uniti 33, Torino", "massimo.papa@its.it", "+39 339 1112223", "Programmazione Python"),
                        ("Verdi Elena", "Docente", 38, "Via Roma, Moncalieri", "elena.verdi@its.it", "+39 335 4445556", "Basi di Dati SQL"),
                        ("Bianchi Roberto", "Docente", 45, "Corso Francia 120, Torino", "roberto.bianchi@its.it", "+39 333 1122334", "Sistemi e Reti"),
                        ("Fontana Annamaria", "Docente", 39, "Via Garibaldi 5, Moncalieri", "annamaria.fontana@its.it", "+39 347 5566778", "Cybersecurity"),
                    
                        # Studenti
                        ("Torres Cristian", "Studente", 28, "Via Milano 2, Torino", "cristian.torres@its.it", "+39 320 7778889", "-"),
                        ("Rossi Mario", "Studente", 26, "Via Francia 11, Collegno", "mario.rossi@its.it", "+39 340 1112223", "-"),
                        ("Bianchi Laura", "Studente", 19, "Via Po 123, Torino", "laura.bianchi@its.it", "+39 349 8889990", "-"),
                        ("Moretti Luca", "Studente", 21, "Corso Roma 88, Collegno", "luca.moretti@its.it", "+39 328 9988776", "-"),
                        ("Russo Sofia", "Studente", 20, "Via Madama Cristina 14, Torino", "sofia.russo@its.it", "+39 315 4433221", "-"),
                        ("Neri Federico", "Studente", 33, "Corso Vittorio Emanuele 201, Rivoli", "federico.neri@its.it", "+39 392 0011223", "-")
                    ]
                    cursor.executemany("INSERT INTO persone (nome, ruolo_scolastico, eta, indirizzo, email, telefono, materia) VALUES (?, ?, ?, ?, ?, ?, ?)", anagrafica_istituzionale)
                    
                    # 3. ALMENO 5 RISULTATI DI VOTI STORICI
                    voti_istituzionali = [
                        ("Torres Cristian", "Programmazione Python", 29),
                        ("Rossi Mario", "Basi di Dati SQL", 25),
                        ("Bianchi Laura", "Sistemi e Reti", 30),
                        ("Moretti Luca", "Programmazione Python", 27),
                        ("Russo Sofia", "Cybersecurity", 29)
                    ]
                    cursor.executemany("INSERT INTO voti (studente, materia, voto) VALUES (?, ?, ?)", voti_istituzionali)
                    
                    conn.commit()
                    print("[INFO DB] Database inizializzato con successo con Anagrafica e 5 Voti storici!")
                    
        except sqlite3.Error as e:
            print(f"[ERRORE DB] Impossibile scrivere i dati istituzionali: {e}")

if __name__ == "__main__":
    db = DatabaseManager()