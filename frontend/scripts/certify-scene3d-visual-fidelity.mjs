/**
 * certify-scene3d-visual-fidelity.mjs — ĐO ĐỘ ĐÚNG TRỰC QUAN BẰNG ĐIỂM ẢNH.
 *
 * ─── VÌ SAO PHẢI ĐO ĐIỂM ẢNH, KHÔNG PHẢI NHÌN ẢNH ────────────────────────
 *
 * Wave trước đã chứng minh envelope dựng được thành mô phỏng. Câu còn lại
 * KHÁC hẳn: **hình trên màn hình có thể hiện đúng quan hệ hình học không, và
 * có đủ rõ để nhìn ra không.** Cả hai vế đều là mệnh đề về ĐIỂM ẢNH.
 *
 * "Mở ảnh ra xem" đã cứu kho này vài lần, nhưng nó không lặp lại được và không
 * đỏ được. Nên ở đây: chụp bằng CDP, rồi **đưa ảnh ngược vào trang** để chính
 * trình duyệt giải mã PNG, và đo trên `ImageData`. Không thư viện ảnh nào phải
 * thêm vào kho, và con số ra là con số thật.
 *
 * ─── BỐN PHÉP ĐO, VÀ MỆNH ĐỀ TỪNG PHÉP ────────────────────────────────────
 *
 *   hộp mực          — vùng có vẽ trên khung, dùng cho khung nhìn và lề
 *   điểm màu thiết diện — thiết diện có THẬT SỰ lên màn hình không
 *   tỉ lệ diện tích / bao lồi — đáy có đọc ra là LÕM không
 *   quan hệ mặt phẳng ↔ thiết diện — tính từ hàm thuần, trước khi vẽ
 *
 * Cần: `npm run dev` (:3000).
 * Chạy: `node scripts/certify-scene3d-visual-fidelity.mjs --nhan before|after`
 */
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join, resolve } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";

const GOC = resolve(new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const FIXTURES = join(GOC, "docs", "evaluation", "geometry",
  "product-ui-result-rendering", "fixtures");
const THU_MUC = join(GOC, "docs", "evaluation", "geometry", "scene3d-visual-fidelity");

const VIEWPORT = { viewport: 1440, height: 900 };

/**
 * Vai trò ↔ SẮC ĐỘ (độ), mirror của `MAU` trong `scene3d-view.tsx`.
 *
 * ⚠️ Phân loại theo SẮC ĐỘ chứ không theo RGB, và đó không phải chuyện thẩm mỹ.
 * Mọi vật trong cảnh vẽ bán trong suốt (`opacity` 0,14–0,5) trên nền sáng, nên
 * màu ĐẾN MÀN HÌNH nhạt hơn hằng số nguồn rất nhiều — khớp RGB trượt gần hết.
 * Pha alpha làm đổi độ bão hoà, **không** đổi sắc độ, nên sắc độ là thứ còn
 * lại. Bản đầu khớp RGB và đếm ra 5 điểm ảnh cho một elip nhìn thấy rõ.
 */
const SAC_DO = {
  line: 174,       // teal — đường, đường tròn, elip, tức THIẾT DIỆN cong
  polygon: 38,     // hổ phách — đa giác, thiết diện phẳng
  surface: 262,    // tím — mặt phẳng và khối cong
  mesh: 215,       // xám lam — khối đa diện
};

/** Dung sai sắc độ (độ) và ngưỡng bão hoà tối thiểu để tính là "có màu". */
const SAI_SAC_DO = 18;
const BAO_HOA_TOI_THIEU = 0.06;

const nhan = process.argv.includes("--nhan")
  ? process.argv[process.argv.indexOf("--nhan") + 1] : "after";
const ANH = join(THU_MUC, "screenshots", nhan);

const ca = readdirSync(FIXTURES).filter((f) => f.endsWith(".json")).sort()
  .map((f) => JSON.parse(readFileSync(join(FIXTURES, f), "utf-8")));

const rows = [];
let im = false;
function ghi(caseId, phep, mong, thuc, pass) {
  rows.push({ case: caseId, phep, mong, thuc, pass });
  if (!im) console.log(`  ${pass ? "✓" : "✗"} [${caseId}] ${phep} — ${thuc}`);
}

/* ── Đường vào: gõ đề thật, bấm nút thật (giống wave UI trước) ─────────── */
async function guiDe(s, de) {
  await s.eval(`(async()=>{
    const st=await import(${JSON.stringify(s.mods.store)});
    st.useAppStore.getState().setProblemText(${JSON.stringify(de)});
    return 'ok';})()`);
  await sleep(120);
  const bam = await s.eval(`(()=>{
    const b=document.querySelector('button[aria-label="Phân tích đề bằng AI"]');
    if(!b||b.disabled) return 'không bấm được';
    b.click(); return 'ok';})()`);
  if (bam !== "ok") return bam;
  for (let i = 0; i < 40; i++) {
    const x = await s.eval(`(async()=>{
      const st=await import(${JSON.stringify(s.mods.store)});
      const g=st.useAppStore.getState();
      return g.analyzing?'dang':(g.active?'active':(g.unsupported?'unsupported':'trong'));})()`);
    if (x !== "dang" && x !== "trong") return x;
    await sleep(150);
  }
  return "quá hạn chờ";
}

/**
 * PHÂN TÍCH ĐIỂM ẢNH của vùng canvas — chạy TRONG trang, trên PNG do CDP chụp.
 *
 * Trả: hộp mực (toạ độ canvas), tỉ lệ phủ, số điểm theo từng màu vai, và tỉ lệ
 * diện tích/bao lồi của lớp màu đa giác (đo tính LÕM đọc được trên màn hình).
 */
const PHAN_TICH = (b64, sac, saiSac, baoHoa) => `(async()=>{
  const el=document.querySelector('.geo3d-canvas canvas');
  if(!el) return JSON.stringify({loi:'không có canvas'});
  const r=el.getBoundingClientRect();
  const img=new Image();
  await new Promise((ok,fail)=>{img.onload=ok;img.onerror=fail;img.src='data:image/png;base64,'+${JSON.stringify(b64)};});
  const dpr=img.width/window.innerWidth;
  const cw=Math.round(r.width*dpr), ch=Math.round(r.height*dpr);
  const cv=document.createElement('canvas'); cv.width=cw; cv.height=ch;
  const g=cv.getContext('2d');
  g.drawImage(img, Math.round(r.left*dpr), Math.round(r.top*dpr), cw, ch, 0, 0, cw, ch);
  const d=g.getImageData(0,0,cw,ch).data;
  const SAC=${JSON.stringify(sac)}, SAI=${saiSac}, BAO=${baoHoa};
  const dem={}; for(const k in SAC) dem[k]=0;
  const hull=[]; let minx=1e9,miny=1e9,maxx=-1,maxy=-1,muc=0;
  let sx0=1e9,sy0=1e9,sx1=-1,sy1=-1;
  /* "CÓ MỰC" = điểm ảnh CÓ MÀU, không phải "khác điểm ảnh góc trên trái".
     Nền khung là một dải xám rất nhạt, nên phép so với một điểm nền đơn lẻ
     đếm cả nền và cho ra "lề 0px, chiếm 100%" ở mọi ca — một phép đo luôn
     đỏ, tức không đo gì. Vật trong cảnh đều có sắc; nền thì không. */
  const hsv=(R,G,B)=>{
    const r=R/255,gg=G/255,b=B/255;
    const mx=Math.max(r,gg,b), mn=Math.min(r,gg,b), c=mx-mn;
    let h=0;
    if(c>0){
      if(mx===r) h=60*(((gg-b)/c)%6);
      else if(mx===gg) h=60*((b-r)/c+2);
      else h=60*((r-gg)/c+4);
    }
    return [(h+360)%360, mx===0?0:c/mx];
  };
  const lech=(a,b)=>{const t=Math.abs(a-b)%360; return t>180?360-t:t;};
  for(let y=0;y<ch;y++) for(let x=0;x<cw;x++){
    const i=(y*cw+x)*4;
    const [h,s]=hsv(d[i],d[i+1],d[i+2]);
    if(s<BAO) continue;                       // nền xám nhạt — bỏ
    muc++;
    if(x<minx)minx=x; if(x>maxx)maxx=x; if(y<miny)miny=y; if(y>maxy)maxy=y;
    for(const k in SAC){
      if(lech(h,SAC[k])<SAI){
        dem[k]++;
        if(k==='polygon') hull.push([x,y]);
        // Hộp bao của LỚP THIẾT DIỆN (teal, và hổ phách khi nó đang nổi bật).
        if(k==='line'||k==='polygon'){
          if(x<sx0)sx0=x; if(x>sx1)sx1=x; if(y<sy0)sy0=y; if(y>sy1)sy1=y;
        }
      }
    }
  }
  // Bao lồi của lớp màu đa giác (Andrew monotone chain) → tỉ lệ diện tích.
  let tiLeLom=null;
  if(hull.length>50){
    hull.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
    const cross=(o,a,b)=>(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);
    const nua=(pts)=>{const h=[];for(const p of pts){while(h.length>=2&&cross(h[h.length-2],h[h.length-1],p)<=0)h.pop();h.push(p);}h.pop();return h;};
    const H=[...nua(hull),...nua([...hull].reverse())];
    let A=0; for(let i=0;i<H.length;i++){const a=H[i],b=H[(i+1)%H.length];A+=a[0]*b[1]-b[0]*a[1];}
    A=Math.abs(A)/2;
    tiLeLom = A>0 ? hull.length/A : null;
  }
  return JSON.stringify({
    canvas:[cw,ch], muc, phu:muc/(cw*ch),
    hop: maxx<0?null:[minx,miny,maxx,maxy],
    le: maxx<0?null:[minx, miny, cw-1-maxx, ch-1-maxy],
    diem_mau: dem, ti_le_dien_tich_tren_bao_loi: tiLeLom,
    hop_thiet_dien: sx1<0?null:[sx0,sy0,sx1,sy1],
  });})()`;

async function anhVaSo(s) {
  const r = await s._send("Page.captureScreenshot", { format: "png" });
  const b64 = r.result?.data;
  if (!b64) return { loi: "không chụp được" };
  const raw = await s.eval(PHAN_TICH(b64, SAC_DO, SAI_SAC_DO, BAO_HOA_TOI_THIEU));
  return { b64, ...(typeof raw === "string" && raw.startsWith("{") ? JSON.parse(raw) : { loi: String(raw) }) };
}

/** Quan hệ mặt phẳng ↔ thiết diện, tính bằng HÀM THUẦN của sản phẩm. */
const QUAN_HE = (canh) => `(async()=>{
  const M=await import(new URL('/src/simulations/domains/geometry/scene3d-model.ts',location.origin).href);
  // Lượt BASELINE chạy trên mã CHƯA có chính sách miếng mặt phẳng. Nói thẳng
  // "chưa có hàm" thay vì ném: một nền so sánh phải chụp được đúng trạng thái
  // cũ, kể cả khi trạng thái ấy là "chưa có gì để đo".
  if(typeof M.khungMatPhang!=='function'||typeof M.diemHuuHan!=='function')
    return JSON.stringify([{chua_co_chinh_sach:true}]);
  const scene=${JSON.stringify(canh)};
  const diem=M.diemHuuHan(scene.objects);
  const ra=[];
  for(const o of scene.objects){
    if(o.render!=='surface'||!o.point||!o.normal) continue;
    const k=M.khungMatPhang(M.toVec3(o.point), M.toVec3(o.normal), diem);
    if(!k){ ra.push({mp:o.id, khung:null}); continue; }
    // Thiết diện nào nằm trên mặt phẳng này, và miếng có phủ hết nó không?
    const phu=[];
    for(const t of scene.objects){
      let tam=null, ban=0;
      if(t.render==='ellipse'&&t.center){
        tam=M.toVec3(t.center);
        ban=Math.sqrt(Math.max(0,M.toNumber(t.semi_major_sq)));
      } else if(t.render==='circle'&&t.center){
        tam=M.toVec3(t.center); ban=Math.sqrt(Math.max(0,M.toNumber(t.radius_sq)));
      } else continue;
      const d=Math.hypot(tam[0]-k.tam[0],tam[1]-k.tam[1],tam[2]-k.tam[2]);
      // miếng là hình vuông cạnh k.canh ⇒ nội tiếp đường tròn bán kính canh/2
      phu.push({thiet_dien:t.id, cach_tam:d, ban_truc:ban,
                nua_canh:k.canh/2, phu_het: d+ban <= k.canh/2});
    }
    ra.push({mp:o.id, tam:k.tam, canh:k.canh, phu});
  }
  return JSON.stringify(ra);})()`;

async function main() {
  mkdirSync(ANH, { recursive: true });
  console.log(`ĐỘ ĐÚNG TRỰC QUAN SCENE3D — nhãn «${nhan}», 0 lượt gọi model\n`);

  const s = new BrowserSession({ ...VIEWPORT, webgl: true });
  await s.open();
  let dangPhucVu = null;
  await s.interceptJson("*/api/analyze*", () =>
    dangPhucVu ? { status: 200, body: dangPhucVu.envelope } : null);

  const bang = [];
  for (const f of ca) {
    dangPhucVu = f;
    await s.resetBetweenScenarios();
    await sleep(250);
    const id = f.case_id;
    const truoc = s.consoleEvents.length;
    const duong = f.positive_or_negative === "positive";

    const ket = await guiDe(s, f.problem_text);
    if (ket !== (duong ? "active" : "unsupported")) {
      ghi(id, "nạp được ca", duong ? "active" : "unsupported", ket, false);
      continue;
    }

    const dong = { case_id: id, loai: f.positive_or_negative };

    if (duong) {
      const canh = f.envelope.scene3d;
      dong.scene_object_count = canh.objects.length;
      dong.scene_object_kinds = [...new Set(canh.objects.map((o) => o.type))].sort();
      dong.trace_step_count = canh.events.length;
      dong.exact_display = [...f.expected_exact_display];

      // ① QUAN HỆ MẶT PHẲNG ↔ THIẾT DIỆN — trước khi nói tới điểm ảnh
      const raw = await s.eval(QUAN_HE(canh));
      const qh = typeof raw === "string" && raw.startsWith("[")
        ? JSON.parse(raw) : [{ loi: String(raw) }];
      dong.quan_he_mat_phang = qh;
      const capPhu = qh.flatMap((x) => x.phu ?? []);
      /* ⚠️ CỔNG KHÔNG ĐƯỢC TỰ TẮT. Phép tiêm "quay về miếng cố định" làm
         `khungMatPhang` trả `null`, nên không còn cặp nào để so — và bản đầu
         lặng lẽ BỎ QUA phép kiểm, báo 38/38 thay vì đỏ. Cùng lớp lỗi đã sửa ở
         oracle không gian thế giới: cảnh CÓ mặt phẳng và CÓ thiết diện thì
         phép kiểm phải chạy, và không tính được miếng là ĐỎ. */
      const coMp0 = canh.objects.some((o) => o.render === "surface");
      const coTd0 = canh.objects.some(
        (o) => o.render === "ellipse" || o.render === "circle");
      if (coMp0 && coTd0 && !capPhu.length) {
        ghi(id, "miếng mặt phẳng PHỦ HẾT thiết diện", "tính được miếng",
          "KHÔNG tính được miếng nào — chính sách vắng mặt?", false);
      }
      if (capPhu.length) {
        const ok = capPhu.every((c) => c.phu_het);
        ghi(id, "miếng mặt phẳng PHỦ HẾT thiết diện", "mọi cặp phủ",
          capPhu.map((c) => `${c.thiet_dien}: cách ${c.cach_tam.toFixed(2)}`
            + ` + bán trục ${c.ban_truc.toFixed(2)} ≤ nửa cạnh ${c.nua_canh.toFixed(2)}`
            + (c.phu_het ? "" : "  ✗")).join(" · "), ok);
      }

      // ② TUA TỚI BƯỚC CUỐI rồi mới đo ảnh — cảnh phải đầy đủ
      for (let k = 1; k < canh.events.length; k++) {
        await s.clickText("Bước sau"); await sleep(80);
      }
      await sleep(500);
      const px = await anhVaSo(s);
      dong.pixel = { ...px, b64: undefined };

      // ③ KHUNG NHÌN — hình phải nằm gọn trong khung và chiếm phần đáng kể
      if (px.hop) {
        const [cw, ch] = px.canvas;
        const leMin = Math.min(...px.le);
        const chiem = Math.max((px.hop[2] - px.hop[0]) / cw, (px.hop[3] - px.hop[1]) / ch);
        dong.projected_screen_bounds = px.hop;
        dong.camera_fill_ratio = chiem;
        /* ⚠️ CẢNH CÓ MẶT PHẲNG THÌ "MỰC CHẠM MÉP" LÀ ĐÚNG, KHÔNG PHẢI LỖI.
           `plane3` vô hạn; miếng vẽ ra cố ý phủ quá vùng hình học, nên nó
           tràn khỏi khung là hành vi mong muốn. Đòi lề cho TOÀN BỘ mực ở
           những cảnh ấy là phạt đúng thứ vừa sửa.
           Thứ phải nằm gọn trong khung là HÌNH CÓ BIÊN — và ở cảnh có thiết
           diện, phần đáng nhìn nhất chính là thiết diện, thứ đo riêng được
           bằng hộp bao lớp màu của nó. */
        const coMatPhang = canh.objects.some((o) => o.render === "surface");
        const hd = px.hop_thiet_dien;
        const leTd = hd ? Math.min(hd[0], hd[1], cw - 1 - hd[2], ch - 1 - hd[3]) : null;
        const okLe = coMatPhang
          ? (leTd === null ? true : leTd >= 4)
          : leMin >= 4;
        ghi(id, "khung nhìn: hình trong khung, có lề, chiếm ≥25%",
          coMatPhang ? "lề THIẾT DIỆN ≥ 4px và mực chiếm 25–100%"
            : "lề ≥ 4px và chiếm 25–98%",
          `lề mực ${leMin}px${leTd === null ? "" : ` · lề thiết diện ${leTd}px`}`
            + ` · chiếm ${(chiem * 100).toFixed(0)}%`,
          okLe && chiem >= 0.25 && chiem <= (coMatPhang ? 1 : 0.98));
      } else {
        ghi(id, "khung nhìn: có mực trên canvas", "có", "KHUNG TRỐNG", false);
      }

      // ④ THIẾT DIỆN CÓ LÊN MÀN HÌNH KHÔNG
      const coThietDienCong = canh.objects.some(
        (o) => o.render === "ellipse" || o.render === "circle");
      if (coThietDienCong) {
        /* ⚠️ Ở BƯỚC CUỐI thiết diện thường đang được LÀM NỔI (bước đo cuối
           nêu bật đại lượng, và đại lượng phụ thuộc thiết diện), nên nó vẽ
           bằng màu nổi bật hổ phách chứ không phải teal. Bản đầu chỉ đếm teal
           và ra 0 điểm cho một elip nhìn thấy rõ trên ảnh — phép đo sai, không
           phải hình sai.
           Cảnh nào KHÔNG có đa giác nào thì điểm hổ phách chỉ có thể là chính
           thiết diện đang nổi bật, nên cộng vào là an toàn. */
        const coDaGiac = canh.objects.some(
          (o) => o.render === "polygon" || o.type === "face");
        const n = (px.diem_mau?.line ?? 0)
          + (coDaGiac ? 0 : (px.diem_mau?.polygon ?? 0));
        dong.diem_anh_thiet_dien = n;
        /* ⚠️ NGƯỠNG "≥ N ĐIỂM ẢNH" LÀ MỘT CON SỐ BỊA. Bản đầu đặt 200 và đỏ
           trên một hình mà mắt đọc ra ngay — ngưỡng tuyệt đối phụ thuộc độ
           phân giải, độ dày nét và tỉ lệ thu phóng, tức phụ thuộc mọi thứ trừ
           điều cần hỏi.
           Điều cần hỏi ở `p3` là: đường tròn có hiện TRỌN VÒNG không, hay chỉ
           còn nửa cung gần vì nửa kia bị khối nuốt. Đó là mệnh đề về HÌNH DẠNG
           và nó không phụ thuộc tỉ lệ: hộp bao của lớp thiết diện phải lớn
           đáng kể so với hộp bao của cả hình. Nửa cung bị che làm nó co lại
           ngay. */
        const hd = px.hop_thiet_dien, hh = px.hop;
        const cheo = (b) => b ? Math.hypot(b[2] - b[0], b[3] - b[1]) : 0;
        const ti = hh ? cheo(hd) / (cheo(hh) || 1) : 0;
        dong.ti_le_hop_thiet_dien = ti;
        ghi(id, "thiết diện hiện TRỌN VÒNG (hộp bao ≥ 25% hộp hình)",
          "≥ 0,25", `${ti.toFixed(3)} · ${n} điểm ảnh`, ti >= 0.25 && n >= 30);
      }

      // ⑤ ĐÁY LÕM CÓ ĐỌC RA LÀ LÕM KHÔNG
      const dayLom = canh.objects.some((o) => o.type === "polygon3"
        && (o.vertices?.length ?? 0) >= 5);
      if (dayLom && px.ti_le_dien_tich_tren_bao_loi != null) {
        const t = px.ti_le_dien_tich_tren_bao_loi;
        dong.ti_le_dien_tich_tren_bao_loi = t;
        ghi(id, "đáy đọc ra là LÕM (diện tích < bao lồi)", "< 0,97",
          t.toFixed(3), t < 0.97);
      }

      // ⑥ ĐÁP SỐ vẫn còn đủ trên màn hình
      const soDo = JSON.parse(await s.eval(
        `(()=>JSON.stringify([...document.querySelectorAll('.geo3d-readout-gt')].map(e=>e.textContent)))()`));
      dong.readout = soDo;
      ghi(id, "đáp số còn đủ", f.expected_exact_display.join(" · "),
        soDo.join(" · "),
        JSON.stringify([...soDo].sort()) === JSON.stringify([...f.expected_exact_display].sort()));

      // ⑦ NHÃN đại lượng nói đúng loại hình, không phải danh từ chung
      const nhanSo = JSON.parse(await s.eval(
        `(()=>JSON.stringify([...document.querySelectorAll('.geo3d-readout-ten')].map(e=>e.textContent)))()`));
      dong.visible_labels = nhanSo;
      ghi(id, "nhãn đại lượng KHÔNG dùng danh từ chung", "không có «đối tượng»",
        nhanSo.join(" | "), !nhanSo.some((x) => /«?đối tượng»?/i.test(x)));
    } else {
      const the = JSON.parse(await s.eval(`(()=>{
        const e=document.querySelector('.card .eyebrow');
        const p=document.querySelectorAll('.card p');
        return JSON.stringify({badge:e?e.textContent:null,
          than:p[0]?p[0].textContent:null, goiY:p[1]?p[1].textContent:null});})()`));
      dong.thong_bao = the;
      /* HAI GIỌNG = trên CÙNG một thẻ vừa KHẲNG ĐỊNH hệ hỗ trợ dạng bài, vừa
         nói yêu cầu nằm ngoài năng lực. Lời khuyên "diễn đạt lại" KHÔNG tính
         là một giọng: nó là gợi ý hành động, tương thích với cả hai kết luận.
         Bản đầu coi nó là một giọng và báo mâu thuẫn ở một thẻ hoàn toàn
         nhất quán. */
      const ca_the = `${the.badge ?? ""} ${the.than ?? ""} ${the.goiY ?? ""}`;
      const hua = /dạng bài này hệ có mô phỏng/i.test(ca_the);
      const gioiHan = /nằm ngoài các phép dựng|chưa có phép dựng/i.test(ca_the);
      ghi(id, "thẻ từ chối KHÔNG nói hai giọng",
        "không vừa hứa hỗ trợ vừa nói ngoài năng lực",
        hua && gioiHan ? "MÂU THUẪN" : "nhất quán", !(hua && gioiHan));
      ghi(id, "không hứa hệ hỗ trợ dạng bài ngoài năng lực",
        "không có lời hứa", (the.goiY ?? "").slice(0, 70), !hua);
      await sleep(300);
      const px = await anhVaSo(s);
      dong.pixel = { ...px, b64: undefined };
    }

    const moi = s.consoleEvents.slice(truoc);
    dong.console_errors = moi.map((e) => e.loai + ":" + e.text);
    ghi(id, "console sạch", "0 lỗi",
      moi.length ? dong.console_errors.join(" | ") : "0 lỗi", moi.length === 0);

    await sleep(300);
    const duong_anh = join(ANH, `${id}.png`);
    await s.screenshot(duong_anh);
    dong.screenshot_sha256 = createHash("sha256")
      .update(readFileSync(duong_anh)).digest("hex");
    bang.push(dong);
  }

  /* ── TIÊM LỖI ─────────────────────────────────────────────────────────
     Bốn phép làm hỏng + MỘT phép chứng minh tính bất biến. Phép thứ năm mới
     là phép nói lên bản vá: dời `plane3.point` đi rất xa DỌC THEO mặt phẳng
     **không được** đổi gì cả, vì miếng nay đặt theo vùng hình học chứ không
     theo `point`. Trước bản vá, chính phép ấy đẩy miếng ra khỏi màn hình. */
  const tiem = [];
  if (process.argv.includes("--faultcheck")) {
    const sao = (x) => JSON.parse(JSON.stringify(x));
    const lay = (id) => sao(ca.find((c) => c.case_id.startsWith(id)));
    const phep = [
      ["xoay sai pháp tuyến mặt phẳng", "miếng mặt phẳng PHỦ HẾT thiết diện", true,
        () => { const g = lay("p7");
          const m = g.envelope.scene3d.objects.find((o) => o.render === "surface");
          m.normal = [m.normal[1], m.normal[0], m.normal[2]]; return g; }],
      ["phóng bán trục elip vượt miếng", "miếng mặt phẳng PHỦ HẾT thiết diện", true,
        () => { const g = lay("p7");
          const e = g.envelope.scene3d.objects.find((o) => o.render === "ellipse");
          e.semi_major_sq = "5000"; return g; }],
      ["làm đáy LỒI", "đáy đọc ra là LÕM (diện tích < bao lồi)", true,
        () => { const g = lay("p2");
          for (const o of g.envelope.scene3d.objects) {
            if (o.vertices && o.vertices.length === 5) o.vertices[3] = ["4", "12", "0"];
          } return g; }],
      ["đổi một đáp số", "đáp số còn đủ", true,
        () => { const g = lay("p1");
          const q = g.envelope.scene3d.objects.find((o) => o.render === "readout");
          q.value = "73"; q.exact = { kind: "rational", value: "73" }; return g; }],
      ["dời `plane3.point` DỌC mặt phẳng 500 đơn vị", "miếng mặt phẳng PHỦ HẾT thiết diện", false,
        () => { const g = lay("p7");
          const m = g.envelope.scene3d.objects.find((o) => o.render === "surface");
          // (1,0,1) là pháp tuyến ⇒ (1,0,−1) nằm TRONG mặt phẳng
          m.point = [String(Number(m.point[0]) + 500), m.point[1],
            String(Number(m.point[2]) - 500)];
          return g; }],
    ];
    console.log("\nTIÊM LỖI — bốn phép phải ĐỎ, một phép phải VẪN XANH\n");
    for (const [ten, nhamToi, mongDo, dung] of phep) {
      const moc = rows.length;
      im = true;
      const g = dung();
      dangPhucVu = g;
      await s.resetBetweenScenarios(); await sleep(250);
      const ket = await guiDe(s, g.problem_text);
      if (ket === "active") {
        const canh = g.envelope.scene3d;
        const raw = await s.eval(QUAN_HE(canh));
        const qh = typeof raw === "string" && raw.startsWith("[") ? JSON.parse(raw) : [];
        const cap = qh.flatMap((x) => x.phu ?? []);
        if (cap.length) {
          ghi(g.case_id, "miếng mặt phẳng PHỦ HẾT thiết diện", "", "",
            cap.every((c) => c.phu_het));
        }
        for (let k = 1; k < canh.events.length; k++) {
          await s.clickText("Bước sau"); await sleep(60);
        }
        await sleep(400);
        const px = await anhVaSo(s);
        const soDo = JSON.parse(await s.eval(
          `(()=>JSON.stringify([...document.querySelectorAll('.geo3d-readout-gt')].map(e=>e.textContent)))()`));
        ghi(g.case_id, "đáp số còn đủ", "", "",
          JSON.stringify([...soDo].sort())
            === JSON.stringify([...g.expected_exact_display].sort()));
        if (px.ti_le_dien_tich_tren_bao_loi != null) {
          ghi(g.case_id, "đáy đọc ra là LÕM (diện tích < bao lồi)", "", "",
            px.ti_le_dien_tich_tren_bao_loi < 0.97);
        }
      }
      im = false;
      const cua = rows.splice(moc);
      const do_ = cua.filter((r) => !r.pass).map((r) => r.phep);
      const ok = do_.includes(nhamToi) === mongDo;
      tiem.push({ phep: ten, nham_toi: nhamToi, mong_do: mongDo, do_o: do_, pass: ok });
      console.log(`  ${ok ? "✓" : "✗"} ${ten} → ${mongDo ? "phải đỏ" : "phải XANH"}`
        + ` · thực tế đỏ ở: ${do_.join(", ") || "không gì"}`);
    }
  }

  const loi = s.consoleEvents;
  await s.close();

  const dat = rows.filter((r) => r.pass).length;
  const ten = nhan === "before" ? "BASELINE_VISUAL_MATRIX.json" : "AFTER_VISUAL_MATRIX.json";
  writeFileSync(join(THU_MUC, ten), JSON.stringify({
    ...provenance("certify-scene3d-visual-fidelity", { nhan, cases: ca.length }),
    khai: "Độ đúng trực quan đo bằng ĐIỂM ẢNH trên ảnh do CDP chụp, giải mã "
        + "bằng chính trình duyệt. 0 lượt gọi model.",
    nhan,
    run_id: "thesis-final-20260908T160224Z",
    application_llm_calls: 0,
    viewport: `${VIEWPORT.viewport}x${VIEWPORT.height}`,
    checks_pass: dat, checks_total: rows.length,
    FAULT_INJECTIONS: tiem.length,
    FAULT_INJECTIONS_PASS: tiem.filter((t) => t.pass).length,
    fault_injections: tiem,
    UNCAUGHT_FRONTEND_EXCEPTIONS: loi.filter((e) => e.loai === "exception").length,
    cases: bang, rows,
  }, null, 1) + "\n", "utf-8");

  console.log(`\n  ${dat}/${rows.length} phép kiểm · ${bang.length} ảnh → screenshots/${nhan}/`);
  return dat === rows.length ? 0 : 1;
}

if (!existsSync(THU_MUC)) mkdirSync(THU_MUC, { recursive: true });
process.exit(await main());
