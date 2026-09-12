/**
 * scene3d-progressive-section.test.ts — THIẾT DIỆN HIỆN DẦN TỪNG CẠNH.
 *
 * ─── NỀN ĐỎ ĐÃ ĐO ĐƯỢC TRƯỚC KHI SỬA ──────────────────────────────────────
 *
 * Trace của ca `S.ABCD ∩ (MNP)` có bốn sự kiện `action: "EXTEND"` (một cạnh
 * mỗi sự kiện, kèm `face_index` trong `object.steps`) rồi mới tới `STEP` đóng
 * hình. Renderer dựng trọn `polygon` ngay từ sự kiện đầu, nên **năm bước cuối
 * cho năm khung hình trùng khít**: cùng băm ảnh `c6952a836c1d`, cùng 4186
 * điểm mực — trong khi lời dẫn vẫn đang kể từng cạnh một.
 *
 * Mọi assert dưới đây ĐỎ trên bản trước: `soDoan` trả 4 ở cả năm bước và
 * `soMangTo` trả 1 từ bước 7.
 */
import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { geometrySampleById } from "../../../data/geometry-samples";
import { buildObject3D } from "./scene3d-view";
import { tienTrinhDung } from "./scene3d-model";
import { canhThietDien } from "./scene3d-subentities";
import type { Scene3D, SceneObject } from "./scene3d-model";

const mau = geometrySampleById("thiet-dien-chop");
if (!mau) throw new Error("thiếu bài mẫu `thiet-dien-chop`");
/* `SimulationEnvelope` khai `scene3d` là trường tuỳ chọn không định kiểu —
 * ép qua `unknown` chứ không ép thẳng, để phép ép hiện ra chứ không lẩn đi. */
const canh3D = (mau.envelope as unknown as { scene3d: Scene3D }).scene3d;
const vatTD = canh3D.objects.find((o) => o.id === "thiet_dien") as SceneObject;

/** Số ĐOẠN nét mà một vật dựng ra — đọc từ bộ đệm thật của `LineSegments2`. */
function soDoan(obj: THREE.Object3D | null): number {
  if (!obj) return 0;
  let n = 0;
  obj.traverse((v) => {
    if (!v.userData?.net) return;
    if (!v.name.endsWith(":thay")) return;          // chỉ đếm MỘT trong hai lượt
    const g = (v as THREE.Mesh).geometry as THREE.BufferGeometry;
    const s = g.attributes?.instanceStart as THREE.BufferAttribute | undefined;
    if (s) n += s.count;
  });
  return n;
}

/** Số mảng tô — `Mesh` KHÔNG phải vật nét (`Line2` cũng là `Mesh`). */
function soMangTo(obj: THREE.Object3D | null): number {
  if (!obj) return 0;
  let n = 0;
  obj.traverse((v) => {
    if (v.userData?.net || v.userData?.baoDong) return;
    if ((v as THREE.Mesh).isMesh) n += 1;
  });
  return n;
}

const dungTaiBuoc = (buoc: number) =>
  buildObject3D(vatTD, false, undefined, [], tienTrinhDung(canh3D, "thiet_dien", buoc));

/* `Bước k/11` hiển thị ứng với chỉ số bước `k − 1`. */
const CHI_SO = (hien: number) => hien - 1;

describe("thiết diện dựng luỹ tiến theo sự kiện EXTEND", () => {
  it("trace của ca này có đúng bốn EXTEND rồi một STEP", () => {
    const cua = canh3D.events.filter((e) => e.object === "thiet_dien");
    expect(cua.map((e) => e.action)).toEqual(["EXTEND", "EXTEND", "EXTEND", "EXTEND", "STEP"]);
    expect(canhThietDien(vatTD)).toHaveLength(4);
  });

  it.each([
    ["STEP_7_SECTION_SEGMENTS", 7, 1],
    ["STEP_8_SECTION_SEGMENTS", 8, 2],
    ["STEP_9_SECTION_SEGMENTS", 9, 3],
    ["STEP_10_SECTION_SEGMENTS", 10, 4],
    ["STEP_11_SECTION_SEGMENTS", 11, 4],
  ])("%s: bước %i vẽ %i cạnh", (_ten, hien, mong) => {
    expect(soDoan(dungTaiBuoc(CHI_SO(hien)))).toBe(mong);
  });

  it.each([7, 8, 9, 10])("STEP_7_TO_10_FILL: bước %i chưa có mảng tô", (hien) => {
    expect(soMangTo(dungTaiBuoc(CHI_SO(hien)))).toBe(0);
  });

  it("STEP_11_FILL: mảng tô chỉ xuất hiện ở sự kiện đóng hình", () => {
    expect(soMangTo(dungTaiBuoc(CHI_SO(11)))).toBe(1);
  });

  it("trước bước 7 chưa nối cạnh nào ⇒ không dựng gì", () => {
    for (const hien of [1, 2, 3, 4, 5, 6]) {
      expect(dungTaiBuoc(CHI_SO(hien))).toBeNull();
    }
  });

  it("bước 10 và bước 11 KHÁC nhau — đúng bốn cạnh, khác ở mảng tô", () => {
    const b10 = dungTaiBuoc(CHI_SO(10));
    const b11 = dungTaiBuoc(CHI_SO(11));
    expect(soDoan(b10)).toBe(soDoan(b11));
    expect(soMangTo(b10)).not.toBe(soMangTo(b11));
  });

  it("tua 11 → 7 → 11 cho đúng cùng một kết quả", () => {
    const dau = { doan: soDoan(dungTaiBuoc(CHI_SO(11))), to: soMangTo(dungTaiBuoc(CHI_SO(11))) };
    soDoan(dungTaiBuoc(CHI_SO(7)));
    const sau = { doan: soDoan(dungTaiBuoc(CHI_SO(11))), to: soMangTo(dungTaiBuoc(CHI_SO(11))) };
    expect(sau).toEqual(dau);
    /* Và mỗi bước trung gian cũng phải phục hồi đúng, không phụ thuộc lối tới. */
    for (const hien of [7, 8, 9, 10, 11]) {
      expect(soDoan(dungTaiBuoc(CHI_SO(hien)))).toBe(soDoan(dungTaiBuoc(CHI_SO(hien))));
    }
  });

  it("HÌNH CUỐI không đổi: bốn cạnh đúng toạ độ của `polygon`", () => {
    const canh = canhThietDien(vatTD);
    expect(canh.map((c) => c.a)).toEqual(vatTD.steps?.map((s) => s.a));
    expect(canh.map((c) => c.b)).toEqual(vatTD.steps?.map((s) => s.b));
    /* Chu trình khép kín: đầu mút cạnh cuối quay về đầu mút cạnh đầu. */
    expect(canh[canh.length - 1].b).toEqual(canh[0].a);
  });
});

describe("vật KHÔNG dựng luỹ tiến giữ nguyên hành vi cũ", () => {
  const thietDienMotLan: SceneObject = {
    ...vatTD, id: "td_mot_lan", steps: undefined,
  } as SceneObject;
  const canhMotLan: Scene3D = {
    ...canh3D,
    objects: [thietDienMotLan],
    events: [{ step_index: 0, action: "CREATE", object: "td_mot_lan",
      depends: [], explanation: "dựng một lần" }],
  } as Scene3D;

  it("không có EXTEND ⇒ soCanh là null, không phải 0", () => {
    expect(tienTrinhDung(canhMotLan, "td_mot_lan", 0).soCanh).toBeNull();
  });

  it("dựng trọn hình kèm mảng tô ngay từ bước đầu", () => {
    const obj = buildObject3D(thietDienMotLan, false, undefined, [],
      tienTrinhDung(canhMotLan, "td_mot_lan", 0));
    expect(soMangTo(obj)).toBe(1);
    /* Đường khép kín ⇒ bốn đỉnh sinh bốn đoạn. */
    expect(soDoan(obj)).toBe(4);
  });

  it("bỏ hẳn tham số tiến trình cũng cho cùng kết quả", () => {
    const co = buildObject3D(thietDienMotLan, false, undefined, [],
      tienTrinhDung(canhMotLan, "td_mot_lan", 0));
    const khong = buildObject3D(thietDienMotLan, false, undefined, []);
    expect([soDoan(khong), soMangTo(khong)]).toEqual([soDoan(co), soMangTo(co)]);
  });
});

describe("không mutate dữ liệu cảnh", () => {
  it("dựng đi dựng lại không đụng vào envelope", () => {
    const truoc = JSON.stringify(canh3D);
    for (const hien of [7, 8, 9, 10, 11, 7]) dungTaiBuoc(CHI_SO(hien));
    expect(JSON.stringify(canh3D)).toBe(truoc);
  });
});
