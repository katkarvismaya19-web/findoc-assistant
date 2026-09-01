"""Pure text helpers: cleaning, chunking, tokenization.

Kept free of chromadb / sentence-transformers imports on purpose, so the unit
tests can exercise this logic without loading a 2 GB model stack.
"""
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

_TOKEN = re.compile(r"[a-z0-9]+")


def clean(text: str) -> str:
    """Collapse the whitespace noise that PDF extraction leaves behind."""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tokenize(text: str):
    """Lowercase alphanumeric tokens. Splits 'DOR.AUT.REC-12' into its parts,
    which is what lets BM25 match on regulatory identifiers."""
    return _TOKEN.findall(text.lower())


def build_chunks(pages, chunk_size, overlap):
    """Split page records into overlapping chunks, preserving source and page."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for page in pages:
        for i, piece in enumerate(splitter.split_text(page["text"])):
            if len(piece.strip()) < 40:
                continue
            chunks.append(
                {
                    "id": f"{page['source']}::p{page['page']}::c{i}",
                    "text": piece.strip(),
                    "source": page["source"],
                    "page": page["page"],
                }
            )
    return chunks


def reciprocal_rank_fusion(ranked_lists, rrf_k=60):
    """Fuse ranked lists of chunk ids into a single score map.

    Uses ranks rather than raw scores, which avoids having to normalise a
    cosine similarity against a BM25 score - they are not on comparable scales.
    """
    scores = {}
    for lst in ranked_lists:
        for rank, chunk_id in enumerate(lst, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
    return scores
