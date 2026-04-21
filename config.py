import os
import configparser

DEFAULT_CONFIG = {
    "General":   {"pseudo": "Joueur", "server_path": "C:/MC_PROJET_SERVEUR"},
    "Syncthing": {"api_url": "http://localhost:8384", "api_key": "", "folder_id": "MC_PROJET_SERVEUR"},
    "Server":    {"java_args": "-Xmx2G -Xms2G", "jar_name": "paper.jar"},
}


class Config:
    def __init__(self, path="config.ini"):
        self.path = path
        self.cfg = configparser.ConfigParser()
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            self.cfg.read_dict(DEFAULT_CONFIG)
            self._save()
        else:
            self.cfg.read(self.path, encoding="utf-8")
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

    def get(self, section, key, fallback=""):
        return self.cfg.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        if not self.cfg.has_section(section):
            self.cfg.add_section(section)
        self.cfg.set(section, key, value)
        self._save()
