import requests


class SyncthingClient:
    def __init__(self, api_url, api_key, folder_id):
        self.api_url = api_url
        self.api_key = api_key
        self.folder_id = folder_id

    def _headers(self):
        return {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    def get_my_id(self):
        """Retourne (ok, device_id) depuis /rest/system/status."""
        try:
            r = requests.get(f"{self.api_url}/rest/system/status",
                             headers=self._headers(), timeout=4)
            if r.status_code == 200:
                return True, r.json().get("myID", "")
            return False, f"Erreur API ({r.status_code})"
        except Exception as e:
            return False, str(e)

    def add_device(self, device_id, name, auto_accept=True):
        """Ajoute un appareil au Syncthing local. Retourne (ok, message)."""
        try:
            payload = {"deviceID": device_id, "name": name,
                       "autoAcceptFolders": auto_accept}
            r = requests.post(f"{self.api_url}/rest/config/devices",
                              headers=self._headers(), json=payload, timeout=5)
            if r.status_code in (200, 201):
                return True, "Appareil ajoute."
            if r.status_code == 409:
                return True, "Appareil deja connu."
            return False, f"Erreur API ({r.status_code})"
        except Exception as e:
            return False, str(e)

    def share_folder(self, device_id):
        """Partage le dossier configure avec un appareil. Retourne (ok, message)."""
        try:
            r = requests.get(
                f"{self.api_url}/rest/config/folders/{self.folder_id}",
                headers=self._headers(), timeout=5)
            if r.status_code != 200:
                return False, f"Dossier '{self.folder_id}' introuvable."
            cfg = r.json()
            existing = [d["deviceID"] for d in cfg.get("devices", [])]
            if device_id in existing:
                return True, "Partage deja actif."
            cfg["devices"].append({"deviceID": device_id, "encryptionPassword": ""})
            r2 = requests.put(
                f"{self.api_url}/rest/config/folders/{self.folder_id}",
                headers=self._headers(), json=cfg, timeout=5)
            if r2.status_code in (200, 201):
                return True, "Dossier partage."
            return False, f"Erreur partage ({r2.status_code})"
        except Exception as e:
            return False, str(e)

    def get_state(self):
        """Retourne l'etat de sync : idle / syncing / scanning / offline / no_key / error."""
        if not self.api_key.strip():
            return "no_key"
        try:
            r = requests.get(f"{self.api_url}/rest/db/status",
                             headers=self._headers(),
                             params={"folder": self.folder_id}, timeout=4)
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
