"""
================================================================================
CommandScout: Tactical Syntax & Command Scaffolding Studio
Hardened Multi-Environment Backend Server (command_scout.py)
Austin Davis Technical Portfolio | Project 11
================================================================================
Key Architectural Hardening:
- Threaded non-blocking server (ThreadingHTTPServer)
- Asynchronous Background Task Manager & Multi-Job Tracker (ACTIVE_TASKS)
- Live process execution monitoring & task termination (/api/tasks, /api/tasks/<id>/kill)
- Deliberate Execution Safety Gate with Confirmation & Audit Trail (audit_log.jsonl)
- Distinct environment runners for Linux/WSL2 Kali, Windows/PowerShell 7, and Android/ADB
- Startup schema contract validation (JSON Schema compliance for 111 tools / 417 recipes)
- Cross-platform capability checks with graceful fallbacks
- Hardware sensors telemetry integration (/api/sensors)
================================================================================
"""

import os
import sys
import json
import time
import shutil
import subprocess
import webbrowser
import shlex
import re
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime, timezone

# Platform capability checks
HAS_WINSOUND = False
if sys.platform == "win32":
    try:
        import winsound
        HAS_WINSOUND = True
    except ImportError:
        HAS_WINSOUND = False

STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(STATIC_DIR, "commands_db.json")
SENSORS_PATH = os.path.join(STATIC_DIR, "sensors.json")
AUDIT_LOG_PATH = os.path.join(STATIC_DIR, "audit_log.jsonl")
PORT = 8899

# Global server settings
SERVER_SETTINGS = {
    "trusted_local_mode": False,   # When False, explicit confirmation required on /api/execute
    "command_timeout_sec": 300,    # 5-minute timeout for long jobs like winget upgrade --all
    "audit_enabled": True
}

# ==============================================================================
# ASYNCHRONOUS TASK & MULTI-JOB MONITORING REGISTRY
# ==============================================================================
TASKS_LOCK = threading.Lock()
ACTIVE_TASKS = {}
TASK_COUNTER = 0


class CommandTask:
    def __init__(self, task_id: str, command: str, env: str, shell_args: list[str], client_ip: str):
        self.task_id = task_id
        self.command = command
        self.env = env
        self.shell_args = shell_args
        self.client_ip = client_ip
        self.status = "RUNNING"
        self.start_time = time.time()
        self.end_time = None
        self.exit_code = None
        self.stdout = ""
        self.stderr = ""
        self.process = None
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            self.process = subprocess.Popen(
                self.shell_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            stdout_lines = []
            stderr_lines = []

            def read_pipe(pipe, acc):
                try:
                    for line in iter(pipe.readline, ''):
                        acc.append(line)
                except Exception:
                    pass
                finally:
                    pipe.close()

            t_out = threading.Thread(target=read_pipe, args=(self.process.stdout, stdout_lines), daemon=True)
            t_err = threading.Thread(target=read_pipe, args=(self.process.stderr, stderr_lines), daemon=True)
            t_out.start()
            t_err.start()

            # Wait for process to terminate or timeout
            try:
                self.process.wait(timeout=SERVER_SETTINGS["command_timeout_sec"])
            except subprocess.TimeoutExpired:
                self.terminate()
                self.status = "TIMED_OUT"
                self.stderr += f"\n[CommandScout] Process timed out after {SERVER_SETTINGS['command_timeout_sec']} seconds."
                return

            t_out.join(timeout=2)
            t_err.join(timeout=2)

            self.stdout = "".join(stdout_lines)
            self.stderr = "".join(stderr_lines)
            self.exit_code = self.process.returncode
            if self.status != "CANCELLED":
                self.status = "COMPLETED" if self.exit_code == 0 else "FAILED"

        except Exception as e:
            self.stderr += f"\nProcess execution error: {e}"
            self.status = "FAILED"
            self.exit_code = -1
        finally:
            self.end_time = time.time()
            duration_ms = (self.end_time - self.start_time) * 1000
            play_chime("ok" if self.exit_code == 0 else "warn")
            record_audit(self.env, self.command, True, self.exit_code or -1, duration_ms, self.client_ip, self.stdout, self.stderr)

    def terminate(self) -> bool:
        if self.process and self.status == "RUNNING":
            self.status = "CANCELLED"
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    self.process.terminate()
            except Exception:
                pass
            self.end_time = time.time()
            return True
        return False

    def to_dict(self, include_output: bool = False) -> dict:
        now = time.time()
        elapsed = (self.end_time or now) - self.start_time
        data = {
            "task_id": self.task_id,
            "command": self.command,
            "env": self.env,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_sec": round(elapsed, 1),
            "exit_code": self.exit_code,
            "pid": self.process.pid if self.process else None
        }
        if include_output:
            data["stdout"] = self.stdout
            data["stderr"] = self.stderr
        return data


def play_chime(sound_type="asterisk"):
    """Emits audio confirmation with cross-platform fallback."""
    if HAS_WINSOUND:
        try:
            if sound_type == "ok":
                winsound.MessageBeep(winsound.MB_OK)
            elif sound_type == "warn":
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            else:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            return
        except Exception:
            pass
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:
        pass


def copy_to_clipboard(text: str) -> bool:
    """Sets system clipboard text cleanly across platforms."""
    text_clean = text.strip()
    if not text_clean:
        return False

    if sys.platform == "win32":
        try:
            subprocess.run(["clip.exe"], input=text_clean.encode("utf-16le"), check=True, timeout=5)
            play_chime("asterisk")
            return True
        except Exception:
            pass

        try:
            subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "Set-Clipboard -Value $input"],
                           input=text_clean, text=True, check=True, timeout=5)
            play_chime("asterisk")
            return True
        except Exception as e:
            print(f"[!] Windows clipboard error: {e}")
            return False

    elif sys.platform == "darwin":
        try:
            subprocess.run(["pbcopy"], input=text_clean.encode("utf-8"), check=True, timeout=5)
            play_chime("asterisk")
            return True
        except Exception:
            return False
    else:
        for tool in [["xclip", "-selection", "clipboard"], ["wl-copy"]]:
            if shutil.which(tool[0]):
                try:
                    subprocess.run(tool, input=text_clean.encode("utf-8"), check=True, timeout=5)
                    play_chime("asterisk")
                    return True
                except Exception:
                    pass
        return False


def locate_executable(name: str, fallback_paths: list[str] = None) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    if fallback_paths:
        for p in fallback_paths:
            if os.path.exists(p):
                return p
    return None


def get_environment_runners():
    wsl_bin = locate_executable("wsl.exe", [r"C:\Windows\System32\wsl.exe"])
    pwsh_bin = locate_executable("pwsh.exe", [r"C:\Program Files\PowerShell\7\pwsh.exe"])
    ps_bin = locate_executable("powershell.exe", [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"])
    
    adb_bin = locate_executable("adb.exe", [
        r"C:\ProgramData\chocolatey\bin\adb.exe",
        r"C:\Users\daddy\AppData\Local\Android\Sdk\platform-tools\adb.exe",
        r"C:\Users\daddy\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.1\adb.exe"
    ])

    return {
        "wsl": wsl_bin,
        "powershell": pwsh_bin or ps_bin,
        "is_pwsh7": pwsh_bin is not None,
        "adb": adb_bin
    }


def validate_catalog(db: dict) -> tuple[bool, list[str]]:
    errors = []
    required_envs = ["linux", "windows", "android"]
    
    for env in required_envs:
        if env not in db:
            errors.append(f"Missing required environment: '{env}'")
            continue
        tools = db[env]
        if not isinstance(tools, list):
            errors.append(f"Environment '{env}' must be a list of tools")
            continue

        for t_idx, tool in enumerate(tools):
            t_id = tool.get("id")
            if not t_id:
                errors.append(f"[{env}] Tool at index {t_idx} missing 'id'")
            if not tool.get("name"):
                errors.append(f"[{env}/{t_id}] Missing 'name'")
            if not tool.get("category"):
                errors.append(f"[{env}/{t_id}] Missing 'category'")
            
            recipes = tool.get("recipes", [])
            if not isinstance(recipes, list) or len(recipes) == 0:
                errors.append(f"[{env}/{t_id}] Must contain at least 1 recipe")
                continue

            for r_idx, r in enumerate(recipes):
                r_id = r.get("id")
                if not r_id:
                    errors.append(f"[{env}/{t_id}] Recipe at index {r_idx} missing 'id'")
                template = r.get("template")
                if not template:
                    errors.append(f"[{env}/{t_id}/{r_id}] Missing 'template'")
                    continue

                placeholders = re.findall(r"\{\{([a-zA-Z0-9_-]+)\}\}", template)
                param_keys = {p.get("key") for p in r.get("params", []) if isinstance(p, dict)}
                for ph in placeholders:
                    if ph not in param_keys:
                        errors.append(f"[{env}/{t_id}/{r_id}] Template placeholder '{{{{{ph}}}}}' missing in params")

    return (len(errors) == 0, errors)


def record_audit(env: str, command: str, confirmed: bool, exit_code: int, duration_ms: float, client_ip: str, stdout: str, stderr: str):
    if not SERVER_SETTINGS["audit_enabled"]:
        return
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_ip": client_ip,
        "environment": env,
        "command": command,
        "confirmed": confirmed,
        "exit_code": exit_code,
        "duration_ms": round(duration_ms, 2),
        "stdout_snippet": stdout[:200] if stdout else "",
        "stderr_snippet": stderr[:200] if stderr else ""
    }
    try:
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[!] Audit logging error: {e}")


class CommandScoutHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def send_json(self, status_code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_json_error(self, status_code: int, code: str, message: str, details: dict = None):
        payload = {
            "status": "error",
            "code": code,
            "message": message,
            "details": details or {}
        }
        self.send_json(status_code, payload)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            runners = get_environment_runners()
            stats = {}
            if os.path.exists(DB_PATH):
                try:
                    with open(DB_PATH, "r", encoding="utf-8") as f:
                        db = json.load(f)
                        stats = db.get("metadata", {})
                except Exception:
                    pass

            with TASKS_LOCK:
                active_count = sum(1 for t in ACTIVE_TASKS.values() if t.status == "RUNNING")

            self.send_json(200, {
                "status": "healthy",
                "service": "CommandScout Studio",
                "port": PORT,
                "offline_mode": True,
                "active_tasks_count": active_count,
                "runners": {
                    "wsl": runners["wsl"] is not None,
                    "powershell": runners["powershell"] is not None,
                    "is_pwsh7": runners["is_pwsh7"],
                    "adb": runners["adb"] is not None
                },
                "settings": SERVER_SETTINGS,
                "metadata": stats
            })
            return

        elif parsed.path == "/api/commands":
            if not os.path.exists(DB_PATH):
                self.send_json_error(404, "DATABASE_NOT_FOUND", "commands_db.json not found on server.")
                return
            try:
                with open(DB_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.send_json(200, data)
            except Exception as e:
                self.send_json_error(500, "DATABASE_READ_ERROR", f"Error reading commands_db.json: {e}")
            return

        elif parsed.path == "/api/sensors":
            if not os.path.exists(SENSORS_PATH):
                self.send_json_error(404, "SENSORS_NOT_FOUND", "sensors.json not found.")
                return
            try:
                with open(SENSORS_PATH, "r", encoding="utf-8") as f:
                    sensors = json.load(f)
                self.send_json(200, sensors)
            except Exception as e:
                self.send_json_error(500, "SENSORS_READ_ERROR", f"Error reading sensors.json: {e}")
            return

        elif parsed.path == "/api/tasks":
            # List all tasks with active summary
            with TASKS_LOCK:
                task_list = [t.to_dict(include_output=False) for t in ACTIVE_TASKS.values()]
                task_list.sort(key=lambda x: x["start_time"], reverse=True)
                active_count = sum(1 for t in task_list if t["status"] == "RUNNING")

            self.send_json(200, {
                "active_count": active_count,
                "total_count": len(task_list),
                "tasks": task_list[:30]
            })
            return

        elif parsed.path.startswith("/api/tasks/"):
            # Get individual task details with live stdout/stderr
            task_id = parsed.path[len("/api/tasks/"):].strip()
            with TASKS_LOCK:
                task = ACTIVE_TASKS.get(task_id)
            if not task:
                self.send_json_error(404, "TASK_NOT_FOUND", f"Task '{task_id}' was not found.")
                return
            self.send_json(200, task.to_dict(include_output=True))
            return

        elif parsed.path == "/api/audit":
            entries = []
            if os.path.exists(AUDIT_LOG_PATH):
                try:
                    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                entries.append(json.loads(line.strip()))
                except Exception as e:
                    print(f"[!] Error reading audit log: {e}")
            self.send_json(200, {"entries": entries[-50:]})
            return

        return super().do_GET()

    def do_POST(self):
        global TASK_COUNTER
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"

        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if parsed.path == "/api/copy":
            cmd = payload.get("command", "").strip()
            if not cmd:
                self.send_json_error(400, "EMPTY_COMMAND", "No command provided to copy.")
                return
            success = copy_to_clipboard(cmd)
            self.send_json(200, {
                "status": "success" if success else "failed",
                "copied": success,
                "command": cmd
            })
            return

        elif parsed.path == "/api/settings":
            if "trusted_local_mode" in payload:
                SERVER_SETTINGS["trusted_local_mode"] = bool(payload["trusted_local_mode"])
            self.send_json(200, {"status": "success", "settings": SERVER_SETTINGS})
            return

        elif parsed.path.startswith("/api/tasks/") and parsed.path.endswith("/kill"):
            # Terminate running task: /api/tasks/<id>/kill
            parts = parsed.path.split("/")
            if len(parts) >= 4:
                task_id = parts[3]
                with TASKS_LOCK:
                    task = ACTIVE_TASKS.get(task_id)
                if not task:
                    self.send_json_error(404, "TASK_NOT_FOUND", f"Task '{task_id}' not found.")
                    return
                killed = task.terminate()
                self.send_json(200, {
                    "status": "cancelled" if killed else "already_terminated",
                    "task_id": task_id
                })
                return

        elif parsed.path == "/api/execute":
            cmd = payload.get("command", "").strip()
            raw_env = payload.get("env", "powershell").lower().strip()
            confirmed = bool(payload.get("confirmed", False))

            if not cmd:
                self.send_json_error(400, "EMPTY_COMMAND", "Command text cannot be empty.")
                return

            if re.search(r"\{\{[a-zA-Z0-9_-]+\}\}", cmd):
                self.send_json_error(400, "UNRESOLVED_PLACEHOLDERS", "Command contains unpopulated template parameters.")
                return

            if not SERVER_SETTINGS["trusted_local_mode"] and not confirmed:
                self.send_json_error(403, "CONFIRMATION_REQUIRED",
                                     "Execution safety gate active. Please confirm live execution in the modal.",
                                     {"command": cmd, "env": raw_env})
                return

            runners = get_environment_runners()
            shell_args = []
            normalized_env = "powershell"

            if raw_env in ["wsl", "linux", "kali"]:
                normalized_env = "wsl"
                if not runners["wsl"]:
                    self.send_json_error(503, "WSL_UNAVAILABLE", "WSL2 executable (wsl.exe) was not found on this host.")
                    return
                shell_args = [runners["wsl"], "bash", "-c", cmd]

            elif raw_env in ["android", "adb"]:
                normalized_env = "adb"
                if not runners["adb"]:
                    self.send_json_error(503, "ADB_UNAVAILABLE", "Android Debug Bridge (adb.exe) was not found on this host.")
                    return
                if cmd.startswith("adb "):
                    clean_sub = cmd[4:].strip()
                    shell_args = [runners["adb"]] + shlex.split(clean_sub)
                else:
                    shell_args = [runners["adb"], "shell", cmd]

            else:
                normalized_env = "powershell"
                if not runners["powershell"]:
                    self.send_json_error(503, "POWERSHELL_UNAVAILABLE", "PowerShell binary was not found on this host.")
                    return
                shell_args = [runners["powershell"], "-NoProfile", "-NonInteractive", "-Command", cmd]

            # Generate Unique Task ID and Launch in Background
            with TASKS_LOCK:
                TASK_COUNTER += 1
                task_id = f"task_{TASK_COUNTER}_{int(time.time())}"
                client_ip = self.client_address[0] if self.client_address else "127.0.0.1"
                task = CommandTask(task_id, cmd, normalized_env, shell_args, client_ip)
                ACTIVE_TASKS[task_id] = task

            print(f"\n[CommandScout] Task Launched [{task_id}] ({normalized_env}): {cmd}")
            task.start()

            # Return task ID immediately so UI can monitor it asynchronously
            self.send_json(200, {
                "status": "started",
                "task_id": task_id,
                "command": cmd,
                "env": normalized_env,
                "message": "Task dispatched to background execution."
            })
            return

        self.send_json_error(404, "ENDPOINT_NOT_FOUND", f"Endpoint {parsed.path} does not exist.")


def start_server():
    print("=" * 70)
    print("       COMMANDSCOUT: TACTICAL SYNTAX & SCAFFOLDING STUDIO v2.1")
    print("=" * 70)

    if not os.path.exists(DB_PATH):
        print(f"[!] FATAL: Database file missing at {DB_PATH}")
        sys.exit(1)

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except Exception as e:
        print(f"[!] FATAL: Failed to parse {DB_PATH}: {e}")
        sys.exit(1)

    is_valid, validation_errors = validate_catalog(catalog)
    if not is_valid:
        print(f"[!] FATAL: Database contract validation failed ({len(validation_errors)} errors):")
        for err in validation_errors[:10]:
            print(f"    - {err}")
        sys.exit(1)

    meta = catalog.get("metadata", {})
    print(f"  [+] Catalog Contract Verified:")
    print(f"      • Schema Version:  {meta.get('schema_version', '2.0.0')}")
    print(f"      • Total Tools:     {meta.get('total_tools', 'N/A')}")
    print(f"      • Total Recipes:   {meta.get('total_recipes', 'N/A')}")
    for env_name, env_data in meta.get("environments", {}).items():
        print(f"        - {env_name.upper():<8}: {env_data.get('tools')} tools | {env_data.get('recipes')} recipes")

    runners = get_environment_runners()
    print("\n  [+] Runtime Environment Runners:")
    print(f"      • Linux / WSL2:    {'[READY] ' + runners['wsl'] if runners['wsl'] else '[DISABLED]'}")
    ps_label = "PowerShell 7 (pwsh)" if runners["is_pwsh7"] else "Windows PowerShell 5"
    print(f"      • Windows Shell:   {'[READY] ' + ps_label + ' (' + runners['powershell'] + ')' if runners['powershell'] else '[DISABLED]'}")
    print(f"      • Android / ADB:   {'[READY] ' + runners['adb'] if runners['adb'] else '[DISABLED]'}")

    print("\n  [+] Operational Mode:")
    print(f"      • Deployment:      100% Offline-First (Localhost Only)")
    print(f"      • Task Monitoring: Live Multi-Job Background Registry Active")
    print(f"      • Default Action:  1-Click Copy to Clipboard")
    print(f"      • Audit Trail:     {AUDIT_LOG_PATH}")

    server = ThreadingHTTPServer(("127.0.0.1", PORT), CommandScoutHandler)
    url = f"http://127.0.0.1:{PORT}"
    print("-" * 70)
    print(f"  [*] Server active on: \033[1;36m{url}\033[0m")
    print("  [*] Launching tactical browser interface...\n")
    print("=" * 70)

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[CommandScout] Server shut down cleanly. Stay tactical.")
        server.server_close()


if __name__ == "__main__":
    start_server()
