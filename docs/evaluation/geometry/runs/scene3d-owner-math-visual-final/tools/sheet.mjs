// Contact sheet for review: node .../tools/sheet.mjs <out.png> <cols> <cellWidth> <img1> <img2> ...
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { resolve, basename } from "node:path";
const { chromium } = createRequire(resolve("frontend/package.json"))("playwright");
const [out, cols, cellW, ...imgs] = process.argv.slice(2);
const cells = imgs.map((f) => `<figure><img src="data:image/png;base64,${readFileSync(f).toString("base64")}"><figcaption>${basename(f)}</figcaption></figure>`).join("");
const b = await chromium.launch({ channel: "chrome", headless: true });
const p = await b.newPage({ viewport: { width: Number(cols) * Number(cellW), height: 400 } });
await p.setContent(`<style>body{margin:0;display:grid;grid-template-columns:repeat(${cols},${cellW}px);font:11px sans-serif}
figure{margin:0;border:1px solid #ccc}img{width:100%;display:block}figcaption{padding:2px}</style>${cells}`);
await p.waitForFunction(() => [...document.images].every((i) => i.complete));
await p.screenshot({ path: out, fullPage: true });
await b.close();
