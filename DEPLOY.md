# Deploying FinDoc Assistant

## Why not Netlify

Netlify hosts static files and short-lived serverless functions. This app
needs:

| Requirement | Netlify limit |
|---|---|
| PyTorch + embedding model, ~2 GB | Functions cap at 50 MB zipped |
| Model load takes ~10 s cold | Functions time out at 10 s |
| ChromaDB persisted on disk | No persistent filesystem |

So Netlify cannot run the backend. It is the wrong shape of host for a
model-serving service, not a matter of configuration.

**Hugging Face Spaces** is the right fit: free, Docker-native, no card
required, and it is where people go to look at ML projects. A recruiter can
click your link and immediately use the thing.

---

## Deploy to Hugging Face Spaces

### 1. Create the Space

Sign up at huggingface.co, then **New Space**:

- Name: `findoc-assistant`
- License: MIT
- SDK: **Docker** (not Gradio or Streamlit)
- Hardware: CPU basic, free
- Visibility: Public

### 2. Add the Space header to README.md

Spaces reads configuration from YAML frontmatter. Put this at the very top of
`README.md`, before the title:

```yaml
---
title: FinDoc Assistant
emoji: 📄
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---
```

### 3. Set your API key as a secret

In the Space: **Settings → Variables and secrets → New secret**

- Name: `GROQ_API_KEY`
- Value: your key from console.groq.com

Never commit the key. `.env` is already gitignored.

### 4. Commit the index, not the PDFs

The Space has no way to run ingestion, so build the index locally and commit
the result:

```bash
python -m app.ingest --chunk-size 1000 --overlap 150 --collection findoc_1000
```

Then allow the index files through `.gitignore` by removing these two lines:

```
data/chroma/
data/chunks/
```

The index is typically 20–60 MB for 30 documents, which is fine for git. Keep
`data/pdfs/*.pdf` ignored — the index holds the text you need, and the PDFs
would bloat the repo.

If your index exceeds 100 MB, use Git LFS:

```bash
git lfs install
git lfs track "data/chroma/**"
git add .gitattributes
```

### 5. Push

```bash
git remote add space https://huggingface.co/spaces/<your-username>/findoc-assistant
git add -A
git commit -m "Deploy FinDoc Assistant"
git push space main
```

The build takes 5–10 minutes on the first push, mostly installing PyTorch and
baking in the embedding model. Watch the **Logs** tab. When it finishes your
app is live at:

```
https://huggingface.co/spaces/<your-username>/findoc-assistant
```

Put that URL in your resume header next to your GitHub link.

---

## If you still want a Netlify URL

You can split the app: the static page on Netlify, the API on Spaces.

1. Copy `app/static/index.html` into a new `frontend/` directory.
2. Change each `fetch("/ask")` to your full Space URL:
   `fetch("https://<user>-findoc-assistant.hf.space/ask")`
3. Add CORS to `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-site.netlify.app"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

4. Add `netlify.toml`:

```toml
[build]
  publish = "frontend"
```

5. Drag the `frontend` folder onto app.netlify.com/drop.

This works, but it is two deployments to maintain for one project. Unless you
specifically want a custom domain, the single Space is the better answer.

---

## Other hosts that work

| Host | Free tier | Notes |
|---|---|---|
| Hugging Face Spaces | Yes, no card | Best fit; sleeps when idle |
| Render | Yes, no card | 512 MB RAM is tight for PyTorch |
| Railway | Trial credit | Fast, needs card after trial |
| Fly.io | Small allowance | More configuration |

---

## Cold starts

Free Spaces sleep after ~48 hours idle and take 30–60 seconds to wake. The UI
already handles this — a failed request shows "The service may still be
starting up." Before an interview, open your Space once to warm it.
