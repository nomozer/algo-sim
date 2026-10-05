/**
 * regular-square-pyramid-w02 · A — nhãn số đo chỉ hiện khi ĐỐI TƯỢNG MANG SỐ ĐO đã được dựng.
 *
 * Tái hiện trên fixture thật của bộ đo W1 (không dựng tay): chóp tam giác hiện `AB = 3`, `AC = 4`, `SA = 5` ở bước
 * 0 — trước khi đáy và đoạn SA được dựng; lăng trụ tam giác hiện `AD = 5` trước bước dựng các cạnh bên. Luật cũ chỉ
 * đòi hai ĐIỂM đầu mút có mặt. Luật mới đọc danh tính: một đoạn có `endpoint_ids` đó, một đa giác có cạnh đó, hay
 * một khối có cạnh đó (`edge_ownership`) phải đang có mặt ở bước. Không đọc tên họ, tên fixture hay lời kể.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import type { Scene3D } from "./scene3d-model";
import { geometryAnchor, geometryStepCount, anchorOfGeometryStep, quantityChoices } from "./scene3d-model";
import { annotationsAt, DEFAULT_ANNOTATION_VIEW } from "./scene3d-annotations";

const W1 = join(__dirname, "../../../../../docs/evaluation/geometry/runs/regular-square-pyramid-w01/inputs/fixtures");
const canh = (ten: string): Scene3D =>
  JSON.parse(readFileSync(join(W1, `${ten}.json`), "utf8")).envelope.scene3d as Scene3D;

const TAT_CA = { showAll: true };
/** Nhãn hiện ở bước dựng `g` (neo của bước), ở cả hai chế độ — "Hiện tất cả" không được lộ thêm. */
const nhan = (s: Scene3D, g: number, view = TAT_CA) =>
  annotationsAt(s, anchorOfGeometryStep(s, g), view, null).map((a) => a.id).sort();

describe("A · nhãn đoạn chờ đoạn được dựng", () => {
  it("chóp tam giác: AB, AC, SA không có nhãn trước khi đáy và SA được dựng", () => {
    const s = canh("triangular_pyramid_positive");
    expect(nhan(s, 0)).toEqual([]);
    expect(nhan(s, 0, DEFAULT_ANNOTATION_VIEW)).toEqual([]);
    // bước 1 dựng tam giác đáy ABC ⇒ AB, AC có chỗ bám; SA chưa
    expect(nhan(s, 1)).toEqual(["AB_length", "AC_length"]);
    // bước 2 dựng đoạn SA
    expect(nhan(s, 2)).toEqual(["AB_length", "AC_length", "SA_length"]);
  });

  it("lăng trụ tam giác: AD chỉ có nhãn từ bước dựng các cạnh bên", () => {
    const s = canh("triangular_prism_positive");
    const buocCanhBen = [...Array(geometryStepCount(s)).keys()].find((g) =>
      s.formation!.steps[anchorOfGeometryStep(s, g)].visible_ids.includes("canh_ben_A_D"))!;
    expect(buocCanhBen).toBeGreaterThan(0);
    for (let g = 0; g < buocCanhBen; g++) expect(nhan(s, g)).not.toContain("AD_length");
    expect(nhan(s, buocCanhBen)).toContain("AD_length");
  });

  it("nhãn đáy (cạnh của đa giác) và cạnh của khối là chỗ bám hợp lệ", () => {
    const s = canh("rectangular_pyramid_positive");
    expect(nhan(s, 1)).toEqual(["AB_length", "AD_length"]);
  });

  it("đối chứng: nhãn diện tích/thể tích vẫn theo luật cũ (chủ thể là vật, có mặt mới hiện)", () => {
    const s = canh("triangular_pyramid_positive");
    const cuoi = geometryStepCount(s) - 1;
    const k = s.formation!.steps.length - 1;
    const tatCa = annotationsAt(s, k, TAT_CA, null).map((a) => a.id);
    expect(tatCa).toEqual(expect.arrayContaining(["dien_tich_day_ABC", "the_tich_khoi_chop"]));
    expect(nhan(s, cuoi)).toEqual(expect.arrayContaining(["AB_length", "AC_length", "SA_length"]));
  });

  it("nhảy bước và lùi bước đều đọc trạng thái dựng của đúng bước ấy", () => {
    const s = canh("triangular_prism_positive");
    const cuoi = geometryStepCount(s) - 1;
    expect(nhan(s, cuoi)).toContain("AD_length");
    expect(nhan(s, 0)).not.toContain("AD_length");   // lùi về đầu sau khi đã ở cuối: không còn nhãn
    expect(annotationsAt(s, geometryAnchor(s, 0), TAT_CA, "AD_length").map((a) => a.id)).not.toContain("AD_length");
  });

  it("dữ kiện vẫn đọc được ở ngăn «Đại lượng» khi nhãn chưa hợp lệ trên hình", () => {
    const s = canh("triangular_pyramid_positive");
    expect(quantityChoices(s, 0).givens).toEqual(expect.arrayContaining(["AB_length", "AC_length", "SA_length"]));
  });
});
