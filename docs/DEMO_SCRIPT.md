# Live demo script

**6 minutes per group, then questions.** Slides are in `docs/presentation/Scam_Checker_Group19.pptx`;
each slide's speaker notes hold the words for that part, with the timings below.

## Run sheet

| Time | Part | Slide |
|---|---|---|
| 0:00–0:10 | Introduction | 1 |
| 0:10–0:30 | The problem, in police figures | 2 |
| 0:30–0:48 | What the chatbot does — basic features | 3 |
| 0:48–1:18 | Additional features | 4 |
| 1:18–1:43 | The interface commitments | 5 |
| 1:43–2:13 | How the score is built | 6 |
| **2:13–4:33** | **Live demo** | 7 |
| 4:33–4:58 | What we measured | 8 |
| 4:58–5:28 | Problems and limits | 9 |
| — | Sources (not presented) | 10 |

Finish at 5:28, which leaves about 30 seconds of slack in the 6 minutes.

## Before you present

1. Start the app on your own laptop and open it once, so the detector is loaded:

   ```powershell
   python -m streamlit run streamlit_app.py
   ```

2. **Restart the app just before the demo.** Bookings are held in memory, so a slot booked in a
   rehearsal stays taken until the app restarts.
3. Turn the laptop volume up — the verdict is read aloud.
4. Keep `data/demo/hidden_characters_scam.txt` open in Notepad, ready to copy.
5. Have the hosted copy open in a second tab as a fallback: <https://comp4431grp19.streamlit.app/>

## Say this before the first click

> "It is 9pm. A 76-year-old has just received an SMS claiming to be from HSBC."

Then run the five steps.

## Live demo steps

| # | What to do | What the audience sees |
|---|---|---|
| 1 | Type `Hello` | A greeting, and two buttons: **Check a message** and **Book a consultation** |
| 2 | Press the **Bank** example, then **Yes, I did** | A red verdict, three plain reasons, the warning read aloud, then the emergency steps: call the bank, keep the message, call 18222 |
| 3 | Paste `data/demo/hidden_characters_scam.txt` | Still high risk, although invisible characters sit inside the words and the text is Simplified Chinese |
| 4 | Switch to **繁體中文** at the top | The whole conversation so far changes language |
| 5 | Type `I want to book a consultation`, press the first day, type `10am`, then press **11:00** and confirm | 10:00 is refused as taken, 11:00 is confirmed with a reference such as SC-4821 |

If time is short, leave out step 2's "Yes, I did" branch.

## Which slots are taken

Counted from the next working day; set in `PREBOOKED` in `backend/booking.py`.

| Day | Already booked |
|---|---|
| 1st open day | 10:00 and 14:00 |
| 2nd | 11:00 |
| 3rd | Every slot (shown as full) |
| 4th | 15:00 |
| 5th | None |

## If something goes wrong

- **The laptop or app fails:** slide 7 carries two screenshots — talk through those.
- **No sound:** say the verdict is read aloud on Windows, and move on.
- **A slot you want is taken:** it was booked in a rehearsal. Pick another time, or restart the app.
- **You are running late:** cut slide 9 to its limitations panel and finish on the URL.
