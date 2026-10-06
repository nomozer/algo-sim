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
  LOP_PHU_KHUNG,
  aliasTreeRowCheck,
  assessCausalCanvasHues,
  assessCssReadiness,
  assessFormation,
  assessSectionFill,
  assessSectionFillUnderEdges,
  assessAnnotationBoxes,
  assessCausalRestore,
  assessDashFollowsSpans,
  assessDetailRegion,
  assessShowAllIsolation,
  assessWitness,
  assessQuantityPicker,
  assessStepsPanel,
  coherentFormulaText,
  expectedAnnotationIds,
  cauTrucKhoi,
  diemCanhQuaThietDien,
  diemMauThietDien,
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
    scroll: await scrollOffsets(session),
  };
}

/** ROADMAP §0.1-9 — vị trí cuộn của TRANG lúc chụp: bộ đo có thể đã cuộn (`scrollIntoView`) khác người học;
 *  ghi ra để ảnh không bị đọc như khung người học thấy khi mở trang. */
async function scrollOffsets(session) {
  return jsonEval(session, "({x:Math.round(window.scrollX),y:Math.round(window.scrollY)})");
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

/** Khung canvas LÚC NGHỈ: chụp tới khi hai lần liền nhau trùng byte (≤ 10 lần, cách 100 ms; không
 *  nghỉ ⇒ `stable: false`, ghi lại chứ không giấu). Lượt trình duyệt T7: khung "trung tính" của khôi
 *  phục nhân quả (cuboid, mobile) bị chụp giữa chừng — lượt chẩn đoán cùng luồng cho trung tính =
 *  khôi phục từng byte; khung so sánh phải là khung nghỉ ở CẢ hai đầu. */
async function khungOnDinh(session) {
  let truoc = await canvasFrame(session);
  for (let i = 0; i < 10; i += 1) {
    await new Promise((done) => setTimeout(done, 100));
    const sau = await canvasFrame(session);
    if (sau.sha256 === truoc.sha256) return { ...sau, stable: true };
    truoc = sau;
  }
  return { ...truoc, stable: false };
}

/** Đoạn mã TRONG TRANG: giải hai khung PNG → ảnh `a`, `b` và mảng RGBA `pa`, `pb` trên một
 *  canvas `c` cỡ `a` (nơi gọi tự kiểm cỡ nếu cần). */
const giaiMaHaiKhung = (truoc, sau) => `const load=src=>new Promise((ok,bad)=>{`
  + `const i=new Image();i.onload=()=>ok(i);i.onerror=bad;i.src=src});`
  + `const a=await load(${JSON.stringify(`data:image/png;base64,${truoc.encoded}`)});`
  + `const b=await load(${JSON.stringify(`data:image/png;base64,${sau.encoded}`)});`
  + `const c=document.createElement('canvas');c.width=a.width;c.height=a.height;const x=c.getContext('2d');`
  + `const doc=img=>{x.clearRect(0,0,c.width,c.height);x.drawImage(img,0,0);`
  + `return x.getImageData(0,0,c.width,c.height).data};const pa=doc(a),pb=doc(b);`;

/** §15.5 khôi phục nhân quả: kênh 8-bit lệch nhiều nhất và số điểm ảnh khác giữa hai khung (giải
 *  PNG trong trang như `pixelDelta`, nhưng không có ngưỡng — ngưỡng ở `assessCausalRestore`). */
async function kenhLech(session, truoc, sau) {
  return session.eval(`(async()=>{${giaiMaHaiKhung(truoc, sau)}`
    + `if(a.width!==b.width||a.height!==b.height)return{same_size:false,max_channel_delta:null,changed_pixels:null};`
    + `let m=0,n=0;for(let i=0;i<pa.length;i+=4){const d=Math.max(Math.abs(pa[i]-pb[i]),Math.abs(pa[i+1]-pb[i+1]),`
    + `Math.abs(pa[i+2]-pb[i+2]),Math.abs(pa[i+3]-pb[i+3]));if(d){n++;if(d>m)m=d}}`
    + `return{same_size:true,max_channel_delta:m,changed_pixels:n}})()`);
}

async function pixelDelta(session, before, after) {
  return session.eval(`(async()=>{${giaiMaHaiKhung(before, after)}`
    + `if(a.width!==b.width||a.height!==b.height)return{pass:false,reason:'SIZE_MISMATCH'};`
    + `let changed=0,minX=c.width,minY=c.height,maxX=-1,maxY=-1;for(let i=0;i<pa.length;i+=4){`
    + `const d=Math.abs(pa[i]-pb[i])+Math.abs(pa[i+1]-pb[i+1])+Math.abs(pa[i+2]-pb[i+2]);`
    + `if(d<24)continue;changed++;const p=i/4,xx=p%c.width,yy=Math.floor(p/c.width);`
    + `minX=Math.min(minX,xx);minY=Math.min(minY,yy);maxX=Math.max(maxX,xx);maxY=Math.max(maxY,yy)}`
    + `const total=c.width*c.height,ratio=changed/total;return{changed_pixels:changed,total_pixels:total,`
    + `changed_ratio:ratio,bounds:changed?{x:minX,y:minY,width:maxX-minX+1,height:maxY-minY+1}:null,`
    + `pass:changed>0&&ratio<0.75}})()`);
}

/** W15 · cặp ảnh tô-BẬT / tô-TẮT ở CÙNG khung hình, cùng camera (móc
 *  `__geo3d_set_section_fill_visible`), lấy mẫu bên trong thiết diện chiếu bằng camera thật.
 *  W16 §14.4: mẫu chừa lề quanh MỌI cạnh khối và dấu điểm (đúng §11); `duoiCanh` thêm dải lõi
 *  và tham chiếu của từng cạnh khối đi qua vùng (SECTION_FILL_UNDER_EDGES). */
async function sectionFillPairs(session, section, scene, { duoiCanh = false } = {}) {
  const doiKhung = "new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))";
  const snapshot = await jsonEval(session, "window.__geo3d_camera_snapshot||null");
  const cham = (await jsonEval(session, "window.__geo3d_vertex_markers||[]")) ?? [];
  const khoi = cauTrucKhoi(scene);
  const canh = khoi.canh.map(([i, j]) => ({ id: `${khoi.ten[i]}-${khoi.ten[j]}`, a: khoi.diem[i], b: khoi.diem[j] }));
  // W17: hộp lớp phủ DOM (nhãn điểm, nhãn số đo, nút) px CSS tương đối canvas — mẫu không nằm dưới chúng.
  const hop = await jsonEval(session, `(()=>{const k=document.querySelector('.geo3d-canvas canvas')`
    + `.getBoundingClientRect();return[...document.querySelectorAll(${JSON.stringify(LOP_PHU_KHUNG)})]`
    + `.map(e=>e.getBoundingClientRect()).filter(r=>r.width>0&&r.height>0)`
    + `.map(r=>({x:r.left-k.left,y:r.top-k.top,w:r.width,h:r.height}))})()`);
  const diem = snapshot ? diemMauThietDien(section.polygon, snapshot, { canh, cham, hop }) : [];
  const dai = duoiCanh && snapshot ? diemCanhQuaThietDien(section.polygon, snapshot, canh, cham, hop) : [];
  const bat = await canvasFrame(session);
  const ten = await jsonEval(session, "window.__geo3d_set_section_fill_visible?.(false)??null");
  await session.eval(doiKhung);
  const tat = await canvasFrame(session);
  await session.eval("window.__geo3d_set_section_fill_visible?.(true)");
  await session.eval(doiKhung);
  if (diem.length === 0 && dai.length === 0) return { fill_mesh_names: ten, pairs: [], under: [] };
  const kq = await session.eval(maDocCapDiem(bat, tat, snapshot, diem, dai));
  return { fill_mesh_names: ten, pairs: kq.pairs, under: kq.under };
}

/** Mã TRONG TRANG (W16): giải hai khung rồi đọc cặp bật/tắt tại các điểm mẫu px CSS và tại dải
 *  lõi/tham chiếu của từng cạnh. Tách ra để node test biên dịch được nó. */
export const maDocCapDiem = (bat, tat, snapshot, diem, dai) => `(async()=>{${giaiMaHaiKhung(bat, tat)}`
  + `const sx=a.width/${snapshot.viewport_width},sy=a.height/${snapshot.viewport_height};`
  // `doc` đã là hàm giải ảnh của `giaiMaHaiKhung`: trùng tên ⇒ SyntaxError trong trang (lượt 55cde06e).
  + `const docDiem=(pts)=>pts.map(([u,v])=>{const i=(Math.min(c.height-1,Math.round(v*sy))*c.width`
  + `+Math.min(c.width-1,Math.round(u*sx)))*4;return{on:[pa[i],pa[i+1],pa[i+2]],off:[pb[i],pb[i+1],pb[i+2]]}});`
  + `return{pairs:docDiem(${JSON.stringify(diem)}),under:${JSON.stringify(dai)}`
  + `.map(e=>({id:e.id,core:docDiem(e.core),ref:docDiem(e.ref)}))}})()`;

/** W15 SECTION_FILL_DISTINGUISHABLE (ngưỡng đăng ký trước, §11): bước khép-và-tô ĐẦU TIÊN phải
 *  phân biệt được (và có vật tô thật); mọi bước TRƯỚC đó kể từ khi mặt cắt hiện, và bước vừa
 *  lùi về sau bước khép, không được có tô. So bật/tắt cùng khung — không so bước với bước. */
async function sectionFillEvidence(session, scene) {
  const section = scene.objects.find((o) => o.type === "section" && (o.polygon?.length ?? 0) >= 3);
  if (!section) return undefined;
  const timeline = expectedGeometryTimeline(scene);
  const tienDo = (k) => scene.formation?.steps?.[k]?.geometry_progress?.find((g) => g.object_id === section.id);
  const matCat = (section.depends ?? []).find((id) =>
    scene.objects.some((o) => o.id === id && o.type === "plane3"));
  const kDong = timeline.findIndex((t) => tienDo(t.anchor)?.closed && tienDo(t.anchor)?.fill_visible);
  const ra = { section_id: section.id, cutting_plane_id: matCat ?? null, closed_ui_step: kDong, pre_close: [] };
  if (kDong < 1) return { ...ra, pass: false, reason: "NO_CLOSED_FILL_STEP" };
  await goToStart(session);
  for (let i = 0; i < kDong; i += 1) {
    if (expectedVisibleIds(scene, timeline[i].anchor).includes(matCat ?? section.id)) {
      const m = await sectionFillPairs(session, section, scene);
      ra.pre_close.push({ ui_step: i, fill_mesh_names: m.fill_mesh_names, ...assessSectionFill("pre_close", m.pairs) });
    }
    await moveStep(session, 1);
  }
  const dong = await sectionFillPairs(session, section, scene, { duoiCanh: true });
  ra.closed = { ui_step: kDong, fill_mesh_names: dong.fill_mesh_names, ...assessSectionFill("closed", dong.pairs),
    under_edges: assessSectionFillUnderEdges(dong.under) };
  await moveStep(session, -1);
  const lui = await sectionFillPairs(session, section, scene);
  ra.rewound = { ui_step: kDong - 1, fill_mesh_names: lui.fill_mesh_names, ...assessSectionFill("rewound", lui.pairs) };
  await goToEnd(session);
  ra.pass = ra.closed.pass && (ra.closed.fill_mesh_names ?? []).length > 0 && ra.rewound.pass
    && ra.pre_close.length > 0 && ra.pre_close.every((x) => x.pass) && ra.closed.under_edges.pass;
  return ra;
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
    + `const che=[...document.querySelectorAll(${JSON.stringify(LOP_PHU_KHUNG)})]`
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
    + `solution=pick('.geo3d-loi-giai'),solutionTitle=pick('.geo3d-lg-ten-muc')||pick('.geo3d-lg-gap');`
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
    + `results_card:!!document.querySelector('.geo3d-lg-ket-qua'),`
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
    scroll: await scrollOffsets(session),
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
  // W4: mỗi bảng thông tin có nút đóng mang TÊN riêng (nhiều bảng có thể cùng mở).
  await clickAria(session, "Đóng các thành phần của hình");
  await pollUntil(() => session.eval(`!document.querySelector('.geo3d-tree')`), Boolean,
    { timeoutMs: 5_000 });
  return { objects: checks, pass: checks.every((item) => item.pass) };
}

/** Vật THẬT SỰ được dựng lên khung (renderer tự báo). Giữ đuôi `#…` — nó là
 *  tiến độ thiết diện (số đỉnh, khép, tô): mỗi cạnh thiết diện là một bước. */
async function renderedIds(session) {
  return jsonEval(session, "(window.__geo3d_rendered_object_ids||[]).map(String).sort()");
}

/** W17 · nhãn số đo: hộp đang hiện (sản phẩm báo mỗi khung), nhãn điểm đang hiện, camera, và tập
 *  nhãn số đo CÓ trong DOM (khả dụng ở bước này, bất kể có chỗ đặt hay không). */
async function annotationState(session) {
  return jsonEval(session, `({boxes:window.__geo3d_annotation_boxes||[],`
    + `points:window.__geo3d_point_label_boxes||[],camera:window.__geo3d_camera_snapshot||null,`
    + `witness:(window.__geo3d_witness_ids||[]).map(String).sort(),selected:window.__geo3d_selected_id||null,`
    + `dom:[...document.querySelectorAll('.geo3d-so-do')].map((e)=>e.dataset.annId).sort()})`);
}

/** W18 §16.6 — mọi vùng ĐANG HIỆN mang chữ công thức `f`: ô soi, hoặc một dòng lời giải đang hiện. */
async function formulaRegions(session, f) {
  return jsonEval(session, `(()=>{const f=${JSON.stringify(f)};const hien=e=>!!e&&e.offsetParent!==null;`
    + `const ra=[];const o=document.querySelector('.geo3d-soi-cong-thuc');`
    + `if(hien(o)&&(o.textContent||'').includes(f))ra.push('inspector');`
    + `for(const d of document.querySelectorAll('.geo3d-lg-dong[data-solution-id]')){const s=d.querySelector('.geo3d-lg-so');`
    + `if(hien(s)&&(s.textContent||'').includes(f))ra.push('solution:'+d.dataset.solutionId)}return ra})()`);
}

/** Bấm nút của một dòng lời giải (chọn/bỏ chọn đại lượng ấy) — sự kiện chuột thật. */
async function clickSolutionRow(session, id) {
  return trustedClick(session, `document.querySelector('[data-solution-id=${JSON.stringify(id)}] .geo3d-lg-nut')`);
}

/** Mở/thu gọn lời giải đầy đủ cho tới khi thân ở trạng thái `mo`. */
async function setSolutionOpen(session, mo) {
  const st = await solutionState(session);
  if (st.body_collapsed === !mo) return;
  await trustedClick(session, "document.querySelector('.geo3d-lg-gap')");
  await pollUntil(() => solutionState(session), (s) => s.body_collapsed === !mo, { timeoutMs: 5_000 });
}

/** Bước NEO (chỉ số sự kiện) của bước dựng đang xem — qua dòng thời gian ĐỘC LẬP của bộ đo. */
async function anchorNow(session, scene) {
  const step = await currentStep(session);
  return step ? expectedGeometryTimeline(scene)[step.index]?.anchor ?? null : null;
}

/** Nhãn số đo bắt buộc hiện ở chế độ mặc định (W18 §16.5): khổ rộng — mọi dữ kiện khả dụng; khổ hẹp
 *  và đổi cỡ — không bắt buộc nhãn nào (hết chỗ thì nhãn ưu tiên thấp ẩn, giá trị vẫn ở ô soi/lời giải);
 *  đại lượng ĐANG CHỌN thì bắt buộc ở mọi khổ (kiểm ở phần chọn từng đại lượng). */
function annotationsMustShow(scene, ids, hep) {
  return hep ? [] : ids;
}

async function clickChip(session, ten) {
  return trustedClick(session, `[...document.querySelectorAll('.geo3d-thanh-nut .geo3d-chip')]`
    + `.find((b)=>(b.textContent||'').includes(${JSON.stringify(ten)}))`);
}

/** ROADMAP §0.1-3 — panel «Các bước dựng»: số nút, bước đang đánh dấu, nhãn của nó (thay dải "Đang dựng" đã
 *  gỡ ở §0.1-8 — nhãn bước giờ đọc ở đây). Panel đóng ⇒ `open:false`, không có nút. */
async function stepsPanelState(session) {
  return jsonEval(session, `(()=>{const t=document.querySelector('.geo3d-cac-buoc-mo');`
    + `const b=[...document.querySelectorAll('.geo3d-cac-buoc-nut')];const c=b.filter(e=>e.getAttribute('aria-current')==='step');`
    + `return{open:t?.getAttribute('aria-expanded')==='true',count:b.length,marked:c.length,`
    + `current:c.length===1?Number(c[0].dataset.geometryStep):null,`
    + `label:(c[0]?.querySelector('.geo3d-cac-buoc-chu')?.textContent||'').trim(),`
    + `scroll_top:Math.round(document.querySelector('.geo3d-cac-buoc')?.scrollTop||0)}})()`);
}

async function setStepsPanelOpen(session, mo) {
  if ((await stepsPanelState(session)).open === mo) return;
  await trustedClick(session, "document.querySelector('.geo3d-cac-buoc-mo')");
  await pollUntil(() => stepsPanelState(session), (p) => p.open === mo, { timeoutMs: 5_000 });
}

/** ROADMAP §0.1-2 — ngăn «Đại lượng»: mở (nếu đang đóng), đọc các nút theo mục (id máy qua `data-quantity-id`). */
async function quantityDrawer(session) {
  if (!await session.eval("!!document.querySelector('.geo3d-dai-luong')")) await clickChip(session, "Đại lượng");
  await pollUntil(() => session.eval("!!document.querySelector('.geo3d-dai-luong')"), Boolean, { timeoutMs: 5_000 });
  return jsonEval(session, `[...document.querySelectorAll('.geo3d-dai-luong [data-quantity-id]')].map(e=>({`
    + `id:e.dataset.quantityId,sec:(e.closest('section')?.getAttribute('aria-label')||''),`
    + `text:(e.textContent||'').replace(/\\s+/g,' ').trim()}))`);
}

/** Id các đại lượng ngăn «Đại lượng» liệt kê ở bước đang xem; chip vắng (chưa có đại lượng) ⇒ []. Mở rồi đóng. */
async function quantityDrawerIds(session) {
  const coChip = await session.eval(`[...document.querySelectorAll('.geo3d-thanh-nut .geo3d-chip')]`
    + `.some((b)=>(b.textContent||'').includes('Đại lượng'))`);
  if (!coChip) return [];
  const ids = (await quantityDrawer(session)).map((x) => x.id);
  await closeQuantityDrawer(session);
  return ids;
}

async function closeQuantityDrawer(session) {
  if (await session.eval("!!document.querySelector('.geo3d-dai-luong')")) await clickChip(session, "Đại lượng");
}

/** Chọn một đại lượng như người học khi lời giải thu gọn: chip «Đại lượng» → nút của nó. W4: bảng «Đại lượng» nay
 *  GIỮ mở khi chọn (sản phẩm); luồng đo này đóng nó sau khi chọn, như người học dọn bàn, để phép đo nhãn và ô soi
 *  phía sau không phụ thuộc bảng ấy đang che phần nào của hình. Bảng ở lại khi chọn: `w04-panels-probe.mjs`. */
async function selectViaPicker(session, id) {
  if (!await session.eval("!!document.querySelector('.geo3d-dai-luong')")) await clickChip(session, "Đại lượng");
  const ok = await trustedClick(session,
    `document.querySelector('.geo3d-dai-luong [data-quantity-id=${JSON.stringify(id)}]')`);
  await closeQuantityDrawer(session);
  return ok;
}

async function deselect(session) {
  return trustedClick(session, `document.querySelector('[aria-label="Bỏ chọn"]')`);
}

/** W12: thanh bước đi qua BƯỚC DỰNG. Mỗi bước: khung = snapshot neo của bước
 *  (oracle độc lập), cây thành phần, nhãn điểm, vật dựng lên khung, dòng "Đang
 *  dựng", bảng lời giải; rồi tua ngược so từng bước. W14: cùng các bước ấy chấm
 *  độ phủ vai trò (kỳ vọng registry · khai báo sản phẩm · vật renderer báo) và
 *  mọi tham chiếu có cấu trúc. */
async function formationEvidence(session, scene, outDir, captureMode, scenario) {
  await goToStart(session);
  // §0.1-3: đi các bước với panel «Các bước dựng» MỞ — nhãn bước đọc ở panel, panel phải theo kịp thanh bước.
  await setStepsPanelOpen(session, true);
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
    const solState = await solutionState(session);
    const solution = rowsBySection(solState);
    // §0.1-1: thu gọn ⇒ không có card Kết quả (đáp số đọc qua ngăn «Đại lượng»).
    const expectedSolution = solState.body_collapsed
      ? { ...expectedSolutionRows(scene, anchor), results: [] } : expectedSolutionRows(scene, anchor);
    const panel = await stepsPanelState(session);
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
    // W17 §15.5: không lộ trước — nhãn số đo trong DOM đúng bằng oracle khả dụng của bước.
    const annotationDom = (await annotationState(session)).dom;
    const expectedAnnotations = expectedAnnotationIds(scene, anchor);
    // W18 §16.8 (đính chính): bước dựng TÔ SÁNG cạnh đang dựng — nét vẽ phải theo phân loại khuất.
    // §0.1-1/2: kết quả ẩn cùng lời giải thu gọn đọc qua ngăn — ghi id của ngăn ở bước này (sau ảnh, trước bước sau).
    const picker = await quantityDrawerIds(session);
    const dash = assessDashFollowsSpans(await jsonEval(session, "({spans:window.__geo3d_edge_spans||[],"
      + "dash_signature:window.__geo3d_edge_dash_signature||{},"
      + "highlighted:window.__geo3d_highlighted_render_owner_ids||[]})"));
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
      focus_label: panel.label,
      panel,
      picker,
      solution_collapsed: solState.body_collapsed,
      solution,
      expected_solution: expectedSolution,
      solution_pass: JSON.stringify(solution) === JSON.stringify(expectedSolution),
      screenshot: image,
      canvas,
      learner_text: learnerText,
      formation_roles: formationRoles,
      annotation_dom: annotationDom,
      expected_annotations: expectedAnnotations,
      annotation_pass: JSON.stringify(annotationDom) === JSON.stringify(expectedAnnotations),
      dash,
    });
    if (index < stepTotal - 1 && !await moveStep(session, 1)) {
      throw new Error(`FORMATION_STOPPED_AT:${index}`);
    }
  }
  // Ở bước cuối, "Bước sau" phải vô hiệu — không có bước tính nào sau nó.
  const endLocked = !await moveStep(session, 1);
  const backwardRendered = [];
  const backwardAnnotations = [];
  const backwardPanel = [];
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
    backwardPanel[index] = { index, panel: await stepsPanelState(session) };
    backwardAnnotations[index] = (await annotationState(session)).dom;
    if (index > 0 && !await moveStep(session, -1)) {
      throw new Error(`FORMATION_BACKWARD_STOPPED_AT:${index}`);
    }
  }
  // §0.1-5: chọn một bước TỪ PANEL (đang phát) ⇒ phát dừng, chỉ báo + vật dựng = bước ấy khi đi tuần tự.
  const target = Math.max(1, representative);
  if (await session.eval(`!!document.querySelector('[aria-label="Phát lại quá trình dựng"]')`)) {
    await clickAria(session, "Phát lại quá trình dựng");
  }
  await trustedClick(session, `document.querySelector('.geo3d-cac-buoc-nut[data-geometry-step="${target}"]')`);
  await pollUntil(() => currentStep(session), (s) => s?.index === target, { timeoutMs: 5_000 }).catch(() => null);
  await new Promise((done) => setTimeout(done, 1_600));   // hơn một nhịp phát: phát còn chạy thì bước đã trôi
  const jumpStep = await currentStep(session);
  const jump = { target, indicator: jumpStep?.index ?? null,
    rendered_matches: JSON.stringify(await renderedIds(session)) === JSON.stringify(steps[target]?.rendered),
    playing: Boolean(await session.eval(`!!document.querySelector('[aria-label="Tạm dừng"]')`)),
    panel: await stepsPanelState(session) };
  const panelOpenShot = await capture(session, join(outDir, "steps_panel_open.png"));
  // §0.1-5: đóng panel không reset bước hay lựa chọn.
  const truocDong = { step: (await currentStep(session))?.index ?? null,
    selected: await session.eval("window.__geo3d_selected_id||null") };
  await setStepsPanelOpen(session, false);
  const close = { step_before: truocDong.step, selected_before: truocDong.selected,
    step_after: (await currentStep(session))?.index ?? null,
    selected_after: await session.eval("window.__geo3d_selected_id||null") };
  const panelClosedShot = await capture(session, join(outDir, "steps_panel_closed.png"));
  const stepsPanel = { ...assessStepsPanel(scene, {
    steps: steps.map((s) => ({ index: s.index, panel: s.panel })), backward: backwardPanel, jump, close }),
  jump, close, screenshots: { open: panelOpenShot, closed: panelClosedShot } };
  const trace = assessFormationSnapshots(scene, observations, timeline.map((g) => g.anchor));
  const geometry = assessGeometrySteps(scene, {
    step_count: steps[0]?.indicator?.count ?? null,
    steps: steps.map((s) => ({ index: s.index, rendered: s.rendered, focus_label: s.focus_label,
      solution_collapsed: s.solution_collapsed, solution: s.solution })),
  });
  const forwardBackward = steps.map((s) => ({ index: s.index,
    pass: JSON.stringify(s.rendered) === JSON.stringify(backwardRendered[s.index])
      && JSON.stringify(s.annotation_dom) === JSON.stringify(backwardAnnotations[s.index]) }));
  const structuredReferences = assessStructuredReferences(scene, {
    steps: steps.map((s) => ({ index: s.index, rendered: s.rendered, solution: s.solution, picker: s.picker })) });
  const roleCoverage = assessFormation(scenario.expected_formation, scene,
    steps.map((s) => ({ index: s.index, renderedSets: renderedSets(scene, s.rendered) })),
    scenario.formation_coverage.enforce, scenario.formation_coverage.measure);
  const canvasHashes = new Set(steps.map((step) => step.canvas.sha256));
  // Kiểm không rỗng: những cạnh khuất ĐƯỢC TÔ SÁNG ở một bước nào đó (ghi lại; một họ có thể không có).
  const dashUnderHighlight = { steps_checked: steps.length,
    highlighted_hidden_owner_ids: sortedUnique(steps.flatMap((s) => s.dash.highlighted_hidden_owner_ids)),
    pass: steps.every((s) => s.dash.pass) };
  const pass = steps.every((step) => step.indicator?.index === step.index
    && step.indicator?.count === stepTotal
    && step.tree.pass && step.point_visibility_pass && step.solution_pass && step.annotation_pass && step.dash.pass)
    && canvasHashes.size >= 2 && trace.pass && geometry.pass && endLocked
    && forwardBackward.every((x) => x.pass) && structuredReferences.pass && roleCoverage.pass && stepsPanel.pass;
  return { steps, observations, trace, geometry, forward_backward: forwardBackward, steps_panel: stepsPanel,
    structured_references: structuredReferences, role_coverage: roleCoverage, dash_under_highlight: dashUnderHighlight,
    end_locked: endLocked, distinct_canvas_frames: canvasHashes.size, pass };
}

async function runPositive({ port, viewport, fixture, scenario, outDir }) {
  const scene = fixture.envelope.scene3d;
  const { session, analyzeCalls, apiEvents } = await openFixture({ port, viewport, fixture });
  const result = { viewport, assertions: {}, screenshots: {}, capture_order: [] };
  try {
    await pollUntil(() => session.eval(`!!document.querySelector('.geo3d-canvas canvas')`), Boolean);
    await goToEnd(session);
    // §0.1-1/2: lời giải thu gọn ⇒ không card Kết quả; đáp số đọc qua ngăn «Đại lượng» (mở rồi đóng, không chọn).
    const cardThuGon = (await solutionState(session)).results_card;
    const ngan = await pollUntil(() => quantityDrawer(session),
      (d) => d.some((x) => x.text.includes(scenario.expected_answer)), { timeoutMs: 8_000 })
      .catch(() => quantityDrawer(session));
    result.quantity_picker = assessQuantityPicker({ scene, anchor: expectedGeometryTimeline(scene).at(-1).anchor,
      resultCardWhileCollapsed: cardThuGon, drawer: ngan, expectedAnswer: scenario.expected_answer });
    result.assertions.quantity_picker = assertion(result.quantity_picker.pass, result.quantity_picker);
    result.screenshots.quantity_picker = await capture(session, join(outDir, "quantity_picker.png"));
    result.capture_order.push("quantity_picker");
    await closeQuantityDrawer(session);

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
      // §0.1-1: mặc định thu gọn ⇒ không có dòng Kết quả; đáp số một lần ở lời giải MỞ (kiểm ở `open`).
      expected: { ...expectedSolutionRows(scene, lastAnchor), results: [] },
      results_card: solutionNeutral.results_card,
      observed: rowsBySection(solutionNeutral),
      answer_rows: answerRows.map((row) => ({ id: row.id, sec: row.sec, text: row.text })),
      body_collapsed: solutionNeutral.body_collapsed,
      panel_box: solutionNeutral.panel,
      canvas_box: solutionNeutral.canvas,
      legend: solutionNeutral.legend,
    };
    result.solution_final.in_sync = JSON.stringify(result.solution_final.expected)
      === JSON.stringify(result.solution_final.observed);
    result.solution_final.answer_hidden_collapsed = answerRows.length === 0 && !solutionNeutral.results_card;
    result.solution_final.panel_over_canvas = overlaps(solutionNeutral.panel, solutionNeutral.canvas);
    result.assertions.solution_final = assertion(result.solution_final.in_sync
      && result.solution_final.answer_hidden_collapsed && !result.solution_final.panel_over_canvas
      && solutionNeutral.legend.length === 0
      // W18 §16.6: lời giải đầy đủ thu gọn mặc định ở MỌI khổ.
      && result.solution_final.body_collapsed === true, result.solution_final);
    // W17 §15.5 — nhãn số đo ở khung cuối trung tính (camera đã lắng; hộp và camera cùng một khung).
    const ann0 = await annotationState(session);
    const neoCuoi = await anchorNow(session, scene);
    result.annotations = { final: assessAnnotationBoxes({ scene, step: neoCuoi, boxes: ann0.boxes,
      points: ann0.points, camera: ann0.camera,
      mustShow: annotationsMustShow(scene, expectedAnnotationIds(scene, neoCuoi), viewport.width < 768) }) };
    result.assertions.annotations_final = assertion(result.annotations.final.pass, result.annotations.final);

    // Default phải được chụp trước causal/orbit/formation.
    result.screenshots.neutral_final = await capture(session, join(outDir, "neutral_final.png"));
    // Hộp canvas NGAY lúc chụp — trang có thể đã cuộn khác lúc ghi `canvas_box`
    // (w10: crop mobile lệch vì hộp ghi ở y = -226).
    result.canvas_boxes = { neutral_final: await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`) };
    result.capture_order.push("neutral_final");
    // Bảng lời giải ở trạng thái mặc định (W18 §16.6: thu gọn ở mọi khổ), rồi mở đủ, rồi thu lại.
    result.screenshots.solution_neutral_final = await captureElement(session, ".geo3d-loi-giai",
      join(outDir, "solution_neutral_final.png"));
    await setSolutionOpen(session, true);
    result.screenshots.solution_expanded = await captureElement(session, ".geo3d-loi-giai",
      join(outDir, "solution_expanded.png"));
    {
      // Lời giải MỞ: card Kết quả có mặt, đáp số ĐÚNG MỘT dòng và nằm ở Kết quả (W12, giữ).
      const mo = await solutionState(session);
      const dapSo = mo.rows.filter((row) => finalIds.has(row.id)
        || finalIds.has(scene.objects.find((object) => object.id === row.id)?.alias_of));
      result.solution_final.open = { results_card: mo.results_card,
        in_sync: JSON.stringify(rowsBySection(mo)) === JSON.stringify(expectedSolutionRows(scene, lastAnchor)),
        answer_rows: dapSo.map((row) => ({ id: row.id, sec: row.sec, text: row.text })),
        answer_once: mo.results_card && dapSo.length === finalIds.size && dapSo.every((row) => row.sec === "Kết quả")
          && mo.result_text.includes(scenario.expected_answer) };
      result.assertions.solution_open = assertion(result.solution_final.open.in_sync
        && result.solution_final.open.answer_once, result.solution_final.open);
    }
    await setSolutionOpen(session, false);
    const chup = async () => {
      const a = await annotationState(session);
      return { ...await jsonEval(session, `({dash_signature:window.__geo3d_edge_dash_signature||{},`
        + `rendered_object_ids:(window.__geo3d_rendered_object_ids||[]).map(String).sort(),`
        + `camera:window.__geo3d_camera_snapshot||null,selected_id:window.__geo3d_selected_id||null})`),
        step: await currentStep(session), annotation_ids: a.dom, witness_ids: a.witness };
    };
    // Hết hạn chờ là MỘT KẾT LUẬN (công tắc không đưa nhãn về trạng thái hứa), không phải lỗi bộ
    // chạy: ghi lại rồi để bộ đánh giá nói vì sao (tiêm lỗi FB1 W17: lượt cũ dừng cả suite ở đây).
    const choHet = (dk) => pollUntil(() => annotationState(session), dk, { timeoutMs: 5_000 })
      .then(() => null, (e) => String(e?.message ?? e).slice(0, 160));
    // W18 §16.8 — "Hiện tất cả" bật → tắt → bật: tập nhãn đúng oracle ở mỗi trạng thái; nét đứt, vật
    // dựng, camera, bước, lựa chọn y nguyên. Công tắc vắng (không có nhãn mặc định đang ẩn) ⇒ không đo.
    const congTac = await jsonEval(session, `[...document.querySelectorAll('.geo3d-thanh-nut .geo3d-chip')]`
      + `.map((b)=>(b.textContent||'').trim()).filter((t)=>t.includes('Hiện tất cả'))`);
    if (congTac.length) {
      const expectedOn = expectedAnnotationIds(scene, neoCuoi, { showAll: true });
      const expectedOff = expectedAnnotationIds(scene, neoCuoi);
      // Mốc TRƯỚC lần bấm đầu (đính chính §16.8): tác dụng phụ lặp ở mọi lần bấm vẫn lộ ra.
      await settleOrRecord(session, result, "show_all_before");
      const before = await chup();
      await clickChip(session, "Hiện tất cả");
      const hetBat = await choHet((s) => JSON.stringify(s.dom) === JSON.stringify(expectedOn));
      await settleOrRecord(session, result, "show_all_on");
      const on = await chup();
      const annOn = await annotationState(session);
      result.annotations.show_all = assessAnnotationBoxes({ scene, step: neoCuoi, boxes: annOn.boxes,
        points: annOn.points, camera: annOn.camera, expected: expectedOn, mustShow: [] });
      result.assertions.annotations_show_all = assertion(result.annotations.show_all.pass,
        result.annotations.show_all);
      result.witness_show_all = assessWitness({ scene, shownIds: annOn.boxes.map((b) => b.id), witnessIds: annOn.witness });
      result.assertions.witness_show_all = assertion(result.witness_show_all.pass, result.witness_show_all);
      result.screenshots.show_all = await capture(session, join(outDir, "show_all.png"));
      result.capture_order.push("show_all");
      await clickChip(session, "Hiện tất cả");
      const hetTat = await choHet((s) => JSON.stringify(s.dom) === JSON.stringify(expectedOff));
      await settleOrRecord(session, result, "show_all_off");
      const off = await chup();
      await clickChip(session, "Hiện tất cả");
      const hetBatLai = await choHet((s) => JSON.stringify(s.dom) === JSON.stringify(expectedOn));
      await settleOrRecord(session, result, "show_all_back");
      const back = await chup();
      result.show_all_toggle = { chips: congTac, before, on, off, back,
        poll_timeouts: { on: hetBat, off: hetTat, back: hetBatLai },
        ...assessShowAllIsolation({ before, on, off, back, expectedOn, expectedOff }) };
      // Về mặc định gọn cho các phép đo sau; công tắc lỡ đổi bước thì đã bị ghi ở trên — quay về.
      await clickChip(session, "Hiện tất cả");
      await choHet((s) => JSON.stringify(s.dom) === JSON.stringify(expectedOff));
      if (JSON.stringify(await currentStep(session)) !== JSON.stringify(before.step)) await goToEnd(session);
      result.assertions.show_all_toggle = assertion(result.show_all_toggle.pass, result.show_all_toggle.reason_codes);
    }
    // W18 §16.5–16.7 — chọn TỪNG đại lượng qua bảng lời giải: nhãn hiện = nó + chuỗi số của nó (oracle
    // độc lập), nhãn của nó bắt buộc có mặt và ≤ 24 px quanh đúng chủ thể; đúng MỘT vùng mang công
    // thức (ô soi khi lời giải thu gọn — mục Kết quả; dòng lời giải khi mở — Dữ kiện/Các bước tính);
    // nhân chứng vẽ đúng cho nhãn khoảng cách đang hiện. Ảnh đại diện theo loại đo.
    {
      await setSolutionOpen(session, true);
      const hang = (await solutionState(session)).rows;
      await setSolutionOpen(session, false);
      result.selection_checks = [];
      const daChup = new Set();
      for (const row of hang) {
        const q = scene.objects.find((o) => o.id === row.id);
        if (!q) continue;
        // §0.1-2: Kết quả không còn dòng khi thu gọn — chọn qua ngăn «Đại lượng» như người học.
        await setSolutionOpen(session, row.sec !== "Kết quả");
        if (row.sec === "Kết quả") await selectViaPicker(session, row.id);
        else await clickSolutionRow(session, row.id);
        const daChon = await choHet((s) => s.selected === row.id);
        await settleOrRecord(session, result, `select_${row.id}`);
        const ann = await annotationState(session);
        const expected = expectedAnnotationIds(scene, neoCuoi, { selectedId: row.id });
        const coNhan = Boolean(q.annotation && !q.annotation.same_as && expected.includes(q.id));
        const hop = assessAnnotationBoxes({ scene, step: neoCuoi, boxes: ann.boxes, points: ann.points,
          camera: ann.camera, expected, mustShow: coNhan ? [q.id] : [] });
        const f = coherentFormulaText(scene, row.id);
        const vung = f ? assessDetailRegion({ formula_text: f, regions: await formulaRegions(session, f) }) : null;
        const nhanChung = assessWitness({ scene, shownIds: ann.boxes.map((b) => b.id), witnessIds: ann.witness });
        const domDung = JSON.stringify(ann.dom) === JSON.stringify(expected);
        const kq = { id: row.id, section: row.sec, selected: daChon === null, dom: ann.dom, expected,
          dom_pass: domDung, boxes: hop, detail_region: vung, witness: nhanChung,
          pass: daChon === null && domDung && hop.pass && (!vung || vung.pass) && nhanChung.pass };
        result.selection_checks.push(kq);
        const loai = q.annotation?.kind;
        if (loai && !daChup.has(loai) && coNhan) {
          daChup.add(loai);
          // Bấm dòng lời giải đã cuộn trang: đưa khung về giữa trước khi chụp hình (nhãn + nhân chứng),
          // rồi chụp riêng ô soi (bảng chi tiết của đại lượng đang chọn).
          await session.eval(`(()=>{document.querySelector('.geo3d-canvas canvas')?.scrollIntoView({block:"center"});return true})()`);
          await settleOrRecord(session, result, `select_${row.id}_scrolled`);
          result.canvas_boxes[`selected_${loai}`] = await rectFor(session, `document.querySelector('.geo3d-canvas canvas')`);
          result.screenshots[`selected_${loai}`] = await capture(session, join(outDir, `selected_${loai}.png`));
          result.screenshots[`detail_${loai}`] = await captureElement(session, ".geo3d-soi", join(outDir, `detail_${loai}.png`));
          result.capture_order.push(`selected_${loai}`, `detail_${loai}`);
        }
        // Đính chính §16.8: đáp số có công thức tham chiếu được chọn cả khi lời giải MỞ — công thức ở dòng
        // lời giải, ô soi bỏ khối công thức (đúng một vùng). Trạng thái duy nhất có thể sinh hai bản (FW4).
        if (f && row.sec === "Kết quả") {
          await setSolutionOpen(session, true);
          kq.detail_region_open = assessDetailRegion({ formula_text: f, regions: await formulaRegions(session, f) });
          kq.pass = kq.pass && kq.detail_region_open.pass;
          await setSolutionOpen(session, false);
        }
        await deselect(session);
        await choHet((s) => s.selected === null);
      }
      await setSolutionOpen(session, false);
      await settleOrRecord(session, result, "selection_done");
      result.assertions.selection_per_quantity = assertion(
        result.selection_checks.length > 0 && result.selection_checks.every((c) => c.pass),
        result.selection_checks.filter((c) => !c.pass));
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
    const causalBeforeFrame = await khungOnDinh(session);
    const causalBeforeState = await jsonEval(session, `({selected_id:window.__geo3d_selected_id||null,`
      + `highlighted_ids:window.__geo3d_highlighted_ids||[],`
      + `highlighted_render_owner_ids:window.__geo3d_highlighted_render_owner_ids||[]})`);
    // W17 §15.5: ba thứ GHI RIÊNG — camera, lựa chọn, vị trí cuộn — ở trạng thái trung tính.
    const CAMERA_CUON = "({camera:window.__geo3d_camera_snapshot||null,scroll_y:Math.round(window.scrollY),"
      + "selected_id:window.__geo3d_selected_id||null})";
    const causalNeutral = { ...await jsonEval(session, CAMERA_CUON), canvas_sha256: causalBeforeFrame.sha256,
      canvas_stable: causalBeforeFrame.stable };

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
    // regular-square-pyramid-w01 (ROADMAP §0.1-1/2): card Kết quả ẩn khi lời giải thu gọn — đích (một đáp số)
    // chọn qua ngăn «Đại lượng» như người học; dòng Dữ kiện/Các bước tính vẫn chọn ở bảng lời giải nếu cần.
    const clicked = await selectViaPicker(session, causalId);
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
    const scrollAfterClick = await session.eval("Math.round(window.scrollY)");
    // §0.1-1: vai trò của các dòng (kể cả dòng Kết quả của đích) đọc ở lời giải MỞ — thu gọn thì không có dòng.
    await setSolutionOpen(session, true);
    const solutionCausal = await solutionState(session);
    await setSolutionOpen(session, false);
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
    await setSolutionOpen(session, true);
    result.screenshots.solution_causal_selected = await captureElement(session, ".geo3d-loi-giai",
      join(outDir, "solution_causal_selected.png"));
    await setSolutionOpen(session, false);
    // W17 §15.5 — KHÔI PHỤC: bỏ chọn bằng nút "Bỏ chọn" của ô soi (không phải "Xem lại toàn hình",
    // vốn đặt lại camera), cuộn về ĐÚNG vị trí trung tính, rồi so camera · lựa chọn · cuộn · khung.
    const causalSelected = { ...await jsonEval(session, CAMERA_CUON), canvas_sha256: causalAfterFrame.sha256,
      scroll_y_after_click: scrollAfterClick };
    // W4: ô soi là `BangNoi` — `.geo3d-soi-dong` nay là lớp chung của MỌI nút đầu bảng (thu gọn, về mặc định, đóng);
    // nút bỏ chọn được gọi bằng tên.
    await trustedClick(session, "document.querySelector('.geo3d-soi [aria-label=\"Bỏ chọn\"]')");
    await pollUntil(() => session.eval("window.__geo3d_selected_id||null"), (id) => id === null,
      { timeoutMs: 5_000 });
    await session.eval(`(()=>{window.scrollTo(0,${causalNeutral.scroll_y});return true})()`);
    await new Promise((done) => setTimeout(done, 300));
    const restoredFrame = await khungOnDinh(session);
    const causalRestored = { ...await jsonEval(session, CAMERA_CUON), canvas_sha256: restoredFrame.sha256,
      canvas_stable: restoredFrame.stable };
    // Khác byte ⇒ đo độ lệch kênh (nhiễu chụp ≤ NHIEU_KHUNG_TOI_DA, §15.5) và LƯU cả hai khung để xem lại.
    const savedFrames = restoredFrame.sha256 === causalBeforeFrame.sha256 ? []
      : [["causal_restore_neutral_frame.png", causalBeforeFrame], ["causal_restore_restored_frame.png", restoredFrame]];
    for (const [ten, khung] of savedFrames) writeFileSync(join(outDir, ten), Buffer.from(khung.encoded, "base64"));
    const canvasDelta = savedFrames.length ? await kenhLech(session, causalBeforeFrame, restoredFrame) : undefined;
    result.causal_restore = { neutral: { ...causalNeutral, camera: undefined },
      selected: { ...causalSelected, camera: undefined }, restored: { ...causalRestored, camera: undefined },
      saved_frames: savedFrames.map(([ten]) => ten),
      ...assessCausalRestore({ neutral: causalNeutral, selected: causalSelected, restored: causalRestored,
        canvasDelta }) };
    result.assertions.causal_restore = assertion(result.causal_restore.pass, result.causal_restore.reason_codes);
    result.screenshots.causal_restored = await capture(session, join(outDir, "causal_restored.png"));
    result.capture_order.push("causal_restored");
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
      // W17 §15.5 — xoay quỹ đạo: nhãn số đo đặt lại, vẫn đủ luật ở góc nhìn mới.
      const annXoay = await annotationState(session);
      const neoXoay = await anchorNow(session, scene);
      result.annotations.rotated = assessAnnotationBoxes({ scene, step: neoXoay, boxes: annXoay.boxes,
        points: annXoay.points, camera: annXoay.camera,
        mustShow: annotationsMustShow(scene, expectedAnnotationIds(scene, neoXoay), viewport.width < 768) });
      result.assertions.annotations_rotated = assertion(result.annotations.rotated.pass, result.annotations.rotated);
      await clickText(session, "Xem lại toàn hình");
    }
    if (viewport.width >= 768) {
      // W17 §15.5 — đổi cỡ (70 % bề rộng) + DPR 2: nhãn đặt lại trong khung mới. Camera KHÔNG tự
      // đặt lại khi đổi cỡ, nên phần rìa hình có thể ra ngoài: chỉ đáp số bắt buộc hiện.
      await session.setViewport({ width: Math.round(viewport.width * 0.7), height: viewport.height, dpr: 2 });
      await settleOrRecord(session, result, "annotations_resized");
      const annCo = await annotationState(session);
      const neoCo = await anchorNow(session, scene);
      result.annotations.resized = assessAnnotationBoxes({ scene, step: neoCo, boxes: annCo.boxes,
        points: annCo.points, camera: annCo.camera,
        mustShow: annotationsMustShow(scene, expectedAnnotationIds(scene, neoCo), true) });
      result.annotations.resized.viewport = { width: annCo.camera?.viewport_width, height: annCo.camera?.viewport_height,
        dpr: annCo.camera?.device_pixel_ratio };
      result.assertions.annotations_resized = assertion(result.annotations.resized.pass, result.annotations.resized);
      result.screenshots.annotations_resized = await capture(session, join(outDir, "annotations_resized.png"));
      await session.setViewport(null);
      await settleOrRecord(session, result, "annotations_size_restored");
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

    result.section_fill = await sectionFillEvidence(session, scene);
    if (result.section_fill !== undefined) {
      result.assertions.section_fill = assertion(result.section_fill.pass, result.section_fill);
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
      quantity_picker: result.quantity_picker,
      steps_panel: viewport.formation ? result.formation.steps_panel : undefined,
      role_colors: roleColors,
      canvas_role_hues: causal.visual.canvas_role_hues,
      panel_over_canvas: result.solution_final.panel_over_canvas,
      capture_order: result.capture_order,
      formation_required: Boolean(viewport.formation),
      formation: viewport.formation
        ? result.formation.trace
        : { pass: true, future_object_leakage: [] },
      raw_token_leakage: result.raw_token_leakage,
      section_fill: result.section_fill,
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
  } catch (error) {
    // W18 (tiêm lỗi FW2 lượt 1 làm cả suite chết, không bằng chứng): một lượt ném lỗi là MỘT KẾT LUẬN —
    // FAIL kèm nguyên nhân, giữ phần đã đo; các họ/khổ khác vẫn chạy và bằng chứng vẫn được ghi.
    result.run_error = String(error?.stack ?? error).slice(0, 2000);
    result.assertions.run_completed = assertion(false, String(error?.message ?? error).slice(0, 300));
    result.pass = false;
    return result;
  } finally {
    await session.close();
  }
}

export async function runNegative({ port, viewport, fixture, expected, outDir }) {
  const { session, analyzeCalls, apiEvents } = await openFixture({ port, viewport, fixture });
  try {
    await pollUntil(() => session.eval(`!!document.querySelector('.refusal-facts')`), Boolean);
    // W16 §14.5: hộp của ĐOẠN LỜI từ chối (px CSS, toạ độ khung nhìn = toạ độ ảnh chụp) —
    // bộ dựng sheet kiểm có chữ trong đúng hộp ấy, không chỉ kiểm tệp tồn tại.
    // cuboid-final-review: nhãn "Loại vấn đề" (dd thứ hai của thẻ) đọc ra để kỳ vọng tuỳ chọn `problem_label`.
    const observed = await jsonEval(session, `(()=>{const s=window.__ALGO_SIM_STORE__?.getState?.();`
      + `const p=document.querySelector('.refusal-facts')?.closest('section')?.querySelector('p');`
      + `const r=p?p.getBoundingClientRect():null;`
      + `const dd=[...document.querySelectorAll('.refusal-facts dd')].map(e=>e.textContent.trim());`
      + `return{unsupported:s?.unsupported||null,canvas:!!document.querySelector('.geo3d-canvas canvas'),`
      + `stageLabel:dd[0]??null,problemLabel:dd[1]??null,`
      + `active:!!s?.active,body:document.body.innerText,scrollWidth:document.documentElement.scrollWidth,`
      + `viewportWidth:window.innerWidth,`
      + `refusalMessageBox:r?{x:r.left,y:r.top,w:r.width,h:r.height}:null}})()`);
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
    // W17 §15.3: nguyên nhân có cấu trúc; chỉ nguyên nhân SOURCE mới được bảo học sinh sửa đề — ở
    // BẤT KỲ chữ nào trên trang (lời từ chối lẫn câu gợi ý), không riêng `learner_reason`.
    const nguyenNhan = observed.unsupported?.refusal_cause ?? null;
    const baoSuaDe = BAO_SUA_DE.filter((cum) => observed.body.includes(cum));
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
      refusal_cause: assertion(!expected.refusal_cause || nguyenNhan === expected.refusal_cause,
        { expected: expected.refusal_cause ?? null, actual: nguyenNhan }),
      problem_label: assertion(!expected.problem_label || observed.problemLabel === expected.problem_label,
        { expected: expected.problem_label ?? null, actual: observed.problemLabel }),
      no_fix_text_advice_without_source_cause: assertion(nguyenNhan === "SOURCE" || baoSuaDe.length === 0,
        { refusal_cause: nguyenNhan, phrases: baoSuaDe }),
      single_analyze_call: assertion(analyzeCalls() === 1, analyzeCalls()),
      no_uncaught_exception: assertion(uncaught.length === 0, uncaught),
      no_failed_api_call: assertion(failedApiCalls.length === 0, failedApiCalls),
      no_serious_console_error: assertion(seriousConsole.length === 0, seriousConsole),
    };
    return {
      viewport, assertions, observed: { ...observed, body: undefined, refusalMessageBox: undefined }, screenshot,
      refusal_message_box: observed.refusalMessageBox,
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

/** W17 §15.3: cụm chữ bảo học sinh viết/sửa lại đề — chỉ hợp lệ khi nguyên nhân là SOURCE. */
const BAO_SUA_DE = ["diễn đạt lại", "kiểm tra lại đề", "đối chiếu lại các số liệu trong đề", "sửa đề",
  "nêu rõ hình"];

/** W17: ca PHỤC VỤ thêm của một kịch bản (vd mặt phẳng ĐÚNG khi đề có hai mặt phẳng) — phục vụ,
 *  đáp số ở mục Kết quả, nhãn số đo của đáp số có mặt, không lỗi; không chạy cả bộ kiểm dương. */
export async function runServed({ port, viewport, fixture, expected, outDir }) {
  const { session, analyzeCalls, apiEvents } = await openFixture({ port, viewport, fixture });
  try {
    await pollUntil(() => session.eval(`!!document.querySelector('.geo3d-canvas canvas')`), Boolean);
    await goToEnd(session);
    // §0.1-2: đáp số đọc qua ngăn «Đại lượng» (card Kết quả ẩn khi lời giải thu gọn).
    const ngan = await pollUntil(() => quantityDrawer(session),
      (d) => d.some((x) => x.text.includes(expected.answer)), { timeoutMs: 8_000 });
    const ketQua = ngan.filter((x) => x.sec === "Kết quả").map((x) => x.text).join(" ");
    // W18 §16.5: nhãn đáp số hiện khi người học CHỌN nó (mặc định gọn) — chọn trong ngăn (tự đóng).
    // W3 · H-W2-2: đoạn mà đề hỏi độ dài được dựng (formation) ⇒ kỳ vọng W18 `annotation_id` khôi phục cho mọi ca.
    if (expected.annotation_id) await selectViaPicker(session, expected.annotation_id);
    else await closeQuantityDrawer(session);
    const ann = await pollUntil(() => annotationState(session),
      (s) => !expected.annotation_id || (s.dom.includes(expected.annotation_id)
        && (!expected.witness || s.witness.includes(expected.annotation_id))), { timeoutMs: 5_000 })
      .catch(() => annotationState(session));
    const screenshot = await capture(session, join(outDir, "served.png"));
    const uncaught = session.consoleEvents.filter((event) => event.loai === "exception");
    const failedApiCalls = apiEvents().filter((event) => event.status >= 400);
    const assertions = {
      answer_shown: assertion(String(ketQua).includes(expected.answer), { answer: expected.answer }),
      annotation_present: assertion(!expected.annotation_id || ann.dom.includes(expected.annotation_id), ann.dom),
      witness_drawn: assertion(!expected.witness || ann.witness.includes(expected.annotation_id), ann.witness),
      single_analyze_call: assertion(analyzeCalls() === 1, analyzeCalls()),
      no_uncaught_exception: assertion(uncaught.length === 0, uncaught),
      no_failed_api_call: assertion(failedApiCalls.length === 0, failedApiCalls),
    };
    return { viewport, assertions, screenshot, pass: Object.values(assertions).every((item) => item.pass) };
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
      // W15: ba loại từ chối mỗi họ, mỗi loại một kỳ vọng mã riêng (`KIEU_TU_CHOI`).
      for (const am of scenario.negative_fixtures) {
        const negative = JSON.parse(readFileSync(join(root, am.fixture), "utf-8"));
        record.negative[am.kind] = {};
        for (const viewport of suite.viewports) {
          record.negative[am.kind][viewport.id] = await runNegative({
            port: cong,
            viewport,
            fixture: negative,
            expected: am.expected,
            outDir: join(scenarioOut, "negative", am.kind, viewport.id),
          });
        }
      }
      // W17: ca phục vụ thêm (mặt phẳng ĐÚNG đi cùng ca lệch phép dựng).
      record.served = {};
      for (const ca of scenario.served_fixtures ?? []) {
        const served = JSON.parse(readFileSync(join(root, ca.fixture), "utf-8"));
        record.served[ca.kind] = {};
        for (const viewport of suite.viewports) {
          record.served[ca.kind][viewport.id] = await runServed({
            port: cong, viewport, fixture: served, expected: ca.expected,
            outDir: join(scenarioOut, "served", ca.kind, viewport.id),
          });
        }
      }
      record.pass = Object.values(record.positive).every((item) => item.pass)
        && Object.values(record.negative).every((kind) => Object.values(kind).every((item) => item.pass))
        && Object.values(record.served).every((kind) => Object.values(kind).every((item) => item.pass));
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
