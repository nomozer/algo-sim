/**
 * scene3d-orbit-gate.node-test.mjs — pure parts of the orbit gate (v3 protocol:
 * docs/evaluation/geometry/runs/orbit-gate-v2/protocol-v3.md; v2 failed its validation and is on record there).
 * Does not open Chrome. Browser validation (known-good window + known-bad injections): run `orbit-gate-v2`.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  GATE_VERSION, KEO, NGUONG, TRANG_THAI, daLang, doDaiKeoNgang, phanLoai, tongGocKhung, trucQuay,
} from "./scene3d-orbit-gate.mjs";

/** A result that passes every v1 check — each test breaks exactly one thing. */
const dat = () => ({
  docDuocCamera: true, draws: 10, chuanTruc: 1, vongNgangDo: 450,
  huong: { tren: true, duoi: true }, snap: 0, capPhat: 0, khongOnDinh: false, khungHep: false,
});

// ── synthetic view matrices (column-major 4×4, rotation only) ──
const nhan = (A, B) => A.map((r, i) => B[0].map((_, j) => r.reduce((s, _x, k) => s + A[i][k] * B[k][j], 0)));
const quay = (truc, a) => {
  const [x, y, z] = truc, c = Math.cos(a), s = Math.sin(a), t = 1 - c;
  return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
    [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
    [t * x * z - s * y, t * y * z + s * x, t * z * z + c]];
};
const m16 = (R) => [R[0][0], R[1][0], R[2][0], 0, R[0][1], R[1][1], R[2][1], 0, R[0][2], R[1][2], R[2][2], 0, 0, 0, 0, 1];
const DO = Math.PI / 180;

/** 50 frames turning 5° about Z, then a damping tail of 200 micro-rotations alternating about X and Y. */
function quayRoiDuoi() {
  let R = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  const tuThe = [{ m: m16(R), f: 0 }];
  for (let i = 1; i <= 50; i++) { R = nhan(R, quay([0, 0, 1], 5 * DO)); tuThe.push({ m: m16(R), f: i }); }
  for (let i = 1; i <= 200; i++) {
    R = nhan(R, quay(i % 2 ? [1, 0, 0] : [0, 1, 0], 1e-6));
    tuThe.push({ m: m16(R), f: 50 + i });
  }
  return tuThe;
}

test("identity is v3", () => {
  assert.equal(GATE_VERSION, "scene3d-orbit-gate/3");
});

test("thresholds are exactly v1's", () => {
  assert.deepEqual(NGUONG, { CHUAN_TRUC: 0.99, VONG_NGANG_DO: 360, COS_CUC: 0.9, SNAP_DO: 25 });
});

test("horizontal drag scales with canvas height (OrbitControls rotates 2π·dx/clientHeight)", () => {
  assert.equal(KEO.NGANG_THEO_CAO, 1.25);
  assert.equal(doDaiKeoNgang(545), 681);
  assert.equal(doDaiKeoNgang(683), 854);
  for (const h of [300, 545, 683, 900, 1200]) {
    const doNominal = (360 * doDaiKeoNgang(h)) / h;
    assert.ok(doNominal >= 449 && doNominal <= 451, `${h}px → ${doNominal}°`);
  }
});

test("settle parameters are the registered ones", () => {
  assert.equal(KEO.CHO_ON_DINH_MS, 20_000);
  assert.equal(KEO.KHUNG_LANG, 30);
  assert.equal(KEO.NGUONG_LANG_DO, 0.01);
});

test("axis consistency is angle-weighted: a near-static tail cannot dilute a real rotation (v2 defect)", () => {
  const tuThe = quayRoiDuoi();
  const t = trucQuay(tuThe);
  assert.ok(t.chuan >= 0.999, `chuan=${t.chuan}`);
  assert.deepEqual(t.vec, [0, 0, 1]);
  // 50 × 5° plus the tail's 200 × 1e-6 rad (≈ 0.0115°)
  assert.ok(Math.abs(tongGocKhung(tuThe) - (250 + 200 * 1e-6 / DO)) < 1e-3);
});

test("a genuinely drifting axis still fails consistency", () => {
  let R = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  const tuThe = [{ m: m16(R), f: 0 }];
  for (let i = 1; i <= 60; i++) { R = nhan(R, quay(i % 2 ? [1, 0, 0] : [0, 0, 1], 5 * DO)); tuThe.push({ m: m16(R), f: i }); }
  assert.ok(trucQuay(tuThe).chuan < NGUONG.CHUAN_TRUC);
});

test("settled = every per-frame rotation in the last 30 animation frames is under 0.01°", () => {
  const tuThe = quayRoiDuoi();               // last 5° turn at frame 50, then 1e-6 rad steps to frame 250
  assert.equal(daLang(tuThe, 250), true);    // window 220..250 holds only micro-steps
  assert.equal(daLang(tuThe, 60), false);    // window 30..60 still holds 5° turns
  assert.equal(daLang(tuThe.slice(0, 51), 120), true);   // no pose since frame 50 ⇒ camera static
  assert.equal(daLang(tuThe.slice(0, 51), 70), false);   // frame 50 (a 5° turn) is inside 40..70
  assert.equal(daLang([], 10), false);       // fewer than 30 frames observed ⇒ cannot conclude
});

test("a camera that never settled is a named failure, before any angle is trusted", () => {
  assert.equal(phanLoai(dat()), TRANG_THAI.DAT);
  assert.equal(phanLoai({ ...dat(), khongOnDinh: true }), TRANG_THAI.KHONG_ON_DINH);
  assert.equal(phanLoai({ ...dat(), khongOnDinh: true, vongNgangDo: 100 }), TRANG_THAI.KHONG_ON_DINH);
});

test("a drag that cannot fit in the canvas is a named failure, never clipped silently", () => {
  assert.equal(phanLoai({ ...dat(), khungHep: true }), TRANG_THAI.KHUNG_HEP);
});

test("v1 classifications are unchanged", () => {
  assert.equal(phanLoai({ ...dat(), docDuocCamera: false }), TRANG_THAI.KHONG_DOC_DUOC_CAMERA);
  assert.equal(phanLoai({ ...dat(), draws: 0 }), TRANG_THAI.CANH_RONG);
  assert.equal(phanLoai({ ...dat(), chuanTruc: 0.98 }), TRANG_THAI.TRUC_TROI);
  assert.equal(phanLoai({ ...dat(), vongNgangDo: 359.9 }), TRANG_THAI.KHONG_DU_VONG);
  assert.equal(phanLoai({ ...dat(), huong: { tren: true, duoi: false } }), TRANG_THAI.THIEU_HUONG_NHIN);
  assert.equal(phanLoai({ ...dat(), snap: 1 }), TRANG_THAI.CO_SNAP);
  assert.equal(phanLoai({ ...dat(), capPhat: 1 }), TRANG_THAI.TU_KHOP_KHUNG);
});
