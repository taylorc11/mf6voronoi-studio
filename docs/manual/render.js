#!/usr/bin/env node
/* Render one content module to a .docx.
 *
 *   node render.js content/manual.en.js out.docx [pagemap.json]
 *
 * Without a pagemap the contents entries are written with blank page numbers
 * (pass 1); build_docs.py then measures the resulting PDF and re-runs this
 * with the map filled in (pass 2). Layout is identical either way, because a
 * page number never changes a line count.
 *
 * Also writes <out.docx>.outline.json so the orchestrator knows which
 * headings to look for.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { Packer } = require('docx');
const { buildDocument } = require('./docbuild');

const [, , contentArg, outArg, mapArg] = process.argv;
if (!contentArg || !outArg) {
  console.error('usage: node render.js <content-module> <out.docx> [pagemap.json]');
  process.exit(2);
}

const spec = require(path.resolve(contentArg));
const pageMap = mapArg && fs.existsSync(mapArg)
  ? JSON.parse(fs.readFileSync(mapArg, 'utf8'))
  : null;

const { doc, outline, figures } = buildDocument(spec, pageMap);

Packer.toBuffer(doc).then(buf => {
  fs.mkdirSync(path.dirname(path.resolve(outArg)), { recursive: true });
  fs.writeFileSync(outArg, buf);
  fs.writeFileSync(outArg + '.outline.json', JSON.stringify(outline, null, 1));
  console.log(`${path.basename(outArg)}  ${(buf.length / 1024).toFixed(0)} KB, `
    + `${figures} figures, ${outline.length} contents entries, `
    + `${pageMap ? 'with' : 'without'} page numbers`);
}).catch(err => {
  console.error(err);
  process.exit(1);
});
