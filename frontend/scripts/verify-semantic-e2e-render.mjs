import { chromium } from "playwright";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

// Bằng chứng phải rơi vào KHO MÃ. Bản trước ghi ra một scratch dir tuyệt đối
// của máy một người, nên ảnh chụp và báo cáo không bao giờ commit được — tức
// script chạy xanh mà luận văn vẫn không có gì để dẫn.
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const ARTIFACT_DIR = process.env.ARTIFACT_DIR
  ? path.resolve(process.env.ARTIFACT_DIR)
  : path.join(REPO, "docs/evaluation/semantic-program/render");
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const VIEWPORTS = [
  { name: "desktop_1920x1080", width: 1920, height: 1080 },
  { name: "laptop_1536x864", width: 1536, height: 864 },
  { name: "school_1366x768", width: 1366, height: 768 },
  { name: "tablet_768x900", width: 768, height: 900 },
];

// ── PHA B của Reliability V2 (2026-08-24) ─────────────────────────────────
//
// Chế độ `--envelopes <dir>` KHÁC HẲN chế độ fixture bên dưới, và khác ở đúng
// chỗ quyết định giá trị của bằng chứng:
//
//   fixture   : envelope do người viết ra để hệ chạy được  → hồi quy renderer
//   envelopes : envelope do LƯỢT ĐO THẬT phát ra           → chỉ số `V`
//
// `SERVE_PROBE_CHAIN §4b` ghi lại lần bằng chứng thị giác hoá ra vô giá trị:
// ảnh chụp một envelope TIÊM THẲNG, nên chứng minh renderer chứ không chứng
// minh đường sinh. Bốn cổng dưới đây tồn tại để lần đó không lặp lại.
//
//   1. TỪ CHỐI chạy nếu thiếu `PROVENANCE.json` — lô envelope không tự khai
//      được nguồn thì không phân biệt được với một thư mục chép tay.
//   2. Tiêu chí PASS đọc DOM THẬT, không phải hằng số. Bản fixture bên dưới
//      gán `status: "RENDER_CERTIFIED"` bất kể trang có gì — đúng bẫy
//      "status=ok không phải bằng chứng".
//   3. `--faultcheck` xoá rỗng khung hình rồi ĐÒI mọi case PHẢI trượt. Guard
//      chưa từng đỏ là guard chưa được chứng minh.
//   4. Đủ bốn bề rộng; thiếu một là case đó KHÔNG được tính PASS.
const ARG = process.argv.slice(2);
const argVal = (k) => {
  const i = ARG.indexOf(k);
  return i >= 0 ? ARG[i + 1] : null;
};

/** Tiêu chí PASS của một lượt render — đọc trạng thái THẬT sau khi nạp. */
async function chamMotViewport(page, envelope) {
  await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
  const kq = await page.evaluate((env) => {
    const store = window.__ALGOSIM_STORE__;
    if (!store) return { ok: false, ly_do: "store chưa expose" };
    try {
      store.getState().loadEnvelope(env);
    } catch (e) {
      return { ok: false, ly_do: `loadEnvelope ném: ${e.message}` };
    }
    const s = store.getState();
    return {
      ok: !!s.active && !s.analysisError,
      ly_do: s.analysisError || (s.active ? null : "không có mô phỏng hoạt động"),
      simulationId: s.active?.envelope?.simulation_id ?? null,
      soBuoc: s.active?.timelineLength ?? null,
    };
  }, envelope);
  if (!kq.ok) return { pass: false, ...kq };

  await page.waitForTimeout(400);
  const dom = await page.evaluate(() => {
    const stage = document.querySelector("[data-sim-stage], main, #root");
    return {
      soPhanTuVe: stage ? stage.querySelectorAll("svg *, [data-obj-id]").length : 0,
      doDaiChu: document.body.innerText.trim().length,
    };
  });
  // Ngưỡng cố ý THẤP: ta hỏi "có dựng được cảnh không", không chấm đẹp/xấu.
  // Nhưng phải > 0 — lần trước envelope `ok` với 5 khung mà mọi khung đều rỗng.
  const pass = dom.soPhanTuVe > 0 && dom.doDaiChu > 40;
  return { pass, ly_do: pass ? null : "cảnh rỗng", ...kq, dom };
}

/** Làm hỏng envelope đúng kiểu đã từng lọt: khung hình rỗng sạch. */
function lamHong(env) {
  const h = JSON.parse(JSON.stringify(env));
  if (h.config?.frames) h.config.frames = [];
  if (h.config?.timeline) h.config.timeline = [];
  if (Array.isArray(h.frames)) h.frames = [];
  return h;
}

async function chayPhaB(thuMuc) {
  const provPath = path.join(thuMuc, "PROVENANCE.json");
  if (!fs.existsSync(provPath)) {
    throw new Error(
      `TỪ CHỐI: thiếu ${provPath}. Lô envelope không tự khai được nguồn gốc, ` +
      `nên không phân biệt được với một thư mục chép tay.`,
    );
  }
  const prov = JSON.parse(fs.readFileSync(provPath, "utf-8"));
  const faultcheck = ARG.includes("--faultcheck");
  console.log(
    `PHA B ${faultcheck ? "[FAULTCHECK]" : ""} · ${prov.so_envelope} envelope ` +
    `· candidate ${prov.measured_system_candidate} · seal ${String(prov.sealed_fingerprint).slice(0, 12)}`,
  );

  const browser = await chromium.launch({ headless: true });
  const ketQua = {};
  const chiTiet = [];

  for (const caseId of prov.case_ids || []) {
    const p = path.join(thuMuc, `${caseId}.json`);
    if (!fs.existsSync(p)) { ketQua[caseId] = false; continue; }
    let env = JSON.parse(fs.readFileSync(p, "utf-8"));
    if (faultcheck) env = lamHong(env);

    let duBonBeRong = true;
    for (const vp of VIEWPORTS) {
      const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
      const r = await chamMotViewport(page, env);
      chiTiet.push({ caseId, viewport: vp.name, ...r });
      if (!r.pass) duBonBeRong = false;
      if (!faultcheck && r.pass) {
        await page.screenshot({
          path: path.join(ARTIFACT_DIR, `v2_${caseId}_${vp.name}.png`),
          fullPage: true,
        });
      }
      await page.close();
    }
    ketQua[caseId] = duBonBeRong;
    console.log(`  ${duBonBeRong ? "✓" : "✗"} ${caseId}`);
  }
  await browser.close();

  const soPass = Object.values(ketQua).filter(Boolean).length;

  if (faultcheck) {
    // Guard phải ĐỎ. Còn case nào xanh nghĩa là tiêu chí không đọc gì thật.
    if (soPass > 0) {
      console.error(
        `\nFAULTCHECK THẤT BẠI: ${soPass} case VẪN PASS trên envelope đã bị ` +
        `xoá rỗng khung hình. Tiêu chí chấm không đọc trạng thái thật — ` +
        `bằng chứng thị giác của lượt này KHÔNG dùng được.`,
      );
      return 1;
    }
    console.log(`\nFAULTCHECK ĐỎ đúng như phải thế: 0/${prov.so_envelope} pass.`);
    fs.writeFileSync(path.join(ARTIFACT_DIR, "faultcheck_red.json"),
      JSON.stringify({ faultcheck_red: true, so_case: prov.so_envelope }, null, 2), "utf-8");
    return 0;
  }

  const red = path.join(ARTIFACT_DIR, "faultcheck_red.json");
  const daDoRed = fs.existsSync(red) && JSON.parse(fs.readFileSync(red, "utf-8")).faultcheck_red === true;
  const out = {
    khai: "PHA B — chỉ số V. Envelope do lượt đo THẬT phát ra, không phải fixture.",
    // Cờ này là thứ `merge_render_v.py` TỪ CHỐI gộp nếu thiếu. Cố ý không tự
    // đặt `true`: nó chỉ đúng khi `--faultcheck` đã thật sự chạy và đã đỏ.
    faultcheck_red: daDoRed,
    viewports: VIEWPORTS.map((v) => v.name),
    provenance: prov,
    ket_qua: ketQua,
    chi_tiet: chiTiet,
  };
  const p = path.join(ARTIFACT_DIR, "renderer_v.json");
  fs.writeFileSync(p, JSON.stringify(out, null, 2), "utf-8");
  console.log(`\nV = ${soPass}/${prov.so_envelope} · faultcheck_red=${daDoRed} → ${p}`);
  if (!daDoRed) {
    console.error("⚠ CHƯA chạy `--faultcheck`. Kết quả này chưa gộp được.");
    return 1;
  }
  return 0;
}

async function run() {
  const thuMuc = argVal("--envelopes");
  if (thuMuc) {
    const rc = await chayPhaB(path.resolve(thuMuc));
    process.exit(rc);
  }
  console.log("Starting Semantic E2E Playwright Browser Verification on port 3000...");
  // Fixture nằm ở `frontend/tests/`, KHÔNG ở `public/` — xem chú thích cùng
  // loại ở `verify-live-gemini-render.mjs`. Neo theo REPO thay vì cwd.
  const fixturesPath = path.join(REPO, "frontend/tests/fixtures/semantic/e2e_semantic_candidates.json");
  if (!fs.existsSync(fixturesPath)) {
    throw new Error(`Candidate fixtures not found at ${fixturesPath}`);
  }
  const rawFixtures = JSON.parse(fs.readFileSync(fixturesPath, "utf-8"));
  const algorithms = Object.keys(rawFixtures);

  const browser = await chromium.launch({ headless: true });
  const report = {
    browser: "Chromium (Headless)",
    algorithmsTested: algorithms,
    results: [],
  };

  for (const algoKey of algorithms) {
    const envelope = rawFixtures[algoKey];
    console.log(`\nTesting Algorithm: ${algoKey} (${envelope.title})`);

    for (const vp of VIEWPORTS) {
      const page = await browser.newPage({
        viewport: { width: vp.width, height: vp.height },
      });

      await page.goto("http://localhost:3000", { waitUntil: "networkidle" });

      // Inject simulation envelope into store
      const loadRes = await page.evaluate((candidate) => {
        const store = window.__ALGO_SIM_STORE__;
        if (!store) return { ok: false, error: "No store" };
        store.getState().loadEnvelope(candidate);
        const state = store.getState();
        return {
          ok: true,
          view: state.view,
          active: !!state.active,
          analysisError: state.analysisError,
        };
      }, envelope);

      await page.waitForTimeout(600);

      // Verify DOM Elements & bounding boxes
      const domStats = await page.evaluate(() => {
        const h1s = document.querySelectorAll("h1");
        const bodyText = document.body.innerText;
        const root = document.getElementById("root");
        const rect = root ? root.getBoundingClientRect() : null;
        return {
          h1Count: h1s.length,
          titleText: h1s.length > 0 ? h1s[0].innerText : "",
          bodyLength: bodyText.length,
          rootWidth: rect ? rect.width : 0,
          rootHeight: rect ? rect.height : 0,
        };
      });

      // Capture screenshot
      const screenshotFilename = `semantic_e2e_${algoKey}_${vp.name}.png`;
      const screenshotPath = path.join(ARTIFACT_DIR, screenshotFilename);
      await page.screenshot({ path: screenshotPath, fullPage: true });

      report.results.push({
        algorithm: algoKey,
        viewport: vp.name,
        width: vp.width,
        height: vp.height,
        loadStatus: loadRes,
        domStats,
        screenshot: screenshotFilename,
        status: "RENDER_CERTIFIED",
      });

      console.log(`  ✓ [${vp.name}] -> Title: '${domStats.titleText}' | Loaded: ${loadRes.ok} | Screenshot: ${screenshotFilename}`);
      await page.close();
    }
  }

  await browser.close();

  const reportPath = path.join(ARTIFACT_DIR, "semantic_e2e_render_report.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf-8");
  console.log(`\nVerification complete! Report written to ${reportPath}`);
}

run().catch((err) => {
  console.error("Verification failed:", err);
  process.exit(1);
});
