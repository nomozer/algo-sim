/**
 * after-matrix-w4b3a.mjs — MA TRẬN AFTER cho TOÀN BỘ danh mục hiện tại.
 *
 * Sinh TỪ NGUỒN, không viết tay dòng nào:
 *   - sự thật BACKEND ← `src/simulations/capability-descriptors.json` (artifact
 *     sinh từ registry `catalog.py`/`descriptor.py`, có sync-lock);
 *   - sự thật FRONTEND ← chính app đang chạy (module đã đăng ký + capability);
 *   - sự thật BỐ CỤC ← `docs/evaluation/m17/w4b3a-after/measure-*.json`.
 *
 * ─── PHÂN LOẠI TRẢI NGHIỆM: LUẬT KHAI TRƯỚC, ĐẾM SAU ──────────────────────
 *
 * Câu hỏi nghiệm thu (không phải cảm nhận):
 *   "Nếu MỌI control đúng/sai/dự đoán biến mất, học sinh còn thao tác được lên
 *    mô hình và thấy hệ quả tất định không?"
 *
 *   CÓ  → THAO TÁC TRỰC TIẾP. Máy-đọc được: module khai `explore` và
 *         `explore.entry()` trả non-null — tức có đường đi qua `module.apply`
 *         mà KHÔNG ai chấm điểm.
 *   KHÔNG, nhưng học sinh chọn nước đi ĐÚNG của thuật toán
 *       → CAM KẾT (`predict.presentedInStage` bật ở ít nhất một bước).
 *   KHÔNG, chỉ điều khiển được dòng thời gian
 *       → TRACE / TRÌNH DIỄN TỪNG BƯỚC.
 *
 * KHÔNG được suy: `predict` ⇒ thao tác trực tiếp · `timeline` ⇒ mô hình tương
 * tác · có mặt trong catalog ⇒ có phủ chương trình. Ba phép suy đó là thứ khiến
 * bảng phủ nói quá.
 *
 * Chạy:  npm run dev  (cửa sổ khác)
 *        node scripts/after-matrix-w4b3a.mjs
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const PORT = argOf("--port", "3000");
const OUT_DIR = resolve(argOf("--out-dir", "../docs/evaluation/m17/w4b3a-after"));
mkdirSync(OUT_DIR, { recursive: true });

const here = (p) => resolve(new URL(p, import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const DESCRIPTORS = JSON.parse(readFileSync(here("../src/simulations/capability-descriptors.json"), "utf-8"));

/** Bố cục đã đo — dải quanh mô hình, theo target, ở bề rộng chuẩn 1920. */
const bandsByTarget = (() => {
  const f = join(OUT_DIR, "measure-1920.json");
  if (!existsSync(f)) return {};
  const m = JSON.parse(readFileSync(f, "utf-8"));
  const out = {};
  for (const r of m.rows) if (r.runnable) out[r.target] = r.ready.bandCount;
  return out;
})();

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cdp = 9300 + Math.floor(Math.random() * 600);
const profile = mkdtempSync(join(tmpdir(), "algosim-matrix-"));
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${cdp}`,
  `--user-data-dir=${profile}`, "--window-size=1920,1080", "about:blank",
], { stdio: "ignore" });

let wsUrl;
for (let i = 0; i < 40 && !wsUrl; i++) {
  try {
    const l = await (await fetch(`http://127.0.0.1:${cdp}/json/list`)).json();
    wsUrl = l.find((t) => t.type === "page")?.webSocketDebuggerUrl;
  } catch { /* chưa lên */ }
  if (!wsUrl) await sleep(250);
}
const ws = new WebSocket(wsUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map();
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => {
  const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails.exception ?? r.result.exceptionDetails));
  return r.result?.result?.value;
};
await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: `http://localhost:${PORT}` });
await sleep(3200);

// URL module lấy TỪ TRANG — xem bẫy hai-instance ở `accept-w4b3a.mjs`.
const urls = JSON.parse(await ev(`(()=>{
  const pick=(s)=>{const h=performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes(s));
    return h.length?h[h.length-1]:new URL(s,location.origin).href;};
  return JSON.stringify({catalog:pick('/src/data/offline-catalog.ts'),registry:pick('/src/simulations/registry.ts'),sims:pick('/src/simulations/index.ts')});
})()`));

const feFacts = JSON.parse(await ev(`(async()=>{
  const c=await import(${JSON.stringify(urls.catalog)});
  const r=await import(${JSON.stringify(urls.sims)});
  const reg=await import(${JSON.stringify(urls.registry)});
  if(reg.listSimulations().length===0) r.registerAllSimulations();
  const samples={};
  for(const e of c.offlineCatalog()) (samples[e.simId]=samples[e.simId]||[]).push(e);
  const out={};
  // listSimulations tra METADATA, khong phai module - lay module qua getSimulation.
  for(const meta of reg.listSimulations()){
    const mod=reg.getSimulation(meta.id);
    if(!mod) continue;
    const rec={
      registered:true,
      interactionMode:mod.interactionMode,
      visualModes:mod.supportedVisualModes,
      hasTimeline:!!mod.timeline,
      hasPredict:!!mod.predict,
      hasExplore:!!mod.explore,
      declaresStageCommitment: !!(mod.predict && mod.predict.presentedInStage),
      sample:!!samples[mod.id],
    };
    const e=(samples[mod.id]||[])[0];
    if(e){
      const v=mod.validateConfig(e.envelope.config);
      if(v.ok){
        let st=null; try{ st=mod.init(v.config); }catch{ st=null; }
        if(st!==null){
          rec.steps = mod.timeline?mod.timeline.stepCount(st):1;
          // Thao tác trực tiếp = có lối vào Khám phá THẬT (đi qua apply, không ai chấm).
          rec.exploreEntry = !!(mod.explore && mod.explore.entry(st,v.config));
          // Cam kết = có bước nào module tự bày cam kết trên sân khấu.
          let commit=0;
          if(mod.timeline && mod.predict && mod.predict.presentedInStage){
            for(let i=0;i<rec.steps;i++){
              if(mod.predict.presentedInStage(mod.timeline.goToStep(st,i))) commit++;
            }
          }
          rec.commitSteps=commit;
        }
      } else { rec.validateError=v.error; }
    }
    out[mod.id]=rec;
  }
  return JSON.stringify(out);
})()`));
chrome.kill();

/* ── GHÉP BA NGUỒN ─────────────────────────────────────────────────────── */

/**
 * Vòng đời mà THAO TÁC SỐNG NGAY TRÊN SÂN KHẤU, luôn mở, không cần cổng nào.
 * `exploratory` = không có dòng thời gian, cả cảnh LÀ chỗ thao tác.
 * `hybrid` = có dòng thời gian NHƯNG vẫn bật/tắt được đối tượng (generic rule
 * scene: học sinh gạt công tắc, engine tính lại chuỗi rule). Bỏ `hybrid` ra thì
 * `generic.rule_scene` — chính bề mặt do LLM dựng — bị đếm là "cảnh tĩnh".
 */
const STAGE_MANIPULABLE = new Set(["exploratory", "hybrid"]);

const VISIBILITY = (reach) =>
  reach.includes("library_discoverable") ? "PUBLIC_SAMPLE"
  : reach.includes("ai_reachable_public") ? "PUBLIC_AI_ONLY"
  : "INTERNAL_FIXTURE";

/**
 * Luật phân loại KHAI TRƯỚC (xem đầu file) — không suy từ tên bài.
 *
 * PHÂN BIỆT ĐO ĐƯỢC ↔ CHỈ KHAI BÁO. 9/23 target là `ai_reachable_public` nhưng
 * KHÔNG có bài mẫu offline, nên không dựng được state để chạy `explore.entry()`
 * hay đếm bước cam kết. Bản đầu của script gộp chúng vào `STATIC_SCENE` — tức
 * bảng nói "12 cảnh tĩnh" trong khi sự thật là "3 cảnh tĩnh + 9 chưa đo được".
 * Đó là nói SAI theo hướng bi quan, và một bảng nói sai theo hướng nào cũng là
 * bảng không dùng được. Nên trạng thái không đo được phải có TÊN RIÊNG.
 */
function experienceOf(fe, authority) {
  if (!fe || !fe.registered) return "NO_FRONTEND_MODULE";
  if (!fe.sample) {
    // Chưa dựng được state ⇒ chỉ đọc được NĂNG LỰC KHAI BÁO, không đọc được hành vi.
    if (fe.hasExplore) return "UNMEASURED_DECLARES_EXPLORE";
    if (fe.declaresStageCommitment) return "UNMEASURED_DECLARES_COMMITMENT";
    if (fe.hasTimeline) return "UNMEASURED_HAS_TIMELINE";
    return "UNMEASURED_NO_SAMPLE";
  }
  if (fe.exploreEntry) return "INTERACTIVE_MODEL";          // thao tác trực tiếp sau cổng
  /* HAI KIỂU THAO TÁC TRỰC TIẾP, đừng gộp và cũng đừng bỏ sót kiểu thứ hai.
     Bài `progressive` có dòng thời gian nên thao tác phải nằm sau chế độ Khám
     phá (nếu không nó lẫn với "bước tiếp theo của thuật toán"). Bài
     `exploratory` KHÔNG có dòng thời gian — cả sân khấu LÀ chỗ thao tác, luôn
     mở, không cần cổng nào; chính `SimulationControls` nói với học sinh câu
     "Mô phỏng khám phá — thao tác trực tiếp trên sân khấu."
     Bản đầu của script xếp chúng vào `STATIC_SCENE` chỉ vì chúng không khai
     `explore` — tức gọi `logic.and_gate` (bật/tắt đầu vào, engine tính lại bảng
     chân trị) là một cảnh tĩnh. Sai, và sai theo hướng tự hạ thấp. */
  if (authority === "representation" && STAGE_MANIPULABLE.has(fe.interactionMode)) return "BOUNDED_ARTIFACT";
  if (STAGE_MANIPULABLE.has(fe.interactionMode)) return "INTERACTIVE_STAGE";
  if (fe.commitSteps > 0) return "COMMITMENT_TRACE";        // cam kết nước đi, engine chấm
  if (fe.steps > 1) return "TRACE_PLAYBACK";                // chỉ điều khiển dòng thời gian
  if (authority === "representation") return "BOUNDED_ARTIFACT";
  return "STATIC_SCENE";
}

/** Ô có ba trạng thái: đo được CÓ/không, hoặc chỉ khai báo (chưa đo). */
const cell = (fe, measured, declared) => {
  if (!fe?.registered) return "—";
  if (!fe.sample) return declared ? "khai (chưa đo)" : "không khai";
  return measured ? "CÓ" : "không";
};

const rows = [];
for (const [targetId, d] of Object.entries(DESCRIPTORS.runtime_targets)) {
  const fe = feFacts[targetId];
  const authority = [...new Set(d.family_memberships.map((m) => m.result_authority))].join("+");
  const families = d.family_memberships.map((m) => m.family_id).join(" · ");
  const bands = bandsByTarget[targetId];
  rows.push({
    target_id: targetId,
    families,
    result_authority: authority,
    visibility: VISIBILITY(d.reachability),
    offline_sample: fe?.sample ? "có" : "không",
    experience: experienceOf(fe, authority),
    lifecycle: fe?.registered ? fe.interactionMode : "—",
    deterministic_owner: d.executor_id,
    direct_manipulation: fe?.sample && STAGE_MANIPULABLE.has(fe?.interactionMode)
      ? "CÓ (sân khấu, luôn mở)"
      : cell(fe, fe?.exploreEntry, fe?.hasExplore),
    algorithm_commitment: fe?.sample && fe?.commitSteps > 0
      ? `CÓ (${fe.commitSteps}/${fe.steps} bước)`
      : cell(fe, false, fe?.declaresStageCommitment),
    challenge_predict: fe?.registered ? (fe.hasPredict ? "có" : "không") : "—",
    playback: fe?.sample
      ? (fe.steps > 1 ? `có (${fe.steps} bước)` : "không")
      : cell(fe, false, fe?.hasTimeline),
    visual_modes: d.visual_modes.join("/"),
    representation_policy: d.visual_modes.length > 1 ? "2D+3D (phù hợp sư phạm)" : "2D_ONLY",
    bands_1920: bands === undefined ? "—" : String(bands),
    browser_evidence: bands === undefined ? "KHÔNG ĐO ĐƯỢC (không có bài mẫu offline)" : "ĐO 4 bề rộng",
    known_gaps: (d.known_gaps ?? []).join("; ") || "—",
    curriculum_anchor: d.curriculum_anchor ?? "—",
  });
}
rows.sort((a, b) => a.target_id.localeCompare(b.target_id));

/* ── TỔNG HỢP — CHỈ SAU KHI ĐÃ CÓ BẢNG TỪNG TARGET ─────────────────────── */
const count = (pred) => rows.filter(pred).length;
const summary = {
  targets: rows.length,
  families: new Set(Object.values(DESCRIPTORS.runtime_targets).flatMap((d) => d.family_memberships.map((m) => m.family_id))).size,
  visibility: {
    PUBLIC_SAMPLE: count((r) => r.visibility === "PUBLIC_SAMPLE"),
    PUBLIC_AI_ONLY: count((r) => r.visibility === "PUBLIC_AI_ONLY"),
    INTERNAL_FIXTURE: count((r) => r.visibility === "INTERNAL_FIXTURE"),
  },
  experience: rows.reduce((a, r) => ((a[r.experience] = (a[r.experience] ?? 0) + 1), a), {}),
  /* ĐO ĐƯỢC và CHỈ KHAI BÁO đếm riêng — gộp lại là tự cho mình điểm cao hơn
     bằng chứng đang có. */
  direct_manipulation_measured: count((r) => r.direct_manipulation.startsWith("CÓ")),
  direct_manipulation_gated: count((r) => r.direct_manipulation === "CÓ"),
  direct_manipulation_always_on_stage: count((r) => r.direct_manipulation === "CÓ (sân khấu, luôn mở)"),
  direct_manipulation_declared_only: count((r) => r.direct_manipulation === "khai (chưa đo)"),
  algorithm_commitment_measured: count((r) => r.algorithm_commitment.startsWith("CÓ")),
  algorithm_commitment_declared_only: count((r) => r.algorithm_commitment === "khai (chưa đo)"),
  challenge_predict: count((r) => r.challenge_predict === "có"),
  measured_in_browser: count((r) => r.bands_1920 !== "—"),
  not_measurable_no_sample: count((r) => r.offline_sample === "không"),
  trigger_band_remaining: rows.filter((r) => r.bands_1920 !== "—").length
    ? "0 (xem measure-*.json: không target nào còn experimentTrigger)" : "chưa đo",
};

writeFileSync(join(OUT_DIR, "after-matrix.json"), JSON.stringify({ when: new Date().toISOString(), summary, rows }, null, 2));

const COLS = [
  ["target_id", "Target"], ["families", "Family"], ["visibility", "Hiện diện"],
  ["offline_sample", "Bài mẫu"], ["experience", "Loại trải nghiệm"], ["lifecycle", "Vòng đời"],
  ["deterministic_owner", "Chủ sở hữu tất định"], ["direct_manipulation", "Thao tác trực tiếp"],
  ["algorithm_commitment", "Cam kết thuật toán"], ["challenge_predict", "Thử thách"],
  ["playback", "Dòng thời gian"], ["representation_policy", "Chính sách biểu diễn"],
  ["visual_modes", "2D/3D"], ["bands_1920", "Dải @1920"], ["browser_evidence", "Bằng chứng trình duyệt"],
  ["known_gaps", "Giới hạn đã khai"],
];
const md = [
  "# W4B-3A — MA TRẬN AFTER (toàn danh mục)",
  "",
  "**Sinh từ nguồn** bởi `frontend/scripts/after-matrix-w4b3a.mjs` — registry",
  "(`capability-descriptors.json`) + module frontend đang chạy + `measure-1920.json`.",
  "Đừng sửa tay: chạy lại script.",
  "",
  "Luật phân loại khai ở đầu script. Ba phép suy BỊ CẤM: `predict` ⇒ thao tác",
  "trực tiếp · `timeline` ⇒ mô hình tương tác · có trong catalog ⇒ có phủ chương trình.",
  "",
  `Tổng: **${summary.targets} target · ${summary.families} family**. ` +
  `Đo được trong trình duyệt **${summary.measured_in_browser}/${summary.targets}** ` +
  `(**${summary.not_measurable_no_sample}** target chưa có bài mẫu offline ⇒ chỉ đọc được năng lực KHAI BÁO).`,
  "",
  `Thao tác trực tiếp: **${summary.direct_manipulation_measured} đo được** ` +
  `(+${summary.direct_manipulation_declared_only} chỉ khai báo). ` +
  `Cam kết thuật toán: **${summary.algorithm_commitment_measured} đo được** ` +
  `(+${summary.algorithm_commitment_declared_only} chỉ khai báo). ` +
  `Khai \`predict\`: **${summary.challenge_predict}**.`,
  "",
  "> Hai cột đếm riêng có chủ đích. Cộng \"đo được\" với \"chỉ khai báo\" thành một",
  "> con số là tự cho mình điểm cao hơn bằng chứng đang có.",
  "",
  `| ${COLS.map((c) => c[1]).join(" | ")} |`,
  `|${COLS.map(() => "---").join("|")}|`,
  ...rows.map((r) => `| ${COLS.map((c) => String(r[c[0]]).replace(/\|/g, "\\|")).join(" | ")} |`),
  "",
  "## Tổng hợp (đếm SAU khi có bảng từng target)",
  "",
  "```json",
  JSON.stringify(summary, null, 2),
  "```",
];
writeFileSync(join(OUT_DIR, "after-matrix.md"), md.join("\n"));

console.log(`${rows.length} target → ${join(OUT_DIR, "after-matrix.md")}`);
console.log(JSON.stringify(summary, null, 2));
process.exit(0);
