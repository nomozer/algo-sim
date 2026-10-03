import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { relative, resolve } from "node:path";

// Bộ đo góc nhìn của CHÍNH sản phẩm (Node ≥ 22.18 bóc kiểu TS; hai module này
// không import gì) — không một định nghĩa thứ hai trong bộ đo.
import { cauTrucGocNhin, toNumber } from "../src/simulations/domains/geometry/scene3d-model.ts";
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
 * diện): choán + sâu như cũ; mặt khối ≥ 12° so với tia nhìn; hai cạnh chung
 * đỉnh không sụp thành một đường, và không đỉnh nào sát cạnh khác — ngưỡng là
 * ½ số đo của khối lập phương tham chiếu ở hướng mặc định cũ (`HUONG`, cùng
 * tham chiếu và cùng hệ số ½ của `NGUONG_GOC_NHIN`). */
const _tru = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const _cheo = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const _tich = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const _chuan = (a) => { const d = Math.hypot(...a) || 1; return a.map((x) => x / d); };

/** Chiếu TRỰC GIAO dọc hướng (tâm → camera) xuống mặt phẳng nhìn. */
function chieuTrucGiao(diem, huong) {
  const d = _chuan(huong);
  const phai = _chuan(Math.abs(d[2]) > 0.999 ? _cheo([0, 1, 0], d) : _cheo([0, 0, 1], d));
  const len = _cheo(d, phai);
  return diem.map((p) => [_tich(p, phai), _tich(p, len)]);
}

/** Bộ ba u–v–w nối bằng HAI CẠNH chung đỉnh v; trả chiều cao nhỏ nhất của tam
 *  giác ảnh (chia bán kính hình trên ảnh). Nhỏ ⇔ góc tại v sụp: hai cạnh trông
 *  như một nét (S–A–B), đỉnh v biến vào đường. Ba đỉnh thẳng hàng KHÔNG qua cạnh
 *  (A trên đường chéo BF không vẽ, lăng trụ w11) không làm người đọc nhầm. */
export function baDinhGanThangHang(anh, canh) {
  const ke = new Map();
  for (const [a, b] of canh) {
    ke.set(a, [...(ke.get(a) ?? []), b]);
    ke.set(b, [...(ke.get(b) ?? []), a]);
  }
  const tam = anh.reduce((s, q) => [s[0] + q[0] / anh.length, s[1] + q[1] / anh.length], [0, 0]);
  const R = Math.max(1e-9, ...anh.map((q) => Math.hypot(q[0] - tam[0], q[1] - tam[1])));
  let min = Infinity;
  let bo = null;
  for (const [v, ns] of ke) {
    for (let i = 0; i < ns.length; i += 1) {
      for (let j = i + 1; j < ns.length; j += 1) {
        const [a, b, c] = [anh[ns[i]], anh[v], anh[ns[j]]];
        const s2 = Math.abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]));
        const dai = Math.max(Math.hypot(b[0] - a[0], b[1] - a[1]), Math.hypot(c[0] - a[0], c[1] - a[1]),
          Math.hypot(c[0] - b[0], c[1] - b[1]));
        if (s2 / dai / R < min) { min = s2 / dai / R; bo = [ns[i], v, ns[j]]; }
      }
    }
  }
  return { min: Number.isFinite(min) ? min : 1, triple: bo };
}

const _LP = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]];
const _LP_CANH = [[0, 1], [1, 2], [2, 3], [0, 3], [4, 5], [5, 6], [6, 7], [4, 7], [0, 4], [1, 5], [2, 6], [3, 7]];
export const NGUONG_ANH_XOAY = {
  tiLeDienTich: 0.6,
  tiLeDoSau: 0.5,
  matNghiengDo: 12,
  baDinhMin: 0.5 * baDinhGanThangHang(chieuTrucGiao(_LP, [...HUONG]), _LP_CANH).min,
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
  const ba = baDinhGanThangHang(chieuTrucGiao(diem, huong), canh);
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

/** Cổng ảnh xoay trên camera THẬT sau cử chỉ, đo trên ẢNH PHỐI CẢNH chứ không
 *  trên phép chiếu trực giao theo hướng: camera đứng gần (khung lấp 68%), và
 *  phối cảnh đã đặt A cách SB 9 px (0,05 R) ở một hướng mà phép trực giao chấm
 *  0,17 R (lượt chẩn đoán w11). Bộ ba đỉnh và đỉnh–cạnh đo bằng toạ độ màn
 *  hình, chia bán kính hình trên màn hình; mặt nghiêng đo theo tia từ mắt tới
 *  tâm mặt. Diện tích/độ sâu giữ số đo theo hướng (so với cực đại của cảnh).
 *  Cộng: mọi đỉnh khối (và chỗ nhãn) trong khung, không dưới lớp phủ
 *  (`overlays`: hộp px CSS tương đối canvas — thanh số đo, nút nổi, ô soi). */
export function danhGiaAnhXoayThuc(scene, snapshot, overlays = []) {
  const m = snapshot.view_matrix_column_major;
  const huong = danhGiaAnhXoay(scene, [m[2], m[6], m[10]]);
  const { diem, ten, canh, mat } = cauTrucKhoi(scene);
  if (diem.length < 3) return { pass: true, failures: [], metrics: null, unreadable_vertices: [] };
  const man = diem.map((p) => chieuManHinh(snapshot, p));
  const diemNhin = [0, 1, 2].map((j) => -(m[4 * j] * m[12] + m[4 * j + 1] * m[13] + m[4 * j + 2] * m[14]));
  const tam = man.reduce((s, q) => ({ x: s.x + q.x / man.length, y: s.y + q.y / man.length }), { x: 0, y: 0 });
  const R = Math.max(1e-9, ...man.map((q) => Math.hypot(q.x - tam.x, q.y - tam.y)));
  const R3 = Math.max(1e-9, ...diem.map((p) => Math.hypot(..._tru(p, diem[0]))));
  const baDinh = baDinhGanThangHang(man.map((q) => [q.x, q.y]), canh);
  const trenDoan3 = (p, a, b) => {
    const ab = _tru(b, a);
    const t = Math.max(0, Math.min(1, _tich(_tru(p, a), ab) / Math.max(1e-12, _tich(ab, ab))));
    return Math.hypot(..._tru(p, [a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2]])) < 1e-6 * R3;
  };
  let dinhCanh = Infinity;
  man.forEach((p, i) => {
    for (const [a, b] of canh) {
      if (a === i || b === i || trenDoan3(diem[i], diem[a], diem[b])) continue;
      const [A, B] = [man[a], man[b]];
      const d2 = (B.x - A.x) ** 2 + (B.y - A.y) ** 2;
      const t = Math.max(0, Math.min(1, ((p.x - A.x) * (B.x - A.x) + (p.y - A.y) * (B.y - A.y)) / Math.max(1e-12, d2)));
      dinhCanh = Math.min(dinhCanh, Math.hypot(p.x - A.x - t * (B.x - A.x), p.y - A.y - t * (B.y - A.y)) / R);
    }
  });
  let matNghieng = Infinity;
  for (const f of mat) {
    const n = _chuan(_cheo(_tru(diem[f[1]], diem[f[0]]), _tru(diem[f[2]], diem[f[0]])));
    const c = f.reduce((s, i) => s.map((x, k) => x + diem[i][k] / f.length), [0, 0, 0]);
    matNghieng = Math.min(matNghieng, (Math.asin(Math.min(1, Math.abs(_tich(n, _chuan(_tru(c, diemNhin)))))) * 180) / Math.PI);
  }
  const metrics = {
    ...huong.metrics,
    mat_nghieng_min_do: matNghieng,
    ba_dinh_min: baDinh.min,
    ba_dinh_gan_thang_hang: baDinh.triple?.map((i) => ten[i]) ?? null,
    dinh_canh_min: Number.isFinite(dinhCanh) ? dinhCanh : 1,
    measured_on: "perspective_screen",
  };
  const n = NGUONG_ANH_XOAY;
  const le = 0.03 * Math.min(snapshot.viewport_width, snapshot.viewport_height);
  const trong = (s, r) => s.x >= r.x && s.x <= r.x + r.w && s.y >= r.y && s.y <= r.y + r.h;
  const lech = [];
  man.forEach((s, i) => {
    const nhan = { x: s.x, y: s.y - 18 };   // nhãn đặt ngay trên đỉnh
    if (s.behind || s.x < le || s.y < le || s.x > snapshot.viewport_width - le
        || s.y > snapshot.viewport_height - le) lech.push({ vertex: ten[i], reason: "OUTSIDE_CANVAS", ...s });
    else if (overlays.some((r) => trong(s, r) || trong(nhan, r))) lech.push({ vertex: ten[i], reason: "UNDER_OVERLAY", ...s });
  });
  const failures = [
    metrics.dien_tich_ti_le < n.tiLeDienTich && "PROJECTED_AREA_TOO_SMALL",
    metrics.do_sau_ti_le < n.tiLeDoSau && "DEPTH_TOO_SHALLOW",
    metrics.mat_nghieng_min_do < n.matNghiengDo && "FACE_NEAR_EDGE_ON",
    metrics.ba_dinh_min < n.baDinhMin && "THREE_KEY_VERTICES_NEAR_COLLINEAR",
    metrics.dinh_canh_min < n.dinhCanhMin && "VERTEX_ON_FOREIGN_EDGE",
    lech.length > 0 && "KEY_VERTEX_NOT_READABLE",
  ].filter(Boolean);
  return { pass: failures.length === 0, failures, metrics, unreadable_vertices: lech };
}

/** Camera SAU cử chỉ hoạch định, mô phỏng đúng OrbitControls (Z lên): xoay
 *  quanh trục Z qua tâm quỹ đạo `target`, rồi lùi `nac` nấc con lăn (mỗi nấc
 *  bán kính ×1/0.95). Chiếu và khung giữ nguyên. */
export function cameraSauCuChi(snapshot, target, doXoay, nac = 0) {
  const m = snapshot.view_matrix_column_major;
  const mat = [0, 1, 2].map((j) => -(m[4 * j] * m[12] + m[4 * j + 1] * m[13] + m[4 * j + 2] * m[14]));
  const v = _xoayZ(_tru(mat, target), doXoay).map((x) => x / 0.95 ** nac);
  const moi = v.map((x, i) => x + target[i]);
  const z = _chuan(v);
  const x = _chuan(_cheo([0, 0, 1], z));
  const y = _cheo(z, x);
  return { ...snapshot, position: moi,
    view_matrix_column_major: [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0,
      -_tich(x, moi), -_tich(y, moi), -_tich(z, moi), 1] };
}

/** Cử chỉ HOẠCH ĐỊNH cho ảnh xoay, chấm TRƯỚC bằng chính cổng phối cảnh trên
 *  camera mô phỏng: mỗi góc (lượng kéo làm tròn px như cử chỉ thật) thử lùi
 *  3 rồi 6 nấc; nhận khi đạt cổng VÀ đổi tập khuất dự đoán. Thứ tự tất định. */
export function orbitPlanThuc(scene, snapshot, target, overlays = [],
  { offsets = ORBIT_OFFSETS_DEG, zooms = [3, 6] } = {}) {
  const m0 = snapshot.view_matrix_column_major;
  const before = predictedHidden(scene, [m0[2], m0[6], m0[10]]);
  const H = snapshot.viewport_height;
  const ra = [];
  for (const offset of offsets) {
    const dx = Math.round((-offset / 360) * H);
    const thuc = (-360 * dx) / H;
    for (const nac of zooms) {
      const cam = cameraSauCuChi(snapshot, target, thuc, nac);
      const m = cam.view_matrix_column_major;
      const gate = danhGiaAnhXoayThuc(scene, cam, overlays);
      const after = predictedHidden(scene, [m[2], m[6], m[10]]);
      if (gate.pass && JSON.stringify(after) !== JSON.stringify(before)) {
        ra.push({ offset_deg: offset, dx, effective_offset_deg: thuc, zoom_out_notches: nac,
          predicted_gate: gate, predicted_hidden_before: before, predicted_hidden_after: after });
        break;
      }
    }
  }
  return ra;
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

/** Lớp CSS mà một dòng của BẢNG LỜI GIẢI phải mang theo tầng của nó (W12;
 *  ngoài chuỗi ⇒ `la-diu`). Dải số đo trên khung đã gỡ. */
export const LOP_DONG_THEO_TANG = {
  dich: "la-chon", du_kien_so: "la-so-lieu", trung_gian: "la-trung-gian", boi_canh: "la-boi-canh",
};

/* ─── W12 · MÀU VAI TRÒ TRÊN KHUNG ─────────────────────────────────────────
 * Chú giải causal hứa: xanh = đích, cam (đậm, nhạt, hổ phách) = số trong chuỗi,
 * xám = ngữ cảnh. Bảng lời giải và ô chú giải đã được đo theo token; khung 3D thì
 * chưa — viền thiết diện NGỮ CẢNH giữ màu kiểu hổ phách mà mọi cổng vẫn xanh
 * (e115eede). Nay: điểm ảnh rơi vào dải sắc của một vai trò thì phải có một vật
 * VẼ ĐƯỢC mang vai trò ấy. Dải định nghĩa bằng sắc độ, không đọc bảng màu sản
 * phẩm. Có vật mang vai trò thì không phán (vật ấy có thể bị che hoặc rất nhỏ). */
export const DAI_SAC_VAI_TRO = { s: 0.45, l: [0.2, 0.85], cam: [10, 50], xanh: [205, 235] };

/** Một điểm ảnh sRGB 0–255 → `"cam"` | `"xanh"` | `null`. HÀM THUẦN, không dùng
 *  biến ngoài: bộ chạy tiêm chính mã nguồn của nó vào trang (`toString`). */
export function phanLoaiSac(r, g, b, dai) {
  const R = r / 255, G = g / 255, B = b / 255;
  const max = Math.max(R, G, B), min = Math.min(R, G, B), d = max - min, l = (max + min) / 2;
  if (d === 0) return null;
  const s = d / (1 - Math.abs(2 * l - 1));
  if (s < dai.s || l < dai.l[0] || l > dai.l[1]) return null;
  const h = ((max === R ? ((G - B) / d) % 6 : max === G ? (B - R) / d + 2 : (R - G) / d + 4) * 60 + 360) % 360;
  if (h >= dai.cam[0] && h <= dai.cam[1]) return "cam";
  if (h >= dai.xanh[0] && h <= dai.xanh[1]) return "xanh";
  return null;
}

/* ─── W15 · SECTION_FILL_DISTINGUISHABLE ─────────────────────────────────────
 * Phần TÔ của thiết diện khép kín phải đọc tách khỏi mặt cắt và khối. Cùng khung hình, cùng
 * camera, cùng trạng thái hình học: ảnh tô-BẬT so với ảnh tô-TẮT
 * (`__geo3d_set_section_fill_visible`) trên các điểm mẫu bên trong đa giác thiết diện chiếu
 * lên màn hình, bỏ một lề quanh mọi cạnh chiếu. Ngưỡng đăng ký TRƯỚC mọi phép đo —
 * `ASSUMPTION_CERTIFICATE_AMENDMENT.md` §11, test node khoá hai bản bằng nhau; sản phẩm trượt
 * ngưỡng thì chỉnh hằng độ đục của renderer, không chỉnh ngưỡng. */
export const NGUONG_TO_THIET_DIEN = { T_ON: 20, T_ON_MIN: 12, T_OFF: 3, margin_px: 3 };

/** CIE76 trên sRGB (D65): 0–255 → tuyến tính → XYZ → Lab, khoảng cách Euclid. Ma trận 4 chữ
 *  số, X và Z chia theo tổng hàng để trắng ↦ đúng (1, 1, 1). HÀM THUẦN. */
export function deltaE76(a, b) {
  const lab = (rgb) => {
    const [r, g, bl] = rgb.map((c) => { const x = c / 255; return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; });
    const X = (0.4124 * r + 0.3576 * g + 0.1805 * bl) / 0.9505;
    const Y = 0.2126 * r + 0.7152 * g + 0.0722 * bl;
    const Z = (0.0193 * r + 0.1192 * g + 0.9505 * bl) / 1.089;
    const f = (t) => (t > 216 / 24389 ? Math.cbrt(t) : ((24389 / 27) * t + 16) / 116);
    return [116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))];
  };
  const [p, q] = [lab(a), lab(b)];
  return Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]);
}

/** `trangThai` ∈ closed | pre_close | rewound; `cap` = [{on: [r,g,b], off: [r,g,b]}] cùng điểm
 *  ảnh. Khép kín: ΔE trung bình ≥ T_ON VÀ mọi mẫu ≥ T_ON_MIN (bắt tô thiếu/nhạt). Trước khi
 *  khép, sau khi tua ngược: ΔE lớn nhất ≤ T_OFF (bắt tô sớm, tô không mất). Không mẫu ⇒ đỏ. */
export function assessSectionFill(trangThai, cap) {
  const nguong = NGUONG_TO_THIET_DIEN;
  const de = (cap ?? []).map((p) => deltaE76(p.on, p.off));
  const dau = { state: trangThai, samples: de.length, thresholds: nguong };
  if (!["closed", "pre_close", "rewound"].includes(trangThai)) return { ...dau, pass: false, reason: "UNKNOWN_STATE" };
  if (de.length === 0) return { ...dau, pass: false, reason: "NO_SAMPLES" };
  const mean = de.reduce((s, x) => s + x, 0) / de.length;
  const [min, max] = [Math.min(...de), Math.max(...de)];
  const pass = trangThai === "closed" ? mean >= nguong.T_ON && min >= nguong.T_ON_MIN : max <= nguong.T_OFF;
  return { ...dau, mean_delta_e: mean, min_delta_e: min, max_delta_e: max, pass };
}

const _cachDoan = (x, y, a, b) => {
  const dx = b.x - a.x, dy = b.y - a.y;
  const t = Math.max(0, Math.min(1, ((x - a.x) * dx + (y - a.y) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(x - (a.x + t * dx), y - (a.y + t * dy));
};

/** Vùng thiết diện chiếu: `trong` (bên trong đa giác) và `xa` (cách mọi cạnh đa giác, mọi cạnh
 *  khối `canh` = [{id, a, b}] và mọi dấu điểm `cham` = [{center, radius_world}] ≥ `margin_px`,
 *  §11 / W16 §14.4). Có đỉnh sau camera ⇒ null (cổng đỏ, không mẫu). */
function _vungThietDien(dinh, snapshot, canh = [], cham = []) {
  const margin = NGUONG_TO_THIET_DIEN.margin_px;
  const p = (dinh ?? []).map((v) => chieuManHinh(snapshot, v.map(num)));
  if (p.length < 3 || p.some((q) => q.behind || !Number.isFinite(q.x + q.y))) return null;
  const doanKhoi = (canh ?? []).map((e) => ({ id: e.id, d: [e.a, e.b].map((v) => chieuManHinh(snapshot, v.map(num))) }))
    .filter((e) => e.d.every((q) => !q.behind && Number.isFinite(q.x + q.y)));
  const dau = (cham ?? []).length ? doCoDauDinh(snapshot, cham).map((d, i) =>
    ({ ...chieuManHinh(snapshot, cham[i].center.map(num)), r: d.diameter_px / 2 })) : [];
  const trong = (x, y) => {
    let c = false;
    for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
      if ((p[i].y > y) !== (p[j].y > y) && x < ((p[j].x - p[i].x) * (y - p[i].y)) / (p[j].y - p[i].y) + p[i].x) c = !c;
    }
    return c;
  };
  const xa = (x, y) =>
    p.every((a, i) => _cachDoan(x, y, a, p[(i + 1) % p.length]) >= margin)
    && doanKhoi.every((e) => _cachDoan(x, y, e.d[0], e.d[1]) >= margin)
    && dau.every((c) => Math.hypot(x - c.x, y - c.y) >= c.r + margin);
  return { p, doanKhoi, trong, xa };
}

/** Điểm mẫu (px CSS của khung, lưới 6 px) BÊN TRONG đa giác thiết diện chiếu bằng camera
 *  thật, cách mọi cạnh và dấu điểm đã chiếu ít nhất `margin_px` — ĐÚNG câu đăng ký §11 (W15
 *  chỉ chừa lề quanh cạnh của chính đa giác; W16 §14.4 sửa cho khớp). `vatCan` = {canh, cham}. */
export function diemMauThietDien(dinh, snapshot, vatCan = {}) {
  const vung = _vungThietDien(dinh, snapshot, vatCan.canh, vatCan.cham);
  if (!vung) return [];
  const [xs, ys] = [vung.p.map((q) => q.x), vung.p.map((q) => q.y)];
  const ra = [];
  for (let y = Math.ceil(Math.min(...ys)); y <= Math.max(...ys); y += 6) {
    for (let x = Math.ceil(Math.min(...xs)); x <= Math.max(...xs); x += 6) {
      if (vung.trong(x, y) && vung.xa(x, y)) ra.push([x, y]);
    }
  }
  return ra;
}

/** W16 · SECTION_FILL_UNDER_EDGES — với mỗi cạnh khối đi qua vùng thiết diện (≥ 3 điểm, bước
 *  1 px CSS, trong vùng và xa biên/dấu điểm): `core` = dải ±1 px CSS (bước ½ px — phủ cả điểm
 *  ảnh thiết bị ở DPR 2), `ref` = hai bên ±4 px CSS, vẫn trong vùng và xa mọi cạnh khác. */
export function diemCanhQuaThietDien(dinh, snapshot, canh = [], cham = []) {
  const vung = _vungThietDien(dinh, snapshot, [], cham);
  const khac = _vungThietDien(dinh, snapshot, canh, cham);
  if (!vung || !khac) return [];
  const ra = [];
  for (const e of khac.doanKhoi) {
    const [a, b] = e.d;
    const dai = Math.hypot(b.x - a.x, b.y - a.y);
    if (dai < 1) continue;
    const [ux, uy] = [(b.x - a.x) / dai, (b.y - a.y) / dai];
    const tam = [];
    for (let k = 0; k <= dai; k += 1) {
      const [x, y] = [a.x + ux * k, a.y + uy * k];
      if (vung.trong(x, y) && vung.xa(x, y)) tam.push([x, y]);
    }
    if (tam.length < 3) continue;
    const core = tam.flatMap(([x, y]) => [-1, -0.5, 0, 0.5, 1].map((d) => [x - uy * d, y + ux * d]));
    const ref = tam.flatMap(([x, y]) => [-4, 4].map((d) => [x - uy * d, y + ux * d]))
      .filter(([x, y]) => khac.trong(x, y) && khac.xa(x, y));
    if (ref.length >= 3) ra.push({ id: e.id, core, ref });
  }
  return ra;
}

/** Trung vị THEO KÊNH của các màu (điểm ảnh tham chiếu) — HÀM THUẦN. */
const _trungViMau = (mau) => [0, 1, 2].map((k) => {
  const s = mau.map((m) => m[k]).sort((x, y) => x - y);
  const g = s.length >> 1;
  return s.length % 2 ? s[g] : (s[g - 1] + s[g]) / 2;
});

/** W16 §14.4: mỗi cạnh = {id, core: [{on, off}], ref: [{on, off}]} cùng điểm ảnh, tô BẬT/TẮT.
 *  Lõi = điểm ảnh tối nhất của dải lúc tắt. Đạt ⇔ ρ = ΔE(lõi bật, lõi tắt) / trung vị
 *  ΔE(tham chiếu bật, tắt) < 1 (cạnh che một phần tô) VÀ ΔE(lõi tắt, trung vị màu tham chiếu
 *  tắt) ≥ T_ON_MIN (cạnh thật sự được vẽ). Không cạnh nào ⇒ không áp dụng — KHÔNG phải đạt. */
export function assessSectionFillUnderEdges(canh) {
  const T = NGUONG_TO_THIET_DIEN;
  if (!(canh ?? []).length) return { pass: false, reason: "NOT_APPLICABLE_NO_CROSSING_EDGE", edges: [] };
  const sang = ([r, g, b]) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
  const edges = canh.map((e) => {
    if (!e.core?.length || !e.ref?.length) return { id: e.id, pass: false, reason: "NO_SAMPLES" };
    const loi = e.core.reduce((m, q) => (sang(q.off) < sang(m.off) ? q : m));
    const de = e.ref.map((q) => deltaE76(q.on, q.off)).sort((x, y) => x - y);
    const g = de.length >> 1;
    const thamChieu = de.length % 2 ? de[g] : (de[g - 1] + de[g]) / 2;
    const rho = thamChieu > 0 ? deltaE76(loi.on, loi.off) / thamChieu : Infinity;
    const tuongPhan = deltaE76(loi.off, _trungViMau(e.ref.map((q) => q.off)));
    return { id: e.id, samples: e.core.length, rho, reference_delta_e: thamChieu, edge_contrast_off: tuongPhan,
      pass: rho < 1 && tuongPhan >= T.T_ON_MIN };
  });
  return { pass: edges.every((e) => e.pass), edges, rule: { rho_lt: 1, edge_contrast_min: T.T_ON_MIN } };
}

/** `census` = {total, cam, xanh} đếm trên ảnh khung ở trạng thái causal. */
export function assessCausalCanvasHues(scene, tiers, census) {
  const ve = new Set((scene?.objects ?? [])
    .filter((o) => o.render !== "readout" && o.render !== "non_visual").map((o) => o.id));
  const coVatVe = (...ts) => Object.entries(tiers ?? {}).some(([id, t]) => ve.has(id) && ts.includes(t));
  const tolerance = Math.max(40, Math.round((census?.total ?? 0) * 2e-4));
  const dai = (pixels, allowed) => ({ pixels, allowed, pass: allowed || pixels <= tolerance });
  const cam = dai(census?.cam ?? Infinity, coVatVe("du_kien_so", "trung_gian"));
  const xanh = dai(census?.xanh ?? Infinity, coVatVe("dich"));
  return { census, tolerance_pixels: tolerance, cam, xanh, pass: cam.pass && xanh.pass };
}

/* ─── W12 · DÒNG THỜI GIAN HÌNH HỌC — oracle đọc từ SNAPSHOT formation ─────
 * Bước dựng = phân hoạch dãy sự kiện: bước mới mở ở sự kiện
 * GEOMETRY_CONSTRUCTION làm đổi chữ ký HÌNH (vật vẽ được + tiến độ thiết diện);
 * khung hiện là sự kiện CUỐI đoạn. Cảnh không gõ loại ⇒ mỗi sự kiện một bước.
 * Không import sản phẩm: bộ đo nói điều sản phẩm PHẢI làm. */
function chuKyHinh(scene, k) {
  const ve = new Set((scene?.objects ?? [])
    .filter((o) => o.render !== "readout" && o.render !== "non_visual").map((o) => o.id));
  const s = scene?.formation?.steps?.[k];
  const hien = (s?.visible_ids ?? expectedVisibleIds(scene, k)).filter((id) => ve.has(id)).sort();
  const tienDo = (s?.geometry_progress ?? []).map((p) =>
    [p.object_id, (p.visible_edge_ids ?? []).length, Boolean(p.closed), Boolean(p.fill_visible)]);
  return JSON.stringify([hien, tienDo]);
}

const loaiSuKien = (scene, k) => scene?.formation?.steps?.[k]?.semantic_kind
  ?? (scene?.events ?? []).find((e) => e.step_index === k)?.semantic_kind;

export function expectedGeometryTimeline(scene) {
  const n = scene?.formation?.steps?.length ?? (scene?.events ?? []).length;
  const coLoai = n > 0 && Array.from({ length: n }, (_, k) => loaiSuKien(scene, k))
    .every((l) => l && l !== "LEGACY_UNTYPED_EVENT");
  const ra = [];
  for (let k = 0; k < n; k += 1) {
    if (k === 0 || !coLoai || (loaiSuKien(scene, k) === "GEOMETRY_CONSTRUCTION"
        && chuKyHinh(scene, k) !== chuKyHinh(scene, k - 1))) {
      ra.push({ index: ra.length, start: k, end: k, anchor: k, kinds: [] });
    }
    const g = ra.at(-1);
    g.end = k;
    g.anchor = k;
    g.kinds.push(loaiSuKien(scene, k) ?? null);
  }
  return ra;
}

/** Lớp lời giải kỳ vọng ở khung `anchor`: kết quả (FINAL_RESULT tới đó, mỗi
 *  vật một lần) · dữ kiện (đại lượng tự do đang hiện, trừ kết quả) · các bước
 *  tính (MEASUREMENT tới đó, trừ hai nhóm trên). */
export function expectedSolutionRows(scene, anchor) {
  const byId = new Map((scene?.objects ?? []).map((o) => [o.id, o]));
  const vat = (k) => (scene?.events ?? []).find((e) => e.step_index === k)?.object;
  const results = [];
  for (let k = 0; k <= anchor; k += 1) {
    const id = vat(k);
    if (loaiSuKien(scene, k) === "FINAL_RESULT" && id && byId.has(id) && !results.includes(id)) {
      results.push(id);
    }
  }
  const hien = new Set(expectedVisibleIds(scene, anchor));
  const givens = (scene?.objects ?? []).filter((o) => o.type === "quantity"
    && o.render === "readout" && o.origin === "free" && hien.has(o.id)
    && !results.includes(o.id)).map((o) => o.id);
  const steps = [];
  for (let k = 1; k <= anchor; k += 1) {
    const o = byId.get(vat(k));
    if (loaiSuKien(scene, k) !== "MEASUREMENT" || !o || o.type !== "quantity"
        || o.render !== "readout" || results.includes(o.id) || givens.includes(o.id)
        || steps.includes(o.id)) continue;
    steps.push(o.id);
  }
  return { givens, steps, results };
}

/** Phán quyết các bước dựng QUAN SÁT trong trình duyệt (W12).
 *  `observed = { step_count, steps: [{ index, rendered, focus_label, solution }] }`
 *  — `rendered`: vật vẽ lên khung; `focus_label`: dòng "Đang dựng"; `solution`:
 *  `{ givens, steps, results }` đọc từ bảng lời giải. */
export function assessGeometrySteps(scene, observed) {
  const t = expectedGeometryTimeline(scene);
  // Nhãn → MỌI vật mang nhãn ấy: đáp số và bí danh của nó trùng nhãn.
  const byLabel = new Map();
  for (const o of scene?.objects ?? []) byLabel.set(o.label, [...(byLabel.get(o.label) ?? []), o]);
  const finalIds = new Set((scene?.events ?? [])
    .filter((e) => e.semantic_kind === "FINAL_RESULT" && e.object).map((e) => e.object));
  const steps = observed?.steps ?? [];
  const staticFrames = steps.slice(1)
    .filter((s, i) => JSON.stringify(s.rendered) === JSON.stringify(steps[i].rendered))
    .map((s) => s.index);
  const focusOf = (s) => byLabel.get(String(s.focus_label ?? "").trim()) ?? [];
  const measurementSteps = steps.slice(1)
    .filter((s) => focusOf(s).some((o) => o.type === "quantity")).map((s) => s.index);
  const finalSteps = steps.slice(1)
    .filter((s) => focusOf(s).some((o) => finalIds.has(o.id) || finalIds.has(o.alias_of)))
    .map((s) => s.index);
  const cung = (a, b) => JSON.stringify(a ?? []) === JSON.stringify(b ?? []);
  const sync = steps.map((s) => {
    const want = t[s.index] ? expectedSolutionRows(scene, t[s.index].anchor) : null;
    return { index: s.index, want, got: s.solution,
      pass: Boolean(want) && cung(want.givens, s.solution?.givens)
        && cung(want.steps, s.solution?.steps) && cung(want.results, s.solution?.results) };
  });
  const checks = {
    step_count_matches: observed?.step_count === t.length && steps.length === t.length,
    no_static_frames: staticFrames.length === 0,
    no_measurement_geometry_steps: measurementSteps.length === 0,
    no_final_result_geometry_steps: finalSteps.length === 0,
    solution_in_sync: sync.length > 0 && sync.every((s) => s.pass),
  };
  return {
    expected_step_count: t.length,
    observed_step_count: observed?.step_count ?? null,
    static_frames: staticFrames,
    measurement_geometry_steps: measurementSteps,
    final_result_geometry_steps: finalSteps,
    solution_sync: sync,
    checks,
    pass: Object.values(checks).every(Boolean),
  };
}

/* ─── ĐỘ PHỦ VAI TRÒ DỰNG HÌNH (W14) ───────────────────────────────────────
 * Ba nguồn, so từng đôi. KỲ VỌNG: `expected_formation` của registry, viết tay từ
 * hợp đồng/tô-pô chuẩn, không mã sản phẩm nào sinh hay đọc. KHAI BÁO: danh sách
 * `formation_requirements` sản phẩm gắn trên vật mang `shape_class`. QUAN SÁT: vật
 * renderer TỰ BÁO đã dựng ở từng bước của thanh bước. Vật nhận diện bằng LOẠI + TẬP
 * ĐỈNH, không bằng id sản phẩm; vai trò không bao giờ suy từ chữ, tên hay công thức. */
const dinhCua = (o) => sortedUnique(o?.vertex_ids ?? o?.endpoint_ids ?? []);
const cungTap = (a, b) => JSON.stringify(sortedUnique(a)) === JSON.stringify(sortedUnique(b));

/** Hai vai trò liền nhau được phép xuất hiện CÙNG bước: đường cao trùng cạnh bên
 *  (V7 — chân là đỉnh đáy) hiện một lần, mang cả hai vai. */
const CAP_VAI_KHONG_NGHIEM = new Set(["CONSTRUCT_HEIGHT>CONSTRUCT_LATERAL_BOUNDARY"]);

/** Id renderer báo (`T#5cf`: thiết diện 5 đỉnh, khép, tô) → `{kind, vertices, closed, filled}`. */
export function renderedSets(scene, renderedIds) {
  const byId = new Map((scene?.objects ?? []).map((o) => [o.id, o]));
  return (renderedIds ?? []).flatMap((raw) => {
    const s = String(raw);
    const cut = s.indexOf("#");
    const o = byId.get(cut < 0 ? s : s.slice(0, cut));
    const tienDo = cut < 0 ? "" : s.slice(cut + 1);
    return o ? [{ kind: o.type, vertices: dinhCua(o), closed: tienDo.includes("c"),
      filled: tienDo.includes("f") }] : [];
  });
}

function khopVat(e, r) {
  if (r.kind !== e.kind || !cungTap(r.vertices, e.vertices)) return false;
  // Khép thiết diện = viền khép VÀ mặt tô; một cạnh giao bất kỳ = đã dựng giao.
  return e.role === "CLOSE_SECTION" ? r.closed && r.filled : true;
}

/** `expected` = registry; `observedSteps` = `[{index, renderedSets}]` theo thanh bước. */
export function assessFormation(expected, scene, observedSteps, enforced, measured = []) {
  const steps = [...(observedSteps ?? [])].sort((a, b) => a.index - b.index);
  const lanDau = (e) => steps.find((s) => (s.renderedSets ?? []).some((r) => khopVat(e, r)))?.index ?? -1;
  const classes = [];
  for (const lop of sortedUnique([...(enforced ?? []), ...(measured ?? [])])) {
    const fail = [];
    const exp = (expected ?? []).filter((e) => e.class === lop);
    const owner = (scene?.objects ?? []).find((o) => o.shape_class === lop);
    const declared = owner?.formation_requirements ?? [];
    const expRoles = [...new Set(exp.map((e) => e.role))];
    if (exp.length === 0) fail.push({ reason: "EXPECTED_REQUIREMENTS_EMPTY" });
    if (declared.length === 0) fail.push({ reason: "DECLARED_REQUIREMENTS_EMPTY" });
    else if (exp.length > 0 && JSON.stringify(declared) !== JSON.stringify(expRoles)) {
      fail.push({ reason: "DECLARED_DISAGREES_WITH_EXPECTED", declared, expected: expRoles });
    }
    const seen = exp.map((e) => ({ ...e, first_step: lanDau(e) }));
    for (const e of seen.filter((x) => x.first_step < 0)) {
      fail.push({ reason: "EXPECTED_OBJECT_NOT_OBSERVED_IN_ORDER", item: e });
    }
    // Mọi vật của vai trò trước phải xuất hiện TRƯỚC mọi vật của vai trò sau.
    for (let i = 1; i < expRoles.length; i += 1) {
      const truoc = seen.filter((x) => x.role === expRoles[i - 1] && x.first_step >= 0);
      const sau = seen.filter((x) => x.role === expRoles[i] && x.first_step >= 0);
      if (!truoc.length || !sau.length) continue;
      const cuoiTruoc = Math.max(...truoc.map((x) => x.first_step));
      const dauSau = Math.min(...sau.map((x) => x.first_step));
      const dung = CAP_VAI_KHONG_NGHIEM.has(`${expRoles[i - 1]}>${expRoles[i]}`)
        ? cuoiTruoc <= dauSau : cuoiTruoc < dauSau;
      if (!dung) {
        fail.push({ reason: "EXPECTED_OBJECT_NOT_OBSERVED_IN_ORDER",
          order: [expRoles[i - 1], cuoiTruoc, expRoles[i], dauSau] });
      }
    }
    classes.push({ class: lop, enforced: (enforced ?? []).includes(lop), declared,
      expected_roles: expRoles, observed: seen, fail, pass: fail.length === 0 });
  }
  const failing = classes.filter((c) => c.enforced && !c.pass);
  return { classes, reason_codes: sortedUnique(failing.flatMap((c) => c.fail.map((f) => f.reason))),
    pass: failing.length === 0 };
}

/** Mọi tham chiếu CÓ CẤU TRÚC của cảnh phải hiện ở đúng bước (W14, thay heuristic
 *  nhãn "Đang dựng"). Bước quan sát k ↔ nhóm `expectedGeometryTimeline(scene)[k]`:
 *  (a) vật trọng tâm vẽ được của mọi sự kiện trong nhóm ⊆ vật renderer báo;
 *  (b) đại lượng trọng tâm và `readout_ids` của khung neo ⊆ bảng lời giải;
 *  (c) mọi `formula.references[*].entity_id` của đại lượng đang hiện được vẽ hoặc hiện;
 *  (d) tiến độ thiết diện của khung neo đúng số cạnh, khép, tô mà renderer báo. */
export function assessStructuredReferences(scene, observed) {
  const byId = new Map((scene?.objects ?? []).map((o) => [o.id, o]));
  const t = expectedGeometryTimeline(scene);
  const buoc = scene?.formation?.steps ?? [];
  const ve = (o) => o && o.render !== "readout" && o.render !== "non_visual";
  const fail = [];
  for (const s of observed?.steps ?? []) {
    const g = t[s.index];
    if (!g) {
      fail.push({ index: s.index, check: "timeline", kind: "STEP_OUTSIDE_TIMELINE" });
      continue;
    }
    const drawn = new Map((s.rendered ?? []).map((raw) => {
      const v = String(raw);
      const cut = v.indexOf("#");
      return cut < 0 ? [v, null] : [v.slice(0, cut), v.slice(cut + 1)];
    }));
    const panel = new Set([...(s.solution?.givens ?? []), ...(s.solution?.steps ?? []),
      ...(s.solution?.results ?? [])]);
    const hien = (id) => drawn.has(id) || panel.has(id);
    for (let j = g.start; j <= g.end; j += 1) {
      for (const id of buoc[j]?.focus_ids ?? []) {
        const o = byId.get(id);
        if (ve(o) && !drawn.has(id)) fail.push({ index: s.index, check: "a", id, kind: o.type });
        if (o?.render === "readout" && !panel.has(id)) {
          fail.push({ index: s.index, check: "b", id, kind: o.type });
        }
      }
    }
    for (const id of buoc[g.anchor]?.readout_ids ?? []) {
      if (!panel.has(id)) fail.push({ index: s.index, check: "b", id, kind: byId.get(id)?.type });
    }
    for (const id of panel) {
      for (const ref of byId.get(id)?.formula?.references ?? []) {
        if (!hien(ref.entity_id)) {
          fail.push({ index: s.index, check: "c", id: ref.entity_id, kind: byId.get(ref.entity_id)?.type });
        }
      }
    }
    for (const p of buoc[g.anchor]?.geometry_progress ?? []) {
      const tienDo = drawn.get(p.object_id);
      const m = /^(\d+)(c?)(f?)$/.exec(tienDo ?? "");
      const canh = m ? (m[2] ? Number(m[1]) : Number(m[1]) - 1) : -1;
      if (!m || canh !== (p.visible_edge_ids ?? []).length || Boolean(m[2]) !== Boolean(p.closed)
          || Boolean(m[3]) !== Boolean(p.fill_visible)) {
        fail.push({ index: s.index, check: "d", id: p.object_id, kind: "section", drawn: tienDo ?? null });
      }
    }
  }
  return { fail, pass: fail.length === 0 };
}

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
    // W12: số đo ở BẢNG LỜI GIẢI dưới thanh bước (dải trên khung đã gỡ).
    solution_styled: Boolean(actual.solution && actual.solutionTitle)
      && actual.solution.display === "grid"
      && actual.solution.fontFamily !== baseline.div.fontFamily
      && actual.solutionTitle.color !== baseline.span.color,
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
    // W14: vai trò và lớp hình là DỮ LIỆU máy — không bao giờ được lên màn hình.
    for (const value of [object.id, object.type, object.render, object.shape_class,
      ...(object.formation_roles ?? []), ...(object.formation_requirements ?? [])]) {
      if (typeof value === "string" && value.includes("_")) candidates.add(value);
    }
  }
  for (const step of scene?.formation?.steps ?? []) {
    for (const role of step.formation_roles ?? []) candidates.add(role);
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

/** `anchors` (W12): khung của từng BƯỚC DỰNG — thanh bước chỉ đi qua chúng.
 *  Vắng ⇒ mọi sự kiện, như trước W12. */
export function assessFormationSnapshots(scene, observations, anchors = null) {
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
  const expectedForward = anchors ?? expectedSteps.map((_, index) => index);
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
  // W12 — chỉ phán khi bộ đo cung cấp dữ kiện (bằng chứng cũ không có chúng).
  const g = facts.geometry;
  if (g !== undefined) {
    if (g?.checks?.step_count_matches !== true) reasons.push("GEOMETRY_STEP_COUNT_MISMATCH");
    if (g?.checks?.no_static_frames !== true) reasons.push("STATIC_GEOMETRY_FRAME");
    if (g?.checks?.no_measurement_geometry_steps !== true) reasons.push("MEASUREMENT_GEOMETRY_STEP");
    if (g?.checks?.no_final_result_geometry_steps !== true) reasons.push("FINAL_RESULT_GEOMETRY_STEP");
    if (g?.checks?.solution_in_sync !== true) reasons.push("SOLUTION_LAYER_OUT_OF_SYNC");
  }
  if (facts.solution_final !== undefined && facts.solution_final?.answer_once !== true) {
    reasons.push("ANSWER_NOT_SHOWN_ONCE");
  }
  // W14 — cùng luật "chỉ phán khi bộ đo cung cấp dữ kiện".
  if (facts.formation_coverage !== undefined && facts.formation_coverage?.pass !== true) {
    reasons.push("FORMATION_ROLE_COVERAGE", ...(facts.formation_coverage?.reason_codes ?? []));
  }
  if (facts.structured_references !== undefined && facts.structured_references?.pass !== true) {
    reasons.push("STRUCTURED_REFERENCE_NOT_RENDERED");
  }
  if (facts.causal?.legend_shown === false) reasons.push("ROLE_LEGEND_MISSING");
  if (facts.role_colors !== undefined && facts.role_colors?.pass !== true) {
    reasons.push("ROLE_COLOR_MISMATCH");
  }
  if (facts.canvas_role_hues !== undefined && facts.canvas_role_hues?.pass !== true) {
    reasons.push("CAUSAL_CANVAS_ROLE_HUE");
  }
  if (facts.panel_over_canvas === true) reasons.push("SOLUTION_PANEL_COVERS_CANVAS");
  // W15 — chỉ phán khi bộ đo cung cấp dữ kiện (cảnh có thiết diện).
  if (facts.section_fill !== undefined && facts.section_fill?.pass !== true) {
    reasons.push("SECTION_FILL_DISTINGUISHABLE");
  }
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

/** W15 — ba loại từ chối mỗi họ trong bộ trình duyệt (khoá thứ tự đã sắp). */
export const KIEU_TU_CHOI = ["assumption", "topology_kernel", "ungrounded_source"];
/** W17 §15.3: loại từ chối THÊM, tuỳ kịch bản — lỗi khâu dựng trên một đề hợp lệ (lệch phép
 *  dựng; hợp đồng bị tiêm). Luôn khai `expected.refusal_cause`: lời học sinh phụ thuộc nó. */
export const KIEU_TU_CHOI_W17 = ["construction_mismatch", "system_cause"];

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
    if (!scenario.positive_fixture) errors.push(`fixtures:${scenario.id}`);
    // W15: ba LOẠI từ chối mỗi họ, mỗi loại kỳ vọng mã riêng — một lời từ chối không đứng
    // thay cho cả ba (nguồn không có trong đề · giả định · topo/kernel).
    const am = scenario.negative_fixtures ?? [];
    const kieu = am.map((n) => n.kind);
    if (KIEU_TU_CHOI.some((k) => !kieu.includes(k)) || new Set(kieu).size !== kieu.length
        || kieu.some((k) => !KIEU_TU_CHOI.includes(k) && !KIEU_TU_CHOI_W17.includes(k))
        || am.some((n) => KIEU_TU_CHOI_W17.includes(n.kind) && !n.expected?.refusal_cause)
        || am.some((n) => !n.fixture || !n.expected?.product_error_code || !n.expected?.stage_reached)) {
      errors.push(`negatives:${scenario.id}`);
    }
    // W17: ca PHỤC VỤ thêm (vd mặt phẳng đúng) — chỉ kiểm phục vụ + đáp số + nhãn số đo.
    if ((scenario.served_fixtures ?? []).some((s) => !s.kind || !s.fixture || !s.expected?.answer)) {
      errors.push(`served:${scenario.id}`);
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
    // W14: thiếu kỳ vọng hoặc danh sách cưỡng chế thì độ phủ vai trò KHÔNG được đo
    // — không để một kịch bản lặng lẽ thành "không cưỡng chế gì".
    const lopKyVong = new Set((scenario.expected_formation ?? []).map((e) => e.class));
    const cuongChe = scenario.formation_coverage?.enforce;
    if (!Array.isArray(cuongChe) || cuongChe.length === 0
        || cuongChe.some((lop) => !lopKyVong.has(lop))) {
      errors.push(`formation_coverage:${scenario.id}`);
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

/* ─── LEARNER PLAYBACK (w10 → W12) ──────────────────────────────────────────
 * Judges a timeline recorded while a learner only pressed Play once: no
 * causal selection, no detail panel, one GEOMETRY step at a time to the final
 * step, then stop. `scene` is the scene the page loaded; each sample carries
 * `rows: [{ id, sec }]` read from the solution panel (`sec` = heading text). */
export function assessPlayback({
  samples, scene, total, intervalMs, replay = null, orbit = null,
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
  // W12: `step` là BƯỚC DỰNG. Mỗi bước sau bước 0 phải đổi HÌNH — không còn
  // bước chỉ tính số làm chỉ số tăng mà khung đứng yên.
  const t = expectedGeometryTimeline(scene);
  add("step_count_is_geometry_steps", total === t.length, { total, expected: t.length });
  const doiHinh = [];
  for (let g = 1; g <= last; g += 1) {
    const now = settledAt(g);
    const before = settledAt(g - 1);
    doiHinh.push({ step: g, changed: Boolean(now && before)
      && JSON.stringify(now.rendered) !== JSON.stringify(before.rendered) });
  }
  add("every_geometry_step_changes_the_figure", doiHinh.every((c) => c.changed), doiHinh);
  // Bảng lời giải ĐỒNG BỘ với bước dựng đang hiện: đúng dữ kiện / bước tính /
  // kết quả của khung ấy — đọc theo tên mục học sinh thấy.
  const theoMuc = (sample, muc) => (sample?.rows ?? []).filter((r) => r.sec === muc).map((r) => r.id);
  const dongBo = [];
  for (let g = 0; g <= last; g += 1) {
    const sample = settledAt(g);
    if (!sample || !t[g]) continue;
    const want = expectedSolutionRows(scene, t[g].anchor);
    const got = { givens: theoMuc(sample, "Dữ kiện"), steps: theoMuc(sample, "Các bước tính"),
      results: theoMuc(sample, "Kết quả") };
    dongBo.push({ step: g, want, got, pass: JSON.stringify(want) === JSON.stringify(got) });
  }
  add("solution_in_sync_with_geometry_step", dongBo.length === last + 1 && dongBo.every((d) => d.pass),
    dongBo);
  // Đáp số + mọi BÍ DANH của nó (`alias_of`) là MỘT kết luận ⇒ đúng MỘT dòng, ở
  // mục Kết quả. Không so giá trị: AB = AD = 4 ở hình lập phương là hai đại lượng.
  const finalRows = firstFinal >= 0 ? settledAt(last).rows ?? [] : [];
  const objects = scene?.objects ?? [];
  const answers = (scene?.events ?? [])
    .filter((event) => event.semantic_kind === "FINAL_RESULT" && event.object)
    .map((event) => event.object).filter((id, i, all) => all.indexOf(id) === i)
    .map((id) => {
      const ids = new Set(objects.filter((o) => o.id === id || o.alias_of === id).map((o) => o.id));
      const rows = finalRows.filter((row) => ids.has(row.id));
      return { id, rows, in_results: rows.every((row) => row.sec === "Kết quả") };
    });
  add("final_result_shown_once", answers.length > 0
    && answers.every((a) => a.rows.length === 1 && a.in_results), { rows: finalRows, answers });
  if (replay) {
    add("replay_resets_step_selection_highlight",
      replay.step === 0 && replay.selected === null && replay.highlighted.length === 0, replay);
  }
  if (orbit) {
    add("orbit_preserves_timeline", orbit.before.step === orbit.after.step
      && JSON.stringify(orbit.before.rows) === JSON.stringify(orbit.after.rows), orbit);
  }
  return { pass: Object.values(checks).every((check) => check.pass), checks };
}

/* ══ W17 · §15.4/§15.5 — NHÃN SỐ ĐO TRÊN HÌNH ════════════════════════════════
 *
 * Oracle ĐỘC LẬP với sản phẩm: không nhập `scene3d-annotations.ts`. Luật khả dụng đã đăng ký
 * (§15.4) chép lại từ payload — đáp số chỉ từ sự kiện KẾT LUẬN của nó, số đo từ sự kiện tính,
 * dữ kiện khi đã có mặt; chủ thể phải có mặt (`expectedVisibleIds`). Điểm neo chiếu bằng ma trận
 * camera THẬT (`chieuManHinh`) từ toạ độ payload — không tin điểm neo sản phẩm tự báo. */

/** Id đại lượng PHẢI có nhãn số đo ở `step` (công tắc bật cả hai). */
export function expectedAnnotationIds(scene, step) {
  const sk = (scene?.events ?? []).filter((e) => (e.step_index ?? 0) <= step && e.object);
  const ketLuan = new Set(sk.filter((e) => e.semantic_kind === "FINAL_RESULT").map((e) => e.object));
  const daTinh = new Set(sk.filter((e) => e.semantic_kind === "MEASUREMENT" || e.semantic_kind === "FINAL_RESULT")
    .map((e) => e.object));
  const coMat = new Set(expectedVisibleIds(scene, step));
  return sortedUnique((scene?.objects ?? [])
    .filter((o) => o.type === "quantity" && o.annotation && o.value != null)
    .filter((o) => (o.annotation.category === "result" ? ketLuan.has(o.id)
      : daTinh.has(o.id) || (o.origin === "free" && coMat.has(o.id))))
    .filter((o) => o.annotation.subject_ids.every((s) => coMat.has(s)))
    .map((o) => o.id));
}

/** Điểm neo THẾ GIỚI của một nhãn, đọc thẳng payload: đoạn → trung điểm · miền/khối → trung
 *  bình đỉnh · cặp → điểm của cặp. `null` khi payload không đủ. */
export function annotationWorldAnchor(scene, annotation) {
  const byId = new Map((scene?.objects ?? []).map((o) => [o.id, o]));
  const xyz = (o) => (o?.xyz ? o.xyz.map(toNumber) : null);
  const tb = (ps) => (ps.length && ps.every(Boolean)
    ? [0, 1, 2].map((i) => ps.reduce((s, p) => s + p[i], 0) / ps.length) : null);
  const chu = annotation.subject_ids.map((id) => byId.get(id));
  if (!chu.length || chu.some((o) => !o)) return null;
  if (annotation.anchor === "segment") return tb(chu.map(xyz));
  if (annotation.anchor === "region" || annotation.anchor === "solid") {
    const o = chu[0];
    return tb(o.vertex_ids?.length ? o.vertex_ids.map((id) => xyz(byId.get(id)))
      : (o.polygon ?? o.vertices ?? []).map((p) => p.map(toNumber)));
  }
  return xyz(chu.find((o) => o.xyz));
}

const GIAO_E = 0.5;
const hopGiao = (a, b) => a.x < b.x + b.w - GIAO_E && b.x < a.x + a.w - GIAO_E
  && a.y < b.y + b.h - GIAO_E && b.y < a.y + a.h - GIAO_E;

/**
 * §15.5 trên MỘT khung: `boxes` = nhãn số đo đang hiện (`__geo3d_annotation_boxes`), `points` =
 * nhãn điểm đang hiện, `camera` = `__geo3d_camera_snapshot`. Luật: chỉ nhãn khả dụng; nhãn bắt
 * buộc có mặt; mọi hộp trong khung canvas; điểm gần nhất của hộp cách điểm neo chiếu ĐỘC LẬP
 * ≤ 24 px; không hộp nào giao nhãn điểm hay giao nhau.
 */
export function assessAnnotationBoxes({ scene, step, boxes, points, camera, mustShow }) {
  const r = [];
  const mongDoi = expectedAnnotationIds(scene, step);
  const hien = sortedUnique(boxes.map((b) => b.id));
  const lo = hien.filter((id) => !mongDoi.includes(id));
  if (lo.length) r.push(`ANNOTATION_NOT_AVAILABLE:${lo.join(",")}`);
  const thieu = (mustShow ?? []).filter((id) => !hien.includes(id));
  if (thieu.length) r.push(`ANNOTATION_MISSING:${thieu.join(",")}`);
  const W = camera?.viewport_width ?? 0;
  const H = camera?.viewport_height ?? 0;
  const neo = {};
  for (const b of boxes) {
    const { x, y, w, h } = b.box;
    if (x < -GIAO_E || y < -GIAO_E || x + w > W + GIAO_E || y + h > H + GIAO_E) {
      r.push(`ANNOTATION_OUTSIDE_CANVAS:${b.id}`);
    }
    const ann = (scene?.objects ?? []).find((o) => o.id === b.id)?.annotation;
    const p = ann ? annotationWorldAnchor(scene, ann) : null;
    const s = p && camera ? chieuManHinh(camera, p) : null;
    if (!s || s.behind) { r.push(`ANNOTATION_ANCHOR_UNKNOWN:${b.id}`); continue; }
    const d = Math.hypot(Math.max(x - s.x, 0, s.x - x - w), Math.max(y - s.y, 0, s.y - y - h));
    neo[b.id] = { x: s.x, y: s.y, distance_px: Number(d.toFixed(2)) };
    if (d > 24 + GIAO_E) r.push(`ANNOTATION_FAR_FROM_SUBJECT:${b.id}:${d.toFixed(1)}`);
    for (const q of points) if (hopGiao(b.box, q)) r.push(`ANNOTATION_OVER_POINT_LABEL:${b.id}:${q.id}`);
  }
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      if (hopGiao(boxes[i].box, boxes[j].box)) r.push(`ANNOTATION_OVERLAP:${boxes[i].id}:${boxes[j].id}`);
    }
  }
  return { pass: r.length === 0, reason_codes: r, expected: mongDoi, shown: hien, anchors: neo };
}

/** §15.5 công tắc: tắt cả hai ⇒ 0 nhãn số đo trong DOM, và hình/camera/lựa chọn/nét đứt KHÔNG
 *  đổi giữa bật và tắt; bật lại ⇒ đúng tập nhãn cũ. */
export function assessToggleIsolation({ on, off, back }) {
  const r = [];
  if (off.annotation_dom_count !== 0) r.push(`TOGGLE_OFF_LEAVES_LABELS:${off.annotation_dom_count}`);
  for (const k of ["dash_signature", "rendered_object_ids", "camera", "selected_id", "step"]) {
    if (JSON.stringify(on[k]) !== JSON.stringify(off[k])) r.push(`TOGGLE_CHANGED_${k.toUpperCase()}`);
  }
  if (JSON.stringify(on.annotation_ids) !== JSON.stringify(back.annotation_ids)) r.push("TOGGLE_BACK_DIFFERENT_LABELS");
  return { pass: r.length === 0, reason_codes: r };
}

/** §15.5 nhân quả: trung tính → chọn → khôi phục (bỏ chọn, KHÔNG đặt lại camera) ở CÙNG camera và
 *  CÙNG vị trí cuộn. Ghi riêng ba thứ; khung canvas khôi phục phải trùng khung trung tính. */
export function assessCausalRestore({ neutral, selected, restored }) {
  const r = [];
  if (selected.selected_id === null) r.push("CAUSAL_NOT_SELECTED");
  if (restored.selected_id !== null) r.push("SELECTION_NOT_RESET");
  if (JSON.stringify(neutral.camera) !== JSON.stringify(selected.camera)) r.push("SELECTION_MOVED_CAMERA");
  if (JSON.stringify(neutral.camera) !== JSON.stringify(restored.camera)) r.push("RESTORE_MOVED_CAMERA");
  if (neutral.scroll_y !== restored.scroll_y) r.push("SCROLL_NOT_RESTORED");
  if (neutral.canvas_sha256 !== restored.canvas_sha256) r.push("CANVAS_NOT_RESTORED");
  return { pass: r.length === 0, reason_codes: r,
    camera_reset: JSON.stringify(neutral.camera) !== JSON.stringify(restored.camera),
    selection_reset: restored.selected_id === null,
    scroll: { neutral: neutral.scroll_y, selected: selected.scroll_y, restored: restored.scroll_y } };
}
