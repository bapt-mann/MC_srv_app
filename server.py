import os
import subprocess
import threading

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


class ServerProcess:
    def __init__(self):
        self._proc = None
        self._running = False
        self._cb = None

    def start(self, server_path, java_args, jar_name, output_cb):
        """Lance PaperMC en arriere-plan. Retourne True si OK."""
        self._cb = output_cb
        cmd = f'java {java_args} -jar "{jar_name}" nogui'
        try:
            self._proc = subprocess.Popen(
                cmd, cwd=server_path,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1,
                shell=True, creationflags=_NO_WINDOW,
            )
            self._running = True
            threading.Thread(target=self._reader, daemon=True).start()
            return True
        except Exception as exc:
            self._emit(f"[ERREUR] {exc}")
            return False

    def send_command(self, cmd):
        """Envoie une commande a la console Java (ex: 'stop')."""
        if self._proc and self._running:
            try:
                self._proc.stdin.write(cmd + "\n")
                self._proc.stdin.flush()
            except Exception:
                pass

    def stop(self):
        self.send_command("stop")

    def wait(self, timeout=60):
        if self._proc:
            try:
                self._proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            finally:
                self._running = False

    def is_running(self):
        return self._proc is not None and self._proc.poll() is None

    def _reader(self):
        for line in self._proc.stdout:
            self._emit(line.rstrip())
        self._running = False

    def _emit(self, line):
        if self._cb:
            self._cb(line)
