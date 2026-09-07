# Building the manuals

The `.pdf` and `.docx` files in this folder are generated, not hand-written.
The actual source is `content/*.js` (one file per document/language) plus the
screenshots in `images/`.

## Requirements

* [Node.js](https://nodejs.org/) (with `npm install` run once in this folder)
* [LibreOffice](https://www.libreoffice.org/) (used headless to convert to PDF)
* Python 3.10-3.12 with [`pypdf`](https://pypi.org/project/pypdf/) (`pip install pypdf`)

## Build

```bash
npm install                 # once, installs the `docx` package used by render.js
python build_docs.py        # builds all four documents (2 languages x manual/quick-start)
python build_docs.py manual.en   # or build just one
```

`build_docs.py` renders each document twice: a first pass to measure which
page every heading lands on, then a second pass that fills in the contents
page with real numbers (LibreOffice doesn't populate Word TOC fields, so a
plain contents list is used instead).

## Regenerating screenshots

`capture_screenshots.py` drives the running app to capture the images in
`images/`. Review new screenshots before committing them — dialogs that show
file-path fields (e.g. background image / raster pickers) can default to
whatever directory the app was last pointed at, so make sure no local file
path is visible before it ends up in a PDF or DOCX that gets distributed.
