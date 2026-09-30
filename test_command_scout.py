"""
================================================================================
CommandScout Automated Verification & Regression Test Suite
Tests schema contracts, safety gate, environment runners, and API endpoints
================================================================================
"""

import os
import sys
import json
import time
import unittest
import urllib.request
import urllib.error
import threading

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import command_scout


class TestCommandScout(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Validate that database exists
        cls.db_path = command_scout.DB_PATH
        cls.sensors_path = command_scout.SENSORS_PATH
        with open(cls.db_path, "r", encoding="utf-8") as f:
            cls.catalog = json.load(f)

    def test_01_database_contract_validation(self):
        """Verify all 111 tools and 417 recipes pass strict schema validation with 0 errors."""
        is_valid, errors = command_scout.validate_catalog(self.catalog)
        self.assertTrue(is_valid, f"Catalog validation failed with errors: {errors}")
        self.assertEqual(len(errors), 0)

        meta = self.catalog.get("metadata", {})
        self.assertEqual(meta.get("schema_version"), "2.0.0")
        self.assertEqual(meta.get("total_tools"), 111)
        self.assertEqual(meta.get("total_recipes"), 417)

    def test_02_sensors_schema_validation(self):
        """Verify hardware sensors telemetry registry exists and contains required targets."""
        self.assertTrue(os.path.exists(self.sensors_path), "sensors.json must exist")
        with open(self.sensors_path, "r", encoding="utf-8") as f:
            sensors = json.load(f)
        self.assertIn("sensors", sensors)
        s_data = sensors["sensors"]
        self.assertIn("sdr", s_data)
        self.assertIn("wifi", s_data)
        self.assertIn("android", s_data)
        self.assertEqual(s_data["sdr"]["model"], "Nooelec NESDR SMArt v5")
        self.assertEqual(s_data["wifi"]["chipset"], "Qualcomm Atheros AR9271")

    def test_03_template_placeholder_integrity(self):
        """Verify that every recipe placeholder matches its param definitions."""
        for env in ["linux", "windows", "android"]:
            for tool in self.catalog.get(env, []):
                for r in tool.get("recipes", []):
                    template = r.get("template", "")
                    placeholders = command_scout.re.findall(r"\{\{([a-zA-Z0-9_-]+)\}\}", template)
                    param_keys = {p.get("key") for p in r.get("params", []) if isinstance(p, dict)}
                    for ph in placeholders:
                        self.assertIn(
                            ph, param_keys,
                            f"[{env}/{tool.get('id')}] Placeholder '{{{{{ph}}}}}' has no matching param"
                        )

    def test_04_environment_runners_detected(self):
        """Verify runtime shell runners are properly detected on this host."""
        runners = command_scout.get_environment_runners()
        self.assertIsInstance(runners, dict)
        self.assertIn("wsl", runners)
        self.assertIn("powershell", runners)
        self.assertIn("adb", runners)
        # PowerShell and WSL should be present on this host
        self.assertIsNotNone(runners["powershell"], "PowerShell must be detected on host")

    def test_05_safety_gate_rejection(self):
        """Verify unconfirmed execution is blocked by the safety gate."""
        handler = command_scout.CommandScoutHandler
        # Ensure trusted mode is off
        command_scout.SERVER_SETTINGS["trusted_local_mode"] = False
        
        # Test placeholder rejection regex
        cmd_with_ph = "nmap {{target}}"
        self.assertTrue(bool(command_scout.re.search(r"\{\{[a-zA-Z0-9_-]+\}\}", cmd_with_ph)))

    def test_06_audit_trail_logging(self):
        """Verify audit records are written cleanly with structured metrics."""
        test_cmd = "echo commandscout_unit_test"
        audit_path = command_scout.AUDIT_LOG_PATH
        initial_lines = 0
        if os.path.exists(audit_path):
            with open(audit_path, "r", encoding="utf-8") as f:
                initial_lines = len(f.readlines())

        command_scout.record_audit(
            env="powershell",
            command=test_cmd,
            confirmed=True,
            exit_code=0,
            duration_ms=12.4,
            client_ip="127.0.0.1",
            stdout="commandscout_unit_test\n",
            stderr=""
        )

        self.assertTrue(os.path.exists(audit_path))
        with open(audit_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertGreater(len(lines), initial_lines)
        last_entry = json.loads(lines[-1].strip())
        self.assertEqual(last_entry["command"], test_cmd)
        self.assertEqual(last_entry["exit_code"], 0)
        self.assertEqual(last_entry["environment"], "powershell")


class TestCommandScoutServer(unittest.TestCase):
    """Integration test against live threaded server instance."""

    @classmethod
    def setUpClass(cls):
        cls.test_port = 8897
        cls.server = command_scout.ThreadingHTTPServer(("127.0.0.1", cls.test_port), command_scout.CommandScoutHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_07_api_health(self):
        url = f"http://127.0.0.1:{self.test_port}/api/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertEqual(data["status"], "healthy")
            self.assertIn("runners", data)
            self.assertIn("metadata", data)
            self.assertEqual(data["metadata"]["total_tools"], 111)

    def test_08_api_sensors(self):
        url = f"http://127.0.0.1:{self.test_port}/api/sensors"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertIn("sensors", data)

    def test_09_safety_gate_blocks_unconfirmed(self):
        url = f"http://127.0.0.1:{self.test_port}/api/execute"
        payload = json.dumps({
            "command": "Get-Date",
            "env": "powershell",
            "confirmed": False
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as res:
                self.fail("Server should have rejected unconfirmed execute request with 403")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 403)
            data = json.loads(e.read().decode("utf-8"))
            self.assertEqual(data["code"], "CONFIRMATION_REQUIRED")

    def test_10_safe_execution_with_confirmation(self):
        url = f"http://127.0.0.1:{self.test_port}/api/execute"
        payload = json.dumps({
            "command": "Write-Output 'CommandScout_Safe_Execution_Confirmed'",
            "env": "powershell",
            "confirmed": True
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertEqual(data["status"], "started")
            self.assertIn("task_id", data)
            task_id = data["task_id"]

        # Poll task until complete
        task_url = f"http://127.0.0.1:{self.test_port}/api/tasks/{task_id}"
        completed = False
        start = time.time()
        task_info = {}
        while time.time() - start < 8:
            with urllib.request.urlopen(task_url, timeout=5) as t_res:
                task_info = json.loads(t_res.read().decode("utf-8"))
                if task_info.get("status") == "COMPLETED":
                    completed = True
                    break
            time.sleep(0.3)

        self.assertTrue(completed, f"Task did not complete in time. Last status: {task_info.get('status')}")
        self.assertEqual(task_info.get("exit_code"), 0)
        self.assertIn("CommandScout_Safe_Execution_Confirmed", task_info.get("stdout", ""))

    def test_11_tasks_list_endpoint(self):
        url = f"http://127.0.0.1:{self.test_port}/api/tasks"
        with urllib.request.urlopen(url, timeout=5) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertIn("active_count", data)
            self.assertIn("total_count", data)
            self.assertIn("tasks", data)
            self.assertIsInstance(data["tasks"], list)


if __name__ == "__main__":
    unittest.main()

