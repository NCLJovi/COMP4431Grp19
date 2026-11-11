# API Contract Proposal — frontend → analysis service

**From:** E1 (frontend)
**To:** EarlyFat (backend / risk scoring), cc Henry (patterns)
**Purpose:** agree the exact JSON before either side writes integration code.

---

## Endpoint

```
POST /analyze
Content-Type: application/json
```

**Request**

```json
{ "message": "HSBC ALERT: your account will be suspended. Verify now: http://hsbc-verify.top" }
```

`message` is the raw text the user pasted. Max 2,000 characters (the frontend enforces
this before sending). No user ID, no phone number, no metadata — we deliberately send
nothing that could identify the person.

**Response — 200 OK**

```json
{
  "risk_score": 85,
  "risk_level": "high",
  "matched_patterns": ["urgency", "money request", "bank impersonation"],
  "explanation": "This message asks for money urgently and claims to be from your bank."
}
```

## Field rules

| Field | Type | Required | Rules | What the UI does with it |
|---|---|---|---|---|
| `risk_score` | integer | yes | 0–100 inclusive. 0 = nothing found, 100 = certain scam. | Not shown as a number. Used only to decide which colour band and how strongly to word the warning. |
| `risk_level` | string | yes | exactly `"low"`, `"medium"` or `"high"` — lowercase, no others. | Selects the whole response template. An unknown value is treated as `"medium"`. |
| `matched_patterns` | array of strings | yes | 1–6 items. **Use the names below**, not free text and not snake_case. | Translated one-by-one into plain sentences ("It pretends to be your bank."). We show at most the first 3. |
| `explanation` | string | yes | One sentence, max 20 words, plain English, no jargon. | Displayed as the sentence under the verdict if it is short enough; otherwise the template's own sentence is used. |

### Pattern names the frontend already has wording for

```
urgency
money request
bank impersonation
government impersonation
prize
parcel
job offer
investment
romance
tech support
account problem
password request
crypto
link
```

If Henry's list uses different names, send them to E1 **before** integration and each one
is a one-line addition to `PATTERN_PLAIN` in `response_templates.py`. Unrecognised names
are not shown to the user as raw text — they fall back to a neutral sentence — so nothing
breaks, but the warning gets vaguer.

## Errors and timing

| Situation | What we need back | What the user sees |
|---|---|---|
| Empty or whitespace-only `message` | `400` with `{"detail": "message is empty"}` | "Please paste or type the message first." (we catch this before sending anyway) |
| Message longer than 2,000 characters | `400` | "That message is too long to check. Please copy the most important part." |
| Anything unexpected inside the service | still a **valid 200** body with `risk_level: "medium"` and a generic `explanation` | "This message looks suspicious…" + the call-18222 line. A crash must never look like "safe". |
| Service down / more than 3 seconds | no response, timeout on our side | "We could not check this message right now. Please call the Anti-Scam Helpline on 18222." |

**Latency:** we need the response inside **3 seconds** (requirement N7). If scoring needs
more, return `medium` fast rather than `high` slowly.

**CORS:** if the frontend and backend run on different ports during the demo, enable CORS
for `http://localhost:8501`.

## How to test it without the frontend

```powershell
curl -X POST http://127.0.0.1:8000/analyze -H "Content-Type: application/json" -d "{\"message\":\"Your account will be suspended, verify now\"}"
```

Expected: a JSON body with `risk_level` of `high` or `medium` and `matched_patterns`
containing at least `urgency`.

## Running against a separate API

The Streamlit app runs the detector in its own process by default. To call a separate API instead, set
`SCAM_API_URL` to the full address, for example `http://127.0.0.1:8000/analyze`.

## Questions for the meeting

1. Is `POST /analyze` the path you want, and which port will you run on?
2. Will `matched_patterns` use the names in the list above?
3. Can you guarantee a response within 3 seconds, or should I show a "checking…" state?
4. What is your realistic date for a working endpoint I can point at?
5. Who do I message when it breaks during the demo?
