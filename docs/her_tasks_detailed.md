# Your tasks — Week 2, Day 4 and Day 5 (step by step)

You will work in a **GitHub Codespace** on your **own branch**, so nothing you do can break `main`.
Your job in one sentence: check whether the copilot's answers are actually correct against the data,
score them, and write down what is still broken.

Replace `<yourname>` everywhere below with your first name in lowercase (example: `rishu`).

---

## Part 0 — Set up (15 min, once)

1. Open the repo on GitHub → green **Code** button → **Codespaces** tab → **Create codespace on main**.
   Wait until the terminal appears. Dependencies install automatically.
2. Add the API key as a Codespaces secret (so it is never committed):
   GitHub → your profile picture → **Settings** → **Codespaces** → **New secret** →
   name `GROQ_API_KEY`, value = the key Nachiket sent you, repository access = `sap-copilot`.
   Then rebuild the Codespace (Command Palette → "Codespaces: Rebuild Container"), or close and reopen it.
3. In the terminal, create your branch:
   ```bash
   git checkout -b <yourname>
   ```
4. Check everything works:
   ```bash
   python -m pytest -q          # expect: 30 passed
   python -m src.app "Which vendors had delayed payments this month?"
   ```
   If the second command prints an answer naming two vendors, you are set up. If it says
   `Set GROQ_API_KEY`, redo step 2.

> Note: "this month" and "this week" are resolved against the fixed date **2026-09-30**
> (the mock data ends in September 2026). Do not change this.

---

## Task 1 — Get the ground truth (10 min)

**What:** The copilot's answers must be compared against numbers that did **not** come from the LLM.
`tests/check_answers.py` computes the correct answer to all 5 questions straight from the CSVs with pandas.

**Do:**
```bash
python -m tests.check_answers
```
Skim each block against the CSVs in `data/mock_sap/`. You know the data best, so check that the logic
matches what the question means (e.g. Q1 = delayed payments whose payment date falls in September 2026).

**File you may need to edit:** `tests/check_answers.py` — only if you find the *checker* is wrong
(for example, you disagree with how it defines "delayed"). Fix it first, because everything else is scored against it.

---

## Task 2 — Score the copilot's answers (20 min)

**What:** Run the 5 seed questions and decide, for each, whether it is right.

**Do:**
```bash
python -m src.app --seed
```
This rewrites **`docs/answer_review.md`** with, for each question, the answer, the SQL that ran, and the rows returned.

**File you edit: `docs/answer_review.md`** — fill in the table at the top, one row per question:

| Column | Mark it OK if... |
|---|---|
| SQL ok? | right tables, joins, date filter, status value, aggregation |
| Answer ok? | every number and name matches Task 1 (a 0.01 rounding difference is fine) |
| Phrasing ok? | clear, nothing invented, missing values (NULL) mentioned, no extra metrics nobody asked for |
| Overall | **Right**, **Partial**, or **Wrong** |

In the **Note** column say exactly what differs, e.g. *"Q4: includes on-time payments in the average"*.

Three things can fail independently: a wrong SQL gives a wrong answer, but a correct SQL can still be
phrased badly. Score each separately.

**Important:** the LLM is not perfectly repeatable. Run `--seed` **twice** and note any question whose
answer changes between runs. `--seed` **overwrites** `docs/answer_review.md`, so fill in your scores
and save a copy of the file (or commit it) *before* running it a second time.

---

## Task 3 — Find schema-documentation gaps (20 min)

**What:** When the SQL looks fine but the answer is still wrong, the cause is usually an ambiguous column,
not a bad prompt. Decide what the data *should* mean.

**Questions to settle** (write your decisions into the file below):
1. A `Scheduled` payment has no `payment_date`. Is it "delayed" if its `due_date` has passed?
2. A `Pending` PO has a `delivery_date` in the past. Is it late, or is that just the planned date?
3. Should "category" ever mean `vendors.vendor_category`? (Current rule: no, it means `purchase_orders.category`.)

**File you edit: `docs/architecture.md`** — add your decisions as one-line rules under the section about
prompt rules. Then send Nachiket each rule; he pastes it into `SQL_RULES` in `src/retrieval/text_to_sql.py`.
(You do **not** edit `text_to_sql.py` — that is Nachiket's file, to avoid merge conflicts.)

---

## Task 4 — Add harder test questions (15 min, optional if short on time)

**What:** Teach the automated eval a few more questions, so wrong answers are caught without manual checking.

**File you edit: `tests/eval_seed_questions.py`** — add these entries at the end of the `CASES` list
(before the closing `]`):
```python
    ("How many Rejected purchase orders are there?",
     "SELECT COUNT(*) FROM purchase_orders WHERE status = 'Rejected'"),
    ("Which paid payments have no amount recorded?",
     "SELECT payment_id FROM payments WHERE status = 'Paid' AND amount IS NULL"),
    ("What is the total value of Closed purchase orders?",
     "SELECT SUM(amount) FROM purchase_orders WHERE status = 'Closed'"),
```
Run it:
```bash
python -m tests.eval_seed_questions
```
Every `FAIL` goes on your broken list (Task 6). Add 1–2 questions of your own if you can think of a tricky one.

---

## Task 5 — Demo run (with Nachiket, 30 min call)

Run the 5 seed questions **live**, not from earlier output:
```bash
python -m src.app --seed
```
Then ask two questions of your own:
```bash
python -m src.app "your question here"
```
Write down anything surprising.

---

## Task 6 — The top-5 broken / missing list (15 min)

**File you edit: `docs/week2_top5_broken.md`** — it already has 5 candidates written by Nachiket.
Keep, edit or replace them using what **you** actually saw. Each row must be specific:
what breaks, an example input, why it matters for Week 3 (anomaly detection). Bad: "data handling issues".
Good: "vendor names containing an apostrophe break the SQL". In the last column mark the 2–3 that
matter most for Week 3 with a ✅.

---

## Task 7 — Check the mock data hasn't drifted (10 min)

**What:** After Day 2's additions, confirm the data still matches its documentation.
```bash
python -m pytest -q
```
Must be all green. Then compare `data/mock_sap/README.md` against the CSVs:
row counts per table, vendor IDs consistent across the three files, all dates `YYYY-MM-DD`, the
3 outliers (PO00148, PO00020, PO00081) and 2 duplicates (PO00221, PO00222) still present, and the 2 `Paid`
payments with a NULL amount (PMT00012, PMT00113). If the README and CSV disagree, fix whichever is wrong
and say which in your commit message.

**File you may edit:** `data/mock_sap/README.md` (or the CSVs, only if you are sure).

---

## Part 8 — Commit and push to your branch

Only these files should change: `docs/answer_review.md`, `docs/architecture.md`,
`docs/week2_top5_broken.md`, and optionally `tests/eval_seed_questions.py`,
`tests/check_answers.py`, `data/mock_sap/README.md`. Check with:
```bash
git status
```
Then:
```bash
git add docs/answer_review.md docs/architecture.md docs/week2_top5_broken.md
git add tests/eval_seed_questions.py tests/check_answers.py data/mock_sap/README.md   # only the ones you changed
git commit -m "Week 2 Day 4-5: scored answer review, top-5 broken list, data check"
git push -u origin <yourname>
```
Never commit `.env` or an API key (`.env` is in `.gitignore`; the Codespaces secret keeps the key out of the repo).

If `git push` is refused for permissions, tell Nachiket — you need write access as a collaborator.

Finally, open GitHub → **Pull requests** → **New pull request** → base `main`, compare `<yourname>` →
title "Week 2 Day 4-5: scoring and top-5 list" → **Create pull request**, and message Nachiket.

---

## What happens after you finish

1. Nachiket reads your scored `docs/answer_review.md`, works through the Wrong/Partial rows worst-first,
   and pastes your rules from Task 3 into the SQL prompt.
2. He re-runs `--seed` to confirm the target: **4 of 5 fully correct, and the 5th explainable**.
3. He merges your pull request into `main`, commits his fixes, and tags the release `v0.1`.
4. Together you pick the 2–3 items from your top-5 list that Week 3 builds on — the anomaly-detection feature.

## If something goes wrong

| Problem | Fix |
|---|---|
| `Set GROQ_API_KEY before calling the LLM layer` | Redo the Codespaces secret (Part 0, step 2), then rebuild/reopen the Codespace |
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| Q1 returns no vendors | Something changed the as-of date; make sure `COPILOT_TODAY` is unset |
| An answer changes between runs | Normal for an LLM; record it in the Note column |
| Merge conflict on a file | Stop and message Nachiket — don't force-push |
