---
title: FinDoc Assistant
emoji: 📄
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# FinDoc Assistant

Hybrid retrieval-augmented generation over financial regulatory documents.

Ask a question about a corpus of RBI circulars and master directions; get an
answer grounded in retrieved passages, with citations back to the source file
and page.

The point of the project is not the chatbot. It is measuring whether
retrieval actually finds the right passage, which is the part of a RAG
system that fails silently. A fluent answer built on the wrong passage looks
correct and is not.

---

## Architecture

```
PDFs ──> parse (pypdf) ──> clean ──> chunk (RecursiveCharacterTextSplitter)
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
          embed (all-MiniLM-L6-v2)                    tokenize
                        │                                   │
                        ▼                                   ▼
              ChromaDB vector index                  BM25 keyword index
                        │                                   │
                        └──────────► RRF fusion ◄───────────┘
                                          │
                                          ▼
                            top-k passages ──> LLM (Groq)
                                          │
                                          ▼
                              FastAPI /ask ──> answer + citations
```

Two indexes are built over the identical chunk list, so the comparison
between them is fair.

### Why hybrid

Dense embeddings capture meaning but blur exact tokens. A question naming
`DOR.AUT.REC.12/24.01.041/2023-24` is poorly served by semantic similarity,
because that identifier means nothing in embedding space. BM25 handles it
exactly, and is in turn useless when the question is worded entirely
differently from the document. Fusing the two ranked lists with Reciprocal
Rank Fusion covers both failure modes.

RRF combines ranks, not scores, which sidesteps having to normalise a
cosine similarity against a BM25 score — they are not on comparable scales.

---

## Setup

A demo corpus of ten documents ships in `data/pdfs/`, so there is nothing to
download before the first run.

**Windows** — double-click `setup.bat`. It builds the environment, the
indexes, and starts the app. After the first run use `run.bat` to start it and
`evaluate.bat` to measure retrieval.

**Mac / Linux**

```bash
bash setup.sh
```

Retrieval works without an API key. Add a free Groq key (console.groq.com) to
`.env` when you want written answers rather than just ranked passages.

### About the demo corpus

The bundled documents are synthetic. They imitate the structure of Indian
banking circulars — numbered clauses, defined terms, circular references,
stated time periods — so the retrieval problem is realistic, but no clause is
real regulation.

Before deploying publicly, swap in real documents:

```bash
python -m scripts.fetch_corpus --limit 30
python -m app.ingest --chunk-size 1000 --overlap 150 --collection findoc_1000
python -m app.ingest --chunk-size 500  --overlap 75  --collection findoc_500
python -m scripts.label_helper     # relabel the question set for the new corpus
```

<details>
<summary>Manual setup</summary>

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

python -m app.ingest --chunk-size 1000 --overlap 150 --collection findoc_1000
python -m app.ingest --chunk-size 500  --overlap 75  --collection findoc_500
```

</details>

`scripts/fetch_corpus.py` scrapes RBI's master directions listing for real
documents, since the PDF URLs contain unguessable hashes and cannot be
constructed. Downloads without an extractable text layer are discarded — a
scanned PDF contributes nothing to the index and would silently shrink the
corpus.

Two collections at different chunk sizes let the evaluator compare them on
the same questions.

---

## Run it

```bash
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 for the web interface, or
http://localhost:8000/docs for the API explorer.

The interface shows the answer beside the passages it was built from, with the
retrieval score for each. Switching between hybrid, dense and BM25 on the same
question shows how the ranking changes — which is the whole argument for
hybrid retrieval, made visible.

```bash
curl -X POST localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"How often must KYC be updated for high risk customers?","strategy":"hybrid"}'
```

`/search` runs retrieval only, with no LLM call — useful for inspecting what
the index returns.

---

## Evaluate

`eval/questions.json` ships with 25 questions labelled against the demo
corpus, so evaluation runs immediately:

```bash
python -m eval.evaluate --collections findoc_1000 findoc_500 --k 3 --show-misses
```

Measured output is in Results below.

When you replace the demo corpus with real documents, relabel the question
set. This helper ranks pages by how many concrete, checkable facts they
contain and walks you through them, which removes the hunting but leaves the
judgement to you:

```bash
python -m scripts.label_helper
```

A chunk counts as a hit when it comes from the expected file and lands within
one page of the expected page, since chunk boundaries do not align with pages.

---

## Results

Demo corpus (synthetic), 25 questions, k=3, page tolerance 1.

**Chunk size 1000** (2,434 chunks)

| Strategy | Recall@3 | MRR |
|---|---|---|
| Dense only | 0.680 | 0.680 |
| BM25 only | 0.920 | 0.920 |
| Hybrid (RRF) | 0.880 | 0.807 |

**Chunk size 500** (4,388 chunks)

| Strategy | Recall@3 | MRR |
|---|---|---|
| Dense only | 0.840 | 0.840 |
| BM25 only | 0.880 | 0.860 |
| Hybrid (RRF) | 0.880 | 0.833 |

**Chunk size 1000 vs 500.** 500 wins on the metric that matters here — it
lifts dense recall from 0.680 to 0.840. Smaller chunks dilute less, so a
single embedding stays closer to one fact instead of averaging several. At
1000 the dense index loses ground that BM25 has to cover.

**Hybrid does not win on this corpus.** BM25 alone beats it at chunk size
1000 (0.920 vs 0.880). The demo documents are synthetic and the questions
were written against that same text, so question and passage share vocabulary
far more than they would with real regulation — near-ideal conditions for
exact keyword matching. RRF pulls in dense results that rank lower, costing a
couple of hits. The honest read: hybrid's value is insurance against
paraphrased questions, and this corpus does not contain any. Re-running on the
real RBI corpus is the test that would actually settle it.

**Where hybrid still misses.** The remaining failures are paraphrases with no
shared tokens — "ignores repeated requests to refresh their paperwork" for
what the document calls periodic updation non-compliance, and penetration
testing frequency where the text uses different phrasing. These are dense's
job, and dense is not ranking them top-3 either. Sub-500 chunks or a reranker
would be the next thing to try.

---

## Tests

```bash
pytest tests/ -q
```

Covers cleaning, chunking, tokenization and fusion — the pure logic, with no
model download required.

## Docker

```bash
docker compose up --build
```

Then open http://localhost:8000. Mounts `data/` so the index and model cache
persist across restarts.

## Deploying

See `DEPLOY.md` for Hugging Face Spaces deployment, and for why
Netlify cannot host this backend.

---

## Layout

```
setup.bat        Windows: one-click setup and launch
run.bat          Windows: start the app
evaluate.bat     Windows: run the evaluation
setup.sh         Mac/Linux equivalent of setup.bat
scripts/
  make_demo_corpus.py  regenerate the bundled sample documents
  fetch_corpus.py      scrape and download real RBI documents
  label_helper.py      find fact-dense pages for the question set
app/
  config.py      settings from environment
  static/        single-page web interface
  text.py        cleaning, chunking, tokenization, RRF  (no heavy deps)
  ingest.py      PDF -> chunks -> embeddings -> Chroma
  retrieval.py   dense / bm25 / hybrid strategies
  llm.py         grounded answer layer
  main.py        FastAPI service
eval/
  questions.json labelled question set
  evaluate.py    Recall@k and MRR across strategies
tests/
```

## Limitations

- Scanned PDFs without a text layer are skipped; OCR would be needed.
- The page-tolerance hit criterion is approximate. Chunk-level labelling
  would be stricter but far slower to produce by hand.
- Twenty-five questions is a small sample. Differences of a few points
  between strategies are inside the noise.
