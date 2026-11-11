"""Central settings. Every value can be overridden with an environment variable."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
WEB_DEMO_DIR = ROOT / "frontend" / "web_demo"
RESULTS_DIR = ROOT / "evaluation" / "results"
TUNED_WEIGHTS_PATH = ROOT / "backend" / "rules" / "weights_tuned.json"
CLASSIFIER_PATH = ROOT / "backend" / "models" / "sms_tfidf_lr.joblib"
ZH_CLASSIFIER_PATH = ROOT / "backend" / "models" / "zh_tfidf_lr.joblib"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
# qwen2.5:7b is the project choice. On a slow demo laptop set OLLAMA_MODEL=qwen2.5:3b.
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TIMEOUT_S = float(os.getenv("OLLAMA_TIMEOUT_S", "30"))
LLM_ENABLED = os.getenv("LLM_ENABLED", "1") == "1"

# Short-link expansion makes a network request, so it stays off unless asked for.
EXPAND_SHORT_URLS = os.getenv("EXPAND_SHORT_URLS", "0") == "1"
URL_EXPAND_TIMEOUT_S = 2.0

# Risk bands. A score at or above MEDIUM counts as "scam" for evaluation.
MEDIUM_THRESHOLD = 40
HIGH_THRESHOLD = 70

MAX_TEXT_CHARS = 5000
MAX_MESSAGE_CHARS = 2000  # /analyze limit agreed with the frontend (API_CONTRACT.md)
MAX_AUDIO_BYTES = 25 * 1024 * 1024
SESSION_TTL_S = 60 * 60
MAX_SESSIONS = 500
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
