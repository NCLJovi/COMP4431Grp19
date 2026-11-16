# Earlier measurements on real messages

These figures were measured **before** rules were changed or the GA was retrained, with a one-off import script that is not part of the project. The current code cannot reproduce them, because the rules have changed since. They are kept here because the README and the slides quote them as the "before" side of each comparison.

To measure the current code, run:

```powershell
python -m evaluation.real_test
```

A message counts as flagged at a score of 40 or more.

| When | Messages | Before | After | How "after" was reached |
|---|---|---|---|---|
| **Combined, as quoted in the README and slides** | 41 = the first 6 + the 35 below | **17 of 41 (41%)** | — | Each message scored before any rule was written from it |
| First six Chinese scams from the questionnaire | 6 | 1 of 6 | 6 of 6 | Text clean-up and new rules, written from these same six messages |
| Questionnaire, first batch (22 answers) | 35 real scams whose wording the rules had not seen | 16 of 35 (46%), 9 high risk | — | Measured before any rule was changed |
| Questionnaire, first batch: held-out test set | 11 | 4 of 11 | 10 of 11 (91%) | Rules written only from the training messages; GA tuned on them plus the synthetic set |
| Questionnaire, second batch (answers 23–41) | Held-out set grew to 17 | 15 of 17 (88%) | 16 of 17 (94%) | GA retrained with the new training messages; no rule written from the test set |

## Notes

- **Answers and messages are counted differently:** an answer can hold more than one message.
- **46 answers:** the 41 answers in the Forms export, plus 5 received earlier. Those 5 are among the first six scams; the sixth is the same message as answer 11.
- **41 messages in the combined figure:** the first six scams, plus 35 from answers 1–22. Answers 1–22 hold 40 messages, but 5 of them share a template with the first six, and rules had already been written from that template, so they were left out. Answers 23–41 came later and are counted in the held-out figures instead.
- **The two parts were measured at different times:** the first six were scored with the original rules. The 35 were scored after the rules for the first six had been added, but before any rule was written from the 35.
- **Held-out set:** the messages were grouped by template, and whole groups were drawn at random into `data/real_test.csv`. The rest went into `data/zh_training.csv` and `data/en_extra_training.tsv`.
- **Test wording was visible:** the test wording was seen while the rules were written. Treat the "after" figures as an encouraging sign, not a measured accuracy.
- **Raw questionnaire export:** it is not in the repository, because it holds respondents' names and email addresses. The messages in `data/` have real phone numbers, links and account numbers replaced by fictional ones.
