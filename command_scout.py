"""
CommandScout: Tactical Syntax & Command Scaffolding Studio
Backend Server (command_scout.py)
- Serves the CommandScout interactive 1-click web interface on localhost:8899
- Handles Windows clipboard copying with system audio confirmation (winsound)
- Optional direct execution into PowerShell or WSL2
"""

import os
import sys
import json
import subprocess
import webbrowser
import winsound
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import tkinter as tk

STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8899

def copy_to_windows_clipboard(text: str) -> bool:
    """Sets Windows clipboard text cleanly and sounds an audio confirmation."""
    try:
        # Use native Windows clip.exe for guaranteed persistence across all apps & VMs
        subprocess.run(["clip.exe"], input=text.strip().encode("utf-16le"), check=True)
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        return True
    except Exception:
        try:
            # Fallback to PowerShell Set-Clipboard
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", "Set-Clipboard -Value $input"], input=text.strip(), text=True, check=True)
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            return True
        except Exception as e:
            print(f"[!] Clipboard error: {e}")
            return False

class CommandScoutHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "port": PORT}).encode("utf-8"))
            return
        elif parsed.path == "/api/commands":
            db_path = os.path.join(STATIC_DIR, "commands_db.json")
            if os.path.exists(db_path):
                with open(db_path, "r", encoding="utf-8") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data.encode("utf-8"))
                return
            else:
                self.send_error(404, "commands_db.json not found")
                return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if parsed.path == "/api/copy":
            cmd = payload.get("command", "")
            if cmd:
                success = copy_to_windows_clipboard(cmd)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": success, "command": cmd}).encode("utf-8"))
            else:
                self.send_response(400)
                self.end_headers()
            return

        elif parsed.path == "/api/execute":
            cmd = payload.get("command", "")
            target_env = payload.get("env", "powershell").lower()

            if not cmd:
                self.send_response(400)
                self.end_headers()
                return

            print(f"\n[CommandScout] Executing ({target_env}): {cmd}")

            try:
                if target_env == "wsl":
                    # Execute in WSL2 Kali/Ubuntu
                    shell_args = ["wsl.exe", "bash", "-c", cmd]
                else:
                    # Execute in PowerShell
                    shell_args = ["powershell.exe", "-NoProfile", "-Command", cmd]

                proc = subprocess.run(shell_args, capture_output=True, text=True, timeout=60)
                winsound.MessageBeep(winsound.MB_OK)

                res = {
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exit_code": proc.returncode
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except subprocess.TimeoutExpired:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Command timed out after 60 seconds."}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_error(404, "Endpoint not found")

def start_server():
    server = HTTPServer(("127.0.0.1", PORT), CommandScoutHandler)
    url = f"http://127.0.0.1:{PORT}"
    print("=" * 65)
    print("       COMMANDSCOUT: TACTICAL SYNTAX & SCAFFOLDING STUDIO")
    print(f"       Running on: {url}")
    print("=" * 65)
    print(">> Mitigating hand fatigue: 1-click syntax copy & parameter builder.")
    print(">> Opening browser UI automatically...\n")
    
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[CommandScout] Shutting down cleanly. Stay tactical.")
        server.server_close()

if __name__ == "__main__":
    start_server()
