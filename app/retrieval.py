"""Three retrieval strategies over the same corpus, so they can be compared.

dense  - semantic similarity via sentence-transformer embeddings in Chroma
bm25   - lexical keyword scoring, good at exact identifiers
hybrid - Reciprocal Rank Fusion over both ranked lists

The interesting result is usually that hybrid wins on questions containing
circular numbers or defined terms, because embeddings blur exact tokens.
"""
import json
from functools import lru_cache

from rank_bm25 import BM25Okapi

from app import config
from app.text import reciprocal_rank_fusion, tokenize


@lru_cache(maxsize=4)
def _load(collection_name: str):
    """Load the model, the Chroma collection and the BM25 index once."""
    chunk_path = config.CHUNKS_DIR / f"{collection_name}.json"
    if not chunk_path.exists():
        raise FileNotFoundError(
            f"{chunk_path} missing. Run: python -m app.ingest --collection {collection_name}"
        )
    chunks = json.loads(chunk_path.read_text(encoding="utf-8"))

    import chromadb
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(config.EMBED_MODEL)
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    collection = client.get_collection(collection_name)

    bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])
    by_id = {c["id"]: c for c in chunks}
    return model, collection, bm25, chunks, by_id


def dense_search(query, k=config.DEFAULT_K, collection_name=None):
    name = collection_name or config.COLLECTION
    model, collection, _, _, by_id = _load(name)
    vector = model.encode([query], normalize_embeddings=True).tolist()
    res = collection.query(query_embeddings=vector, n_results=k)
    out = []
    for cid, dist in zip(res["ids"][0], res["distances"][0]):
        chunk = dict(by_id[cid])
        chunk["score"] = 1.0 - dist  # cosine distance -> similarity
        out.append(chunk)
    return out


def bm25_search(query, k=config.DEFAULT_K, collection_name=None):
    name = collection_name or config.COLLECTION
    _, _, bm25, chunks, _ = _load(name)
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    out = []
    for i in ranked:
        chunk = dict(chunks[i])
        chunk["score"] = float(scores[i])
        out.append(chunk)
    return out


def hybrid_search(query, k=config.DEFAULT_K, collection_name=None, pool=20):
    """Reciprocal Rank Fusion.

    Each list contributes 1/(RRF_K + rank) per document. Using ranks rather
    than raw scores avoids having to normalise a cosine similarity against a
    BM25 score, which are not on comparable scales.
    """
    dense = dense_search(query, k=pool, collection_name=collection_name)
    lexical = bm25_search(query, k=pool, collection_name=collection_name)

    scores = reciprocal_rank_fusion(
        [[c["id"] for c in dense], [c["id"] for c in lexical]], config.RRF_K
    )
    by_id = {c["id"]: c for c in dense + lexical}
    fused = [{**by_id[cid], "score": s} for cid, s in scores.items()]
    return sorted(fused, key=lambda c: c["score"], reverse=True)[:k]


STRATEGIES = {
    "dense": dense_search,
    "bm25": bm25_search,
    "hybrid": hybrid_search,
}


def search(query, strategy="hybrid", k=config.DEFAULT_K, collection_name=None):
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {list(STRATEGIES)}")
    return STRATEGIES[strategy](query, k=k, collection_name=collection_name)

