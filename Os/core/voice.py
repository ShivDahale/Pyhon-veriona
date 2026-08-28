"""
V.E.R.O.N.I.C.A. Voice & Neural TTS Synthesizer
Provides natural speech output using edge-tts and system audio playback.
"""

from __future__ import annotations
import os
import sys
import asyncio
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import edge_tts


class VoiceEngine:
    """Asynchronous Neural Text-to-Speech Engine."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        voice_cfg = self.config.get("voice", {})
        self.enabled = voice_cfg.get("enabled", True)
        self.voice_name = voice_cfg.get("voice_name", "en-GB-SoniaNeural")
        self.rate = voice_cfg.get("rate", "+0%")
        self.volume = voice_cfg.get("volume", "+0%")
        self.pitch = voice_cfg.get("pitch", "+0Hz")
        self.temp_dir = Path(tempfile.gettempdir()) / "veronica_audio"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def generate_speech_file(self, text: str, output_path: Optional[str] = None) -> Optional[str]:
        """Synthesizes text into an MP3 file using edge-tts."""
        if not self.enabled or not text.strip():
            return None

        clean_text = text.replace("*", "").replace("#", "").replace("`", "").strip()
        if not clean_text:
            return None

        if not output_path:
            output_path = str(self.temp_dir / f"speech_{abs(hash(clean_text)) % 100000}.mp3")

        try:
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=self.voice_name,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch
            )
            await communicate.save(output_path)
            return output_path
        except Exception as e:
            # TTS generation error (e.g. offline or network blip)
            return None

    def play_audio_file(self, audio_path: str, block: bool = True):
        """Plays an audio file on Windows or cross-platform."""
        if not os.path.exists(audio_path):
            return

        try:
            if sys.platform == "win32":
                # PowerShell Media.MediaPlayer for mp3 playback
                escaped_path = audio_path.replace("'", "''")
                cmd = [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    f"Add-Type -AssemblyName presentationCore; "
                    f"$mediaPlayer = New-Object system.windows.media.mediaplayer; "
                    f"$mediaPlayer.open('{escaped_path}'); "
                    f"$mediaPlayer.Play(); "
                    f"Start-Sleep -Milliseconds 200; "
                    f"while($mediaPlayer.NaturalDuration.HasTimeSpan -and ($mediaPlayer.Position -lt $mediaPlayer.NaturalDuration.TimeSpan)) {{ Start-Sleep -Milliseconds 100 }}; "
                    f"$mediaPlayer.Close()"
                ]
                if block:
                    subprocess.run(cmd, capture_output=True, timeout=30)
                else:
                    subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                # Fallback on Linux/Mac (ffplay, aplay, etc.)
                subprocess.Popen(["ffplay", "-nodisp", "-autoexit", audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    async def speak_async(self, text: str, block: bool = True):
        """Synthesizes and immediately plays speech."""
        audio_file = await self.generate_speech_file(text)
        if audio_file and os.path.exists(audio_file):
            self.play_audio_file(audio_file, block=block)

    def speak(self, text: str, block: bool = True):
        """Synchronous wrapper for speak_async."""
        if not self.enabled:
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.speak_async(text, block=block))
            else:
                loop.run_until_complete(self.speak_async(text, block=block))
        except RuntimeError:
            asyncio.run(self.speak_async(text, block=block))
        except Exception:
            pass
