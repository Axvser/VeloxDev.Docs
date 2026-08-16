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

function main() {
  const arg = process.argv[2];
  const target = arg ? path.resolve(arg) : path.resolve(__dirname, "../content");
  const files = fs.statSync(target).isFile() ? [target] : walk(target);
  let errors = 0, rendered = 0;

  for (const f of files) {
    const lines = fs.readFileSync(f, "utf8").split("\n");
    let inCode = false;
    let prose = [];
    for (let i = 0; i < lines.length; i++) {
      if (FENCE.test(lines[i].trim())) {
        inCode = !inCode;
        continue;
      }
      if (!inCode) prose.push(lines[i]);
    }
    const proseText = prose.join("\n");
    for (const { display, math } of renderAll(proseText)) {
      rendered++;
      try {
        katex.renderToString(math, { throwOnError: true, displayMode: display });
      } catch (e) {
        errors++;
        console.log(`${f}: ERROR katex (${display ? "$$" : "$"}${math}${display ? "$$" : "$"}): ${e.message}`);
      }
    }
  }
  console.log(`[katex-real] rendered ${rendered} expression(s); ${errors} error(s)`);
  process.exit(errors ? 1 : 0);
}

main();
