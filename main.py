"""
Serveur Volant Manager
======================
Launcher Python/CustomTkinter pour un serveur Minecraft PaperMC décentralisé (P2P).
Gère le verrou de session (lock.json), l'API Syncthing et le processus Java.
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import configparser
from pathlib import Path
from datetime import datetime

import requests
import customtkinter as ctk


# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION MANAGER
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    "General": {
        "pseudo": "Joueur",
        "server_path": "C:/MC_PROJET_SERVEUR",
    },
    "Syncthing": {
        "api_url": "http://localhost:8384",
        "api_key": "",
        "folder_id": "MC_PROJET_SERVEUR",
    },
    "Server": {
        "java_args": "-Xmx2G -Xms2G",
        "jar_name": "paper.jar",
    },
}


class Config:
    def __init__(self, path: str = "config.ini"):
        self.path = path
        self.cfg = configparser.ConfigParser()
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            self.cfg.read_dict(DEFAULT_CONFIG)
            self._save()
        else:
            self.cfg.read(self.path, encoding="utf-8")
            # Ensure all default sections/keys exist
            for section, values in DEFAULT_CONFIG.items():
                if not self.cfg.has_section(section):
                    self.cfg.add_section(section)
                for key, val in values.items():
                    if not self.cfg.has_option(section, key):
                        self.cfg.set(section, key, val)
            self._save()

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            self.cfg.write(f)

    def get(self, section: str, key: str, fallback: str = "") -> str:
        return self.cfg.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str):
        if not self.cfg.has_section(section):
            self.cfg.add_section(section)
        self.cfg.set(section, key, value)
        self._save()


# ══════════════════════════════════════════════════════════════════════════════
#  LOCK MANAGER  (lock.json)
# ══════════════════════════════════════════════════════════════════════════════

class LockManager:
    def __init__(self, server_path: str):
        self._update(server_path)

    def _update(self, server_path: str):
        self.lock_path = Path(server_path) / "lock.json"

    def update_path(self, server_path: str):
        self._update(server_path)

    def exists(self) -> bool:
        return self.lock_path.exists()

    def read(self) -> dict | None:
        try:
            with open(self.lock_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def create(self, pseudo: str, ip: str):
        data = {"status": "online", "host": pseudo, "ip": f"{ip}:25565"}
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lock_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def delete(self):
        try:
            self.lock_path.unlink(missing_ok=True)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  SYNCTHING CLIENT
# ══════════════════════════════════════════════════════════════════════════════

class SyncthingClient:
    def __init__(self, api_url: str, api_key: str, folder_id: str):
        self.api_url = api_url
        self.api_key = api_key
        self.folder_id = folder_id

    def get_state(self) -> str:
        """Retourne: 'idle' | 'syncing' | 'scanning' | 'offline' | 'no_key' | 'error'"""
        if not self.api_key.strip():
            return "no_key"
        try:
            headers = {"X-API-Key": self.api_key}
            url = f"{self.api_url}/rest/db/status"
            params = {"folder": self.folder_id}
            r = requests.get(url, headers=headers, params=params, timeout=4)
            if r.status_code == 403:
                return "bad_key"
            if r.status_code == 200:
                return r.json().get("state", "unknown")
            return "error"
        except requests.exceptions.ConnectionError:
            return "offline"
        except requests.exceptions.Timeout:
            return "timeout"
        except Exception:
            return "error"


# ══════════════════════════════════════════════════════════════════════════════
#  SERVER PROCESS MANAGER  (Java / PaperMC)
# ══════════════════════════════════════════════════════════════════════════════

_WIN = os.name == "nt"
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if _WIN else 0


class ServerProcess:
    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._running = False
        self._output_cb = None

    # ── Public API ──────────────────────────────────────────────────────────

    def start(self, server_path: str, java_args: str, jar_name: str, output_cb) -> bool:
        """Lance le serveur Java. Retourne True si OK."""
        self._output_cb = output_cb
        cmd = f'java {java_args} -jar "{jar_name}" nogui'
        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=server_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                shell=True,
                creationflags=_NO_WINDOW,
            )
            self._running = True
            threading.Thread(target=self._reader, daemon=True).start()
            return True
        except FileNotFoundError:
            self._emit("[ERREUR] Java introuvable. Assure-toi que Java est installé et dans le PATH.")
            return False
        except PermissionError:
            self._emit("[ERREUR] Permission refusée. Lance l'app en administrateur.")
            return False
        except Exception as exc:
            self._emit(f"[ERREUR] Impossible de lancer Java : {exc}")
            return False

    def send_command(self, cmd: str):
        """Envoie une commande à la console Java (ex: 'stop')."""
        if self._process and self._running:
            try:
                self._process.stdin.write(cmd + "\n")
                self._process.stdin.flush()
            except Exception:
                pass

    def stop(self):
        self.send_command("stop")

    def wait(self, timeout: int = 60):
        if self._process:
            try:
                self._process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._process.kill()
            finally:
                self._running = False

    def is_running(self) -> bool:
        if self._process is None:
            return False
        return self._process.poll() is None

    # ── Internals ───────────────────────────────────────────────────────────

    def _reader(self):
        """Lit stdout du processus Java en arrière-plan."""
        for line in self._process.stdout:
            self._emit(line.rstrip())
        self._running = False

    def _emit(self, line: str):
        if self._output_cb:
            self._output_cb(line)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_tailscale_ip() -> str | None:
    """Tente de récupérer l'IP Tailscale (plage 100.x.x.x)."""
    # Méthode 1 : CLI tailscale
    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True, text=True, timeout=5,
            creationflags=_NO_WINDOW,
        )
        ip = result.stdout.strip()
        if result.returncode == 0 and ip.startswith("100."):
            return ip
    except Exception:
        pass

    # Méthode 2 : scan des interfaces réseau
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ip.startswith("100."):
                return ip
    except Exception:
        pass

    return None


def local_ip() -> str:
    """IP locale de repli."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS WINDOW
# ══════════════════════════════════════════════════════════════════════════════

SETTINGS_FIELDS = [
    ("Pseudo",                  "General",   "pseudo"),
    ("Chemin du dossier serveur","General",   "server_path"),
    ("URL Syncthing",           "Syncthing", "api_url"),
    ("Clé API Syncthing",       "Syncthing", "api_key"),
    ("ID dossier Syncthing",    "Syncthing", "folder_id"),
    ("Arguments Java",          "Server",    "java_args"),
    ("Nom du JAR",              "Server",    "jar_name"),
]


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, config: Config, on_save=None):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        self.title("⚙️ Paramètres")
        self.geometry("540x380")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self, text="⚙️  Paramètres",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(15, 8))

        frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20)

        self._entries: dict[tuple, ctk.CTkEntry] = {}
        for label, section, key in SETTINGS_FIELDS:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, width=200, anchor="w",
                         font=ctk.CTkFont(size=13)).pack(side="left")
            entry = ctk.CTkEntry(row, width=280)
            entry.insert(0, self.config.get(section, key))
            entry.pack(side="left")
            self._entries[(section, key)] = entry

        ctk.CTkButton(
            self, text="💾  Sauvegarder", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save,
        ).pack(pady=15)

    def _save(self):
        for (section, key), entry in self._entries.items():
            self.config.set(section, key, entry.get().strip())
        if self.on_save:
            self.on_save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  JOIN POPUP
# ══════════════════════════════════════════════════════════════════════════════

class JoinPopup(ctk.CTkToplevel):
    def __init__(self, parent, host: str, ip: str):
        super().__init__(parent)
        self.title("Rejoindre le serveur")
        self.geometry("380x220")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(
            self, text=f"🔵  Serveur de {host}",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).pack(pady=(20, 5))

        ctk.CTkLabel(self, text="Copie cette IP dans Minecraft :",
                     text_color="gray").pack()

        ip_var = ctk.StringVar(value=ip)
        entry = ctk.CTkEntry(self, textvariable=ip_var, width=240,
                             font=ctk.CTkFont(size=15), state="readonly",
                             justify="center")
        entry.pack(pady=8)

        self._copied_label = ctk.CTkLabel(self, text="", text_color="#4caf50")
        self._copied_label.pack()

        ctk.CTkButton(
            self, text="📋  Copier l'IP", height=36,
            command=lambda: self._copy(ip),
        ).pack(pady=4)
        ctk.CTkButton(
            self, text="Fermer", height=36, fg_color="gray40",
            hover_color="gray30", command=self.destroy,
        ).pack(pady=2)

    def _copy(self, ip: str):
        self.clipboard_clear()
        self.clipboard_append(ip)
        self._copied_label.configure(text="✅  Copié dans le presse-papiers !")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

POLL_MS = 3_000  # Intervalle de polling (ms)

# Couleurs thème sombre
CLR_GREEN  = "#2d7a2d"
CLR_BLUE   = "#1a4a8a"
CLR_RED    = "#8a1a1a"
CLR_HOVER_GREEN = "#3d9a3d"
CLR_HOVER_BLUE  = "#2a6aaa"
CLR_HOVER_RED   = "#aa2a2a"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Backend
        self.config    = Config()
        self.lock_mgr  = LockManager(self.config.get("General", "server_path"))
        self.syncthing = SyncthingClient(
            self.config.get("Syncthing", "api_url"),
            self.config.get("Syncthing", "api_key"),
            self.config.get("Syncthing", "folder_id"),
        )
        self.server     = ServerProcess()
        self.is_hosting = False

        # Fenêtre
        self.title("⛏  Serveur Volant Manager")
        self.geometry("820x620")
        self.minsize(700, 540)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._log("✅  Serveur Volant Manager démarré.")
        self._log(f"📁  Dossier serveur : {self.config.get('General', 'server_path')}")
        self._start_polling()

    # ── Construction UI ────────────────────────────────────────────────────

    def _build_ui(self):
        # ---- Header --------------------------------------------------------
        header = ctk.CTkFrame(self, corner_radius=0, height=56,
                              fg_color=("#1a1a2e", "#1a1a2e"))
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="⛏  Serveur Volant Manager",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=20)

        ctk.CTkButton(
            header, text="⚙️", width=42, height=36,
            fg_color="gray25", hover_color="gray35",
            command=self._open_settings,
        ).pack(side="right", padx=14)

        # ---- Status bar ----------------------------------------------------
        status_bar = ctk.CTkFrame(self, corner_radius=12,
                                  fg_color=("#111122", "#111122"))
        status_bar.pack(fill="x", padx=14, pady=(10, 4))

        # Syncthing status
        sync_col = ctk.CTkFrame(status_bar, fg_color="transparent")
        sync_col.pack(side="left", expand=True, fill="both", padx=20, pady=12)
        ctk.CTkLabel(sync_col, text="SYNCHRONISATION",
                     font=ctk.CTkFont(size=10), text_color="gray60").pack()
        self.lbl_sync = ctk.CTkLabel(
            sync_col, text="⏳  Vérification...",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.lbl_sync.pack()

        ctk.CTkFrame(status_bar, width=1, fg_color="gray30").pack(
            side="left", fill="y", pady=8)

        # Server status
        srv_col = ctk.CTkFrame(status_bar, fg_color="transparent")
        srv_col.pack(side="left", expand=True, fill="both", padx=20, pady=12)
        ctk.CTkLabel(srv_col, text="SERVEUR",
                     font=ctk.CTkFont(size=10), text_color="gray60").pack()
        self.lbl_server = ctk.CTkLabel(
            srv_col, text="🔴  Hors ligne",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.lbl_server.pack()

        ctk.CTkFrame(status_bar, width=1, fg_color="gray30").pack(
            side="left", fill="y", pady=8)

        # Pseudo
        pseudo_col = ctk.CTkFrame(status_bar, fg_color="transparent")
        pseudo_col.pack(side="left", padx=20, pady=12)
        ctk.CTkLabel(pseudo_col, text="PSEUDO",
                     font=ctk.CTkFont(size=10), text_color="gray60").pack()
        self.lbl_pseudo = ctk.CTkLabel(
            pseudo_col,
            text=self.config.get("General", "pseudo") or "Joueur",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.lbl_pseudo.pack()

        # ---- Button container ----------------------------------------------
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(fill="x", padx=14, pady=6)

        # Frame normale (Héberger + Rejoindre)
        self._frame_normal = ctk.CTkFrame(btn_container, fg_color="transparent")
        self._frame_normal.pack(fill="x")

        self.btn_host = ctk.CTkButton(
            self._frame_normal,
            text="🟢  Héberger",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=54, fg_color=CLR_GREEN, hover_color=CLR_HOVER_GREEN,
            command=self._on_host,
        )
        self.btn_host.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_join = ctk.CTkButton(
            self._frame_normal,
            text="🔵  Rejoindre",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=54, fg_color=CLR_BLUE, hover_color=CLR_HOVER_BLUE,
            command=self._on_join,
        )
        self.btn_join.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # Frame hébergeur (Arrêter)
        self._frame_hosting = ctk.CTkFrame(btn_container, fg_color="transparent")
        # Non packed par défaut

        self.btn_stop = ctk.CTkButton(
            self._frame_hosting,
            text="🔴  Arrêter le serveur",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=54, fg_color=CLR_RED, hover_color=CLR_HOVER_RED,
            command=self._on_stop,
        )
        self.btn_stop.pack(fill="x")

        # ---- Console -------------------------------------------------------
        console_frame = ctk.CTkFrame(self)
        console_frame.pack(fill="both", expand=True, padx=14, pady=(4, 14))

        ctk.CTkLabel(
            console_frame, text="📋  Console",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).pack(fill="x", padx=10, pady=(6, 2))

        self.console = ctk.CTkTextbox(
            console_frame,
            font=ctk.CTkFont(family="Courier New", size=12),
            fg_color="#0d0d0d",
            state="disabled",
            wrap="word",
        )
        self.console.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ── Logging ───────────────────────────────────────────────────────────

    def _log(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.configure(state="normal")
        self.console.insert("end", f"[{ts}]  {message}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    # ── Polling ───────────────────────────────────────────────────────────

    def _start_polling(self):
        self._poll()

    def _poll(self):
        threading.Thread(target=self._fetch_status, daemon=True).start()
        self.after(POLL_MS, self._poll)

    def _fetch_status(self):
        sync_state = self.syncthing.get_state()
        lock_data  = self.lock_mgr.read() if self.lock_mgr.exists() else None
        self.after(0, self._apply_status, sync_state, lock_data)

    def _apply_status(self, sync_state: str, lock_data: dict | None):
        # --- Syncthing label ---
        sync_map = {
            "idle":    ("🟢  À jour",                  "#4caf50"),
            "syncing": ("🟡  Synchronisation...",       "#ffeb3b"),
            "scanning":("🟡  Analyse en cours...",      "#ffeb3b"),
            "offline": ("⚫  Syncthing hors ligne",     "#9e9e9e"),
            "timeout": ("🔴  Timeout API",              "#f44336"),
            "error":   ("🔴  Erreur API",               "#f44336"),
            "no_key":  ("⚠️  Clé API manquante",        "#ff9800"),
            "bad_key": ("🔴  Clé API invalide",         "#f44336"),
        }
        sync_txt, sync_clr = sync_map.get(sync_state, (f"❓  {sync_state}", "#9e9e9e"))
        self.lbl_sync.configure(text=sync_txt, text_color=sync_clr)

        # --- Server label ---
        if lock_data:
            host = lock_data.get("host", "?")
            ip   = lock_data.get("ip",   "?")
            self.lbl_server.configure(
                text=f"🔵  En ligne chez {host}  ({ip})",
                text_color="#42a5f5",
            )
        else:
            self.lbl_server.configure(text="🔴  Hors ligne", text_color="#ef5350")

        # --- Buttons ---
        if self.is_hosting:
            self._frame_normal.pack_forget()
            self._frame_hosting.pack(fill="x")
        else:
            self._frame_hosting.pack_forget()
            self._frame_normal.pack(fill="x")
            can_host = (lock_data is None)
            can_join = (lock_data is not None)
            self.btn_host.configure(state="normal" if can_host else "disabled")
            self.btn_join.configure(state="normal" if can_join else "disabled")

    # ── Bouton Héberger ───────────────────────────────────────────────────

    def _on_host(self):
        # 1. Vérification Syncthing
        sync_state = self.syncthing.get_state()
        if sync_state not in ("idle", "offline", "no_key"):
            self._log(f"⚠️  Syncthing est occupé ({sync_state}). Attends la fin de la sync avant d'héberger.")
            return
        if sync_state == "offline":
            self._log("⚠️  Syncthing hors ligne — impossible de vérifier la sync. Continue avec précaution.")
        if sync_state == "no_key":
            self._log("⚠️  Clé API Syncthing non configurée (Paramètres). Vérification ignorée.")

        # 2. Vérification verrou
        if self.lock_mgr.exists():
            data = self.lock_mgr.read()
            host = data.get("host", "?") if data else "?"
            self._log(f"🔒  Serveur déjà hébergé par {host}. Impossible d'héberger.")
            return

        # 3. IP Tailscale
        self._log("🔍  Récupération de l'IP Tailscale...")
        ip = get_tailscale_ip()
        if ip:
            self._log(f"✅  IP Tailscale : {ip}")
        else:
            ip = local_ip()
            self._log(f"⚠️  IP Tailscale introuvable, utilisation de l'IP locale : {ip}")

        pseudo = self.config.get("General", "pseudo") or "Joueur"

        # 4. Création du verrou
        try:
            self.lock_mgr.create(pseudo, ip)
            self._log(f"🔒  Verrou créé — {pseudo} @ {ip}:25565")
        except PermissionError:
            self._log("❌  Impossible d'écrire lock.json. Vérifie les permissions du dossier serveur.")
            return
        except Exception as e:
            self._log(f"❌  Erreur lors de la création du verrou : {e}")
            return

        # 5. Lancement du serveur Java
        server_path = self.config.get("General", "server_path")
        java_args   = self.config.get("Server",  "java_args")
        jar_name    = self.config.get("Server",  "jar_name")

        if not Path(server_path).exists():
            self._log(f"❌  Dossier serveur introuvable : {server_path}")
            self.lock_mgr.delete()
            return

        self._log(f"🚀  Lancement de PaperMC ({jar_name}) …")
        ok = self.server.start(server_path, java_args, jar_name,
                               output_cb=lambda line: self.after(0, self._log, f"☕  {line}"))
        if ok:
            self.is_hosting = True
            self._log("✅  Serveur lancé ! Connecte-toi sur localhost:25565")
        else:
            self.lock_mgr.delete()
            self._log("❌  Échec du lancement Java. Vérifie le chemin et le JAR.")

    # ── Bouton Rejoindre ──────────────────────────────────────────────────

    def _on_join(self):
        if not self.lock_mgr.exists():
            self._log("❌  Aucun serveur en ligne (lock.json absent).")
            return
        data = self.lock_mgr.read()
        if not data:
            self._log("❌  lock.json illisible ou corrompu.")
            return
        host = data.get("host", "?")
        ip   = data.get("ip",   "?")
        self._log(f"🔵  Serveur de {host} — IP : {ip}")
        JoinPopup(self, host, ip)

    # ── Bouton Arrêter ────────────────────────────────────────────────────

    def _on_stop(self):
        self.btn_stop.configure(state="disabled", text="⏳  Arrêt en cours…")
        self._log("⏹  Arrêt du serveur en cours…")
        threading.Thread(target=self._stop_sequence, daemon=True).start()

    def _stop_sequence(self):
        self.server.stop()
        self.server.wait(timeout=90)
        self.lock_mgr.delete()
        self.is_hosting = False
        self.after(0, self._log, "✅  Serveur arrêté. Verrou supprimé.")
        self.after(0, self._log, "📤  Syncthing envoie la sauvegarde aux autres joueurs…")
        self.after(0, self.btn_stop.configure, {"state": "normal",
                                                 "text": "🔴  Arrêter le serveur"})
        self._wait_for_sync()

    def _wait_for_sync(self, max_checks: int = 30):
        """Attend que Syncthing repasse en 'idle' après l'arrêt du serveur."""
        for _ in range(max_checks):
            time.sleep(3)
            state = self.syncthing.get_state()
            if state in ("idle", "offline", "no_key"):
                self.after(0, self._log, "✅  Sauvegarde synchronisée. Les amis ont les dernières données.")
                return
            self.after(0, self._log, f"🔄  Syncthing : {state}…")
        self.after(0, self._log,
                   "⚠️  Syncthing toujours occupé. Vérifie l'interface Syncthing manuellement.")

    # ── Paramètres ────────────────────────────────────────────────────────

    def _open_settings(self):
        SettingsWindow(self, self.config, on_save=self._reload_config)

    def _reload_config(self):
        self.lock_mgr.update_path(self.config.get("General", "server_path"))
        self.syncthing.api_url   = self.config.get("Syncthing", "api_url")
        self.syncthing.api_key   = self.config.get("Syncthing", "api_key")
        self.syncthing.folder_id = self.config.get("Syncthing", "folder_id")
        self.lbl_pseudo.configure(text=self.config.get("General", "pseudo") or "Joueur")
        self._log("⚙️  Paramètres rechargés.")

    # ── Fermeture ─────────────────────────────────────────────────────────

    def _on_close(self):
        if self.is_hosting and self.server.is_running():
            from tkinter import messagebox
            if not messagebox.askyesno(
                "Serveur actif",
                "Le serveur est en cours d'exécution.\n"
                "Veux-tu l'arrêter proprement avant de quitter ?",
                parent=self,
            ):
                self.destroy()
                return
            self._log("🛑  Arrêt du serveur avant fermeture…")
            self.server.stop()
            self.server.wait(timeout=30)
            self.lock_mgr.delete()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.mainloop()
