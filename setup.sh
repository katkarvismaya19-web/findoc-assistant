#!/usr/bin/env bash
# One-command setup: environment, corpus, both indexes, server.
# Usage:  bash setup.sh
set -e

say() { printf "\n\033[1m%s\033[0m\n" "$1"; }

say "1/5  Creating virtual environment"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

say "2/5  Installing dependencies (pulls PyTorch, takes a few minutes)"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  say "Created .env - add your Groq key to it now (console.groq.com)"
  say "Retrieval works without it; only the written answer needs a key."
fi

say "3/5  Verifying the code before adding data"
python -m pytest tests/ -q

say "4/5  Downloading RBI documents"
if [ -z "$(ls -A data/pdfs/*.pdf 2>/dev/null)" ]; then
  python -m scripts.fetch_corpus --limit 30
else
  echo "PDFs already present, skipping download."
fi

say "5/5  Building both indexes"
python -m app.ingest --chunk-size 1000 --overlap 150 --collection findoc_1000
python -m app.ingest --chunk-size 500  --overlap 75  --collection findoc_500

say "Setup complete."
cat <<'MSG'

Next, in order:

  1. Start the app and try some questions:
       source .venv/bin/activate
       uvicorn app.main:app --reload --port 8000
       open http://localhost:8000

  2. Write your 20 evaluation questions (the helper finds the good pages):
       python -m scripts.label_helper

  3. Measure retrieval and get your resume number:
       python -m eval.evaluate --collections findoc_1000 findoc_500 --k 3 --show-misses

  4. Deploy - see DEPLOY.md

MSG
