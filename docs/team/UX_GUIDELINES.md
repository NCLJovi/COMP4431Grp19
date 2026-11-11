# UX Guidelines — Scam Check (E1)

Rules for the elderly-facing interface. Every rule here is implemented somewhere in
`streamlit_app.py`, `frontend/response_templates.py` or `.streamlit/config.toml`, so it can be checked
against the running app rather than argued about.

**Who we design for:** someone in their 70s or 80s who reads slowly, may have reduced
vision, has used WhatsApp but not much else, and is likely to be embarrassed about being
fooled. They are not stupid. They are being targeted.

---

## 1. Size and spacing

| # | Rule | Value | Where it lives |
|---|---|---|---|
| U1 | Base text is larger than normal | **22px** base (Streamlit default: 16px) | `config.toml` → `baseFontSize` |
| U2 | Headings scale up from that base | 42 / 34 / 28 / 24 / 22 / 20 px | `config.toml` → `headingFontSizes` |
| U3 | Minimum tap target | **56px** tall for ordinary buttons, **68px** for the two main actions. The three example shortcuts are 52px — they are demo aids, not actions the user must take | `streamlit_app.py` → scoped CSS on `.st-key-check_button` |
| U4 | One column, generous page edges | Centred layout, extra top and bottom padding | `config.toml` → `paddingTop`, `paddingBottom` |
| U5 | Text never justified, never narrower than ~40 characters | full width of the column | Streamlit default |

**Why 22px and not 18px:** 18px passes the requirement on paper, but at 18px the
secondary text (captions, hints) drops to 14px, which is where elderly readers stop.
Raising the base raises everything at once.

## 2. Colour and contrast

| # | Rule | Value | Measured |
|---|---|---|---|
| U6 | Body text on white | `#14171A` on `#FFFFFF` | **17.99 : 1** |
| U7 | Body text on panels | `#14171A` on `#F1F4F8` | **16.31 : 1** |
| U8 | Links and primary buttons | `#0B57D0` on white, white on `#0B57D0` | **6.39 : 1** |
| U9 | Never colour alone carries meaning | risk level always has icon + sentence + colour | `frontend/response_templates.py` |
| U10 | One appearance only, no dark-mode toggle | theme locked to light | `config.toml` (`[theme]`, no `[theme.dark]`) |

Everything clears WCAG AA (4.5:1 for body text, 3:1 for large text) with a wide margin,
because elderly users lose contrast sensitivity before they lose acuity.

## 3. Words

| # | Rule |
|---|---|
| U11 | **Never** say: phishing, smishing, social engineering, malware, credential, 2FA, OTP, API, algorithm, pattern, score, database, model, AI. |
| U12 | Say instead: **fake message**, **scam**, **your bank**, **a code we sent you**, **someone pretending to be**. |
| U13 | Maximum **15 words** per sentence. If it needs a comma and an "and", split it. |
| U14 | Maximum **3 reasons** and **3 next steps** per screen. More than three and nothing is remembered. |
| U15 | Every screen ends with something to **do**, not just something to know. |
| U16 | Tone: calm and on the user's side. Never "you should have known", never "warning!", never "danger". |
| U17 | **Never** promise safety. No "100% safe", no "guaranteed", no "this is definitely fine". Low risk says "nothing obviously dangerous" and then explains that nobody can promise safety. |
| U18 | **Never** ask for a name, phone number, ID, card number, password or code. We only ever *tell the user not to give them out*. |

The reassurance line is deliberate: *"Messages like this fool many careful people — you
did the right thing by checking."* This is the difference between a user who tells
someone next time, and a user who hides the message out of shame.

## 4. Interaction

| # | Rule | Implementation |
|---|---|---|
| U19 | One primary action per screen | Screen 1: "Check this message". Screen 2: "Check another message" |
| U20 | Nothing moves on its own; no carousels, no countdowns, no popups | no timers anywhere in `streamlit_app.py` |
| U21 | No login, no account, no email | nothing to sign up for |
| U22 | Privacy notice before anything is typed | first block on screen 1 |
| U23 | Mistakes are not punished | an empty box gets a friendly line, not a red error |
| U24 | Failures still give the user something to do | on error the app says *call 18222*, never shows a stack trace |
| U29 | One question at a time, and every question has a **tap-able** answer | the "have you replied?" step is two buttons, not a text box |
| U30 | The assistant admits what it does not know | an unrecognised question gets "I am not sure, call 18222", never a guess |
| U31 | The conversation is optional: the verdict and the number are always visible without answering anything | the card is complete before the follow-up question appears |
| U32 | **A verdict fits on roughly one phone screen** — no subheadings, three reasons, three steps, one call button | `draw_verdict()`, about 700px at 390px width |
| U33 | The big title disappears once the conversation starts | it is 300px of scrolling that repeats what the user already knows |
| U34 | Older checks fold down to a single line | only the newest verdict is shown in full; earlier ones become "🛑 This looks like a scam (checked earlier)" |
| U35 | The whole page stays under about two phone screens | measured after the first phone test, which showed roughly 3.5 screens of scrolling |
| U36 | **Action before explanation.** The steps and the phone number come *above* the reasons | `draw_verdict()` order: banner → steps → call button → why |
| U37 | The reasons are **one line of short phrases**, never a bulleted diagnosis | "Why: it pretends to be your bank, asks for money, asks you to act fast." |
| U38 | The most serious sign is named first | `PRIORITY` in `frontend/response_templates.py` puts impersonation above "it has a link" |

## 5. Sound

| # | Rule | Implementation |
|---|---|---|
| U25 | Sound only starts after the user does something, never on arrival | speech plays when a verdict appears, which is always the result of a press |
| U26 | The spoken version is **shorter** than the written one | verdict plus first two steps, about 8 seconds |
| U27 | If the computer cannot speak, the screen still works and says what to do | falls back to "call 18222" instead of a dead play button |
| U28 | Speech is slower than the default rate | synthesis rate −1 |

Reading aloud exists because a frightened user may not read carefully. It is not a
decoration: it is the difference between the warning being understood and being skipped.

## 6. Privacy wording (exact)

> **Your message is not saved.** We do not keep it, we do not share it, and we never ask
> for your name, password or bank details.

This sentence must stay on screen 1. Requirement F8 and T4 both depend on it.

## 7. The checklist to hold against every screenshot

- [ ] Is every piece of text readable from arm's length on a phone?
- [ ] Is the biggest thing on the screen the thing the user must do?
- [ ] Does any sentence contain a word a 75-year-old would not use?
- [ ] Can the whole screen be understood without scrolling far?
- [ ] Is there exactly one obvious next step?
- [ ] Would a person who just got scammed feel stupid reading this? (If yes, rewrite it.)
- [ ] Does anything promise the message is safe?
- [ ] If the sound fails, can the user still finish and still know who to call?
- [ ] Can every question the assistant asks be answered by tapping, not typing?

## 8. What this document is for

It is the source for the **UX / Frontend section of the final report**, and it is the
answer to "why did you make those choices?" in the Q&A. Each numbered rule can be cited
as `U13` in the report.
