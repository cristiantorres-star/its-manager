class Persona:
    """Classe base che rappresenta una persona generale dell'istituto.

    Implementa gli attributi comuni (nome, età, indirizzo) come proprietà
    private con relativi getter/setter, secondo il paradigma OOP.
    """

    def __init__(self, nome: str, eta: int, indirizzo: str) -> None:
        """Inizializza una persona con i suoi dati anagrafici di base.

        Args:
            nome: nome (o cognome e nome) della persona.
            eta: età in anni della persona.
            indirizzo: indirizzo di residenza o domicilio.
        """
        self._nome = nome
        self._eta = eta
        self._indirizzo = indirizzo

    @property
    def nome(self) -> str:
        """Restituisce il nome della persona."""
        return self._nome

    @nome.setter
    def nome(self, valore: str) -> None:
        """Imposta un nuovo nome per la persona.

        Args:
            valore: nuovo nome da assegnare.
        """
        self._nome = valore

    @property
    def eta(self) -> int:
        """Restituisce l'età della persona, in anni."""
        return self._eta

    @eta.setter
    def eta(self, valore: int) -> None:
        """Imposta una nuova età per la persona, con validazione del dato.

        Args:
            valore: nuova età in anni, deve essere un valore non negativo.

        Raises:
            ValueError: se il valore fornito è negativo.
        """
        if valore < 0:
            raise ValueError("L'età non può essere negativa.")
        self._eta = valore

    @property
    def indirizzo(self) -> str:
        """Restituisce l'indirizzo di residenza/domicilio della persona."""
        return self._indirizzo

    @indirizzo.setter
    def indirizzo(self, valore: str) -> None:
        """Imposta un nuovo indirizzo per la persona.

        Args:
            valore: nuovo indirizzo da assegnare.
        """
        self._indirizzo = valore

    def __str__(self) -> str:
        """Restituisce una rappresentazione testuale sintetica della persona.

        Returns:
            Una stringa nel formato "Nome (età anni)".
        """
        return f"{self._nome} ({self._eta} anni)"


class Studente(Persona):
    """Rappresenta uno studente iscritto ai corsi dell'istituto.

    Eredita da Persona tramite super() e aggiunge la gestione dei voti
    tramite un dizionario {materia: voto}, con calcolo automatico della media.
    """

    def __init__(self, nome: str, eta: int, indirizzo: str) -> None:
        """Inizializza uno studente riutilizzando il costruttore di Persona.

        Args:
            nome: nome (o cognome e nome) dello studente.
            eta: età in anni dello studente.
            indirizzo: indirizzo di residenza o domicilio.
        """
        super().__init__(nome, eta, indirizzo)
        self.voti: dict[str, int] = {}

    def aggiungi_voto(self, materia: str, voto: int) -> None:
        """Registra o aggiorna il voto di una materia nel dizionario dello studente.

        Args:
            materia: nome della materia/corso a cui si riferisce il voto.
            voto: valutazione numerica ottenuta nella materia.
        """
        self.voti[materia] = voto

    def calcola_media(self) -> float:
        """Calcola la media aritmetica dei voti registrati.

        Returns:
            La media dei voti, oppure 0.0 se non è presente alcun voto.
        """
        if not self.voti:
            return 0.0
        return sum(self.voti.values()) / len(self.voti)

    def __str__(self) -> str:
        """Restituisce una rappresentazione testuale dello studente con la media voti.

        Returns:
            Una stringa nel formato "Studente: Nome (età anni) - Media: X.XX".
        """
        return f"Studente: {self._nome} ({self._eta} anni) - Media: {self.calcola_media():.2f}"


class Docente(Persona):
    """Rappresenta un docente dell'istituto.

    Eredita da Persona e aggiunge la materia insegnata e l'elenco dei corsi
    assegnati (lista di tuple (nome_corso, anno_accademico)).
    """

    def __init__(self, nome: str, eta: int, indirizzo: str, materia: str) -> None:
        """Inizializza un docente riutilizzando il costruttore di Persona.

        Args:
            nome: nome (o cognome e nome) del docente.
            eta: età in anni del docente.
            indirizzo: indirizzo di residenza o domicilio.
            materia: materia principale insegnata dal docente.
        """
        super().__init__(nome, eta, indirizzo)
        self._materia = materia
        self.corsi_assegnati: list[tuple[str, str]] = []

    @property
    def materia(self) -> str:
        """Restituisce la materia principale insegnata dal docente."""
        return self._materia

    @materia.setter
    def materia(self, valore: str) -> None:
        """Imposta una nuova materia principale per il docente.

        Args:
            valore: nuova materia da assegnare.
        """
        self._materia = valore

    def assegna_corso(self, nome_corso: str, anno_accademico: str) -> None:
        """Aggiunge un corso (tupla immutabile) all'elenco dei corsi del docente.

        Args:
            nome_corso: nome del corso da assegnare al docente.
            anno_accademico: anno accademico di riferimento (es. "2025/2026").
        """
        self.corsi_assegnati.append((nome_corso, anno_accademico))

    def __str__(self) -> str:
        """Restituisce una rappresentazione testuale del docente e della sua materia.

        Returns:
            Una stringa nel formato "Docente: Nome - Materia: X".
        """
        return f"Docente: {self._nome} - Materia: {self._materia}"


class Amministratore(Persona):
    """Rappresenta un utente con privilegi di amministrazione completa.

    Eredita da Persona; rappresenta il ruolo con permessi di gestione totale
    su utenti, anagrafica e voti all'interno dell'applicazione.
    """

    def __init__(self, nome: str, eta: int, indirizzo: str) -> None:
        """Inizializza un amministratore riutilizzando il costruttore di Persona.

        Args:
            nome: nome (o cognome e nome) dell'amministratore.
            eta: età in anni dell'amministratore.
            indirizzo: indirizzo di residenza o domicilio.
        """
        super().__init__(nome, eta, indirizzo)

    def __str__(self) -> str:
        """Restituisce una rappresentazione testuale sintetica dell'amministratore.

        Returns:
            Una stringa nel formato "Amministratore: Nome".
        """
        return f"Amministratore: {self._nome}"
