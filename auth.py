"""Modulo di autenticazione e tracciamento accessi per ITS Manager.

Centralizza in un'unica classe (AuthManager) la logica di hashing della
password, la verifica delle credenziali sul database e la registrazione
di ogni tentativo di login (riuscito o fallito) tramite il modulo logging,
così come richiesto dalle specifiche del progetto.
"""

import sqlite3
import hashlib
import logging


class AuthManager:
    """Gestisce l'autenticazione degli utenti e il log dei tentativi di accesso."""

    def __init__(self, db_name: str) -> None:
        """Inizializza l'AuthManager collegandolo al database dell'applicazione.

        Args:
            db_name: percorso/nome del file del database SQLite.
        """
        self.db_name = db_name

    @staticmethod
    def _hash_password(password: str) -> str:
        """Calcola l'hash SHA-256 di una password in chiaro.

        Args:
            password: password inserita dall'utente.

        Returns:
            La rappresentazione esadecimale dell'hash SHA-256.
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Verifica le credenziali fornite e registra l'esito nel file di log.

        Args:
            username: username o email inserito dall'utente.
            password: password in chiaro inserita dall'utente.

        Returns:
            Una tupla (successo, ruolo): se il login fallisce, ruolo è "".
        """
        if not username or not password:
            logging.warning("LOGIN FALLITO - campi vuoti")
            return False, ""

        password_hash = self._hash_password(password)

        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ruolo FROM utenti WHERE username = ? AND password_hash = ?",
                    (username, password_hash),
                )
                risultato = cursor.fetchone()

            if risultato:
                ruolo = risultato[0]
                logging.info(f"LOGIN OK - utente: '{username}' - ruolo: {ruolo}")
                return True, ruolo

            logging.warning(f"LOGIN FALLITO - credenziali non valide per utente: '{username}'")
            return False, ""

        except sqlite3.Error as e:
            logging.error(f"ERRORE DB durante il login di '{username}': {e}")
            return False, ""
