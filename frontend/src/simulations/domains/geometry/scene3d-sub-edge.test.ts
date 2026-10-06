/**
 * regular-square-pyramid-w04 · yêu cầu 4 — đoạn nằm TRÊN cạnh khối có sẵn (SM, M trung điểm SA).
 *
 * Trình duyệt tại f3db0f6f (run w04, `diagnostics/sm_overlap/before/`): `doan_SM` vẽ nét liền riêng đè lên cạnh SA đang
 * nét đứt. Backend nay gắn đoạn con vào cạnh chuẩn (`boundary_edge_ids` + `edge_span`); ở đây: nó nhường nét như đoạn
 * trùng cạnh, vẫn bấm chọn được (vùng bấm), và khi được tô sáng thì chỉ KHÚC của nó trên owner của cạnh sáng lên.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { Scene3D } from "./scene3d-model";
import { objectsAt, stepCount } from "./scene3d-model";
import * as THREE from "three";
import {
  buildObject3D, canonicalEdgeMaterial, chiaKhucToSang, doanNhuongCanh, lamDiu, toSangCanhChuan,
  updateCanonicalEdgeVisibility,
} from "./scene3d-view";

const nap = (ten: string): Scene3D => JSON.parse(readFileSync(fileURLToPath(new URL(
  `../../../../../docs/evaluation/geometry/runs/regular-square-pyramid-w04/diagnostics/sm_overlap/fixtures/${ten}.json`,
  import.meta.url)), "utf8")).envelope.scene3d;
const TRUOC = nap("w04_sm_on_edge_sa_before");
const SAU = nap("w04_sm_on_edge_sa_after");
const cuoi = (s: Scene3D) => objectsAt(s, stepCount(s) - 1);
const cungCho = () => "0,0,0";

describe("W4 · đoạn con trên cạnh khối", () => {
  it("trước bản sửa SM vẽ nét riêng; sau bản sửa nó nhường nét cho cạnh S-A như đoạn trùng cạnh", () => {
    expect(doanNhuongCanh(cuoi(TRUOC), cungCho).has("doan_SM")).toBe(false);
    const nhuong = doanNhuongCanh(cuoi(SAU), cungCho);
    expect(nhuong.has("doan_SM")).toBe(true);
    expect(nhuong.has("canh_ben_S_A")).toBe(true);
  });

  it("chọn SM chỉ tô KHÚC [0, ½] của owner S-A; chọn cạnh bên SA tô cả cạnh", () => {
    const vat = cuoi(SAU);
    const mau = () => 7;
    const sm = toSangCanhChuan(vat, (id) => id === "doan_SM", mau);
    expect(sm.ca.has("S.ABCD::edge:S-A")).toBe(false);
    expect(sm.khuc.get("S.ABCD::edge:S-A")).toEqual({ t0: 0, t1: 0.5, mau: 7 });
    const sa = toSangCanhChuan(vat, (id) => id === "canh_ben_S_A", mau);
    expect(sa.ca.get("S.ABCD::edge:S-A")).toBe(7);
    expect(sa.khuc.size).toBe(0);
  });

  it("chia khúc: mỗi đoạn khuất/hiện cắt tại biên khúc, chỉ phần trong khúc sáng", () => {
    const spans = [{ t0: 0, t1: 0.3, visibility: "VISIBLE" }, { t0: 0.3, t1: 1, visibility: "HIDDEN" }];
    expect(chiaKhucToSang(spans, { t0: 0, t1: 0.5 })).toEqual([
      { t0: 0, t1: 0.3, visibility: "VISIBLE", sang: true },
      { t0: 0.3, t1: 0.5, visibility: "HIDDEN", sang: true },
      { t0: 0.5, t1: 1, visibility: "HIDDEN", sang: false },
    ]);
    expect(chiaKhucToSang(spans, undefined)).toEqual(spans.map((s) => ({ ...s, sang: false })));
  });

  /* Bằng chứng trình duyệt W4 (lần đo 3, `images/sm-overlap-after-selected/sm_selected.png`): chọn SM thì khối S.ABCD
     NGOÀI chuỗi nhân quả của SM ⇒ cả khối bị làm dịu — kể cả khúc S–M vừa tô, nên trên hình không thấy gì sáng. Cạnh
     tô CẢ cạnh đã được miễn làm dịu; khúc tô sáng phải được miễn như thế, lúc dựng lẫn lúc dựng lại khi xoay. */
  it("khúc tô sáng không bị làm dịu khi khối nằm ngoài chuỗi nhân quả (lúc dựng và khi dựng lại)", () => {
    const khoi = SAU.objects.find((o) => o.type === "solid")!;
    const MAU = 0x2563eb;
    const dung = () => buildObject3D(khoi, false, undefined, undefined, undefined, new Map(),
      new Map([["S.ABCD::edge:S-A", { t0: 0, t1: 0.5, mau: MAU }]]))!;
    const ownerCua = (goc: THREE.Object3D) => {
      let o: THREE.Object3D | undefined;
      goc.traverse((x) => { if (x.userData?.visualOwnerId === "S.ABCD::edge:S-A") o = x; });
      return o!;
    };
    // mốc: vật liệu tô sáng CHƯA làm dịu của đúng kiểu nét (khuất/hiện) — mỗi kiểu có độ mờ riêng
    const moc = (l: THREE.Line) => canonicalEdgeMaterial(l.userData.hidden === true, true, 0, 0.1, MAU).opacity;
    const obj = dung();
    lamDiu(obj);
    const owner = () => ownerCua(obj);
    const kiem = () => {
      const lines = owner().children as THREE.Line[];
      const sang = lines.filter((l) => l.userData.sang === true);
      expect(sang.length).toBeGreaterThan(0);
      for (const l of sang) {
        const m = l.material as THREE.LineBasicMaterial;
        expect(m.opacity).toBe(moc(l));
        expect(m.color.getHex()).toBe(MAU);
      }
      for (const l of lines.filter((x) => x.userData.sang !== true)) {
        expect((l.material as THREE.Material).opacity).toBeLessThan(1);
      }
    };
    kiem();
    // dựng lại owner như khi xoay (chữ ký khúc khuất/hiện đổi)
    owner().userData.spanSignature = "buoc-dung-lai";
    const cam = new THREE.PerspectiveCamera(45, 1.5, 0.1, 100);
    cam.position.set(-6, 4, 8);
    cam.lookAt(0, 0, 0);
    cam.updateMatrixWorld();
    obj.updateMatrixWorld(true);
    updateCanonicalEdgeVisibility(obj, cam);
    kiem();
  });
});
