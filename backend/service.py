"""The single entry point used by both the Streamlit app and the POST /analyze API."""
from __future__ import annotations

import logging

from . import dialogue, wording
from .config import MAX_MESSAGE_CHARS
from .patterns import FALLBACK_PATTERN, short_explanation
from .schemas import AnalyzeResponse

logger = logging.getLogger(__name__)


class InvalidMessage(ValueError):
    """The message is empty or too long. The text of the error is safe to return to the caller."""


async def check_message(message: str, session_id: str | None = None) -> AnalyzeResponse:
    text = message.strip()
    if not text:
        raise InvalidMessage("message is empty")
    if len(text) > MAX_MESSAGE_CHARS:
        raise InvalidMessage("message is too long")
    # Without a session_id nothing is kept, because the app promises "your message is not saved".
    session = dialogue.get_session(session_id) if session_id else dialogue.Session(id="")
    try:
        # No LLM here: the app needs an answer within 3 seconds and a local model can take longer.
        response = await dialogue.analyze_new(session, text, use_llm=False)
    except Exception:
        # A crash must never look like "safe" to the user.
        logger.exception("analysis failed")
        return AnalyzeResponse(risk_score=50, risk_level="medium", triggered_rules=[], url_findings=[], similar_cases=[],
                               matched_patterns=[FALLBACK_PATTERN],
                               explanation=wording.SHORT_EXPLANATION["analysis_failed"])
    response.session_id = session_id
    response.explanation = short_explanation(response.risk_level, response.matched_patterns)
    return response
