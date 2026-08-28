"""
V.E.R.O.N.I.C.A. - Tactical AI Assistant & System Orchestrator
Main entry point featuring Rich-based Stark Terminal HUD and interactive CLI.
"""

from __future__ import annotations
import os
import sys
import time
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt

from modules.veronica_guard import VeronicaGuard
from modules.os_controller import OSController
from core.memory import MemoryStore
from core.voice import VoiceEngine
from core.brain import VeronicaBrain


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Loads configuration from YAML file or defaults."""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def render_dashboard(guard: VeronicaGuard, controller: OSController) -> Panel:
    """Renders a Rich terminal HUD displaying current hardware telemetry and status."""
    snap = guard.get_telemetry()
    sys_info = controller.get_system_info()

    # Telemetry Table
    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Subsystem", style="bold white")
    table.add_column("Metric", style="cyan")
    table.add_column("Status", justify="right")

    # Status color
    status_style = "bold green" if snap.health_status == "OPTIMAL" else ("bold red" if snap.health_status == "CRITICAL" else "bold yellow")
    table.add_row("OVERALL HEALTH", snap.health_status, f"[{status_style}]●[/{status_style}]")

    cpu_color = "red" if snap.cpu_percent > 90 else ("yellow" if snap.cpu_percent > 75 else "green")
    table.add_row("CPU Load", f"{snap.cpu_percent}%", f"[{cpu_color}]{snap.cpu_percent:.1f}%[/{cpu_color}]")

    ram_color = "red" if snap.ram_percent > 90 else ("yellow" if snap.ram_percent > 75 else "green")
    table.add_row("RAM Utilization", f"{snap.ram_used_gb} / {snap.ram_total_gb} GB", f"[{ram_color}]{snap.ram_percent:.1f}%[/{ram_color}]")

    disk_color = "red" if snap.disk_percent > 90 else ("yellow" if snap.disk_percent > 75 else "green")
    table.add_row("Primary Storage", f"{snap.disk_used_gb} / {snap.disk_total_gb} GB", f"[{disk_color}]{snap.disk_percent:.1f}%[/{disk_color}]")

    table.add_row("Node & Uptime", f"{sys_info['hostname']} (IP: {sys_info['local_ip']})", sys_info['uptime'])

    alerts_text = f"[bold red]{' | '.join(snap.active_alerts)}[/bold red]" if snap.active_alerts else "[dim green]ALL SYSTEMS NOMINAL[/dim green]"
    
    top_proc_text = ""
    if snap.top_cpu_processes:
        top_proc_text = "\n[bold cyan]Top Active Processes:[/bold cyan] " + ", ".join([f"{p['name']} ({p.get('cpu_percent', 0):.1f}%)" for p in snap.top_cpu_processes[:3]])

    content = table
    footer = f"\n[bold]Alerts:[/bold] {alerts_text}{top_proc_text}"

    return Panel(
        content,
        title="[bold cyan]⚡ V.E.R.O.N.I.C.A. TACTICAL HUD ⚡[/bold cyan]",
        subtitle="[dim]Stark Operating System Subsystem v1.0.0[/dim]",
        border_style="cyan"
    )


def run_interactive_cli(brain: VeronicaBrain, console: Console, voice_enabled: bool = True):
    """Runs the interactive command loop."""
    console.print(render_dashboard(brain.guard, brain.controller))
    console.print("\n[bold green]VERONICA is online.[/bold green] Type a command (e.g. [cyan]'status'[/cyan], [cyan]'purge ram'[/cyan], [cyan]'launch notepad'[/cyan], [cyan]'system info'[/cyan], [cyan]'exit'[/cyan]):\n")

    # Initial greeting voice
    if voice_enabled:
        brain.voice.speak("Veronica online and standing by.", block=False)

    while True:
        try:
            prompt_input = Prompt.ask("[bold cyan]Veronica[/bold cyan] [bold white]>[/bold white]").strip()
            if not prompt_input:
                continue
            if prompt_input.lower() in ["exit", "quit", "shutdown", "q"]:
                console.print("[yellow]Shutting down VERONICA subsystems. Goodbye, Boss.[/yellow]")
                if voice_enabled:
                    brain.voice.speak("Standing down. Subsystems offline.", block=True)
                break

            response = brain.process_query(prompt_input, speak_output=voice_enabled)
            console.print(f"[bold green]>[/bold green] {response['text']}\n")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Session interrupted. Standing down.[/yellow]")
            break


def main():
    parser = argparse.ArgumentParser(description="V.E.R.O.N.I.C.A. Tactical Assistant & Telemetry Orchestrator")
    parser.add_argument("--cli", action="store_true", help="Launch in interactive CLI mode")
    parser.add_argument("--server", action="store_true", help="Launch FastAPI / WebSocket Telemetry Server")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--exec", type=str, default=None, help="Execute a single tactical command and exit")
    parser.add_argument("--no-voice", action="store_true", help="Disable text-to-speech output")
    args = parser.parse_args()

    config = load_config()
    console = Console()

    guard = VeronicaGuard(config)
    controller = OSController(config)
    memory = MemoryStore()
    voice = VoiceEngine(config)
    if args.no_voice:
        voice.enabled = False

    brain = VeronicaBrain(guard, controller, memory, voice, config)

    if args.exec:
        res = brain.process_query(args.exec, speak_output=not args.no_voice)
        console.print(res["text"])
        return

    if args.server:
        import uvicorn
        from core.server import create_app
        app = create_app(brain)
        console.print(f"[bold cyan]Launching V.E.R.O.N.I.C.A. Tactical Web Server on http://127.0.0.1:{args.port}[/bold cyan]")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
        return

    # Default: Interactive CLI with Stark HUD
    run_interactive_cli(brain, console, voice_enabled=not args.no_voice)


if __name__ == "__main__":
    main()
