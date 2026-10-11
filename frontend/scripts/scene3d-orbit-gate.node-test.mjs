/**
 * scene3d-orbit-gate.node-test.mjs — pure parts of orbit gate v2 (protocol:
 * docs/evaluation/geometry/runs/orbit-gate-v2/protocol.md). Does not open Chrome.
 * Browser validation (known-good window + known-bad injections): run `orbit-gate-v2`.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { GATE_VERSION, KEO, NGUONG, TRANG_THAI, doDaiKeoNgang, phanLoai } from "./scene3d-orbit-gate.mjs";

/** A result that passes every v1 check — each test breaks exactly one thing. */
const dat = () => ({
  docDuocCamera: true, draws: 10, chuanTruc: 1, vongNgangDo: 450,
  huong: { tren: true, duoi: true }, snap: 0, capPhat: 0, khongOnDinh: false, khungHep: false,
});

test("identity is v2", () => {
  assert.equal(GATE_VERSION, "scene3d-orbit-gate/2");
});

test("thresholds are exactly v1's — v2 only changes how the drag is made and read", () => {
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

test("settle budget is an explicit timeout", () => {
  assert.equal(KEO.CHO_ON_DINH_MS, 10_000);
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
