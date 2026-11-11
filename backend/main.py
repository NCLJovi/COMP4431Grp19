"""FastAPI app. Run with: python -m uvicorn backend.main:app --port 8000"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import classifier, dialogue, gym, llm, service, stt
from .config import LLM_ENABLED, MAX_AUDIO_BYTES, MAX_TEXT_CHARS, OLLAMA_MODEL, WEB_DEMO_DIR
from .pipeline import analyze
from .rules.engine import RULES_BY_ID
from .schemas import AnalyzeRequest, AnalyzeResponse, ChatRequest

app = FastAPI(title="Scam Checker API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?", allow_methods=["*"], allow_headers=["*"])


class GymStart(BaseModel):
    scenario: str = "bank"


class GymReply(BaseModel):
    session_id: str
    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "rules": len(RULES_BY_ID), "llm_enabled": LLM_ENABLED,
            "llm_model": OLLAMA_MODEL, "llm_ready": await llm.is_available(),
            "classifier_ready": classifier.is_ready(), "zh_classifier_ready": classifier.is_ready("zh")}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_message(request: AnalyzeRequest) -> AnalyzeResponse:
    """See docs/API_CONTRACT.md. Pass session_id to continue with /chat."""
    try:
        return await service.check_message(request.message, request.session_id)
    except service.InvalidMessage as error:
        raise HTTPException(400, str(error)) from error


@app.post("/chat", response_model=AnalyzeResponse)
async def chat_turn(request: ChatRequest) -> AnalyzeResponse:
    """Conversation entry point: handles new messages and follow-up answers."""
    return await dialogue.chat(dialogue.get_session(request.session_id), request.message, use_llm=request.use_llm)


@app.post("/analyze-audio", response_model=AnalyzeResponse)
async def analyze_audio(file: UploadFile = File(...), session_id: str | None = None) -> AnalyzeResponse:
    audio = await file.read(MAX_AUDIO_BYTES + 1)
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "Audio file is too large (limit 25 MB).")
    try:
        transcript = await run_in_threadpool(stt.transcribe, audio, Path(file.filename or "a.wav").suffix or ".wav")
    except stt.SttUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    if not transcript:
        raise HTTPException(422, "No speech was found in the recording.")
    response = await dialogue.analyze_new(dialogue.get_session(session_id), transcript[:MAX_TEXT_CHARS])
    response.transcript = transcript
    return response


@app.post("/mock/analyze", response_model=AnalyzeResponse)
async def mock_analyze() -> AnalyzeResponse:
    """Fixed response so that the UI can be built without the engine or Ollama."""
    return AnalyzeResponse(
        risk_score=87, risk_level="high",
        triggered_rules=[{"id": "R1", "name": "Urgency", "span": [12, 20]}],
        url_findings=[{"url": "hsbc-hk-secure.example", "issue": "lookalike", "target": "hsbc.com.hk"}],
        similar_cases=[{"title": "Fake bank alert", "similarity": 0.87, "source": "mock"}],
        explanation="Mock response.", next_question="Did they ask for your OTP?", session_id="mock",
    )


@app.post("/gym/start")
async def gym_start(request: GymStart) -> dict:
    try:
        return gym.start(request.scenario)
    except KeyError as exc:
        raise HTTPException(404, "Unknown scenario.") from exc


@app.post("/gym/reply")
async def gym_reply(request: GymReply) -> dict:
    try:
        return gym.reply(request.session_id, request.text)
    except KeyError as exc:
        raise HTTPException(404, "Training session not found.") from exc


# Registered last so that it does not shadow the API routes.
app.mount("/", StaticFiles(directory=WEB_DEMO_DIR, html=True), name="web_demo")
