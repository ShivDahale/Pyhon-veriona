"""Tests for OSController Automation & Safety"""

import unittest
from modules.os_controller import OSController


class TestOSController(unittest.TestCase):
    def setUp(self):
        self.controller = OSController()

    def test_get_system_info(self):
        info = self.controller.get_system_info()
        self.assertIn("hostname", info)
        self.assertIn("os_name", info)
        self.assertIn("uptime", info)
        self.assertIn("local_ip", info)

    def test_list_processes(self):
        procs = self.controller.list_processes(limit=5)
        self.assertIsInstance(procs, list)
        self.assertLessEqual(len(procs), 5)
        if procs:
            self.assertIn("pid", procs[0])
            self.assertIn("name", procs[0])

    def test_safe_mode_blocks_dangerous_commands(self):
        res = self.controller.execute_command("format C: /y")
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("Security violation", res["error"])

    def test_execute_safe_command(self):
        res = self.controller.execute_command("echo 'Hello Veronica'")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("Hello Veronica", res["stdout"])


if __name__ == "__main__":
    unittest.main()
