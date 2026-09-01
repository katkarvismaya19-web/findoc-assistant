"""Central configuration. Everything is overridable via environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

PDF_DIR = ROOT / os.getenv("PDF_DIR", "data/pdfs")
CHROMA_DIR = ROOT / os.getenv("CHROMA_DIR", "data/chroma")
CHUNKS_DIR = ROOT / os.getenv("CHUNKS_DIR", "data/chunks")

COLLECTION = os.getenv("COLLECTION", "findoc_1000")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Default retrieval settings
DEFAULT_K = 3
RRF_K = 60  # smoothing constant for Reciprocal Rank Fusion

CHROMA_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
