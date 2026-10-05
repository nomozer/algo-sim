/**
 * regular-square-pyramid-w01 — chín chỉnh sửa giao diện đã chốt (ROADMAP §0.1), phần kiểm được không cần WebGL.
 * **0 mạng, 0 LLM.** Cùng luật với `Scene3DExplorer.test.tsx`: quyết định nằm ở hàm thuần, component kiểm qua
 * `renderToString` và cấu trúc mã nguồn; bấm thật, đồng bộ panel ↔ phát lại và đo bố cục ở bộ đo trình duyệt.
 */
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import type { Scene3D } from "./scene3d-model";
import {
  anchorOfGeometryStep,
  geometryStepCount,
  geometryStepList,
  quantityChoices,
} from "./scene3d-model";
import { Scene3DPlayer } from "./scene3d-playback";
import { Scene3DSolution } from "./scene3d-solution";

const CANH: Scene3D = JSON.parse(readFileSync(fileURLToPath(new URL(
  "../../../../../docs/evaluation/geometry/runs/w11-pedagogical-polish/inputs/fixtures/rectangular_pyramid_positive.json",
  import.meta.url)), "utf8")).envelope.scene3d;
const CUOI = anchorOfGeometryStep(CANH, geometryStepCount(CANH) - 1);
const sach = (h: string) => h.replace(/<!--.*?-->/g, "");
const nguon = (f: string) => readFileSync(new URL(f, import.meta.url), "utf8");

describe("§0.1-1 · card Kết quả ẩn mặc định", () => {
  it("lời giải thu gọn ⇒ không có mục Kết quả dưới hình; mở ⇒ có", () => {
    const thu = sach(renderToString(<Scene3DSolution scene={CANH} step={CUOI} open={false} />));
    const mo = sach(renderToString(<Scene3DSolution scene={CANH} step={CUOI} open />));
    expect(thu).not.toContain("geo3d-lg-ket-qua");
    expect(thu).toContain('aria-expanded="false"');
    expect(mo).toContain("geo3d-lg-ket-qua");
  });
});

describe("§0.1-2 · mọi kết quả qua nút chọn đại lượng + một ô chi tiết", () => {
  it("danh sách đại lượng ở bước: kết quả trước, rồi đại lượng trung gian, rồi dữ kiện; không trùng", () => {
    const c = quantityChoices(CANH, CUOI);
    expect(c.results.length).toBeGreaterThan(0);
    const moi = [...c.results, ...c.steps, ...c.givens];
    expect(new Set(moi).size).toBe(moi.length);
    for (const id of moi) expect(CANH.objects.find((o) => o.id === id)?.type).toBe("quantity");
  });

  it("bước đầu (chưa tính gì) không có kết quả để chọn", () => {
    expect(quantityChoices(CANH, 0).results).toEqual([]);
  });

  it("xưởng có nút «Đại lượng»; chọn một đại lượng đóng ngăn và mở ô soi của nó (một nơi chi tiết)", () => {
    const src = nguon("./Scene3DExplorer.tsx");
    expect(src).toContain("Đại lượng");
    expect(src).toMatch(/ngan === "dai-luong"/);
    expect(src).toMatch(/chon\(id\);\s*setNgan\(null\)/);
  });
});

describe("§0.1-3/4/5 · «Các bước dựng»", () => {
  it("danh sách = đúng các bước DỰNG (không bước tính), mỗi bước một nhãn và một neo", () => {
    const ds = geometryStepList(CANH);
    expect(ds.length).toBe(geometryStepCount(CANH));
    ds.forEach((b, k) => {
      expect(b.index).toBe(k);
      expect(b.anchor).toBe(anchorOfGeometryStep(CANH, k));
      expect(b.label.trim().length).toBeGreaterThan(0);
    });
  });

  it("nút mở nằm trong thanh điều khiển; đóng ⇒ không có danh sách; mở ⇒ một nút mỗi bước, bước hiện tại đánh dấu", () => {
    const dong = sach(renderToString(<Scene3DPlayer scene={CANH} stepsOpen={false} />));
    expect(dong).toContain("Các bước dựng");
    expect(dong).toMatch(/aria-expanded="false"[^>]*>[^<]*(<svg[\s\S]*?<\/svg>)?\s*Các bước dựng/);
    expect(dong).not.toContain("geo3d-cac-buoc-ds");
    const mo = sach(renderToString(<Scene3DPlayer scene={CANH} stepsOpen />));
    const so = (mo.match(/data-geometry-step="/g) ?? []).length;
    expect(so).toBe(geometryStepCount(CANH));
    expect((mo.match(/aria-current="step"/g) ?? []).length).toBe(1);
  });

  it("chọn một bước: dừng phát rồi đặt bước theo neo (đồng bộ hình, thanh bước, phát lại); không bỏ chọn", () => {
    const src = nguon("./scene3d-playback.tsx");
    expect(src).toMatch(/setDangPhat\(false\);\s*setStep\(b\.anchor\)/);
    expect(src).not.toMatch(/setStep\(b\.anchor[^)]*true/);
  });

  it("trạng thái mở panel do xưởng giữ — đóng/mở không đụng `InteractionState`", () => {
    const src = nguon("./Scene3DExplorer.tsx");
    expect(src).toMatch(/stepsOpen=\{moBuoc\}/);
    expect(src).toMatch(/onStepsOpenChange=\{setMoBuoc\}/);
  });

  it("mobile: panel trong dòng chảy dưới điều khiển, cuộn bên trong, không phủ lên khung", () => {
    const css = nguon("../../../styles/global.css");
    const khoi = css.slice(css.indexOf(".geo3d-cac-buoc {"), css.indexOf("}", css.indexOf(".geo3d-cac-buoc {")));
    expect(khoi).toContain("overflow-y: auto");
    expect(khoi).not.toContain("position: absolute");
  });
});

describe("§0.1-8 · bớt dòng mô tả lặp", () => {
  it("không còn dải «Đang dựng / Dựa trên» — dòng thuyết minh và ô soi đã nói điều ấy", () => {
    expect(nguon("./scene3d-playback.tsx")).not.toContain("geo3d-focus");
    expect(sach(renderToString(<Scene3DPlayer scene={CANH} />))).not.toContain("Đang dựng");
  });
});
