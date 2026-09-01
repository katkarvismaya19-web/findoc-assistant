"""Download a corpus of RBI documents into data/pdfs/.

RBI puts an unguessable hash in every PDF filename, so links cannot be
constructed - they have to be scraped from the listing pages.

    python -m scripts.fetch_corpus              # 30 master directions
    python -m scripts.fetch_corpus --limit 40
    python -m scripts.fetch_corpus --urls my_links.txt

Downloads are checked for an extractable text layer and scanned files are
discarded, because a PDF with no text contributes nothing to the index and
will silently shrink your corpus.
"""
import argparse
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "pdfs"

LISTINGS = [
    "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx",
    "https://www.rbi.org.in/Scripts/NotificationUser.aspx",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    )
}

PDF_HREF = re.compile(r'href="([^"]+?\.PDF)"', re.IGNORECASE)


def extract_pdf_links(html, base):
    """Pull absolute .PDF links out of a listing page, preserving order."""
    seen, links = set(), []
    for href in PDF_HREF.findall(html):
        url = urljoin(base, href.replace("&amp;", "&"))
        if url not in seen:
            seen.add(url)
            links.append(url)
    return links


def safe_name(url):
    """Readable filename from RBI's hash-laden URLs.

    RBI appends a long hex blob to every filename, e.g.
    MD18KYCF6E92C82E1E1419D87323E3869BC9F13.PDF -> md18kyc.pdf
    Strip the extension first, then only a trailing hex run, so the
    meaningful prefix survives.
    """
    stem = url.rstrip("/").split("/")[-1]
    stem = re.sub(r"\.PDF$", "", stem, flags=re.I)
    # The hash is exactly 32 hex chars. Matching a variable-length run would
    # eat real letters, since C, E, F etc. are valid hex - "MD18KYC" would
    # lose its C. Strip the fixed width instead.
    if len(stem) > 32 and re.fullmatch(r"[0-9A-F]{32}", stem[-32:]):
        stem = stem[:-32]
    else:
        stem = re.sub(r"[0-9A-F]{24,}$", "", stem)
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", stem).strip("._-")
    return f"{(stem[:60] or 'document').lower()}.pdf"


def has_text_layer(path, min_chars=400):
    """True if the PDF yields real text. Scanned image PDFs return almost none."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        chars = 0
        for page in reader.pages[:5]:
            chars += len(page.extract_text() or "")
            if chars >= min_chars:
                return True
        return False
    except Exception:
        return False


def gather_links(limit):
    links = []
    for listing in LISTINGS:
        if len(links) >= limit * 3:
            break
        try:
            print(f"Scanning {listing}")
            resp = requests.get(listing, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            found = extract_pdf_links(resp.text, listing)
            print(f"  found {len(found)} PDF links")
            links.extend(l for l in found if l not in links)
        except requests.RequestException as exc:
            print(f"  ! {exc}")
    return links


def download(links, limit, delay):
    OUT.mkdir(parents=True, exist_ok=True)
    kept = 0

    for url in links:
        if kept >= limit:
            break
        dest = OUT / safe_name(url)
        if dest.exists():
            print(f"  = {dest.name} (already have it)")
            kept += 1
            continue

        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"  ! {url.split('/')[-1][:40]}: {exc}")
            continue

        if not resp.content.startswith(b"%PDF"):
            print(f"  ! {dest.name}: not a PDF, skipping")
            continue

        dest.write_bytes(resp.content)

        if not has_text_layer(dest):
            dest.unlink()
            print(f"  x {dest.name}: scanned image, no text layer - discarded")
            continue

        kept += 1
        size = len(resp.content) / 1024
        print(f"  + {dest.name} ({size:.0f} KB)  [{kept}/{limit}]")
        time.sleep(delay)  # be polite to a public server

    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--urls", help="text file of PDF URLs, one per line")
    args = ap.parse_args()

    if args.urls:
        links = [
            l.strip()
            for l in Path(args.urls).read_text().splitlines()
            if l.strip() and not l.startswith("#")
        ]
        print(f"Using {len(links)} URLs from {args.urls}")
    else:
        links = gather_links(args.limit)

    if not links:
        print(
            "\nNo links found. RBI may have changed their page layout.\n"
            "Fallback: open https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx,\n"
            "save PDF links into links.txt, then run:\n"
            "  python -m scripts.fetch_corpus --urls links.txt"
        )
        sys.exit(1)

    print(f"\nDownloading up to {args.limit} documents into {OUT}\n")
    kept = download(links, args.limit, args.delay)

    print(f"\n{kept} usable PDFs in {OUT}")
    if kept < 10:
        print("That is a thin corpus. Re-run with a higher --limit.")
    else:
        print("Next: python -m app.ingest --chunk-size 1000 --overlap 150 "
              "--collection findoc_1000")


if __name__ == "__main__":
    main()
