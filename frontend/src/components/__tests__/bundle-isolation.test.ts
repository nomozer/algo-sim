import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";
import { describe, expect, it } from "vitest";

const FRONTEND_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const DIST_DIR = join(FRONTEND_DIR, "dist");
const ASSETS_DIR = join(DIST_DIR, "assets");

function collectStaticImportClosure(entryAssetRelPath: string): Map<string, string> {
  const visited = new Map<string, string>();
  const normalizedEntry = entryAssetRelPath.replace(/^\//, "");
  const stack = [join(DIST_DIR, normalizedEntry)];

  while (stack.length > 0) {
    const filePath = stack.pop()!;
    if (visited.has(filePath) || !existsSync(filePath)) continue;
    const code = readFileSync(filePath, "utf8");
    visited.set(filePath, code);

    // Inspect ONLY static ESM imports (from"..." or side-effect import"..."),
    // never dynamic import("...") which is intentionally lazy-loaded on demand.
    const staticRe = /(?:^|[;}\s])import(?:\s*[^"'`()]*?from)?\s*"([^"]+)"/g;
    for (const m of code.matchAll(staticRe)) {
      const target = m[1];
      if (!target || !target.startsWith(".")) continue;
      const resolved = resolve(dirname(filePath), target);
      if (existsSync(resolved) && !visited.has(resolved)) {
        stack.push(resolved);
      }
    }
  }
  return visited;
}

describe("Production Bundle Isolation & Lazy Boundary Gate", () => {
  it("dist/index.html never modulepreloads Three.js, full sample JSONs, Admin, Workspace, or app-wide CSS", () => {
    const indexHtml = readFileSync(join(DIST_DIR, "index.html"), "utf8");
    expect(indexHtml).not.toMatch(/modulepreload[^>]*vendor-three/i);
    expect(indexHtml).not.toMatch(/modulepreload[^>]*geometry-samples/i);
    expect(indexHtml).not.toMatch(/modulepreload[^>]*AdminWorkspaceView/i);
    expect(indexHtml).not.toMatch(/modulepreload[^>]*SimulationWorkspace/i);
    expect(indexHtml).not.toMatch(/modulepreload[^>]*pdf/i);
    expect(indexHtml).not.toMatch(/href="[^"]*load-app-styles[^"]*\.css"/i);

    const entryJsMatch = indexHtml.match(/<script[^>]+src="(\/assets\/index-[^"]+\.js)"/);
    expect(entryJsMatch).not.toBeNull();
    const entryCssMatch = indexHtml.match(/<link[^>]+href="(\/assets\/index-[^"]+\.css)"/);
    expect(entryCssMatch).not.toBeNull();

    const entryCssPath = join(DIST_DIR, entryCssMatch![1].replace(/^\//, ""));
    const entryCssBytes = readFileSync(entryCssPath);
    expect(entryCssBytes.length).toBeLessThan(120 * 1024);
    expect(gzipSync(entryCssBytes).length).toBeLessThan(20 * 1024);

    const closure = collectStaticImportClosure(entryJsMatch![1]);
    const combinedStaticJs = [...closure.values()].join("\n");
    const entryJsRawBytes = [...closure.keys()].reduce(
      (sum, f) => sum + readFileSync(f).length,
      0,
    );
    expect(entryJsRawBytes).toBeLessThan(550 * 1024);

    // Zero Three.js, pdfjs, Admin, 3D Workspace, or sample polygon payloads in Landing static closure.
    expect(combinedStaticJs).not.toMatch(/WebGLRenderer|PerspectiveCamera|BufferGeometry/);
    expect(combinedStaticJs).not.toMatch(/pdfjsLib|getDocument/);
    expect(combinedStaticJs).not.toMatch(/Scene3DView|scene3d-canvas/);
    expect(combinedStaticJs).not.toMatch(/Quản trị hệ thống Axo|admin-user-table/);
    expect(combinedStaticJs).not.toMatch(/"faces":\[\[/);
  });

  it("emits isolated lazy chunks for Three.js, geometry sample groups, Admin, SimulationWorkspace, Library, and app CSS", () => {
    const assets = readdirSync(ASSETS_DIR);
    expect(assets.some((f) => /^vendor-three-[^.]+\.js$/.test(f))).toBe(true);
    expect(assets.some((f) => /^geometry-samples-public-[^.]+\.js$/.test(f))).toBe(true);
    expect(assets.some((f) => /^geometry-samples-legacy-[^.]+\.js$/.test(f))).toBe(true);
    expect(assets.some((f) => /^AdminWorkspaceView-[^.]+\.js$/.test(f))).toBe(true);
    expect(assets.some((f) => /^SimulationWorkspace-[^.]+\.js$/.test(f))).toBe(true);
    expect(assets.some((f) => /^LibraryView-[^.]+\.js$/.test(f))).toBe(true);
    expect(assets.some((f) => /^load-app-styles-[^.]+\.css$/.test(f))).toBe(true);
  });
});
