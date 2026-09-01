"""Speed up building eval/questions.json.

Writing 20 labelled questions by hand is the slowest part of this project.
Most of that time goes on hunting for a page worth asking about, not on
writing the question. This finds the good pages for you.

    python -m scripts.label_helper              # interactive
    python -m scripts.label_helper --list       # just show candidate pages

Pages are ranked by how many concrete, checkable facts they contain -
numbers, time periods, percentages, circular references - because a page
stating "KYC shall be updated once every two years" makes a far better
evaluation question than a page of definitions.

You still write the questions. That judgement is the part that matters, and
it is what you will be asked about in an interview.
"""
import argparse
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
OUT = ROOT / "eval" / "questions.json"

# Signals that a page states something specific enough to ask about.
SIGNALS = [
    (re.compile(r"\b(?:once|at least once|every)\s+(?:in\s+)?\w+\s+(?:year|month|day)", re.I), 3),
    (re.compile(r"\b\d+\s*(?:days?|months?|years?|hours?)\b", re.I), 2),
    (re.compile(r"\b\d+(?:\.\d+)?\s*(?:per cent|percent|%)", re.I), 2),
    (re.compile(r"\bRs\.?\s?[\d,]+|\b(?:lakh|crore)\b", re.I), 2),
    (re.compile(r"\b[A-Z]{2,4}\.[A-Z]{2,4}\.[A-Z]{2,4}\.?\s?\d+", re.I), 3),  # circular ids
    (re.compile(r"\bshall\s+(?:be|not|ensure|carry|maintain|report)", re.I), 1),
    (re.compile(r"\bwithin\s+(?:a\s+period\s+of\s+)?\w+\s+(?:days?|months?)", re.I), 3),
]


def score_page(text):
    return sum(weight * len(pattern.findall(text)) for pattern, weight in SIGNALS)


def snippet(text, width=340):
    """The densest-looking sentence run on the page."""
    text = re.sub(r"\s+", " ", text).strip()
    best, best_score = text[:width], -1
    for match in re.finditer(r"[^.]{60,}?\.", text):
        chunk = match.group(0)
        s = score_page(chunk)
        if s > best_score:
            best, best_score = chunk.strip(), s
    return best[:width]


def candidates(min_score=6, per_file=3):
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(
            f"No PDFs in {PDF_DIR}. Run: python -m scripts.fetch_corpus"
        )

    results = []
    for path in pdfs:
        try:
            reader = PdfReader(str(path))
        except Exception as exc:
            print(f"! skipping {path.name}: {exc}")
            continue

        pages = []
        for page_no, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if len(text) < 300:
                continue
            score = score_page(text)
            if score >= min_score:
                pages.append(
                    {
                        "source": path.name,
                        "page": page_no,
                        "score": score,
                        "snippet": snippet(text),
                    }
                )
        pages.sort(key=lambda p: p["score"], reverse=True)
        results.extend(pages[:per_file])

    results.sort(key=lambda p: p["score"], reverse=True)
    return results


TYPES = {
    "1": "semantic  - ask in plain words the document does not use",
    "2": "identifier - include an exact circular number or defined term",
    "3": "paraphrase - deliberately different vocabulary from the page",
}


def interactive(cands, target):
    print(
        "\nFor each page: type a question whose answer is on it, or press\n"
        "Enter to skip. Aim for a mix:\n"
    )
    for key, desc in TYPES.items():
        print(f"  {key}. {desc}")
    print(
        "\nThat mix is what makes the hybrid-vs-dense comparison meaningful -\n"
        "identifier questions are where BM25 wins, paraphrase questions are\n"
        "where dense wins. Ctrl-C saves and exits.\n"
    )

    written = []
    try:
        for cand in cands:
            if len(written) >= target:
                break
            print("-" * 72)
            print(f"{cand['source']}  page {cand['page']}   [{len(written)}/{target} done]")
            print(f"  {cand['snippet']}\n")
            q = input("  Question (Enter to skip): ").strip()
            if not q:
                continue
            written.append(
                {
                    "question": q,
                    "expected_source": cand["source"],
                    "expected_page": cand["page"],
                }
            )
    except (KeyboardInterrupt, EOFError):
        print("\n\nStopping early.")

    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="show candidates, write nothing")
    ap.add_argument("--target", type=int, default=20)
    ap.add_argument("--min-score", type=int, default=6)
    args = ap.parse_args()

    cands = candidates(min_score=args.min_score)
    print(f"Found {len(cands)} fact-dense pages across the corpus.")

    if args.list:
        for c in cands[:60]:
            print(f"\n[{c['score']:>3}] {c['source']} p.{c['page']}\n     {c['snippet'][:200]}")
        return

    written = interactive(cands, args.target)

    if not written:
        print("Nothing written.")
        return

    if OUT.exists():
        existing = json.loads(OUT.read_text())
        existing = [q for q in existing if "_comment" not in q]
        if existing:
            keep = input(f"\n{OUT.name} has {len(existing)} questions. Keep them? [y/N] ")
            if keep.lower().startswith("y"):
                written = existing + written

    OUT.write_text(json.dumps(written, indent=2, ensure_ascii=False))
    print(f"\nWrote {len(written)} questions to {OUT}")
    if len(written) < 15:
        print("Under 15 questions makes the metrics noisy. Try to reach 20.")
    print("\nNext: python -m eval.evaluate --collections findoc_1000 findoc_500 --k 3")


if __name__ == "__main__":
    main()
