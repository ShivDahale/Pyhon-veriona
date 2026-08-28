"""
V.E.R.O.N.I.C.A. OS Controller & Automation Module
Provides safe, automated system control, application orchestration, process management, and shell execution.
"""

from __future__ import annotations
import os
import sys
import subprocess
import socket
import platform
import time
import shutil
import ctypes
from typing import Dict, Any, List, Optional
import psutil


class OSController:
    """Tactical OS automation controller for Windows and cross-platform environments."""

    BLOCKED_PATTERNS = [
        "format ",
        "rmdir /s /q c:",
        "del /f /s /q c:",
        "rd /s /q c:",
        ":(){ :|:& };:",
        "drop database",
        "mkfs"
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        os_cfg = self.config.get("os_controller", {})
        self.safe_mode = os_cfg.get("safe_mode", True)
        self.timeout = os_cfg.get("execution_timeout_sec", 15)
        self.shortcuts = os_cfg.get("allowed_app_shortcuts", {
            "browser": "https://www.google.com",
            "terminal": "cmd.exe",
            "powershell": "powershell.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe",
            "taskmanager": "taskmgr.exe",
            "vscode": "code"
        })

    def launch_app(self, target: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Launches an application or URL shortcut."""
        target_lower = target.lower().strip()
        cmd_target = self.shortcuts.get(target_lower, target)
        args = args or []

        try:
            if cmd_target.startswith("http://") or cmd_target.startswith("https://"):
                import webbrowser
                webbrowser.open(cmd_target)
                return {
                    "status": "SUCCESS",
                    "action": "open_url",
                    "target": cmd_target,
                    "message": f"Opened URL {cmd_target} in default browser."
                }
            else:
                full_cmd = [cmd_target] + args
                # Spawn in background detached
                if sys.platform == "win32":
                    subprocess.Popen(
                        full_cmd,
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                        shell=False
                    )
                else:
                    subprocess.Popen(full_cmd, start_new_session=True)

                return {
                    "status": "SUCCESS",
                    "action": "launch_process",
                    "target": cmd_target,
                    "message": f"Launched application: {cmd_target}"
                }
        except Exception as e:
            return {
                "status": "FAILED",
                "action": "launch_app",
                "target": target,
                "error": str(e)
            }

    def list_processes(self, filter_name: Optional[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
        """Lists active processes with resource usage metrics."""
        results = []
        filter_lower = filter_name.lower() if filter_name else None

        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = p.info
                p_name = info.get('name') or ""
                if filter_lower and filter_lower not in p_name.lower():
                    continue
                results.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        results = sorted(results, key=lambda x: x.get('memory_percent') or 0, reverse=True)
        return results[:limit]

    def terminate_process(self, pid: Optional[int] = None, process_name: Optional[str] = None) -> Dict[str, Any]:
        """Safely terminates a process by PID or process name."""
        terminated = []
        errors = []

        if pid:
            try:
                p = psutil.Process(pid)
                name = p.name()
                p.terminate()
                terminated.append({"pid": pid, "name": name})
            except Exception as e:
                errors.append(f"PID {pid}: {str(e)}")

        elif process_name:
            target_name = process_name.lower()
            for p in psutil.process_iter(['pid', 'name']):
                try:
                    if p.info['name'] and target_name in p.info['name'].lower():
                        p_pid = p.info['pid']
                        proc = psutil.Process(p_pid)
                        proc.terminate()
                        terminated.append({"pid": p_pid, "name": p.info['name']})
                except Exception as e:
                    errors.append(f"{p.info.get('name')}: {str(e)}")

        return {
            "status": "SUCCESS" if terminated else "FAILED",
            "terminated_count": len(terminated),
            "terminated": terminated,
            "errors": errors
        }

    def execute_command(self, command: str) -> Dict[str, Any]:
        """Safely executes a shell or PowerShell command with output capture and timeout."""
        cmd_lower = command.lower()
        if self.safe_mode:
            for pattern in self.BLOCKED_PATTERNS:
                if pattern in cmd_lower:
                    return {
                        "status": "BLOCKED",
                        "command": command,
                        "error": f"Security violation: Command contains restricted pattern '{pattern}'"
                    }

        start_time = time.time()
        try:
            if sys.platform == "win32":
                # Run via powershell.exe
                shell_cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command]
            else:
                shell_cmd = ["/bin/bash", "-c", command]

            proc = subprocess.run(
                shell_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            duration = round(time.time() - start_time, 3)

            return {
                "status": "SUCCESS" if proc.returncode == 0 else "ERROR",
                "returncode": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
                "duration_sec": duration
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "command": command,
                "error": f"Command timed out after {self.timeout} seconds."
            }
        except Exception as e:
            return {
                "status": "FAILED",
                "command": command,
                "error": str(e)
            }

    def get_system_info(self) -> Dict[str, Any]:
        """Retrieves comprehensive system, network, and OS environment information."""
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"

        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return {
            "hostname": hostname,
            "os_name": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version.split()[0],
            "uptime": f"{hours}h {minutes}m {seconds}s",
            "uptime_seconds": uptime_seconds,
            "local_ip": local_ip
        }

    def lock_workstation(self) -> Dict[str, Any]:
        """Locks the current Windows workstation."""
        if sys.platform == "win32":
            try:
                ctypes.windll.user32.LockWorkStation()
                return {"status": "SUCCESS", "message": "Workstation locked successfully."}
            except Exception as e:
                return {"status": "FAILED", "error": str(e)}
        return {"status": "UNSUPPORTED", "message": "Lock workstation only supported on Windows."}
