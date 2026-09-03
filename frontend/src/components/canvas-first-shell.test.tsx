import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { hopLeScene3D } from "../simulations/domains/geometry/scene3d-model";
import geometrySamples from "../data/geometry-samples.json";

/**
 * VỎ CANVAS-FIRST — xưởng 3D KHÔNG có cột điều hướng thường trực.
 *
 * ─── VÌ SAO SOI MÃ NGUỒN, KHÔNG RENDER ──────────────────────────────────
 *
 * `App` đọc zustand, mà zustand v5 dùng `useSyncExternalStore` nên SSR luôn
 * trả TRẠNG THÁI ĐẦU (`ARCHITECTURE_MAP §8` #8): `renderToString(<App/>)` sau
 * khi nạp envelope vẫn ra màn hình chưa-đăng-nhập, và mọi khẳng định kiểu
 * "không chứa cột trái" sẽ XANH vì màn hình rỗng — xanh vì lý do sai.
 *
 * Nên luật được khoá ở hai chỗ KIỂM ĐƯỢC THẬT: điều kiện rẽ nhánh trong mã vỏ,
 * và luật CSS thực thi nó. Cộng một phép kiểm HÀNH VI trên `hopLeScene3D` với
 * dữ liệu THẬT (bài mẫu sinh từ kernel).
 */

const SRC = (p: string) =>
  readFileSync(join(__dirname, p), "utf-8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");

const APP = SRC("../App.tsx");
const CSS = readFileSync(join(__dirname, "../styles/global.css"), "utf-8");

describe("D — xưởng 3D không phụ thuộc cột điều hướng thường trực", () => {
  it("bóc chú thích KHÔNG làm rỗng phép đo", () => {
    expect(APP).toContain("export default function App");
    expect(APP.length).toBeGreaterThan(1500);
  });

  it("vỏ rẽ nhánh theo CẢNH ĐÃ DỰNG, không theo `visual_mode` được khai", () => {
    expect(APP).toMatch(/hopLeScene3D\(/);
    expect(APP).not.toMatch(/visual_mode\s*===\s*["']3d["']/);
  });

  /* `is-canvas-first` trên gốc ứng dụng đã gỡ cùng cột trái: cờ ấy chỉ có một
     người dùng là luật thu cột. Cái CÒN LẠI — và là thứ đáng khoá — là cờ bố
     cục nới lưới nội dung cho cảnh 3D. */
  it("gắn cờ bố cục `la-canh-3d` lên lưới nội dung", () => {
    expect(APP).toMatch(/canvasFirst \? " la-canh-3d" : ""/);
    expect(APP).not.toMatch(/is-canvas-first/);
  });

  /* ── VÌ SAO BA CA CŨ BIẾN MẤT ─────────────────────────────────────────
   *
   * Chúng khoá CƠ CHẾ chứ không khoá bất biến: *"CSS thu cột về 0"*, *"ngăn
   * kéo thắng luật thu cột"*, *"xưởng dựng chip «Menu» để mở lại cột"*. Cả ba
   * nói về một cột điều hướng trái nay đã gỡ hẳn (`AppSidebar` + khối
   * `.app-nav*`), nên giữ lại là đòi mã dựng lại thứ vừa bỏ.
   *
   * Bất biến THẬT mà chúng phục vụ chỉ có hai, và hai ca dưới đây giữ nguyên:
   *   1. xưởng 3D không bị một cột thường trực ăn mất bề rộng;
   *   2. học sinh vào xưởng vẫn có đường ra.
   *
   * Vỏ mới thoả cả hai bằng cách BỎ điều kiện thay vì thêm luật: điều hướng là
   * một hàng ngang luôn hiện trong thanh trên, nên không còn cột nào để thu, và
   * đường ra có mặt ở mọi trang mà không cần ai nhớ bật. */

  it("KHÔNG còn cột điều hướng thường trực — bất biến 1", () => {
    // Chiều VẮNG MẶT: cột cũ và mọi luật quản nó phải đi hẳn, không nằm lại
    // dưới dạng CSS chết rồi một wave sau có người gắn lại vào JSX.
    expect(APP).not.toMatch(/AppSidebar/);
    expect(CSS).not.toMatch(/^\.app-nav-shell\s*\{/m);
    expect(CSS).not.toMatch(/\.nav-drawer-btn\s*\{/);
    // …và trạng thái của nó cũng không còn sống trong store.
    const store = SRC("../state/store.ts");
    expect(store).not.toMatch(/sidebarCollapsed|sidebarDrawerOpen/);
  });

  it("xưởng có ĐƯỜNG RA: hàng điều hướng luôn hiện — bất biến 2", () => {
    /* Đường ra nay là chính thanh trên, nên nó phải dựng KHÔNG điều kiện theo
       trang: `App` chỉ được rẽ nhánh theo ĐÃ ĐĂNG NHẬP CHƯA, không theo
       `inWorkspace` — rẽ theo trang là đúng cách chip «Menu» cũ sinh ra. */
    expect(APP).toMatch(/\{user\s*\n?\s*\?\s*<TopNav \/>/);
    expect(APP).not.toMatch(/inWorkspace[^\n]*<TopNav/);

    const nav = SRC("./TopNav.tsx");
    expect(nav).toMatch(/itemsForRole/);
    // Mục điều hướng phải bấm được thật, không phải nhãn trang trí.
    expect(nav).toMatch(/onClick=\{\(\) => setView\(it\.view\)\}/);

    // Xưởng thôi tự dựng đường ra riêng — không còn chip nào để lệch trạng thái.
    const xuong = SRC("../simulations/domains/geometry/Scene3DExplorer.tsx");
    expect(xuong).not.toMatch(/onMoMenu/);
    expect(xuong).not.toContain("Mở điều hướng");

    // Và khách vẫn phải có lối về: dấu hiệu sản phẩm ở thanh trên đưa về nhà.
    expect(APP).toMatch(/nav-wordmark/);
  });
});

describe("D2 — điều kiện canvas-first đúng trên dữ liệu THẬT", () => {
  const mau = (geometrySamples as { samples: { envelope: { scene3d?: unknown } }[] }).samples;

  it("mọi bài mẫu hình học đều kích hoạt canvas-first", () => {
    expect(mau.length).toBeGreaterThan(0);
    for (const s of mau) expect(hopLeScene3D(s.envelope.scene3d)).toBe(true);
  });

  it("bài KHÔNG có cảnh 3D thì KHÔNG kích hoạt — đường 2D nguyên vẹn", () => {
    expect(hopLeScene3D(undefined)).toBe(false);
    expect(hopLeScene3D({ config: { inputA: 0 } })).toBe(false);
  });
});
