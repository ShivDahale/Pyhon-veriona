# ⚡ V.E.R.O.N.I.C.A. (Visual & Electronic Resource Orchestration Network for Intelligent Control & Automation)

An advanced AI assistant, system orchestrator, and telemetry guard inspired by Tony Stark's contingency deployment and defense platform.

---

## 🌟 Features

- **🛡️ Real-Time Telemetry & Health Monitoring (`VeronicaGuard`)**:
  - Live CPU per core, RAM, primary storage, and battery metrics.
  - Automatic bottleneck detection, thermal monitoring, and health status grading (`OPTIMAL`, `ELEVATED`, `CRITICAL`).
- **🚨 Tactical Contingency Protocols**:
  - `PROTOCOL_PURGE_RAM`: Force garbage collection, release cached memory, and isolate memory hogs.
  - `PROTOCOL_COOL_DOWN`: Identify runaway tasks and analyze CPU throttling.
  - `PROTOCOL_LOCKDOWN`: Emergency workstation lock and audit snapshot generation.
  - `PROTOCOL_DIAGNOSTIC_REPORT`: Full tactical hardware report.
- **💻 OS Automation & Safety Controller (`OSController`)**:
  - Launch applications (browser, notepad, calculator, terminal, powershell, custom apps).
  - List and inspect running processes with resource usage.
  - Safely terminate processes by PID or name.
  - Execute PowerShell and system commands with safety guardrails blocking destructive commands.
- **🧠 Hybrid AI Brain (`VeronicaBrain`)**:
  - Dual-engine architecture: Online LLM tool-calling (Gemini / OpenAI) with an intelligent Offline Tactical NLP fallback engine that operates with zero latency and no external API keys required.
- **🎙️ Neural Speech (`VoiceEngine`)**:
  - Asynchronous natural voice synthesis using `edge-tts` (`en-GB-SoniaNeural`, `en-US-GuyNeural`, etc.).
- **📊 Stark Terminal HUD & Web Dashboard**:
  - Interactive Rich terminal HUD with live gauge meters.
  - Built-in FastAPI and WebSocket server for remote web dashboards.

---

## 🚀 Quick Start

### 1. Interactive CLI & Stark HUD
Launch the interactive terminal dashboard:
```powershell
python main.py
```

### 2. Silent Mode (Text Only)
Run without audio synthesis:
```powershell
python main.py --no-voice
```

### 3. One-Shot Tactical Execution
Execute an immediate tactical command and exit:
```powershell
python main.py --exec "system check"
python main.py --exec "purge ram"
python main.py --exec "launch notepad"
python main.py --exec "system info"
```

### 4. Launch Web HUD & Telemetry Server
Start the local FastAPI & WebSocket streaming server:
```powershell
python main.py --server --port 8000
```
Open `http://127.0.0.1:8000` in your browser to view the live web dashboard.

---

## 🛠️ Configuration (`config.yaml`)

Edit `config.yaml` to adjust thresholds, select voices, or configure API keys:

```yaml
telemetry:
  thresholds:
    cpu_warning_pct: 80.0
    cpu_critical_pct: 95.0
    ram_warning_pct: 85.0
    ram_critical_pct: 95.0

voice:
  enabled: true
  voice_name: "en-GB-SoniaNeural" # Options: en-US-GuyNeural, en-GB-RyanNeural, en-US-AriaNeural

os_controller:
  safe_mode: true
  execution_timeout_sec: 15
```

---

## 🧪 Running Tests

Run the complete test suite:
```powershell
python -m unittest discover -s tests -p "test_*.py"
```
