"""Cattura uno screenshot della dashboard di ITS Manager.

Lo script avvia l'applicazione, compila il form di login con le credenziali
indicate, attende il rendering della dashboard e salva in PNG il contenuto
della finestra. Serve a rigenerare l'immagine usata nel README senza dover
ritagliare a mano una schermata del desktop.

È uno strumento di documentazione: l'applicazione continua a funzionare con la
sola standard library, mentre qui serve Pillow per catturare i pixel.

Uso:
    pip install pillow
    python tools/capture_dashboard.py                        # docs/dashboard.png
    python tools/capture_dashboard.py --user admin --password admin123
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _enable_dpi_awareness() -> None:
    """Allinea le coordinate Tkinter ai pixel reali dello schermo su Windows.

    Senza questa chiamata, su display con scaling superiore al 100% la finestra
    viene disegnata in pixel logici e il ritaglio risulta sfocato o spostato.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass  # Su ambienti senza API Win32 la cattura funziona comunque.


def _pump(root, seconds: float) -> None:
    """Mantiene vivo il loop degli eventi per ``seconds`` secondi.

    Tkinter disegna solo mentre elabora eventi: senza questo ciclo la finestra
    resterebbe bianca al momento della cattura.

    Args:
        root: finestra Tkinter principale.
        seconds: durata dell'attesa, in secondi.
    """
    scadenza = time.monotonic() + seconds
    while time.monotonic() < scadenza:
        root.update()
        time.sleep(0.05)


def capture(user: str, password: str, output: Path, delay: float) -> Path:
    """Esegue il login e salva la schermata della dashboard.

    Args:
        user: username da inserire nel form di accesso.
        password: password in chiaro da inserire nel form di accesso.
        output: percorso del file PNG da creare.
        delay: secondi di attesa prima della cattura, per lasciar disegnare
            tabelle e statistiche.

    Returns:
        Il percorso assoluto dell'immagine salvata.

    Raises:
        RuntimeError: se dopo il login la dashboard non risulta costruita.
    """
    try:
        import tkinter as tk

        from PIL import ImageGrab
    except ImportError as exc:  # pragma: no cover - dipende dall'ambiente
        raise SystemExit(
            "Manca Pillow: esegui 'pip install pillow' e rilancia lo script."
        ) from exc

    from database import DatabaseManager
    from gui import AppGUI

    _enable_dpi_awareness()

    db = DatabaseManager()
    root = tk.Tk()
    app = AppGUI(root, db)

    app.ent_username.insert(0, user)
    app.ent_password.insert(0, password)
    app.esegui_login()

    if not getattr(app, "albero", None):
        root.destroy()
        raise RuntimeError("Login non riuscito: la dashboard non è stata costruita.")

    root.lift()
    root.attributes("-topmost", True)
    _pump(root, delay)

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    larghezza = root.winfo_width()
    altezza = root.winfo_height()

    output.parent.mkdir(parents=True, exist_ok=True)
    immagine = ImageGrab.grab(bbox=(x, y, x + larghezza, y + altezza), all_screens=True)
    immagine.save(output)
    root.destroy()

    print(f"Screenshot salvato in {output} ({immagine.width}x{immagine.height})")
    return output


def main() -> None:
    """Legge gli argomenti da riga di comando e avvia la cattura."""
    parser = argparse.ArgumentParser(
        description="Salva uno screenshot della dashboard di ITS Manager."
    )
    parser.add_argument("--user", default="admin", help="username per il login")
    parser.add_argument("--password", default="admin123", help="password per il login")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "dashboard.png",
        help="file PNG da creare (default: docs/dashboard.png)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="secondi di attesa prima della cattura (default: 1.5)",
    )
    args = parser.parse_args()

    capture(args.user, args.password, args.output, args.delay)


if __name__ == "__main__":
    main()
