import { createRequire } from "node:module";
import { writeFileSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import os from "node:os";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";
const playwrightRoot = resolve(process.argv[3], "frontend/node_modules/playwright");
const { chromium } = await import(pathToFileURL(join(playwrightRoot, "index.mjs")).href);
const require = createRequire(pathToFileURL(join(playwrightRoot, "index.mjs")));
const args = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"];
const browser = await chromium.launch({ headless: true, args });
try {
  const page = await browser.newPage();
  await page.route("**/*", route => route.abort());
  const webgl = await page.evaluate(() => {
    const gl = document.createElement("canvas").getContext("webgl2");
    if (!gl) return { available: false };
    const ext = gl.getExtension("WEBGL_debug_renderer_info");
    return { available: true, version: gl.getParameter(gl.VERSION),
      renderer: gl.getParameter(ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER),
      vendor: gl.getParameter(ext ? ext.UNMASKED_VENDOR_WEBGL : gl.VENDOR) };
  });
  const executable = chromium.executablePath();
  const result = { schema_version: "browser-preflight/1", probe_utc: new Date().toISOString(),
    os: { platform: os.platform(), release: os.release(), architecture: os.arch() },
    node: process.version, playwright: require("./package.json").version,
    chromium: browser.version(), executable, executable_sha256: createHash("sha256").update(readFileSync(executable)).digest("hex"),
    headless: true, args, viewport: { width: 1280, height: 860 }, rendering_mode: "ANGLE SwiftShader software WebGL",
    webgl, note: "Separate preflight probe; reproduction uses the unchanged frozen audit runner with the same executable and flags." };
  writeFileSync(process.argv[2], JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify(result));
  if (!webgl.available) process.exitCode = 1;
} finally { await browser.close(); }
