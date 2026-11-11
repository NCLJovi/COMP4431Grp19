# Data collection guide

Real messages are the most useful thing we can add before the demo. They let us measure how well the detector really works and train the Chinese model.

## What to collect

| | Target | Minimum |
|---|---|---|
| Scam messages, Chinese | 50 to 100 | 30 |
| Normal messages, Chinese | 50 to 100 | 30 |
| Scam messages, English | 30 to 50 | 20 |
| Normal messages, English | 30 to 50 | 20 |

**Normal messages matter as much as scams.** Without them, the detector learns that anything that looks official is a scam and will frighten people about genuine messages.

### Good scam examples

- Bank or card alerts asking you to log in, verify, or reply with a code
- Fake parcel or delivery fees
- Officials such as police, immigration or customs
- Investment groups, crypto, "guaranteed returns"
- Part-time jobs, liking videos, "earn per day"
- "Mum, this is my new number", or a friend who needs money
- Prizes, refunds, subsidies
- Account verification, or "your account will be cancelled"
- Contracts or subscriptions charging you unless you call
- Online gambling offers
- Simplified Chinese versions of any of these

### Good normal examples

These are the ones most often mistaken for scams, so they matter most:

- Genuine one-time passwords that say "do not share"
- Bank statements and payment reminders
- Delivery updates and pickup codes
- Government reminders, hospital appointments, utility bills
- Family and friends, including requests for small amounts such as "transfer me $120 for dinner"
- Shop promotions and work messages

## Where to find them

- Messages received by you, family or friends. Ask first.
- Police anti-scam sites: the Anti-Deception Coordination Centre (ADCC) and CyberDefender
- HKMA alerts on fraudulent bank websites, and bank anti-fraud notices
- Your own genuine bank, delivery and government messages for the normal examples

## Remove personal data before adding anything

| Replace | With |
|---|---|
| Real names | `Chan Tai Man` or `陳大文` |
| Phone numbers | `2123 4567` or `9123 4567` |
| Account or card numbers | `123-456789-001` |
| Links in scam messages | A fake address with the same ending, e.g. `https://scam-example.wiki/` |
| Codes and OTPs | Any made-up number |

Keep everything else exactly as received, including typos, emoji, odd spacing and Simplified characters. Those details are what scammers use to get past filters.

## How to fill in the file

Open `data/collection_template.csv` in Excel. Add one message per row:

| Column | What to write | Example |
|---|---|---|
| `label` | `scam` or `ham` (normal) | `scam` |
| `lang` | `zh` or `en` | `zh` |
| `category` | A short type, see the list below | `bank` |
| `text` | The whole message | `【滙豐】閣下戶口已被凍結，請立即回覆驗證碼。` |
| `source` | Where it came from | `ADCC 2026-10` or `family member` |

Category list: `bank`, `parcel`, `government`, `investment`, `job`, `family`, `prize`, `refund`, `account`, `charge`, `gambling`, `tech_support`, `shopping`, `otp`, `delivery`, `work`, `other`.

Save with **File → Save As → CSV UTF-8 (Comma delimited)**. Other CSV options break Chinese characters.

A message with line breaks is fine. Excel keeps it in one cell.

## What happens next

Send the file to the person maintaining the backend. They will:

1. Check the format and remove duplicates.
2. Set about 30% aside as a test set, chosen at random before anyone looks at the results. Those messages are never used to change rules or train models, so the accuracy figure in the slides is fair.
3. Use the rest to train the Chinese model and tune the rule weights.

Please do not send the same messages to anyone else for tuning, otherwise the test set stops being fair.
