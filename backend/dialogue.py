"""Multi-turn follow-up: tracks what has already happened, then gives the matching action plan."""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from . import wording
from .normalize import normalize, to_traditional
from .config import MAX_SESSIONS, SESSION_TTL_S
from .pipeline import analyze, detect_language
from .schemas import ActionPlan, AnalyzeResponse
from .scoring import risk_level

SLOTS = ("paid", "otp_shared", "details_shared", "clicked")

_POS = {
    "paid": r"\b(?:i(?:'ve| have)?|we(?:'ve| have)?|already|just)\b[^.!?\n]{0,25}\b(?:paid|transferred|sent (?:the |them |him |her )?money|wired|remitted|deposited)\b|過咗數|过咗数|過左數|已經過數|已過數|轉咗|转咗|轉左|俾咗錢|畀咗錢|俾左錢|已轉帳|已转账|已轉賬|已付款|付咗款|匯咗|入咗錢|入左錢",
    "otp_shared": r"\b(?:i(?:'ve| have)?|already|just)\b[^.!?\n]{0,25}\b(?:gave|given|told|sent|shared|entered|typed)\b[^.!?\n]{0,25}\b(?:otp|code|password|pin)\b|(?:俾|畀|話俾|話畀|講|輸入|输入|入|填)(?:咗|左|了).{0,10}(?:OTP|otp|驗證碼|验证码|密碼|密码)",
    "details_shared": r"\b(?:i(?:'ve| have)?|already|just)\b[^.!?\n]{0,25}\b(?:gave|given|told|sent|shared|entered|typed)\b[^.!?\n]{0,30}\b(?:card|hkid|id|details|account)\b|(?:俾|畀|話俾|講|輸入|入|填)(?:咗|左|了).{0,10}(?:卡號|信用卡|身份證|資料|戶口)",
    "clicked": r"\b(?:i(?:'ve| have)?|already|just)\b[^.!?\n]{0,20}\b(?:clicked|tapped|opened)\b|(?:撳|㩒|按|點|点|開)(?:咗|左)|(?:撳|㩒|按|點|点|打開)了.{0,4}(?:連結|链接|網址|网址)",
}
_NEG = {
    "paid": r"\b(?:have not|haven't|didn't|did not|not yet)\b[^.!?\n]{0,20}\b(?:pa(?:y|id)|transfer\w*|sen[dt])\b|未過數|未过数|冇過數|沒有轉|未轉|未俾錢|冇俾錢|冇轉",
    "otp_shared": r"\b(?:have not|haven't|didn't|did not)\b[^.!?\n]{0,25}\b(?:give|given|share|shared|tell|told|enter|entered)\b[^.!?\n]{0,20}\b(?:otp|code|password|pin)\b|(?:未|冇|沒有)(?:俾|畀|提供|話).{0,8}(?:OTP|otp|驗證碼|密碼)",
    "details_shared": r"\b(?:have not|haven't|didn't|did not)\b[^.!?\n]{0,25}\b(?:give|given|share|shared|enter|entered)\b[^.!?\n]{0,25}\b(?:card|details|hkid|id)\b|(?:未|冇|沒有)(?:俾|畀|提供|填).{0,8}(?:資料|卡號|身份證)",
    "clicked": r"\b(?:have not|haven't|didn't|did not)\b[^.!?\n]{0,15}\b(?:click|clicked|tap|tapped|open|opened)\b|(?:未|冇|沒有)(?:撳|㩒|按|點|开|開)",
}
POSITIVE = {k: re.compile(to_traditional(v), re.IGNORECASE) for k, v in _POS.items()}
NEGATIVE = {k: re.compile(to_traditional(v), re.IGNORECASE) for k, v in _NEG.items()}
_YES = re.compile(r"^\s*(?:yes|yeah|yep|y|i did|did|有|係|係呀|係啊|是|是的|對|做咗|有呀|有啊|已經)\s*[.!。！]*\s*$", re.IGNORECASE)
_NO = re.compile(r"^\s*(?:no|nope|n|not yet|i didn't|冇|沒有|未|未有|唔係|不是|否|冇呀|未呀|無)\s*[.!。！]*\s*$", re.IGNORECASE)
_AMOUNT = re.compile(r"(?:hk\$|hkd\s?|\$)\s?([\d,]+(?:\.\d+)?)|([\d,]+(?:\.\d+)?)\s*(?:蚊|元|港元|港幣|hkd|dollars)", re.IGNORECASE)

RULE_SLOT_PRIORITY = (
    ("paid", {"R5", "R18", "C4", "C5", "C7", "C8"}),
    ("otp_shared", {"R3", "C3"}),
    ("details_shared", {"R4", "C3"}),
    ("clicked", {"R15", "R16", "U1", "C1"}),
)


@dataclass
class Session:
    id: str
    language: str = "en"
    state: dict[str, bool | None] = field(default_factory=lambda: {s: None for s in SLOTS})
    pending_slot: str | None = None
    analysis: AnalyzeResponse | None = None
    original_text: str | None = None
    amount: str | None = None
    updated: float = field(default_factory=time.time)


_sessions: dict[str, Session] = {}


def get_session(session_id: str | None) -> Session:
    now = time.time()
    for key in [k for k, s in _sessions.items() if now - s.updated > SESSION_TTL_S]:
        del _sessions[key]
    if session_id in _sessions:
        session = _sessions[session_id]
    else:
        while len(_sessions) >= MAX_SESSIONS:
            del _sessions[min(_sessions, key=lambda k: _sessions[k].updated)]
        session = Session(id=session_id or uuid.uuid4().hex)
        _sessions[session.id] = session
    session.updated = now
    return session


def reset_for_new_message(session: Session) -> None:
    """Forget the previous case, so an explicit new submission is always analysed from scratch."""
    session.state = {s: None for s in SLOTS}
    session.pending_slot = session.analysis = session.original_text = session.amount = None


def update_state(session: Session, message: str) -> bool:
    """Reads the user's reply. Returns True if it said anything about what has happened."""
    message = normalize(message)[0]
    changed = False
    if session.pending_slot and _YES.match(message):
        session.state[session.pending_slot] = True
        return True
    if session.pending_slot and _NO.match(message):
        session.state[session.pending_slot] = False
        return True
    for slot in SLOTS:
        if NEGATIVE[slot].search(message):
            session.state[slot] = False
            changed = True
        elif POSITIVE[slot].search(message):
            session.state[slot] = True
            changed = True
    amount = _AMOUNT.search(message)
    if session.state["paid"] and amount:
        session.amount = (amount.group(1) or amount.group(2)).replace(",", "")
    return changed


def _next_slot(session: Session) -> str | None:
    if session.analysis is None or session.analysis.risk_level == "low":
        return None
    triggered = {r.id for r in session.analysis.triggered_rules}
    for slot, rule_ids in RULE_SLOT_PRIORITY:
        if session.state[slot] is None and triggered & rule_ids:
            return slot
    return None


def build_action_plan(session: Session) -> ActionPlan:
    state = session.state
    keys: list[str] = []
    if state["paid"]:
        keys += ["call_bank", "call_hotline", "report_police"]
    if state["otp_shared"] or state["details_shared"]:
        keys += ["freeze_account"]
        if not state["paid"]:
            keys += ["hotline_advice"]
    if state["clicked"]:
        keys += ["close_website"]
    if any(state[s] for s in SLOTS):
        keys += ["keep_evidence", "recovery_scam"]
        urgency = "critical" if state["paid"] or state["otp_shared"] else "urgent"
    else:
        keys = ["do_not_engage", "verify_yourself", "ask_for_help"]
        urgency = "routine"
    return ActionPlan(urgency=urgency, steps=[wording.ACTION_STEPS[k][session.language] for k in keys])


def incident_summary(session: Session) -> str:
    analysis = session.analysis
    text = wording.INCIDENT
    events = "; ".join(v for k, v in wording.INCIDENT_EVENTS.items() if session.state[k]) or text["nothing_confirmed"]
    lines = [text["title"].format(time=f"{datetime.now():%Y-%m-%d %H:%M}"), text["check_notice"], text["what_happened"].format(events=events)]
    if session.amount:
        lines.append(text["amount"].format(amount=session.amount))
    if analysis:
        lines.append(text["assessment"].format(level=analysis.risk_level, score=analysis.risk_score))
        rule_names = sorted({r.name for r in analysis.triggered_rules if r.weight > 0})
        lines.append(text["warning_signs"].format(signs=", ".join(rule_names) or text["no_signs"]))
        if analysis.url_findings:
            lines.append(text["links"].format(links=", ".join(u.url for u in analysis.url_findings)))
    if session.original_text:
        lines.append(text["original"].format(text=session.original_text[:500]))
    return "\n".join(lines)


def _finish_turn(session: Session, response: AnalyzeResponse) -> AnalyzeResponse:
    session.pending_slot = _next_slot(session)
    response.next_question = wording.FOLLOW_UP_QUESTIONS[session.pending_slot][session.language] if session.pending_slot else None
    response.session_id = session.id
    harmed = any(session.state[s] for s in SLOTS)
    if harmed or response.risk_level != "low":
        response.action_plan = build_action_plan(session)
    if harmed:
        response.incident_summary = incident_summary(session)
    return response


def _follow_up_text(session: Session) -> str:
    state = session.state
    if state["paid"] or state["otp_shared"]:
        key = "money_or_code_lost"
    elif any(state[s] for s in SLOTS):
        key = "other_harm"
    else:
        key = "nothing_lost"
    return wording.FOLLOW_UP_REPLY[key][session.language]


def _looks_like_new_message(message: str) -> bool:
    return len(message) > 80 or bool(re.search(r"https?://|www\.", message, re.IGNORECASE))


async def analyze_new(session: Session, text: str, use_llm: bool = True, read_state: bool = False) -> AnalyzeResponse:
    """Start a new case. Pasted scam text says nothing about the user, so state is read only on request."""
    reset_for_new_message(session)
    if read_state:
        update_state(session, text)
    response = await analyze(text, use_llm=use_llm)
    session.language = response.language
    session.analysis = response
    session.original_text = text
    return _finish_turn(session, response.model_copy(deep=True))


async def _follow_up(session: Session, message: str) -> AnalyzeResponse:
    if session.analysis is None:
        # Money or secrets may be gone and no message has been seen yet: help first, assess later.
        session.language = detect_language(message)
        harmed = any(session.state[s] for s in SLOTS)
        score = 40 if harmed else 0
        response = AnalyzeResponse(risk_score=score, risk_level=risk_level(score), triggered_rules=[], url_findings=[],
                                   similar_cases=[], explanation=_follow_up_text(session), language=session.language)
        result = _finish_turn(session, response)
        result.next_question = wording.ASK_FOR_THE_MESSAGE[session.language]
        return result
    response = session.analysis.model_copy(deep=True)
    response.explanation = _follow_up_text(session)
    response.explanation_source = "template"
    return _finish_turn(session, response)


async def chat(session: Session, message: str, use_llm: bool = True) -> AnalyzeResponse:
    """One chat turn: either an answer about what happened, or a message to analyse."""
    if _looks_like_new_message(message):
        return await analyze_new(session, message, use_llm, read_state=True)
    if update_state(session, message):
        return await _follow_up(session, message)
    preview = await analyze(message, use_llm=False)
    if session.analysis is None or preview.risk_level != "low":
        return await analyze_new(session, message, use_llm)
    # Small talk during a case: stay on the case and repeat what to do next.
    response = session.analysis.model_copy(deep=True)
    response.explanation = wording.FOLLOW_UP_REPLY["stay_on_case"][session.language]
    response.explanation_source = "template"
    return _finish_turn(session, response)
