#!/usr/bin/env node
/**
 * AXO Final Landing Cutover, Admin Auth & Integration Readiness Acceptance Runner.
 *
 * Runs against the live frontend (`http://localhost:3000`) backed by the real FastAPI
 * backend (`http://127.0.0.1:8000` via `/api` proxy) using an isolated test database.
 * Zero auth mocks; zero hardcoded secrets (all test credentials are supplied via env vars).
 *
 * Usage:
 *   node scripts/accept-landing-cutover-and-admin.mjs --out <json-path> --screenshots-dir <dir>
 *
 * Required env vars for real-backend auth verification:
 *   E2E_STUDENT_EMAIL, E2E_STUDENT_PASSWORD
 *   E2E_ADMIN_USERNAME (default: admin), E2E_ADMIN_EMAIL, E2E_ADMIN_PASSWORD
 */

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

function parseArgs(argv) {
  const args = {
    baseUrl: process.env.E2E_BASE_URL || "http://localhost:3000",
    out: null,
    screenshotsDir: null,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const k = argv[i];
    if (k === "--base-url" && argv[i + 1]) args.baseUrl = argv[++i];
    else if (k === "--out" && argv[i + 1]) args.out = argv[++i];
    else if (k === "--screenshots-dir" && argv[i + 1]) args.screenshotsDir = argv[++i];
  }
  return args;
}

const ARGS = parseArgs(process.argv);
const BASE = ARGS.baseUrl.replace(/\/+$/, "");
const OUT_DIR = ARGS.screenshotsDir
  ? path.resolve(ARGS.screenshotsDir)
  : path.resolve(process.cwd(), "tmp-acceptance-screenshots");
fs.mkdirSync(OUT_DIR, { recursive: true });

const STUDENT_EMAIL = (process.env.E2E_STUDENT_EMAIL || "").trim();
const STUDENT_PW = (process.env.E2E_STUDENT_PASSWORD || "").trim();
const STUDENT_NAME = (process.env.E2E_STUDENT_NAME || "Nguyễn Minh Anh").trim();
const ADMIN_USERNAME = (process.env.E2E_ADMIN_USERNAME || "admin").trim();
const ADMIN_EMAIL = (process.env.E2E_ADMIN_EMAIL || "").trim();
const ADMIN_PW = (process.env.E2E_ADMIN_PASSWORD || "").trim();

const VIEWPORTS = [
  { name: "1920x1080", width: 1920, height: 1080 },
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1366x768", width: 1366, height: 768 },
  { name: "768x1024", width: 768, height: 1024 },
  { name: "390x844", width: 390, height: 844 },
  { name: "375x812", width: 375, height: 812 },
  { name: "320x700", width: 320, height: 700 },
];

const report = {
  runAt: new Date().toISOString(),
  baseUrl: BASE,
  cutover: {},
  interactions: {},
  responsive: [],
  authRegression: {},
  adminAuthAndRbac: {},
  screenshots: [],
  unexpectedConsoleErrors: [],
  pageErrors: [],
  server5xx: [],
};

function shot(name) {
  const full = path.join(OUT_DIR, name);
  report.screenshots.push(full);
  return full;
}

function attachLogs(page, label) {
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      const text = msg.text();
      // Expected negative-auth status logs during intentional 401/403 RBAC/logout probes
      if ((label === "auth-regression" || label === "admin-rbac") && /status of (401|403)/.test(text)) {
        return;
      }
      report.unexpectedConsoleErrors.push({ label, text });
    }
  });
  page.on("pageerror", (err) => report.pageErrors.push({ label, text: String(err) }));
  page.on("response", (res) => {
    if (res.status() >= 500) {
      report.server5xx.push({ label, url: res.url(), status: res.status() });
    }
  });
}

(async () => {
  if (!STUDENT_EMAIL || !STUDENT_PW || !ADMIN_EMAIL || !ADMIN_PW) {
    console.error(
      "Missing required env vars: E2E_STUDENT_EMAIL, E2E_STUDENT_PASSWORD, E2E_ADMIN_EMAIL, E2E_ADMIN_PASSWORD",
    );
    process.exit(2);
  }

  const browser = await chromium.launch({ headless: true });

  // 1) GATE A & B: Canonical /about cutover + stale preview query cleanup + interactions
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    attachLogs(page, "cutover-and-interactions");

    // Direct /about (NO preview query)
    await page.goto(`${BASE}/about`, { waitUntil: "load" });
    await page.waitForSelector("#landing-hero");
    await page.waitForTimeout(400);
    await page.screenshot({ path: shot("cutover-about-default-1440.png") });

    const directAbout = await page.evaluate(() => ({
      pathname: window.location.pathname,
      search: window.location.search,
      heroHeading: document.querySelector("#axo-v14-hero-heading")?.textContent?.replace(/\s+/g, " ").trim() || "",
      hasAbout: Boolean(document.querySelector("#about-axo")),
      hasHow: Boolean(document.querySelector("#cach-hoat-dong")),
      hasSamples: Boolean(document.querySelector("#bai-mau")),
      hasFooter: Boolean(document.querySelector("#landing-footer")),
      headerZones: {
        logo: Boolean(document.querySelector("#btn-landing-logo")),
        navCount: document.querySelectorAll("#landing-header .axo-sp-nav-link").length,
        library: Boolean(document.querySelector("#btn-landing-header-library")),
        ctaText: document.querySelector("#btn-landing-header-start")?.textContent?.trim() || "",
      },
    }));

    // Legacy ?preview=landing-v14 URL must render same Landing and strip preview query to /about
    await page.goto(`${BASE}/about?preview=landing-v14`, { waitUntil: "load" });
    await page.waitForSelector("#landing-hero");
    await page.waitForTimeout(300);
    const afterLegacyPreview = await page.evaluate(() => ({
      pathname: window.location.pathname,
      search: window.location.search,
      hasHero: Boolean(document.querySelector("#landing-hero")),
    }));

    // Legacy /gioi-thieu?preview=v1.4 alias must canonicalize to /about
    await page.goto(`${BASE}/gioi-thieu?preview=v1.4`, { waitUntil: "load" });
    await page.waitForSelector("#landing-hero");
    await page.waitForTimeout(300);
    const afterLegacyAlias = await page.evaluate(() => ({
      pathname: window.location.pathname,
      search: window.location.search,
      hasHero: Boolean(document.querySelector("#landing-hero")),
    }));

    report.cutover = {
      directAbout,
      afterLegacyPreview,
      afterLegacyAlias,
      pass:
        directAbout.pathname === "/about" &&
        directAbout.search === "" &&
        directAbout.heroHeading.includes("Hình học không gian") &&
        directAbout.hasAbout &&
        directAbout.hasHow &&
        directAbout.hasSamples &&
        directAbout.hasFooter &&
        directAbout.headerZones.logo &&
        directAbout.headerZones.navCount === 3 &&
        directAbout.headerZones.library &&
        directAbout.headerZones.ctaText === "Bắt đầu" &&
        afterLegacyPreview.pathname === "/about" &&
        afterLegacyPreview.search === "" &&
        afterLegacyPreview.hasHero &&
        afterLegacyAlias.pathname === "/about" &&
        afterLegacyAlias.search === "" &&
        afterLegacyAlias.hasHero,
    };

    // Hover + Mouse Leave + Keyboard Focus + Parallax + Footer Top
    const aboutBtn = page.locator("#btn-landing-hero-about");
    const startBtn = page.locator("#btn-landing-hero-start");
    const readBox = (loc) =>
      loc.evaluate((el) => {
        const s = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        return {
          bg: s.backgroundColor,
          shadow: s.boxShadow,
          transform: s.transform,
          w: Math.round(r.width * 10) / 10,
          h: Math.round(r.height * 10) / 10,
          x: Math.round(r.x * 10) / 10,
          y: Math.round(r.y * 10) / 10,
        };
      });

    const defAbout = await readBox(aboutBtn);
    const defStart = await readBox(startBtn);
    await aboutBtn.hover();
    await page.waitForTimeout(260);
    const hovAbout = await readBox(aboutBtn);
    const hovStart = await readBox(startBtn);
    await page.mouse.move(10, 10);
    await page.waitForTimeout(260);
    const leaveAbout = await readBox(aboutBtn);

    await startBtn.focus();
    await page.keyboard.press("Tab");
    const focusAbout = await aboutBtn.evaluate((el) => ({
      active: document.activeElement === el,
      focusVisible: el.matches(":focus-visible"),
      outlineStyle: getComputedStyle(el).outlineStyle,
    }));

    const stageBox = await page.locator("#landing-hero-sculpture").boundingBox();
    let parallaxMoved = false;
    if (stageBox) {
      await page.mouse.move(stageBox.x + stageBox.width * 0.8, stageBox.y + stageBox.height * 0.3);
      await page.waitForTimeout(140);
      parallaxMoved = await page.evaluate(() =>
        Boolean(document.querySelector(".axo-v14-hero-atelier-diorama")?.getAttribute("style")?.includes("translate3d")),
      );
      await page.mouse.move(10, 10);
    }

    // Scroll to footer and verify "Trở về đầu trang" returns smoothly near top
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(250);
    const yBeforeTop = await page.evaluate(() => window.scrollY);
    await page.click("#btn-landing-footer-top");
    await page.waitForTimeout(700);
    const yAfterTop = await page.evaluate(() => window.scrollY);
    const backToTopWorks = yBeforeTop > 400 && yAfterTop < 120;

    report.interactions.desktop = {
      defAbout,
      hovAbout,
      leaveAbout,
      focusAbout,
      parallaxMoved,
      backToTopWorks,
      pass:
        defAbout.shadow === "none" &&
        hovAbout.transform === "matrix(1, 0, 0, 1, 0, -2)" &&
        hovAbout.bg !== "rgb(255, 255, 255)" &&
        hovAbout.shadow !== "none" &&
        !hovAbout.shadow.includes("18px") &&
        hovAbout.w === defAbout.w &&
        hovAbout.h === defAbout.h &&
        hovStart.x === defStart.x &&
        hovStart.y === defStart.y &&
        leaveAbout.transform === "none" &&
        leaveAbout.shadow === "none" &&
        focusAbout.active &&
        focusAbout.focusVisible &&
        focusAbout.outlineStyle === "solid" &&
        parallaxMoved &&
        backToTopWorks,
    };

    await ctx.close();
  }

  // 2) Reduced motion + Mobile touch & drawer
  {
    const ctxRm = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: "reduce" });
    const pageRm = await ctxRm.newPage();
    attachLogs(pageRm, "reduced-motion");
    await pageRm.goto(`${BASE}/about`, { waitUntil: "load" });
    await pageRm.waitForSelector("#btn-landing-hero-about");
    await pageRm.locator("#btn-landing-hero-about").hover();
    await pageRm.waitForTimeout(160);
    const rm = await pageRm.locator("#btn-landing-hero-about").evaluate((el) => {
      const s = getComputedStyle(el);
      return { transform: s.transform, shadow: s.boxShadow };
    });
    report.interactions.reducedMotion = { ...rm, pass: rm.transform === "none" && rm.shadow === "none" };
    await ctxRm.close();

    const ctxMob = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
    const pageMob = await ctxMob.newPage();
    attachLogs(pageMob, "mobile-drawer");
    await pageMob.goto(`${BASE}/about`, { waitUntil: "load" });
    await pageMob.waitForSelector("#btn-landing-mobile-menu");
    await pageMob.locator("#btn-landing-mobile-menu").tap();
    await pageMob.waitForSelector("#landing-mobile-drawer");
    await pageMob.waitForTimeout(250);
    await pageMob.screenshot({ path: shot("cutover-mobile-drawer-390.png") });
    const drawerState = await pageMob.evaluate(() => {
      const lib = document.querySelector("#btn-landing-drawer-library");
      const st = lib ? getComputedStyle(lib) : null;
      return {
        overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        libBorderTopColor: st?.borderTopColor,
        hasAccount: Boolean(document.querySelector("#landing-mobile-account")),
      };
    });
    await pageMob.keyboard.press("Escape");
    await pageMob.waitForTimeout(200);
    const scrollAfterClose = await pageMob.evaluate(() => {
      const closed = !document.querySelector("#landing-mobile-drawer");
      window.scrollTo(0, 340);
      const y = Math.round(window.scrollY);
      window.scrollTo(0, 0);
      return { closed, y };
    });
    report.interactions.mobileDrawer = {
      drawerState,
      scrollAfterClose,
      pass:
        drawerState.overflowX <= 0 &&
        drawerState.libBorderTopColor === "rgba(0, 0, 0, 0)" &&
        !drawerState.hasAccount &&
        scrollAfterClose.closed &&
        scrollAfterClose.y >= 300,
    };
    await ctxMob.close();
  }

  // 3) 7-Viewport Responsive Matrix directly on /about
  {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    attachLogs(page, "responsive-about");
    for (const vp of VIEWPORTS) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto(`${BASE}/about`, { waitUntil: "load" });
      await page.waitForSelector("#landing-hero");
      await page.waitForTimeout(300);

      const m = await page.evaluate(async () => {
        const html = document.documentElement;
        const start = document.querySelector("#btn-landing-hero-start")?.getBoundingClientRect();
        const about = document.querySelector("#btn-landing-hero-about")?.getBoundingClientRect();
        const stage = document.querySelector("#landing-hero-sculpture")?.getBoundingClientRect();
        const body = document.querySelector(".axo-v14-hero-atelier-body")?.getBoundingClientRect();
        const ov = (a, b) =>
          Boolean(a && b && a.left < b.right - 2 && a.right > b.left + 2 && a.top < b.bottom - 2 && a.bottom > b.top + 2);
        const overflowX = html.scrollWidth - html.clientWidth;
        const step = Math.max(300, Math.round(window.innerHeight * 0.7));
        for (let y = 0; y <= html.scrollHeight; y += step) {
          window.scrollTo(0, y);
          await new Promise((r) => setTimeout(r, 70));
        }
        window.scrollTo(0, 0);
        await new Promise((r) => setTimeout(r, 200));
        const imgs = Array.from(document.querySelectorAll("img"));
        const brokenImgs = imgs.filter((i) => !i.complete || i.naturalWidth === 0).length;
        return {
          overflowX,
          imgCount: imgs.length,
          brokenImgs,
          ctaOverlap: ov(start, about),
          heroOverlap: ov(body, stage),
          ctaAboutH: about ? Math.round(about.height) : 0,
        };
      });

      report.responsive.push({
        viewport: vp.name,
        ...m,
        pass: m.overflowX <= 0 && m.brokenImgs === 0 && !m.ctaOverlap && !m.heroOverlap && m.ctaAboutH >= 44,
      });
    }
    await ctx.close();
  }

  // 4) GATE D: Guest, Forgot Password, Registration, Student Login, Reload, Logout & Back/Forward
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    attachLogs(page, "auth-regression");

    // Guest -> /about -> Bắt đầu -> /login
    await page.goto(`${BASE}/about`, { waitUntil: "load" });
    await page.click("#btn-landing-header-start");
    await page.waitForSelector("#view-login");
    const loginLabel = (await page.locator('label[for="login-email-input"]').textContent())?.trim() || "";
    await page.screenshot({ path: shot("cutover-login-identifier-1440.png") });

    // Forgot password honest state (no fake form)
    await page.click("#btn-login-to-forgot");
    await page.waitForSelector("#forgot-unavailable-note", { timeout: 10000 });
    const forgotHasFakeForm = (await page.locator("#form-forgot").count()) > 0;
    await page.click("#btn-forgot-to-login");
    await page.waitForSelector("#view-login");

    // Public admin registration attempt must be blocked 403 by backend (even if legacy signup code is passed)
    const publicAdminRegStatus = await page.evaluate(async () => {
      const r = await fetch("/api/auth/register", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: `blocked.admin.${Date.now()}@axo.edu.vn`,
          displayName: "Blocked",
          password: "BlockedPassword123!",
          role: "admin",
          teacherCode: "LEGACY-CODE-BLOCKED",
        }),
      });
      return r.status;
    });

    // Student Login -> Workspace /app
    await page.fill("#login-email-input", STUDENT_EMAIL);
    await page.fill("#login-pw-input", STUDENT_PW);
    await page.click("#btn-login-submit");
    await page.waitForSelector("#sb-user-account-btn", { timeout: 10000 });
    await page.waitForTimeout(250);
    const studentLoginPath = new URL(page.url()).pathname;

    // Reload authenticated on /app
    await page.reload({ waitUntil: "load" });
    await page.waitForSelector("#sb-user-account-btn", { timeout: 10000 });
    const studentReloadOk = (await page.locator("#sb-user-account-btn").textContent())?.includes(STUDENT_NAME);

    // Student visits /about -> NO Avatar, CTA "Vào ứng dụng" -> /app
    await page.goto(`${BASE}/about`, { waitUntil: "load" });
    await page.waitForSelector("#landing-hero");
    await page.waitForTimeout(300);
    const studentOnLanding = await page.evaluate((name) => {
      const hdr = document.querySelector("#landing-header");
      return {
        hasAvatar: Boolean(hdr?.querySelector("#header-user-actions")),
        hasName: Boolean(hdr?.textContent?.includes(name)),
        cta: hdr?.querySelector("#btn-landing-header-start")?.textContent?.trim() || "",
      };
    }, STUDENT_NAME);

    // Student tries /admin directly -> BLOCKED UI (#view-admin-denied) AND backend 403!
    await page.goto(`${BASE}/admin`, { waitUntil: "load" });
    await page.waitForSelector("#view-admin-denied", { timeout: 10000 });
    const studentAdminApiStatus = await page.evaluate(async () => {
      const r = await fetch("/api/admin/overview", { credentials: "include" });
      return r.status;
    });

    // Return to /app and Logout -> MUST stay on /app Guest Workspace, /api/history 401
    await page.goto(`${BASE}/app`, { waitUntil: "load" });
    await page.waitForSelector("#sb-user-account-btn", { timeout: 10000 });
    await page.click("#sb-user-account-btn");
    await page.waitForSelector("#btn-sb-acc-logout");
    await page.click("#btn-sb-acc-logout");
    await page.waitForSelector("#sb-guest-account-btn", { timeout: 10000 });
    await page.waitForTimeout(300);
    const postLogout = await page.evaluate(async (name) => {
      const h = await fetch("/api/history", { credentials: "include" });
      return {
        pathname: window.location.pathname,
        hasGuestBtn: Boolean(document.querySelector("#sb-guest-account-btn")),
        leakedName: (document.body.innerText || "").includes(name),
        historyStatus: h.status,
      };
    }, STUDENT_NAME);

    // Back button after logout must not resurrect authenticated session
    await page.goBack().catch(() => null);
    await page.waitForTimeout(300);
    const backAfterLogoutSafe = await page.evaluate((name) => ({
      hasUserBtn: Boolean(document.querySelector("#sb-user-account-btn")),
      leakedName: (document.body.innerText || "").includes(name),
    }), STUDENT_NAME);

    report.authRegression = {
      loginLabel,
      forgotHasFakeForm,
      publicAdminRegStatus,
      studentLoginPath,
      studentReloadOk,
      studentOnLanding,
      studentAdminApiStatus,
      postLogout,
      backAfterLogoutSafe,
      pass:
        loginLabel === "Email hoặc tên đăng nhập" &&
        !forgotHasFakeForm &&
        publicAdminRegStatus === 403 &&
        studentLoginPath === "/app" &&
        Boolean(studentReloadOk) &&
        !studentOnLanding.hasAvatar &&
        !studentOnLanding.hasName &&
        studentOnLanding.cta === "Vào ứng dụng" &&
        studentAdminApiStatus === 403 &&
        postLogout.pathname === "/app" &&
        postLogout.hasGuestBtn &&
        !postLogout.leakedName &&
        postLogout.historyStatus === 401 &&
        !backAfterLogoutSafe.hasUserBtn &&
        !backAfterLogoutSafe.leakedName,
    };

    await ctx.close();
  }

  // 5) GATE C: Admin Login via username ("admin") AND via email (same single account), /admin console & RBAC
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    attachLogs(page, "admin-rbac");

    // Guest direct /admin -> denied UI + backend 401
    await page.goto(`${BASE}/admin`, { waitUntil: "load" });
    await page.waitForSelector("#view-admin-denied", { timeout: 10000 });
    const guestAdminApiStatus = await page.evaluate(async () => {
      const r = await fetch("/api/admin/overview", { credentials: "include" });
      return r.status;
    });

    // Admin login via USERNAME ("admin") on shared /login
    await page.goto(`${BASE}/login`, { waitUntil: "load" });
    await page.waitForSelector("#login-email-input");
    await page.fill("#login-email-input", ADMIN_USERNAME);
    await page.fill("#login-pw-input", ADMIN_PW);
    await page.click("#btn-login-submit");
    await page.waitForFunction(() => window.location.pathname === "/admin" && !document.querySelector("#view-admin-denied"), null, {
      timeout: 10000,
    });
    await page.waitForTimeout(450);
    await page.screenshot({ path: shot("cutover-admin-console-1440.png") });

    const byUsernameState = await page.evaluate(async () => {
      const me = await (await fetch("/api/auth/me", { credentials: "include" })).json();
      const ov = await fetch("/api/admin/overview", { credentials: "include" });
      return {
        pathname: window.location.pathname,
        hasDeniedView: Boolean(document.querySelector("#view-admin-denied")),
        userId: me?.user?.id ?? null,
        role: me?.user?.role ?? null,
        username: me?.user?.username ?? null,
        email: me?.user?.email ?? null,
        overviewStatus: ov.status,
      };
    });

    // Reload /admin stays authenticated
    await page.reload({ waitUntil: "load" });
    await page.waitForFunction(() => window.location.pathname === "/admin" && !document.querySelector("#view-admin-denied"), null, {
      timeout: 10000,
    });

    // Admin visits /about -> NO Avatar, "Vào ứng dụng" -> back to /admin
    await page.goto(`${BASE}/about`, { waitUntil: "load" });
    await page.waitForSelector("#landing-hero");
    await page.waitForTimeout(300);
    const adminOnLandingNoAvatar = await page.evaluate(() => !document.querySelector("#header-user-actions"));
    await page.click("#btn-landing-header-start");
    await page.waitForFunction(() => window.location.pathname === "/admin", null, { timeout: 10000 });

    // Logout admin session via API + verify 401
    await page.evaluate(async () => {
      await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    });
    const afterAdminLogoutStatus = await page.evaluate(async () => {
      const r = await fetch("/api/admin/overview", { credentials: "include" });
      return r.status;
    });

    // Admin login via EMAIL on shared /login -> MUST resolve to EXACT SAME userId!
    await page.goto(`${BASE}/login`, { waitUntil: "load" });
    await page.waitForSelector("#login-email-input");
    await page.fill("#login-email-input", ADMIN_EMAIL);
    await page.fill("#login-pw-input", ADMIN_PW);
    await page.click("#btn-login-submit");
    await page.waitForFunction(() => window.location.pathname === "/admin" && !document.querySelector("#view-admin-denied"), null, {
      timeout: 10000,
    });
    await page.waitForTimeout(300);

    const byEmailState = await page.evaluate(async () => {
      const me = await (await fetch("/api/auth/me", { credentials: "include" })).json();
      const ov = await fetch("/api/admin/overview", { credentials: "include" });
      return {
        pathname: window.location.pathname,
        userId: me?.user?.id ?? null,
        role: me?.user?.role ?? null,
        email: me?.user?.email ?? null,
        overviewStatus: ov.status,
      };
    });

    report.adminAuthAndRbac = {
      guestAdminApiStatus,
      byUsernameState,
      adminOnLandingNoAvatar,
      afterAdminLogoutStatus,
      byEmailState,
      sameSingleAccount: byUsernameState.userId !== null && byUsernameState.userId === byEmailState.userId,
      pass:
        guestAdminApiStatus === 401 &&
        byUsernameState.pathname === "/admin" &&
        !byUsernameState.hasDeniedView &&
        byUsernameState.role === "admin" &&
        byUsernameState.username === ADMIN_USERNAME &&
        byUsernameState.overviewStatus === 200 &&
        adminOnLandingNoAvatar &&
        afterAdminLogoutStatus === 401 &&
        byEmailState.pathname === "/admin" &&
        byEmailState.role === "admin" &&
        byEmailState.overviewStatus === 200 &&
        byUsernameState.userId === byEmailState.userId,
    };

    await ctx.close();
  }

  await browser.close();

  const outPath = ARGS.out ? path.resolve(ARGS.out) : path.join(OUT_DIR, "acceptance-results.json");
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2), "utf8");

  const checks = [
    ["GATE_A_B_cutover", report.cutover.pass],
    ["interactions_desktop", report.interactions.desktop?.pass],
    ["interactions_reducedMotion", report.interactions.reducedMotion?.pass],
    ["interactions_mobileDrawer", report.interactions.mobileDrawer?.pass],
    ...report.responsive.map((r) => [`responsive_${r.viewport}`, r.pass]),
    ["GATE_D_authRegression", report.authRegression.pass],
    ["GATE_C_adminAuthAndRbac", report.adminAuthAndRbac.pass],
    ["zeroUnexpectedConsoleErrors", report.unexpectedConsoleErrors.length === 0],
    ["zeroPageErrors", report.pageErrors.length === 0],
    ["zeroServer5xx", report.server5xx.length === 0],
  ];

  console.log("=== FINAL CUTOVER & ADMIN ACCEPTANCE ===");
  for (const [k, ok] of checks) {
    console.log(`  [${ok ? "PASS" : "FAIL"}] ${k}`);
  }
  console.log(`Report JSON: ${outPath}`);
  if (checks.some(([, ok]) => !ok)) {
    process.exit(1);
  }
})();
