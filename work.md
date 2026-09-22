# Day 2 Walkthrough Notes — LLM Calls, Embeddings vs. Text-to-SQL, and Why RAG Isn't the Tool Here

These are the notes for the "You" walkthrough on Day 2 (~20 min). Written to
be either talked through live or sent to her to read directly.

---

## 1. What an LLM API call actually looks like

Stripped down, every call to an LLM API (Anthropic, Groq, Gemini — doesn't
matter which) is the same shape:

```json
POST /v1/messages
{
  "model": "some-model-name",
  "messages": [
    { "role": "user", "content": "What were total Q3 purchase orders by category?" }
  ],
  "system": "You are a SQL generator for a Purchase Orders database...",
  "max_tokens": 500
}
```

And the response:

```json
{
  "content": [
    { "type": "text", "text": "SELECT category, SUM(amount) FROM purchase_orders WHERE ..." }
  ]
}
```

A few things worth landing explicitly:

- **The model has no memory between calls.** Every call is stateless — if
  you want conversation history or context, *you* resend it every time as
  part of `messages`.
- **`system` is where instructions/constraints live** — e.g. "only generate
  read-only SELECT statements," "here is the schema," "respond in JSON
  only." This is where most of the actual engineering effort goes: not the
  API call itself, but what you put in front of the model.
- **The model doesn't touch the database.** It only ever sees text (the
  schema description + the question) and returns text (a SQL string). Our
  code is what actually runs the query. This matters for the RAG discussion
  below — the LLM is a translator, not an executor.
- **Cost/latency scale with tokens**, not "how hard the question is." A
  short question against a well-described schema is cheap and fast
  regardless of how complex the underlying data is.

For SAP Copilot specifically: every question costs **at most two calls** —
one to turn the question into SQL, one to turn the SQL result into a
natural-language answer. No agent loop, no unbounded tool-calling.

---

## 2. Embeddings vs. text-to-SQL

These solve different problems and it's easy to conflate them because both
show up under "AI + your data."

**Embeddings (→ semantic search / RAG)**
- Turn a chunk of text into a vector (a list of numbers) that captures its
  *meaning*.
- Similar meaning → vectors that are close together in that vector space.
- To answer a question, you embed the question too, then find the
  stored chunks whose vectors are closest, and hand those chunks to the LLM
  as context ("here's some relevant text, now answer the question").
- This is fundamentally a **fuzzy, similarity-based lookup** — it's built
  for unstructured text (documents, policies, support tickets, emails)
  where "relevant" is a matter of degree.

**Text-to-SQL**
- The LLM never looks at the data itself. It looks at a **schema
  description** (table names, column names, types) and the question, and
  produces an exact query.
- The query then runs against the real database and returns **exact,
  correct rows** — not "the closest match."
- This is built for **structured, tabular data** where questions have a
  precise, computable answer ("sum this," "filter to this," "group by
  that") rather than a fuzzy one.

The one-line distinction worth planting: **embeddings retrieve relevant
text; text-to-SQL computes an exact answer.** A PO table doesn't have
"relevant" rows waiting to be found by similarity — it has rows that either
do or don't match `category = 'IT Hardware' AND po_date BETWEEN ...`.

---

## 3. Why RAG is (usually) the wrong tool for structured tables

This is the idea to plant clearly, since "just use RAG" is the default
reach for anyone who's only seen the document-Q&A use case.

**What breaks if you use RAG on a table like `purchase_orders`:**

- **Aggregation questions fail outright.** "What's the average payment
  delay by vendor?" has no single "chunk" that contains the answer —
  it requires computing over *all* matching rows. Embedding-based
  retrieval returns a handful of similar-looking rows, not a full,
  correct aggregate.
- **Exactness matters and similarity doesn't guarantee it.** "Show me PO
  above ₹1,00,000" needs every row above that threshold, not the rows
  whose *text* happens to look similar to the question. A vector search
  has no concept of "greater than."
- **Rows aren't really "text."** Embedding a row like `PO00042, V013, IT
  Hardware, 2026-06-15, 203061.54, Approved` throws away the structure
  (types, relationships, filterable fields) that makes the data useful in
  the first place — you're forcing structured data through a tool built
  for prose.
- **Text-to-SQL gets all of this for free** because the database engine
  already knows how to filter, join, and aggregate correctly — the LLM's
  only job is to generate the right query, not to "retrieve" the answer
  itself.

**When RAG *would* make sense for this project (for contrast, so the line
is clear):** if we later added unstructured content — vendor contract PDFs,
policy documents, email threads about a dispute — semantic search over
*that* content would be the right tool. It's not that RAG is bad, it's that
it's answering a different kind of question than "sum this column filtered
by that condition."

**The framing to land by the end of this walkthrough:** SAP Copilot is
closer to **structured retrieval / text-to-SQL** than classic RAG, because
every seed question (see `docs/seed_questions.md`) is really "filter,
aggregate, or join over exact fields" — not "find text similar to this
question."

---

