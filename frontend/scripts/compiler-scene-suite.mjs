import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import {
  mkdirSync, readFileSync, statSync, writeFileSync,
} from "node:fs";
import { dirname, join, relative, resolve } from "node:path";

import { BrowserSession } from "./browser-runner.mjs";
import { kiemDistMoi, phucVu } from "./scene3d-orbit-gate.mjs";
// Token chấm đỉnh của CHÍNH sản phẩm (module không import gì ⇒ Node nạp thẳng).
import { DAU_DINH_PX, KHUNG_HEP_PX } from "../src/simulations/domains/geometry/pick-target.ts";
import {
  DAI_SAC_VAI_TRO,
  LOP_DONG_THEO_TANG,
  aliasTreeRowCheck,
  assessCausalCanvasHues,
  assessCssReadiness,
  assessFormation,
  assessGeometrySteps,
  assessStructuredReferences,
  isHiddenAlias,
  assessFormationSnapshots,
  assessImmutableWindow,
  cameraSauCuChi,
  compareClosures,
  danhGiaAnhXoayThuc,
  detectRawTokenLeakage,
  doCoDauDinh,
  evaluateEvidenceGates,
  eventDeclaredClosure,
  expectedCausalTiers,
  expectedGeometryTimeline,
  expectedSolutionRows,
  expectedVisibleIds,
  orbitPlanThuc,
  pollUntil,
  settleCamera,
  sha256File,
  sha256GitBlob,
  solidTopology,
  validateFormulaReferences,
  validateSuiteManifest,
  phanLoaiSac,
  renderedSets,
  sortedUnique,
} from "./compiler-scene-replay-lib.mjs";

const REPO_ROOT = resolve(import.meta.dirname, "..", "..");
const FRONTEND = join(REPO_ROOT, "frontend");
const DIST = join(FRONTEND, "dist");
const SUBMIT = '[aria-label="Phân tích đề bằng AI"]';

export const jsonEval = async (session, expression) => {
  const value = await session.eval(`JSON.stringify(${expression})`);
  if (typeof value !== "string") throw new Error(`EXPECTED_JSON:${String(value)}`);
  return JSON.parse(value);
};

const sha256 = (value) => createHash("sha256").update(value).digest("hex");

function assertion(pass, details = undefined) {
  return { pass: Boolean(pass), ...(details === undefined ? {} : { details }) };
}

const VISIBILITY_STATE = "visible_edge_ids:window.__geo3d_visible_edge_ids||[],"
  + "hidden_edge_ids:window.__geo3d_hidden_edge_ids||[],"
  + "mixed_edge_ids:window.__geo3d_mixed_edge_ids||[],"
  + "edge_spans:window.__geo3d_edge_spans||[],";
const EDGE_STATE = VISIBILITY_STATE
  + "duplicate_visual_owner_ids:window.__geo3d_duplicate_visual_owner_ids||[],"
  + "highlighted_render_owner_ids:window.__geo3d_highlighted_render_owner_ids||[],"
  + "selected_id:window.__geo3d_selected_id||null,"
  + "dash_signature:window.__geo3d_edge_dash_signature||{},";

/** Settle the camera; a camera that never settles is recorded as a failed
 *  `camera_settled_<state>` assertion (with diagnostic) instead of aborting. */
async function settleOrRecord(session, result, state) {
  try {
    const settled = await settleCamera(() => jsonEval(session,
      "({snapshot:window.__geo3d_camera_snapshot||null,"
      + "frame_count:(window.__geo3d_occlusion_performance||{}).frame_count||0})"));
    result.camera_settle = { ...result.camera_settle,
      [state]: { samples: settled.settle_samples, max_motion: settled.settle_max_motion } };
    return settled;
  } catch (error) {
    if (!String(error.message).startsWith("SETTLING_TIMEOUT")) throw error;
    result.assertions[`camera_settled_${state}`] = assertion(false, error.diagnostic);
    return null;
  }
}

async function setTextarea(session, text) {
  return session.eval(`(()=>{const t=document.querySelector('textarea');if(!t)return false;`
    + `const set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;`
    + `set.call(t,${JSON.stringify(text)});t.dispatchEvent(new Event('input',{bubbles:true}));return true})()`);
}

async function rectFor(session, expression) {
  return jsonEval(session, `(()=>{const e=${expression};if(!e)return null;const r=e.getBoundingClientRect();`
    + `return{x:r.left,y:r.top,w:r.width,h:r.height}})()`);
}

/** Lớp phủ trên sân khấu (nút nổi, ô soi) — hộp px CSS TƯƠNG ĐỐI canvas, cho
 *  cổng ảnh xoay biết đỉnh nào bị che (w11). W12: dải số đo trên khung đã gỡ. */
export async function overlayRects(session) {
  return jsonEval(session, `(()=>{const c=document.querySelector('.geo3d-canvas canvas');if(!c)return[];`
    + `const k=c.getBoundingClientRect();return['.geo3d-noi','.geo3d-soi']`
    + `.map(s=>document.querySelector(s)).filter(Boolean).map(e=>e.getBoundingClientRect())`
    + `.filter(r=>r.width>0&&r.height>0).map(r=>({x:r.left-k.left-4,y:r.top-k.top-4,w:r.width+8,h:r.height+8}))})()`);
}

/** Cỡ chấm đỉnh ĐO qua ma trận camera, so với token của sản phẩm (w11, W10-H5). */
export async function vertexMarkerCheck(session) {
  const { markers, camera } = await jsonEval(session,
    "({markers:window.__geo3d_vertex_markers||[],camera:window.__geo3d_camera_snapshot||null})");
  const doDuoc = camera ? doCoDauDinh(camera, markers) : [];
  const kyVong = (state) => (state === "chon" ? DAU_DINH_PX.chon
    : camera.viewport_width < KHUNG_HEP_PX ? DAU_DINH_PX.hep : DAU_DINH_PX.thuong);
  const lech = doDuoc.filter((m) => Math.abs(m.diameter_px - kyVong(m.state)) > 0.25);
  return assertion(doDuoc.length > 0 && lech.length === 0,
    { token: DAU_DINH_PX, markers: doDuoc, mismatched: lech });
}

export async function trustedClick(session, expression) {
  // Như người dùng: cuộn tới phần tử trước khi bấm. Không cuộn thì phần tử
  // nằm dưới khung nhìn (ô soi mobile, w10) nhận một cú bấm ở toạ độ ngoài màn hình.
  // Kiểm phần tử tại điểm bấm ĐÚNG là đích — không bấm mù vào thứ đang che.
  // Chỉ cuộn khi đích bị che/ngoài khung nhìn, và cuộn vào GIỮA: `nearest` đặt
  // nó sát mép trên, DƯỚI thanh điều hướng dính — cú bấm từng mở lớp phủ đăng
  // nhập (w10, mobile). Không cuộn khi đích đã thấy rõ: cuộn làm khung canvas
  // dời chỗ và phép so canvas trước/sau causal mất nghĩa (lần đo w10 thứ 6).
  const trenCung = async () => {
    const rect = await rectFor(session, expression);
    if (!rect || rect.w <= 0 || rect.h <= 0) return null;
    const x = rect.x + rect.w / 2;
    const y = rect.y + rect.h / 2;
    const ok = await session.eval(`(()=>{const e=${expression};const h=document.elementFromPoint(${x},${y});`
      + `return !!(e&&h&&(e===h||e.contains(h)))})()`);
    return ok ? { x, y } : null;
  };
  let diem = await trenCung();
  if (!diem) {
    await session.eval(`(()=>{const e=${expression};if(e)e.scrollIntoView({block:"center"});return true})()`);
    diem = await trenCung();
  }
  if (!diem) return false;
  await session.mouse(diem.x, diem.y);
  return true;
}

async function clickAria(session, label) {
  return trustedClick(session,
    `document.querySelector('[aria-label=${JSON.stringify(label)}]')`);
}

async function clickText(session, text) {
  return trustedClick(session,
    `[...document.querySelectorAll('button')].find(e=>(e.textContent||'').includes(${JSON.stringify(text)}))`);
}

export async function currentStep(session) {
  const text = await session.eval(`document.querySelector('.geo3d-buoc-so')?.textContent||''`);
  const match = /Bước\s+(\d+)\/(\d+)/.exec(String(text));
  return match ? { index: Number(match[1]) - 1, count: Number(match[2]), text } : null;
}

async function moveStep(session, direction) {
  const before = await currentStep(session);
  const label = direction > 0 ? "Bước sau" : "Bước trước";
  const state = await jsonEval(session, `(()=>{const b=document.querySelector('[aria-label=${JSON.stringify(label)}]');`
    + `return b?{exists:true,disabled:b.disabled}:{exists:false,disabled:true}})()`);
  if (!state.exists || state.disabled) return false;
  if (!await clickAria(session, label)) return false;
  await pollUntil(() => currentStep(session),
    (next) => next && before && next.index === before.index + direction,
    { timeoutMs: 5_000 });
  return true;
}

async function goToEnd(session) {
  while (await moveStep(session, 1)) { /* semantic state transition */ }
  return currentStep(session);
}

async function goToStart(session) {
  while (await moveStep(session, -1)) { /* semantic state transition */ }
  return currentStep(session);
}

async function projectedLabels(session) {
  return jsonEval(session, `(()=>Object.fromEntries([...document.querySelectorAll('.geo3d-label[data-id]')].map(e=>{`
    + `const r=e.getBoundingClientRect();return[e.dataset.id,{x:Math.round(r.left+r.width/2),`
    + `y:Math.round(r.top+r.height/2),text:(e.textContent||'').trim()}]})))()`);
}

function projectionComparison(before, after) {
  const common = Object.keys(before).filter((id) => after[id]);
  const deltas = Object.fromEntries(common.map((id) => [id, Math.hypot(
    after[id].x - before[id].x, after[id].y - before[id].y,
  )]));
  const moved = common.filter((id) => deltas[id] >= 3);
  const distinctBefore = new Set(common.map((id) => `${before[id].x}:${before[id].y}`)).size;
  const distinctAfter = new Set(common.map((id) => `${after[id].x}:${after[id].y}`)).size;
  return {
    common_ids: common,
    deltas,
    moved_ids: moved,
    distinct_before: distinctBefore,
    distinct_after: distinctAfter,
    pass: common.length >= 3 && moved.length >= 2
      && distinctBefore === common.length && distinctAfter === common.length,
  };
}

export async function trustedOrbit(session, {
  dx = 190, dy = 48, startX = 0.52, startY = 0.48,
} = {}) {
  const canvas = `document.querySelector('.geo3d-canvas canvas')`;
  // Điểm bắt đầu kéo phải nằm TRÊN canvas, không trên lớp phủ nào (w10); chỉ
  // cuộn khi nó chưa như thế.
  const diemBatDau = async () => {
    const r = await rectFor(session, canvas);
    if (!r) throw new Error("NO_CANVAS_FOR_ORBIT");
    const p = { x: r.x + r.w * startX, y: r.y + r.h * startY };
    return await session.eval(`document.elementFromPoint(${p.x},${p.y})===${canvas}`) ? p : null;
  };
  let p = await diemBatDau();
  if (!p) {
    await session.eval(`(()=>{const e=${canvas};if(e)e.scrollIntoView({block:"center"});return true})()`);
    p = await diemBatDau();
  }
  if (!p) throw new Error("ORBIT_START_NOT_ON_CANVAS");
  const { x, y } = p;
  await session._send("Input.dispatchMouseEvent", {
    type: "mouseMoved", x, y, button: "left", buttons: 0,
  });
  await session._send("Input.dispatchMouseEvent", {
    type: "mousePressed", x, y, button: "left", buttons: 1, clickCount: 1,
  });
  for (let step = 1; step <= 16; step += 1) {
    await session._send("Input.dispatchMouseEvent", {
      type: "mouseMoved",
      x: x + (dx * step) / 16,
      y: y + (dy * step) / 16,
      button: "left", buttons: 1,
    });
  }
  await session._send("Input.dispatchMouseEvent", {
    type: "mouseReleased", x: x + dx, y: y + dy,
    button: "left", buttons: 0, clickCount: 1,
  });
}

/** Lùi camera `nac` nấc con lăn tại giữa canvas (OrbitControls: mỗi nấc 100
 *  ⇒ khoảng cách ×1/0.95). Là một phần của cử chỉ HOẠCH ĐỊNH cho ảnh xoay (w11):
 *  khung mặc định lấp 68% khung, nên xoay 60–90° kéo đỉnh đáy xuống dưới mép. */
export async function trustedZoomOut(session, nac) {
  const r = await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`);
  if (!r) throw new Error("NO_CANVAS_FOR_ZOOM");
  const [x, y] = [r.x + r.w * 0.52, r.y + r.h * 0.48];
  if (!await session.eval(`document.elementFromPoint(${x},${y})===document.querySelector('.geo3d-canvas canvas')`)) {
    throw new Error("ZOOM_POINT_NOT_ON_CANVAS");
  }
  // Giả lập mobile (DPR 2) chia `deltaY` của CDP cho DPR trước khi tới trang
  // (đo được: 100 ⇒ 50, nên 3 nấc chỉ lùi (1/0.95)^1,5). Nhân lại để trang nhận
  // đúng 100 mỗi nấc — mô hình `cameraSauCuChi` giả định đúng điều đó.
  const dpr = Number(await session.eval("window.devicePixelRatio")) || 1;
  for (let i = 0; i < nac; i += 1) {
    await session._send("Input.dispatchMouseEvent", { type: "mouseWheel", x, y, deltaX: 0, deltaY: 100 * dpr });
  }
}

export async function capture(session, path) {
  const absolute = resolve(path);
  mkdirSync(dirname(absolute), { recursive: true });
  const result = await session.screenshot(absolute);
  if (result !== "ok" || statSync(absolute).size < 4_096) {
    throw new Error(`INVALID_SCREENSHOT:${absolute}`);
  }
  return {
    path: relative(REPO_ROOT, absolute).replaceAll("\\", "/"),
    bytes: statSync(absolute).size,
    sha256: sha256File(absolute),
  };
}

/** Hộp cắt ảnh theo toạ độ TÀI LIỆU: `clip` của `Page.captureScreenshot` tính
 *  từ gốc trang, còn `getBoundingClientRect` tính từ khung nhìn — trang đã cuộn
 *  (W12: bảng lời giải dưới thanh bước) thì hai hệ lệch nhau đúng `scrollY`. */
async function pageClip(session, expression) {
  return jsonEval(session, `(()=>{const e=${expression};if(!e)return null;const r=e.getBoundingClientRect();`
    + `return{x:r.left+window.scrollX,y:r.top+window.scrollY,width:r.width,height:r.height,scale:1}})()`);
}

async function canvasHash(session) {
  const clip = await pageClip(session, `document.querySelector('.geo3d-canvas canvas')`);
  if (!clip) throw new Error("NO_CANVAS_CLIP");
  const response = await session._send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
    clip,
  });
  const data = Buffer.from(response.result.data, "base64");
  return { sha256: sha256(data), bytes: data.length };
}

async function canvasFrame(session) {
  const clip = await pageClip(session, `document.querySelector('.geo3d-canvas canvas')`);
  if (!clip) throw new Error("NO_CANVAS_CLIP");
  const response = await session._send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
    clip,
  });
  const encoded = response.result.data;
  const data = Buffer.from(encoded, "base64");
  return { sha256: sha256(data), bytes: data.length, encoded };
}

async function pixelDelta(session, before, after) {
  return session.eval(`(async()=>{const load=src=>new Promise((ok,bad)=>{`
    + `const i=new Image();i.onload=()=>ok(i);i.onerror=bad;i.src=src});`
    + `const a=await load(${JSON.stringify(`data:image/png;base64,${before.encoded}`)});`
    + `const b=await load(${JSON.stringify(`data:image/png;base64,${after.encoded}`)});`
    + `if(a.width!==b.width||a.height!==b.height)return{pass:false,reason:'SIZE_MISMATCH'};`
    + `const c=document.createElement('canvas');c.width=a.width;c.height=a.height;const x=c.getContext('2d');`
    + `x.drawImage(a,0,0);const pa=x.getImageData(0,0,c.width,c.height).data;`
    + `x.clearRect(0,0,c.width,c.height);x.drawImage(b,0,0);const pb=x.getImageData(0,0,c.width,c.height).data;`
    + `let changed=0,minX=c.width,minY=c.height,maxX=-1,maxY=-1;for(let i=0;i<pa.length;i+=4){`
    + `const d=Math.abs(pa[i]-pb[i])+Math.abs(pa[i+1]-pb[i+1])+Math.abs(pa[i+2]-pb[i+2]);`
    + `if(d<24)continue;changed++;const p=i/4,xx=p%c.width,yy=Math.floor(p/c.width);`
    + `minX=Math.min(minX,xx);minY=Math.min(minY,yy);maxX=Math.max(maxX,xx);maxY=Math.max(maxY,yy)}`
    + `const total=c.width*c.height,ratio=changed/total;return{changed_pixels:changed,total_pixels:total,`
    + `changed_ratio:ratio,bounds:changed?{x:minX,y:minY,width:maxX-minX+1,height:maxY-minY+1}:null,`
    + `pass:changed>0&&ratio<0.75}})()`);
}

/** W12: đếm điểm ảnh theo dải sắc vai trò trên ảnh khung — chính hàm thuần của
 *  thư viện (`phanLoaiSac`) được tiêm vào trang, nên node test đo đúng mã chạy.
 *  Lớp phủ HTML (nút nổi, ô soi, nhãn đỉnh) bị bỏ ra: chữ của chúng ở DPR 1 khử
 *  răng cưa theo điểm ảnh con, viền chữ ra cam/xanh bão hoà — đo được ~700 điểm
 *  ảnh cam trên ô soi của MỌI họ (e115eede). Cổng đo thứ WebGL vẽ, không đo chữ. */
async function roleHueCensus(session, frame) {
  return session.eval(`(async()=>{const phan=${phanLoaiSac.toString()};`
    + `const dai=${JSON.stringify(DAI_SAC_VAI_TRO)};`
    + `const i=await new Promise((ok,bad)=>{const x=new Image();x.onload=()=>ok(x);x.onerror=bad;`
    + `x.src=${JSON.stringify(`data:image/png;base64,${frame.encoded}`)}});`
    + `const k=document.querySelector('.geo3d-canvas canvas').getBoundingClientRect();`
    + `const che=[...document.querySelectorAll('.geo3d-noi,.geo3d-soi,.geo3d-label')]`
    + `.map(e=>e.getBoundingClientRect()).filter(r=>r.width>0&&r.height>0)`
    + `.map(r=>[r.left-k.left-2,r.top-k.top-2,r.right-k.left+2,r.bottom-k.top+2]);`
    + `const c=document.createElement('canvas');c.width=i.width;c.height=i.height;`
    + `const x=c.getContext('2d');x.drawImage(i,0,0);const p=x.getImageData(0,0,c.width,c.height).data;`
    + `const sx=i.width/k.width,sy=i.height/k.height;let total=0,cam=0,xanh=0;`
    + `for(let y=0;y<i.height;y++)for(let q=0;q<i.width;q++){const cx=q/sx,cy=y/sy;`
    + `if(che.some(([a,b,e,f])=>cx>=a&&cx<e&&cy>=b&&cy<f))continue;total++;const o=(y*i.width+q)*4;`
    + `const v=phan(p[o],p[o+1],p[o+2],dai);if(v==='cam')cam++;else if(v==='xanh')xanh++}`
    + `return{total,cam,xanh,masked_overlays:che.length}})()`);
}

async function cssReadiness(session, viewport) {
  const measured = await jsonEval(session, `(()=>{const pick=s=>document.querySelector(s);const style=e=>{const s=getComputedStyle(e);`
    + `const r=e.getBoundingClientRect();return{display:s.display,position:s.position,fontFamily:s.fontFamily,`
    + `fontSize:s.fontSize,color:s.color,width:r.width,height:r.height,left:r.left,right:r.right}};`
    + `const baselineTag=(tag)=>{const e=document.createElement(tag);e.style.cssText='all:initial;position:static;';`
    + `e.textContent='sentinel';document.body.appendChild(e);const x=style(e);e.remove();return x};`
    + `const scene=pick('.geo3d'),box=pick('.geo3d-canvas'),canvas=pick('.geo3d-canvas canvas'),`
    + `controls=pick('.geo3d-controls'),controlButton=pick('.geo3d-controls button'),`
    + `controlText=pick('.geo3d-scrub-label'),`
    + `solution=pick('.geo3d-loi-giai'),solutionTitle=pick('.geo3d-lg-ten-muc');`
    + `const actual={scene:scene&&style(scene),box:box&&style(box),canvas:canvas&&style(canvas),`
    + `controls:controls&&style(controls),controlButton:controlButton&&style(controlButton),`
    + `controlText:controlText&&style(controlText),`
    + `solution:solution&&style(solution),solutionTitle:solutionTitle&&style(solutionTitle)};`
    + `const baseline={div:baselineTag('div'),button:baselineTag('button'),`
    + `ul:baselineTag('ul'),span:baselineTag('span')};`
    + `let sheets={count:document.styleSheets.length,readableRules:0,unreadable:0};`
    + `for(const sheet of document.styleSheets){try{sheets.readableRules+=(sheet.cssRules||[]).length}catch(e){sheets.unreadable++}}`
    + `return{actual,baseline,stylesheets_auxiliary:sheets,scrollWidth:document.documentElement.scrollWidth,`
    + `viewportWidth:window.innerWidth}})()`);
  const assessed = assessCssReadiness(
    measured.actual, measured.baseline, measured.scrollWidth, Number(viewport.width),
  );
  return { ...measured, ...assessed };
}

/** BẢNG LỜI GIẢI (W12): các dòng theo mục học sinh thấy, lớp vai trò, màu vạch
 *  trái; chú giải; hộp của bảng so với canvas; mục thân đang gập hay mở. */
export async function solutionState(session) {
  return jsonEval(session, `(()=>{const muc=e=>(e.closest('.geo3d-lg-muc')?.querySelector('.geo3d-lg-ten-muc')`
    + `?.textContent||'').trim();const hop=e=>{if(!e)return null;const r=e.getBoundingClientRect();`
    + `return{x:r.left,y:r.top,w:r.width,h:r.height}};`
    + `const rows=[...document.querySelectorAll('.geo3d-lg-dong[data-solution-id]')].map(e=>({`
    + `id:e.dataset.solutionId,sec:muc(e),classes:[...e.classList].filter(c=>c.startsWith('la-')),`
    + `text:(e.textContent||'').replace(/\\s+/g,' ').trim(),border:getComputedStyle(e).borderLeftColor}));`
    + `const legend=[...document.querySelectorAll('.geo3d-chu-giai-muc')].map(e=>({`
    + `text:(e.textContent||'').trim(),classes:[...e.classList].filter(c=>c.startsWith('la-')),`
    + `swatch:getComputedStyle(e,'::before').backgroundColor}));`
    + `const than=document.querySelector('.geo3d-lg-than');`
    + `return{present:!!document.querySelector('.geo3d-loi-giai'),rows,legend,`
    + `panel:hop(document.querySelector('.geo3d-loi-giai')),canvas:hop(document.querySelector('.geo3d-canvas canvas')),`
    + `body_collapsed:!!than&&getComputedStyle(than).display==='none',`
    + `result_text:(document.querySelector('.geo3d-lg-ket-qua')?.textContent||'').replace(/\\s+/g,' ').trim()}})()`);
}

const rowsBySection = (state) => ({
  givens: state.rows.filter((row) => row.sec === "Dữ kiện").map((row) => row.id),
  steps: state.rows.filter((row) => row.sec === "Các bước tính").map((row) => row.id),
  results: state.rows.filter((row) => row.sec === "Kết quả").map((row) => row.id),
});

const overlaps = (a, b) => Boolean(a && b) && a.x < b.x + b.w && b.x < a.x + a.w
  && a.y < b.y + b.h && b.y < a.y + a.h;

/** Ảnh MỘT phần tử (cuộn vào khung trước) — bảng lời giải ở các trạng thái. */
async function captureElement(session, selector, path) {
  await session.eval(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});`
    + `if(e)e.scrollIntoView({block:"center"});return true})()`);
  await new Promise((done) => setTimeout(done, 200));
  const clip = await pageClip(session, `document.querySelector(${JSON.stringify(selector)})`);
  if (!clip || clip.width <= 0 || clip.height <= 0) throw new Error(`NO_ELEMENT_CLIP:${selector}`);
  const response = await session._send("Page.captureScreenshot", {
    format: "png", captureBeyondViewport: false, clip,
  });
  const absolute = resolve(path);
  mkdirSync(dirname(absolute), { recursive: true });
  writeFileSync(absolute, Buffer.from(response.result.data, "base64"));
  return {
    path: relative(REPO_ROOT, absolute).replaceAll("\\", "/"),
    bytes: statSync(absolute).size,
    sha256: sha256File(absolute),
  };
}

/** Màu vai trò TÍNH TOÁN của bảng (vạch trái, ô chú giải) khớp token W12 —
 *  đọc giá trị token từ `tokens.css`, không chép số. */
function roleTokens() {
  const css = readFileSync(join(FRONTEND, "src", "styles", "tokens.css"), "utf-8");
  const hex = (name) => new RegExp(`${name}\\s*:\\s*#([0-9a-fA-F]{6})`).exec(css)?.[1];
  const rgb = (h) => h ? `rgb(${parseInt(h.slice(0, 2), 16)}, ${parseInt(h.slice(2, 4), 16)}, ${parseInt(h.slice(4, 6), 16)})` : null;
  return {
    "la-chon": rgb(hex("--geo3d-vai-tro-dich")),
    "la-so-lieu": rgb(hex("--geo3d-vai-tro-du-kien-so")),
    "la-trung-gian": rgb(hex("--geo3d-vai-tro-trung-gian")),
    "la-boi-canh": rgb(hex("--geo3d-vai-tro-boi-canh")),
  };
}

export function assessRoleColors(state) {
  const tokens = roleTokens();
  const rows = state.rows.filter((row) => tokens[row.classes[0]])
    .map((row) => ({ id: row.id, role: row.classes[0], border: row.border, want: tokens[row.classes[0]],
      pass: row.border === tokens[row.classes[0]] }));
  const legend = state.legend.filter((item) => tokens[item.classes[0]])
    .map((item) => ({ text: item.text, role: item.classes[0], swatch: item.swatch,
      want: tokens[item.classes[0]], pass: item.swatch === tokens[item.classes[0]] }));
  const distinct = new Set(Object.values(tokens)).size === Object.keys(tokens).length;
  return { tokens, rows, legend, distinct_tokens: distinct,
    pass: distinct && rows.length > 0 && rows.every((r) => r.pass) && legend.every((l) => l.pass) };
}

export async function openFixture({ port, viewport, fixture }) {
  const envelope = fixture.envelope;
  const session = new BrowserSession({
    viewport: viewport.width,
    height: viewport.height,
    webgl: true,
    url: `http://127.0.0.1:${port}`,
    napModuleDev: false,
  });
  await session.open();
  if (viewport.width < 600) {
    await session._send("Emulation.setDeviceMetricsOverride", {
      width: viewport.width, height: viewport.height, deviceScaleFactor: 2, mobile: true,
    });
  }
  let analyzeCalls = 0;
  const apiEvents = [];
  await session.interceptJson("*/api/*", async ({ url }) => {
    const pathname = new URL(url).pathname;
    if (pathname === "/api/analyze") {
      analyzeCalls += 1;
      apiEvents.push({ pathname, status: 200 });
      return { status: 200, body: envelope };
    }
    if (pathname === "/api/health") {
      apiEvents.push({ pathname, status: 200 });
      return { status: 200, body: { ok: true, hasKey: true, cachedProblems: 0 } };
    }
    if (pathname === "/api/auth/me") {
      apiEvents.push({ pathname, status: 200 });
      return { status: 200, body: { user: null } };
    }
    apiEvents.push({ pathname, status: 404 });
    return { status: 404, body: { error: "outside frozen replay" } };
  });
  session.consoleEvents = [];
  await session._send("Page.reload", {});
  await pollUntil(() => session.eval(`!!document.querySelector('textarea')`), Boolean);
  if (!await setTextarea(session, fixture.problem_text)) throw new Error("TEXTAREA_NOT_READY");
  await pollUntil(() => session.eval(`(()=>{const b=document.querySelector(${JSON.stringify(SUBMIT)});`
    + `return !!b&&!b.disabled})()`), Boolean);
  if (!await trustedClick(session, `document.querySelector(${JSON.stringify(SUBMIT)})`)) {
    throw new Error("SUBMIT_NOT_CLICKED");
  }
  return { session, analyzeCalls: () => analyzeCalls, apiEvents: () => [...apiEvents] };
}

async function observeTree(session, scene, expectedIds) {
  await clickText(session, "Thành phần");
  await pollUntil(() => session.eval(`!!document.querySelector('.geo3d-tree')`), Boolean,
    { timeoutMs: 5_000 });
  const rows = await jsonEval(session, `(()=>[...document.querySelectorAll('.geo3d-tree-item')].map(e=>({`
    + `text:(e.querySelector('.geo3d-tree-nhan')?.textContent||'').trim(),disabled:e.disabled})))()`);
  const expected = new Set(expectedIds);
  const checks = [];
  for (const object of scene.objects ?? []) {
    const matches = rows.filter((row) => row.text === object.label);
    // w10: bí danh đáp số KHÔNG có dòng riêng trong cây (`aliasTreeRowCheck`).
    if (isHiddenAlias(object)) {
      checks.push(aliasTreeRowCheck(scene, object, rows));
      continue;
    }
    const observedPresent = matches.some((row) => !row.disabled);
    checks.push({
      id: object.id,
      label: object.label,
      expected_present: expected.has(object.id),
      matches: matches.length,
      observed_present: matches.length > 0 ? observedPresent : null,
      pass: matches.length > 0 && observedPresent === expected.has(object.id),
    });
  }
  await clickAria(session, "Đóng");
  await pollUntil(() => session.eval(`!document.querySelector('.geo3d-tree')`), Boolean,
    { timeoutMs: 5_000 });
  return { objects: checks, pass: checks.every((item) => item.pass) };
}

/** Vật THẬT SỰ được dựng lên khung (renderer tự báo). Giữ đuôi `#…` — nó là
 *  tiến độ thiết diện (số đỉnh, khép, tô): mỗi cạnh thiết diện là một bước. */
async function renderedIds(session) {
  return jsonEval(session, "(window.__geo3d_rendered_object_ids||[]).map(String).sort()");
}

async function focusLabel(session) {
  return session.eval(`(()=>{const d=[...document.querySelectorAll('.geo3d-focus dt')]`
    + `.find(e=>(e.textContent||'').trim()==='Đang dựng');return (d?.nextElementSibling?.textContent||'').trim()})()`);
}

/** W12: thanh bước đi qua BƯỚC DỰNG. Mỗi bước: khung = snapshot neo của bước
 *  (oracle độc lập), cây thành phần, nhãn điểm, vật dựng lên khung, dòng "Đang
 *  dựng", bảng lời giải; rồi tua ngược so từng bước. W14: cùng các bước ấy chấm
 *  độ phủ vai trò (kỳ vọng registry · khai báo sản phẩm · vật renderer báo) và
 *  mọi tham chiếu có cấu trúc. */
async function formationEvidence(session, scene, outDir, captureMode, scenario) {
  await goToStart(session);
  const timeline = expectedGeometryTimeline(scene);
  const stepTotal = timeline.length;
  const steps = [];
  const observations = { forward: [], backward: [] };
  const representative = Math.floor((stepTotal - 1) / 2);
  for (let index = 0; index < stepTotal; index += 1) {
    const anchor = timeline[index].anchor;
    // Vai trò dựng hình của CẢ nhóm sự kiện (bước neo có thể là một kết luận
    // mang `[]`) — chỉ để chú thích ảnh; phép chấm vai trò dùng vật renderer báo.
    const { start, end } = timeline[index];
    const formationRoles = sortedUnique(Array.from({ length: end - start + 1 },
      (_, d) => scene.formation?.steps?.[start + d]?.formation_roles ?? []).flat());
    const step = await currentStep(session);
    const expectedIds = expectedVisibleIds(scene, anchor);
    const tree = await observeTree(session, scene, expectedIds);
    const labels = await projectedLabels(session);
    const expectedPointIds = expectedIds.filter((id) =>
      scene.objects.some((object) => object.id === id && object.type === "point3")).sort();
    const actualPointIds = Object.keys(labels).sort();
    const solution = rowsBySection(await solutionState(session));
    const expectedSolution = expectedSolutionRows(scene, anchor);
    const shouldCapture = captureMode === "full" || index === representative;
    const image = shouldCapture
      ? await capture(session, join(outDir,
          index === representative && captureMode !== "full"
            ? "formation_current_step.png" : `formation_step_${index}.png`))
      : null;
    const canvas = await canvasHash(session);
    const learnerText = await session.eval(
      `document.querySelector('.geo3d-buoc-loi')?.textContent||''`,
    );
    const observedVisibleIds = tree.objects
      .filter((item) => item.observed_present === true).map((item) => item.id).sort();
    observations.forward.push({ index: anchor, direction: "forward", visible_ids: observedVisibleIds });
    steps.push({
      index,
      anchor,
      indicator: step,
      expected_visible_ids: expectedIds,
      tree,
      expected_point_ids: expectedPointIds,
      observed_point_ids: actualPointIds,
      point_visibility_pass: JSON.stringify(expectedPointIds) === JSON.stringify(actualPointIds),
      rendered: await renderedIds(session),
      focus_label: await focusLabel(session),
      solution,
      expected_solution: expectedSolution,
      solution_pass: JSON.stringify(solution) === JSON.stringify(expectedSolution),
      screenshot: image,
      canvas,
      learner_text: learnerText,
      formation_roles: formationRoles,
    });
    if (index < stepTotal - 1 && !await moveStep(session, 1)) {
      throw new Error(`FORMATION_STOPPED_AT:${index}`);
    }
  }
  // Ở bước cuối, "Bước sau" phải vô hiệu — không có bước tính nào sau nó.
  const endLocked = !await moveStep(session, 1);
  const backwardRendered = [];
  for (let index = stepTotal - 1; index >= 0; index -= 1) {
    const anchor = timeline[index].anchor;
    const tree = await observeTree(session, scene, expectedVisibleIds(scene, anchor));
    observations.backward.push({
      index: anchor,
      direction: "backward",
      visible_ids: tree.objects
        .filter((item) => item.observed_present === true).map((item) => item.id).sort(),
    });
    backwardRendered[index] = await renderedIds(session);
    if (index > 0 && !await moveStep(session, -1)) {
      throw new Error(`FORMATION_BACKWARD_STOPPED_AT:${index}`);
    }
  }
  const trace = assessFormationSnapshots(scene, observations, timeline.map((g) => g.anchor));
  const geometry = assessGeometrySteps(scene, {
    step_count: steps[0]?.indicator?.count ?? null,
    steps: steps.map((s) => ({ index: s.index, rendered: s.rendered, focus_label: s.focus_label,
      solution: s.solution })),
  });
  const forwardBackward = steps.map((s) => ({ index: s.index,
    pass: JSON.stringify(s.rendered) === JSON.stringify(backwardRendered[s.index]) }));
  const structuredReferences = assessStructuredReferences(scene, {
    steps: steps.map((s) => ({ index: s.index, rendered: s.rendered, solution: s.solution })) });
  const roleCoverage = assessFormation(scenario.expected_formation, scene,
    steps.map((s) => ({ index: s.index, renderedSets: renderedSets(scene, s.rendered) })),
    scenario.formation_coverage.enforce, scenario.formation_coverage.measure);
  const canvasHashes = new Set(steps.map((step) => step.canvas.sha256));
  const pass = steps.every((step) => step.indicator?.index === step.index
    && step.indicator?.count === stepTotal
    && step.tree.pass && step.point_visibility_pass && step.solution_pass)
    && canvasHashes.size >= 2 && trace.pass && geometry.pass && endLocked
    && forwardBackward.every((x) => x.pass) && structuredReferences.pass && roleCoverage.pass;
  return { steps, observations, trace, geometry, forward_backward: forwardBackward,
    structured_references: structuredReferences, role_coverage: roleCoverage,
    end_locked: endLocked, distinct_canvas_frames: canvasHashes.size, pass };
}

async function runPositive({ port, viewport, fixture, scenario, outDir }) {
  const scene = fixture.envelope.scene3d;
  const { session, analyzeCalls, apiEvents } = await openFixture({ port, viewport, fixture });
  const result = { viewport, assertions: {}, screenshots: {}, capture_order: [] };
  try {
    await pollUntil(() => session.eval(`!!document.querySelector('.geo3d-canvas canvas')`), Boolean);
    await goToEnd(session);
    // W12: đáp số ở mục Kết quả của bảng lời giải (dải số trên khung đã gỡ).
    await pollUntil(() => session.eval(`document.querySelector('.geo3d-lg-ket-qua')?.textContent||''`),
      (text) => String(text).includes(scenario.expected_answer));

    const topology = solidTopology(scene);
    result.topology = topology;
    result.assertions.topology = assertion(
      Object.entries(scenario.topology).every(([key, value]) => topology[key] === value),
      { expected: scenario.topology, actual: topology },
    );
    if (scenario.section_vertices) {
      const section = scene.objects.find((object) => object.type === "section");
      result.assertions.section_vertices = assertion(
        section?.polygon?.length === scenario.section_vertices,
        { expected: scenario.section_vertices, actual: section?.polygon?.length ?? null },
      );
    }

    const labels = await projectedLabels(session);
    result.labels = labels;
    result.assertions.labels = assertion(
      scenario.expected_labels.every((label) =>
        Object.values(labels).some((point) => point.text === label)),
      { expected: scenario.expected_labels, actual: Object.values(labels).map((point) => point.text) },
    );
    const css = await cssReadiness(session, viewport);
    result.css_readiness = css;
    result.assertions.css_readiness = assertion(css.pass, css.checks);
    result.canvas_box = await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`);

    await pollUntil(
      () => jsonEval(session, `({${EDGE_STATE}})`),
      (edge) => edge.visible_edge_ids.length > 0 && edge.hidden_edge_ids.length > 0,
      { timeoutMs: 8_000 },
    );
    // Auto-fit + damping keep moving the camera after the edge sets first
    // appear; snapshot and sets are read together only once it has settled.
    const neutralSettled = await settleOrRecord(session, result, "neutral_final");
    const { camera: neutralCamera, ...edgeDefault } = await jsonEval(session,
      `({${EDGE_STATE}camera:window.__geo3d_camera_snapshot||null})`);
    result.edge_semantics_neutral_final = edgeDefault;
    result.camera_snapshots = {
      neutral_final: { snapshot: neutralCamera, sha256: sha256(JSON.stringify(neutralCamera)) },
    };
    result.scene3d_envelope_sha256 = sha256(JSON.stringify(scene));
    result.assertions.neutral_has_no_emphasis = assertion(
      edgeDefault.selected_id === null && edgeDefault.highlighted_render_owner_ids.length === 0,
      edgeDefault,
    );
    result.assertions.vertex_marker_px = await vertexMarkerCheck(session);
    const visibleText = await session.eval(`document.body.innerText||''`);
    result.raw_token_leakage = detectRawTokenLeakage(scene, visibleText);
    result.formula_entity_coherence = validateFormulaReferences(scene);
    // W12 — bảng lời giải ở khung cuối: đúng ba mục của oracle, đáp số ĐÚNG MỘT
    // dòng (ở Kết quả), bảng không đè lên canvas, chưa có chú giải (trung tính).
    const solutionNeutral = await solutionState(session);
    const lastAnchor = expectedGeometryTimeline(scene).at(-1).anchor;
    const finalIds = new Set(scene.events
      .filter((event) => event.semantic_kind === "FINAL_RESULT" && event.object)
      .map((event) => event.object));
    const answerRows = solutionNeutral.rows.filter((row) => finalIds.has(row.id)
      || finalIds.has(scene.objects.find((object) => object.id === row.id)?.alias_of));
    result.solution_final = {
      rows: solutionNeutral.rows,
      expected: expectedSolutionRows(scene, lastAnchor),
      observed: rowsBySection(solutionNeutral),
      answer_rows: answerRows.map((row) => ({ id: row.id, sec: row.sec, text: row.text })),
      body_collapsed: solutionNeutral.body_collapsed,
      panel_box: solutionNeutral.panel,
      canvas_box: solutionNeutral.canvas,
      legend: solutionNeutral.legend,
    };
    result.solution_final.in_sync = JSON.stringify(result.solution_final.expected)
      === JSON.stringify(result.solution_final.observed);
    result.solution_final.answer_once = answerRows.length === finalIds.size
      && answerRows.every((row) => row.sec === "Kết quả")
      && solutionNeutral.result_text.includes(scenario.expected_answer);
    result.solution_final.panel_over_canvas = overlaps(solutionNeutral.panel, solutionNeutral.canvas);
    result.assertions.solution_final = assertion(result.solution_final.in_sync
      && result.solution_final.answer_once && !result.solution_final.panel_over_canvas
      && solutionNeutral.legend.length === 0
      && result.solution_final.body_collapsed === (viewport.width < 768), result.solution_final);

    // Default phải được chụp trước causal/orbit/formation.
    result.screenshots.neutral_final = await capture(session, join(outDir, "neutral_final.png"));
    // Hộp canvas NGAY lúc chụp — trang có thể đã cuộn khác lúc ghi `canvas_box`
    // (w10: crop mobile lệch vì hộp ghi ở y = -226).
    result.canvas_boxes = { neutral_final: await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`) };
    result.capture_order.push("neutral_final");
    // Bảng lời giải ở trạng thái mặc định (khổ hẹp: gập; khổ rộng: mở đủ).
    result.screenshots.solution_neutral_final = await captureElement(session, ".geo3d-loi-giai",
      join(outDir, "solution_neutral_final.png"));
    if (viewport.width < 768) {
      await trustedClick(session, "document.querySelector('.geo3d-lg-gap')");
      await pollUntil(() => solutionState(session), (state) => !state.body_collapsed, { timeoutMs: 5_000 });
      result.screenshots.solution_expanded = await captureElement(session, ".geo3d-loi-giai",
        join(outDir, "solution_expanded.png"));
      await trustedClick(session, "document.querySelector('.geo3d-lg-gap')");
      await pollUntil(() => solutionState(session), (state) => state.body_collapsed, { timeoutMs: 5_000 });
    }
    // Chụp phần tử có thể đã cuộn trang: đưa canvas về giữa khung trước khi đo tiếp.
    await session.eval(`(()=>{document.querySelector('.geo3d-canvas canvas')?.scrollIntoView({block:"center"});return true})()`);
    // The window opens only after settling (the capture above may itself
    // have scheduled frames), so settle again right before resetting.
    const windowSettled = neutralSettled
      && await settleOrRecord(session, result, "immutable_window");
    // The published counters only refresh on the next rendered frame: zero them
    // in the same task as the reset, or the poll reads the pre-reset window
    // (seen in w09: frame_count 138 >= 120 before any window frame ran).
    await session.eval(`(()=>{window.__geo3d_reset_occlusion_performance?.();`
      + `window.__geo3d_occlusion_performance={frame_count:0,recompute_count:0}})()`);
    const { perf: immutable, camera: windowEnd } = await pollUntil(
      () => jsonEval(session, `({perf:window.__geo3d_occlusion_performance||{frame_count:0},`
        + `camera:window.__geo3d_camera_snapshot||null})`),
      (value) => value.perf.frame_count >= 120,
      { timeoutMs: 8_000, intervalMs: 20 },
    );
    const timings = [...(immutable.recomputation_times_ms ?? [])].sort((a, b) => a - b);
    const percentile = (p) => timings.length
      ? timings[Math.min(timings.length - 1, Math.floor((timings.length - 1) * p))] : 0;
    result.occlusion_performance = {
      ...immutable,
      median_recomputation_ms: percentile(0.5),
      p95_recomputation_ms: percentile(0.95),
      max_recomputation_ms: timings.at(-1) ?? 0,
      immutable_frame_recomputations: immutable.recompute_count,
    };
    const windowVerdict = assessImmutableWindow({
      settled: windowSettled || null, end: windowEnd, perf: immutable,
    });
    result.occlusion_performance.immutable_window = windowVerdict;
    result.assertions.immutable_120_frames = assertion(windowVerdict.pass, result.occlusion_performance);
    await session.eval(`(()=>{document.querySelector('.geo3d-canvas canvas')?.scrollIntoView({block:"center"});return true})()`);
    await new Promise((done) => setTimeout(done, 200));
    const causalBeforeFrame = await canvasFrame(session);
    const causalBeforeState = await jsonEval(session, `({selected_id:window.__geo3d_selected_id||null,`
      + `highlighted_ids:window.__geo3d_highlighted_ids||[],`
      + `highlighted_render_owner_ids:window.__geo3d_highlighted_render_owner_ids||[]})`);

    // w10: bí danh đáp số (`alias_of`) là MỘT kết luận với nguồn — không có dòng
    // số đo riêng, người học bấm dòng đáp số là chọn NGUỒN. Bao đóng kỳ vọng
    // (manifest độc lập) chỉ bỏ đúng id bí danh; mọi id khác giữ nguyên.
    const declaredTarget = scene.objects.find((object) => object.id === scenario.causal_target_id);
    const causalId = declaredTarget?.alias_of ?? scenario.causal_target_id;
    const expectedClosure = declaredTarget?.alias_of
      ? scenario.oracle_expected_closure.filter((id) => id !== declaredTarget.id)
      : scenario.oracle_expected_closure;
    const target = scene.objects.find((object) => object.id === causalId);
    if (!target) throw new Error(`MISSING_CAUSAL_TARGET:${scenario.causal_target_id}`);
    // W12: dòng của đích nằm ở BẢNG LỜI GIẢI (kết quả luôn hiện, kể cả khổ hẹp).
    const rowButton = `document.querySelector('.geo3d-lg-dong[data-solution-id=${JSON.stringify(causalId)}] .geo3d-lg-nut')`;
    const clicked = await trustedClick(session, rowButton);
    if (!clicked) throw new Error(`CAUSAL_TARGET_NOT_CLICKABLE:${causalId}`);
    await pollUntil(() => session.eval(`window.__geo3d_selected_id||null`),
      (id) => id === causalId, { timeoutMs: 5_000 });
    // w11: chờ bảng TẦNG causal của sản phẩm, không chờ owner cạnh được tô —
    // chọn một con số (V) thì khối chỉ là ngữ cảnh, không cạnh nào đổi màu.
    const causalState = await pollUntil(
      () => jsonEval(session, `({selected_id:window.__geo3d_selected_id||null,`
        + `highlighted_ids:window.__geo3d_highlighted_ids||[],`
        + `highlighted_render_owner_ids:window.__geo3d_highlighted_render_owner_ids||[],`
        + `tiers:window.__geo3d_causal_tiers||null,`
        + `dash_signature:window.__geo3d_edge_dash_signature||{}})`),
      (state) => state.selected_id === causalId && state.tiers?.[causalId] === "dich",
      { timeoutMs: 8_000 },
    );
    const solutionCausal = await solutionState(session);
    const declared = eventDeclaredClosure(scene.events, causalId);
    const causal = compareClosures(expectedClosure, declared, causalState.highlighted_ids);
    causal.declared_target_id = scenario.causal_target_id;
    causal.selected_id = causalState.selected_id;
    // Bấm có thể đã cuộn trang (khổ hẹp): canvas về cùng vị trí như ảnh "trước".
    await session.eval(`(()=>{document.querySelector('.geo3d-canvas canvas')?.scrollIntoView({block:"center"});return true})()`);
    await new Promise((done) => setTimeout(done, 200));
    const causalAfterFrame = await canvasFrame(session);
    const delta = causalBeforeFrame.sha256 === causalAfterFrame.sha256
      ? { changed_pixels: 0, changed_ratio: 0, bounds: null, pass: false }
      : await pixelDelta(session, causalBeforeFrame, causalAfterFrame);
    // Tầng kỳ vọng tính ĐỘC LẬP từ cảnh; mỗi dòng của bảng lời giải mang đúng
    // lớp tầng mình (ngoài chuỗi ⇒ `la-diu`), theo id — không theo chữ.
    const tierExpected = expectedCausalTiers(scene, causalId);
    const readoutTiers = solutionCausal.rows.map((row) => {
      const tier = tierExpected[row.id];
      const want = tier ? LOP_DONG_THEO_TANG[tier] : "la-diu";
      return { id: row.id, sec: row.sec, classes: row.classes, tier: tier ?? null, expected_class: want,
        pass: row.classes.length === 1 && row.classes[0] === want };
    });
    const legendClasses = solutionCausal.legend.map((item) => item.classes[0]).sort();
    const roleColors = assessRoleColors(solutionCausal);
    result.role_colors = roleColors;
    const canvasRoleHues = assessCausalCanvasHues(scene, causalState.tiers,
      await roleHueCensus(session, causalAfterFrame));
    causal.visual = {
      selected_changed: causalBeforeState.selected_id !== causalState.selected_id,
      closure_changed: JSON.stringify(causalBeforeState.highlighted_ids)
        !== JSON.stringify(causalState.highlighted_ids),
      tiers_match: JSON.stringify(causalState.tiers, Object.keys(causalState.tiers ?? {}).sort())
        === JSON.stringify(tierExpected, Object.keys(tierExpected).sort()),
      tiers_expected: tierExpected,
      tiers_observed: causalState.tiers,
      readout_tiers: readoutTiers,
      readout_classes_match: readoutTiers.length > 0 && readoutTiers.every((r) => r.pass),
      legend: solutionCausal.legend,
      legend_shown: JSON.stringify(legendClasses)
        === JSON.stringify(["la-boi-canh", "la-chon", "la-so-lieu", "la-trung-gian"]),
      role_colors_match: roleColors.pass,
      canvas_role_hues: canvasRoleHues,
      canvas_changed: causalBeforeFrame.sha256 !== causalAfterFrame.sha256,
      pixel_delta: delta,
      dash_signature_preserved:
        JSON.stringify(edgeDefault.dash_signature) === JSON.stringify(causalState.dash_signature),
    };
    causal.pass = causal.pass && causalState.selected_id === causalId
      && causal.visual.selected_changed && causal.visual.closure_changed
      && causal.visual.tiers_match && causal.visual.readout_classes_match
      && causal.visual.legend_shown && causal.visual.role_colors_match
      && canvasRoleHues.pass
      && causal.visual.canvas_changed && delta.pass
      && causal.visual.dash_signature_preserved;
    result.causal_closure = causal;
    result.assertions.causal_closure = assertion(causal.pass, causal);
    result.screenshots.causal_selected = await capture(session, join(outDir, "causal_selected.png"));
    result.canvas_boxes.causal_selected = await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`);
    result.capture_order.push("causal_selected");
    result.screenshots.solution_causal_selected = await captureElement(session, ".geo3d-loi-giai",
      join(outDir, "solution_causal_selected.png"));
    await session.eval(`(()=>{document.querySelector('.geo3d-canvas canvas')?.scrollIntoView({block:"center"});return true})()`);

    await clickText(session, "Xem lại toàn hình");
    await pollUntil(() => session.eval(`window.__geo3d_selected_id||null`),
      (id) => id === null, { timeoutMs: 5_000 });
    const resetEmphasis = await jsonEval(session,
      `({selected_id:window.__geo3d_selected_id||null,highlighted_ids:window.__geo3d_highlighted_ids||[],`
      + `highlighted_render_owner_ids:window.__geo3d_highlighted_render_owner_ids||[]})`);
    result.assertions.emphasis_reset_before_rotation = assertion(
      resetEmphasis.selected_id === null && resetEmphasis.highlighted_render_owner_ids.length === 0,
      resetEmphasis,
    );
    await goToEnd(session);
    if (viewport.orbit) {
      const before = await projectedLabels(session);
      const hiddenBefore = await jsonEval(session,
        `({visible_edge_ids:window.__geo3d_visible_edge_ids||[],`
        + `hidden_edge_ids:window.__geo3d_hidden_edge_ids||[],`
        + `mixed_edge_ids:window.__geo3d_mixed_edge_ids||[],edge_spans:window.__geo3d_edge_spans||[]})`);
      // w11 (review W10-H4): CHỈ cử chỉ hoạch định. Ứng viên = mọi góc quanh Z
      // đạt cổng không suy biến VÀ đổi tập khuất dự đoán, theo thứ tự tất định.
      // Ảnh chỉ được nhận khi CAMERA THẬT sau cử chỉ cũng đạt cổng (đỉnh khối
      // trong khung, không dưới lớp phủ); trượt ⇒ về khung mặc định, thử ứng
      // viên sau. Cú kéo pixel cố định w10 đã bỏ: nó từng nhận ảnh dẹt.
      // OrbitControls: Δφ = 2π·dx / chiều cao khung, kéo phải làm phương vị GIẢM.
      const cam0 = await jsonEval(session, "window.__geo3d_camera_snapshot||null");
      const tam0 = await jsonEval(session, "window.__geo3d_camera_target||null");
      // Ứng viên chấm TRƯỚC trên camera mô phỏng (xoay quanh Z qua tâm quỹ đạo +
      // lùi nấc) bằng chính cổng phối cảnh; cử chỉ thật chỉ gửi cho ứng viên đạt.
      const candidates = cam0 && tam0 ? orbitPlanThuc(scene, cam0, tam0, await overlayRects(session)) : [];
      let observedOrbit = null;
      let rotatedCamera = null;
      let hiddenAfter = null;
      let accepted = null;
      const attempts = [];
      const t0 = Date.now();
      for (const candidate of candidates) {
        if (attempts.length > 0) {
          await clickText(session, "Xem lại toàn hình");
          await settleOrRecord(session, result, "rotated_retry_reset");
        }
        const gesture = { dx: candidate.dx, dy: 0, startX: 0.52, startY: 0.48,
          planned_offset_deg: candidate.offset_deg, zoom_out_notches: candidate.zoom_out_notches };
        const started_ms = Date.now() - t0;
        await trustedOrbit(session, gesture);
        try {
          observedOrbit = await pollUntil(async () => ({
            points: await projectedLabels(session),
            sets: await jsonEval(session,
              `({visible_edge_ids:window.__geo3d_visible_edge_ids||[],`
              + `hidden_edge_ids:window.__geo3d_hidden_edge_ids||[],`
              + `mixed_edge_ids:window.__geo3d_mixed_edge_ids||[],`
              + `edge_spans:window.__geo3d_edge_spans||[]})`),
          }), (observed) => projectionComparison(before, observed.points).moved_ids.length >= 2
            && JSON.stringify(observed.sets) !== JSON.stringify(hiddenBefore),
          { timeoutMs: 4_000 });
        } catch (error) {
          attempts.push({ gesture, started_ms, ended_ms: Date.now() - t0, pass: false,
            state: "GESTURE_SENT→TIMEOUT", reason: String(error) });
          observedOrbit = null;
          continue;
        }
        // Phần thứ hai của cử chỉ: lùi đúng số nấc đã hoạch định.
        await trustedZoomOut(session, candidate.zoom_out_notches);
        // Damping is still carrying the orbit here: settle, then read the sets
        // and the camera in ONE evaluation so the oracle sees the same camera.
        await settleOrRecord(session, result, "rotated_neutral");
        ({ camera: rotatedCamera, ...hiddenAfter } = await jsonEval(session,
          `({${VISIBILITY_STATE}camera:window.__geo3d_camera_snapshot||null})`));
        const gate = danhGiaAnhXoayThuc(scene, rotatedCamera, await overlayRects(session));
        const du = cameraSauCuChi(cam0, tam0, candidate.effective_offset_deg, candidate.zoom_out_notches);
        const saiSo = Math.max(...du.view_matrix_column_major.map((x, i) =>
          Math.abs(x - rotatedCamera.view_matrix_column_major[i])));
        attempts.push({ gesture, started_ms, ended_ms: Date.now() - t0, pass: gate.pass,
          state: gate.pass ? "GESTURE_SENT→ZOOM_OUT→SETTLED→GATE_PASS" : "GESTURE_SENT→ZOOM_OUT→SETTLED→GATE_FAIL",
          prediction_max_view_matrix_error: saiSo, gate });
        if (gate.pass) { accepted = { ...candidate, actual_gate: gate }; break; }
      }
      if (!accepted) throw new Error(`ORBIT_EVIDENCE_NOT_NON_DEGENERATE:${JSON.stringify({
        candidates: candidates.map((c) => c.offset_deg), attempts })}`);
      const plan = accepted;
      const after = observedOrbit.points;
      result.camera_snapshots.rotated_neutral = {
        snapshot: rotatedCamera,
        sha256: sha256(JSON.stringify(rotatedCamera)),
      };
      const orbit = projectionComparison(before, after);
      orbit.plan = plan;
      orbit.attempts = attempts;
      orbit.visibility_before = hiddenBefore;
      orbit.visibility_after = hiddenAfter;
      // Chữ ký nét đứt + owner của trạng thái xoay (cho crop có metadata) —
      // đọc RIÊNG: gộp vào `hiddenAfter` thì phép so tập khuất bên dưới luôn đúng.
      result.edge_semantics_rotated_neutral = { ...hiddenAfter, ...await jsonEval(session,
        "({dash_signature:window.__geo3d_edge_dash_signature||{},"
        + "duplicate_visual_owner_ids:window.__geo3d_duplicate_visual_owner_ids||[]})") };
      orbit.visibility_recomputed = JSON.stringify(hiddenBefore) !== JSON.stringify(hiddenAfter);
      orbit.non_degenerate = plan.actual_gate.pass;
      orbit.pass = orbit.pass && orbit.visibility_recomputed && orbit.non_degenerate;
      result.orbit = orbit;
      result.assertions.orbit = assertion(orbit.pass, orbit);
      result.screenshots.rotated_neutral = await capture(session, join(outDir, "rotated_neutral.png"));
      result.canvas_boxes.rotated_neutral = await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`);
      await clickText(session, "Xem lại toàn hình");
    }

    if (viewport.formation) {
      await clickText(session, "Xem lại toàn hình");
      result.formation = await formationEvidence(
        session, scene, join(outDir, "formation"),
        viewport.formation === "representative" ? "representative" : "full", scenario,
      );
      result.assertions.formation = assertion(result.formation.pass, {
        steps: result.formation.steps.length,
        distinct_canvas_frames: result.formation.distinct_canvas_frames,
        geometry: result.formation.geometry.checks,
        role_coverage: result.formation.role_coverage.reason_codes,
        structured_references: result.formation.structured_references.fail,
        end_locked: result.formation.end_locked,
      });
    }

    const apiCalls = analyzeCalls();
    result.assertions.single_analyze_call = assertion(apiCalls === 1, apiCalls);
    const uncaught = session.consoleEvents.filter((event) => event.loai === "exception");
    const seriousConsole = session.consoleEvents.filter((event) =>
      event.loai !== "exception" &&
      !/favicon|DevTools|Download the React/i.test(event.text));
    const failedApiCalls = apiEvents().filter((event) => event.status >= 400);
    result.uncaught_exceptions = uncaught;
    result.failed_api_calls = failedApiCalls;
    result.console_events = seriousConsole;
    result.assertions.no_uncaught_exception = assertion(uncaught.length === 0, uncaught);
    result.assertions.no_failed_api_call = assertion(failedApiCalls.length === 0, failedApiCalls);
    result.assertions.no_serious_console_error = assertion(seriousConsole.length === 0, seriousConsole);
    result.evidence_gates = evaluateEvidenceGates({
      edge: edgeDefault,
      orbit_required: Boolean(viewport.orbit),
      orbit_visibility_changed: viewport.orbit ? result.orbit?.visibility_recomputed : true,
      orbit_non_degenerate: viewport.orbit ? result.orbit?.non_degenerate : true,
      causal: {
        selected_changed: causal.visual.selected_changed,
        closure_changed: causal.visual.closure_changed,
        tiers_match: causal.visual.tiers_match,
        readout_classes_match: causal.visual.readout_classes_match,
        legend_shown: causal.visual.legend_shown,
        canvas_changed: causal.visual.canvas_changed,
        bounded_pixel_delta: causal.visual.pixel_delta.pass,
        dash_signature_preserved: causal.visual.dash_signature_preserved,
      },
      geometry: viewport.formation ? result.formation.geometry : undefined,
      formation_coverage: viewport.formation ? result.formation.role_coverage : undefined,
      structured_references: viewport.formation ? result.formation.structured_references : undefined,
      solution_final: result.solution_final,
      role_colors: roleColors,
      canvas_role_hues: causal.visual.canvas_role_hues,
      panel_over_canvas: result.solution_final.panel_over_canvas,
      capture_order: result.capture_order,
      formation_required: Boolean(viewport.formation),
      formation: viewport.formation
        ? result.formation.trace
        : { pass: true, future_object_leakage: [] },
      raw_token_leakage: result.raw_token_leakage,
      formula: result.formula_entity_coherence,
      causal_oracle_source: "independent_manifest",
      screenshot: { blank: false, premature: !css.pass },
      uncaught_exceptions: uncaught,
      failed_api_calls: failedApiCalls,
    });
    result.assertions.evidence_gates = assertion(
      result.evidence_gates.pass, result.evidence_gates.reason_codes,
    );
    result.pass = Object.values(result.assertions).every((item) => item.pass);
    return result;
  } finally {
    await session.close();
  }
}

async function runNegative({ port, viewport, fixture, scenario, outDir }) {
  const { session, analyzeCalls, apiEvents } = await openFixture({ port, viewport, fixture });
  try {
    await pollUntil(() => session.eval(`!!document.querySelector('.refusal-facts')`), Boolean);
    const observed = await jsonEval(session, `(()=>{const s=window.__ALGO_SIM_STORE__?.getState?.();`
      + `return{unsupported:s?.unsupported||null,canvas:!!document.querySelector('.geo3d-canvas canvas'),`
      + `active:!!s?.active,body:document.body.innerText,scrollWidth:document.documentElement.scrollWidth,`
      + `viewportWidth:window.innerWidth}})()`);
    const expected = scenario.negative_expected;
    // W12: âm của mọi họ là một GIVEN đề không ghi ⇒ mã nguồn có cấu trúc.
    const structuredPass = observed.unsupported?.error_code === expected.product_error_code
      && observed.unsupported?.stage_reached === expected.stage_reached
      && (!expected.reason_code || observed.unsupported?.reason_code === expected.reason_code);
    const learnerPass = Boolean(fixture.envelope.learner_reason)
      && observed.body.includes(fixture.envelope.learner_reason)
      && !observed.body.includes(fixture.envelope.reason);
    const kernelPass = !expected.kernel_error_code
      || (fixture.contract_gate?.kernel_error_code === expected.kernel_error_code
        && fixture.envelope.reason.includes(expected.kernel_error_code));
    const screenshot = await capture(session, join(outDir, "refusal.png"));
    const rawTokenLeakage = detectRawTokenLeakage(fixture.envelope.scene3d, observed.body);
    const uncaught = session.consoleEvents.filter((event) => event.loai === "exception");
    const seriousConsole = session.consoleEvents.filter((event) =>
      event.loai !== "exception" &&
      !/favicon|DevTools|Download the React/i.test(event.text));
    const failedApiCalls = apiEvents().filter((event) => event.status >= 400);
    const assertions = {
      structured_refusal: assertion(structuredPass, {
        expected: { error_code: expected.product_error_code, stage_reached: expected.stage_reached,
          reason_code: expected.reason_code ?? null },
        actual: observed.unsupported,
      }),
      learner_message: assertion(learnerPass),
      canvas_absent: assertion(!observed.canvas),
      answer_absent: assertion(!observed.active),
      no_document_overflow: assertion(observed.scrollWidth <= observed.viewportWidth + 1, {
        scroll_width: observed.scrollWidth,
        viewport_width: observed.viewportWidth,
      }),
      no_raw_token_leakage: assertion(rawTokenLeakage.pass, rawTokenLeakage),
      contract_gate: assertion(kernelPass, fixture.contract_gate ?? null),
      single_analyze_call: assertion(analyzeCalls() === 1, analyzeCalls()),
      no_uncaught_exception: assertion(uncaught.length === 0, uncaught),
      no_failed_api_call: assertion(failedApiCalls.length === 0, failedApiCalls),
      no_serious_console_error: assertion(seriousConsole.length === 0, seriousConsole),
    };
    return {
      viewport, assertions, observed: { ...observed, body: undefined }, screenshot,
      raw_token_leakage: rawTokenLeakage,
      uncaught_exceptions: uncaught,
      failed_api_calls: failedApiCalls,
      console_events: seriousConsole,
      pass: Object.values(assertions).every((item) => item.pass),
    };
  } finally {
    await session.close();
  }
}

function verifyContractGate(suite) {
  const gate = suite.section_contract_gate;
  if (gate?.semantics !== "requested_non_empty_section_must_fail_closed"
      || gate?.kernel_error_code !== "PLANE_DOES_NOT_CUT") {
    throw new Error("SECTION_CONTRACT_DRIFT");
  }
  for (const source of gate.sources ?? []) {
    if (source.hash_basis !== "git_blob_at_measurement_commit"
        || sha256GitBlob(REPO_ROOT, source.path) !== source.sha256) {
      throw new Error(`SECTION_CONTRACT_DRIFT:${source.path}`);
    }
  }
  return gate;
}

export async function runSuite({
  suitePath, fixtureRoot, outDir, screenshotDir = undefined, skipBuild = false,
}) {
  const suiteAbsolute = resolve(suitePath);
  const suite = JSON.parse(readFileSync(suiteAbsolute, "utf-8"));
  validateSuiteManifest(suite, REPO_ROOT);
  const contractGate = verifyContractGate(suite);
  const candidate = JSON.parse(readFileSync(join(REPO_ROOT, "docs", "evaluation",
    "semantic-benchmark", "EVALUATION_CANDIDATE.json"), "utf-8"));
  if ((candidate.product_commit_sha ?? candidate.commit) !== suite.product_commit_sha
      || candidate.measured_system?.tree_hash !== suite.product_tree_sha) {
    throw new Error("PRODUCT_PROVENANCE_MISMATCH");
  }
  const measurementCommitSha = execFileSync("git", ["rev-parse", "HEAD"], {
    cwd: REPO_ROOT, encoding: "utf-8",
  }).trim();
  if (!skipBuild) {
    execFileSync("npm", ["run", "build"], {
      cwd: FRONTEND, stdio: "inherit", shell: true, timeout: 600_000,
    });
    kiemDistMoi();
  }
  const output = resolve(outDir);
  const screenshots = resolve(screenshotDir ?? join(output, "screenshots"));
  mkdirSync(output, { recursive: true });
  mkdirSync(screenshots, { recursive: true });
  const root = resolve(fixtureRoot);
  const { sv, cong } = await phucVu(DIST);
  const report = {
    schema_version: "generic-tier-a-browser-evidence/1",
    task_id: suite.task_id,
    measured_at: new Date().toISOString(),
    measurement_commit_sha: measurementCommitSha,
    product_commit_sha: suite.product_commit_sha,
    product_tree_sha: suite.product_tree_sha,
    suite_manifest: relative(REPO_ROOT, suiteAbsolute).replaceAll("\\", "/"),
    suite_manifest_sha256: sha256File(suiteAbsolute),
    fixture_manifest_sha256: sha256File(join(root, "FIXTURE_MANIFEST.json")),
    section_contract_gate: contractGate,
    application_llm_calls: 0,
    scenarios: {},
  };
  try {
    for (const scenario of suite.scenarios) {
      const positive = JSON.parse(readFileSync(join(root, scenario.positive_fixture), "utf-8"));
      const negative = JSON.parse(readFileSync(join(root, scenario.negative_fixture), "utf-8"));
      // w11: manifest có thể đặt thư mục ảnh của họ (`images/<họ>/`), để ảnh
      // nguồn nằm ngay cạnh contact sheet của họ; manifest cũ vẫn dùng `id`.
      const scenarioOut = join(screenshots, scenario.evidence_dir ?? scenario.id);
      const record = { positive: {}, negative: {} };
      for (const viewport of suite.viewports) {
        record.positive[viewport.id] = await runPositive({
          port: cong,
          viewport,
          fixture: positive,
          scenario,
          outDir: join(scenarioOut, viewport.id),
        });
      }
      for (const viewport of suite.viewports) {
        record.negative[viewport.id] = await runNegative({
          port: cong,
          viewport,
          fixture: negative,
          scenario,
          outDir: join(scenarioOut, "negative", viewport.id),
        });
      }
      record.pass = Object.values(record.positive).every((item) => item.pass)
        && Object.values(record.negative).every((item) => item.pass);
      report.scenarios[scenario.id] = record;
      console.log(`${scenario.id}: ${record.pass ? "PASS" : "FAIL"}`);
    }
  } finally {
    sv.close();
  }
  report.pass = Object.values(report.scenarios).every((scenario) => scenario.pass);
  const reportPath = join(output, "BROWSER_EVIDENCE.json");
  writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf-8");
  console.log(`Wrote ${reportPath}: ${report.pass ? "PASS" : "FAIL"}`);
  return report;
}
