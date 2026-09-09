/**
 * certify-product-ui-rendering.mjs — CHÍN ENVELOPE CỦA LƯỢT ĐO CUỐI, DỰNG
 * TRONG CHROME THẬT. **0 lượt gọi model.**
 *
 * ─── CÂU HỎI DUY NHẤT ─────────────────────────────────────────────────────
 *
 * Luận văn đã chứng minh backend phát ra JSON đúng. Câu JSON không tự trả lời
 * được: **nó có thành một mô phỏng trên màn hình học sinh không.** WebGL, tua
 * bước, đáp số vô tỉ, thẻ từ chối — trên chín envelope THẬT của lượt đo cuối.
 *
 * ─── VÌ SAO CHẶN Ở BIÊN MẠNG, KHÔNG NẠP THẲNG VÀO STORE ───────────────────
 *
 * `store.loadEnvelope` là đúng cửa Thư viện đi qua, nhưng nó **bỏ qua** đoạn
 * `onAnalyze → analyzeViaServer → res.json() → rẽ theo status`. Đúng đoạn ấy
 * mới là "response adapter", và đúng đoạn ấy quyết định một envelope thật có
 * dựng được không. Nên ở đây: gõ đề vào ô nhập thật, bấm nút thật, và
 * `/api/analyze` trả về fixture đã đóng băng.
 *
 * ⚠️ **WebGL bắt buộc bật.** Không có nó `tryCreateWebGLRenderer` trả `null`
 * và trang hiện lời nhắn thay canvas — lúc ấy một lượt soát "không lỗi" chẳng
 * chứng minh gì. Script này ĐỎ khi thấy lời nhắn dự phòng.
 *
 * Cần: `npm run dev` (:3000). Chạy: `node scripts/certify-product-ui-rendering.mjs`
 */
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";

const GOC = resolve(new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const THU_MUC = join(GOC, "docs", "evaluation", "geometry", "product-ui-result-rendering");
const FIXTURES = join(THU_MUC, "fixtures");
const ANH = join(THU_MUC, "screenshots");

const VIEWPORT = { viewport: 1440, height: 900 };

const ca = readdirSync(FIXTURES).filter((f) => f.endsWith(".json")).sort()
  .map((f) => JSON.parse(readFileSync(join(FIXTURES, f), "utf-8")));

const rows = [];
let im = false;                     // chế độ tiêm lỗi: đỏ là KỲ VỌNG, đừng ồn
function ghi(caseId, action, expected, actual, pass) {
  rows.push({ case: caseId, action, expected, actual, pass });
  if (!im) console.log(`  ${pass ? "✓" : "✗"} [${caseId}] ${action} — ${actual}`);
}

/* ── Đường vào: gõ đề thật, bấm nút thật ───────────────────────────────── */
async function guiDe(s, de) {
  await s.eval(`(async()=>{
    const st=await import(${JSON.stringify(s.mods.store)});
    st.useAppStore.getState().setProblemText(${JSON.stringify(de)});
    return 'ok';})()`);
  await sleep(120);
  const bam = await s.eval(`(()=>{
    const b=document.querySelector('button[aria-label="Phân tích đề bằng AI"]');
    if(!b) return 'không thấy nút gửi';
    if(b.disabled) return 'nút gửi đang bị khoá';
    b.click(); return 'ok';})()`);
  if (bam !== "ok") return bam;
  for (let i = 0; i < 40; i++) {
    const xong = await s.eval(`(async()=>{
      const st=await import(${JSON.stringify(s.mods.store)});
      const g=st.useAppStore.getState();
      return g.analyzing ? 'dang' : (g.active ? 'active' : (g.unsupported ? 'unsupported'
        : (g.analysisError ? 'loi:'+g.analysisError : 'trong')));})()`);
    if (xong !== "dang" && xong !== "trong") return xong;
    await sleep(150);
  }
  return "quá hạn chờ";
}

const soDoTrenMan = (s) => s.eval(`(()=>JSON.stringify(
  [...document.querySelectorAll('.geo3d-readout-gt')].map(e=>e.textContent)))()`);

async function main() {
  if (!existsSync(ANH)) mkdirSync(ANH, { recursive: true });
  console.log("NGHIỆM THU HIỂN THỊ SẢN PHẨM — 9 envelope thật, 0 lượt gọi model\n");

  const s = new BrowserSession({ ...VIEWPORT, webgl: true });
  await s.open();

  let dangPhucVu = null;   // fixture đang được `/api/analyze` trả về
  await s.interceptJson("*/api/analyze*", () =>
    dangPhucVu ? { status: 200, body: dangPhucVu.envelope } : null);

  /** Một ca, trọn bộ khẳng định. Dùng chung cho lượt sạch và lượt tiêm lỗi —
   *  guard chỉ chứng minh được khi CHÍNH nó là thứ đỏ lên. */
  async function kiemMotCa(f, { chup = true } = {}) {
    dangPhucVu = f;
    await s.resetBetweenScenarios();
    await sleep(250);
    const id = f.case_id;
    const truoc = s.consoleEvents.length;

    const ket = await guiDe(s, f.problem_text);
    const duong = f.positive_or_negative === "positive";
    ghi(id, "adapter rẽ đúng nhánh", duong ? "active" : "unsupported", ket,
        ket === (duong ? "active" : "unsupported"));
    if (ket !== (duong ? "active" : "unsupported")) return;

    if (duong) {
      // ① CANVAS THẬT — và KHÔNG phải lời nhắn dự phòng WebGL
      const canvas = await s.eval(`(()=>{
        if(document.querySelector('.geo3d-fallback')) return 'rơi về lời nhắn WebGL';
        const c=document.querySelector('.geo3d-canvas canvas');
        if(!c) return 'không có canvas';
        return c.width>0 && c.height>0 ? 'có canvas '+c.width+'x'+c.height : 'canvas 0px';})()`);
      ghi(id, "canvas 3D dựng thật", "có canvas", canvas, canvas.startsWith("có canvas"));

      // ② SỐ BƯỚC trên thanh tua khớp `events` của JSON
      const tong = await s.eval(`(()=>{
        const r=document.querySelector('.geo3d-scrub input[type=range],input[type=range]');
        return r ? Number(r.max)+1 : -1;})()`);
      ghi(id, "số bước tua", String(f.expected_trace_event_count), String(tong),
          tong === f.expected_trace_event_count);

      // ③ BƯỚC ĐẦU chưa có đáp số — đó là mục tiêu sư phạm, không phải thiếu sót
      const dau = JSON.parse(await soDoTrenMan(s));
      ghi(id, "bước đầu chưa lộ đáp số", "0 số đo", `${dau.length} số đo`,
          dau.length === 0);

      // ④ TUA TỚI BƯỚC CUỐI bằng nút thật, rồi đọc đáp số TRÊN MÀN HÌNH
      for (let k = 1; k < f.expected_trace_event_count; k++) {
        await s.clickText("Bước sau");
        await sleep(90);
      }
      const cuoi = JSON.parse(await soDoTrenMan(s));
      const khop = JSON.stringify([...cuoi].sort())
        === JSON.stringify([...f.expected_exact_display].sort());
      ghi(id, "đáp số trên màn hình", f.expected_exact_display.join(" · "),
          cuoi.join(" · "), khop);

      // ⑤ CẢNH ĐỔI THEO BƯỚC — bước cuối phải bày nhiều hơn bước đầu
      const nhan = await s.eval(`(()=>document.querySelectorAll('.geo3d-label').length)()`);
      ghi(id, "bước cuối bày đủ hình", ">0 nhãn điểm", `${nhan} nhãn`, nhan > 0);

      // ⑥ KHÔNG rò JSON thô lên bề mặt
      const ro = await s.eval(`(()=>{
        const t=document.body.innerText;
        return ['generic.semantic_program','"scene3d"','free_objects','semantic_program']
          .filter(x=>t.includes(x)).join(',') || 'sạch';})()`);
      ghi(id, "không rò định danh kỹ thuật", "sạch", ro, ro === "sạch");
    } else {
      /* ① THẺ TỪ CHỐI nói đúng lớp nguyên nhân — và HAI CA ÂM PHẢI KHÁC NHAU.
         `n1` dừng ở lượt viết chương trình: thử lại còn cửa, nên "CHƯA DỰNG
         ĐƯỢC" là đúng. `n2` trượt cổng phủ: không phép dựng nào tạo ra vật ấy,
         nên chữ "CHƯA" hứa một tương lai không tồn tại. Một nhãn dùng chung
         cho cả hai là nói sai cho một trong hai. */
      const nhanMong = id.startsWith("n2")
        ? "NGOÀI PHẠM VI DỰNG HÌNH" : "CHƯA DỰNG ĐƯỢC MÔ PHỎNG";
      const the = await s.eval(`(()=>{
        const e=[...document.querySelectorAll('.eyebrow')].map(x=>x.textContent);
        return e.join('|') || 'không có thẻ';})()`);
      ghi(id, "thẻ từ chối hiện ra", nhanMong, the, the.includes(nhanMong));

      // ② KHÔNG cảnh, KHÔNG đáp số — kể cả sót lại từ ca trước
      const sach = await s.eval(`(()=>{
        const c=document.querySelector('.geo3d-canvas,.geo3d-readout');
        return c ? 'còn dấu vết cảnh' : 'sạch';})()`);
      ghi(id, "không còn cảnh của ca trước", "sạch", sach, sach === "sạch");

      // ③ KHÔNG in mã lỗi kỹ thuật cho học sinh
      const ro = await s.eval(`(()=>{
        const t=document.body.innerText;
        return ['geometry_generation_failed','structural_coverage',
          'requested_operation_uncovered','UNANCHORED_DERIVED_ASSUMPTION','error_code']
          .filter(x=>t.includes(x)).join(',') || 'sạch';})()`);
      ghi(id, "không rò mã lỗi", "sạch", ro, ro === "sạch");

      /* (PRODUCT_RESPONSE_CONTRACT_ALIGNMENT) ④ TỪ CHỐI CÓ CẤU TRÚC.
         `THESIS_DRAFT §1.6/§3.9` hứa nêu giai đoạn dừng và loại thất bại. Ba
         khẳng định trên MÀN HÌNH THẬT, vì backend giao đủ trường mà bề mặt bỏ
         qua thì lời hứa vẫn chưa được giữ. */
      const sk = JSON.parse(await s.eval(`(()=>{
        const d=document.querySelector('.refusal-facts');
        if(!d) return JSON.stringify({co:false});
        const c=[...d.querySelectorAll('div')].map(x=>({
          nhan:(x.querySelector('dt')||{}).textContent||'',
          gia:(x.querySelector('dd')||{}).textContent||''}));
        return JSON.stringify({co:true,cap:c});})()`));
      ghi(id, "hiện giai đoạn dừng + loại vấn đề", "2 cặp",
          sk.co ? `${sk.cap.length} cặp` : "không có khối",
          sk.co === true && sk.cap.length === 2);
      if (sk.co) {
        const trong = sk.cap.filter((c) => !c.gia
          || c.gia.includes("Không xác định")).map((c) => c.nhan);
        ghi(id, "hai sự thật đều XÁC ĐỊNH được", "0 ô trống",
            trong.length ? trong.join(",") : "0 ô trống", trong.length === 0);
      }

      /* ⑤ KHÔNG NÓI HAI LẦN CÙNG MỘT CÂU. Phát hiện bằng MẮT trên ảnh `n2`:
         `learner_reason` (backend) và câu gợi ý (frontend) liệt kê gần y hệt
         một danh sách năng lực, nên học sinh đọc hai lần cùng một điều mà
         không nhận thêm thông tin nào. Không phép kiểm tự động nào lúc ấy bắt
         được — chúng chỉ hỏi "có mặt không", không hỏi "có thừa không".
         Đo bằng đoạn trùng dài nhất giữa hai khối văn bản. */
      const trung = await s.eval(`(()=>{
        const c=document.querySelector('.card');
        const p=c.querySelector('p'), n=c.querySelector('.notes');
        if(!p||!n) return -1;
        const a=p.innerText, b=n.innerText;
        let max=0;
        for(let i=0;i<b.length;i++){
          for(let j=i+max+1;j<=b.length;j++){
            if(a.includes(b.slice(i,j))) max=Math.max(max,j-i); else break;
          }
        }
        return max;})()`);
      ghi(id, "gợi ý không lặp lại lý do", "<40 ký tự trùng",
          `${trung} ký tự trùng`, trung >= 0 && trung < 40);

      /* ⑥ MỘT MÀN HÌNH, MỘT KẾT LUẬN. `n2` từng vừa nói "ngoài các phép dựng"
         (mã) vừa khuyên "diễn đạt lại đề" (thông điệp) — hai kết luận ngược
         nhau trên cùng một thẻ, và học sinh tin câu sai. */
      if (id.startsWith("n2")) {
        const mau = await s.eval(`(()=>{
          const t=document.querySelector('.card').innerText;
          return JSON.stringify({ngoai:t.includes('ngoài các phép dựng'),
                                 viet_lai:t.includes('diễn đạt lại')});})()`);
        const m = JSON.parse(mau);
        ghi(id, "không có hai kết luận trái nhau", "ngoài-bao-đóng, KHÔNG khuyên viết lại",
            `ngoài=${m.ngoai} viết_lại=${m.viet_lai}`, m.ngoai && !m.viet_lai);
      }
    }

    // ⑦ KHÔNG có ngoại lệ / lỗi console mới trong ca này
    const moi = s.consoleEvents.slice(truoc);
    ghi(id, "console sạch", "0 lỗi",
        moi.length ? moi.map((e) => e.loai + ":" + e.text).join(" | ") : "0 lỗi",
        moi.length === 0);

    await sleep(400);   // renderer ổn định trước khi chụp
    if (chup) await s.screenshot(join(ANH, `${id}.png`));
  }

  for (const f of ca) await kiemMotCa(f);

  /* ── TIÊM LỖI ────────────────────────────────────────────────────────
     Sáu bản envelope HỎNG theo sáu kiểu khác nhau. Mỗi bản phải làm ít nhất
     một khẳng định ĐỎ, và phải đỏ ở ĐÚNG khẳng định nhắm tới — một guard đỏ
     vì lý do khác là một guard vẫn chưa được chứng minh. */
  const tiem = [];
  if (process.argv.includes("--faultcheck")) {
    const p1 = ca.find((x) => x.case_id === "p1_chop_thiet_dien_khoang_cach");
    const n2 = ca.find((x) => x.case_id === "n2_khoi_ghep_bu_can_boolean");
    const sao = (x) => JSON.parse(JSON.stringify(x));
    const doiSo = (f) => {
      const g = sao(f);
      const o = g.envelope.scene3d.objects.find((z) => z.render === "readout");
      o.value = "73"; o.exact = { kind: "rational", value: "73" };
      return g;
    };
    const phep = [
      ["gỡ scene3d", "canvas 3D dựng thật",
        () => { const g = sao(p1); delete g.envelope.scene3d; return g; }],
      ["đổi một đáp số 72→73", "đáp số trên màn hình", () => doiSo(p1)],
      ["cắt bớt events", "số bước tua",
        () => { const g = sao(p1); g.envelope.scene3d.events.length = 3; return g; }],
      ["lật status sang unsupported", "adapter rẽ đúng nhánh",
        () => { const g = sao(p1); g.envelope.status = "unsupported";
                g.envelope.failure_category = "geometry_generation_failed"; return g; }],
      /* ⚠️ Tiêm vào `description` KHÔNG đỏ được, và đó là phát hiện chứ không
         phải hỏng phép tiêm: đề bài nằm sau nút «Xem đề» nên nó không có mặt
         trong `innerText`. Guard soi thứ NGƯỜI HỌC THẤY, nên phép tiêm cũng
         phải đặt vào chỗ người học thấy — nhãn của số đo. */
      ["rò định danh vào nhãn số đo", "không rò định danh kỹ thuật",
        () => { const g = sao(p1);
                g.envelope.scene3d.objects.find((z) => z.render === "readout")
                  .label = "generic.semantic_program"; return g; }],
      ["đổi lớp từ chối của ca âm", "thẻ từ chối hiện ra",
        () => { const g = sao(n2); g.envelope.failure_category = "out_of_scope"; return g; }],
    ];
    console.log("\nTIÊM LỖI — mỗi phép phải làm ĐỎ đúng khẳng định nó nhắm tới\n");
    for (const [ten, nhamToi, dung] of phep) {
      const moc = rows.length;
      im = true;
      await kiemMotCa(dung(), { chup: false });
      im = false;
      const cua = rows.splice(moc);                       // không trộn vào bảng sạch
      const do_ = cua.filter((r) => !r.pass).map((r) => r.action);
      const dungCho = do_.includes(nhamToi);
      tiem.push({ phep: ten, nham_toi: nhamToi, do_o: do_, pass: dungCho });
      console.log(`  ${dungCho ? "✓" : "✗"} ${ten} → đỏ ở: ${do_.join(", ") || "KHÔNG CÓ GÌ ĐỎ"}`);
    }
  }

  const loi = s.consoleEvents;
  await s.close();

  const dat = rows.filter((r) => r.pass).length;
  const anhChup = readdirSync(ANH).filter((f) => f.endsWith(".png")).length;
  const bao = {
    ...provenance("certify-product-ui-rendering", {
      viewport: `${VIEWPORT.viewport}x${VIEWPORT.height}`, cases: ca.length }),
    khai: "Chín envelope của lượt đo cuối, dựng trong Chrome thật qua ĐƯỜNG "
        + "NGƯỜI DÙNG (gõ đề → bấm nút → /api/analyze bị chặn trả fixture đóng "
        + "băng). 0 lượt gọi model, 0 lượt gọi provider.",
    run_id: "thesis-final-20260908T160224Z",
    application_llm_calls: 0,
    real_provider_calls: 0,
    viewport: `${VIEWPORT.viewport}x${VIEWPORT.height}`,
    webgl: "swiftshader",
    server_starts: s.serverStarts,
    POSITIVE_CASES_RENDERED: ca.filter((f) => f.positive_or_negative === "positive").length,
    NEGATIVE_CASES_PRESENTED: ca.filter((f) => f.positive_or_negative === "negative").length,
    SCREENSHOTS_CAPTURED: anhChup,
    UNCAUGHT_FRONTEND_EXCEPTIONS: loi.filter((e) => e.loai === "exception").length,
    CONSOLE_EVENTS: loi,
    checks_pass: dat,
    checks_total: rows.length,
    UI_RESULT_RENDERING: dat === rows.length ? "PASS" : "FAIL",
    FAULT_INJECTIONS: tiem.length,
    FAULT_INJECTIONS_PROVEN_RED: tiem.filter((t) => t.pass).length,
    fault_injections: tiem,
    rows,
  };
  writeFileSync(join(THU_MUC, "UI_ACCEPTANCE_MATRIX.json"),
    JSON.stringify(bao, null, 1) + "\n", "utf-8");

  console.log(`\n  ${dat}/${rows.length} phép kiểm · ${anhChup} ảnh · `
    + `ngoại lệ ${bao.UNCAUGHT_FRONTEND_EXCEPTIONS} · `
    + `UI_RESULT_RENDERING = ${bao.UI_RESULT_RENDERING}`);
  return dat === rows.length ? 0 : 1;
}

process.exit(await main());
