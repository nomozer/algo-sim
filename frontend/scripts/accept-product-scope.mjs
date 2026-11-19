#!/usr/bin/env node
/**
 * Product-scope browser acceptance guard (Option B aligned).
 *
 * Audits live runtime routes (`/`, `/app`, `/simulation/chop-mat-cau-ngoai-tiep`)
 * across desktop/tablet/mobile viewports without probing or seeding deprecated
 * Classroom / Live Session features, and without writing into frozen docs.
 */
import os from "node:os";
import path from "node:path";
import { writeFileSync } from "node:fs";
import { chromium } from "playwright";
import { provenance } from "./evidence.mjs";

const LEGACY_INFORMATICS_DOMAINS = [
  "Thuật toán",
  "Nhị phân",
  "CSDL",
  "Lôgic",
  "Màu sắc",
];
const LEGACY_INFORMATICS_PHRASES = [
  "Tin học THPT",
  "mô phỏng thuật toán",
  "số nhị phân",
  "cổng logic",
  "mạng máy tính",
  "cơ sở dữ liệu",
];
const RETIRED_CLASSROOM_LABELS = [
  "Lớp học của tôi",
  "Quản lý lớp học",
  "Bài thực hành",
  "Bài đã giao",
  "Quan sát lớp học",
  "Phiên trực tiếp",
  "Bắt đầu tiết",
  "Theo cô/thầy",
];

function parseArgs(argv) {
  let baseUrl = "http://localhost:3001";
  let outPath = path.join(os.tmpdir(), "axo-product-scope-acceptance.json");
  let help = false;

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") {
      help = true;
    } else if (arg === "--base" && argv[i + 1]) {
      baseUrl = argv[++i];
    } else if (arg.startsWith("--base=")) {
      baseUrl = arg.slice("--base=".length);
    } else if (arg === "--out" && argv[i + 1]) {
      outPath = argv[++i];
    } else if (arg.startsWith("--out=")) {
      outPath = arg.slice("--out=".length);
    }
  }
  return { baseUrl: baseUrl.replace(/\/+$/, ""), outPath, help };
}

function includesFolded(haystack, needle) {
  return haystack.toLowerCase().includes(needle.toLowerCase());
}

async function fetchJson(url) {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    json = null;
  }
  return { status: res.status, ok: res.ok, json, text };
}

async function waitForRouteReady(page, routePath) {
  await page.waitForLoadState("domcontentloaded");
  if (routePath.startsWith("/simulation/")) {
    await page.waitForSelector(".geo3d-canvas canvas", { timeout: 15000 });
    await page.waitForTimeout(1000);
  } else {
    await page.waitForFunction(
      () => (document.body?.innerText ?? "").trim().length > 100,
      { timeout: 15000 },
    );
    await page.waitForTimeout(600);
  }
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    process.stdout.write(
      "Usage: node frontend/scripts/accept-product-scope.mjs [--base http://localhost:3001] [--out <json-path>]\n",
    );
    process.exit(0);
  }

  const rows = [];
  const consoleErrors = [];
  const pageErrors = [];
  const viewports = [
    [1920, 1080],
    [1366, 768],
    [390, 844],
  ];
  const routes = ["/", "/app", "/simulation/chop-mat-cau-ngoai-tiep"];

  const record = (section, check, expected, actual, pass) => {
    rows.push({ section, check, expected, actual, pass: Boolean(pass) });
  };

  // 1. Live health & Option B 404 verification via the configured base URL
  const health = await fetchJson(`${opts.baseUrl}/api/health`);
  record(
    "backend-health",
    "GET /api/health",
    "HTTP 200 & ok === true",
    `HTTP ${health.status} ok=${health.json?.ok}`,
    health.status === 200 && health.json?.ok === true,
  );

  for (const retiredPath of ["/api/classes", "/api/assignments"]) {
    const resp = await fetchJson(`${opts.baseUrl}${retiredPath}`);
    record(
      "option-b-routes",
      `GET ${retiredPath} retired`,
      'HTTP 404 {"detail":"Not Found"}',
      `HTTP ${resp.status} ${resp.text.slice(0, 100)}`,
      resp.status === 404 && resp.json?.detail === "Not Found",
    );
  }

  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await context.newPage();
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push({ url: page.url(), text: msg.text() });
      }
    });
    page.on("pageerror", (err) => {
      pageErrors.push({ url: page.url(), text: String(err) });
    });

    for (const [width, height] of viewports) {
      await page.setViewportSize({ width, height });
      for (const routePath of routes) {
        const vpTag = `${width}x${height} ${routePath}`;
        await page.goto(`${opts.baseUrl}${routePath}`, { waitUntil: "domcontentloaded", timeout: 25000 });
        await waitForRouteReady(page, routePath);

        const snap = await page.evaluate(() => ({
          pathname: window.location.pathname,
          text: document.body?.innerText ?? "",
          navButtons: [...document.querySelectorAll("nav button, nav a, .app-sidebar button, .app-sidebar a")]
            .map((el) => (el.textContent ?? "").trim())
            .filter(Boolean),
          canvasCount: document.querySelectorAll(".geo3d-canvas canvas").length,
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        }));

        // Guard against false-green blank screen
        const nonEmpty = snap.text.trim().length > 100;
        record("surface-anchor", `${vpTag} non-empty`, "> 100 chars", `${snap.text.trim().length} chars`, nonEmpty);

        if (routePath === "/") {
          record(
            "surface-anchor",
            `${vpTag} Axo landing identity`,
            "Contains Axo copy",
            `hasAxo=${includesFolded(snap.text, "Axo")}`,
            includesFolded(snap.text, "Axo"),
          );
        } else if (routePath === "/app") {
          record(
            "surface-anchor",
            `${vpTag} Workspace shell`,
            "Has workspace or library navigation",
            `hasLib=${includesFolded(snap.text, "Thư viện")}`,
            includesFolded(snap.text, "Thư viện") || includesFolded(snap.text, "Hình học"),
          );
        } else {
          record(
            "surface-anchor",
            `${vpTag} Simulation 3D canvas`,
            ">= 1 Scene3D canvas",
            `canvasCount=${snap.canvasCount}`,
            snap.canvasCount >= 1,
          );
        }

        const leakedInformatics = [...LEGACY_INFORMATICS_DOMAINS, ...LEGACY_INFORMATICS_PHRASES].filter((term) =>
          includesFolded(snap.text, term),
        );
        record(
          "domain-scope",
          `${vpTag} 0 Informatics terms`,
          "0 leaked terms",
          leakedInformatics.length ? leakedInformatics.join(",") : "0",
          leakedInformatics.length === 0,
        );

        const leakedClassroom = RETIRED_CLASSROOM_LABELS.filter((term) => includesFolded(snap.text, term));
        record(
          "option-b-ui",
          `${vpTag} 0 Classroom UI controls`,
          "0 retired Classroom labels",
          leakedClassroom.length ? leakedClassroom.join(",") : "0",
          leakedClassroom.length === 0,
        );

        const overflowPx = snap.scrollWidth - snap.clientWidth;
        record(
          "responsive-layout",
          `${vpTag} no horizontal overflow`,
          "scrollWidth <= clientWidth + 2",
          `scroll=${snap.scrollWidth} client=${snap.clientWidth} (diff=${overflowPx})`,
          overflowPx <= 2,
        );
      }
    }
    await context.close();
  } finally {
    await browser.close();
  }

  const failures = rows.filter((r) => !r.pass);
  const pass = failures.length === 0 && consoleErrors.length === 0 && pageErrors.length === 0;
  const report = {
    schema: "axo-product-scope-acceptance/v2-option-b",
    baseUrl: opts.baseUrl,
    runAt: new Date().toISOString(),
    routes,
    viewports: viewports.map(([w, h]) => `${w}x${h}`),
    checksTotal: rows.length,
    checksPassed: rows.length - failures.length,
    failures,
    consoleErrors,
    pageErrors,
    pass,
    ...provenance("accept-product-scope", {
      baseUrl: opts.baseUrl,
      routes: routes.join(","),
      viewports: viewports.map(([w, h]) => `${w}x${h}`).join(","),
    }),
    rows,
  };

  writeFileSync(opts.outPath, `${JSON.stringify(report, null, 2)}\n`, "utf-8");
  process.stdout.write(
    `${pass ? "[PASS]" : "[FAIL]"} accept-product-scope: ${report.checksPassed}/${report.checksTotal}, consoleErrors=${consoleErrors.length}, pageErrors=${pageErrors.length} -> ${opts.outPath}\n`,
  );
  process.exit(pass ? 0 : 1);
}

main().catch((err) => {
  process.stderr.write(`[ERROR] accept-product-scope failed: ${err?.stack || err}\n`);
  process.exit(1);
});
