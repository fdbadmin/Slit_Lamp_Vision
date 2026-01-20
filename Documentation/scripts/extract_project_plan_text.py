#!/usr/bin/env python3
"""Extract readable text from a project plan PDF.

- First tries normal text extraction (works for text-based PDFs).
- If the PDF appears scanned (little/no extractable text) and `ocrmypdf` is available,
  runs OCR to add a text layer and re-extracts.

Outputs:
- Documentation/project-plan.txt
- Documentation/project-plan.md

Usage:
  python Documentation/scripts/extract_project_plan_text.py \
    --pdf "Documentation/Project Plan_v2.pdf"
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_text_pypdf(pdf_path: Path) -> list[str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Missing dependency 'pypdf'. Install with: pip install pypdf"
        ) from exc

    reader = PdfReader(str(pdf_path))
    pages_text: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)
    return pages_text


def looks_scanned(pages_text: list[str], min_total_chars: int, min_avg_chars: int) -> bool:
    stripped_lengths = [len((t or "").strip()) for t in pages_text]
    total = sum(stripped_lengths)
    avg = (total // max(1, len(stripped_lengths))) if stripped_lengths else 0
    return total < min_total_chars or avg < min_avg_chars


def run_ocrmypdf(input_pdf: Path, output_pdf: Path) -> None:
    if shutil.which("ocrmypdf") is None:
        raise RuntimeError(
            "PDF seems scanned, but 'ocrmypdf' is not installed.\n"
            "Install on macOS with: brew install ocrmypdf tesseract"
        )

    cmd = [
        "ocrmypdf",
        "--skip-text",
        "--deskew",
        "--rotate-pages",
        "--optimize",
        "1",
        str(input_pdf),
        str(output_pdf),
    ]
    subprocess.run(cmd, check=True)


def write_txt(out_path: Path, pages_text: list[str]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for idx, text in enumerate(pages_text, start=1):
            f.write(f"\n\n===== Page {idx} =====\n\n")
            f.write((text or "").rstrip())
            f.write("\n")


def write_md(out_path: Path, pages_text: list[str]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Project Plan (Extracted)\n")
        for idx, text in enumerate(pages_text, start=1):
            f.write(f"\n\n## Page {idx}\n\n")
            f.write((text or "").rstrip())
            f.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract text from a project plan PDF")
    parser.add_argument(
        "--pdf",
        default=str(Path("Documentation") / "Project Plan_v2.pdf"),
        help="Path to input PDF",
    )
    parser.add_argument(
        "--out-txt",
        default=str(Path("Documentation") / "project-plan.txt"),
        help="Path to output .txt",
    )
    parser.add_argument(
        "--out-md",
        default=str(Path("Documentation") / "project-plan.md"),
        help="Path to output .md",
    )
    parser.add_argument(
        "--min-total-chars",
        type=int,
        default=1200,
        help="If extracted text total chars is below this, treat PDF as scanned",
    )
    parser.add_argument(
        "--min-avg-chars",
        type=int,
        default=150,
        help="If extracted text avg chars/page is below this, treat PDF as scanned",
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Never attempt OCR fallback",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    workspace_root = Path(__file__).resolve().parents[2]
    pdf_path = (workspace_root / args.pdf).resolve() if not os.path.isabs(args.pdf) else Path(args.pdf)
    out_txt = (workspace_root / args.out_txt).resolve() if not os.path.isabs(args.out_txt) else Path(args.out_txt)
    out_md = (workspace_root / args.out_md).resolve() if not os.path.isabs(args.out_md) else Path(args.out_md)

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}", file=sys.stderr)
        return 2

    pages_text = extract_text_pypdf(pdf_path)

    if looks_scanned(pages_text, args.min_total_chars, args.min_avg_chars) and not args.no_ocr:
        with tempfile.TemporaryDirectory() as tmpdir:
            ocr_pdf = Path(tmpdir) / "ocr.pdf"
            try:
                run_ocrmypdf(pdf_path, ocr_pdf)
            except Exception as exc:
                print(str(exc), file=sys.stderr)
                print(
                    "Tip: If you can select text in Preview, the PDF is text-based and OCR isn't needed.\n"
                    "Otherwise, install OCR deps and re-run.",
                    file=sys.stderr,
                )
                return 3
            pages_text = extract_text_pypdf(ocr_pdf)

    write_txt(out_txt, pages_text)
    write_md(out_md, pages_text)

    total = sum(len((t or "").strip()) for t in pages_text)
    print(f"Wrote: {out_txt}")
    print(f"Wrote: {out_md}")
    print(f"Extracted characters: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
