# Live demo script (6 minutes)

The time limit is 6 minutes per group, then questions. The slides are in `docs/presentation/Scam_Checker_Group19.pptx`, and each slide's speaker notes hold the words for that part.

| Time | Part | Slide |
|---|---|---|
| 0:00–0:15 | Introduction | 1 |
| 0:15–0:40 | What the chatbot does, basic features | 2 |
| 0:40–1:15 | Additional features | 3 |
| 1:15–1:45 | How it works | 4 |
| 1:45–4:30 | **Live demo** | 5 |
| 4:30–5:15 | Evaluation | 6 |
| 5:15–6:00 | Challenges and limitations | 7 |

## Before you present

1. Start the app on your own laptop, and open it once so the detector is loaded:

   ```powershell
   python -m streamlit run streamlit_app.py
   ```

2. **Restart the app just before the demo.** Bookings are kept in memory, so a slot booked in a rehearsal stays taken until the app restarts.
3. Turn the laptop volume up for the read-aloud voice.
4. Keep the two files below open in Notepad, ready to copy.

## Live demo steps

| # | What to do | What the audience sees |
|---|---|---|
| 1 | Type `Hello` | A greeting, and two buttons: **Check a message** and **Book a consultation** |
| 2 | Press the **Bank** example | A red verdict, the reasons, three steps, and the warning read aloud |
| 3 | Press **Yes, I did** | The emergency steps: call the bank, keep the message, call 18222 |
| 4 | Paste the text of `data/demo/hidden_characters_scam.txt` | Still high risk, although invisible characters are hidden inside the words and it is written in Simplified Chinese |
| 5 | Switch to **繁體中文** at the top | The whole conversation so far changes language |
| 6 | Switch back to **English**, then type `I want to book a consultation` | The open days, with one day marked full |
| 7 | Press the first day, then type `10am` | "Sorry, 10:00 … is already booked", with the free times |
| 8 | Press **11:00**, then **Yes, book it** | A booking reference such as SC-4821 |

If time is short, leave out steps 3 and 5.

## Which slots are taken

Counted from the next working day. This is set in `PREBOOKED` in `backend/booking.py`.

| Day | Already booked |
|---|---|
| 1st open day | 10:00 and 14:00 |
| 2nd | 11:00 |
| 3rd | Every slot (shown as full) |
| 4th | 15:00 |
| 5th | None |

## If something goes wrong

- **The laptop or app fails:** slide 5 has two screenshots to talk through.
- **No sound:** say that the warning is also read aloud on Windows, and move on.
- **A slot you want is taken:** it was booked in a rehearsal. Pick another time, or restart the app.
