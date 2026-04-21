"""
Fenetres secondaires de l'application :
  - SettingsWindow   : parametres de configuration
  - MyIdWindow       : affiche l'ID Syncthing local (pour l'hote)
  - JoinGroupWindow  : l'ami colle l'ID de l'hote pour rejoindre
  - JoinPopup        : affiche l'IP du serveur actif pour se connecter
"""

import threading
import customtkinter as ctk

from config import Config
from syncthing import SyncthingClient

SETTINGS_FIELDS = [
    ("Pseudo",                    "General",   "pseudo"),
    ("Chemin du dossier serveur", "General",   "server_path"),
    ("URL Syncthing",             "Syncthing", "api_url"),
    ("Cle API Syncthing",         "Syncthing", "api_key"),
    ("ID dossier Syncthing",      "Syncthing", "folder_id"),
    ("Arguments Java",            "Server",    "java_args"),
    ("Nom du JAR",                "Server",    "jar_name"),
]


# ==============================================================================
#  SETTINGS
# ==============================================================================

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, config: Config, on_save=None):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        self.title("Parametres")
        self.geometry("540x380")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Parametres",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 8))

        frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20)

        self._entries = {}
        for label, section, key in SETTINGS_FIELDS:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, width=200, anchor="w",
                         font=ctk.CTkFont(size=13)).pack(side="left")
            entry = ctk.CTkEntry(row, width=280)
            entry.insert(0, self.config.get(section, key))
            entry.pack(side="left")
            self._entries[(section, key)] = entry

        ctk.CTkButton(self, text="Sauvegarder", height=40,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._save).pack(pady=15)

    def _save(self):
        for (section, key), entry in self._entries.items():
            self.config.set(section, key, entry.get().strip())
        if self.on_save:
            self.on_save()
        self.destroy()


# ==============================================================================
#  MON ID SYNCTHING
# ==============================================================================

class MyIdWindow(ctk.CTkToplevel):
    """Affiche l'ID Syncthing local pour le partager aux amis."""

    def __init__(self, parent, syncthing: SyncthingClient):
        super().__init__(parent)
        self.title("Mon ID Syncthing")
        self.geometry("520x300")
        self.resizable(False, False)
        self.grab_set()
        self._build(syncthing)

    def _build(self, syncthing):
        ctk.CTkLabel(self, text="Mon ID Syncthing",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(
            self,
            text="Envoie cet ID a tes amis.\nIls le collent dans leur app pour rejoindre le groupe.",
            text_color="gray", justify="center", font=ctk.CTkFont(size=12),
        ).pack(pady=(0, 10))

        self._id_var = ctk.StringVar(value="Chargement...")
        ctk.CTkEntry(self, textvariable=self._id_var, width=460,
                     font=ctk.CTkFont(family="Courier New", size=11),
                     state="readonly", justify="center").pack(padx=20, pady=4)

        self._copy_lbl = ctk.CTkLabel(self, text="", text_color="#4caf50",
                                      font=ctk.CTkFont(size=12))
        self._copy_lbl.pack(pady=4)
        ctk.CTkButton(self, text="Copier l'ID", height=36,
                      command=self._copy).pack(pady=4)

        info = ctk.CTkFrame(self, fg_color="#1a2a1a", corner_radius=8)
        info.pack(fill="x", padx=20, pady=(10, 16))
        ctk.CTkLabel(
            info,
            text="Pour que tes amis soient acceptes automatiquement :\n"
                 "Syncthing > Actions > Parametres > Connexions\n"
                 "> Active 'Accepter automatiquement les nouveaux appareils'",
            text_color="#88cc88", justify="center", font=ctk.CTkFont(size=11),
        ).pack(pady=10)

        threading.Thread(target=self._load, args=(syncthing,), daemon=True).start()

    def _load(self, syncthing):
        ok, result = syncthing.get_my_id()
        self.after(0, self._id_var.set, result if ok else f"Erreur : {result}")

    def _copy(self):
        val = self._id_var.get()
        if val and not val.startswith("Erreur") and val != "Chargement...":
            self.clipboard_clear()
            self.clipboard_append(val)
            self._copy_lbl.configure(text="Copie !")


# ==============================================================================
#  REJOINDRE LE GROUPE
# ==============================================================================

class JoinGroupWindow(ctk.CTkToplevel):
    """L'ami colle l'ID de l'hote pour s'ajouter a son Syncthing."""

    def __init__(self, parent, syncthing: SyncthingClient, log_cb):
        super().__init__(parent)
        self.syncthing = syncthing
        self.log_cb = log_cb
        self.title("Rejoindre le groupe")
        self.geometry("480x270")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Rejoindre le groupe Syncthing",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(
            self,
            text="Colle ici l'ID Syncthing de l'hote.\nTon appareil sera ajoute automatiquement.",
            text_color="gray", justify="center", font=ctk.CTkFont(size=12),
        ).pack(pady=(0, 12))

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=28)

        ctk.CTkLabel(frame, text="Ton pseudo", anchor="w",
                     font=ctk.CTkFont(size=13)).pack(fill="x")
        self.name_entry = ctk.CTkEntry(frame, placeholder_text="Pseudo",
                                       height=36)
        self.name_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="ID Syncthing de l'hote", anchor="w",
                     font=ctk.CTkFont(size=13)).pack(fill="x")
        self.id_entry = ctk.CTkEntry(
            frame, placeholder_text="XXXXXXX-XXXXXXX-XXXXXXX-...", height=36)
        self.id_entry.pack(fill="x", pady=(2, 0))

        self.status_lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12))
        self.status_lbl.pack(pady=8)

        self.btn = ctk.CTkButton(self, text="Rejoindre", height=38,
                                 font=ctk.CTkFont(size=14, weight="bold"),
                                 command=self._join)
        self.btn.pack(pady=(0, 12))

    def _join(self):
        name = self.name_entry.get().strip()
        host_id = self.id_entry.get().strip().upper()

        if not name or not host_id:
            self.status_lbl.configure(text="Remplis les deux champs.",
                                      text_color="#ff9800")
            return

        self.btn.configure(state="disabled", text="Connexion...")
        self.status_lbl.configure(text="Ajout dans Syncthing...", text_color="gray")
        self.update()

        ok, msg = self.syncthing.add_device(host_id, "Hote", auto_accept=True)
        if not ok:
            self.status_lbl.configure(text=f"Erreur : {msg}", text_color="#f44336")
            self.btn.configure(state="normal", text="Rejoindre")
            return

        self.log_cb(f"Connexion au groupe initiee en tant que {name}.")
        self.status_lbl.configure(
            text="Demande envoyee ! Syncthing va synchroniser le dossier.",
            text_color="#4caf50",
        )
        self.btn.configure(state="disabled", text="Fait !")


# ==============================================================================
#  JOIN POPUP  (affichage IP serveur)
# ==============================================================================

class JoinPopup(ctk.CTkToplevel):
    def __init__(self, parent, host, ip):
        super().__init__(parent)
        self.title("Rejoindre le serveur")
        self.geometry("380x220")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text=f"Serveur de {host}",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Copie cette IP dans Minecraft :",
                     text_color="gray").pack()

        ip_var = ctk.StringVar(value=ip)
        ctk.CTkEntry(self, textvariable=ip_var, width=240,
                     font=ctk.CTkFont(size=15), state="readonly",
                     justify="center").pack(pady=8)

        self._lbl = ctk.CTkLabel(self, text="", text_color="#4caf50")
        self._lbl.pack()
        ctk.CTkButton(self, text="Copier l'IP", height=36,
                      command=lambda: self._copy(ip)).pack(pady=4)
        ctk.CTkButton(self, text="Fermer", height=36,
                      fg_color="gray40", hover_color="gray30",
                      command=self.destroy).pack(pady=2)

    def _copy(self, ip):
        self.clipboard_clear()
        self.clipboard_append(ip)
        self._lbl.configure(text="Copie !")
