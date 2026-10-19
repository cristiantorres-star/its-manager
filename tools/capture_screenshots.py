"""Cattura gli screenshot di ITS Manager usati nel README.

Lo script avvia l'applicazione e salva in PNG il contenuto della finestra, senza
ritagli manuali del desktop:

- ``login``     → schermata di autenticazione (440x420);
- ``dashboard`` → dashboard dopo il login con le credenziali indicate;
- ``both``      → entrambe, rigenerando la galleria completa.

È uno strumento di documentazione: l'applicazione continua a funzionare con la
sola standard library, mentre qui serve Pillow per catturare i pixel.

Uso:
    pip install pillow
    python tools/capture_screenshots.py                     # entrambe
    python tools/capture_screenshots.py --view dashboard
    python tools/capture_screenshots.py --user admin --password admin123
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


def _require_pillow():
    """Importa Pillow restituendo il modulo ImageGrab, con messaggio d'aiuto.

    Returns:
        Il modulo ``PIL.ImageGrab``.

    Raises:
        SystemExit: se Pillow non è installato.
    """
    try:
        from PIL import ImageGrab
    except ImportError as exc:  # pragma: no cover - dipende dall'ambiente
        raise SystemExit(
            "Manca Pillow: esegui 'pip install pillow' e rilancia lo script."
        ) from exc
    return ImageGrab


def _new_window():
    """Crea la finestra Tkinter con l'applicazione già istanziata.

    Returns:
        La tupla ``(root, app)``: finestra principale e istanza di ``AppGUI``
        ferma sulla schermata di login.
    """
    import tkinter as tk

    from database import DatabaseManager
    from gui import AppGUI

    _enable_dpi_awareness()
    root = tk.Tk()
    app = AppGUI(root, DatabaseManager())
    return root, app


def _save_window(root, output: Path, delay: float, ImageGrab) -> Path:
    """Porta la finestra in primo piano e ne salva il contenuto in PNG.

    Args:
        root: finestra Tkinter da catturare.
        output: percorso del file PNG da creare.
        delay: secondi di attesa prima della cattura, per lasciar disegnare
            tabelle e statistiche.
        ImageGrab: modulo ``PIL.ImageGrab`` già importato.

    Returns:
        Il percorso assoluto dell'immagine salvata.
    """
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


def capture_login(output: Path, delay: float) -> Path:
    """Salva la schermata di autenticazione, senza effettuare il login.

    Args:
        output: percorso del file PNG da creare.
        delay: secondi di attesa prima della cattura.

    Returns:
        Il percorso assoluto dell'immagine salvata.
    """
    ImageGrab = _require_pillow()
    root, _app = _new_window()
    return _save_window(root, output, delay, ImageGrab)


def capture_dashboard(user: str, password: str, output: Path, delay: float) -> Path:
    """Esegue il login e salva la schermata della dashboard.

    Args:
        user: username da inserire nel form di accesso.
        password: password in chiaro da inserire nel form di accesso.
        output: percorso del file PNG da creare.
        delay: secondi di attesa prima della cattura.

    Returns:
        Il percorso assoluto dell'immagine salvata.

    Raises:
        RuntimeError: se dopo il login la dashboard non risulta costruita.
    """
    ImageGrab = _require_pillow()
    root, app = _new_window()

    app.ent_username.insert(0, user)
    app.ent_password.insert(0, password)
    app.esegui_login()

    if not getattr(app, "albero", None):
        root.destroy()
        raise RuntimeError("Login non riuscito: la dashboard non è stata costruita.")

    return _save_window(root, output, delay, ImageGrab)


def main() -> None:
    """Legge gli argomenti da riga di comando e avvia le catture richieste."""
    parser = argparse.ArgumentParser(
        description="Salva gli screenshot di ITS Manager per il README."
    )
    parser.add_argument(
        "--view",
        choices=("dashboard", "login", "both"),
        default="both",
        help="schermata da catturare (default: both)",
    )
    parser.add_argument("--user", default="admin", help="username per il login")
    parser.add_argument("--password", default="admin123", help="password per il login")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "dashboard.png",
        help="file PNG della dashboard (default: docs/dashboard.png)",
    )
    parser.add_argument(
        "--login-output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "login.png",
        help="file PNG della schermata di login (default: docs/login.png)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="secondi di attesa prima della cattura (default: 1.5)",
    )
    args = parser.parse_args()

    if args.view in ("login", "both"):
        capture_login(args.login_output, args.delay)
    if args.view in ("dashboard", "both"):
        capture_dashboard(args.user, args.password, args.output, args.delay)


if __name__ == "__main__":
    main()
