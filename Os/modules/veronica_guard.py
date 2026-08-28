"""
V.E.R.O.N.I.C.A. Guard & Telemetry Module
Oversees system health, hardware diagnostics, and automated contingency protocols.
"""

from __future__ import annotations
import os
import sys
import time
import gc
import ctypes
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import psutil


@dataclass
class TelemetrySnapshot:
    timestamp: float
    cpu_percent: float
    cpu_cores_percent: List[float]
    ram_total_gb: float
    ram_used_gb: float
    ram_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    battery_percent: Optional[float] = None
    power_plugged: Optional[bool] = None
    top_cpu_processes: List[Dict[str, Any]] = field(default_factory=list)
    top_ram_processes: List[Dict[str, Any]] = field(default_factory=list)
    health_status: str = "OPTIMAL"  # OPTIMAL, ELEVATED, CRITICAL
    active_alerts: List[str] = field(default_factory=list)


class VeronicaGuard:
    """
    Tactical System Health Monitor & Contingency Engine.
    Inspired by Tony Stark's orbital deployment & monitoring platform.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        telemetry_cfg = self.config.get("telemetry", {})
        thresholds = telemetry_cfg.get("thresholds", {})
        self.cpu_warn = thresholds.get("cpu_warning_pct", 80.0)
        self.cpu_crit = thresholds.get("cpu_critical_pct", 95.0)
        self.ram_warn = thresholds.get("ram_warning_pct", 85.0)
        self.ram_crit = thresholds.get("ram_critical_pct", 95.0)
        self.disk_warn = thresholds.get("disk_warning_pct", 90.0)
        self.disk_crit = thresholds.get("disk_critical_pct", 98.0)
        self.history: List[TelemetrySnapshot] = []

    def get_telemetry(self, process_limit: int = 5) -> TelemetrySnapshot:
        """Captures a complete snapshot of current hardware metrics."""
        now = time.time()
        cpu_total = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_percent(interval=0.0, percpu=True)

        ram = psutil.virtual_memory()
        ram_total_gb = round(ram.total / (1024 ** 3), 2)
        ram_used_gb = round(ram.used / (1024 ** 3), 2)
        ram_pct = ram.percent

        disk = psutil.disk_usage(os.path.abspath(os.sep))
        disk_total_gb = round(disk.total / (1024 ** 3), 2)
        disk_used_gb = round(disk.used / (1024 ** 3), 2)
        disk_pct = disk.percent

        battery_pct = None
        power_plugged = None
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_pct = battery.percent
                power_plugged = battery.power_plugged
        except Exception:
            pass

        # Top processes by CPU and Memory
        processes = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = p.info
                if info['pid'] != 0: # skip system idle
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        top_cpu = sorted(
            [p for p in processes if p.get('cpu_percent') is not None],
            key=lambda x: x['cpu_percent'],
            reverse=True
        )[:process_limit]

        top_ram = sorted(
            [p for p in processes if p.get('memory_percent') is not None],
            key=lambda x: x['memory_percent'],
            reverse=True
        )[:process_limit]

        # Evaluate Health
        alerts = []
        health_status = "OPTIMAL"

        if cpu_total >= self.cpu_crit:
            alerts.append(f"CRITICAL: CPU load at {cpu_total:.1f}%")
            health_status = "CRITICAL"
        elif cpu_total >= self.cpu_warn:
            alerts.append(f"WARNING: Elevated CPU load at {cpu_total:.1f}%")
            if health_status != "CRITICAL":
                health_status = "ELEVATED"

        if ram_pct >= self.ram_crit:
            alerts.append(f"CRITICAL: Memory utilization at {ram_pct:.1f}%")
            health_status = "CRITICAL"
        elif ram_pct >= self.ram_warn:
            alerts.append(f"WARNING: Elevated Memory utilization at {ram_pct:.1f}%")
            if health_status != "CRITICAL":
                health_status = "ELEVATED"

        if disk_pct >= self.disk_crit:
            alerts.append(f"CRITICAL: Primary disk capacity at {disk_pct:.1f}%")
            health_status = "CRITICAL"
        elif disk_pct >= self.disk_warn:
            alerts.append(f"WARNING: Disk capacity at {disk_pct:.1f}%")
            if health_status != "CRITICAL":
                health_status = "ELEVATED"

        snapshot = TelemetrySnapshot(
            timestamp=now,
            cpu_percent=cpu_total,
            cpu_cores_percent=cpu_cores,
            ram_total_gb=ram_total_gb,
            ram_used_gb=ram_used_gb,
            ram_percent=ram_pct,
            disk_total_gb=disk_total_gb,
            disk_used_gb=disk_used_gb,
            disk_percent=disk_pct,
            battery_percent=battery_pct,
            power_plugged=power_plugged,
            top_cpu_processes=top_cpu,
            top_ram_processes=top_ram,
            health_status=health_status,
            active_alerts=alerts
        )

        self.history.append(snapshot)
        if len(self.history) > 120:  # Keep last 120 snapshots
            self.history.pop(0)

        return snapshot

    def execute_contingency(self, protocol_name: str, **kwargs) -> Dict[str, Any]:
        """
        Executes a targeted contingency protocol.
        Supported Protocols:
        - PROTOCOL_PURGE_RAM: Force garbage collection and identify memory hogs.
        - PROTOCOL_COOL_DOWN: Identifies and reports/throttles runaway CPU tasks.
        - PROTOCOL_LOCKDOWN: Immediate workstation lockdown.
        - PROTOCOL_DIAGNOSTIC_REPORT: Comprehensive tactical hardware summary.
        """
        normalized_name = protocol_name.upper().strip()
        result = {
            "protocol": normalized_name,
            "status": "SUCCESS",
            "timestamp": time.time(),
            "details": {}
        }

        if normalized_name in ["PROTOCOL_PURGE_RAM", "PURGE_RAM", "MEMORY_CLEAN"]:
            gc_collected = gc.collect()
            ram_before = psutil.virtual_memory().percent
            time.sleep(0.1)
            ram_after = psutil.virtual_memory().percent
            result["details"] = {
                "message": "Memory purge completed.",
                "objects_collected": gc_collected,
                "ram_percent_before": ram_before,
                "ram_percent_after": ram_after,
                "freed_pct": max(0.0, round(ram_before - ram_after, 2))
            }

        elif normalized_name in ["PROTOCOL_COOL_DOWN", "COOL_DOWN", "THROTTLE_CHECK"]:
            top_hogs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    if p.info['cpu_percent'] and p.info['cpu_percent'] > 20.0:
                        top_hogs.append(p.info)
                except Exception:
                    continue
            result["details"] = {
                "message": "Thermal and CPU load analysis executed.",
                "heavy_processes": top_hogs,
                "recommended_action": "Terminate runaway processes if unneeded." if top_hogs else "CPU within normal parameters."
            }

        elif normalized_name in ["PROTOCOL_LOCKDOWN", "LOCKDOWN", "EMERGENCY_LOCK"]:
            # Workstation lock
            locked = False
            if sys.platform == "win32":
                try:
                    ctypes.windll.user32.LockWorkStation()
                    locked = True
                except Exception as e:
                    locked = False
                    result["details"]["error"] = str(e)
            result["details"] = {
                "message": "Tactical Emergency Lockdown initiated.",
                "workstation_locked": locked
            }

        elif normalized_name in ["PROTOCOL_DIAGNOSTIC_REPORT", "DIAGNOSTICS", "STATUS"]:
            snap = self.get_telemetry()
            result["details"] = {
                "health_status": snap.health_status,
                "cpu_percent": snap.cpu_percent,
                "ram_percent": snap.ram_percent,
                "disk_percent": snap.disk_percent,
                "alerts": snap.active_alerts,
                "top_cpu": snap.top_cpu_processes[:3],
                "top_ram": snap.top_ram_processes[:3]
            }

        else:
            result["status"] = "FAILED"
            result["details"] = {"error": f"Unknown protocol: {protocol_name}"}

        return result
