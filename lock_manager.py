import json
from pathlib import Path


class LockManager:
    def __init__(self, server_path):
        self.lock_path = Path(server_path) / "lock.json"

    def update_path(self, server_path):
        self.lock_path = Path(server_path) / "lock.json"

    def exists(self):
        return self.lock_path.exists()

    def read(self):
        try:
            with open(self.lock_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def create(self, pseudo, ip):
        data = {"status": "online", "host": pseudo, "ip": f"{ip}:25565"}
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lock_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def delete(self):
        try:
            self.lock_path.unlink(missing_ok=True)
        except Exception:
            pass
