# Week 3 — Today's plan for you (and what you will explain back)

Nachiket has finished his side of Week 3 in `main`: the eval set and script, the data-validation report, the anomaly
rules, the multi-part question fixes, and a draft scope lock. **Your job today is to understand it, check it against
the data, and be able to explain it.** The goal is not to write lots of code: it is to be the person who can say
whether the answers are right, and why the rules flag what they flag.

Work on your **own branch** so `main` stays safe. Replace `<yourname>` with your first name in lowercase.
Setup (Codespace, key, branch) is in `docs/her_tasks_detailed.md`, Part 0.

```bash
git pull origin main
git checkout -b <yourname>-week3
python -m pytest -q          # expect: 35 passed
```

## Schedule

| Time | What | Who leads |
|---|---|---|
| 20 min | **Lesson 1 — Evaluation** (Nachiket teaches, notes below) | Nachiket |
| 40 min | Tasks A and B (below) | You |
| 20 min | **Lesson 2 — SAP data quality** (you teach, outline below) | You |
| 30 min | Tasks C and D | You |
| 20 min | Explain-back call: you walk Nachiket through Tasks A–D | You |

---

## Lesson 1 (Nachiket → you): why "looks right" is not enough

Read this beforehand, then ask questions on the call.

1. An LLM answer can be **fluent and wrong**. Last week the copilot printed "Packaging average ₹1,047,600.02"; the
   real figure is 104,760.02. It read fine. Only a check against the data caught it.
2. **SQL-correct and answer-correct are different.** The SQL can be right and the final sentence wrong (the model
   did its own maths), or the SQL wrong and the sentence confidently built on it.
3. An **eval set** is a list of questions, each paired with an answer we already know is correct. Run the copilot over
   it, count passes. The pass rate is a number we can improve and defend, instead of "it seems okay".
4. Ours: `tests/eval_cases.json` (the cases) and `tests/eval_answers.py` (the runner). A case passes when every
   `must_contain` value appears in the answer and no `must_not_contain` value does.
5. Result so far: the v0.1 code scored **6/7**; the current code scores **7/7**. The one v0.1 failure was Q3, which
   missed the 6 late-payment anomalies that the new rule finds.

Run it yourself: `python -m tests.eval_answers` (about 1–2 minutes, uses the API). Add `--runs 3` to see flakiness.

---

## Task A — Confirm the eval answers are really correct (30 min)

Nachiket wrote the expected values in `tests/eval_cases.json` from the data; **you are the one who confirms them.**

1. Run `python -m tests.check_answers` (pandas ground truth, no LLM).
2. Open `tests/eval_cases.json`. For each of the 7 cases, check every `must_contain` value against the ground truth
   and the CSVs in `data/mock_sap/`. Pay special attention to:
   - **q1:** are Quantum Circuit Traders and Summit Consulting Services really the only vendors with a delayed
     payment whose payment date is in September 2026?
   - **q6:** "which vendors had delayed payments and by how much" — is 35, 33, 32 the right set of delays?
   - **q7:** September 2026 has 19 POs / 2,524,057.69 and August has 36 / 2,811,804.49. Check with a filter in Excel
     or pandas on `po_date`.
3. If a value is wrong or a case is ambiguous, edit `tests/eval_cases.json` and write the reason in that case's
   `"note"` field.

**Files you edit:** `tests/eval_cases.json` (only if you find an error).

## Task B — Judge the anomaly rules by eye (30 min)

This is the Day 3 task. The rule lives in `src/data_layer/anomaly.py` and is documented in `docs/architecture.md`
(Decision 4). Run it:

```bash
python -m src.app "Flag any transactions that look unusual this week."
```

It flags 6 late payments (more than 24.6 days after due date, which is the mean plus 2 standard deviations),
3 amount outliers and 2 duplicate POs. Answer these in `docs/anomaly_review.md` (create it):

1. Open `data/mock_sap/payments.csv` and look at the 6 flagged payments. Do they look unusual to you as an SAP
   person, or is a 26-day delay normal for some vendors?
2. Is 2 standard deviations too loose or too tight? Nachiket tried 1.5 and got 13 flags (too many to review). Would
   you pick a different cut-off, or a fixed rule instead (for example "more than 30 days late")? Give a reason.
3. Are there payments that *should* be flagged but aren't (for example a payment barely late for a very large amount)?
4. Anything flagged that a finance person would call normal?

**File you create:** `docs/anomaly_review.md` (one short paragraph per question).

Background you need to explain the maths: the **mean** is the average delay (−10.8, so on average payments are made
10.8 days *early*); the **standard deviation** measures how spread out delays are (17.7 days); "2σ above the mean" means
unusually far from normal. It is a screening rule, not proof of a problem.

---

## Lesson 2 (you → Nachiket): SAP data quality (20 min, prepare in advance)

Prepare a short walkthrough covering the points below. Use your own words and examples from the mock data.

1. **The real flow:** PO → goods receipt → invoice → payment. In real SAP, payment follows an *invoice*, not the PO
   directly. Where are time gaps normal (for example payment terms of 30 days) and where are they suspicious
   (payment before the goods arrived)?
2. **Three real-world data problems** and how they would look in our tables:
   - duplicate POs from re-entry (we have PO00221 and PO00222)
   - missing vendor master data (a PO whose vendor is not in `vendors.csv`)
   - backdated entries (a payment dated before its PO)
3. **Whether our validation catches them.** Nachiket added `flag_bad_rows` in `src/data_layer/loader.py` (negative
   amount, missing vendor ID, payment before PO date, Paid with no amount, vendor not in master). Run
   `python -m src.data_layer.loader` and look at `data/mock_sap/flagged_rows.csv`: three rows are flagged. Would a real
   data-quality report catch more?

## Task C — Propose realistic bad rows and extra rules (20 min)

In `docs/data_quality_notes.md` (create it) write:

1. Three **specific bad rows** you would add to the mock data to make it feel real (give all column values, for example
   "payment PMT00200 for PO00050 dated 2026-02-01 while PO00050 is dated 2026-03-10: backdated"). Do **not** edit the CSVs
   today; we will add them together so the tests stay in sync.
2. Two **extra validation rules** a real SAP data-quality report would have, written as a sentence each.
3. Whether the current rules wrongly flag anything normal (false positives).

**File you create:** `docs/data_quality_notes.md`.

## Task D — Write 3 tricky questions for the eval set (20 min)

Write the questions a real procurement user might ask that you think the copilot will **fail**. For each, work out the
correct answer from the CSVs yourself, then add a case to the end of the list in `tests/eval_cases.json`:

```json
  {
    "id": "q8_your_short_name",
    "question": "Your question here?",
    "must_contain": ["a value or name that must appear", "another one"],
    "must_not_contain": ["something wrong that must not appear"],
    "note": "How you worked out the answer, and the as-of date assumption."
  }
```

Remember "this month" means September 2026 (as-of 2026-09-30). Ideas: "Which vendor has the most pending POs?",
"What is the total of POs with no category?", "Which vendors are paid late more than once?". Run
`python -m tests.eval_answers q8` to see whether it passes. A failure is a **success** here: it goes on the broken list.

**File you edit:** `tests/eval_cases.json`.

---

## Explain-back call: be ready to answer these

1. What is the difference between SQL-correct and answer-correct? Give an example from our own data.
2. How does the eval script decide a case passes? What can it not catch?
3. In plain words, how does the delay rule decide a payment is anomalous? Why overall mean and not per vendor?
4. What does "flag, don't drop" mean, and why does it matter for a data-quality report?
5. Which of your three tricky questions did the copilot get wrong, and why?
6. What would you cut from the project if you had two weeks left? (This feeds `docs/scope_lock.md`.)

## Commit and push to your branch

```bash
git status
git add docs/anomaly_review.md docs/data_quality_notes.md tests/eval_cases.json
git commit -m "Week 3: eval answers confirmed, anomaly review, data-quality notes, new eval cases"
git push -u origin <yourname>-week3
```
Then open a pull request into `main` and message Nachiket. Never commit `.env` or an API key.

## Still open from Week 2

You still owe the scored answer review from `docs/her_tasks_detailed.md` (Tasks 2, 3 and 7). Do those after today's
tasks. Task A above covers most of Task 1 and the ground-truth check.

## After you finish

1. Nachiket reads your review, adjusts the threshold or rules if you disagree, and merges your pull request.
2. The 2–3 new tricky cases become the Day 4 target: the pass rate must improve, not just feel better.
3. Both of you read `docs/scope_lock.md`, move items between "In v1" and "Out", and sign it.
