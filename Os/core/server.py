"""
V.E.R.O.N.I.C.A. Tactical Web & WebSocket Server
Provides REST endpoints and real-time streaming telemetry for external dashboards and HUDs.
"""

from __future__ import annotations
import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from modules.veronica_guard import VeronicaGuard
from modules.os_controller import OSController
from core.brain import VeronicaBrain


class CommandRequest(BaseModel):
    prompt: str
    speak: bool = False


def create_app(brain: VeronicaBrain) -> FastAPI:
    app = FastAPI(title="V.E.R.O.N.I.C.A. Tactical Server", version="1.0.0")

    @app.get("/api/telemetry")
    async def get_telemetry():
        snap = brain.guard.get_telemetry()
        return {
            "timestamp": snap.timestamp,
            "health_status": snap.health_status,
            "cpu_percent": snap.cpu_percent,
            "cpu_cores": snap.cpu_cores_percent,
            "ram_percent": snap.ram_percent,
            "ram_used_gb": snap.ram_used_gb,
            "ram_total_gb": snap.ram_total_gb,
            "disk_percent": snap.disk_percent,
            "battery_percent": snap.battery_percent,
            "active_alerts": snap.active_alerts,
            "top_cpu_processes": snap.top_cpu_processes,
            "top_ram_processes": snap.top_ram_processes
        }

    @app.post("/api/command")
    async def run_command(req: CommandRequest):
        res = brain.process_query(req.prompt, speak_output=req.speak)
        return res

    @app.post("/api/contingency/{protocol_name}")
    async def run_contingency(protocol_name: str):
        res = brain.guard.execute_contingency(protocol_name)
        return res

    @app.websocket("/ws/telemetry")
    async def ws_telemetry(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                snap = brain.guard.get_telemetry()
                data = {
                    "timestamp": snap.timestamp,
                    "health_status": snap.health_status,
                    "cpu_percent": snap.cpu_percent,
                    "ram_percent": snap.ram_percent,
                    "disk_percent": snap.disk_percent,
                    "alerts": snap.active_alerts
                }
                await websocket.send_text(json.dumps(data))
                await asyncio.sleep(2.0)
        except WebSocketDisconnect:
            pass

    @app.get("/", response_class=HTMLResponse)
    async def get_hud():
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>V.E.R.O.N.I.C.A. Tactical HUD</title>
            <style>
                body { background: #050b14; color: #00f2ff; font-family: 'Consolas', 'Courier New', monospace; margin: 0; padding: 20px; }
                h1 { border-bottom: 2px solid #00f2ff; padding-bottom: 10px; text-shadow: 0 0 10px #00f2ff; }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 20px; }
                .card { background: rgba(0, 242, 255, 0.05); border: 1px solid #00f2ff; padding: 20px; border-radius: 8px; box-shadow: 0 0 15px rgba(0,242,255,0.1); }
                .metric { font-size: 2.2em; font-weight: bold; margin: 10px 0; color: #ffffff; }
                .status-optimal { color: #00ff66; text-shadow: 0 0 8px #00ff66; }
                .status-warning { color: #ffbb00; text-shadow: 0 0 8px #ffbb00; }
                .status-critical { color: #ff0044; text-shadow: 0 0 8px #ff0044; }
                .btn { background: transparent; border: 1px solid #00f2ff; color: #00f2ff; padding: 10px 15px; cursor: pointer; border-radius: 4px; font-weight: bold; margin-right: 10px; margin-top: 10px; transition: 0.2s; }
                .btn:hover { background: #00f2ff; color: #050b14; box-shadow: 0 0 15px #00f2ff; }
                #terminal-log { background: #02050a; border: 1px solid #005577; padding: 15px; height: 180px; overflow-y: auto; color: #88ccee; font-size: 0.9em; margin-top: 20px; border-radius: 6px; }
            </style>
        </head>
        <body>
            <h1>V.E.R.O.N.I.C.A. // TACTICAL ORCHESTRATOR</h1>
            <div class="grid">
                <div class="card">
                    <h3>SYSTEM STATUS</h3>
                    <div id="status" class="metric status-optimal">OPTIMAL</div>
                    <div id="alerts" style="color: #aaa;">SUBSYSTEMS NORMAL</div>
                </div>
                <div class="card">
                    <h3>CPU UTILIZATION</h3>
                    <div id="cpu" class="metric">-- %</div>
                </div>
                <div class="card">
                    <h3>RAM USAGE</h3>
                    <div id="ram" class="metric">-- %</div>
                </div>
                <div class="card">
                    <h3>PRIMARY STORAGE</h3>
                    <div id="disk" class="metric">-- %</div>
                </div>
            </div>

            <div class="card" style="margin-top: 20px;">
                <h3>CONTINGENCY PROTOCOLS</h3>
                <button class="btn" onclick="triggerContingency('PROTOCOL_PURGE_RAM')">PURGE RAM</button>
                <button class="btn" onclick="triggerContingency('PROTOCOL_COOL_DOWN')">COOL DOWN</button>
                <button class="btn" onclick="triggerContingency('PROTOCOL_LOCKDOWN')" style="border-color:#ff0044; color:#ff0044;">TACTICAL LOCKDOWN</button>
            </div>

            <div id="terminal-log">
                [SYSTEM] Veronica HUD initialized. Telemetry stream connected.
            </div>

            <script>
                const logEl = document.getElementById('terminal-log');
                function log(msg) {
                    const line = document.createElement('div');
                    line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
                    logEl.appendChild(line);
                    logEl.scrollTop = logEl.scrollHeight;
                }

                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws = new WebSocket(`${protocol}//${window.location.host}/ws/telemetry`);
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    document.getElementById('cpu').textContent = data.cpu_percent + ' %';
                    document.getElementById('ram').textContent = data.ram_percent + ' %';
                    document.getElementById('disk').textContent = data.disk_percent + ' %';
                    const statusEl = document.getElementById('status');
                    statusEl.textContent = data.health_status;
                    statusEl.className = 'metric ' + (data.health_status === 'OPTIMAL' ? 'status-optimal' : (data.health_status === 'CRITICAL' ? 'status-critical' : 'status-warning'));
                    if (data.alerts && data.alerts.length > 0) {
                        document.getElementById('alerts').textContent = data.alerts.join(' | ');
                    } else {
                        document.getElementById('alerts').textContent = 'SUBSYSTEMS NORMAL';
                    }
                };

                async function triggerContingency(protocolName) {
                    log(`Executing ${protocolName}...`);
                    const res = await fetch(`/api/contingency/${protocolName}`, { method: 'POST' });
                    const result = await res.json();
                    log(`Response: ${JSON.stringify(result.details)}`);
                }
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    return app
