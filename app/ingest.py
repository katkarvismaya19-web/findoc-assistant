"""Ingestion: PDF -> text -> chunks -> embeddings -> Chroma index.

Run:
    python -m app.ingest --chunk-size 1000 --overlap 150 --collection findoc_1000
    python -m app.ingest --chunk-size 500  --overlap 75  --collection findoc_500

Building two collections lets evaluate.py compare chunk sizes on the same
question set, which is the experiment worth reporting.
"""
import argparse
import json
import re

from pypdf import PdfReader

from app import config
from app.text import build_chunks, clean



def load_pages(pdf_dir):
    """Yield one record per page so we keep page numbers for citation."""
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(
            f"No PDFs in {pdf_dir}. Download 25-30 RBI circulars there first."
        )
    for path in pdfs:
        try:
            reader = PdfReader(str(path))
        except Exception as exc:  # a corrupt file should not kill the run
            print(f"  ! skipping {path.name}: {exc}")
            continue
        for page_no, page in enumerate(reader.pages, start=1):
            text = clean(page.extract_text() or "")
            if len(text) < 50:  # cover pages, blank pages, pure-image scans
                continue
            yield {"source": path.name, "page": page_no, "text": text}



def main():
    # Imported here so `import app.ingest` stays cheap for the test suite.
    import chromadb
    from sentence_transformers import SentenceTransformer

    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk-size", type=int, default=1000)
    ap.add_argument("--overlap", type=int, default=150)
    ap.add_argument("--collection", default=config.COLLECTION)
    ap.add_argument("--batch", type=int, default=128)
    args = ap.parse_args()

    print(f"Reading PDFs from {config.PDF_DIR}")
    pages = list(load_pages(config.PDF_DIR))
    print(f"  {len(pages)} pages with usable text")

    chunks = build_chunks(pages, args.chunk_size, args.overlap)
    print(f"  {len(chunks)} chunks at size={args.chunk_size} overlap={args.overlap}")

    # Persist chunks as JSON. BM25 and the evaluator read this file, so the
    # keyword index and the vector index always describe the same corpus.
    chunk_path = config.CHUNKS_DIR / f"{args.collection}.json"
    chunk_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote {chunk_path}")

    print(f"Embedding with {config.EMBED_MODEL} (first run downloads the model)")
    model = SentenceTransformer(config.EMBED_MODEL)

    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    try:
        client.delete_collection(args.collection)
    except Exception:
        pass
    collection = client.create_collection(
        name=args.collection, metadata={"hnsw:space": "cosine"}
    )

    for start in range(0, len(chunks), args.batch):
        batch = chunks[start : start + args.batch]
        vectors = model.encode(
            [c["text"] for c in batch],
            show_progress_bar=False,
            normalize_embeddings=True,
        ).tolist()
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            embeddings=vectors,
            metadatas=[{"source": c["source"], "page": c["page"]} for c in batch],
        )
        print(f"  indexed {min(start + args.batch, len(chunks))}/{len(chunks)}")

    print(f"Done. Collection '{args.collection}' holds {collection.count()} chunks.")


if __name__ == "__main__":
    main()


