#!/usr/bin/env node
/**
 * validate-katex.js — REAL-engine validation of KaTeX math.
 *
 * Every `$...$` / `$$...$$` expression in prose is rendered with the actual
 * `katex` package (throwOnError). Invalid math throws with the exact error —
 * ground truth, not a heuristic. Content inside code fences is skipped
 * (`$` there is usually C# interpolation, not math).
 *
 * Usage:
 *   node validate-katex.js                    # auto-detect content root
 *   node validate-katex.js <dir-or-file>      # explicit path
 *
 * Requires: `npm install` in this directory (see package.json).
 * Exit code: 0 = clean, 1 = at least one render error.
 */
const fs = require("fs");
const path = require("path");
const katex = require("katex");

const FENCE = /^```\w*\s*$/;
const BLOCK = /\$\$(.*?)\$\$/gs; // $$ ... $$ (may span lines)
const INLINE = /\$(.+?)\$/g; // $ ... $ (single line)

function isMathSpan(open, close, s, start) {
  // crude guard: a `$` that is part of `$$` is handled by BLOCK pass first
  return true;
}

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith(".md")) out.push(p);
  }
  return out;
}

function renderAll(text) {
  const out = [];
  // display math first ($$ ... $$)
  let rest = text;
  for (const m of text.matchAll(BLOCK)) {
    out.push({ display: true, math: m[1] });
  }
  rest = text.replace(BLOCK, "  ");
  // inline math ($ ... $)
  for (const m of rest.matchAll(INLINE)) {
    out.push({ display: false, math: m[1] });
  }
  return out;
}

const CJK = /[一-鿿]/;
const TEXT_CMD = "\\text{";
const SAME_LINE_DISPLAY = /\$\$.+?\$\$/;

function cjkOutsideText(math) {
  // CJK characters in a math snippet that are NOT inside a \text{...} group.
  const found = [];
  let i = 0;
  while (i < math.length) {
    if (math.startsWith(TEXT_CMD, i)) {
      let depth = 1, j = i + TEXT_CMD.length;
      while (j < math.length && depth > 0) {
        if (math[j] === "{") depth++;
        else if (math[j] === "}") depth--;
        j++;
      }
      i = j;
      continue;
    }
    if (math[i] === "\\" && i + 1 < math.length && /[A-Za-z]/.test(math[i + 1])) {
      i += 2;
      continue;
    }
    if (CJK.test(math[i])) found.push(math[i]);
    i++;
  }
  return found.join("");
}

function mathSpans(line) {
  const spans = [];
  let i = 0;
  while (i < line.length) {
    if (line[i] !== "$") { i++; continue; }
    let j = i + 1;
    const dbl = j < line.length && line[j] === "$";
    if (dbl) j++;
    const end = dbl ? line.indexOf("$$", j) : line.indexOf("$", j);
    if (end === -1) break;
    spans.push(line.slice(j, end));
    i = end + (dbl ? 2 : 1);
  }
  return spans;
}

function main() {
  const arg = process.argv[2];
  const target = arg ? path.resolve(arg) : path.resolve(__dirname, "../content");
  const files = fs.statSync(target).isFile() ? [target] : walk(target);
  let errors = 0, warnings = 0, rendered = 0;

  for (const f of files) {
    const lines = fs.readFileSync(f, "utf8").split("\n");
    let inCode = false;
    const proseLines = []; // {n, line}
    for (let i = 0; i < lines.length; i++) {
      if (FENCE.test(lines[i].trim())) {
        inCode = !inCode;
        continue;
      }
      if (!inCode) proseLines.push({ n: i + 1, line: lines[i] });
    }
    const proseText = proseLines.map((p) => p.line).join("\n");
    for (const { display, math } of renderAll(proseText)) {
      rendered++;
      try {
        katex.renderToString(math, { throwOnError: true, displayMode: display });
      } catch (e) {
        errors++;
        console.log(`${f}: ERROR katex (${display ? "$$" : "$"}${math}${display ? "$$" : "$"}): ${e.message}`);
      }
    }
    // Renderer-compatibility checks (CloudGlyph viewer = AvalonMarkdown block parser):
    for (const { n, line } of proseLines) {
      if (SAME_LINE_DISPLAY.test(line)) {
        errors++;
        console.log(`${f}:${n}: ERROR single-line display math '$$…$$' (open+close on one line) — ` +
          "the viewer only renders display math as a standalone multi-line '$$' block");
      }
      for (const math of mathSpans(line)) {
        const bare = cjkOutsideText(math);
        if (bare) {
          warnings++;
          console.log(`${f}:${n}: WARN CJK characters ${JSON.stringify(bare)} in math outside \\text{} — ` +
            "wrap in \\text{...} or move the prose out of the formula");
        }
      }
    }
  }
  console.log(`[katex-real] rendered ${rendered} expression(s); ${errors} error(s), ${warnings} warning(s)`);
  process.exit(errors ? 1 : 0);
}

main();
