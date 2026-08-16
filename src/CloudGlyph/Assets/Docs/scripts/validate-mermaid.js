#!/usr/bin/env node
/**
 * validate-mermaid.js — REAL-engine validation of Mermaid blocks.
 *
 * Uses the actual `mermaid` npm package: every ```mermaid block is fed to
 * mermaid.parse() (the real grammar parser), which throws with the exact error
 * on invalid syntax. This is ground truth — not a heuristic.
 *
 * Usage:
 *   node validate-mermaid.js                 # auto-detect content root
 *   node validate-mermaid.js <dir-or-file>   # explicit path
 *
 * Requires: `npm install` in this directory (see package.json).
 * Exit code: 0 = clean, 1 = at least one parse error.
 */
const fs = require("fs");
const path = require("path");

// mermaid v11 needs a DOM (DOMPurify sanitization) even for parse(); provide jsdom.
const { JSDOM } = require("jsdom");
const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", { url: "http://localhost/" });
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

const mermaid = require("mermaid").default; // mermaid v11 exposes the API on `.default`

mermaid.initialize({ startOnLoad: false, securityLevel: "loose", theme: "base" });

const FENCE_OPEN = /^```\s*mermaid\s*$/;
const FENCE_CLOSE = /^```\s*$/;

function findBlocks(lines) {
  const blocks = [];
  for (let i = 0; i < lines.length; i++) {
    if (FENCE_OPEN.test(lines[i].trim())) {
      let j = i + 1;
      while (j < lines.length && !FENCE_CLOSE.test(lines[j].trim())) j++;
      blocks.push({ start: i + 2, text: lines.slice(i + 1, j).join("\n") });
      i = j;
    }
  }
  return blocks;
}

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith(".md")) out.push(p);
  }
  return out;
}

async function main() {
  const arg = process.argv[2];
  const target = arg
    ? path.resolve(arg)
    : path.resolve(__dirname, "../content");
  const files = fs.statSync(target).isFile() ? [target] : walk(target);
  let errors = 0, scanned = 0;

  for (const f of files) {
    const lines = fs.readFileSync(f, "utf8").split("\n");
    for (const b of findBlocks(lines)) {
      scanned++;
      try {
        await mermaid.parse(b.text);
      } catch (e) {
        errors++;
        const msg = (e && (e.message || e.str)) || String(e);
        const first = String(msg).split("\n")[0];
        console.log(`${f}:${b.start}: ERROR mermaid parse: ${first}`);
      }
    }
  }
  console.log(`[mermaid-real] parsed ${scanned} block(s); ${errors} error(s)`);
  process.exit(errors ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(2); });
