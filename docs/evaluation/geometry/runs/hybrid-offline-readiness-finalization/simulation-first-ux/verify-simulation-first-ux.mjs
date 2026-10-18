import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import {
  readFileSync,
  writeFileSync,
  existsSync,
  statSync,
  mkdirSync,
  rmSync,
  copyFileSync,
} from "node:fs";
import { resolve, join, dirname, extname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repo = resolve(__dirname, "../../../../../../");
const fe = join(repo, "frontend");
const outDir = __dirname;
const shotsDir = join(outDir, "screenshots");
const tmpBuildRoot = join(outDir, ".tmp-build");
const prodDist = join(tmpBuildRoot, "prod-dist");
const harnessDist = join(tmpBuildRoot, "harness-dist");

mkdirSync(shotsDir, { recursive: true });
mkdirSync(prodDist, { recursive: true });
mkdirSync(harnessDist, { recursive: true });

const req = createRequire(join(fe, "package.json"));
const { chromium } = req("playwright");
const { build } = await import(pathToFileURL(req.resolve("vite")).href);
const react = (await import(pathToFileURL(req.resolve("@vitejs/plugin-react")).href)).default;
const nm = join(fe, "node_modules");

// 1. Build current frontend into prodDist and harness into harnessDist
await build({
  root: fe,
  configFile: false,
  plugins: [react()],
  logLevel: "error",
  build: {
    outDir: prodDist,
    emptyOutDir: true,
  },
});

const harnessSrc = join(
  repo,
  "docs/evaluation/geometry/runs/hybrid-offline-readiness-finalization/p3-offline-e2e/harness",
);
await build({
  root: harnessSrc,
  configFile: false,
  plugins: [react()],
  logLevel: "error",
  resolve: {
    alias: [
      { find: /^@fe\/(.*)$/, replacement: join(fe, "src", "$1") },
      { find: /^react-dom(\/.*)?$/, replacement: join(nm, "react-dom") + "$1" },
      { find: /^react(\/.*)?$/, replacement: join(nm, "react") + "$1" },
    ],
  },
  build: {
    outDir: harnessDist,
    emptyOutDir: true,
    rollupOptions: { input: join(harnessSrc, "hfoi-harness.html") },
  },
});

const fxDir = join(
  repo,
  "docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2",
);
const w11Path = join(
  repo,
  "docs/evaluation/geometry/runs/w11-pedagogical-polish/inputs/fixtures/rectangular_pyramid_positive.json",
);
const loadJson = (p) => JSON.parse(readFileSync(p, "utf8"));
const manifest = loadJson(join(fxDir, "manifest.json"));
const servedRows = manifest.fixtures.filter((f) => f.kind === "served");
const responses = Object.fromEntries(
  servedRows.map((r) => [r.id, loadJson(join(fxDir, r.file)).response]),
);
const w11Envelope = loadJson(w11Path).envelope;

const MIME = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".json": "application/json",
};

const prodServer = createServer((reqUrl, res) => {
  const pathname = new URL(reqUrl.url, "http://127.0.0.1").pathname;
  let p = join(prodDist, pathname);
  if (!existsSync(p) || statSync(p).isDirectory()) p = join(prodDist, "index.html");
  res.setHeader("Content-Type", MIME[extname(p)] ?? "application/octet-stream");
  res.end(readFileSync(p));
});
await new Promise((r) => prodServer.listen(0, "127.0.0.1", r));

const harnessServer = createServer((reqUrl, res) => {
  const pathname = new URL(reqUrl.url, "http://127.0.0.1").pathname;
  if (pathname.startsWith("/responses/")) {
    const id = pathname.slice("/responses/".length).replace(/\.json$/, "");
    res.setHeader("Content-Type", "application/json");
    return res.end(JSON.stringify(responses[id]));
  }
  let p = join(harnessDist, pathname);
  if (!existsSync(p) || statSync(p).isDirectory()) p = join(harnessDist, "hfoi-harness.html");
  res.setHeader("Content-Type", MIME[extname(p)] ?? "application/octet-stream");
  res.end(readFileSync(p));
});
await new Promise((r) => harnessServer.listen(0, "127.0.0.1", r));

const VIEWPORTS = {
  desktop: { width: 1440, height: 900 },
  compact: { width: 390, height: 844 },
};

async function inspectDomAndFraming(page) {
  return await page.evaluate(() => {
    const rect = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return {
        left: Math.round(r.left),
        top: Math.round(r.top),
        right: Math.round(r.right),
        bottom: Math.round(r.bottom),
        width: Math.round(r.width),
        height: Math.round(r.height),
      };
    };

    const canvas = document.querySelector(".geo3d-canvas");
    const cRect = rect(canvas);
    const controls = document.querySelector(".geo3d-controls");
    const ctrlRect = rect(controls);
    const guidance = document.querySelector("[data-learner-guidance]");
    const gRect = rect(guidance);

    const pointLabels = [...document.querySelectorAll(".geo3d-label")].map((el) => {
      const r = el.getBoundingClientRect();
      const insideCanvas =
        cRect &&
        r.left >= cRect.left - 2 &&
        r.right <= cRect.right + 2 &&
        r.top >= cRect.top - 2 &&
        r.bottom <= cRect.bottom + 2;
      return {
        text: (el.textContent || "").trim(),
        insideCanvas: Boolean(insideCanvas),
        rect: rect(el),
      };
    });

    const annBadges = [...document.querySelectorAll(".geo3d-so-do")].map((el) => ({
      id: el.getAttribute("data-ann-id"),
      role: el.getAttribute("data-ann-role"),
      text: (el.textContent || "").trim(),
      rect: rect(el),
    }));

    const buttons = [...document.querySelectorAll("button")].map((b) =>
      (b.textContent || "").trim(),
    );
    const noiItems = [...document.querySelectorAll(".geo3d-noi .geo3d-noi-nut")].map((el) =>
      (el.textContent || "").trim(),
    );
    const hybridAnswerEls = [...document.querySelectorAll("[data-hybrid-answer]")].map((el) =>
      (el.textContent || "").trim(),
    );
    const quantityItems = [...document.querySelectorAll("[data-quantity-id]")].map((el) => ({
      id: el.getAttribute("data-quantity-id"),
      text: (el.textContent || "").trim(),
    }));
    const resultSectionItems = [
      ...document.querySelectorAll('section[aria-label="Kết quả"] [data-quantity-id]'),
    ].map((el) => ({
      id: el.getAttribute("data-quantity-id"),
      text: (el.textContent || "").trim(),
    }));
    const liveNarration = (
      document.querySelector(".geo3d-sr-only[aria-live]")?.textContent || ""
    ).trim();

    return {
      viewport: { width: window.innerWidth, height: window.innerHeight },
      canvasRect: cRect,
      controlsRect: ctrlRect,
      guidanceRect: gRect,
      stepText: (document.querySelector(".geo3d-buoc-so")?.textContent || "").trim(),
      guidanceStep: (
        document.querySelector("[data-guidance-step]")?.textContent || ""
      ).trim(),
      guidanceHint: (
        document.querySelector("[data-guidance-hint]")?.textContent || ""
      ).trim(),
      lengthUnitText: (
        document.querySelector("[data-length-unit]")?.textContent || ""
      ).trim(),
      liveNarration,
      hasAnswerToggleButton: buttons.some(
        (t) => t.includes("Xem đáp án") || t.includes("Ẩn đáp án"),
      ),
      hasDapSoTextInNoi: noiItems.some((t) => t.includes("Đáp số")),
      hybridAnswerEls,
      noiItems,
      annBadges,
      pointLabelsCount: pointLabels.length,
      croppedPointLabels: pointLabels.filter((p) => !p.insideCanvas),
      quantityItems,
      resultSectionItems,
      guidanceOverlapsCanvas:
        gRect && cRect ? gRect.bottom > cRect.top + 1 && gRect.top < cRect.bottom - 1 : false,
    };
  });
}

const stepToEnd = async (page) => {
  for (let i = 0; i < 60; i++) {
    const next = page.getByRole("button", { name: "Bước sau", exact: true });
    if (await next.isDisabled()) return;
    await next.click();
  }
  throw new Error("Timeline did not reach final step");
};

async function openMenusAndInspect(page) {
  const hienThiBtn = page.getByRole("button", { name: "Hiển thị", exact: true });
  let showAllToggled = false;
  if (await hienThiBtn.count()) {
    await hienThiBtn.click();
    const showAllItem = page.getByRole("menuitemcheckbox", {
      name: "Hiện tất cả số đo",
      exact: true,
    });
    if (await showAllItem.count()) {
      await showAllItem.click();
      showAllToggled = true;
    }
    await page.keyboard.press("Escape");
    await page.waitForTimeout(100);
  }

  const khamPhaBtn = page.getByRole("button", { name: "Khám phá", exact: true });
  let daiLuongOpened = false;
  if (await khamPhaBtn.count()) {
    await khamPhaBtn.click();
    const dlItem = page.getByRole("menuitemcheckbox", { name: "Đại lượng", exact: true });
    if (await dlItem.count()) {
      await dlItem.click();
      daiLuongOpened = true;
      await page.waitForTimeout(120);
    } else {
      await page.keyboard.press("Escape");
      await page.waitForTimeout(80);
    }
  }

  const state = await inspectDomAndFraming(page);
  return { showAllToggled, daiLuongOpened, state };
}

async function verifyOrbitAndReset(page) {
  const canvas = page.locator(".geo3d-canvas canvas");
  const box = await canvas.boundingBox();
  if (!box) return { orbited: false, resetWorked: false };
  const startX = box.x + box.width * 0.5;
  const startY = box.y + box.height * 0.5;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX + 75, startY - 45, { steps: 6 });
  await page.mouse.up();
  await page.waitForTimeout(120);

  const resetBtn = page.getByRole("button", { name: "Xem lại toàn hình" });
  const hasReset = (await resetBtn.count()) > 0;
  if (hasReset) {
    await resetBtn.click();
    await page.waitForTimeout(150);
  }
  const afterReset = await inspectDomAndFraming(page);
  return {
    orbited: true,
    resetWorked: hasReset && afterReset.croppedPointLabels.length === 0,
  };
}

const browser = await chromium.launch({
  headless: true,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});

const report = {
  schema: "simulation-first-ux-browser-verification/1",
  generated_at_utc: new Date().toISOString(),
  live_ai_calls: 0,
  pathA_product_ui: {},
  pathB_injected_hybrid: {},
  served12Sweep: [],
  allPassed: true,
  failures: [],
};

const recordCheck = (name, ok, detail) => {
  if (!ok) {
    report.allPassed = false;
    report.failures.push({ name, detail });
  }
};

try {
  // =========================================================================
  // 1. PATH A: Real Product UI (prodDist/index.html)
  // =========================================================================
  for (const [vpName, vp] of Object.entries(VIEWPORTS)) {
    report.pathA_product_ui[vpName] = {};
    const pageA = await browser.newPage({ viewport: vp });
    pageA.setDefaultTimeout(10000);
    let currentMockEnvelope = responses["served-H01_CUBE"].envelope;

    await pageA.route("**/*", (route) => {
      const u = new URL(route.request().url());
      if (u.hostname !== "127.0.0.1") return route.abort();
      if (!u.pathname.startsWith("/api/")) return route.continue();
      if (u.pathname === "/api/analyze") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(currentMockEnvelope),
        });
      }
      return route.fulfill({
        contentType: "application/json",
        body:
          u.pathname === "/api/health"
            ? '{"ok":true,"hasKey":true,"cachedProblems":0}'
            : '{"user":null}',
      });
    });

    // A1: Offline starter sample ("the-tich-chop")
    await pageA.goto(`http://127.0.0.1:${prodServer.address().port}/`);
    await pageA
      .getByText("Thể tích khối chóp và khoảng cách từ đỉnh đến đáy", { exact: false })
      .first()
      .click();
    await pageA.waitForSelector(".geo3d-buoc-so");
    const pauseSample = pageA.getByRole("button", { name: "Tạm dừng", exact: true });
    if (await pauseSample.count()) await pauseSample.click();
    await pageA.waitForTimeout(200);
    const sampleInitial = await inspectDomAndFraming(pageA);
    await stepToEnd(pageA);
    await pageA.waitForTimeout(250);
    const sampleFinalDefault = await inspectDomAndFraming(pageA);
    const sampleMenus = await openMenusAndInspect(pageA);
    const shotSample = join(shotsDir, `pathA_offline_sample_${vpName}_final.png`);
    await pageA.screenshot({ path: shotSample });
    const sampleOrbit = await verifyOrbitAndReset(pageA);

    report.pathA_product_ui[vpName].offline_sample_the_tich_chop = {
      screenshot: shotSample,
      initial: sampleInitial,
      finalDefault: sampleFinalDefault,
      finalMenus: sampleMenus.state,
      orbitCheck: sampleOrbit,
    };

    recordCheck(
      `pathA:${vpName}:offline_sample:noAnswerLeak`,
      !sampleInitial.hasAnswerToggleButton &&
        !sampleFinalDefault.hasAnswerToggleButton &&
        !sampleFinalDefault.hasDapSoTextInNoi &&
        sampleMenus.state.resultSectionItems.length === 0 &&
        !sampleMenus.state.quantityItems.some((q) => ["V", "d"].includes(q.id)) &&
        !sampleMenus.state.annBadges.some((b) => ["V", "d"].includes(b.id)) &&
        !sampleFinalDefault.liveNarration.includes("16/3") &&
        sampleFinalDefault.croppedPointLabels.length === 0 &&
        Boolean(sampleFinalDefault.guidanceStep) &&
        !sampleFinalDefault.guidanceOverlapsCanvas &&
        sampleOrbit.resetWorked,
      report.pathA_product_ui[vpName].offline_sample_the_tich_chop,
    );

    // A2: Analyze path for Cube, Pyramid, Elongated Cuboid, and W11 Pyramid (intermediate vs final)
    const analyzeCases = [
      {
        id: "served-H01_CUBE",
        tag: "cube",
        envelope: responses["served-H01_CUBE"].envelope,
        problemText:
          "Cho hình lập phương ABCD.A'B'C'D' có cạnh a. Tính thể tích khối lập phương và khoảng cách từ A đến C'.",
        forbiddenResultIds: ["kq_f3", "kq_f4"],
        expectedGivenOrStepIds: [],
      },
      {
        id: "served-H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS",
        tag: "pyramid",
        envelope: responses["served-H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS"].envelope,
        problemText:
          "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và cạnh bên bằng a√2. Tính thể tích khối chóp và góc giữa cạnh bên SA và mặt phẳng đáy (ABCD).",
        forbiddenResultIds: ["kq_f4", "kq_f5"],
        expectedGivenOrStepIds: [],
      },
      {
        id: "served-H02_CUBOID_DISTANCE",
        tag: "elongated_cuboid",
        envelope: responses["served-H02_CUBOID_DISTANCE"].envelope,
        problemText:
          "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = a, AD = 2a, AA' = 2a. Tính khoảng cách từ A đến mặt phẳng (A'BD).",
        forbiddenResultIds: ["kq_f6"],
        expectedGivenOrStepIds: [],
      },
      {
        id: "w11_rectangular_pyramid",
        tag: "w11_intermediate_pyramid",
        envelope: w11Envelope,
        problemText:
          "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4, SA vuông góc với đáy và SA = 6. Tính thể tích khối chóp S.ABCD.",
        forbiddenResultIds: ["the_tich_khoi_chop", "v"],
        expectedGivenOrStepIds: ["AB_length", "AD_length", "SA_length", "dien_tich_day_ABCD"],
      },
    ];

    for (const c of analyzeCases) {
      currentMockEnvelope = structuredClone(c.envelope);
      await pageA.goto(`http://127.0.0.1:${prodServer.address().port}/`);
      await pageA.locator("textarea").first().fill(c.problemText);
      await pageA.getByRole("button", { name: /Phân tích đề/i }).click();
      await pageA.waitForSelector(".geo3d-buoc-so");
      const pause = pageA.getByRole("button", { name: "Tạm dừng", exact: true });
      if (await pause.count()) await pause.click();
      await pageA.waitForTimeout(250);

      const initial = await inspectDomAndFraming(pageA);
      const shot1 = join(shotsDir, `pathA_${c.tag}_${vpName}_1_initial.png`);
      await pageA.screenshot({ path: shot1 });

      await stepToEnd(pageA);
      await pageA.waitForTimeout(250);
      const finalDefault = await inspectDomAndFraming(pageA);
      const shot2 = join(shotsDir, `pathA_${c.tag}_${vpName}_2_final_default.png`);
      await pageA.screenshot({ path: shot2 });

      const finalMenus = await openMenusAndInspect(pageA);
      const shot3 = join(shotsDir, `pathA_${c.tag}_${vpName}_3_final_menus.png`);
      await pageA.screenshot({ path: shot3 });

      const orbitCheck = await verifyOrbitAndReset(pageA);

      const qIds = finalMenus.state.quantityItems.map((q) => q.id);
      const badgeIds = finalMenus.state.annBadges.map((b) => b.id);

      report.pathA_product_ui[vpName][c.id] = {
        screenshots: { initial: shot1, final_default: shot2, final_menus: shot3 },
        initial,
        finalDefault,
        finalMenus: finalMenus.state,
        orbitCheck,
      };

      recordCheck(
        `pathA:${vpName}:${c.id}:simulationFirstContract`,
        !initial.hasAnswerToggleButton &&
          !finalDefault.hasAnswerToggleButton &&
          !finalDefault.hasDapSoTextInNoi &&
          finalDefault.hybridAnswerEls.length === 0 &&
          finalMenus.state.resultSectionItems.length === 0 &&
          c.forbiddenResultIds.every((id) => !qIds.includes(id) && !badgeIds.includes(id)) &&
          c.expectedGivenOrStepIds.every((id) => qIds.includes(id)) &&
          finalDefault.croppedPointLabels.length === 0 &&
          Boolean(finalDefault.guidanceStep) &&
          Boolean(finalDefault.guidanceHint) &&
          !finalDefault.guidanceOverlapsCanvas &&
          orbitCheck.resetWorked,
        report.pathA_product_ui[vpName][c.id],
      );
    }

    await pageA.close();
  }

  // =========================================================================
  // 2. PATH B: Injected Hybrid Fixture UI (hfoi-harness.html)
  // =========================================================================
  const pathBFocusedIds = [
    ["served-H01_CUBE", "cube"],
    ["served-H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS", "pyramid"],
    ["served-H02_CUBOID_DISTANCE", "elongated_cuboid"],
    ["served-H11_SKEW_DISTANCE_COMPOSITION", "elongated_skew"],
  ];

  for (const [vpName, vp] of Object.entries(VIEWPORTS)) {
    report.pathB_injected_hybrid[vpName] = {};
    const pageB = await browser.newPage({ viewport: vp });
    pageB.setDefaultTimeout(10000);
    await pageB.route("**/*", (route) => {
      const u = new URL(route.request().url());
      if (u.hostname !== "127.0.0.1") return route.abort();
      if (!u.pathname.startsWith("/api/")) return route.continue();
      return route.fulfill({
        contentType: "application/json",
        body:
          u.pathname === "/api/health"
            ? '{"ok":true,"hasKey":false,"cachedProblems":0}'
            : '{"user":null}',
      });
    });

    await pageB.goto(`http://127.0.0.1:${harnessServer.address().port}/hfoi-harness.html`);
    await pageB.waitForFunction(() => !!window.__HFOI__);

    for (const [id, tag] of pathBFocusedIds) {
      const r = await pageB.evaluate((id) => window.__HFOI__.nap(`/responses/${id}.json`), id);
      assert.equal(r.adapter, "ACCEPTED");
      await pageB.waitForSelector(".geo3d-buoc-so");
      const pause = pageB.getByRole("button", { name: "Tạm dừng", exact: true });
      if (await pause.count()) await pause.click();
      await pageB.waitForTimeout(250);

      const initial = await inspectDomAndFraming(pageB);
      const shot1 = join(shotsDir, `pathB_${tag}_${vpName}_1_initial.png`);
      await pageB.screenshot({ path: shot1 });

      await stepToEnd(pageB);
      await pageB.waitForTimeout(250);
      const finalDefault = await inspectDomAndFraming(pageB);
      const shot2 = join(shotsDir, `pathB_${tag}_${vpName}_2_final_default.png`);
      await pageB.screenshot({ path: shot2 });

      const finalMenus = await openMenusAndInspect(pageB);
      const shot3 = join(shotsDir, `pathB_${tag}_${vpName}_3_final_menus.png`);
      await pageB.screenshot({ path: shot3 });

      const orbitCheck = await verifyOrbitAndReset(pageB);

      const ansIds = Object.keys(responses[id].route_d?.answers || {}).map((k) => `kq_${k}`);
      const qIds = finalMenus.state.quantityItems.map((q) => q.id);
      const badgeIds = finalMenus.state.annBadges.map((b) => b.id);

      report.pathB_injected_hybrid[vpName][id] = {
        screenshots: { initial: shot1, final_default: shot2, final_menus: shot3 },
        initial,
        finalDefault,
        finalMenus: finalMenus.state,
        orbitCheck,
      };

      recordCheck(
        `pathB:${vpName}:${id}:simulationFirstContract`,
        !initial.hasAnswerToggleButton &&
          !finalDefault.hasAnswerToggleButton &&
          !finalDefault.hasDapSoTextInNoi &&
          finalDefault.hybridAnswerEls.length === 0 &&
          finalMenus.state.resultSectionItems.length === 0 &&
          ansIds.every((aid) => !qIds.includes(aid) && !badgeIds.includes(aid)) &&
          finalDefault.croppedPointLabels.length === 0 &&
          Boolean(finalDefault.guidanceStep) &&
          Boolean(finalDefault.guidanceHint) &&
          !finalDefault.guidanceOverlapsCanvas &&
          orbitCheck.resetWorked,
        report.pathB_injected_hybrid[vpName][id],
      );
    }

    await pageB.close();
  }

  // =========================================================================
  // 3. Sweep all 12 served-* fixtures on desktop
  // =========================================================================
  const sweepPage = await browser.newPage({ viewport: VIEWPORTS.desktop });
  sweepPage.setDefaultTimeout(10000);
  await sweepPage.route("**/*", (route) => {
    const u = new URL(route.request().url());
    if (u.hostname !== "127.0.0.1") return route.abort();
    if (!u.pathname.startsWith("/api/")) return route.continue();
    return route.fulfill({ contentType: "application/json", body: '{"user":null}' });
  });
  await sweepPage.goto(`http://127.0.0.1:${harnessServer.address().port}/hfoi-harness.html`);
  await sweepPage.waitForFunction(() => !!window.__HFOI__);

  for (const row of servedRows) {
    const r = await sweepPage.evaluate(
      (id) => window.__HFOI__.nap(`/responses/${id}.json`),
      row.id,
    );
    assert.equal(r.adapter, "ACCEPTED");
    await sweepPage.waitForSelector(".geo3d-buoc-so");
    const pause = sweepPage.getByRole("button", { name: "Tạm dừng", exact: true });
    if (await pause.count()) await pause.click();
    await stepToEnd(sweepPage);
    await sweepPage.waitForTimeout(150);
    const menus = await openMenusAndInspect(sweepPage);
    const ansIds = Object.keys(responses[row.id].route_d?.answers || {}).map((k) => `kq_${k}`);
    const qIds = menus.state.quantityItems.map((q) => q.id);
    const badgeIds = menus.state.annBadges.map((b) => b.id);
    const rowRes = {
      id: row.id,
      answerIds: ansIds,
      hasAnswerToggleButton: menus.state.hasAnswerToggleButton,
      hybridAnswerElsCount: menus.state.hybridAnswerEls.length,
      resultSectionCount: menus.state.resultSectionItems.length,
      leakedBadgesCount: ansIds.filter((id) => badgeIds.includes(id)).length,
      leakedQuantsCount: ansIds.filter((id) => qIds.includes(id)).length,
      croppedPointLabelsCount: menus.state.croppedPointLabels.length,
      guidanceStep: menus.state.guidanceStep,
    };
    report.served12Sweep.push(rowRes);
    recordCheck(
      `sweep:${row.id}`,
      !rowRes.hasAnswerToggleButton &&
        rowRes.hybridAnswerElsCount === 0 &&
        rowRes.resultSectionCount === 0 &&
        rowRes.leakedBadgesCount === 0 &&
        rowRes.leakedQuantsCount === 0 &&
        rowRes.croppedPointLabelsCount === 0 &&
        Boolean(rowRes.guidanceStep),
      rowRes,
    );
  }
  await sweepPage.close();
} finally {
  await browser.close();
  await new Promise((r) => prodServer.close(r));
  await new Promise((r) => harnessServer.close(r));
  rmSync(tmpBuildRoot, { recursive: true, force: true });
}

const outPath = join(outDir, "simulation-first-ux-browser-report.json");
const jsonText = JSON.stringify(report, null, 2)
  .replaceAll(repo.replaceAll("\\", "\\\\") + "\\\\", "")
  .replaceAll(repo.replaceAll("\\", "/") + "/", "")
  .replaceAll("\\\\", "/");
writeFileSync(outPath, jsonText, "utf8");
console.log(
  `Wrote ${outPath} (allPassed=${report.allPassed}, failures=${report.failures.length})`,
);
if (!report.allPassed) {
  console.error("Failures:", JSON.stringify(report.failures, null, 2));
  process.exit(1);
}
