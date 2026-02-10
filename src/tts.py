"""Hebrew Text-to-Speech using Google Cloud TTS."""

import io
import logging
import os
import re
import tempfile

from google.cloud import texttospeech
from pydub import AudioSegment

from .config import get_data_dir

logger = logging.getLogger(__name__)

# Audio cache directory
AUDIO_CACHE_DIR = get_data_dir() / "cache" / "audio"

# Google Cloud TTS byte limit is 5000 per request.
# Nikud'd Hebrew ≈ 4 bytes/char, so ~1200 chars stays safely under the limit.
MAX_CHUNK_CHARS = 1200

# Voice configuration
VOICE_NAME = "he-IL-Wavenet-D"  # Male, deep, clear
LANGUAGE_CODE = "he-IL"
SPEAKING_RATE = 1.0  # Telegram provides built-in 1x/1.5x/2x controls

# Silence between chunks (milliseconds)
INTER_CHUNK_SILENCE_MS = 300


class HebrewTTSClient:
    """Client for generating Hebrew audio using Google Cloud TTS."""

    def __init__(self, credentials_json: str | None = None):
        """Initialize Google Cloud TTS client.

        Args:
            credentials_json: Service account JSON string. If provided, written
                to a temp file and used for authentication. Falls back to
                default credentials (e.g. gcloud auth) if not provided.
        """
        self._temp_creds_path: str | None = None

        if credentials_json:
            # Write credentials to temp file for the Google client
            fd, path = tempfile.mkstemp(suffix=".json", prefix="gcloud_tts_")
            os.write(fd, credentials_json.encode())
            os.close(fd)
            self._temp_creds_path = path
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path

        self.client = texttospeech.TextToSpeechClient()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code=LANGUAGE_CODE,
            name=VOICE_NAME,
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.OGG_OPUS,
            speaking_rate=SPEAKING_RATE,
        )

    def __del__(self):
        """Clean up temp credentials file."""
        if self._temp_creds_path and os.path.exists(self._temp_creds_path):
            os.unlink(self._temp_creds_path)

    def get_or_generate_audio(self, text: str, cache_key: str) -> bytes | None:
        """Get audio from cache or generate it.

        Args:
            text: Hebrew text to synthesize.
            cache_key: Cache filename without extension (e.g. "audio_2026-02-10_1").

        Returns:
            OGG Opus audio bytes, or None on failure.
        """
        cache_path = AUDIO_CACHE_DIR / f"{cache_key}.ogg"
        if cache_path.exists():
            logger.info(f"Audio cache hit: {cache_key}")
            return cache_path.read_bytes()

        audio = self.synthesize_text(text)
        if audio:
            AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(audio)
            logger.info(f"Cached audio: {cache_key} ({len(audio)} bytes)")
        return audio

    def synthesize_text(self, text: str) -> bytes | None:
        """Synthesize Hebrew text to OGG Opus audio.

        Chunks long text, synthesizes each chunk, and concatenates
        with brief silence gaps for natural pacing.

        Returns:
            OGG Opus audio bytes, or None on failure.
        """
        try:
            chunks = chunk_text(text)
            logger.info(f"Synthesizing {len(chunks)} chunk(s), {len(text)} chars total")

            audio_chunks = []
            for i, chunk in enumerate(chunks):
                audio_bytes = self._synthesize_chunk(chunk)
                audio_chunks.append(audio_bytes)
                logger.debug(f"Chunk {i + 1}/{len(chunks)}: {len(audio_bytes)} bytes")

            if len(audio_chunks) == 1:
                return audio_chunks[0]

            return _concatenate_audio(audio_chunks)

        except Exception:
            logger.exception("TTS synthesis failed")
            return None

    def _synthesize_chunk(self, chunk: str) -> bytes:
        """Synthesize a single text chunk via Google Cloud TTS."""
        synthesis_input = texttospeech.SynthesisInput(text=chunk)
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=self.voice,
            audio_config=self.audio_config,
        )
        return response.audio_content


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split Hebrew text into chunks for TTS synthesis.

    Splits at sentence boundaries first (period, colon, sof-pasuk),
    then falls back to word boundaries.

    Args:
        text: Hebrew text to chunk.
        max_chars: Maximum characters per chunk.

    Returns:
        List of text chunks, each under max_chars.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    # Split at sentence boundaries: period, colon, or sof-pasuk (׃) followed by space
    sentence_pattern = re.compile(r"(?<=[.:׃])\s+")
    sentences = sentence_pattern.split(text)

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            # Current chunk is full — save it
            if current:
                chunks.append(current)
            # If this sentence itself exceeds the limit, split at word boundaries
            if len(sentence) > max_chars:
                words = sentence.split()
                current = ""
                for word in words:
                    candidate = f"{current} {word}".strip() if current else word
                    if len(candidate) <= max_chars:
                        current = candidate
                    else:
                        if current:
                            chunks.append(current)
                        current = word
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def _concatenate_audio(audio_chunks: list[bytes]) -> bytes:
    """Concatenate OGG Opus audio chunks with silence gaps.

    Args:
        audio_chunks: List of OGG Opus audio bytes.

    Returns:
        Single concatenated OGG Opus audio bytes.
    """
    silence = AudioSegment.silent(duration=INTER_CHUNK_SILENCE_MS)
    combined = AudioSegment.empty()

    for i, chunk_bytes in enumerate(audio_chunks):
        segment = AudioSegment.from_ogg(io.BytesIO(chunk_bytes))
        if i > 0:
            combined += silence
        combined += segment

    buf = io.BytesIO()
    combined.export(buf, format="ogg", codec="libopus")
    return buf.getvalue()
