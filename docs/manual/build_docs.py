#!/usr/bin/env python3
"""Build every mf6Voronoi Studio manual (.docx + .pdf), in both languages.

    py -3.12 docs/manual/build_docs.py            # all four documents
    py -3.12 docs/manual/build_docs.py manual.en  # just one

Each document is built twice. The first pass leaves the contents page numbers
blank; the PDF of that pass is measured to find the page each heading landed
on; the second pass writes those numbers in. Because a page number never
changes a line count, the measured pages stay valid in the final file -- and
the script verifies exactly that at the end.

A real contents list is used rather than a Word TOC field, because LibreOffice
does not populate field codes, which would leave the PDF's contents page blank.

Requires: node (with `npm install` already run in this folder), LibreOffice,
and pypdf.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, ".build")

SOFFICE = os.environ.get("SOFFICE", r"C:\Program Files\LibreOffice\program\soffice.exe")
LO_PROFILE = "file:///" + os.path.join(BUILD, "loprofile").replace("\\", "/")

DOCS = {
    "manual.en": ("content/manual.en.js",
                  "mf6VoronoiStudio-3.0.0-User-Manual"),
    "quickstart.en": ("content/quickstart.en.js",
                      "mf6VoronoiStudio-3.0.0-Quick-Start-Guide"),
    "manual.es": ("content/manual.es.js",
                  "mf6VoronoiStudio-3.0.0-Manual-de-Usuario"),
    "quickstart.es": ("content/quickstart.es.js",
                      "mf6VoronoiStudio-3.0.0-Guia-de-Inicio-Rapido"),
}


def run(cmd, **kw):
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        raise SystemExit(f"command failed: {' '.join(map(str, cmd))}")
    return r.stdout.strip()


def to_pdf(docx_path: str, outdir: str) -> str:
    """Convert with an isolated profile so a stray LibreOffice instance on the
    machine cannot make the conversion silently no-op."""
    run([SOFFICE, "--headless", "--norestore",
         f"-env:UserInstallation={LO_PROFILE}",
         "--convert-to", "pdf", "--outdir", outdir, docx_path])
    pdf = os.path.join(
        outdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    if not os.path.exists(pdf):
        raise SystemExit(f"LibreOffice produced no PDF for {docx_path}")
    return pdf


def page_texts(pdf_path: str) -> list[str]:
    from pypdf import PdfReader
    return [re.sub(r"\s+", "", (p.extract_text() or ""))
            for p in PdfReader(pdf_path).pages]


def locate(outline, pages) -> tuple[dict, list]:
    """Map each heading to its page.

    Every heading appears twice in the PDF: once in the contents listing, once
    as the heading itself. The contents comes first, so the second occurrence
    is the one we want.
    """
    mapping, problems = {}, []
    for e in outline:
        k = re.sub(r"\s+", "", e["text"])
        hits = [i + 1 for i, t in enumerate(pages) if k in t]
        if len(hits) >= 2:
            mapping[k] = hits[1]
        elif hits:
            mapping[k] = hits[0]
            problems.append((e["text"], "only one occurrence"))
        else:
            problems.append((e["text"], "not found"))
    return mapping, problems


def build(doc_id: str) -> None:
    content, stem = DOCS[doc_id]
    os.makedirs(BUILD, exist_ok=True)
    tmp_docx = os.path.join(BUILD, f"{doc_id}.pass1.docx")
    final_docx = os.path.join(HERE, stem + ".docx")
    mapfile = os.path.join(BUILD, f"{doc_id}.pagemap.json")

    print(f"\n=== {doc_id} -> {stem} ===")

    # pass 1: no page numbers, purely to measure where headings land
    print("  pass 1 ", end="")
    print(run(["node", "render.js", content, tmp_docx]))
    pages = page_texts(to_pdf(tmp_docx, BUILD))
    outline = json.load(open(tmp_docx + ".outline.json", encoding="utf-8"))
    mapping, problems = locate(outline, pages)
    for text, why in problems:
        print(f"  !! {why}: {text}")
    json.dump(mapping, open(mapfile, "w", encoding="utf-8"), indent=1)
    print(f"  measured {len(mapping)}/{len(outline)} headings over {len(pages)} pages")

    # pass 2: the real document
    print("  pass 2 ", end="")
    print(run(["node", "render.js", content, final_docx, mapfile]))
    final_pdf_tmp = to_pdf(final_docx, BUILD)

    # verify the numbers we printed match the file we shipped
    final_pages = page_texts(final_pdf_tmp)
    wrong = 0
    for e in outline:
        k = re.sub(r"\s+", "", e["text"])
        hits = [i + 1 for i, t in enumerate(final_pages) if k in t]
        actual = hits[1] if len(hits) >= 2 else (hits[0] if hits else None)
        if actual != mapping.get(k):
            wrong += 1
            print(f"  !! contents says {mapping.get(k)}, actually {actual}: {e['text']}")
    print(f"  verified: {len(final_pages)} pages, {wrong} wrong contents entries")

    dest_pdf = os.path.join(HERE, stem + ".pdf")
    try:
        shutil.copyfile(final_pdf_tmp, dest_pdf)
    except PermissionError:
        print(f"  !! {os.path.basename(dest_pdf)} is open in another program; "
              f"close it and re-run. The new file is at {final_pdf_tmp}")
        return
    os.remove(final_docx + ".outline.json")
    print(f"  wrote {stem}.docx and {stem}.pdf")


def main() -> None:
    wanted = sys.argv[1:] or list(DOCS)
    for doc_id in wanted:
        if doc_id not in DOCS:
            raise SystemExit(f"unknown document {doc_id!r}; "
                             f"choose from {', '.join(DOCS)}")
        build(doc_id)
    print("\nDone.")


if __name__ == "__main__":
    main()
