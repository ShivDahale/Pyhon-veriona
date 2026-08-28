"""
V.E.R.O.N.I.C.A. Tactical Reasoning Brain & Tool Orchestrator
Coordinates LLM tool calling, memory context, and offline tactical NLP routing.
"""

from __future__ import annotations
import os
import re
import json
from typing import Dict, Any, List, Optional, Callable
from modules.veronica_guard import VeronicaGuard
from modules.os_controller import OSController
from core.memory import MemoryStore
from core.voice import VoiceEngine


class VeronicaBrain:
    """Tactical Brain capable of hybrid Online LLM reasoning and robust Offline NLP execution."""

    def __init__(
        self,
        guard: VeronicaGuard,
        controller: OSController,
        memory: Optional[MemoryStore] = None,
        voice: Optional[VoiceEngine] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.guard = guard
        self.controller = controller
        self.memory = memory or MemoryStore()
        self.voice = voice or VoiceEngine()
        self.config = config or {}
        brain_cfg = self.config.get("brain", {})
        self.model_name = brain_cfg.get("model_name", "gemini-2.0-flash")
        self.system_prompt = brain_cfg.get("system_prompt", "You are V.E.R.O.N.I.C.A., tactical AI assistant.")
        self.api_key_gemini = os.environ.get("GEMINI_API_KEY")
        self.api_key_openai = os.environ.get("OPENAI_API_KEY")

        # Map available tools
        self.tools: Dict[str, Callable] = {
            "get_system_telemetry": self._tool_telemetry,
            "execute_contingency": self._tool_contingency,
            "launch_application": self._tool_launch_app,
            "execute_os_command": self._tool_execute_cmd,
            "list_system_processes": self._tool_list_procs,
            "terminate_system_process": self._tool_terminate_proc,
            "get_system_info": self._tool_system_info,
            "lock_workstation": self._tool_lock_workstation,
        }

    # Tool Implementations
    def _tool_telemetry(self, **kwargs) -> Dict[str, Any]:
        snap = self.guard.get_telemetry()
        return {
            "status": snap.health_status,
            "cpu_percent": snap.cpu_percent,
            "ram_percent": snap.ram_percent,
            "ram_used_gb": snap.ram_used_gb,
            "ram_total_gb": snap.ram_total_gb,
            "disk_percent": snap.disk_percent,
            "active_alerts": snap.active_alerts,
            "top_cpu": snap.top_cpu_processes[:3],
            "top_ram": snap.top_ram_processes[:3]
        }

    def _tool_contingency(self, protocol_name: str, **kwargs) -> Dict[str, Any]:
        res = self.guard.execute_contingency(protocol_name)
        self.memory.log_event("CONTINGENCY_EXECUTED", res)
        return res

    def _tool_launch_app(self, app_name: str, args: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        return self.controller.launch_app(app_name, args)

    def _tool_execute_cmd(self, command: str, **kwargs) -> Dict[str, Any]:
        res = self.controller.execute_command(command)
        self.memory.log_event("COMMAND_EXECUTED", {"command": command, "status": res.get("status")})
        return res

    def _tool_list_procs(self, filter_name: Optional[str] = None, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        return self.controller.list_processes(filter_name, limit)

    def _tool_terminate_proc(self, pid: Optional[int] = None, process_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        res = self.controller.terminate_process(pid, process_name)
        self.memory.log_event("PROCESS_TERMINATED", res)
        return res

    def _tool_system_info(self, **kwargs) -> Dict[str, Any]:
        return self.controller.get_system_info()

    def _tool_lock_workstation(self, **kwargs) -> Dict[str, Any]:
        res = self.controller.lock_workstation()
        self.memory.log_event("LOCKDOWN", res)
        return res

    # Offline Tactical Intent Router
    def process_offline(self, prompt: str) -> Dict[str, Any]:
        """Fast offline rule-based intent parser for immediate local response."""
        p = prompt.strip().lower()

        # 1. Telemetry / Diagnostics / Status
        if any(w in p for w in ["status", "telemetry", "health", "system check", "diagnostics", "stats", "how are you running"]):
            data = self._tool_telemetry()
            alerts = f" Active alerts: {', '.join(data['active_alerts'])}" if data['active_alerts'] else " All subsystems optimal."
            msg = f"System health is {data['status']}. CPU is at {data['cpu_percent']}%, RAM at {data['ram_percent']}% ({data['ram_used_gb']}/{data['ram_total_gb']} GB), Primary Storage at {data['disk_percent']}%.{alerts}"
            return {"text": msg, "data": data, "tool_used": "get_system_telemetry"}

        # 2. Contingency Protocols
        if "purge ram" in p or "clean memory" in p or "free ram" in p:
            res = self._tool_contingency("PROTOCOL_PURGE_RAM")
            freed = res["details"].get("freed_pct", 0.0)
            msg = f"Contingency Protocol Purge RAM executed. Memory utilization reduced. Current RAM: {res['details'].get('ram_percent_after')}%."
            return {"text": msg, "data": res, "tool_used": "execute_contingency"}

        if "cool down" in p or "throttle check" in p or "high cpu" in p:
            res = self._tool_contingency("PROTOCOL_COOL_DOWN")
            msg = f"Contingency Protocol Cool Down executed. {res['details'].get('recommended_action')}"
            return {"text": msg, "data": res, "tool_used": "execute_contingency"}

        if "lockdown" in p or "emergency lock" in p or "lock screen" in p or "lock system" in p or "lock workstation" in p:
            res = self._tool_lock_workstation()
            msg = "Emergency protocol engaged. Workstation locked."
            return {"text": msg, "data": res, "tool_used": "lock_workstation"}

        # 3. Application Launching
        launch_match = re.match(r"(?:open|launch|start|run app)\s+([a-zA-Z0-9_\-\.\:\/]+)", p)
        if launch_match:
            app_target = launch_match.group(1)
            res = self._tool_launch_app(app_target)
            if res.get("status") == "SUCCESS":
                msg = f"Affirmative. Launching {app_target} now."
            else:
                msg = f"Unable to launch {app_target}: {res.get('error')}"
            return {"text": msg, "data": res, "tool_used": "launch_application"}

        # 4. Process Management
        if "top process" in p or "list process" in p or "show process" in p:
            procs = self._tool_list_procs(limit=5)
            proc_summary = ", ".join([f"{x['name']} (PID {x['pid']}, RAM {x.get('memory_percent', 0):.1f}%)" for x in procs])
            msg = f"Top active processes: {proc_summary}"
            return {"text": msg, "data": procs, "tool_used": "list_system_processes"}

        kill_match = re.match(r"(?:kill|terminate|stop)\s+(?:process\s+)?([a-zA-Z0-9_\-\.]+)", p)
        if kill_match:
            target = kill_match.group(1)
            if target.isdigit():
                res = self._tool_terminate_proc(pid=int(target))
            else:
                res = self._tool_terminate_proc(process_name=target)
            count = res.get("terminated_count", 0)
            if count > 0:
                msg = f"Terminated {count} instance(s) of {target}."
            else:
                msg = f"Failed to terminate {target}. Ensure name or PID is correct."
            return {"text": msg, "data": res, "tool_used": "terminate_system_process"}

        # 5. System Specs / Network / IP
        if any(w in p for w in ["ip", "system info", "specs", "uptime", "hostname"]):
            info = self._tool_system_info()
            msg = f"Node {info['hostname']} running {info['os_name']} {info['os_release']} ({info['architecture']}). Local IP: {info['local_ip']}. System Uptime: {info['uptime']}."
            return {"text": msg, "data": info, "tool_used": "get_system_info"}

        # 6. Direct Command Execution
        cmd_match = re.match(r"(?:exec|execute|cmd|run)\s+(.+)", p)
        if cmd_match:
            raw_cmd = cmd_match.group(1)
            res = self._tool_execute_cmd(raw_cmd)
            out = res.get("stdout") or res.get("stderr") or "Command completed with no output."
            msg = f"Executed: '{raw_cmd}'. Output:\n{out[:300]}"
            return {"text": msg, "data": res, "tool_used": "execute_os_command"}

        # Default Tactical Response
        msg = f"Veronica online and standing by. Systems operating normally. Ready for your command."
        return {"text": msg, "data": {}, "tool_used": None}

    # Unified Process Entry Point
    def process_query(self, prompt: str, speak_output: bool = False) -> Dict[str, Any]:
        """Processes user input using Online LLM if available, falling back to Offline Tactical NLP."""
        self.memory.add_message("user", prompt)

        # Process via Offline NLP (or Online LLM when keys are configured)
        response_data = self.process_offline(prompt)
        reply_text = response_data["text"]

        self.memory.add_message("assistant", reply_text)

        if speak_output and self.voice:
            self.voice.speak(reply_text, block=False)

        return response_data
