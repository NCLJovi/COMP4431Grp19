"""API contract (CLAUDE.md section 6). The extra fields are additive, so the agreed keys stay valid."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, Field

from .config import MAX_TEXT_CHARS


class AnalyzeRequest(BaseModel):
    # Length is checked in the endpoint because the frontend contract needs 400, not 422.
    message: str = Field(default="", validation_alias=AliasChoices("message", "text"))
    session_id: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)
    session_id: Optional[str] = None
    use_llm: bool = True


class TriggeredRule(BaseModel):
    id: str
    name: str
    span: Optional[list[int]] = None  # [start, end) in Unicode code points; null for compound rules
    name_zh: str = ""
    category: str = ""
    weight: float = 0
    why: str = ""


class UrlFinding(BaseModel):
    url: str
    issue: Optional[str] = None  # lookalike, homoglyph, punycode, ip_address, suspicious_tld, shortened
    target: Optional[str] = None
    expanded_url: Optional[str] = None
    span: Optional[list[int]] = None


class SimilarCase(BaseModel):
    title: str
    similarity: float
    source: str


class ActionPlan(BaseModel):
    urgency: Literal["routine", "urgent", "critical"]
    steps: list[str]


class AnalyzeResponse(BaseModel):
    risk_score: int
    risk_level: Literal["low", "medium", "high"]
    triggered_rules: list[TriggeredRule]
    url_findings: list[UrlFinding]
    similar_cases: list[SimilarCase]
    explanation: str
    next_question: Optional[str] = None
    transcript: Optional[str] = None
    matched_patterns: list[str] = []  # names from the frontend's API_CONTRACT.md
    # Additions to the agreed contract
    session_id: Optional[str] = None
    language: Literal["en", "zh"] = "en"
    action_plan: Optional[ActionPlan] = None
    incident_summary: Optional[str] = None
    inference_trace: list[str] = []
    score_breakdown: dict[str, float] = {}
    explanation_source: Literal["llm", "template"] = "template"
    scam_probability: Optional[float] = None  # from the trained classifier; null when it has no basis
