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

const CANH: Scene3D = JSON.parse(readFileSync(fileURLToPath(new URL(
  "../../../../../docs/evaluation/geometry/runs/w11-pedagogical-polish/inputs/fixtures/rectangular_pyramid_positive.json",
  import.meta.url)), "utf8")).envelope.scene3d;
const CUOI = anchorOfGeometryStep(CANH, geometryStepCount(CANH) - 1);
const sach = (h: string) => h.replace(/<!--.*?-->/g, "");
// Checkout Windows (CRLF) phải cho cùng kết quả: so mẫu nhiều dòng trên "\n".
const nguon = (f: string) => readFileSync(new URL(f, import.meta.url), "utf8").replace(/\r\n/g, "\n");

describe("§0.1-1 · không có card Kết quả dưới hình", () => {
  it("trình phát không dựng thẻ lời giải nào — đáp số đọc ở «Đại lượng» và ô soi", () => {
    // §0.1-1 ẩn card Kết quả khi lời giải thu gọn; W05 gỡ hẳn thẻ lời giải (nó lặp tập đại lượng của «Đại lượng»).
    const h = sach(renderToString(<Scene3DPlayer scene={CANH} initialStep={CUOI} />));
    expect(h).not.toContain("geo3d-lg-ket-qua");
    expect(h).not.toContain("geo3d-loi-giai");
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

  it("xưởng có nút «Đại lượng»; chọn một đại lượng mở ô soi của nó (một nơi chi tiết) và GIỮ bảng mở (W4)", () => {
    const src = nguon("./Scene3DExplorer.tsx");
    expect(src).toContain("Đại lượng");
    expect(src).toMatch(/moBang\.has\("dai-luong"\)/);
    // W1 đóng ngăn khi chọn vì ngăn và ô soi tranh nhau mép phải; W4 hai thứ là hai bảng nổi riêng ⇒ giữ bảng mở.
    expect(src).toMatch(/onClick=\{\(\) => chon\(id\)\}/);
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

describe("bảng nổi «Các bước dựng»", () => {
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
describe("mặt phẳng phụ chỉ để đo không mở bước dựng", () => {
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

/* W2 · B xếp ngăn và ô soi CỐ ĐỊNH trên bảng nổi (z 4 > 3) để nút Đóng của chúng không bị che. W4: mọi bảng là
   `BangNoi` ⇒ thứ tự lớp do host đặt theo lần dùng gần nhất (`lenTren`): bảng vừa mở / vừa chạm luôn trên cùng, nên
   nút Đóng của bảng người học đang dùng không bao giờ nằm dưới bảng khác. */
describe("thứ tự lớp: bảng vừa dùng nằm trên cùng", () => {
  it("lớp đặt theo host (mở, chạm, nhận tiêu điểm ⇒ lên trên), không còn z cố định riêng của ngăn/ô soi", () => {
    const css = nguon("../../../styles/global.css");
    const bp = nguon("./scene3d-floating-panel.tsx");
    for (const sel of [".geo3d-bang-noi.geo3d-ngan {", ".geo3d-bang-noi.geo3d-soi {"]) {
      const i = css.indexOf(sel);
      expect(i, sel).toBeGreaterThan(-1);
      expect(css.slice(i, css.indexOf("}", i))).not.toMatch(/z-index/);
    }
    expect(bp).toMatch(/onPointerDownCapture=\{\(\) => host\?\.len\(panel\)\}/);
    expect(bp).toMatch(/onFocusCapture=\{\(\) => host\?\.len\(panel\)\}/);
    expect(bp).toMatch(/zIndex: lop/);
  });
});

describe("lời kể của bước đang xem không lặp tiêu đề", () => {
  it("bước dữ kiện (tiêu đề CHÍNH LÀ lời kể) không in lời kể lần hai; bước dựng có lời kể khác tiêu đề thì giữ", () => {
    const dau = sach(renderToString(<Scene3DPlayer scene={CANH} initialStep={0} stepsOpen />));
    expect(dau).not.toContain("geo3d-cac-buoc-mo-ta");
    const ds = geometryStepList(CANH);
    const buoc = ds.find((b) => b.index > 0)!;
    const sau = sach(renderToString(<Scene3DPlayer scene={CANH} initialStep={buoc.anchor} stepsOpen />));
    expect(sau).toContain("geo3d-cac-buoc-mo-ta");
  });
});
