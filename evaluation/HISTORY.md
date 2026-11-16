# Earlier measurements on real messages

These figures were measured **before** rules were changed or the GA was retrained, with a one-off import script that is not part of the project. The current code cannot reproduce them, because the rules have changed since. They are kept here because the README and the slides quote them as the "before" side of each comparison.

To measure the current code, run:

```powershell
python -m evaluation.real_test
```

A message counts as flagged at a score of 40 or more.

| When | Messages | Before | After | How "after" was reached |
|---|---|---|---|---|
| Six Chinese scams collected by the team | 6 | 1 of 6 | 6 of 6 | Text clean-up and new rules, written from these same six messages |
| Questionnaire, first batch (22 answers) | 35 real scams whose wording the rules had not seen | 16 of 35 (46%), 9 high risk | — | Measured before any rule was changed |
| Questionnaire, first batch: held-out test set | 11 | 4 of 11 | 10 of 11 (91%) | Rules written only from the training messages; GA tuned on them plus the synthetic set |
| Questionnaire, second batch (answers 23–41) | Held-out set grew to 17 | 15 of 17 (88%) | 16 of 17 (94%) | GA retrained with the new training messages; no rule written from the test set |

## Notes

- **35 messages:** these are the messages from the first batch, minus 5 that share a template with the six team-collected scams. Those 5 were left out because rules had already been written from that template.
- **Held-out set:** the messages were grouped by template, and whole groups were drawn at random into `data/real_test.csv`. The rest went into `data/zh_training.csv` and `data/en_extra_training.tsv`.
- **Test wording was visible:** the test wording was seen while the rules were written. Treat the "after" figures as an encouraging sign, not a measured accuracy.
- **Raw questionnaire export:** it is not in the repository, because it holds respondents' names and email addresses. The messages in `data/` have real phone numbers, links and account numbers replaced by fictional ones.
