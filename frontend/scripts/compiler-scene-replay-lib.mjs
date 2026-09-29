import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { relative, resolve } from "node:path";

// Bộ đo góc nhìn của CHÍNH sản phẩm (Node ≥ 22.18 bóc kiểu TS; hai module này
// không import gì) — không một định nghĩa thứ hai trong bộ đo.
import { cauTrucGocNhin } from "../src/simulations/domains/geometry/scene3d-model.ts";
import {
  GOC_NHIN_THAM_CHIEU, HUONG, NGUONG_GOC_NHIN, danhGiaGocNhin, datNguong, doLuoiGocNhin,
} from "../src/simulations/domains/geometry/scene3d-camera.ts";

const cameraModules = { cauTrucGocNhin, danhGiaGocNhin, datNguong, doLuoiGocNhin, NGUONG_GOC_NHIN };

export const sortedUnique = (values) => [...new Set(values ?? [])].sort();

export function setDiff(expected, actual) {
  const left = sortedUnique(expected);
  const right = sortedUnique(actual);
  return {
    missing: left.filter((id) => !right.includes(id)),
    unexpected: right.filter((id) => !left.includes(id)),
  };
}

function comparePair(leftName, left, rightName, right) {
  const diff = setDiff(left, right);
  return {
    left: leftName,
    right: rightName,
    missing: diff.missing,
    unexpected: diff.unexpected,
    pass: diff.missing.length === 0 && diff.unexpected.length === 0,
  };
}

export function compareClosures(oracle, declared, observed) {
  const sets = {
    oracle_expected_closure: sortedUnique(oracle),
    event_declared_closure: sortedUnique(declared),
    browser_observed_closure: sortedUnique(observed),
  };
  const pairs = {
    oracle_vs_event: comparePair(
      "oracle_expected_closure", sets.oracle_expected_closure,
      "event_declared_closure", sets.event_declared_closure,
    ),
    oracle_vs_browser: comparePair(
      "oracle_expected_closure", sets.oracle_expected_closure,
      "browser_observed_closure", sets.browser_observed_closure,
    ),
    event_vs_browser: comparePair(
      "event_declared_closure", sets.event_declared_closure,
      "browser_observed_closure", sets.browser_observed_closure,
    ),
  };
  return { ...sets, pairs, pass: Object.values(pairs).every((p) => p.pass) };
}

export function eventDeclaredClosure(events, targetId) {
  const dependencies = new Map();
  for (const event of events ?? []) {
    const objectIds = Array.isArray(event.objects)
      ? event.objects
      : event.object ? [event.object] : [];
    for (const objectId of objectIds) {
      const next = sortedUnique(event.depends);
      if (dependencies.has(objectId)) {
        const before = dependencies.get(objectId);
        if (JSON.stringify(before) !== JSON.stringify(next)) {
          throw new Error(`EVENT_DEPENDENCY_CONFLICT:${objectId}`);
        }
      } else {
        dependencies.set(objectId, next);
      }
    }
  }
  const seen = new Set();
  const queue = [targetId];
  while (queue.length > 0) {
    const id = queue.shift();
    if (!id || seen.has(id)) continue;
    seen.add(id);
    queue.push(...(dependencies.get(id) ?? []));
  }
  return sortedUnique(seen);
}

export function solidTopology(scene) {
  const solid = (scene?.objects ?? []).find((object) => object.type === "solid");
  if (!solid) return { vertices: 0, edges: 0, faces: 0, euler: null };
  const edges = new Set();
  for (const face of solid.faces ?? []) {
    for (let index = 0; index < face.length; index += 1) {
      const a = face[index];
      const b = face[(index + 1) % face.length];
      edges.add(a < b ? `${a}:${b}` : `${b}:${a}`);
    }
  }
  const vertices = (solid.vertex_ids ?? solid.vertices ?? []).length;
  const faces = (solid.faces ?? []).length;
  return { vertices, edges: edges.size, faces, euler: vertices - edges.size + faces };
}

/* ─── ORBIT CHỌN TRƯỚC (w10) ────────────────────────────────────────────────
 * Cú kéo pixel cố định (w09) có thể dừng ở một góc ép dẹt hình, hoặc không đổi
 * cạnh khuất nào — và cổng chờ một điều không bao giờ tới (ORBIT_EVIDENCE_
 * TIMEOUT). Ở đây góc xoay quanh Z được CHỌN TRƯỚC: đạt ngưỡng góc nhìn của
 * chính sản phẩm (`scene3d-camera.ts`) VÀ đổi tập cạnh khuất dự đoán. Dự đoán
 * dùng mặt trước/sau của khối lồi — chỉ để chọn cử chỉ; phán quyết vẫn là tập
 * cạnh sản phẩm báo ra. */
const num = (s) => { const [a, b] = String(s).split("/"); return b ? Number(a) / Number(b) : Number(a); };

function predictedHidden(scene, d) {
  const hidden = [];
  for (const solid of (scene.objects ?? []).filter((o) => o.type === "solid" && o.faces)) {
    const p = solid.vertices.map((v) => v.map(num));
    const c = p.reduce((s, q) => s.map((x, i) => x + q[i] / p.length), [0, 0, 0]);
    const back = solid.faces.map((f) => {
      const [a, b, e] = [p[f[0]], p[f[1]], p[f[2]]];
      const u = b.map((x, i) => x - a[i]);
      const v = e.map((x, i) => x - a[i]);
      let n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
      if (n.reduce((s, x, i) => s + x * (a[i] - c[i]), 0) < 0) n = n.map((x) => -x);
      return n.reduce((s, x, i) => s + x * d[i], 0) < 0;
    });
    const adj = new Map();
    solid.faces.forEach((f, k) => f.forEach((ia, i) => {
      const ib = f[(i + 1) % f.length];
      const key = [solid.vertex_ids[Math.min(ia, ib)], solid.vertex_ids[Math.max(ia, ib)]].join("-");
      adj.set(key, [...(adj.get(key) ?? []), k]);
    }));
    for (const [key, faces] of adj) if (faces.every((k) => back[k])) hidden.push(key);
  }
  return hidden.sort();
}

/** Góc xoay ứng viên, TẤT ĐỊNH: |góc| 30°–150° bước 5°, gần 60° trước, dương
 *  trước âm. Đủ lớn để ảnh xoay khác hẳn khung mặc định. */
export const ORBIT_OFFSETS_DEG = Array.from({ length: 25 }, (_, i) => 30 + 5 * i)
  .sort((a, b) => Math.abs(a - 60) - Math.abs(b - 60) || a - b).flatMap((a) => [a, -a]);

/** Khung "đã xoay" (w10): hình vẫn choán, có độ sâu, không mặt ép thành đường. */
export function hasDepth(q, tran, nguong = cameraModules.NGUONG_GOC_NHIN) {
  return q.dienTichBao >= nguong.tiLeDienTichBao * tran.dienTichBao
    && q.doSau >= nguong.tiLeDoSau * tran.doSau
    && q.matNghiengMin >= nguong.matNghiengMin;
}

/* ─── ẢNH XOAY KHÔNG SUY BIẾN (w11, review W10-H4) ─────────────────────────
 * Ảnh xoay w10 chỉ cần `hasDepth` và đã nhận A nằm trên SC, S–A–B gần thẳng
 * hàng. Cổng này đo trên các ĐỈNH KHỐI (đỉnh chủ chốt, không kể điểm thiết
 * diện): choán + sâu như cũ; mặt khối ≥ 12° so với tia nhìn; không bộ ba đỉnh
 * nào gần thẳng hàng hơn, và không đỉnh nào sát cạnh hơn, so với khối lập
 * phương tham chiếu ở hướng mặc định cũ (`HUONG` — cùng tham chiếu của
 * `NGUONG_GOC_NHIN`). */
const _tru = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const _cheo = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const _tich = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const _chuan = (a) => { const d = Math.hypot(...a) || 1; return a.map((x) => x / d); };

/** Chiều cao nhỏ nhất (chia bán kính cảnh) của các tam giác chiếu từ mọi bộ ba
 *  đỉnh KHÔNG thẳng hàng trong 3D — nhỏ ⇔ ba đỉnh gần thẳng hàng trên ảnh. */
export function baDinhGanThangHang(diem, huong) {
  const d = _chuan(huong);
  const phai = _chuan(Math.abs(d[2]) > 0.999 ? _cheo([0, 1, 0], d) : _cheo([0, 0, 1], d));
  const len = _cheo(d, phai);
  const tam = diem.reduce((s, p) => s.map((x, i) => x + p[i] / diem.length), [0, 0, 0]);
  const R = Math.max(1e-9, ...diem.map((p) => Math.hypot(..._tru(p, tam))));
  const uv = diem.map((p) => [_tich(_tru(p, tam), phai) / R, _tich(_tru(p, tam), len) / R]);
  let min = Infinity;
  let bo = null;
  for (let i = 0; i < diem.length; i += 1) {
    for (let j = i + 1; j < diem.length; j += 1) {
      for (let k = j + 1; k < diem.length; k += 1) {
        if (Math.hypot(..._cheo(_tru(diem[j], diem[i]), _tru(diem[k], diem[i]))) < 1e-9 * R * R) continue;
        const [a, b, c] = [uv[i], uv[j], uv[k]];
        const s2 = Math.abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]));
        const dai = Math.max(Math.hypot(b[0] - a[0], b[1] - a[1]), Math.hypot(c[0] - a[0], c[1] - a[1]),
          Math.hypot(c[0] - b[0], c[1] - b[1]));
        if (s2 / dai < min) { min = s2 / dai; bo = [i, j, k]; }
      }
    }
  }
  return { min: Number.isFinite(min) ? min : 1, triple: bo };
}

const _LP = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]];
export const NGUONG_ANH_XOAY = {
  tiLeDienTich: 0.6,
  tiLeDoSau: 0.5,
  matNghiengDo: 12,
  baDinhMin: baDinhGanThangHang(_LP, [...HUONG]).min,
  dinhCanhMin: 0.5 * GOC_NHIN_THAM_CHIEU.khoangDinhCanhMin,
};

/** Đỉnh / cạnh / mặt của mọi KHỐI trong cảnh — các đỉnh chủ chốt. */
export function cauTrucKhoi(scene) {
  const diem = [];
  const ten = [];
  const canh = new Map();
  const mat = [];
  for (const k of (scene?.objects ?? []).filter((o) => o.type === "solid" && o.vertices && o.faces)) {
    const goc = diem.length;
    k.vertices.forEach((v, i) => { diem.push(v.map(num)); ten.push(k.vertex_ids?.[i] ?? `${k.id}#${i}`); });
    for (const f of k.faces) {
      mat.push(f.map((i) => goc + i));
      f.forEach((a, i) => {
        const [x, y] = [goc + a, goc + f[(i + 1) % f.length]].sort((p, q) => p - q);
        canh.set(`${x}:${y}`, [x, y]);
      });
    }
  }
  return { diem, ten, canh: [...canh.values()], mat };
}

const _khoiDaDo = new WeakMap();   // cảnh → cấu trúc khối + cực đại lưới (đo một lần)

/** Cổng ảnh xoay trên HƯỚNG (tâm → camera). Ghi số đo và từng lý do trượt. */
export function danhGiaAnhXoay(scene, huong, camera = cameraModules) {
  if (!_khoiDaDo.has(scene)) {
    const k = cauTrucKhoi(scene);
    _khoiDaDo.set(scene, { ...k, tran: k.diem.length < 3 ? null : camera.doLuoiGocNhin(k.diem, k.canh, k.mat).tran });
  }
  const { diem, ten, canh, mat, tran } = _khoiDaDo.get(scene);
  if (diem.length < 3) return { pass: true, failures: [], metrics: null };
  const q = camera.danhGiaGocNhin(diem, canh, mat, huong);
  const ba = baDinhGanThangHang(diem, huong);
  const metrics = {
    dien_tich_ti_le: q.dienTichBao / (tran.dienTichBao || 1),
    do_sau_ti_le: q.doSau / (tran.doSau || 1),
    mat_nghieng_min_do: (Math.asin(Math.min(1, q.matNghiengMin)) * 180) / Math.PI,
    ba_dinh_min: ba.min,
    ba_dinh_gan_thang_hang: ba.triple?.map((i) => ten[i]) ?? null,
    dinh_canh_min: q.khoangDinhCanhMin,
  };
  const n = NGUONG_ANH_XOAY;
  const failures = [
    metrics.dien_tich_ti_le < n.tiLeDienTich && "PROJECTED_AREA_TOO_SMALL",
    metrics.do_sau_ti_le < n.tiLeDoSau && "DEPTH_TOO_SHALLOW",
    metrics.mat_nghieng_min_do < n.matNghiengDo && "FACE_NEAR_EDGE_ON",
    metrics.ba_dinh_min < n.baDinhMin && "THREE_KEY_VERTICES_NEAR_COLLINEAR",
    metrics.dinh_canh_min < n.dinhCanhMin && "VERTEX_ON_FOREIGN_EDGE",
  ].filter(Boolean);
  return { pass: failures.length === 0, failures, metrics };
}

const _xoayZ = (d, doXoay) => {
  const a = (doXoay * Math.PI) / 180;
  return [d[0] * Math.cos(a) - d[1] * Math.sin(a), d[0] * Math.sin(a) + d[1] * Math.cos(a), d[2]];
};

/** MỌI góc xoay đạt cổng VÀ đổi tập cạnh khuất dự đoán, theo thứ tự ứng viên. */
export function orbitCandidates(scene, direction, { offsets = ORBIT_OFFSETS_DEG, camera = cameraModules } = {}) {
  const before = predictedHidden(scene, direction);
  const ra = [];
  for (const offset of offsets) {
    const d = _xoayZ(direction, offset);
    const gate = danhGiaAnhXoay(scene, d, camera);
    const after = predictedHidden(scene, d);
    if (gate.pass && JSON.stringify(after) !== JSON.stringify(before)) {
      ra.push({ offset_deg: offset, direction_after: d, gate,
        predicted_hidden_before: before, predicted_hidden_after: after });
    }
  }
  return ra;
}

export function planOrbit(scene, direction, options = {}) {
  const ra = orbitCandidates(scene, direction, options);
  return ra.length ? { ...ra[0], candidate_offsets_deg: ra.map((c) => c.offset_deg) } : null;
}

/** Điểm thế giới → px CSS trong canvas, bằng ma trận camera THẬT (cột-trước). */
export function chieuManHinh(snapshot, p) {
  const nhan = (m, v) => [0, 1, 2, 3].map((r) => m[r] * v[0] + m[4 + r] * v[1] + m[8 + r] * v[2] + m[12 + r] * v[3]);
  const c = nhan(snapshot.projection_matrix_column_major,
    nhan(snapshot.view_matrix_column_major, [p[0], p[1], p[2], 1]));
  return { x: ((c[0] / c[3] + 1) / 2) * snapshot.viewport_width,
    y: ((1 - c[1] / c[3]) / 2) * snapshot.viewport_height, behind: c[3] <= 0 };
}

/** Cổng ảnh xoay trên camera THẬT sau cử chỉ: số đo hướng + mọi đỉnh khối (và
 *  chỗ nhãn của nó) nằm trong khung, không dưới lớp phủ (`overlays`: hộp px CSS
 *  tương đối canvas — thanh số đo, nút nổi, ô soi). */
export function danhGiaAnhXoayThuc(scene, snapshot, overlays = []) {
  const m = snapshot.view_matrix_column_major;
  const gate = danhGiaAnhXoay(scene, [m[2], m[6], m[10]]);
  const { diem, ten } = cauTrucKhoi(scene);
  const le = 0.03 * Math.min(snapshot.viewport_width, snapshot.viewport_height);
  const trong = (s, r) => s.x >= r.x && s.x <= r.x + r.w && s.y >= r.y && s.y <= r.y + r.h;
  const lech = [];
  diem.forEach((p, i) => {
    const s = chieuManHinh(snapshot, p);
    const nhan = { x: s.x, y: s.y - 18 };   // nhãn đặt ngay trên đỉnh
    if (s.behind || s.x < le || s.y < le || s.x > snapshot.viewport_width - le
        || s.y > snapshot.viewport_height - le) lech.push({ vertex: ten[i], reason: "OUTSIDE_CANVAS", ...s });
    else if (overlays.some((r) => trong(s, r) || trong(nhan, r))) lech.push({ vertex: ten[i], reason: "UNDER_OVERLAY", ...s });
  });
  const failures = [...gate.failures, ...(lech.length ? ["KEY_VERTEX_NOT_READABLE"] : [])];
  return { pass: failures.length === 0, failures, metrics: gate.metrics, unreadable_vertices: lech };
}

/** Tầng causal kỳ vọng (w11), tính ĐỘC LẬP với `tangNhanManh`: bao đóng qua
 *  `depends`; chuỗi số qua cạnh `numerical`; gốc tự do trong chuỗi số là dữ
 *  kiện số, còn lại trong chuỗi số là trung gian, ngoài chuỗi số là ngữ cảnh. */
export function expectedCausalTiers(scene, id) {
  const byId = new Map((scene?.objects ?? []).map((o) => [o.id, o]));
  const dong = (next) => {
    const thay = new Set();
    const hang = [id];
    while (hang.length) {
      for (const x of next(byId.get(hang.shift()))) {
        if (x !== id && !thay.has(x)) { thay.add(x); hang.push(x); }
      }
    }
    return thay;
  };
  const tatCa = dong((o) => o?.depends ?? []);
  const so = dong((o) => (o?.dependency_edges ?? []).filter((e) => e.relation === "numerical").map((e) => e.source_id));
  const ra = { [id]: "dich" };
  for (const x of tatCa) ra[x] = !so.has(x) ? "boi_canh" : byId.get(x)?.origin === "free" ? "du_kien_so" : "trung_gian";
  return ra;
}

/** Lớp CSS mà một dòng số đo phải mang theo tầng của nó. */
export const LOP_SO_DO_THEO_TANG = { dich: "la-chon", du_kien_so: "la-so-lieu", trung_gian: "la-trung-gian" };

/** Đường kính px CSS của từng chấm đỉnh, đo bằng ma trận camera — không đọc
 *  con số renderer tự báo. */
export function doCoDauDinh(snapshot, markers) {
  const m = snapshot.view_matrix_column_major;
  const phai = [m[0], m[4], m[8]];
  return markers.map((k) => {
    const a = chieuManHinh(snapshot, k.center);
    const b = chieuManHinh(snapshot, k.center.map((x, i) => x + phai[i] * k.radius_world));
    return { id: k.id, state: k.state, diameter_px: 2 * Math.hypot(b.x - a.x, b.y - a.y) };
  });
}

/** Bước ĐO không được làm hình học xuất hiện hay biến mất: tập vật HÌNH HỌC
 *  thấy được ở bước đo trùng bước liền trước (review W10: formation). */
export function measurementStepsKeepGeometry(scene) {
  const byId = new Map((scene?.objects ?? []).map((o) => [o.id, o]));
  const hinh = (k) => sortedUnique(expectedVisibleIds(scene, k).filter((x) => byId.get(x)?.type !== "quantity"));
  const lech = [];
  for (const e of scene?.events ?? []) {
    if (!["MEASUREMENT", "FINAL_RESULT"].includes(e.semantic_kind) || !e.step_index) continue;
    const diff = setDiff(hinh(e.step_index - 1), hinh(e.step_index));
    if (diff.missing.length || diff.unexpected.length) lech.push({ step: e.step_index, ...diff });
  }
  return { pass: lech.length === 0, mismatches: lech };
}

/** Bí danh KHÔNG hiện ở đâu (bí danh đáp số, `render: "non_visual"`). Bí danh
 *  vẫn hiện — AD := AB ở hình lập phương — là một vật bình thường của cây. */
export const isHiddenAlias = (o) => Boolean(o?.alias_of) && o.render === "non_visual";

/** Bí danh đáp số (w10) không có dòng riêng trong cây: số dòng mang nhãn của
 *  nó phải bằng số vật khác cùng nhãn (1 khi mượn nhãn nguồn, 0 khi có nhãn
 *  riêng). Cây nhận dạng theo nhãn nên đây là cách đếm duy nhất đúng. */
export function aliasTreeRowCheck(scene, alias, rows) {
  const matches = rows.filter((row) => row.text === alias.label).length;
  const owners = (scene?.objects ?? []).filter((o) => !isHiddenAlias(o) && o.label === alias.label).length;
  return { id: alias.id, label: alias.label, alias_of: alias.alias_of, matches,
    expected_rows: owners, observed_present: null, pass: matches === owners };
}

export function assessCssReadiness(actual, baseline, scrollWidth, viewportWidth) {
  const checks = {
    scene_layout: Boolean(actual.scene)
      && actual.scene.display === "flex" && actual.scene.width > 100,
    canvas_layout: Boolean(actual.box)
      && ["relative", "absolute"].includes(actual.box.position),
    canvas_size: Boolean(actual.canvas)
      && actual.canvas.width > 100 && actual.canvas.height > 100
      && actual.canvas.width <= actual.box.width + 2
      && actual.canvas.height <= actual.box.height + 2,
    controls_styled: Boolean(actual.controls && actual.controlButton && actual.controlText)
      && actual.controls.display !== baseline.div.display
      && actual.controls.fontFamily !== baseline.div.fontFamily
      && actual.controlText.color !== baseline.span.color,
    readout_styled: Boolean(actual.readout && actual.readoutText)
      && actual.readout.position !== baseline.ul.position
      && actual.readout.fontFamily !== baseline.ul.fontFamily
      && actual.readoutText.color !== baseline.span.color,
    no_document_overflow: scrollWidth <= viewportWidth + 1,
  };
  return { checks, pass: Object.values(checks).every(Boolean) };
}

export function expectedVisibleIds(scene, step) {
  const formationStep = scene?.formation?.steps?.[step];
  if (formationStep && Array.isArray(formationStep.visible_ids)) {
    return sortedUnique(formationStep.visible_ids);
  }
  const visible = new Set(scene?.free_objects ?? []);
  for (const event of scene?.events ?? []) {
    if ((event.step_index ?? 0) > step) continue;
    if (Array.isArray(event.objects)) event.objects.forEach((id) => visible.add(id));
    else if (event.object) visible.add(event.object);
  }
  return sortedUnique([...visible].filter((id) =>
    (scene?.objects ?? []).some((object) => object.id === id)));
}

const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export function detectRawTokenLeakage(scene, visibleText) {
  const candidates = new Set();
  for (const object of scene?.objects ?? []) {
    for (const value of [object.id, object.type, object.render]) {
      if (typeof value === "string" && value.includes("_")) candidates.add(value);
    }
  }
  const leakedTokens = [...candidates].filter((token) =>
    new RegExp(`(^|[^\\p{L}\\p{N}_])${escapeRegex(token)}($|[^\\p{L}\\p{N}_])`, "u")
      .test(String(visibleText ?? "")));
  const snakeTokens = String(visibleText ?? "").match(/\b[\p{L}\p{N}]+_[\p{L}\p{N}_]+\b/gu) ?? [];
  const leaked = sortedUnique([...leakedTokens, ...snakeTokens]);
  return { leaked_tokens: leaked, pass: leaked.length === 0 };
}

export function validateFormulaReferences(scene) {
  const ids = new Set((scene?.objects ?? []).map((object) => object.id));
  const unresolved = [];
  for (const object of scene?.objects ?? []) {
    const formula = object.formula;
    if (!formula) continue;
    for (const reference of formula.references ?? []) {
      if (!ids.has(reference.entity_id)
          || !String(reference.display_label ?? "").trim()) {
        unresolved.push({ object_id: object.id, reference });
      }
    }
  }
  return { unresolved, pass: unresolved.length === 0 };
}

export function assessFormationSnapshots(scene, observations) {
  const expectedSteps = scene?.formation?.steps ?? [];
  const forward = observations?.forward ?? [];
  const backward = observations?.backward ?? [];
  const mismatch = [];
  // Bí danh đáp số (w10) là MỘT kết luận với nguồn, không có dòng riêng trong
  // cây ⇒ không phải vật quan sát được; nguồn của nó vẫn được kiểm như mọi vật.
  const aliases = new Set((scene?.objects ?? []).filter(isHiddenAlias).map((o) => o.id));
  for (const observation of [...forward, ...backward]) {
    const expected = expectedVisibleIds(scene, observation.index).filter((id) => !aliases.has(id));
    const diff = setDiff(expected, observation.visible_ids);
    if (diff.missing.length || diff.unexpected.length) {
      mismatch.push({ index: observation.index, direction: observation.direction, ...diff });
    }
  }
  const forwardOrder = forward.map((item) => item.index);
  const backwardOrder = backward.map((item) => item.index);
  const expectedForward = expectedSteps.map((_, index) => index);
  const expectedBackward = [...expectedForward].reverse();
  return {
    mismatch,
    forward_complete: JSON.stringify(forwardOrder) === JSON.stringify(expectedForward),
    backward_complete: JSON.stringify(backwardOrder) === JSON.stringify(expectedBackward),
    future_object_leakage: mismatch.flatMap((item) => item.unexpected),
    pass: mismatch.length === 0
      && JSON.stringify(forwardOrder) === JSON.stringify(expectedForward)
      && JSON.stringify(backwardOrder) === JSON.stringify(expectedBackward),
  };
}

export function evaluateEvidenceGates(facts) {
  const reasons = [];
  if ((facts.edge?.visible_edge_ids ?? []).length === 0) reasons.push("VISIBLE_EDGE_IDS_EMPTY");
  if ((facts.edge?.hidden_edge_ids ?? []).length === 0) reasons.push("HIDDEN_EDGE_IDS_EMPTY");
  if ((facts.edge?.mixed_edge_ids ?? []).length > 0) reasons.push("MIXED_EDGE_POLICY");
  if ((facts.edge?.duplicate_visual_owner_ids ?? []).length > 0) {
    reasons.push("DUPLICATE_VISUAL_OWNER");
  }
  if (facts.orbit_required && facts.orbit_visibility_changed !== true) {
    reasons.push("ORBIT_VISIBILITY_FROZEN");
  }
  if (facts.causal?.selected_changed !== true) reasons.push("CAUSAL_SELECTION_UNCHANGED");
  if (facts.causal?.closure_changed !== true) reasons.push("CAUSAL_CLOSURE_UNCHANGED");
  if (facts.orbit_required && facts.orbit_non_degenerate !== true) {
    reasons.push("ORBIT_DEGENERATE_PROJECTION");
  }
  // w11: tầng causal (đích > dữ kiện số > trung gian số > ngữ cảnh) thay cho
  // "owner cạnh đổi" — chọn một con số thì khối chỉ là ngữ cảnh, nét giữ mực.
  if (facts.causal?.tiers_match !== true) reasons.push("CAUSAL_TIERS_MISMATCH");
  if (facts.causal?.readout_classes_match !== true) reasons.push("CAUSAL_READOUT_TIER_CLASS");
  if (facts.causal?.canvas_changed !== true) reasons.push("CAUSAL_CANVAS_UNCHANGED");
  if (facts.causal?.bounded_pixel_delta !== true) reasons.push("CAUSAL_PIXEL_DELTA_UNBOUNDED");
  if (facts.causal?.dash_signature_preserved !== true) reasons.push("HIGHLIGHT_DASH_OVERWRITE");
  const order = facts.capture_order ?? [];
  const neutral = order.indexOf("neutral_final") >= 0
    ? order.indexOf("neutral_final") : order.indexOf("default");
  const causal = order.indexOf("causal_selected") >= 0
    ? order.indexOf("causal_selected") : order.indexOf("causal");
  if (neutral < 0 || causal < 0 || neutral > causal) {
    reasons.push("DEFAULT_CAPTURE_AFTER_CAUSAL");
  }
  if ((facts.formation?.future_object_leakage ?? []).length > 0) {
    reasons.push("FUTURE_OBJECT_LEAK");
  }
  if (facts.formation_required && facts.formation?.pass !== true) {
    reasons.push("FORMATION_FORWARD_BACKWARD_INCOMPLETE");
  }
  if ((facts.raw_token_leakage?.leaked_tokens ?? []).length > 0) reasons.push("RAW_TOKEN_LEAK");
  if ((facts.formula?.unresolved ?? []).length > 0) reasons.push("UNRESOLVED_FORMULA_SYMBOL");
  if (facts.causal_oracle_source !== "independent_manifest") {
    reasons.push("CAUSAL_ORACLE_NOT_INDEPENDENT");
  }
  if (facts.screenshot?.blank === true || facts.screenshot?.premature === true) {
    reasons.push("BLANK_OR_PREMATURE_SCREENSHOT");
  }
  if ((facts.uncaught_exceptions ?? []).length > 0) reasons.push("UNCAUGHT_EXCEPTION");
  if ((facts.failed_api_calls ?? []).length > 0) reasons.push("FAILED_API_CALL");
  return { reason_codes: sortedUnique(reasons), pass: reasons.length === 0 };
}

export function sha256File(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function sha256GitBlob(repoRoot, path) {
  const absolute = resolve(repoRoot, path);
  const repositoryPath = relative(repoRoot, absolute).replaceAll("\\", "/");
  if (repositoryPath === ".." || repositoryPath.startsWith("../")) {
    throw new Error(`SOURCE_OUTSIDE_REPOSITORY:${path}`);
  }
  const content = execFileSync("git", ["show", `HEAD:${repositoryPath}`], {
    cwd: repoRoot,
  });
  return createHash("sha256").update(content).digest("hex");
}

export function validateSuiteManifest(manifest, repoRoot) {
  const errors = [];
  if (manifest?.schema_version !== "generic-tier-a-suite/1") {
    errors.push("schema_version");
  }
  if (!Array.isArray(manifest?.viewports) || manifest.viewports.length !== 2) {
    errors.push("viewports");
  }
  if (!Array.isArray(manifest?.scenarios) || manifest.scenarios.length !== 6) {
    errors.push("scenarios");
  }
  const names = new Set();
  for (const scenario of manifest?.scenarios ?? []) {
    if (!scenario.id || names.has(scenario.id)) errors.push(`scenario_id:${scenario.id}`);
    names.add(scenario.id);
    if (!scenario.positive_fixture || !scenario.negative_fixture) {
      errors.push(`fixtures:${scenario.id}`);
    }
    if (!scenario.causal_target_id
        || !scenario.oracle_expected_closure?.includes(scenario.causal_target_id)) {
      errors.push(`oracle_target:${scenario.id}`);
    }
    if (!scenario.oracle_source?.path || !scenario.oracle_source?.sha256
        || scenario.oracle_source?.hash_basis !== "git_blob_at_measurement_commit") {
      errors.push(`oracle_source:${scenario.id}`);
    } else if (repoRoot) {
      if (sha256GitBlob(repoRoot, scenario.oracle_source.path)
          !== scenario.oracle_source.sha256) {
        errors.push(`oracle_source_hash:${scenario.id}`);
      }
    }
    for (const key of ["vertices", "edges", "faces", "euler"]) {
      if (typeof scenario.topology?.[key] !== "number") errors.push(`topology:${scenario.id}:${key}`);
    }
  }
  const requiredScenarios = [
    "triangular_pyramid", "triangular_prism", "rectangular_pyramid",
    "cuboid", "cube", "cross_section",
  ];
  if (JSON.stringify([...names].sort()) !== JSON.stringify(requiredScenarios.sort())) {
    errors.push("cross_family_scenarios");
  }
  if (errors.length > 0) throw new Error(`INVALID_SUITE_MANIFEST:${errors.join(",")}`);
  return true;
}

export async function pollUntil(read, predicate, {
  timeoutMs = 25_000,
  intervalMs = 100,
  now = () => Date.now(),
  pause = (ms) => new Promise((resolvePause) => setTimeout(resolvePause, ms)),
} = {}) {
  const deadline = now() + timeoutMs;
  let last;
  do {
    last = await read();
    if (predicate(last)) return last;
    await pause(intervalMs);
  } while (now() <= deadline);
  throw new Error(`POLL_TIMEOUT:${JSON.stringify(last)}`);
}

/* ─── CAMERA SETTLING (w09) ─────────────────────────────────────────────────
 * OrbitControls damping keeps rewriting the pose in its last ULPs after
 * auto-fit (mobile: every frame, forever), so "settled" cannot mean
 * byte-identical. Relative matrix motion ≤ 1e-9 moves a projected point by
 * ≤ ~1e-6 px at ≤ 2000 physical px — far below the 0.5 px oracle tolerance —
 * while any pose change a learner could see is orders of magnitude larger. */
export const CAMERA_SETTLE_TOLERANCE = 1e-9;

export function cameraMotion(a, b) {
  if (!a || !b || a.viewport_width !== b.viewport_width || a.viewport_height !== b.viewport_height
      || a.device_pixel_ratio !== b.device_pixel_ratio) return Infinity;
  let worst = 0;
  for (const key of ["view_matrix_column_major", "projection_matrix_column_major"]) {
    a[key].forEach((value, index) => {
      worst = Math.max(worst, Math.abs(value - b[key][index]) / Math.max(1, Math.abs(value)));
    });
  }
  return worst;
}

/** Poll `read()` → `{snapshot, frame_count}` until the camera has stayed within
 *  tolerance for `stableSamples` consecutive samples spanning ≥ `minFrames`
 *  animation frames. Never settling is a failure with a diagnostic. */
export async function settleCamera(read, {
  stableSamples = 5, minFrames = 30, tolerance = CAMERA_SETTLE_TOLERANCE,
  timeoutMs = 10_000, intervalMs = 50,
  now = () => Date.now(),
  pause = (ms) => new Promise((resolvePause) => setTimeout(resolvePause, ms)),
} = {}) {
  const deadline = now() + timeoutMs;
  let previous = null;
  let streakStart = null;
  let streak = 0;
  let samples = 0;
  let maxMotion = 0;
  let lastMotion = null;
  do {
    const current = await read();
    samples += 1;
    if (previous) {
      lastMotion = cameraMotion(previous.snapshot, current.snapshot);
      maxMotion = Math.max(maxMotion, lastMotion);
      if (lastMotion <= tolerance) {
        streak += 1;
        streakStart ??= previous;
      } else {
        streak = 0;
        streakStart = null;
      }
      if (streak >= stableSamples && current.frame_count - streakStart.frame_count >= minFrames) {
        return { ...current, settle_samples: samples, settle_max_motion: maxMotion };
      }
    }
    previous = current;
    await pause(intervalMs);
  } while (now() <= deadline);
  const error = new Error(`SETTLING_TIMEOUT:${JSON.stringify({ samples, last_motion: lastMotion })}`);
  error.diagnostic = { samples, streak, last_motion: lastMotion, max_motion: maxMotion, tolerance };
  throw error;
}

/** The 120-frame window only means "immutable" after settling: zero
 *  recomputation, and the camera at the end still equals the settled one. */
export function assessImmutableWindow({ settled, end, perf, frames = 120 }) {
  const details = { frames: perf?.frame_count ?? 0, recompute_count: perf?.recompute_count ?? null,
    motion_since_settle: settled ? cameraMotion(settled.snapshot, end) : null };
  const fail = (code) => ({ pass: false, code, ...details });
  if (!settled) return fail("MEASURED_BEFORE_SETTLE");
  if (details.frames < frames) return fail("IMMUTABLE_WINDOW_TOO_SHORT");
  if (details.motion_since_settle > CAMERA_SETTLE_TOLERANCE) return fail("CAMERA_CHANGED_AFTER_SETTLE");
  if (details.recompute_count !== 0) return fail("IMMUTABLE_FRAME_RECOMPUTE");
  return { pass: true, code: "IMMUTABLE_WINDOW_PASS", ...details };
}

/* ─── LEARNER PLAYBACK (w10) ────────────────────────────────────────────────
 * Judges a timeline recorded while a learner only pressed Play once: no
 * causal selection, no detail panel, one step at a time to the final step,
 * then stop. `events[k].semantic_kind` comes from the scene the page loaded. */
export function assessPlayback({
  samples, events, objects = [], total, intervalMs, replay = null, orbit = null,
}) {
  const checks = {};
  const add = (name, pass, details = undefined) => {
    checks[name] = { pass: Boolean(pass), ...(details === undefined ? {} : { details }) };
  };
  const last = total - 1;
  const byStep = new Map();
  for (const sample of samples) if (!byStep.has(sample.step)) byStep.set(sample.step, sample);
  const settledAt = (step) => [...samples].reverse().find((sample) => sample.step === step);
  const steps = samples.map((sample) => sample.step);
  add("starts_at_step_zero", steps[0] === 0, { first: steps[0] });
  add("no_causal_selection", samples.every((sample) => sample.selected === null),
    samples.filter((sample) => sample.selected !== null).slice(0, 3));
  add("detail_panel_stays_closed", samples.every((sample) => !sample.panel_open));
  const jumps = steps.slice(1).map((step, index) => step - steps[index]).filter((delta) => delta !== 0);
  add("advances_one_step_at_a_time", jumps.every((delta) => delta === 1), { jumps });
  const firstFinal = samples.findIndex((sample) => sample.step === last);
  add("reaches_final_step", firstFinal >= 0, { last, max: Math.max(...steps) });
  const afterFinal = firstFinal >= 0 ? samples.slice(firstFinal) : [];
  const stopped = afterFinal.find((sample) => !sample.playing);
  add("stops_at_final_step", firstFinal >= 0 && afterFinal.every((sample) => sample.step === last)
    && !!stopped && stopped.t - samples[firstFinal].t <= intervalMs + 500
    && samples.at(-1).t - samples[firstFinal].t >= 2 * intervalMs,
  { stopped_after_ms: stopped ? stopped.t - samples[firstFinal].t : null,
    observed_after_final_ms: firstFinal >= 0 ? samples.at(-1).t - samples[firstFinal].t : null });
  const construction = [];
  const measurement = [];
  for (let k = 1; k <= last; k += 1) {
    const kind = events.find((event) => event.step_index === k)?.semantic_kind;
    const now = settledAt(k);
    const before = settledAt(k - 1);
    if (!now || !before) continue;
    if (kind === "GEOMETRY_CONSTRUCTION") {
      construction.push({ step: k,
        changed: JSON.stringify(now.rendered) !== JSON.stringify(before.rendered) });
    }
    if (kind === "MEASUREMENT") {
      measurement.push({ step: k, added: now.readout.filter((row) => !before.readout.includes(row)) });
    }
  }
  add("construction_steps_change_geometry", construction.every((c) => c.changed), construction);
  add("measurement_steps_show_a_value", measurement.every((m) => m.added.length > 0), measurement);
  // Đáp số + mọi BÍ DANH của nó (`alias_of`) là MỘT kết luận ⇒ đúng MỘT dòng.
  // Không so giá trị: AB = AD = 4 ở hình lập phương là hai đại lượng thật.
  const finalRows = firstFinal >= 0 ? settledAt(last).readout : [];
  const ten = (o) => (o?.notation || o?.label || "").replace(/\s+/g, "");
  const answers = events.filter((event) => event.semantic_kind === "FINAL_RESULT" && event.object)
    .map((event) => event.object).filter((id, i, all) => all.indexOf(id) === i)
    .map((id) => {
      const names = new Set((objects ?? []).filter((o) => o.id === id || o.alias_of === id).map(ten));
      return { id, rows: finalRows.filter((row) => names.has(row.split("=")[0].replace(/\s+/g, ""))) };
    });
  add("final_result_shown_once", answers.length > 0 && answers.every((a) => a.rows.length === 1),
    { rows: finalRows, answers });
  if (replay) {
    add("replay_resets_step_selection_highlight",
      replay.step === 0 && replay.selected === null && replay.highlighted.length === 0, replay);
  }
  if (orbit) {
    add("orbit_preserves_timeline", orbit.before.step === orbit.after.step
      && JSON.stringify(orbit.before.readout) === JSON.stringify(orbit.after.readout), orbit);
  }
  return { pass: Object.values(checks).every((check) => check.pass), checks };
}
