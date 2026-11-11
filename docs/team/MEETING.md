# Team meeting — E1's agenda

**Meeting date:** __________  **Attending:** Henry, EarlyFat, E1
**Hard deadline:** 19 Nov 2026, 23:59 (Friday class) — Canvas: source zip + pptx
**Demo:** 20 or 27 Nov, English, 7 minutes + 3 minutes Q&A

---

## 1. Show first, talk second (5 minutes)

Open the app and press three buttons. Do not explain the code first.

| Order | Action | What it proves |
|---|---|---|
| 1 | Type a question: *"what is 18222?"* | it answers like a chatbot, not a form |
| 2 | **A bank text** | red verdict, 3 plain reasons, 3 next steps |
| 3 | **Yes, I did** | the emergency branch: call the bank, keep the message, report |
| 4 | **A parcel text** | amber verdict — the "might be real" case |
| 5 | **A message from family** | green verdict that still does not promise safety |

Then say one sentence: *"All the wording is in one file, and the answer comes from a fake
function until your scorer is ready."*

## 2. Questions for EarlyFat

| Question | What I need written down |
|---|---|
| What JSON will your API return? Can we use `{risk_score, risk_level, matched_patterns, explanation}`? | |
| Which port and path? (`POST /analyze` on 8000?) | |
| Will `matched_patterns` use the names in `API_CONTRACT.md`, or should I map yours? | |
| Can you guarantee a reply inside 3 seconds? | |
| When will there be something I can point `USE_REAL_API = True` at? | |
| Who do I message when it breaks at 2am? | |

## 3. Questions for Henry

| Question | What I need written down |
|---|---|
| What scam categories are you covering? (I need the list to write wording for each) | |
| Are the categories the same as the `matched_patterns` names, or separate? | |
| Will you return confidence or severity per pattern, or just a yes/no? | |
| Can you give me 3–4 real (anonymised) scam messages for the usability test? | |

## 4. Decisions nobody owns yet — settle these today

| # | Decision | Answer |
|---|---|---|
| D1 | **Who builds the pptx?** (the submission requires one; it is not in anyone's plan) | |
| D2 | **Who merges the three report sections into one voice?** | |
| D3 | **End-to-end testing:** when the API and frontend meet, who is in the room, and on which day? | |

## 5. For both — evaluation and demo

| Question | Answer |
|---|---|
| Can we recruit 3–5 elderly users together? Who knows someone we can ask? | |
| When is the first full end-to-end run-through? | |
| Who presents the 7 minutes, and who answers Q&A? | |
| Does the UI part of the demo belong to me, or does the presenter drive? | |

## 6. What I am committing to after this meeting

- Replace the fake function with EarlyFat's endpoint on the agreed date, and add the
  timeout / failure screens.
- Voice input and read-aloud, once the text version is stable.
- Usability test script for 3–5 elderly users, and the findings section.
- Screenshots of every screen for the slides.

## 7. What I need from the team

- Two hours of someone's grandparent, if at all possible.
- A fixed date for integration — not "next week".
- Any scam message that actually reached a family member, with the names removed. Real
  examples make the demo land; invented ones sound like a textbook.
