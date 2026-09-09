/**
 * capture-release-demo.mjs — BỘ ẢNH DEMO CUỐI, có xuất xứ đầy đủ.
 *
 * ─── VÌ SAO MỖI ẢNH PHẢI MANG SIÊU DỮ LIỆU ────────────────────────────────
 *
 * Một thư mục ảnh PNG không tự nói nó chụp bản nào. Đem vào khoá luận thì mỗi
 * ảnh là một khẳng định — *"hệ dựng ra hình này cho đề kia"* — và một khẳng
 * định không truy được về mã nguồn thì không kiểm lại được.
 *
 * Nên mỗi ảnh đi kèm: `case_id` · băm ĐỀ BÀI · băm PHẢN HỒI · tư thế camera ·
 * `candidate_hash` · thời điểm. Ảnh PNG **không** cần trùng byte giữa các máy
 * (`§9`) — oracle ngữ nghĩa/raster đã đăng ký mới là thứ phán quyết.
 *
 * Chín ca đóng băng + ảnh SAU XOAY cho ba ca có thiết diện trên mặt cong (nơi
 * nét khuất đổi theo camera). 0 lượt gọi model: envelope trả tại `/api/analyze`.
 */
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { BrowserSession, sleep } from "./browser-runner.mjs";

const FE = fileURLToPath(new URL("..", import.meta.url));
const GOC = resolve(FE, "..");
const FIXTURES = join(GOC, "docs/evaluation/geometry/product-ui-result-rendering/fixtures");
const OUT = join(GOC, "docs/evaluation/geometry/final-system-release");
const ANH = join(OUT, "demo-screenshots");
mkdirSync(ANH, { recursive: true });

const VIEWPORT = { viewport: 1440, height: 900 };
/** Ca có thiết diện nằm TRÊN mặt cong ⇒ nét khuất đổi khi xoay. */
const CAN_XOAY = new Set(["p3_mat_cau_va_thiet_dien_tron",
                          "p6_thiet_dien_elip_cua_hinh_tru",
                          "p7_thiet_dien_elip_cua_hinh_non"]);

const bam = (x) => createHash("sha256").update(x).digest("hex");

const ca = readdirSync(FIXTURES).filter((f) => f.endsWith(".json")).sort()
  .map((f) => JSON.parse(readFileSync(join(FIXTURES, f), "utf-8")));

const manifest = [];

async function tuThe(s) {
  return JSON.parse(await s.eval(`(()=>{
    const c=window.__scene3dCamera;
    if(!c) return JSON.stringify(null);
    return JSON.stringify({pos:[c.position.x,c.position.y,c.position.z].map(v=>+v.toFixed(4))});
  })()`)) ?? null;
}

async function main() {
  const candidate = JSON.parse(readFileSync(
    join(OUT, "RELEASE_MANIFEST.json"), "utf-8")).candidate_hash;

  const s = new BrowserSession({ ...VIEWPORT, webgl: true });
  await s.open();
  let phucVu = null;
  await s.interceptJson("*/api/analyze*", () =>
    phucVu ? { status: 200, body: phucVu.envelope } : null);

  for (const f of ca) {
    phucVu = f;
    await s.resetBetweenScenarios();
    await sleep(200);
    await s.eval(`(async()=>{const st=await import(${JSON.stringify(s.mods.store)});
      st.useAppStore.getState().setProblemText(${JSON.stringify(f.problem_text)});
      return 'ok';})()`);
    await sleep(120);
    await s.eval(`(()=>{const b=document.querySelector(
      'button[aria-label="Phân tích đề bằng AI"]'); if(b&&!b.disabled) b.click();})()`);

    // Chờ THEO TRẠNG THÁI: cảnh dựng xong, hoặc thẻ từ chối hiện ra.
    let den = "";
    for (let i = 0; i < 100 && !den; i++) {
      den = await s.eval(`(()=>{
        if(document.querySelector('.geo3d-canvas canvas')) return 'canh';
        if(document.querySelector('.refusal-facts')) return 'the';
        return '';})()`);
      if (!den) await sleep(120);
    }
    const duong = f.positive_or_negative === "positive";
    if (duong && den !== "canh") throw new Error(`${f.case_id}: không dựng được cảnh`);
    if (!duong && den !== "the") throw new Error(`${f.case_id}: không hiện thẻ từ chối`);

    // Ca dương: tua tới bước CUỐI để ảnh mang đáp số.
    if (duong) {
      for (let k = 1; k < f.expected_trace_event_count; k++) {
        await s.clickText("Bước sau");
        await sleep(80);
      }
    }
    await sleep(500);
    const ten = `${f.case_id}.png`;
    await s.screenshot(join(ANH, ten));
    manifest.push({
      file: ten, case_id: f.case_id,
      loai: f.positive_or_negative,
      problem_sha256: bam(f.problem_text),
      response_sha256: bam(JSON.stringify(f.envelope)),
      camera_pose: await tuThe(s),
      candidate_hash: candidate,
      created_at: new Date().toISOString(),
      dap_so: f.expected_exact_display,
    });
    console.log(`  ✓ ${ten}`);

    // Ảnh SAU XOAY — bằng chứng nét khuất đổi theo camera.
    if (duong && CAN_XOAY.has(f.case_id)) {
      await s.eval(`(()=>{const c=document.querySelector('.geo3d-canvas canvas');
        if(!c) return; const r=c.getBoundingClientRect();
        const x=r.left+r.width/2, y=r.top+r.height/2;
        c.dispatchEvent(new PointerEvent('pointerdown',{clientX:x,clientY:y,bubbles:true,pointerId:1}));
        for(let i=1;i<=12;i++) window.dispatchEvent(new PointerEvent('pointermove',
          {clientX:x+i*18,clientY:y,bubbles:true,pointerId:1}));
        window.dispatchEvent(new PointerEvent('pointerup',{clientX:x+216,clientY:y,bubbles:true,pointerId:1}));
      })()`);
      await sleep(600);
      const tenX = `${f.case_id}--sau-xoay.png`;
      await s.screenshot(join(ANH, tenX));
      manifest.push({
        file: tenX, case_id: f.case_id, loai: "positive-rotated",
        problem_sha256: bam(f.problem_text),
        response_sha256: bam(JSON.stringify(f.envelope)),
        camera_pose: await tuThe(s),
        candidate_hash: candidate,
        created_at: new Date().toISOString(),
        ghi_chu: "Sau khi kéo xoay 216 px — nét thấy/khuất phải phân loại lại.",
      });
      console.log(`  ✓ ${tenX}`);
    }
  }

  writeFileSync(join(OUT, "DEMO_SCREENSHOTS.json"), JSON.stringify({
    khai: "Bộ ảnh demo cuối. PNG KHÔNG cần trùng byte giữa các máy; oracle "
      + "ngữ nghĩa/raster đã đăng ký mới là thứ phán quyết (§9).",
    viewport: `${VIEWPORT.viewport}×${VIEWPORT.height}`,
    device_scale_factor: 1, webgl: "angle/swiftshader (phần mềm)",
    locale: "vi-VN",
    page_load_retries: s.pageLoadRetries,
    SCREENSHOTS: manifest.length,
    anh: manifest,
  }, null, 1), "utf8");

  console.log(`\n  ${manifest.length} ảnh · mở lại trình duyệt ${s.pageLoadRetries}`);
  console.log(`  ghi: ${join(OUT, "DEMO_SCREENSHOTS.json").replace(GOC, "")}`);
  await s.close?.();
  process.exit(0);
}

if (!existsSync(join(OUT, "RELEASE_MANIFEST.json"))) {
  console.error("chạy `build_release_manifest.py` trước — ảnh phải ghim candidate.");
  process.exit(2);
}
await main();
