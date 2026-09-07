/* Shared layout engine for the mf6Voronoi Studio documentation set.
 *
 * Content lives in ./content/<doc>.<lang>.js as data + helper calls; this
 * module owns every formatting decision, so the English and Spanish editions
 * of a document are guaranteed to lay out identically.
 *
 * Screenshots come from ./images, captured from the live application by
 * ./capture_screenshots.py running against the bundled Example dataset.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const {
  Document, Paragraph, TextRun, HeadingLevel, AlignmentType,
  ImageRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  PageBreak, Footer, Header, PageNumber, LevelFormat,
  TabStopType, LeaderType, Tab,
} = require('docx');

const IMG = path.join(__dirname, 'images');

const CONTENT_DXA = 10080;   // 7.0" content width (US Letter, 0.75" margins)
const PX = 672;              // the same 7.0" expressed at 96 dpi
const ACCENT = '1F4E79';
const MUTED = '5A6672';
const RULE = 'C8D2DC';
const TOC_MARK = ' TOC ';

/* ------------------------------------------------------------------ utils */
function pngSize(p) {
  const b = fs.readFileSync(p);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

/** Runs from [text, style] pairs. style: 'b' bold | 'i' italic | 'c' code. */
function runs(parts, base = {}) {
  return parts.map(([t, s]) => new TextRun({
    text: t,
    size: s === 'c' ? (base.size ? base.size - 2 : 19) : (base.size || 21),
    bold: s === 'b' || base.bold,
    italics: s === 'i' || base.italics,
    font: s === 'c' ? 'Consolas' : undefined,
    color: s === 'c' ? '8A3B1E' : base.color,
  }));
}

/* ============================================================== builder == */
/**
 * @param {object} meta  document chrome and localised words
 * @returns {{H: object, state: object}}  helpers plus mutable build state
 */
function createBuilder(meta) {
  const state = { figNo: 0, outline: [] };

  /* -------------------------------------------------------------- figures */
  function figure(name, widthPx, caption) {
    const file = path.join(IMG, name + '.png');
    const { w, h } = pngSize(file);
    state.figNo += 1;
    return [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 180, after: 40 },
        keepNext: true,
        children: [new ImageRun({
          type: 'png',
          data: fs.readFileSync(file),
          transformation: { width: widthPx, height: Math.round(widthPx * h / w) },
        })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 240 },
        children: [new TextRun({
          text: `${meta.figureWord} ${state.figNo}. ${caption}`,
          italics: true, size: 17, color: MUTED,
        })],
      }),
    ];
  }

  /* ----------------------------------------------------------- paragraphs */
  const p = (text, opts = {}) => new Paragraph({
    spacing: { after: opts.after === undefined ? 120 : opts.after },
    alignment: opts.align,
    children: [new TextRun({ text, size: 21, ...opts.run })],
  });

  const rp = (parts, opts = {}) => new Paragraph({
    spacing: { after: opts.after === undefined ? 120 : opts.after },
    children: runs(parts),
  });

  /* ------------------------------------------------------------- headings */
  function h1(text) {
    if (text !== meta.contentsTitle) state.outline.push({ level: 1, text });
    return new Paragraph({
      heading: HeadingLevel.HEADING_1,
      spacing: { before: 320, after: 200 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: RULE, space: 6 } },
      children: [new TextRun({ text, bold: true, size: 32, color: ACCENT })],
    });
  }
  function h2(text) {
    state.outline.push({ level: 2, text });
    return new Paragraph({
      heading: HeadingLevel.HEADING_2,
      spacing: { before: 280, after: 140 },
      keepNext: true,
      children: [new TextRun({ text, bold: true, size: 25, color: ACCENT })],
    });
  }
  const h3 = text => new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 220, after: 110 },
    keepNext: true,
    children: [new TextRun({ text, bold: true, size: 22, color: '2E2E2E' })],
  });

  /* ---------------------------------------------------------------- lists */
  const bullet = (text, level = 0) => new Paragraph({
    numbering: { reference: 'bullets', level },
    spacing: { after: 70 },
    children: [new TextRun({ text, size: 21 })],
  });
  const bulletR = (parts, level = 0) => new Paragraph({
    numbering: { reference: 'bullets', level },
    spacing: { after: 70 },
    children: runs(parts),
  });
  const step = text => new Paragraph({
    numbering: { reference: 'steps', level: 0 },
    spacing: { after: 90 },
    children: [new TextRun({ text, size: 21 })],
  });
  const stepR = parts => new Paragraph({
    numbering: { reference: 'steps', level: 0 },
    spacing: { after: 90 },
    children: runs(parts),
  });

  /* --------------------------------------------------------------- tables */
  function cell(text, width, opts = {}) {
    const parts = Array.isArray(text) ? text : [[text, opts.bold ? 'b' : '']];
    return new TableCell({
      width: { size: width, type: WidthType.DXA },
      shading: opts.shade
        ? { type: ShadingType.CLEAR, fill: opts.shade, color: 'auto' }
        : undefined,
      margins: { top: 70, bottom: 70, left: 110, right: 110 },
      children: [new Paragraph({
        spacing: { after: 0 },
        children: parts.map(([t, s]) => new TextRun({
          text: t,
          size: s === 'c' ? 18 : 19,
          bold: s === 'b' || opts.bold,
          italics: s === 'i',
          font: s === 'c' ? 'Consolas' : undefined,
          color: opts.headerRow ? 'FFFFFF' : (s === 'c' ? '8A3B1E' : undefined),
        })),
      })],
    });
  }

  function table(headers, rows, widths) {
    const trs = [new TableRow({
      tableHeader: true,
      children: headers.map((hd, i) =>
        cell(hd, widths[i], { shade: ACCENT, bold: true, headerRow: true })),
    })];
    rows.forEach((r, ri) => trs.push(new TableRow({
      children: r.map((c, i) => cell(c, widths[i], { shade: ri % 2 ? 'F2F5F8' : undefined })),
    })));
    return new Table({
      columnWidths: widths,
      width: { size: CONTENT_DXA, type: WidthType.DXA },
      borders: {
        top: { style: BorderStyle.SINGLE, size: 4, color: RULE },
        bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE },
        left: { style: BorderStyle.SINGLE, size: 4, color: RULE },
        right: { style: BorderStyle.SINGLE, size: 4, color: RULE },
        insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: RULE },
        insideVertical: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      },
      rows: trs,
    });
  }

  /* ------------------------------------------------------------ call-outs */
  function note(label, text, fill = 'FFF6E5', bar = 'E0A030') {
    return new Table({
      columnWidths: [CONTENT_DXA],
      width: { size: CONTENT_DXA, type: WidthType.DXA },
      borders: {
        top: { style: BorderStyle.SINGLE, size: 2, color: fill },
        bottom: { style: BorderStyle.SINGLE, size: 2, color: fill },
        right: { style: BorderStyle.SINGLE, size: 2, color: fill },
        left: { style: BorderStyle.SINGLE, size: 18, color: bar },
        insideHorizontal: { style: BorderStyle.NONE },
        insideVertical: { style: BorderStyle.NONE },
      },
      rows: [new TableRow({
        children: [new TableCell({
          width: { size: CONTENT_DXA, type: WidthType.DXA },
          shading: { type: ShadingType.CLEAR, fill, color: 'auto' },
          margins: { top: 110, bottom: 110, left: 160, right: 140 },
          children: [new Paragraph({
            spacing: { after: 0 },
            children: [
              new TextRun({ text: label + '  ', bold: true, size: 19, color: '7A4B00' }),
              new TextRun({ text, size: 19 }),
            ],
          })],
        })],
      })],
    });
  }
  /** Green "verified" variant, for statements backed by an actual run. */
  const ok = (label, text) => note(label, text, 'EAF3EA', '4A8C4A');

  const spacer = (after = 200) => new Paragraph({ spacing: { after }, children: [] });
  const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

  /* ----------------------------------------------------------- cover page */
  function cover() {
    const out = [
      spacer(meta.coverTopSpace || 1400),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 60 },
        children: [new TextRun({ text: meta.appName, bold: true, size: 60, color: ACCENT })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 40 },
        children: [new TextRun({ text: meta.docTitle, size: 34, color: '404040' })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 300 },
        children: [new TextRun({ text: meta.versionLine, bold: true, size: 24, color: MUTED })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 260 },
        children: [new TextRun({ text: meta.tagline, italics: true, size: 22, color: MUTED })],
      }),
    ];
    if (meta.coverImage) {
      const file = path.join(IMG, meta.coverImage + '.png');
      const { w, h } = pngSize(file);
      const cw = meta.coverImageWidth || 620;
      out.push(new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { after: 320 },
        children: [new ImageRun({
          type: 'png',
          data: fs.readFileSync(file),
          transformation: { width: cw, height: Math.round(cw * h / w) },
        })],
      }));
    }
    (meta.coverNotes || []).forEach((line, i, arr) => out.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: i === arr.length - 1 ? 300 : 40 },
      children: [new TextRun({ text: line, size: 19, color: MUTED })],
    })));
    (meta.credits || []).forEach(line => out.push(new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 30 },
      children: [new TextRun({ text: line, size: 19 })],
    })));
    if (meta.motto) {
      out.push(new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: meta.motto, italics: true, size: 19, color: MUTED })],
      }));
    }
    out.push(pageBreak());
    return out;
  }

  /** Contents heading plus a placeholder the renderer replaces with entries. */
  const contents = () => [h1(meta.contentsTitle), TOC_MARK, pageBreak()];

  return {
    state,
    H: {
      h1, h2, h3, p, rp, bullet, bulletR, step, stepR, table, note, ok,
      figure, spacer, pageBreak, cover, contents,
      PX, CONTENT_DXA,
    },
  };
}

/* ------------------------------------------------------- contents entries */
/** One contents line: title, dot leader, page number flush right.
 *  Uses a classic right tab stop; a positional tab (w:ptab) is Word-only and
 *  renders as nothing in LibreOffice, and so in the PDF. */
function tocLine(entry, page) {
  const lvl1 = entry.level === 1;
  const style = { bold: lvl1, size: lvl1 ? 20 : 19, color: lvl1 ? ACCENT : '2E2E2E' };
  return new Paragraph({
    spacing: { after: lvl1 ? 60 : 20 },
    indent: { left: lvl1 ? 0 : 360 },
    tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_DXA, leader: LeaderType.DOT }],
    children: [
      new TextRun({ text: entry.text, ...style }),
      // A real <w:tab/> element -- a literal tab character inside <w:t> is
      // ignored by both Word and LibreOffice.
      new TextRun({ children: [new Tab(), String(page)], ...style }),
    ],
  });
}

/** Normalised lookup key, so PDF text extraction (which loses spacing) matches. */
const keyOf = e => (typeof e === 'string' ? e : e.text).replace(/\s+/g, '');

/* ============================================================== assemble = */
/**
 * @param {object} spec         the content module ({meta, body})
 * @param {object|null} pageMap heading key -> page number, or null on pass 1
 * @returns {{doc: Document, outline: Array, figures: number}}
 */
function buildDocument(spec, pageMap) {
  const { meta } = spec;
  const { H, state } = createBuilder(meta);

  const body = spec.body(H);
  const at = body.indexOf(TOC_MARK);
  if (at !== -1) {
    const lines = state.outline.map(e =>
      tocLine(e, pageMap ? (pageMap[keyOf(e)] || '') : ''));
    body.splice(at, 1, ...lines);
  }

  const doc = new Document({
    creator: meta.appName,
    title: `${meta.appName} — ${meta.docTitle}`,
    description: meta.description || meta.docTitle,
    styles: {
      default: { document: { run: { font: 'Calibri', size: 21 } } },
      paragraphStyles: [
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal',
          quickFormat: true,
          run: { size: 32, bold: true, color: ACCENT, font: 'Calibri' } },
        { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal',
          quickFormat: true,
          run: { size: 25, bold: true, color: ACCENT, font: 'Calibri' } },
        { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal',
          quickFormat: true,
          run: { size: 22, bold: true, color: '2E2E2E', font: 'Calibri' } },
      ],
    },
    numbering: {
      config: [
        {
          reference: 'bullets',
          levels: [
            { level: 0, format: LevelFormat.BULLET, text: '•',
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 420, hanging: 240 } } } },
            { level: 1, format: LevelFormat.BULLET, text: '◦',
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 820, hanging: 240 } } } },
          ],
        },
        {
          reference: 'steps',
          levels: [
            { level: 0, format: LevelFormat.DECIMAL, text: '%1.',
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 460, hanging: 300 } } } },
          ],
        },
      ],
    },
    sections: [{
      properties: {
        titlePage: true,
        page: {
          size: { width: 12240, height: 15840 },   // US Letter, in DXA
          margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
        },
      },
      headers: {
        first: new Header({ children: [new Paragraph({ children: [] })] }),
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 4 } },
            children: [new TextRun({ text: meta.headerText, size: 17, color: MUTED })],
          })],
        }),
      },
      footers: {
        first: new Footer({ children: [new Paragraph({ children: [] })] }),
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({
              children: [meta.pageWord + ' ', PageNumber.CURRENT],
              size: 17, color: MUTED,
            })],
          })],
        }),
      },
      children: body,
    }],
  });

  return { doc, outline: state.outline, figures: state.figNo };
}

module.exports = { buildDocument, keyOf, CONTENT_DXA, PX, ACCENT, MUTED, RULE };
