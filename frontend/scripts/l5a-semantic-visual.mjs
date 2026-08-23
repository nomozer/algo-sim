/**
 * L5a — SOÁT THỊ GIÁC ĐẠI DIỆN cho route `generic.semantic_program`.
 *
 * ─── VÌ SAO CẦN TẦNG NÀY ──────────────────────────────────────────────────
 *
 * L3 (bất biến #31) chứng minh **semantic visual fidelity**: khung thứ k suy
 * đúng từ trạng thái bước k. Nó KHÔNG chứng minh **màn hình nhìn được** — chữ
 * vẫn có thể đè nhau, hình vẫn có thể tràn, con trỏ vẫn có thể chui vào nhãn.
 * Ràng buộc "hiển thị chuẩn xác" của giáo viên hướng dẫn đòi đúng tầng này.
 *
 * ─── VÌ SAO ĐO HÌNH HỌC, KHÔNG SO ẢNH PIXEL ───────────────────────────────
 *
 * Repo chỉ có thư viện `playwright`, không có `@playwright/test`, nên không có
 * `toHaveScreenshot()` và bộ ảnh nền. Nhưng đo `getBoundingClientRect()` còn
 * CHẶT HƠN so ảnh: nó phát biểu được *vì sao* hỏng ("nhãn A đè nhãn B 14px")
 * thay vì "12.000 pixel đổi màu", và nó không đỏ oan khi đổi một token màu.
 *
 * ─── HAI ĐIỀU KIỆN TRƯỚC KHI TIN MỘT BẢN SOÁT "SẠCH" (ARCHITECTURE_MAP §8 #14)
 *
 *   1. DẤU VÂN TAY TRANG — khẳng định đang đo ĐÚNG route và ĐÚNG bản dựng.
 *      `vite.config.ts` cấm nhảy cổng ngầm chính vì hai artifact từng bị gỡ do
 *      chụp nhầm một server cũ còn giữ cổng 3000.
 *   2. TIÊM LỖI GIẢ — chạy với `--faultcheck` để thấy guard ĐỎ được. Một guard
 *      chưa từng đỏ là một guard chưa được chứng minh.
 *
 * Dùng:
 *   node scripts/l5a-semantic-visual.mjs --port 3100 [--out-dir <thư mục>]
 *   node scripts/l5a-semantic-visual.mjs --port 3100 --faultcheck
 */
import { chromium } from "playwright";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const argOf = (name, fallback) => {
  const i = argv.indexOf(name);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : fallback;
};
const PORT = argOf("--port", "3100");
const OUT_DIR = argOf("--out-dir", path.resolve(HERE, "../../docs/evaluation/semantic-l5a"));
const FAULTCHECK = argv.includes("--faultcheck");

/** Bề rộng ĐẠI DIỆN — không phải toàn bộ ma trận (L5b mới là phủ rộng). */
const VIEWPORTS = [
  { name: "school_1366x768", width: 1366, height: 768 },
  { name: "desktop_1920x1080", width: 1920, height: 1080 },
];

const FIXTURES = JSON.parse(
  // `frontend/tests/`, không `public/`: fixture đọc bằng `fs` chứ không qua
  // HTTP, để trong `public/` chỉ khiến nó bị bundle vào `dist/` sản phẩm.
  fs.readFileSync(path.resolve(HERE, "../tests/fixtures/semantic/semantic_l5a.json"), "utf-8"),
);

/* ── Phép đo chạy TRONG trang ─────────────────────────────────────────────── */

/** Hai hình chữ nhật có chồng nhau không, và chồng bao nhiêu. */
const OVERLAP_FN = `
function overlap(a, b) {
  const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
  const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
  return w > 0 && h > 0 ? { w: Math.round(w), h: Math.round(h) } : null;
}`;

async function measure(page) {
  return page.evaluate(`(() => {
    ${OVERLAP_FN}
    const stage = document.querySelector("[data-route='semantic']");
    if (!stage) return { error: "KHÔNG tìm thấy sân khấu semantic" };

    const rectOf = (el) => {
      const r = el.getBoundingClientRect();
      return { left: r.left, top: r.top, right: r.right, bottom: r.bottom,
               w: Math.round(r.width), h: Math.round(r.height) };
    };
    const textNodes = [...stage.querySelectorAll(
      ".sem-label, .sem-cell, .sem-box, .sem-bar-val, .sem-narration, .sem-note, .sem-pointer-cap, .sem-stack-empty"
    )].filter((el) => (el.textContent || "").trim().length > 0);

    // 1. CHỮ ĐÈ CHỮ — bỏ qua cặp lồng nhau (cha/con thì chồng là đương nhiên).
    const collisions = [];
    for (let i = 0; i < textNodes.length; i++) {
      for (let j = i + 1; j < textNodes.length; j++) {
        const A = textNodes[i], B = textNodes[j];
        if (A.contains(B) || B.contains(A)) continue;
        const o = overlap(rectOf(A), rectOf(B));
        if (o && o.w > 2 && o.h > 2) {
          collisions.push({
            a: A.className + ":" + (A.textContent || "").trim().slice(0, 12),
            b: B.className + ":" + (B.textContent || "").trim().slice(0, 12),
            overlap: o,
          });
        }
      }
    }

    // 2. CLIPPING — phần tử tràn ra ngoài sân khấu.
    const sr = rectOf(stage);
    const clipped = [];
    for (const el of stage.querySelectorAll(".sem-strip, .sem-stack, .sem-bars, .sem-grid, .sem-box")) {
      const r = rectOf(el);
      if (r.right > sr.right + 1 || r.left < sr.left - 1) {
        clipped.push({ cls: el.className, right: Math.round(r.right), stageRight: Math.round(sr.right) });
      }
    }

    // 3. CON TRỎ chui vào nhãn/chữ khác — đúng lỗi trong ảnh chụp §0(b).
    const pointerHits = [];
    for (const p of stage.querySelectorAll(".sem-pointer-cap")) {
      for (const t of textNodes) {
        if (t === p || p.contains(t) || t.contains(p)) continue;
        const o = overlap(rectOf(p), rectOf(t));
        if (o && o.w > 2 && o.h > 2) {
          pointerHits.push({ text: (t.textContent || "").trim().slice(0, 16), overlap: o });
        }
      }
    }

    /* 4. CHỮ LẶP — hai khối văn bản DÀI giống hệt nhau trên cùng màn hình.
       Thêm 2026-08-21 sau khi ảnh L5a phơi ra một lỗi mà ba phép đo trên KHÔNG
       thấy: dòng thuyết minh hiện HAI LẦN (module tự vẽ, rồi shell vẽ lại qua
       narrate()). Chúng xếp DỌC nên không chồng nhau — phép đo chồng lấn mù
       hoàn toàn với loại lỗi này. Chỉ soi chuỗi dài để không báo oan hai ô mảng
       cùng giá trị. */
    const duplicates = [];
    const seen = new Map();
    for (const el of document.querySelectorAll("p, .sem-narration, .narration, [class*='narration']")) {
      const t = (el.textContent || "").trim();
      if (t.length < 20) continue;
      if (seen.has(t)) duplicates.push({ text: t.slice(0, 40), lan: 2 });
      else seen.set(t, el);
    }

    return {
      collisions, clipped, pointerHits, duplicates,
      pageOverflowX: document.documentElement.scrollWidth
                     > document.documentElement.clientWidth + 1,
      counts: {
        cells: stage.querySelectorAll(".sem-cell").length,
        bars: stage.querySelectorAll(".sem-bar").length,
        boxes: stage.querySelectorAll(".sem-box").length,
        pointers: stage.querySelectorAll(".sem-pointer").length,
      },
      /* Chữ HIỂN THỊ của bước hiện tại — dùng để chứng minh khung ĐỔI theo
         bước, tức lỗi "narration chạy mà hình đứng" không quay lại. */
      signature: [...stage.querySelectorAll(".sem-cell, .sem-box")]
        .map((el) => (el.textContent || "").trim()).join("|"),
      /* Thuyết minh nay do SHELL dựng (".narration-bar"), không nằm trong sân
         khấu — đọc đúng chủ sở hữu, nếu không phép đo "khung có đổi không" sẽ
         luôn thấy chuỗi rỗng và báo hỏng oan. */
      narration: (document.querySelector(".narration-bar")?.textContent || "").trim(),
    };
  })()`);
}

/* ── Chạy ─────────────────────────────────────────────────────────────────── */

async function run() {
  const base = `http://localhost:${PORT}`;
  const browser = await chromium.launch({ headless: true });
  const rows = [];
  let failures = 0;

  for (const [key, envelope] of Object.entries(FIXTURES)) {
    for (const vp of VIEWPORTS) {
      const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
      await page.goto(base, { waitUntil: "networkidle" });

      const loaded = await page.evaluate((env) => {
        const store = window.__ALGO_SIM_STORE__;
        if (!store) return { ok: false, error: "thiếu __ALGO_SIM_STORE__" };
        store.getState().loadEnvelope(env);
        const st = store.getState();
        return { ok: !!st.active, simId: st.active?.moduleId ?? null, err: st.analysisError ?? null };
      }, envelope);

      if (!loaded.ok) {
        rows.push({ case: key, viewport: vp.name, fatal: `nạp thất bại: ${loaded.error ?? "?"}` });
        failures += 1;
        await page.close();
        continue;
      }

      /* DẤU VÂN TAY TRANG — không có nó thì một bản soát "SẠCH" có thể là kết
         quả của việc đo nhầm route hoặc nhầm server. */
      await page.waitForSelector("[data-route='semantic']", { timeout: 5000 });
      if (loaded.simId !== "generic.semantic_program") {
        rows.push({ case: key, viewport: vp.name, fatal: `sai route: ${loaded.simId}` });
        failures += 1;
        await page.close();
        continue;
      }

      if (FAULTCHECK) {
        /* TIÊM LỖI GIẢ — phải TẤT ĐỊNH ở mọi ca.
           Bản đầu DỜI một nhãn có sẵn sang `position: fixed`, và điều đó làm
           trang REFLOW: ở `find_max`/`bar_chart` dòng thuyết minh trôi lên, nên
           chỗ định đè trống trơn và guard báo SẠCH — tức phép tiêm hỏng, không
           phải guard hỏng. Nay THÊM một nút mới (fixed nên không đụng dòng chảy)
           đặt đúng lên hình chữ nhật của một nút chữ đang có. */
        await page.evaluate(() => {
          const stage = document.querySelector("[data-route='semantic']");
          /* Mục tiêu phải CÓ CHỮ: `graph_bfs` có ô đầu RỖNG, và ô rỗng bị lọc
             khỏi tập nút chữ — đặt lên đó thì không sinh cặp nào và faultcheck
             báo SẠCH oan. */
          const nan = [...stage.querySelectorAll(".sem-narration, .sem-cell, .sem-box, .sem-label")]
            .find((el) => (el.textContent || "").trim().length > 0
                          && el.getBoundingClientRect().width > 4);
          if (!stage || !nan) return;
          const r = nan.getBoundingClientRect();
          const gia = document.createElement("span");
          gia.className = "sem-label";
          gia.textContent = "CHỮ ĐÈ";
          gia.style.cssText = `position:fixed;left:${r.left + 2}px;top:${r.top + 1}px;z-index:99`;
          stage.appendChild(gia);
        });
      }

      const first = await measure(page);

      // Tiến 6 bước rồi đo lại — khung PHẢI đổi (hồi quy cho lỗi E1).
      // 6 chứ không 3: BFS dành mấy bước đầu để khởi tạo hàng đợi/tập đã thăm.
      await page.evaluate(() => {
        const s = window.__ALGO_SIM_STORE__.getState();
        for (let i = 0; i < 6; i += 1) s.nextStep();
      });
      await page.waitForTimeout(120);
      const later = await measure(page);

      const loi = [];
      if (first.error) loi.push(first.error);
      if (first.collisions?.length) loi.push(`${first.collisions.length} cặp chữ đè nhau`);
      if (first.clipped?.length) loi.push(`${first.clipped.length} phần tử tràn khỏi sân khấu`);
      if (first.pointerHits?.length) loi.push(`con trỏ đè ${first.pointerHits.length} chỗ chữ`);
      if (first.pageOverflowX) loi.push("trang tràn ngang");
      if (first.duplicates?.length) {
        loi.push(`${first.duplicates.length} khối chữ hiện hai lần`);
      }
      if (first.signature === later.signature && first.narration === later.narration) {
        loi.push("khung KHÔNG đổi sau 6 bước — lỗi E1 quay lại");
      }
      if (key === "bar_chart" && (first.counts?.bars ?? 0) === 0) {
        loi.push("bar_chart không dựng cột nào");
      }

      if (loi.length) failures += 1;
      rows.push({
        case: key, viewport: vp.name,
        ok: loi.length === 0, loi,
        counts: first.counts,
        doiKhungSau6Buoc: first.signature !== later.signature,
        chiTiet: {
          collisions: first.collisions?.slice(0, 3) ?? [],
          clipped: first.clipped?.slice(0, 3) ?? [],
          pointerHits: first.pointerHits?.slice(0, 3) ?? [],
          duplicates: first.duplicates?.slice(0, 3) ?? [],
        },
      });

      if (!FAULTCHECK) {
        fs.mkdirSync(path.join(OUT_DIR, "shots"), { recursive: true });
        await page.screenshot({
          path: path.join(OUT_DIR, "shots", `${key}_${vp.name}.png`),
          fullPage: true,
        });
      }
      await page.close();
    }
  }

  await browser.close();

  const report = {
    when: new Date().toISOString(),
    port: PORT,
    mode: FAULTCHECK ? "faultcheck" : "soát",
    viewports: VIEWPORTS.map((v) => v.name),
    cases: Object.keys(FIXTURES),
    failures,
    rows,
  };

  if (!FAULTCHECK) {
    fs.mkdirSync(OUT_DIR, { recursive: true });
    fs.writeFileSync(
      path.join(OUT_DIR, "l5a-report.json"),
      JSON.stringify(report, null, 2) + "\n", "utf-8",
    );
  }

  for (const r of rows) {
    const nhan = r.fatal ? `FATAL ${r.fatal}` : r.ok ? "SẠCH" : r.loi.join(" · ");
    console.log(`${r.ok ? "  " : "✗ "}${r.case.padEnd(15)} ${r.viewport.padEnd(18)} ${nhan}`);
  }
  console.log(`\n${FAULTCHECK ? "FAULTCHECK" : "L5A"}: ${failures} hàng hỏng / ${rows.length}`);

  if (FAULTCHECK) {
    // Tiêm lỗi mà guard vẫn SẠCH ⇒ guard vô dụng ⇒ thoát != 0.
    process.exit(failures > 0 ? 0 : 1);
  }
  process.exit(failures > 0 ? 1 : 0);
}

run().catch((e) => {
  console.error(e);
  process.exit(2);
});
