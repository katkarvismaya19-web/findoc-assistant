from pypdf import PdfReader
from pathlib import Path

for p in sorted(Path("data/pdfs").glob("*.pdf")):
    text = PdfReader(str(p)).pages[0].extract_text() or ""
    first = " ".join(text.split())[:220]
    print(f"{p.name[:22]:<24} {first}")