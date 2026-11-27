import { existsSync, readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { resolveLocationRoute } from "./components/AxoErrorExperience";

interface VercelRewrite {
  source: string;
  destination: string;
}

interface VercelHeaderRule {
  source: string;
  headers: Array<{ key: string; value: string }>;
}

interface VercelConfig {
  $schema?: string;
  framework?: string;
  buildCommand?: string;
  outputDirectory?: string;
  rewrites?: VercelRewrite[];
  headers?: VercelHeaderRule[];
}

const FRONTEND_DIR = resolve(__dirname, "..");
const REPO_ROOT = resolve(FRONTEND_DIR, "..");
const VERCEL_JSON_PATH = resolve(FRONTEND_DIR, "vercel.json");

function loadVercelConfig(): VercelConfig {
  return JSON.parse(readFileSync(VERCEL_JSON_PATH, "utf8")) as VercelConfig;
}

function compileVercelSourcePattern(source: string): RegExp {
  return new RegExp(`^${source}$`);
}

function findNestedCapturingGroup(source: string): string | null {
  // Vercel's @vercel/routing-utils rejects nested unnamed capturing groups `(...)` inside an outer `(...)`.
  const stack: Array<{ capturing: boolean }> = [];
  let inCharClass = false;
  for (let i = 0; i < source.length; i += 1) {
    const ch = source[i]!;
    if (ch === "\\") {
      i += 1;
      continue;
    }
    if (inCharClass) {
      if (ch === "]") inCharClass = false;
      continue;
    }
    if (ch === "[") {
      inCharClass = true;
      continue;
    }
    if (ch === "(") {
      const next = source[i + 1];
      const capturing = next !== "?";
      if (capturing && stack.some((entry) => entry.capturing)) {
        return `Nested capturing group at index ${i} in "${source}" (use non-capturing "(?:...)" inside outer groups)`;
      }
      stack.push({ capturing });
    } else if (ch === ")" && stack.length > 0) {
      stack.pop();
    }
  }
  return null;
}

describe("Vercel production deployment configuration & SPA routing contract", () => {
  it("keeps a single canonical frontend/vercel.json using the official Vite schema without duplicates", () => {
    expect(existsSync(VERCEL_JSON_PATH)).toBe(true);
    expect(existsSync(resolve(REPO_ROOT, "vercel.json"))).toBe(false);
    expect(existsSync(resolve(REPO_ROOT, "vercel.ts"))).toBe(false);
    expect(existsSync(resolve(FRONTEND_DIR, "vercel.ts"))).toBe(false);

    const raw = readFileSync(VERCEL_JSON_PATH, "utf8");
    const cfg = loadVercelConfig();
    expect(cfg.$schema).toBe("https://openapi.vercel.sh/vercel.json");
    expect(cfg.framework).toBe("vite");
    expect(cfg.buildCommand).toBe("npm run build");
    expect(cfg.outputDirectory).toBe("dist");
    expect(raw).not.toContain("localhost");
    expect(raw).not.toContain("127.0.0.1");
    expect(raw).not.toMatch(/GEMINI_API_KEY|SECRET|PASSWORD|TOKEN/i);
  });

  it("rewrites valid and unknown SPA routes to /index.html while excluding /api, /assets, and static file extensions", () => {
    const cfg = loadVercelConfig();
    expect(cfg.rewrites).toHaveLength(1);
    const spaRewrite = cfg.rewrites![0]!;
    expect(spaRewrite.destination).toBe("/index.html");
    expect(findNestedCapturingGroup(spaRewrite.source)).toBeNull();

    const matcher = compileVercelSourcePattern(spaRewrite.source);
    const expectedSpaPaths = [
      "/",
      "/about",
      "/gioi-thieu",
      "/login",
      "/register",
      "/forgot",
      "/forgot-password",
      "/reset",
      "/app",
      "/library",
      "/history",
      "/workspace",
      "/admin",
      "/account",
      "/simulation/pyramid-circumscribed-sphere",
      "/simulation/chop-mat-cau-ngoai-tiep",
      "/simulation/cube-hexagonal-plane-section",
      "/simulation/point-to-inclined-plane-distance",
      "/simulation/oxyz-line-plane-intersection",
      "/khong-ton-tai",
    ];
    for (const p of expectedSpaPaths) {
      expect(matcher.test(p), `SPA rewrite must match ${p}`).toBe(true);
    }

    const excludedPaths = [
      "/api",
      "/api/",
      "/api/health",
      "/api/auth/me",
      "/api/analyze",
      "/api/admin/overview",
      "/api/nonexistent",
      "/assets",
      "/assets/",
      "/assets/missing.js",
      "/assets/index-DJxTn82Y.js",
      "/assets/landing/product-renders/about-cube-section.png",
      "/favicon.svg",
      "/favicon-32x32.png",
      "/robots.txt",
      "/manifest.json",
    ];
    for (const p of excludedPaths) {
      expect(matcher.test(p), `SPA rewrite must NOT intercept ${p}`).toBe(false);
    }
  });

  it("configures security headers (keeping camera=(self)) and safe cache policies (immutable only for hashed Vite assets)", () => {
    const cfg = loadVercelConfig();
    const rules = cfg.headers ?? [];
    for (const rule of rules) {
      expect(findNestedCapturingGroup(rule.source)).toBeNull();
    }
    expect(findNestedCapturingGroup("/assets/([^/]+-[A-Za-z0-9_-]{8}\\.(js|mjs|css))")).not.toBeNull();
    expect(findNestedCapturingGroup("/assets/([^/]+-[A-Za-z0-9_-]{8}\\.(?:js|mjs|css))")).toBeNull();

    const globalRule = rules.find((r) => r.source === "/(.*)");
    expect(globalRule).toBeDefined();
    const globalHeaderMap = new Map(globalRule!.headers.map((h) => [h.key.toLowerCase(), h.value]));
    expect(globalHeaderMap.get("x-content-type-options")).toBe("nosniff");
    expect(globalHeaderMap.get("x-frame-options")).toBe("DENY");
    expect(globalHeaderMap.get("referrer-policy")).toBe("strict-origin-when-cross-origin");
    expect(globalHeaderMap.get("permissions-policy")).toContain("camera=(self)");

    const htmlRule = rules.find((r) => r.source === "/index.html");
    expect(htmlRule).toBeDefined();
    const htmlCache = htmlRule!.headers.find((h) => h.key.toLowerCase() === "cache-control")?.value ?? "";
    expect(htmlCache).toContain("must-revalidate");
    expect(htmlCache).not.toContain("immutable");

    const hashedRule = rules.find((r) =>
      r.headers.some((h) => h.key.toLowerCase() === "cache-control" && h.value.includes("immutable")),
    );
    expect(hashedRule).toBeDefined();
    const hashedMatcher = compileVercelSourcePattern(hashedRule!.source);
    expect(hashedMatcher.test("/assets/index-DJxTn82Y.js")).toBe(true);
    expect(hashedMatcher.test("/assets/vendor-three-DZzGZQF_.js")).toBe(true);
    expect(hashedMatcher.test("/assets/pdf.worker.min-Ab12Cd34.mjs")).toBe(true);
    expect(hashedMatcher.test("/assets/index-DYVDY5zx.css")).toBe(true);
    expect(hashedMatcher.test("/assets/index-A_b-1234.js")).toBe(true);
    expect(hashedMatcher.test("/assets/foo-bar.js")).toBe(false);
    expect(hashedMatcher.test("/assets/helper-v2.css")).toBe(false);
    expect(hashedMatcher.test("/index.html")).toBe(false);
    expect(hashedMatcher.test("/api/health")).toBe(false);
    expect(hashedMatcher.test("/assets/landing/product-renders/about-cube-section.png")).toBe(false);
    expect(hashedMatcher.test("/assets/landing/product-renders/how-step-construct.png")).toBe(false);

    const distAssetsDir = resolve(FRONTEND_DIR, "dist", "assets");
    if (existsSync(distAssetsDir)) {
      const bundleFiles = readdirSync(distAssetsDir).filter((f) => /\.(?:js|mjs|css)$/.test(f));
      expect(bundleFiles.length).toBeGreaterThan(0);
      for (const fname of bundleFiles) {
        expect(hashedMatcher.test(`/assets/${fname}`), `Vite hashed bundle ${fname} must match immutable rule`).toBe(true);
      }
    }
  });

  it("resolves /forgot-password and /simulation/pyramid-circumscribed-sphere cleanly in the client router", () => {
    expect(resolveLocationRoute("/forgot-password")).toEqual({ kind: "view", view: "forgot" });
    expect(resolveLocationRoute("/forgot")).toEqual({ kind: "view", view: "forgot" });
    expect(resolveLocationRoute("/simulation/pyramid-circumscribed-sphere")).toEqual({
      kind: "sample",
      sampleId: "chop-mat-cau-ngoai-tiep",
    });
  });
});
