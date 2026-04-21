import os
import socket
import subprocess

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def get_tailscale_ip():
    """Tente de recuperer l'IP Tailscale (plage 100.x.x.x)."""
    # Methode 1 : CLI tailscale
    try:
        r = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True, text=True, timeout=5,
            creationflags=_NO_WINDOW,
        )
        ip = r.stdout.strip()
        if r.returncode == 0 and ip.startswith("100."):
            return ip
    except Exception:
        pass

    # Methode 2 : scan des interfaces reseau
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ip.startswith("100."):
                return ip
    except Exception:
        pass

    return None


def local_ip():
    """IP locale de repli."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
