"""Tests for VeronicaBrain Reasoning & Memory"""

import unittest
from modules.veronica_guard import VeronicaGuard
from modules.os_controller import OSController
from core.memory import MemoryStore
from core.brain import VeronicaBrain


class TestVeronicaBrain(unittest.TestCase):
    def setUp(self):
        self.guard = VeronicaGuard()
        self.controller = OSController()
        self.memory = MemoryStore()
        self.brain = VeronicaBrain(self.guard, self.controller, self.memory, voice=None)

    def test_status_query(self):
        res = self.brain.process_query("What is the system status?", speak_output=False)
        self.assertIn("health", res["text"].lower())
        self.assertEqual(res["tool_used"], "get_system_telemetry")

    def test_purge_ram_query(self):
        res = self.brain.process_query("purge ram now", speak_output=False)
        self.assertIn("purge ram", res["text"].lower())
        self.assertEqual(res["tool_used"], "execute_contingency")

    def test_system_info_query(self):
        res = self.brain.process_query("show system info and uptime", speak_output=False)
        self.assertIn("node", res["text"].lower())
        self.assertEqual(res["tool_used"], "get_system_info")

    def test_memory_logging(self):
        self.brain.process_query("system check", speak_output=False)
        history = self.memory.get_recent_history(limit=2)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")


if __name__ == "__main__":
    unittest.main()
