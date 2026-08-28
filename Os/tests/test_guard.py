"""Tests for VeronicaGuard Telemetry & Contingencies"""

import unittest
from modules.veronica_guard import VeronicaGuard, TelemetrySnapshot


class TestVeronicaGuard(unittest.TestCase):
    def setUp(self):
        self.guard = VeronicaGuard()

    def test_get_telemetry(self):
        snap = self.guard.get_telemetry()
        self.assertIsInstance(snap, TelemetrySnapshot)
        self.assertGreaterEqual(snap.cpu_percent, 0.0)
        self.assertGreaterEqual(snap.ram_percent, 0.0)
        self.assertGreaterEqual(snap.disk_percent, 0.0)
        self.assertIn(snap.health_status, ["OPTIMAL", "ELEVATED", "CRITICAL"])
        self.assertIsInstance(snap.top_cpu_processes, list)
        self.assertIsInstance(snap.top_ram_processes, list)

    def test_purge_ram_contingency(self):
        res = self.guard.execute_contingency("PROTOCOL_PURGE_RAM")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("freed_pct", res["details"])
        self.assertIn("objects_collected", res["details"])

    def test_cool_down_contingency(self):
        res = self.guard.execute_contingency("PROTOCOL_COOL_DOWN")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("heavy_processes", res["details"])

    def test_diagnostic_report_contingency(self):
        res = self.guard.execute_contingency("PROTOCOL_DIAGNOSTIC_REPORT")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("health_status", res["details"])

    def test_unknown_contingency(self):
        res = self.guard.execute_contingency("PROTOCOL_UNKNOWN_XYZ")
        self.assertEqual(res["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
