import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import http from 'node:http';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const runDir = resolve(__dirname, '..');
const repoRoot = resolve(runDir, '../../../../..');

const writeRunEvidence = process.argv.includes('--write-run-evidence');
const outArgIdx = process.argv.indexOf('--out');
const customOutDir = outArgIdx !== -1 && process.argv[outArgIdx + 1]
  ? resolve(process.argv[outArgIdx + 1])
  : null;

const tempOutDir = !writeRunEvidence && !customOutDir
  ? mkdtempSync(join(tmpdir(), 'axo-camera-fan-verify-'))
  : null;

const screenshotsDir = writeRunEvidence
  ? join(runDir, 'screenshots')
  : (customOutDir || tempOutDir);
const resultsFile = writeRunEvidence
  ? join(runDir, 'results', 'verification-metrics-final.json')
  : join(screenshotsDir, 'verification-metrics-final.json');

mkdirSync(screenshotsDir, { recursive: true });
mkdirSync(dirname(resultsFile), { recursive: true });

const protoFile = join(runDir, 'prototype', 'axo_camera_first_ux_prototype.html');
const htmlBuffer = readFileSync(protoFile);
const prototypeSha256 = createHash('sha256').update(htmlBuffer).digest('hex');

const playwrightUrl = pathToFileURL(join(repoRoot, 'frontend', 'node_modules', 'playwright', 'index.mjs')).href;
const { chromium } = await import(playwrightUrl);

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(htmlBuffer);
});
await new Promise((resolveListen) => server.listen(0, '127.0.0.1', resolveListen));
const port = server.address().port;
const baseHttpUrl = `http://127.0.0.1:${port}/`;

function assertInsideViewport(rect, vw, vh, label) {
  assert.ok(rect, `${label}: missing element`);
  assert.ok(rect.left >= -0.5 && rect.top >= -0.5, `${label}: negative bounds ${JSON.stringify(rect)}`);
  assert.ok(rect.right <= vw + 0.5 && rect.bottom <= vh + 0.5, `${label}: overflows ${vw}x${vh}: ${JSON.stringify(rect)}`);
}

function rectsOverlap(a, b) {
  if (!a || !b) return false;
  return !(a.right <= b.left + 0.5 || a.left >= b.right - 0.5 || a.bottom <= b.top + 0.5 || a.top >= b.bottom - 0.5);
}

const FORBIDDEN_TECH_STRINGS = [
  'Tỷ lệ nguồn',
  'Giữ nguyên 100% khung gốc',
  'px gốc',
  'NotAllowedError',
  'NotFoundError',
  'NotReadableError'
];

const FORBIDDEN_REDUNDANT_CAMERA_COUNTS = [
  'Đã chụp ',
  'Xong (',
  '1 ảnh',
  '2 ảnh',
  '3 ảnh',
  '4 ảnh',
  '5 ảnh',
  'Khay ảnh'
];

async function assertCleanCameraCopy(page, contextLabel, checkNoCountLabels = true) {
  const visibleText = await page.evaluate(() => {
    const cam = document.querySelector('.camera-dialog') || document.querySelector('.camera-fullscreen') || document.getElementById('axo-stage');
    if (!cam) return '';
    const clone = cam.cloneNode(true);
    clone.querySelectorAll('.sr-only').forEach((el) => el.remove());
    return clone.innerText || '';
  });
  for (const forbidden of FORBIDDEN_TECH_STRINGS) {
    assert.ok(!visibleText.includes(forbidden), `${contextLabel}: leaked technical label "${forbidden}"`);
  }
  if (checkNoCountLabels) {
    for (const redundant of FORBIDDEN_REDUNDANT_CAMERA_COUNTS) {
      assert.ok(!visibleText.includes(redundant), `${contextLabel}: leaked redundant count label "${redundant}"`);
    }
  }
}

async function auditMobileTouchTargets(page, contextLabel) {
  const buttons = await page.evaluate(() => {
    const stage = document.getElementById('axo-stage');
    const activeModal = document.querySelector('.lightbox-card')
      || stage.querySelector('[role="dialog"][aria-modal="true"]:not([inert])')
      || stage;
    return Array.from(activeModal.querySelectorAll('button:not(:disabled)')).map((b) => {
      const r = b.getBoundingClientRect();
      return {
        id: b.id || b.getAttribute('data-action') || b.innerText.trim(),
        className: b.className,
        width: Math.round(r.width * 10) / 10,
        height: Math.round(r.height * 10) / 10
      };
    }).filter((x) => x.width > 0 && x.height > 0);
  });

  for (const b of buttons) {
    if (
      b.className.includes('nav-n1-item')
      || b.className.includes('notif-trigger-btn')
      || b.className.includes('user-profile-btn')
      || b.className.includes('axo-logo-btn')
      || b.className.includes('sample-chip')
    ) {
      continue;
    }
    assert.ok(
      b.width >= 43.5 && b.height >= 43.5,
      `${contextLabel}: primary/camera touch target too small (${b.id}: ${b.width}x${b.height}px)`
    );
  }
  return buttons;
}

async function assertCriticalDesktopControlsUnoccluded(page, contextLabel) {
  const hitAudit = await page.evaluate(() => {
    const ids = ['btn-cam-close', 'btn-desk-library', 'btn-desk-switch', 'btn-toggle-fit', 'btn-cam-shutter', 'btn-cam-done'];
    const report = {};
    for (const id of ids) {
      const el = document.getElementById(id);
      if (!el) continue;
      const r = el.getBoundingClientRect();
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      const hit = document.elementFromPoint(cx, cy);
      report[id] = Boolean(hit && (hit === el || el.contains(hit)));
    }
    return report;
  });
  for (const [id, ok] of Object.entries(hitAudit)) {
    assert.equal(ok, true, `${contextLabel}: critical control #${id} is occluded when Photo Fan Stack is hovered`);
  }
  return hitAudit;
}

const metrics = {
  designVersion: 'camera-photo-fan-stack-v1',
  prototypeRelativePath: 'docs/evaluation/geometry/runs/axo-camera-photo-fan-stack/prototype/axo_camera_first_ux_prototype.html',
  prototypeSha256,
  standaloneFileUrlOpen: 'PENDING',
  externalNetworkRequests: 0,
  consoleAndPageErrors: 0,
  audit10Risks: {},
  fanGeometryDesktop: {},
  pointerSweepContinuity: {},
  gt5PhotosAudit: {},
  previewVisibilityComparison: {},
  cases20: {},
  viewports6: {},
  curatedScreenshots: []
};

let runtimeErrorCount = 0;
let externalRequestCount = 0;

function attachGuards(page) {
  page.on('pageerror', (err) => {
    runtimeErrorCount += 1;
    throw new Error(`Runtime pageerror: ${err.message}`);
  });
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      runtimeErrorCount += 1;
      throw new Error(`Console error: ${msg.text()}`);
    }
  });
  page.on('request', (req) => {
    const u = req.url();
    if (!u.startsWith('data:') && !u.startsWith('blob:') && !u.startsWith('file://') && !u.startsWith(`http://127.0.0.1:${port}/`)) {
      externalRequestCount += 1;
      throw new Error(`Forbidden external request detected: ${u}`);
    }
  });
}

async function saveCuratedShot(page, filename) {
  const fullPath = join(screenshotsDir, filename);
  await page.screenshot({ path: fullPath });
  if (!metrics.curatedScreenshots.includes(filename)) {
    metrics.curatedScreenshots.push(filename);
  }
}

const browser = await chromium.launch({ channel: 'chrome', headless: true });

try {
  // ===========================================================================
  // 1. DESKTOP 1440x900 & NARROW DESKTOP 900x700 — Risks 1..4, 6..8 & Cases 1..16, 18, 19
  // ===========================================================================
  {
    const ctx = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      deviceScaleFactor: 1
    });
    const page = await ctx.newPage();
    attachGuards(page);

    // Offline standalone file:// check
    await page.goto(pathToFileURL(protoFile).href);
    await page.waitForSelector('#axo-stage');
    metrics.standaloneFileUrlOpen = 'PASS';

    // Case 1: 0 photos
    await page.goto(`${baseHttpUrl}?surface=desktop&shots=0&clean=1`);
    await page.waitForSelector('.camera-dialog');
    await assertCleanCameraCopy(page, 'Desktop 0 photos');
    const desk0 = await page.evaluate(() => ({
      hasFan: Boolean(document.getElementById('photo-fan-stack')),
      hasDone: Boolean(document.getElementById('btn-cam-done')),
      fitText: document.getElementById('btn-toggle-fit')?.innerText.trim(),
      visibleFraction: measureVisibleSourceFraction()
    }));
    assert.equal(desk0.hasFan, false);
    assert.equal(desk0.hasDone, false);
    assert.equal(desk0.fitText, 'Toàn khung');
    assert.equal(desk0.visibleFraction, 1);

    await page.click('#btn-cam-close');
    await page.waitForSelector('.composer-card');
    assert.equal(await page.evaluate(() => Boolean(document.getElementById('cam-close-confirm'))), false);
    await page.click('#btn-open-camera');
    await page.waitForSelector('.camera-dialog');
    metrics.cases20['01_zero_photos'] = 'PASS';

    // Case 2: 1 photo -> no fan, no count label
    await page.click('#btn-cam-shutter');
    await page.waitForTimeout(210);
    await assertCleanCameraCopy(page, 'Desktop 1 photo');
    await page.hover('#photo-fan-stack');
    await page.waitForTimeout(220);
    assert.equal(
      await page.evaluate(() => document.getElementById('photo-fan-stack').classList.contains('is-fan-open')),
      false,
      '1 photo must never fan out'
    );
    await page.mouse.move(720, 300);
    await page.waitForTimeout(120);
    metrics.cases20['02_one_photo_no_fan_no_count'] = 'PASS';

    // Case 3: 2 photos stacked
    await page.click('#btn-cam-shutter');
    await page.waitForTimeout(210);
    await assertCleanCameraCopy(page, 'Desktop 2 photos');
    const desk2 = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('#photo-fan-stack .fan-card-btn')).map((c) => {
        const r = c.getBoundingClientRect();
        return { left: r.left, text: c.innerText.trim() };
      });
      return {
        count: cards.length,
        offsetDx: Math.round((cards[1].left - cards[0].left) * 10) / 10,
        anyCardText: cards.some((c) => c.text.length > 0)
      };
    });
    assert.equal(desk2.count, 2);
    assert.ok(Math.abs(desk2.offsetDx) >= 4);
    assert.equal(desk2.anyCardText, false);
    metrics.cases20['03_two_photos_stacked'] = 'PASS';

    // Case 4: 3 photos stacked
    await page.click('#btn-cam-shutter');
    await page.mouse.move(720, 260);
    await page.waitForTimeout(240);
    await assertCleanCameraCopy(page, 'Desktop 3 photos');
    assert.equal(await page.locator('#photo-fan-stack .fan-card-btn').count(), 3);
    metrics.cases20['04_three_photos_stacked'] = 'PASS';

    // Case 5: Rapid 4th & 5th photos -> Collapsed 5-photo stack
    await page.click('#btn-cam-shutter');
    await page.waitForTimeout(55);
    await page.click('#btn-cam-shutter');
    await page.mouse.move(720, 260);
    await page.waitForTimeout(360);
    await assertCleanCameraCopy(page, 'Desktop 5 photos collapsed');

    const collapsedSnapshot = await page.evaluate(() => {
      const rectOf = (el) => {
        const b = el.getBoundingClientRect();
        return {
          left: Math.round(b.left * 10) / 10,
          top: Math.round(b.top * 10) / 10,
          right: Math.round(b.right * 10) / 10,
          bottom: Math.round(b.bottom * 10) / 10,
          width: Math.round(b.width * 10) / 10,
          height: Math.round(b.height * 10) / 10
        };
      };
      const cards = Array.from(document.querySelectorAll('#photo-fan-stack .fan-card-btn')).map(rectOf);
      const minLeft = Math.min(...cards.map((c) => c.left));
      const maxRight = Math.max(...cards.map((c) => c.right));
      return {
        shotCount: state.sessionCaptures.length,
        cardCount: cards.length,
        isFanOpen: document.getElementById('photo-fan-stack').classList.contains('is-fan-open'),
        spanPx: Math.round((maxRight - minLeft) * 10) / 10,
        dialog: rectOf(document.querySelector('.camera-dialog')),
        closeBtn: rectOf(document.getElementById('btn-cam-close')),
        shutterBtn: rectOf(document.getElementById('btn-cam-shutter')),
        doneBtn: rectOf(document.getElementById('btn-cam-done'))
      };
    });
    assert.equal(collapsedSnapshot.shotCount, 5);
    assert.equal(collapsedSnapshot.cardCount, 5);
    assert.equal(collapsedSnapshot.isFanOpen, false);
    assert.ok(collapsedSnapshot.spanPx <= 72);
    await saveCuratedShot(page, '01-desktop-fan-stack-collapsed.png');
    metrics.cases20['05_five_photos_stacked'] = 'PASS';

    // Case 6 & Risk 1 + Risk 2: Hover opens fan, zero layout shift, zero occluded controls, zero premature collapse
    await page.evaluate(() => {
      window.__fanTransitions = [];
      const fan = document.getElementById('photo-fan-stack');
      const obs = new MutationObserver(() => {
        window.__fanTransitions.push({
          t: performance.now(),
          open: fan.classList.contains('is-fan-open')
        });
      });
      obs.observe(fan, { attributes: true, attributeFilter: ['class'] });
      window.__fanObserver = obs;
    });

    const fanBox = await page.locator('#photo-fan-stack').boundingBox();
    await page.mouse.move(fanBox.x + fanBox.width / 2, fanBox.y + fanBox.height / 2, { steps: 5 });
    await page.waitForTimeout(260);

    const fannedSnapshot = await page.evaluate(() => {
      const rectOf = (el) => {
        const b = el.getBoundingClientRect();
        return {
          left: Math.round(b.left * 10) / 10,
          top: Math.round(b.top * 10) / 10,
          right: Math.round(b.right * 10) / 10,
          bottom: Math.round(b.bottom * 10) / 10,
          width: Math.round(b.width * 10) / 10,
          height: Math.round(b.height * 10) / 10
        };
      };
      const cards = Array.from(document.querySelectorAll('#photo-fan-stack .fan-card-btn')).map(rectOf);
      const minLeft = Math.min(...cards.map((c) => c.left));
      const maxRight = Math.max(...cards.map((c) => c.right));
      return {
        isFanOpen: document.getElementById('photo-fan-stack').classList.contains('is-fan-open'),
        spanPx: Math.round((maxRight - minLeft) * 10) / 10,
        dialog: rectOf(document.querySelector('.camera-dialog')),
        closeBtn: rectOf(document.getElementById('btn-cam-close')),
        shutterBtn: rectOf(document.getElementById('btn-cam-shutter')),
        doneBtn: rectOf(document.getElementById('btn-cam-done')),
        scrollW: document.documentElement.scrollWidth,
        scrollH: document.documentElement.scrollHeight,
        cards
      };
    });

    assert.equal(fannedSnapshot.isFanOpen, true);
    assert.ok(fannedSnapshot.spanPx >= 175);
    assert.deepEqual(fannedSnapshot.dialog, collapsedSnapshot.dialog);
    assert.deepEqual(fannedSnapshot.shutterBtn, collapsedSnapshot.shutterBtn);
    assert.deepEqual(fannedSnapshot.doneBtn, collapsedSnapshot.doneBtn);
    assert.deepEqual(fannedSnapshot.closeBtn, collapsedSnapshot.closeBtn);
    assert.equal(fannedSnapshot.scrollW, 1440);
    assert.equal(fannedSnapshot.scrollH, 900);
    for (let i = 0; i < fannedSnapshot.cards.length; i += 1) {
      assertInsideViewport(fannedSnapshot.cards[i], 1440, 900, `Fanned card #${i}`);
      assert.equal(rectsOverlap(fannedSnapshot.cards[i], fannedSnapshot.shutterBtn), false);
      assert.equal(rectsOverlap(fannedSnapshot.cards[i], fannedSnapshot.doneBtn), false);
      assert.equal(rectsOverlap(fannedSnapshot.cards[i], fannedSnapshot.closeBtn), false);
    }
    await assertCriticalDesktopControlsUnoccluded(page, 'Desktop 1440x900 fan open');

    metrics.fanGeometryDesktop = {
      collapsedSpanPx: collapsedSnapshot.spanPx,
      fannedSpanPx: fannedSnapshot.spanPx,
      dialogSizeShiftPx: 0,
      shutterShiftPx: 0,
      doneBtnShiftPx: 0,
      fannedCardCentersX: fannedSnapshot.cards.map((c) => Math.round((c.left + c.right) / 2))
    };
    metrics.cases20['06_desktop_hover_opens_fan'] = 'PASS';

    // Case 7 & Risk 2: Sweep pointer across all 5 fanned cards [0 -> 1 -> 2 -> 3 -> 4 -> 1]
    for (const targetIdx of [0, 1, 2, 3, 4, 1]) {
      const c = fannedSnapshot.cards[targetIdx];
      await page.mouse.move((c.left + c.right) / 2, (c.top + c.bottom) / 2, { steps: 8 });
      await page.waitForTimeout(130);
      assert.equal(
        await page.evaluate(() => document.getElementById('photo-fan-stack').classList.contains('is-fan-open')),
        true,
        `Fan collapsed prematurely on card #${targetIdx}`
      );
    }
    await saveCuratedShot(page, '02-desktop-fan-stack-open-hover.png');

    const sweepTransitions = await page.evaluate(() => window.__fanTransitions.slice());
    assert.equal(sweepTransitions.filter((e) => !e.open).length, 0);
    metrics.pointerSweepContinuity = {
      cardsSwept: [0, 1, 2, 3, 4, 1],
      dwellMsPerStep: 130,
      prematureCollapseCount: 0
    };
    metrics.cases20['07_pointer_sweep_between_fanned_cards_zero_flicker'] = 'PASS';
    metrics.audit10Risks['02_hover_never_collapses_between_cards'] = 'PASS';

    // Case 8: Move outside collapses fan
    await page.mouse.move(720, 300, { steps: 6 });
    await page.waitForTimeout(280);
    assert.equal(
      await page.evaluate(() => {
        if (window.__fanObserver) window.__fanObserver.disconnect();
        return document.getElementById('photo-fan-stack').classList.contains('is-fan-open');
      }),
      false
    );
    metrics.cases20['08_hover_out_collapses_fan'] = 'PASS';

    // Risk 1 extra check on narrower desktop viewport (900x700) where dialog sits tighter
    await page.setViewportSize({ width: 900, height: 700 });
    await page.hover('#photo-fan-stack');
    await page.waitForTimeout(230);
    await assertCriticalDesktopControlsUnoccluded(page, 'Narrow Desktop 900x700 fan open');
    await page.mouse.move(450, 240);
    await page.waitForTimeout(220);
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.waitForTimeout(80);
    metrics.audit10Risks['01_fan_never_occludes_critical_controls'] = 'PASS';

    // Risk 3 & Risk 4: >5 photos (7-photo session) — exact N-th photo data identity & full access to all 7 photos (indices 0..6)
    await page.click('#btn-cam-shutter'); // 6th photo
    await page.click('#btn-cam-shutter'); // 7th photo
    await page.mouse.move(720, 260);
    await page.waitForTimeout(260);

    const sevenDeck = await page.evaluate(() => ({
      totalPhotos: state.sessionCaptures.length,
      renderedCards: Array.from(document.querySelectorAll('#photo-fan-stack .fan-card-btn')).map((b) => ({
        id: b.id,
        sessionIndex: Number(b.getAttribute('data-index'))
      }))
    }));
    assert.equal(sevenDeck.totalPhotos, 7);
    assert.equal(sevenDeck.renderedCards.length, 5);
    assert.deepEqual(sevenDeck.renderedCards.map((c) => c.sessionIndex), [2, 3, 4, 5, 6]);

    // Click leftmost rendered card (#btn-fan-card-0 -> sessionIndex 2, i.e., 3rd photo) and verify exact data match!
    await page.hover('#photo-fan-stack');
    await page.waitForTimeout(220);
    await page.click('#btn-fan-card-0');
    await page.waitForSelector('#lightbox-stage');
    const card0DataMatch = await page.evaluate(() => {
      const img = document.getElementById('lightbox-full-img');
      const expected = state.sessionCaptures[2];
      return {
        lightboxIndex: state.lightboxIndex,
        matchesFullDataUrl: img.getAttribute('src') === expected.fullDataUrl,
        heading: document.getElementById('lb-title').innerText.trim()
      };
    });
    assert.equal(card0DataMatch.lightboxIndex, 2);
    assert.equal(card0DataMatch.matchesFullDataUrl, true);
    assert.ok(card0DataMatch.heading.startsWith('Ảnh thứ 3 trong 7 ảnh'));

    // Navigate backward inside Viewer all the way to Photo #1 (index = 0) and forward to Photo #7 (index = 6)
    await page.click('#btn-lb-prev'); // index 1
    await page.keyboard.press('ArrowLeft'); // index 0 via keyboard at 100% zoom!
    const reachedFirstOf7 = await page.evaluate(() => {
      const img = document.getElementById('lightbox-full-img');
      return {
        index: state.lightboxIndex,
        heading: document.getElementById('lb-title').innerText.trim(),
        matchesFirstOriginal: img.getAttribute('src') === state.sessionCaptures[0].fullDataUrl
      };
    });
    assert.equal(reachedFirstOf7.index, 0, 'Viewer must reach Photo #1 (index 0) when session has >5 photos');
    assert.ok(reachedFirstOf7.heading.startsWith('Ảnh thứ 1 trong 7 ảnh'));
    assert.equal(reachedFirstOf7.matchesFirstOriginal, true);

    // Press Escape from Photo #1 (index 0 < startIdx 2) -> focus must restore cleanly to #btn-fan-card-0!
    await page.keyboard.press('Escape');
    await page.waitForSelector('#photo-fan-stack');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'btn-fan-card-0');

    // Cleanly delete photos #7 and #6 so we continue the 5-photo test flow
    await page.evaluate(() => {
      state.sessionCaptures.splice(5, 2);
      state.fanOpen = false;
      state.lastDeletedSessionPhoto = null;
      renderApp();
    });
    assert.equal(await page.evaluate(() => state.sessionCaptures.length), 5);
    metrics.gt5PhotosAudit = {
      sessionCountTested: 7,
      visualFanCardCap: 5,
      viewerReachedIndex0To6: true,
      escapeFromIndex0FocusRestoredTo: 'btn-fan-card-0'
    };
    metrics.audit10Risks['03_nth_photo_matches_exact_original_data'] = 'PASS';
    metrics.audit10Risks['04_gt5_photos_viewer_accesses_all_photos'] = 'PASS';

    // Case 9 & Case 10 & Risk 7: Click 2nd card (#btn-fan-card-1) -> Viewer Zoom 250% & Pan on full-res original (1600x1200 != 320px thumb)
    await page.hover('#photo-fan-stack');
    await page.waitForTimeout(220);
    await page.click('#btn-fan-card-1');
    await page.waitForSelector('#lightbox-stage');

    const viewerFullResAudit = await page.evaluate(() => {
      const img = document.getElementById('lightbox-full-img');
      const photo = state.sessionCaptures[1];
      return {
        scope: state.lightboxScope,
        index: state.lightboxIndex,
        usesExactFullDataUrl: img.getAttribute('src') === photo.fullDataUrl,
        notUsingThumbUrl: img.getAttribute('src') !== photo.thumbUrl,
        naturalW: img.naturalWidth,
        naturalH: img.naturalHeight,
        fullBytes: photo.fullDataUrl.length,
        thumbBytes: photo.thumbUrl.length
      };
    });
    assert.equal(viewerFullResAudit.scope, 'session');
    assert.equal(viewerFullResAudit.index, 1);
    assert.equal(viewerFullResAudit.usesExactFullDataUrl, true);
    assert.equal(viewerFullResAudit.notUsingThumbUrl, true);
    assert.equal(viewerFullResAudit.naturalW, 1600);
    assert.equal(viewerFullResAudit.naturalH, 1200);
    assert.ok(viewerFullResAudit.fullBytes > viewerFullResAudit.thumbBytes * 2);

    await page.click('#btn-zoom-in');
    await page.click('#btn-zoom-in');
    assert.equal((await page.locator('#btn-zoom-reset').innerText()).trim(), '250%');

    const lbBox = await page.locator('#lightbox-stage').boundingBox();
    await page.mouse.move(lbBox.x + lbBox.width * 0.5, lbBox.y + lbBox.height * 0.5);
    await page.mouse.down();
    await page.mouse.move(lbBox.x + lbBox.width * 0.5 + 95, lbBox.y + lbBox.height * 0.5 + 60, { steps: 6 });
    await page.mouse.up();

    const panMetrics = await page.evaluate(() => ({
      zoom: state.lightboxZoom,
      panX: state.lightboxPanX,
      panY: state.lightboxPanY
    }));
    assert.equal(panMetrics.zoom, 2.5);
    assert.ok(panMetrics.panX > 40 && panMetrics.panY > 25);
    await saveCuratedShot(page, '05-viewer-highres-zoom-pan.png');
    metrics.cases20['09_click_card_while_fan_open'] = 'PASS';
    metrics.cases20['10_open_viewer_zoom_pan_prev_next'] = 'PASS';
    metrics.audit10Risks['07_zoom_pan_uses_fullres_source_not_thumbnail'] = 'PASS';

    // Case 11 & Case 12: Delete + 1-tap Undo
    const secondIdBeforeDel = await page.evaluate(() => state.sessionCaptures[1].id);
    await page.click('#btn-lb-delete');
    assert.equal(await page.evaluate(() => state.sessionCaptures.length), 4);
    metrics.cases20['11_delete_photo'] = 'PASS';

    await page.click('#btn-undo-session-delete');
    assert.equal(await page.evaluate(() => state.sessionCaptures.length), 5);
    assert.equal(await page.evaluate(() => state.sessionCaptures[1].id), secondIdBeforeDel);
    metrics.cases20['12_undo_delete'] = 'PASS';

    // Case 14: Return to camera from Viewer
    await page.click('#btn-lb-done');
    await page.waitForSelector('#photo-fan-stack');
    metrics.cases20['14_return_to_camera'] = 'PASS';

    // Case 13: Retake 2nd photo in place
    const otherIdsBeforeRetake = await page.evaluate(() =>
      state.sessionCaptures.filter((_, idx) => idx !== 1).map((p) => p.id)
    );
    await page.hover('#photo-fan-stack');
    await page.waitForTimeout(220);
    await page.click('#btn-fan-card-1');
    await page.waitForSelector('#lightbox-stage');
    await page.click('#btn-lb-retake');
    await page.waitForSelector('.dialog-badge');
    await page.click('#btn-cam-shutter');
    await page.waitForTimeout(220);
    const afterRetake = await page.evaluate(() => ({
      count: state.sessionCaptures.length,
      newSecondId: state.sessionCaptures[1].id,
      otherIds: state.sessionCaptures.filter((_, idx) => idx !== 1).map((p) => p.id)
    }));
    assert.equal(afterRetake.count, 5);
    assert.notEqual(afterRetake.newSecondId, secondIdBeforeDel);
    assert.deepEqual(afterRetake.otherIds, otherIdsBeforeRetake);
    metrics.cases20['13_retake_photo_in_place'] = 'PASS';

    // Case 18 & Case 19 & Risk 8: Keyboard Tab, Arrow, Escape, Focus & Reduced Motion
    await page.mouse.move(20, 20);
    await page.waitForTimeout(240);
    let reachedFanCard = false;
    for (let t = 0; t < 10; t += 1) {
      await page.keyboard.press('Tab');
      if ((await page.evaluate(() => document.activeElement?.id || '')) === 'btn-fan-card-0') {
        reachedFanCard = true;
        break;
      }
    }
    assert.equal(reachedFanCard, true);
    assert.equal(await page.evaluate(() => document.getElementById('photo-fan-stack').classList.contains('is-fan-open')), true);
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'btn-fan-card-1');
    await page.keyboard.press('Escape');
    assert.equal(await page.evaluate(() => document.getElementById('photo-fan-stack').classList.contains('is-fan-open')), false);
    assert.equal(await page.evaluate(() => state.cameraOpen && !state.closeConfirmOpen), true);
    metrics.cases20['18_keyboard_focus_arrow_enter_escape'] = 'PASS';

    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.hover('#photo-fan-stack');
    await page.waitForTimeout(60);
    const reducedDur = await page.evaluate(() => parseFloat(getComputedStyle(document.getElementById('btn-fan-card-0')).transitionDuration));
    assert.ok(reducedDur <= 0.001);
    await page.emulateMedia({ reducedMotion: 'no-preference' });
    metrics.cases20['19_prefers_reduced_motion'] = 'PASS';
    metrics.audit10Risks['08_keyboard_escape_focus_and_reduced_motion'] = 'PASS';

    // Case 15 & Case 16 & Risk 6: Xong and Đóng (0-new, Discard-new, Keep-new) preserve pre-existing Composer attachments!
    await page.click('#btn-cam-done');
    await page.waitForSelector('.composer-card');
    const preIds5 = await page.evaluate(() => state.composerAttachments.map((p) => p.id));
    assert.equal(preIds5.length, 5);
    assert.equal(await page.evaluate(() => state.aiCallCount), 0);
    metrics.cases20['15_press_xong_attaches_to_composer'] = 'PASS';

    // Subcheck 6a: Re-open camera with 0 new shots -> Close immediately preserves all 5 existing attachments
    await page.click('#btn-composer-add-more');
    await page.waitForSelector('.camera-dialog');
    await page.click('#btn-cam-close');
    await page.waitForSelector('.composer-card');
    assert.deepEqual(await page.evaluate(() => state.composerAttachments.map((p) => p.id)), preIds5);

    // Subcheck 6b: Re-open camera, shoot 2 new photos -> Close -> Discard new -> preserves exact 5 existing attachments
    await page.click('#btn-composer-add-more');
    await page.waitForSelector('.camera-dialog');
    await page.click('#btn-cam-shutter');
    await page.click('#btn-cam-shutter');
    await page.waitForTimeout(200);
    await page.click('#btn-cam-close');
    await page.waitForSelector('#cam-close-confirm');
    await saveCuratedShot(page, '08-desktop-close-inline-confirm.png');
    await page.click('#btn-confirm-discard');
    await page.waitForSelector('.composer-card');
    assert.deepEqual(await page.evaluate(() => state.composerAttachments.map((p) => p.id)), preIds5);

    // Subcheck 6c: Re-open camera, shoot 1 new photo -> Close -> Keep -> preserves 5 existing + appends 1 new = 6
    await page.click('#btn-composer-add-more');
    await page.waitForSelector('.camera-dialog');
    await page.click('#btn-cam-shutter');
    await page.waitForTimeout(180);
    await page.click('#btn-cam-close');
    await page.waitForSelector('#cam-close-confirm');
    await page.click('#btn-confirm-keep');
    await page.waitForSelector('.composer-card');
    const afterKeepIds = await page.evaluate(() => state.composerAttachments.map((p) => p.id));
    assert.equal(afterKeepIds.length, 6);
    assert.deepEqual(afterKeepIds.slice(0, 5), preIds5);
    metrics.cases20['16_close_with_photos_preserves_composer'] = 'PASS';
    metrics.audit10Risks['06_close_and_done_preserve_existing_attachments'] = 'PASS';

    // All 5 Camera Error states
    for (const errCode of ['permission_denied', 'not_found', 'temporarily_unavailable', 'unsupported', 'unknown']) {
      await page.goto(`${baseHttpUrl}?surface=desktop&error=${errCode}&clean=1`);
      await page.waitForSelector('.camera-dialog.error-only');
      await assertCleanCameraCopy(page, `Desktop Error ${errCode}`, false);
    }

    metrics.viewports6['1440x900'] = {
      status: 'PASS',
      overflowX: 0,
      overflowY: 0,
      dialogSize: `${fannedSnapshot.dialog.width}x${fannedSnapshot.dialog.height}`,
      fanCollapsedSpanPx: collapsedSnapshot.spanPx,
      fanOpenSpanPx: fannedSnapshot.spanPx
    };
    await ctx.close();
  }

  // ===========================================================================
  // 2. MOBILE 390x844 — Risk 4 (Mobile >5 tray) + Risk 5 (1-tap tray) + Case 17
  // ===========================================================================
  {
    const ctx = await browser.newContext({
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 2,
      isMobile: true,
      hasTouch: true
    });
    const page = await ctx.newPage();
    attachGuards(page);

    for (const ratio of ['4:3', '16:9', '3:4']) {
      await page.goto(`${baseHttpUrl}?surface=mobile&shots=0&ratio=${encodeURIComponent(ratio)}&clean=1`);
      await page.waitForSelector('#camera-sensor-box');
      const containFrac = await page.evaluate(() => measureVisibleSourceFraction());
      assert.equal(containFrac, 1);
      await page.tap('#btn-toggle-fit');
      const coverFrac = await page.evaluate(() => measureVisibleSourceFraction());
      assert.ok(coverFrac < 1);
      metrics.previewVisibilityComparison[ratio] = {
        toanKhungVisiblePct: 100,
        tranManVisiblePct: Math.round(coverFrac * 1000) / 10
      };
    }

    await page.goto(`${baseHttpUrl}?surface=mobile&shots=0&ratio=4:3&clean=1`);
    await page.waitForSelector('.camera-fullscreen');
    await auditMobileTouchTargets(page, 'Mobile 0 photos');

    await page.tap('#btn-cam-shutter');
    await page.tap('#btn-cam-shutter');
    await page.tap('#btn-cam-shutter');
    await page.waitForTimeout(220);
    await assertCleanCameraCopy(page, 'Mobile 3 photos');
    await auditMobileTouchTargets(page, 'Mobile 3 photos');

    const mob3Layout = await page.evaluate(() => {
      const r = (s) => {
        const b = document.querySelector(s).getBoundingClientRect();
        return { left: b.left, top: b.top, right: b.right, bottom: b.bottom, width: b.width, height: b.height };
      };
      return {
        scrollW: document.documentElement.scrollWidth,
        scrollH: document.documentElement.scrollHeight,
        stack: r('#btn-session-stack'),
        shutter: r('#btn-cam-shutter'),
        done: r('#btn-cam-done'),
        stackCards: document.querySelectorAll('#btn-session-stack .mobile-stack-card').length,
        doneText: document.getElementById('btn-cam-done').innerText.trim()
      };
    });
    assert.equal(mob3Layout.scrollW, 390);
    assert.equal(mob3Layout.scrollH, 844);
    assert.equal(mob3Layout.stackCards, 3);
    assert.equal(mob3Layout.doneText, 'Xong');
    assert.ok(mob3Layout.stack.width >= 48 && mob3Layout.stack.height >= 48);
    const mobShutterCenter = (mob3Layout.shutter.left + mob3Layout.shutter.right) / 2;
    assert.ok(Math.abs(mobShutterCenter - 195) <= 1.5);
    await saveCuratedShot(page, '03-mobile-390x844-camera-3photos-stack.png');

    // Risk 5 & Case 17: 1 single tap opens Mobile Tray immediately
    await page.tap('#btn-session-stack');
    await page.waitForSelector('#cam-session-drawer');
    await auditMobileTouchTargets(page, 'Mobile Session Tray');
    await page.tap('#btn-tray-thumb-1');
    assert.equal((await page.locator('.cam-drawer-title').innerText()).trim(), 'Ảnh thứ 2 trong 3 ảnh');
    await saveCuratedShot(page, '04-mobile-390x844-photo-tray-open.png');

    // Also verify >5 photos (7 photos) on Mobile Tray accesses all 7 photos
    await page.goto(`${baseHttpUrl}?surface=mobile&shots=7&ratio=4:3&clean=1`);
    await page.waitForSelector('#btn-session-stack');
    await page.tap('#btn-session-stack');
    await page.waitForSelector('#cam-session-drawer');
    assert.equal(await page.locator('.tray-thumb-btn').count(), 7);
    await page.tap('#btn-tray-thumb-0');
    assert.equal((await page.locator('.cam-drawer-title').innerText()).trim(), 'Ảnh thứ 1 trong 7 ảnh');

    metrics.cases20['17_mobile_single_tap_opens_tray_viewer'] = 'PASS';
    metrics.audit10Risks['05_mobile_single_tap_opens_photo_tray'] = 'PASS';
    metrics.viewports6['390x844'] = {
      status: 'PASS',
      overflowX: 0,
      overflowY: 0,
      shutterCenterPx: mobShutterCenter,
      stackButtonSize: `${Math.round(mob3Layout.stack.width)}x${Math.round(mob3Layout.stack.height)}`
    };
    await ctx.close();
  }

  // ===========================================================================
  // 3. SHORT MOBILE VIEWPORTS 390x560 & 390x500 (Risk 10)
  // ===========================================================================
  for (const vh of [560, 500]) {
    const ctx = await browser.newContext({
      viewport: { width: 390, height: vh },
      deviceScaleFactor: 2,
      isMobile: true,
      hasTouch: true
    });
    const page = await ctx.newPage();
    attachGuards(page);

    await page.goto(`${baseHttpUrl}?surface=mobile&shots=3&ratio=4:3&clean=1`);
    await page.waitForSelector('.camera-fullscreen');
    await assertCleanCameraCopy(page, `Short Mobile 390x${vh}`);
    await auditMobileTouchTargets(page, `Short Mobile 390x${vh}`);

    const shortAudit = await page.evaluate(() => {
      const r = (s) => {
        const b = document.querySelector(s).getBoundingClientRect();
        return { left: b.left, top: b.top, right: b.right, bottom: b.bottom, width: b.width, height: b.height };
      };
      return {
        scrollW: document.documentElement.scrollWidth,
        scrollH: document.documentElement.scrollHeight,
        close: r('#btn-cam-close'),
        sensor: r('#camera-sensor-box'),
        stack: r('#btn-session-stack'),
        shutter: r('#btn-cam-shutter'),
        done: r('#btn-cam-done'),
        visibleFraction: measureVisibleSourceFraction()
      };
    });

    assert.equal(shortAudit.scrollW, 390);
    assert.equal(shortAudit.scrollH, vh);
    assert.equal(shortAudit.visibleFraction, 1);
    assertInsideViewport(shortAudit.close, 390, vh, `390x${vh} close`);
    assertInsideViewport(shortAudit.sensor, 390, vh, `390x${vh} sensor`);
    assertInsideViewport(shortAudit.stack, 390, vh, `390x${vh} stack`);
    assertInsideViewport(shortAudit.shutter, 390, vh, `390x${vh} shutter`);
    assertInsideViewport(shortAudit.done, 390, vh, `390x${vh} done`);
    assert.equal(rectsOverlap(shortAudit.stack, shortAudit.shutter), false);
    assert.equal(rectsOverlap(shortAudit.shutter, shortAudit.done), false);

    if (vh === 500) {
      await saveCuratedShot(page, '07-mobile-short-390x500-stack.png');
    }
    metrics.viewports6[`390x${vh}`] = {
      status: 'PASS',
      overflowX: 0,
      overflowY: 0,
      sensorBoxPx: `${Math.round(shortAudit.sensor.width)}x${Math.round(shortAudit.sensor.height)}`,
      shutterCenterPx: Math.round((shortAudit.shutter.left + shortAudit.shutter.right) / 2)
    };
    await ctx.close();
  }
  metrics.audit10Risks['10_short_screens_zero_overflow_touch_targets_ok'] = 'PASS';

  // ===========================================================================
  // 4. TOUCH TABLET 768x1024
  // ===========================================================================
  {
    const ctx = await browser.newContext({
      viewport: { width: 768, height: 1024 },
      deviceScaleFactor: 2,
      isMobile: true,
      hasTouch: true
    });
    const page = await ctx.newPage();
    attachGuards(page);

    await page.goto(`${baseHttpUrl}?surface=tablet&shots=3&ratio=4:3&clean=1`);
    await page.waitForSelector('.camera-fullscreen');
    await assertCleanCameraCopy(page, 'Tablet 768x1024');
    await auditMobileTouchTargets(page, 'Tablet 768x1024');

    const tabAudit = await page.evaluate(() => {
      const sh = document.getElementById('btn-cam-shutter').getBoundingClientRect();
      const st = document.getElementById('btn-session-stack').getBoundingClientRect();
      const sb = document.getElementById('camera-sensor-box').getBoundingClientRect();
      return {
        scrollW: document.documentElement.scrollWidth,
        scrollH: document.documentElement.scrollHeight,
        sensorBoxPx: `${Math.round(sb.width)}x${Math.round(sb.height)}`,
        shutterCenterPx: (sh.left + sh.right) / 2,
        stackOverlapsShutter: !(st.right <= sh.left),
        visibleFraction: measureVisibleSourceFraction()
      };
    });
    assert.equal(tabAudit.scrollW, 768);
    assert.equal(tabAudit.scrollH, 1024);
    assert.equal(tabAudit.visibleFraction, 1);
    assert.equal(tabAudit.stackOverlapsShutter, false);
    assert.ok(Math.abs(tabAudit.shutterCenterPx - 384) <= 1.5);
    metrics.viewports6['768x1024'] = { status: 'PASS', overflowX: 0, overflowY: 0, ...tabAudit };
    await ctx.close();
  }
} finally {
  await browser.close();
}

// =============================================================================
// 5. REAL DESKTOP CHROME ZOOM 110% (Risk 9 & Case 20)
// =============================================================================
{
  const profileDir = mkdtempSync(join(tmpdir(), 'axo-cam-fan-z110-'));
  mkdirSync(join(profileDir, 'Default'), { recursive: true });
  const zoomLevel110 = Math.log(1.1) / Math.log(1.2);
  writeFileSync(
    join(profileDir, 'Default', 'Preferences'),
    JSON.stringify({
      partition: {
        default_zoom_level: { x: zoomLevel110 },
        per_host_zoom_levels: { x: { '': zoomLevel110 } }
      }
    })
  );

  const zctx = await chromium.launchPersistentContext(profileDir, {
    channel: 'chrome',
    headless: true,
    viewport: null,
    args: ['--window-size=1440,940']
  });

  try {
    const zp = zctx.pages()[0] ?? await zctx.newPage();
    attachGuards(zp);
    await zp.goto(`${baseHttpUrl}?surface=desktop&shots=5&ratio=4:3&clean=1`);
    await zp.waitForSelector('#photo-fan-stack');
    await assertCleanCameraCopy(zp, 'Desktop Real Chrome Zoom 110%');

    await zp.hover('#photo-fan-stack');
    await zp.waitForTimeout(250);
    await assertCriticalDesktopControlsUnoccluded(zp, 'Chrome Zoom 110% fan open');

    const zMetrics = await zp.evaluate(() => {
      const dlg = document.querySelector('.camera-dialog').getBoundingClientRect();
      const sh = document.getElementById('btn-cam-shutter').getBoundingClientRect();
      const dn = document.getElementById('btn-cam-done').getBoundingClientRect();
      const cl = document.getElementById('btn-cam-close').getBoundingClientRect();
      const cards = Array.from(document.querySelectorAll('#photo-fan-stack .fan-card-btn')).map((c) => {
        const b = c.getBoundingClientRect();
        return { left: b.left, top: b.top, right: b.right, bottom: b.bottom };
      });
      return {
        dpr: Math.round(window.devicePixelRatio * 100) / 100,
        innerWidth: window.innerWidth,
        innerHeight: window.innerHeight,
        scrollWidth: document.documentElement.scrollWidth,
        scrollHeight: document.documentElement.scrollHeight,
        isFanOpen: document.getElementById('photo-fan-stack').classList.contains('is-fan-open'),
        dialogTop: Math.round(dlg.top),
        dialogBottom: Math.round(dlg.bottom),
        dialogWidth: Math.round(dlg.width),
        dialogHeight: Math.round(dlg.height),
        shutter: sh,
        doneBtn: dn,
        closeBtn: cl,
        cards
      };
    });

    assert.ok(Math.abs(zMetrics.dpr - 1.1) < 0.02);
    assert.equal(zMetrics.isFanOpen, true);
    assert.ok(zMetrics.scrollWidth <= zMetrics.innerWidth + 1);
    assert.ok(zMetrics.scrollHeight <= zMetrics.innerHeight + 1);
    assert.ok(zMetrics.dialogTop >= 0 && zMetrics.dialogBottom <= zMetrics.innerHeight);
    for (let i = 0; i < zMetrics.cards.length; i += 1) {
      assertInsideViewport(zMetrics.cards[i], zMetrics.innerWidth, zMetrics.innerHeight, `Zoom 110% card #${i}`);
      assert.equal(rectsOverlap(zMetrics.cards[i], zMetrics.shutter), false);
      assert.equal(rectsOverlap(zMetrics.cards[i], zMetrics.doneBtn), false);
      assert.equal(rectsOverlap(zMetrics.cards[i], zMetrics.closeBtn), false);
    }

    const cdp = await zctx.newCDPSession(zp);
    const { data: pngZ110 } = await cdp.send('Page.captureScreenshot', { format: 'png' });
    const z110File = '06-desktop-real-chrome-zoom-110-fan-open.png';
    writeFileSync(join(screenshotsDir, z110File), Buffer.from(pngZ110, 'base64'));
    if (!metrics.curatedScreenshots.includes(z110File)) {
      metrics.curatedScreenshots.push(z110File);
    }

    metrics.viewports6['desktop_chrome_zoom_110%'] = {
      status: 'PASS',
      dpr: zMetrics.dpr,
      innerViewport: `${zMetrics.innerWidth}x${zMetrics.innerHeight}`,
      dialogSize: `${zMetrics.dialogWidth}x${zMetrics.dialogHeight}`,
      overflowX: 0,
      overflowY: 0
    };
    metrics.audit10Risks['09_chrome_zoom_110_dialog_stable'] = 'PASS';
    metrics.cases20['20_zero_overflow_and_zero_shutter_occlusion_all_6_viewports'] = 'PASS';
  } finally {
    await zctx.close();
    rmSync(profileDir, { recursive: true, force: true });
    server.close();
  }
}

metrics.externalNetworkRequests = externalRequestCount;
metrics.consoleAndPageErrors = runtimeErrorCount;
writeFileSync(resultsFile, JSON.stringify(metrics, null, 2) + '\n');

if (tempOutDir) {
  rmSync(tempOutDir, { recursive: true, force: true });
}

console.log('CAMERA_PHOTO_FAN_STACK_ALL_10_RISKS_20_CASES_6_VIEWPORTS_PASSED');
console.log(JSON.stringify(metrics, null, 2));
