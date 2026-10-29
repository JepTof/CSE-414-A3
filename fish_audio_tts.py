import hashlib
import http.client
import json
import os
import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
VOICE_CHARACTERS = ("Kevin", "Bob", "Stuart", "Evil Kevin", "Evil Bob", "Evil Stuart")
VOICE_ID_KEY = "FISH_AUDIO_VOICE_ID"
FISH_AUDIO_HOST = "api.fish.audio"
CACHE_DIR = Path.home() / "Library" / "Caches" / "CSE415FishAudio"


class FishAudioError(RuntimeError):
    """A configuration, generation, or playback error from Fish Audio."""


def _read_settings():
    settings = {}
    env_file = PROJECT_DIR / ".env"
    if env_file.is_file():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                value = value.strip().strip("\"'")
                settings[key.strip()] = value
        except OSError as error:
            raise FishAudioError(f"Could not read {env_file}: {error}") from error

    settings.update(os.environ)
    return settings


class FishAudioTTS:
    """Generate and play a line using a configured Fish Audio voice model."""

    def __init__(self):
        settings = _read_settings()
        self.api_key = settings.get("FISH_API_KEY", "").strip()
        self.model = settings.get("FISH_AUDIO_TTS_MODEL", "s2.1-pro-free").strip()
        self.voice_id = settings.get(VOICE_ID_KEY, "").strip()
        if not self.api_key:
            raise FishAudioError(
                "FISH_API_KEY is missing from the environment or project .env."
            )
        if not self.model:
            raise FishAudioError("FISH_AUDIO_TTS_MODEL must not be empty.")
        if not self.voice_id:
            raise FishAudioError(
                f"{VOICE_ID_KEY} is missing from the project .env."
            )
        self._connection = None

    def speak(self, character, text):
        if character not in VOICE_CHARACTERS:
            raise FishAudioError(f"No Fish Audio voice mapping for {character!r}.")
        if not text or not text.strip():
            return

        cache_key = hashlib.sha256(
            f"{self.model}\0{self.voice_id}\0{text}".encode("utf-8")
        ).hexdigest()
        audio_path = CACHE_DIR / f"{cache_key}.mp3"
        if not audio_path.is_file():
            self._generate_audio(text, audio_path)

        try:
            subprocess.run(["afplay", str(audio_path)], check=True)
        except FileNotFoundError as error:
            raise FishAudioError(
                "Audio playback requires macOS afplay."
            ) from error
        except subprocess.CalledProcessError as error:
            raise FishAudioError(
                f"Audio playback failed with exit code {error.returncode}."
            ) from error

    def _generate_audio(self, text, audio_path):
        payload = json.dumps({
            "text": text,
            "reference_id": self.voice_id,
            "format": "mp3",
            "latency": "balanced",
            "chunk_length": 100,
            "mp3_bitrate": 64,
            "prosody": {"speed": 1.15},
        })
        try:
            if self._connection is None:
                self._connection = http.client.HTTPSConnection(
                    FISH_AUDIO_HOST, timeout=60
                )
            self._connection.request(
                "POST",
                "/v1/tts",
                body=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "model": self.model,
                },
            )
            response = self._connection.getresponse()
            audio_data = response.read()
        except (OSError, http.client.HTTPException) as error:
            self._close_connection()
            raise FishAudioError(
                f"Could not generate speech with Fish Audio: {error}"
            ) from error

        if response.status < 200 or response.status >= 300:
            message = audio_data[:500].decode("utf-8", errors="replace")
            self._close_connection()
            raise FishAudioError(
                f"Fish Audio returned HTTP {response.status}: {message}"
            )
        if not audio_data:
            raise FishAudioError("Fish Audio returned an empty audio response.")

        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            temporary_path = audio_path.with_suffix(".tmp")
            temporary_path.write_bytes(audio_data)
            temporary_path.replace(audio_path)
        except OSError as error:
            raise FishAudioError(
                f"Could not save generated audio cache: {error}"
            ) from error

    def _close_connection(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None
