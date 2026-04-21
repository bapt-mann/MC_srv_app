"""
Classe principale App (fenetre CustomTkinter).
Orchestre le polling, les boutons et les appels aux modules backend.
"""

import time
import threading
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from config import Config
from lock_manager import LockManager
from syncthing import SyncthingClient
from server import ServerProcess
from helpers import get_tailscale_ip, local_ip
from windows import SettingsWindow, MyIdWindow, JoinGroupWindow, JoinPopup

# Intervalle de polling (ms)
POLL_MS = 3_000

# Couleurs
CLR_GREEN       = "#2d7a2d"
CLR_BLUE        = "#1a4a8a"
CLR_RED         = "#8a1a1a"
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

        # Fenetre
        self.title("Serveur Volant Manager")
        self.geometry("860x640")
        self.minsize(720, 560)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._log("Serveur Volant Manager demarre.")
        self._log(f"Dossier serveur : {self.config.get('General', 'server_path')}")
        self._start_polling()

    # --------------------------------------------------------------------------
    #  Construction de l'UI
    # --------------------------------------------------------------------------

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, corner_radius=0, height=56,
                              fg_color=("#1a1a2e", "#1a1a2e"))
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="Serveur Volant Manager",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(
            side="left", padx=20)

        # Barre d'outils (row sous le header)
        toolbar = ctk.CTkFrame(self, corner_radius=0, height=40,
                               fg_color=("#12122a", "#12122a"))
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        ctk.CTkButton(toolbar, text="Mon ID Syncthing", height=28,
                      fg_color="#2a3a1a", hover_color="#3a5a2a",
                      font=ctk.CTkFont(size=12),
                      command=self._open_my_id).pack(side="left", padx=(12, 4), pady=6)

        ctk.CTkButton(toolbar, text="Rejoindre le groupe", height=28,
                      fg_color="#1a3a5a", hover_color="#2a5a8a",
                      font=ctk.CTkFont(size=12),
                      command=self._open_join_group).pack(side="left", padx=4, pady=6)

        ctk.CTkButton(toolbar, text="Parametres", height=28,
                      fg_color="gray25", hover_color="gray35",
                      font=ctk.CTkFont(size=12),
                      command=self._open_settings).pack(side="right", padx=(4, 12), pady=6)

        # Barre de statut
        status_bar = ctk.CTkFrame(self, corner_radius=12,
                                  fg_color=("#111122", "#111122"))
        status_bar.pack(fill="x", padx=14, pady=(10, 4))

        sync_col = ctk.CTkFrame(status_bar, fg_color="transparent")
        sync_col.pack(side="left", expand=True, fill="both", padx=20, pady=12)
        ctk.CTkLabel(sync_col, text="SYNCHRONISATION",
                     font=ctk.CTkFont(size=10), text_color="gray60").pack()
        self.lbl_sync = ctk.CTkLabel(sync_col, text="Verification...",
                                     font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_sync.pack()

        ctk.CTkFrame(status_bar, width=1, fg_color="gray30").pack(
            side="left", fill="y", pady=8)

        srv_col = ctk.CTkFrame(status_bar, fg_color="transparent")
        srv_col.pack(side="left", expand=True, fill="both", padx=20, pady=12)
        ctk.CTkLabel(srv_col, text="SERVEUR",
                     font=ctk.CTkFont(size=10), text_color="gray60").pack()
        self.lbl_server = ctk.CTkLabel(srv_col, text="Hors ligne",
                                       font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_server.pack()

        ctk.CTkFrame(status_bar, width=1, fg_color="gray30").pack(
            side="left", fill="y", pady=8)

        pseudo_col = ctk.CTkFrame(status_bar, fg_color="transparent")
        pseudo_col.pack(side="left", padx=20, pady=12)
        ctk.CTkLabel(pseudo_col, text="PSEUDO",
                     font=ctk.CTkFont(size=10), text_color="gray60").pack()
        self.lbl_pseudo = ctk.CTkLabel(
            pseudo_col,
            text=self.config.get("General", "pseudo") or "Joueur",
            font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_pseudo.pack()

        # Boutons principaux
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(fill="x", padx=14, pady=6)

        self._frame_normal = ctk.CTkFrame(btn_container, fg_color="transparent")
        self._frame_normal.pack(fill="x")

        self.btn_host = ctk.CTkButton(
            self._frame_normal, text="Heberger",
            font=ctk.CTkFont(size=16, weight="bold"), height=54,
            fg_color=CLR_GREEN, hover_color=CLR_HOVER_GREEN,
            command=self._on_host)
        self.btn_host.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_join = ctk.CTkButton(
            self._frame_normal, text="Rejoindre",
            font=ctk.CTkFont(size=16, weight="bold"), height=54,
            fg_color=CLR_BLUE, hover_color=CLR_HOVER_BLUE,
            command=self._on_join)
        self.btn_join.pack(side="left", expand=True, fill="x", padx=(5, 0))

        self._frame_hosting = ctk.CTkFrame(btn_container, fg_color="transparent")

        self.btn_stop = ctk.CTkButton(
            self._frame_hosting, text="Arreter le serveur",
            font=ctk.CTkFont(size=16, weight="bold"), height=54,
            fg_color=CLR_RED, hover_color=CLR_HOVER_RED,
            command=self._on_stop)
        self.btn_stop.pack(fill="x")

        # Console
        console_frame = ctk.CTkFrame(self)
        console_frame.pack(fill="both", expand=True, padx=14, pady=(4, 14))
        ctk.CTkLabel(console_frame, text="Console",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").pack(fill="x", padx=10, pady=(6, 2))
        self.console = ctk.CTkTextbox(
            console_frame,
            font=ctk.CTkFont(family="Courier New", size=12),
            fg_color="#0d0d0d", state="disabled", wrap="word")
        self.console.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # --------------------------------------------------------------------------
    #  Logging
    # --------------------------------------------------------------------------

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.configure(state="normal")
        self.console.insert("end", f"[{ts}]  {msg}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    # --------------------------------------------------------------------------
    #  Polling (toutes les POLL_MS ms)
    # --------------------------------------------------------------------------

    def _start_polling(self):
        self._poll()

    def _poll(self):
        threading.Thread(target=self._fetch_status, daemon=True).start()
        self.after(POLL_MS, self._poll)

    def _fetch_status(self):
        sync_state = self.syncthing.get_state()
        lock_data  = self.lock_mgr.read() if self.lock_mgr.exists() else None
        self.after(0, self._apply_status, sync_state, lock_data)

    def _apply_status(self, sync_state, lock_data):
        sync_map = {
            "idle":     ("A jour",             "#4caf50"),
            "syncing":  ("Synchronisation...", "#ffeb3b"),
            "scanning": ("Analyse...",         "#ffeb3b"),
            "offline":  ("Syncthing offline",  "#9e9e9e"),
            "timeout":  ("Timeout API",        "#f44336"),
            "error":    ("Erreur API",         "#f44336"),
            "no_key":   ("Cle API manquante",  "#ff9800"),
            "bad_key":  ("Cle API invalide",   "#f44336"),
        }
        txt, clr = sync_map.get(sync_state, (sync_state, "#9e9e9e"))
        self.lbl_sync.configure(text=txt, text_color=clr)

        if lock_data:
            host = lock_data.get("host", "?")
            ip   = lock_data.get("ip", "?")
            self.lbl_server.configure(
                text=f"En ligne chez {host}  ({ip})", text_color="#42a5f5")
        else:
            self.lbl_server.configure(text="Hors ligne", text_color="#ef5350")

        if self.is_hosting:
            self._frame_normal.pack_forget()
            self._frame_hosting.pack(fill="x")
        else:
            self._frame_hosting.pack_forget()
            self._frame_normal.pack(fill="x")
            self.btn_host.configure(
                state="normal" if lock_data is None else "disabled")
            self.btn_join.configure(
                state="normal" if lock_data is not None else "disabled")

    # --------------------------------------------------------------------------
    #  Heberger
    # --------------------------------------------------------------------------

    def _on_host(self):
        sync_state = self.syncthing.get_state()
        if sync_state not in ("idle", "offline", "no_key"):
            self._log(f"Syncthing occupe ({sync_state}). Attends la fin de la sync.")
            return
        if self.lock_mgr.exists():
            data = self.lock_mgr.read()
            self._log(f"Serveur deja heberge par {data.get('host', '?') if data else '?'}.")
            return

        self._log("Recuperation de l'IP Tailscale...")
        ip = get_tailscale_ip()
        if ip:
            self._log(f"IP Tailscale : {ip}")
        else:
            ip = local_ip()
            self._log(f"IP Tailscale introuvable, IP locale utilisee : {ip}")

        pseudo = self.config.get("General", "pseudo") or "Joueur"

        try:
            self.lock_mgr.create(pseudo, ip)
            self._log(f"Verrou cree : {pseudo} @ {ip}:25565")
        except Exception as e:
            self._log(f"Erreur verrou : {e}")
            return

        server_path = self.config.get("General", "server_path")
        java_args   = self.config.get("Server", "java_args")
        jar_name    = self.config.get("Server", "jar_name")

        if not Path(server_path).exists():
            self._log(f"Dossier serveur introuvable : {server_path}")
            self.lock_mgr.delete()
            return

        self._log(f"Lancement de PaperMC ({jar_name})...")
        ok = self.server.start(
            server_path, java_args, jar_name,
            output_cb=lambda line: self.after(0, self._log, f"Java > {line}"),
        )
        if ok:
            self.is_hosting = True
            self._log("Serveur lance ! Connecte-toi sur localhost:25565")
        else:
            self.lock_mgr.delete()
            self._log("Echec du lancement Java. Verifie le chemin et le JAR.")

    # --------------------------------------------------------------------------
    #  Rejoindre
    # --------------------------------------------------------------------------

    def _on_join(self):
        if not self.lock_mgr.exists():
            self._log("Aucun serveur en ligne (lock.json absent).")
            return
        data = self.lock_mgr.read()
        if not data:
            self._log("lock.json illisible.")
            return
        JoinPopup(self, data.get("host", "?"), data.get("ip", "?"))

    # --------------------------------------------------------------------------
    #  Arreter
    # --------------------------------------------------------------------------

    def _on_stop(self):
        self.btn_stop.configure(state="disabled", text="Arret en cours...")
        self._log("Arret du serveur en cours...")
        threading.Thread(target=self._stop_sequence, daemon=True).start()

    def _stop_sequence(self):
        self.server.stop()
        self.server.wait(timeout=90)
        self.lock_mgr.delete()
        self.is_hosting = False
        self.after(0, self._log, "Serveur arrete. Verrou supprime.")
        self.after(0, self._log, "Syncthing envoie la sauvegarde...")
        self.after(0, self.btn_stop.configure,
                   {"state": "normal", "text": "Arreter le serveur"})
        self._wait_for_sync()

    def _wait_for_sync(self, max_checks=30):
        for _ in range(max_checks):
            time.sleep(3)
            state = self.syncthing.get_state()
            if state in ("idle", "offline", "no_key"):
                self.after(0, self._log,
                           "Sauvegarde synchronisee. Les amis ont les dernieres donnees.")
                return
            self.after(0, self._log, f"Syncthing : {state}...")
        self.after(0, self._log,
                   "Syncthing toujours occupe. Verifie l'interface Syncthing.")

    # --------------------------------------------------------------------------
    #  Fenetres secondaires
    # --------------------------------------------------------------------------

    def _open_my_id(self):
        MyIdWindow(self, self.syncthing)

    def _open_join_group(self):
        JoinGroupWindow(self, self.syncthing, self._log)

    def _open_settings(self):
        SettingsWindow(self, self.config, on_save=self._reload_config)

    def _reload_config(self):
        self.lock_mgr.update_path(self.config.get("General", "server_path"))
        self.syncthing.api_url   = self.config.get("Syncthing", "api_url")
        self.syncthing.api_key   = self.config.get("Syncthing", "api_key")
        self.syncthing.folder_id = self.config.get("Syncthing", "folder_id")
        self.lbl_pseudo.configure(
            text=self.config.get("General", "pseudo") or "Joueur")
        self._log("Parametres recharges.")

    # --------------------------------------------------------------------------
    #  Fermeture
    # --------------------------------------------------------------------------

    def _on_close(self):
        if self.is_hosting and self.server.is_running():
            from tkinter import messagebox
            if not messagebox.askyesno(
                "Serveur actif",
                "Le serveur tourne encore.\nL'arreter proprement avant de quitter ?",
                parent=self,
            ):
                self.destroy()
                return
            self._log("Arret avant fermeture...")
            self.server.stop()
            self.server.wait(timeout=30)
            self.lock_mgr.delete()
        self.destroy()
