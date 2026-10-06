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
  objectsAt,
  quantityChoices,
} from "./scene3d-model";
import { auxiliaryHiddenAt } from "./scene3d-auxiliary";
import { Scene3DPlayer } from "./scene3d-playback";
import { Scene3DSolution } from "./scene3d-solution";

const CANH: Scene3D = JSON.parse(readFileSync(fileURLToPath(new URL(
  "../../../../../docs/evaluation/geometry/runs/w11-pedagogical-polish/inputs/fixtures/rectangular_pyramid_positive.json",
  import.meta.url)), "utf8")).envelope.scene3d;
const CUOI = anchorOfGeometryStep(CANH, geometryStepCount(CANH) - 1);
const sach = (h: string) => h.replace(/<!--.*?-->/g, "");
// Checkout Windows (CRLF) phải cho cùng kết quả: so mẫu nhiều dòng trên "\n".
const nguon = (f: string) => readFileSync(new URL(f, import.meta.url), "utf8").replace(/\r\n/g, "\n");

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
    // Bộ đo trình duyệt bấm đúng đại lượng qua id máy — thuộc tính dữ liệu, không phải chữ hiển thị.
    expect(src).toMatch(/data-quantity-id=\{id\}/);
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
    // W2 · B: cuộn bên trong chuyển từ danh sách sang THÂN bảng nổi; khổ hẹp đưa bảng về dòng chảy (static).
    const css = nguon("../../../styles/global.css");
    const khoi = (sel: string, tu = 0) => css.slice(css.indexOf(sel, tu), css.indexOf("}", css.indexOf(sel, tu)));
    expect(khoi(".geo3d-bang-noi-than {")).toContain("overflow-y: auto");
    const hep = css.indexOf("@media (max-width: 48rem) {\n  .geo3d-bang-noi {");
    expect(hep).toBeGreaterThan(0);
    expect(khoi(".geo3d-bang-noi {", hep)).toContain("position: static");
  });
});

describe("§0.1-8 · bớt dòng mô tả lặp", () => {
  it("không còn dải «Đang dựng / Dựa trên» — dòng thuyết minh và ô soi đã nói điều ấy", () => {
    expect(nguon("./scene3d-playback.tsx")).not.toContain("geo3d-focus");
    expect(sach(renderToString(<Scene3DPlayer scene={CANH} />))).not.toContain("Đang dựng");
  });
});

describe("W2 · B · bảng nổi «Các bước dựng»", () => {
  it("kẹp trong vùng mô phỏng: kéo ra ngoài mọi phía vẫn để nguyên bảng (và nút đóng) trong khung", async () => {
    const { kepBang, LE_BANG } = await import("./scene3d-floating-panel");
    const khung = { x: 0, y: 0, w: 800, h: 500 };
    const co = { w: 272, h: 300 };
    expect(kepBang({ x: -500, y: -500 }, co, khung)).toEqual({ x: LE_BANG, y: LE_BANG });
    expect(kepBang({ x: 5000, y: 5000 }, co, khung)).toEqual({ x: 800 - 272 - LE_BANG, y: 500 - 300 - LE_BANG });
    // khung thu lại (đổi cỡ cửa sổ) sau khi đã kéo: vị trí cũ bị kẹp lại vào trong
    expect(kepBang({ x: 500, y: 150 }, co, { ...khung, w: 600, h: 400 })).toEqual({ x: 600 - 272 - LE_BANG, y: 400 - 300 - LE_BANG });
    // bảng cao hơn khung ⇒ dính lề trên (tiêu đề + nút đóng vẫn thấy)
    expect(kepBang({ x: 10, y: 99 }, { w: 272, h: 900 }, khung).y).toBe(LE_BANG);
  });

  it("vị trí mặc định ở phía phải vùng mô phỏng; phím mũi tên dời bảng, Shift dời xa hơn", async () => {
    const { viTriMacDinh, dichBangPhim, BUOC_PHIM } = await import("./scene3d-floating-panel");
    const p = viTriMacDinh({ w: 272, h: 300 }, { x: 0, y: 10, w: 1000, h: 560 });
    expect(p.x).toBeGreaterThan(1000 / 2);
    expect(p.y).toBeLessThan(560 / 4);
    expect(dichBangPhim({ x: 100, y: 100 }, "ArrowLeft", false)).toEqual({ x: 100 - BUOC_PHIM, y: 100 });
    expect(dichBangPhim({ x: 100, y: 100 }, "ArrowDown", true)).toEqual({ x: 100, y: 100 + 4 * BUOC_PHIM });
    expect(dichBangPhim({ x: 100, y: 100 }, "Enter", false)).toBeNull();
  });

  it("không còn cột lưới: mở bảng không đổi lưới/kích thước của trình phát", () => {
    const css = nguon("../../../styles/global.css");
    expect(css).not.toContain("co-cac-buoc");
    const mo = sach(renderToString(<Scene3DPlayer scene={CANH} stepsOpen />));
    const dong = sach(renderToString(<Scene3DPlayer scene={CANH} stepsOpen={false} />));
    const lop = (h: string) => h.match(/class="(geo3d-player[^"]*)"/)?.[1];
    expect(lop(mo)).toBe(lop(dong));
    expect(mo).toContain("geo3d-bang-noi");
  });

  it("nút ở phía phải thanh điều khiển; aria-controls chỉ trỏ tới bảng khi bảng có mặt", () => {
    const dong = sach(renderToString(<Scene3DPlayer scene={CANH} stepsOpen={false} />));
    const mo = sach(renderToString(<Scene3DPlayer scene={CANH} stepsOpen />));
    const nut = (h: string) => h.match(/<button[^>]*geo3d-cac-buoc-mo[^>]*>/)?.[0] ?? "";
    expect(nut(dong)).not.toContain("aria-controls");
    const id = nut(mo).match(/aria-controls="([^"]+)"/)?.[1];
    expect(id).toBeTruthy();
    expect(mo).toContain(`id="${id}"`);
    // nút mở là phần tử cuối của thanh điều khiển (sau thanh bước)
    const dieuKhien = dong.slice(dong.indexOf("geo3d-controls"));
    expect(dieuKhien.indexOf("geo3d-scrub")).toBeLessThan(dieuKhien.indexOf("geo3d-cac-buoc-mo"));
  });

  it("bảng có đóng, về vị trí mặc định, thu gọn và tiêu đề nhận bàn phím", () => {
    const mo = sach(renderToString(<Scene3DPlayer scene={CANH} stepsOpen />));
    expect(mo).toContain('aria-label="Đóng các bước dựng"');
    // không trùng tên với nút "Đóng" của ngăn / ô soi
    expect(mo).not.toContain('aria-label="Đóng"');
    expect(mo).toContain('aria-label="Về vị trí mặc định"');
    expect(mo).toContain('aria-label="Thu gọn bảng"');
    expect(mo).toMatch(/class="geo3d-bang-noi-dau" tabindex="0"/);
  });
});

/* regular-square-pyramid-w03 · H-W2-4. W2 mở một bước dựng cho «Mặt phẳng qua A, B, C» — mặt phẳng chỉ làm toán hạng
 * của chiều cao, ẩn mặc định — nên bước ấy KHÔNG đổi hình khi hình phụ tắt (bất biến W12), và W2 nới ba cổng để nó
 * qua. Thay chú thích «hình phụ, đang ẩn» bằng gốc: mặt phẳng chỉ để đo không mở bước dựng. */
describe("W3 · H-W2-4 · mặt phẳng phụ chỉ để đo không mở bước dựng", () => {
  const RSP: Scene3D = JSON.parse(readFileSync(fileURLToPath(new URL(
    "../../../../../docs/evaluation/geometry/runs/regular-square-pyramid-w02/inputs/fixtures/regular_square_pyramid_positive.json",
    import.meta.url)), "utf8")).envelope.scene3d;
  const hinhTrungTinh = (sc: Scene3D, g: number) => {
    const k = anchorOfGeometryStep(sc, g);
    const an = auxiliaryHiddenAt(sc, k, false, null);
    return JSON.stringify(objectsAt(sc, k)
      .filter((o) => o.render !== "readout" && o.render !== "non_visual" && !an.has(o.id)).map((o) => o.id).sort());
  };

  it("mọi bước dựng sau bước 0 đổi hình trung tính (hình phụ tắt, không chọn gì)", () => {
    const tinh = Array.from({ length: geometryStepCount(RSP) }, (_, g) => g)
      .filter((g) => g > 0 && hinhTrungTinh(RSP, g) === hinhTrungTinh(RSP, g - 1));
    expect(tinh).toEqual([]);
  });

  it("danh sách bước không có bước riêng cho mặt phẳng ấy; bật «Hình phụ» thì nó hiện ở khung cuối", () => {
    const html = sach(renderToString(<Scene3DPlayer scene={RSP} stepsOpen />));
    expect(html).not.toContain("Mặt phẳng qua A, B, C");
    expect(html).not.toContain("hình phụ, đang ẩn");
    const cuoi = anchorOfGeometryStep(RSP, geometryStepCount(RSP) - 1);
    expect(objectsAt(RSP, cuoi).map((o) => o.id)).toContain("mp_day");
    expect(auxiliaryHiddenAt(RSP, cuoi, false, null).has("mp_day")).toBe(true);
    expect(auxiliaryHiddenAt(RSP, cuoi, true, null).has("mp_day")).toBe(false);
  });

  it("mặt phẳng KHÔNG phải hình phụ chỉ để đo vẫn mở bước của nó", () => {
    const sc: Scene3D = JSON.parse(JSON.stringify(RSP));
    const mp = sc.objects.find((o) => o.id === "mp_day")!;
    mp.formation_roles = ["CONSTRUCT_CUTTING_OBJECT"];
    expect(geometryStepCount(sc)).toBe(geometryStepCount(RSP) + 1);
    expect(sach(renderToString(<Scene3DPlayer scene={sc} stepsOpen />))).toContain("Mặt phẳng qua A, B, C");
  });
});

describe("W2 · B · thứ tự lớp: ngăn và ô soi nằm trên bảng nổi", () => {
  it("nút Đóng của ngăn/ô soi không bị bảng nổi che", () => {
    const css = nguon("../../../styles/global.css");
    const z = (sel: string) => Number(/z-index:\s*(\d+)/.exec(css.slice(css.indexOf(sel), css.indexOf("}", css.indexOf(sel))))?.[1]);
    expect(z(".geo3d-ngan {")).toBeGreaterThan(z(".geo3d-bang-noi {"));
    expect(z(".geo3d-soi {")).toBeGreaterThan(z(".geo3d-bang-noi {"));
  });
});
