"""Basic speech-to-text (P3). faster-whisper is optional, so the rest of the app runs without it."""
from __future__ import annotations

import os
import tempfile
from functools import lru_cache

from .config import WHISPER_MODEL


class SttUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _model():
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SttUnavailable("faster-whisper is not installed. See requirements-optional.txt.") from exc
    return WhisperModel(WHISPER_MODEL, device="auto", compute_type="auto")


def transcribe(audio: bytes, suffix: str = ".wav") -> str:
    handle, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(handle, "wb") as tmp:
            tmp.write(audio)
        segments, _ = _model().transcribe(path, vad_filter=True)
        return " ".join(s.text.strip() for s in segments).strip()
    finally:
        os.unlink(path)
