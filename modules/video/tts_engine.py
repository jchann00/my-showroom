import os
import io
import asyncio
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import edge_tts
from config.settings import BASE_DIR, load_config
from database.db import save_log


class TTSEngine:
    """Multi-provider TTS Engine supporting Edge-TTS neural voices & ElevenLabs Voice Cloning."""

    def __init__(self):
        self.reload_config()

    def reload_config(self):
        cfg = load_config()
        self.tts_cfg = cfg.get("tts", {})
        self.provider = self.tts_cfg.get("provider", "edge_tts")  # 'edge_tts' or 'elevenlabs'
        self.edge_voice = self.tts_cfg.get("edge_voice", "ko-KR-InJoonNeural")  # InJoon (warm male) by default
        self.speed = self.tts_cfg.get("speed", "+15%")  # 1.15x tempo for high retention
        
        # ElevenLabs settings (for user sample voice cloning)
        self.elevenlabs_key = self.tts_cfg.get("elevenlabs_api_key", "").strip()
        self.elevenlabs_voice_id = self.tts_cfg.get("elevenlabs_voice_id", "").strip()

    def generate_audio(self, text: str, output_path: str) -> bool:
        """Generates voiceover MP3 using ElevenLabs voice cloning or Edge-TTS."""
        self.reload_config()

        # 1. Try ElevenLabs Voice Cloning if configured
        if self.provider == "elevenlabs" and self.elevenlabs_key and self.elevenlabs_voice_id:
            try:
                success = self._generate_elevenlabs(text, output_path)
                if success:
                    save_log("INFO", "tts", f"Voiceover generated via ElevenLabs Cloned Voice ({self.elevenlabs_voice_id})")
                    return True
            except Exception as e:
                save_log("WARNING", "tts", f"ElevenLabs voice cloning failed, falling back to Edge-TTS: {e}")

        # 2. Edge-TTS Neural Voice
        return self._generate_edge_tts(text, output_path)

    def _generate_elevenlabs(self, text: str, output_path: str) -> bool:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
        headers = {
            "xi-api-key": self.elevenlabs_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.85
            }
        }
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        if res.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(res.content)
            return True
        else:
            raise RuntimeError(f"ElevenLabs API Error {res.status_code}: {res.text[:200]}")

    def _generate_edge_tts(self, text: str, output_path: str) -> bool:
        """Generates voiceover using Edge TTS with speed adjustment."""
        async def _speak():
            comm = edge_tts.Communicate(text, self.edge_voice, rate=self.speed)
            await comm.save(output_path)

        # Run safely across sync or active event loops
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(asyncio.run, _speak()).result()
        else:
            asyncio.run(_speak())

        save_log("INFO", "tts", f"Voiceover generated via Edge-TTS [{self.edge_voice}] (rate: {self.speed})")
        return True
