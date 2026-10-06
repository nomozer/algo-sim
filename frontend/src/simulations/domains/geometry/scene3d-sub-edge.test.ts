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
import { chiaKhucToSang, doanNhuongCanh, toSangCanhChuan } from "./scene3d-view";

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
});
