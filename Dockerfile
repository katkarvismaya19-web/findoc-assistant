# Works locally and on Hugging Face Spaces.
# Spaces routes traffic to port 7860, so that is the default here.
FROM python:3.11-slim

# Spaces runs containers as a non-root user; create it and own the app dir.
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HF_HOME=/home/user/app/data/hf_cache \
    SENTENCE_TRANSFORMERS_HOME=/home/user/app/data/hf_cache

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user app/ ./app/
COPY --chown=user eval/ ./eval/
COPY --chown=user tests/ ./tests/
COPY --chown=user data/ ./data/

# Bake the embedding model into the image so the first request is not a
# multi-minute download on a cold Space.
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

RUN chown -R user:user /home/user/app
USER user

EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
