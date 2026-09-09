/**
 * certify-scene3d-hidden-lines.mjs — NÉT LIỀN / NÉT KHUẤT, ĐO BẰNG ĐIỂM ẢNH.
 *
 * ─── HAI TẦNG, VÀ VÌ SAO PHẢI TÁCH ────────────────────────────────────────
 *
 *   A. PHÂN LOẠI THẤY/KHUẤT — oracle ĐỘC LẬP, không hỏi renderer một câu nào.
 *   B. DẠNG NÉT TRÊN CANVAS — đoạn thấy có liền không, đoạn khuất có đứt không.
 *
 * Gộp hai tầng lại thì một renderer vẽ mọi thứ bằng nét liền vẫn "đạt", vì
 * chẳng có gì để so. Tách ra thì tầng A nói *"điểm này ĐÁNG LẼ bị che"* trước,
 * rồi tầng B mới đi xem màn hình có nói đúng như vậy không.
 *
 * ─── ORACLE, VÀ VÌ SAO NÓ ĐỘC LẬP THẬT ───────────────────────────────────
 *
 * Ba thiết diện của `p3`/`p6`/`p7` nằm **trên mặt** khối lồi (đã chứng minh ở
 * `scene3d_world_oracles.py`, tolerance 0). Với một khối LỒI, một điểm trên mặt
 * nhìn thấy được **khi và chỉ khi** pháp tuyến ngoài tại đó hướng về camera:
 *
 *     thấy  ⟺  n̂(Q) · (mắt − Q) > 0
 *
 * Đó là hình học thuần, tính từ toạ độ backend gửi. Nó KHÔNG đọc cờ nào của
 * renderer, không đọc buffer chiều sâu, không gọi `Raycaster`.
 *
 * ⚠️ Camera mặc định tính lại bằng chính hàm thuần của sản phẩm
 * (`diemHuuHan` → `hopBaoCuaDiem` → `khungNhinVua`). Đó KHÔNG phải vòng luẩn
 * quẩn: hàm ấy là **đặc tả** camera đứng ở đâu, còn phần được kiểm — phép che
 * khuất — vẫn do oracle độc lập quyết.
 *
 * Cần: `npm run dev` (:3000).
 */
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join, resolve } from "node:path";
import { BrowserSession, sleep } from "./browser-runner.mjs";
import { provenance } from "./evidence.mjs";

const GOC = resolve(new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const FIXTURES = join(GOC, "docs", "evaluation", "geometry",
  "product-ui-result-rendering", "fixtures");
const THU_MUC = join(GOC, "docs", "evaluation", "geometry", "scene3d-hidden-lines");
const ANH = join(THU_MUC, "screenshots");

const VIEWPORT = { viewport: 1440, height: 900 };
const FOV = 50;                     // khớp `new THREE.PerspectiveCamera(50, …)`

/** Ca có thiết diện nằm TRÊN MẶT một khối lồi ⇒ oracle pháp tuyến dùng được. */
const CA_CO_THIET_DIEN = [
  "p3_mat_cau_va_thiet_dien_tron",
  "p6_thiet_dien_elip_cua_hinh_tru",
  "p7_thiet_dien_elip_cua_hinh_non",
];

const rows = [];
let im = false;
function ghi(ca, phep, mong, thuc, pass) {
  rows.push({ case: ca, phep, mong, thuc, pass });
  if (!im) console.log(`  ${pass ? "✓" : "✗"} [${ca}] ${phep} — ${thuc}`);
}

const ca = readdirSync(FIXTURES).filter((f) => f.endsWith(".json")).sort()
  .map((f) => JSON.parse(readFileSync(join(FIXTURES, f), "utf-8")));

async function guiDe(s, de) {
  await s.eval(`(async()=>{const st=await import(${JSON.stringify(s.mods.store)});
    st.useAppStore.getState().setProblemText(${JSON.stringify(de)});return 'ok';})()`);
  await sleep(120);
  await s.eval(`(()=>{const b=document.querySelector('button[aria-label="Phân tích đề bằng AI"]');
    if(b&&!b.disabled) b.click(); return 'ok';})()`);
  for (let i = 0; i < 40; i++) {
    const x = await s.eval(`(async()=>{const st=await import(${JSON.stringify(s.mods.store)});
      const g=st.useAppStore.getState();
      return g.analyzing?'dang':(g.active?'active':(g.unsupported?'unsupported':'trong'));})()`);
    if (x !== "dang" && x !== "trong") return x;
    await sleep(150);
  }
  return "quá hạn";
}

/**
 * ORACLE + CHIẾU MÀN HÌNH, chạy trong trang.
 *
 * Trả, cho mỗi điểm mẫu trên thiết diện: `{t, thay, px, py}` — `thay` do oracle
 * pháp tuyến quyết, `px/py` là chỗ đi soi điểm ảnh.
 */
const MAU_THIET_DIEN = (canh, fov, goc = 0) => `(async()=>{
  const M=await import(new URL('/src/simulations/domains/geometry/scene3d-model.ts',location.origin).href);
  const C=await import(new URL('/src/simulations/domains/geometry/scene3d-camera.ts',location.origin).href);
  const el=document.querySelector('.geo3d-canvas canvas');
  if(!el) return JSON.stringify({loi:'không canvas'});
  const r=el.getBoundingClientRect();
  const scene=${JSON.stringify(canh)};

  // ── camera mặc định, tính bằng ĐÚNG hàm thuần của sản phẩm ──────────
  const kn=C.khungNhinVua(C.hopBaoCuaDiem(M.diemHuuHan(scene.objects)),
                          ${fov}, r.width/r.height);
  if(!kn) return JSON.stringify({loi:'không đặt được khung nhìn'});
  const dich=kn.nhinVao;
  /* Camera SAU KHI XOAY, tinh duoc chu khong doan: OrbitControls doi phuong vi
     dung 2*PI*dx/clientHeight cho moi luot keo ngang, va damping chi doi DUONG
     DI chu khong doi DIEM DEN. Xoay quanh truc dung cua the gioi.
     (Chu thich khong dau va khong backtick: khoi nay nam trong template
     literal duoc tiem vao trang.) */
  const G=${goc};
  const d0=[kn.viTri[0]-dich[0], kn.viTri[1]-dich[1], kn.viTri[2]-dich[2]];
  const cg=Math.cos(G), sg=Math.sin(G);
  const mat=[dich[0]+d0[0]*cg+d0[2]*sg, dich[1]+d0[1], dich[2]-d0[0]*sg+d0[2]*cg];

  const tru=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
  const cham=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
  const cheo=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const dai=(a)=>Math.hypot(a[0],a[1],a[2]);
  const chuan=(a)=>{const d=dai(a)||1;return [a[0]/d,a[1]/d,a[2]/d];};

  // ── chiếu phối cảnh, dựng tay (không mượn ma trận của renderer) ─────
  const f=chuan(tru(dich,mat));
  const ph=chuan(cheo(f,[0,1,0]));
  const tren=cheo(ph,f);
  const tanF=Math.tan(${fov}*Math.PI/360), ti=r.width/r.height;
  const chieu=(Q)=>{
    const v=tru(Q,mat);
    const z=-cham(v,f);
    if(z>=0) return null;                       // sau lưng camera
    const x=cham(v,ph)/(-z)/(tanF*ti), y=cham(v,tren)/(-z)/tanF;
    return [ (x+1)/2*r.width, (1-y)/2*r.height ];
  };

  const khoi=scene.objects.find(o=>o.render==='curved_solid');
  const td=scene.objects.find(o=>o.render==='ellipse'||o.render==='circle');
  if(!khoi||!td) return JSON.stringify({loi:'ca không có khối cong + thiết diện'});
  const A=M.toVec3(khoi.anchor);
  const D=khoi.apex_or_top?M.toVec3(khoi.apex_or_top):null;
  const truc=D?chuan(tru(D,A)):null;

  // pháp tuyến NGOÀI tại một điểm trên mặt khối lồi
  const phapTuyen=(Q)=>{
    if(khoi.curved_kind==='ball') return chuan(tru(Q,A));
    const w=tru(Q,A), t=cham(w,truc);
    const ban=[w[0]-truc[0]*t, w[1]-truc[1]*t, w[2]-truc[2]*t];
    if(khoi.curved_kind==='cylinder') return chuan(ban);
    // NÓN: pháp tuyến nghiêng — thành phần dọc trục bằng r/h
    const R=Math.sqrt(M.toNumber(khoi.radius_sq)), H=Math.sqrt(M.toNumber(khoi.height_sq));
    const b=chuan(ban);
    return chuan([b[0]*H+truc[0]*R, b[1]*H+truc[1]*R, b[2]*H+truc[2]*R]);
  };

  // điểm mẫu trên thiết diện
  const tam=M.toVec3(td.center);
  let A1,B1;
  if(td.render==='ellipse'){
    const m1=M.toVec3(td.major_dir), m2=M.toVec3(td.minor_dir);
    const a=Math.sqrt(M.toNumber(td.semi_major_sq)), b=Math.sqrt(M.toNumber(td.semi_minor_sq));
    const u1=chuan(m1), u2=chuan(m2);
    A1=[u1[0]*a,u1[1]*a,u1[2]*a]; B1=[u2[0]*b,u2[1]*b,u2[2]*b];
  } else {
    const n=chuan(M.toVec3(td.normal));
    const t0=Math.abs(n[0])<0.9?[1,0,0]:[0,1,0];
    const u1=chuan(cheo(n,t0)), u2=chuan(cheo(n,u1));
    const R=Math.sqrt(M.toNumber(td.radius_sq));
    A1=[u1[0]*R,u1[1]*R,u1[2]*R]; B1=[u2[0]*R,u2[1]*R,u2[2]*R];
  }
  const mau=[];
  const N=72;
  for(let i=0;i<N;i++){
    const th=i/N*Math.PI*2, c=Math.cos(th), s=Math.sin(th);
    const Q=[tam[0]+A1[0]*c+B1[0]*s, tam[1]+A1[1]*c+B1[1]*s, tam[2]+A1[2]*c+B1[2]*s];
    const n=phapTuyen(Q);
    const thay=cham(n,chuan(tru(mat,Q)))>0;
    const p=chieu(Q);
    if(p) mau.push({i, thay, px:p[0], py:p[1]});
  }
  return JSON.stringify({camera:{viTri:mat,nhinVao:dich,fov:${fov}},
    canvas:[r.width,r.height], mau});
})()`;

/** Đọc điểm ảnh tại các vị trí mẫu, trên PNG do CDP chụp, giải mã trong trang. */
const DOC_DIEM = (b64, mau) => `(async()=>{
  const el=document.querySelector('.geo3d-canvas canvas');
  const r=el.getBoundingClientRect();
  const img=new Image();
  await new Promise((ok,f)=>{img.onload=ok;img.onerror=f;img.src='data:image/png;base64,'+${JSON.stringify(b64)};});
  const dpr=img.width/window.innerWidth;
  const cw=Math.round(r.width*dpr), ch=Math.round(r.height*dpr);
  const cv=document.createElement('canvas'); cv.width=cw; cv.height=ch;
  const g=cv.getContext('2d');
  g.drawImage(img, Math.round(r.left*dpr), Math.round(r.top*dpr), cw, ch, 0, 0, cw, ch);
  const d=g.getImageData(0,0,cw,ch).data;
  const hsv=(R,G,B)=>{const a=R/255,b=G/255,c=B/255;
    const mx=Math.max(a,b,c),mn=Math.min(a,b,c),k=mx-mn;let h=0;
    if(k>0){ if(mx===a)h=60*(((b-c)/k)%6); else if(mx===b)h=60*((c-a)/k+2); else h=60*((a-b)/k+4); }
    return [(h+360)%360, mx===0?0:k/mx];};
  const lech=(x,y)=>{const t=Math.abs(x-y)%360;return t>180?360-t:t;};
  /* "Có nét" tại một điểm mẫu = trong bán kính 1px có điểm ảnh mang sắc của
     đường (teal 174) hoặc của vật đang nổi bật (hổ phách 43).
     ⚠️ Bán kính PHẢI nhỏ hơn khe đứt. Bản đầu lấy ±3px trong khi vành dày ~9px
     và khe đứt ~12px, nên mọi điểm mẫu đều "có nét" và đoạn khuất đo ra 100% —
     một phép đo báo "không có nét đứt" trên một hình đứt rõ trong ảnh. */
  const coNet=(px,py)=>{
    const X=Math.round(px*dpr), Y=Math.round(py*dpr);
    for(let dy=-1;dy<=1;dy++) for(let dx=-1;dx<=1;dx++){
      const x=X+dx,y=Y+dy;
      if(x<0||y<0||x>=cw||y>=ch) continue;
      const i=(y*cw+x)*4; const [h,s]=hsv(d[i],d[i+1],d[i+2]);
      if(s>=0.08 && (lech(h,174)<20 || lech(h,43)<20)) return true;
    }
    return false;
  };
  return JSON.stringify(${JSON.stringify(mau)}.map(m=>({...m, net:coNet(m.px,m.py)})));
})()`;

/**
 * Chuỗi `net` của một cung → có phải NÉT ĐỨT không.
 *
 * ⚠️ NGƯỠNG DƯỚI 0,5 LÀ HIỆU CHỈNH TỪ PHÉP TIÊM, không phải một con số chọn
 * cho đẹp. Tiêu chí đầu chỉ đòi *"đổi ≥ 2 lần và tỉ lệ trong 0,1–0,95"*, và
 * phép tiêm *"vẽ mọi phần bằng nét liền"* (đặt cả hai lượt về `LessEqualDepth`)
 * **lọt qua**: khi ấy cung khuất chẳng vẽ gì cả, chỉ còn răng cưa rải rác, ra
 * 15–37% với 2 lần đổi — và tiêu chí đọc "thưa" thành "đứt".
 *
 * Hai quần thể đo được tách bạch:
 *     nét đứt THẬT        62 %, 69 %, 79 %, 80 %   (14, 10, 4, 6 lần đổi)
 *     tiêm "vẽ liền hết"  15 %, 32 %, 37 %         (2 lần đổi)
 *
 * Nên vạch đặt ở 0,5: một nét đứt thật vẽ QUÁ NỬA chiều dài cung, một cung
 * không được vẽ thì không.
 */
function laNetDut(chuoi) {
  let doi = 0;
  for (let i = 1; i < chuoi.length; i++) if (chuoi[i] !== chuoi[i - 1]) doi++;
  const co = chuoi.filter(Boolean).length / (chuoi.length || 1);
  return { doi, tiLe: co, dut: doi >= 2 && co >= 0.5 && co < 0.95 };
}

async function main() {
  mkdirSync(ANH, { recursive: true });
  console.log("NÉT LIỀN / NÉT KHUẤT — oracle độc lập + đo điểm ảnh, 0 lượt gọi model\n");
  const s = new BrowserSession({ ...VIEWPORT, webgl: true });
  await s.open();
  let phucVu = null;
  await s.interceptJson("*/api/analyze*", () =>
    phucVu ? { status: 200, body: phucVu.envelope } : null);

  const bang = [];
  for (const f of ca.filter((x) => CA_CO_THIET_DIEN.includes(x.case_id))) {
    phucVu = f;
    await s.resetBetweenScenarios(); await sleep(250);
    const id = f.case_id;
    if (await guiDe(s, f.problem_text) !== "active") {
      ghi(id, "nạp được ca", "active", "hỏng", false); continue;
    }
    const canh = f.envelope.scene3d;
    for (let k = 1; k < canh.events.length; k++) { await s.clickText("Bước sau"); await sleep(70); }
    await sleep(500);

    const raw = await s.eval(MAU_THIET_DIEN(canh, FOV));
    const o = typeof raw === "string" && raw.startsWith("{") ? JSON.parse(raw) : { loi: String(raw) };
    if (o.loi) { ghi(id, "oracle dựng được điểm mẫu", "có", o.loi, false); continue; }

    const thay = o.mau.filter((m) => m.thay).length;
    const khuat = o.mau.length - thay;
    ghi(id, "oracle chia thiết diện thành phần THẤY và phần KHUẤT",
      "cả hai đều > 0", `thấy ${thay} · khuất ${khuat}`, thay > 0 && khuat > 0);
    if (!(thay > 0 && khuat > 0)) continue;

    const shot = await s._send("Page.captureScreenshot", { format: "png" });
    const doc = JSON.parse(await s.eval(DOC_DIEM(shot.result.data, o.mau)));
    const cungThay = doc.filter((m) => m.thay).map((m) => m.net);
    const cungKhuat = doc.filter((m) => !m.thay).map((m) => m.net);
    const A = laNetDut(cungThay), B = laNetDut(cungKhuat);

    ghi(id, "đoạn THẤY liền (không ngắt quãng)", "tỉ lệ có nét ≥ 0,9",
      `${(A.tiLe * 100).toFixed(0)}% · ${A.doi} lần đổi`, A.tiLe >= 0.9);
    ghi(id, "đoạn KHUẤT có chu kỳ NÉT ĐỨT", "đổi ≥ 2 lần, tỉ lệ 0,1–0,95",
      `${(B.tiLe * 100).toFixed(0)}% · ${B.doi} lần đổi`, B.dut);
    ghi(id, "hai kiểu PHÂN BIỆT được", "tỉ lệ thấy > tỉ lệ khuất + 0,15",
      `${(A.tiLe * 100).toFixed(0)}% vs ${(B.tiLe * 100).toFixed(0)}%`,
      A.tiLe > B.tiLe + 0.15);

    // ── XOAY CAMERA: PHÂN LOẠI phải cập nhật, không chỉ hình dịch chỗ ────
    //
    // ⚠️ Bản đầu so cờ `net` tại ĐÚNG các vị trí điểm ảnh cũ sau khi xoay, rồi
    // mừng vì 69/72 điểm "đổi". Nhưng xoay xong đường cong đã đi chỗ khác, nên
    // phép ấy đo *hình có dịch không* — một điều hiển nhiên — chứ không đo
    // *phân loại có cập nhật không*. Nay: tính lại camera SAU xoay, chạy lại
    // oracle trên chính các điểm thế giới ấy, rồi so nét ở vị trí MỚI.
    await s.screenshot(join(ANH, `${id}-mac-dinh.png`));
    const rc = await s.eval(`(()=>{const c=document.querySelector('.geo3d-canvas canvas');
      const r=c.getBoundingClientRect();
      return JSON.stringify([r.left+r.width/2, r.top+r.height/2, r.height]);})()`);
    const [cx, cy, ch] = JSON.parse(rc);
    const dx = 264;
    await s._send("Input.dispatchMouseEvent", { type: "mousePressed", x: cx, y: cy, button: "left", buttons: 1, clickCount: 1 });
    /* CHUỖI KHUNG của thao tác xoay — ảnh tĩnh một góc chỉ chứng minh trạng
       thái, không chứng minh HÀNH VI. Sáu khung trong lúc kéo cho thấy nét
       liền và nét đứt đổi vai liên tục chứ không phải một lần. */
    mkdirSync(join(ANH, "xoay", id), { recursive: true });
    for (let i = 1; i <= 12; i++) {
      await s._send("Input.dispatchMouseEvent", { type: "mouseMoved", x: cx + i * (dx / 12), y: cy, button: "left", buttons: 1 });
      await sleep(60);
      if (i % 2 === 0) {
        await s.screenshot(join(ANH, "xoay", id, `khung-${String(i / 2).padStart(2, "0")}.png`));
      }
    }
    await s._send("Input.dispatchMouseEvent", { type: "mouseReleased", x: cx + dx, y: cy, button: "left", buttons: 0 });
    await sleep(1200);

    const goc = -(2 * Math.PI * dx) / ch;
    const raw2 = await s.eval(MAU_THIET_DIEN(canh, FOV, goc));
    const o2 = typeof raw2 === "string" && raw2.startsWith("{") ? JSON.parse(raw2) : { loi: String(raw2) };
    let doiPhanLoai = -1, khopSauXoay = false;
    if (!o2.loi) {
      const shot2 = await s._send("Page.captureScreenshot", { format: "png" });
      const doc2 = JSON.parse(await s.eval(DOC_DIEM(shot2.result.data, o2.mau)));
      // Cổng tự-kiểm: nếu camera dự đoán SAI thì điểm mẫu rơi ra ngoài đường và
      // đoạn "thấy" sẽ không còn liền. Không có cổng này thì mọi kết luận sau
      // đó dựa trên một camera bịa.
      const A2 = laNetDut(doc2.filter((m) => m.thay).map((m) => m.net));
      khopSauXoay = A2.tiLe >= 0.9;
      ghi(id, "camera sau xoay TÍNH ĐÚNG (đoạn thấy vẫn liền)", "≥ 90%",
        `${(A2.tiLe * 100).toFixed(0)}%`, khopSauXoay);
      if (khopSauXoay) {
        const B2 = laNetDut(doc2.filter((m) => !m.thay).map((m) => m.net));
        ghi(id, "sau xoay: đoạn khuất VẪN đứt", "đổi ≥ 2 lần",
          `${(B2.tiLe * 100).toFixed(0)}% · ${B2.doi} lần đổi`, B2.dut);
        doiPhanLoai = o.mau.filter((m, i) => m.thay !== o2.mau[i]?.thay).length;
        ghi(id, "xoay camera ⇒ PHÂN LOẠI thấy/khuất đổi", "≥ 4 điểm mẫu đổi vai",
          `${doiPhanLoai}/${o.mau.length} điểm đổi vai`, doiPhanLoai >= 4);
      }
      await s.screenshot(join(ANH, `${id}-sau-xoay.png`));
    }
    bang.push({
      case_id: id, camera: o.camera, canvas: o.canvas,
      so_mau: o.mau.length, oracle_thay: thay, oracle_khuat: khuat,
      net_doan_thay: A, net_doan_khuat: B,
      camera_sau_xoay_khop: khopSauXoay, diem_doi_vai_sau_xoay: doiPhanLoai,
    });
  }

  // Hồi quy: hai ca đa diện vẫn dựng và vẫn giữ đáp số.
  for (const f of ca.filter((x) => ["p1_chop_thiet_dien_khoang_cach",
    "p2_chop_day_ngu_giac_lom"].includes(x.case_id))) {
    phucVu = f;
    await s.resetBetweenScenarios(); await sleep(250);
    if (await guiDe(s, f.problem_text) !== "active") {
      ghi(f.case_id, "hồi quy: nạp được", "active", "hỏng", false); continue;
    }
    const canh = f.envelope.scene3d;
    for (let k = 1; k < canh.events.length; k++) { await s.clickText("Bước sau"); await sleep(70); }
    await sleep(400);
    const soDo = JSON.parse(await s.eval(
      `(()=>JSON.stringify([...document.querySelectorAll('.geo3d-readout-gt')].map(e=>e.textContent)))()`));
    ghi(f.case_id, "hồi quy: đáp số không đổi", f.expected_exact_display.join(" · "),
      soDo.join(" · "),
      JSON.stringify([...soDo].sort()) === JSON.stringify([...f.expected_exact_display].sort()));
    await s.screenshot(join(ANH, `${f.case_id}-mac-dinh.png`));
  }

  const loi = s.consoleEvents;
  await s.close();
  const dat = rows.filter((r) => r.pass).length;
  const anh = readdirSync(ANH).filter((x) => x.endsWith(".png"));
  writeFileSync(join(THU_MUC, "HIDDEN_LINE_MATRIX.json"), JSON.stringify({
    ...provenance("certify-scene3d-hidden-lines", { cases: bang.length }),
    khai: "Phân loại thấy/khuất do ORACLE PHÁP TUYẾN quyết (khối lồi: thấy ⟺ "
        + "n̂·(mắt−Q) > 0), không đọc cờ nào của renderer. Dạng nét đo trên "
        + "điểm ảnh tại đúng vị trí oracle chỉ ra. 0 lượt gọi model.",
    viewport: `${VIEWPORT.viewport}x${VIEWPORT.height}`, fov: FOV,
    checks_pass: dat, checks_total: rows.length,
    UNCAUGHT_FRONTEND_EXCEPTIONS: loi.filter((e) => e.loai === "exception").length,
    screenshots: anh.map((x) => ({
      ten: x,
      sha256: createHash("sha256").update(readFileSync(join(ANH, x))).digest("hex"),
    })),
    cases: bang, rows,
  }, null, 1) + "\n", "utf-8");
  console.log(`\n  ${dat}/${rows.length} phép kiểm · ${anh.length} ảnh`);
  return dat === rows.length ? 0 : 1;
}

process.exit(await main());
