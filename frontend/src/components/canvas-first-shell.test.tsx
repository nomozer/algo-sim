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

  it("gắn cờ `is-canvas-first` lên gốc ứng dụng", () => {
    expect(APP).toMatch(/is-canvas-first/);
  });

  it("CSS thu cột thường trực về 0 ở chế độ canvas-first", () => {
    const luat = CSS.match(
      /\.app-root\.is-canvas-first \.app-nav-shell[^{]*\{[^}]*\}/,
    );
    expect(luat, "thiếu luật CSS tắt cột thường trực").toBeTruthy();
    expect(luat![0]).toMatch(/width:\s*0/);
    expect(luat![0]).toMatch(/flex-basis:\s*0/);
  });

  it("NGĂN KÉO vẫn thắng — không thì học sinh vào xưởng là kẹt lại", () => {
    // Luật tắt cột phải loại trừ trạng thái ngăn kéo đang mở.
    expect(CSS).toMatch(
      /\.app-root\.is-canvas-first \.app-nav-shell:not\(\.is-drawer-open\)/,
    );
    // …và component điều hướng vẫn được MOUNT (không bị rẽ nhánh bỏ đi).
    expect(APP).toMatch(/\{user && <AppSidebar \/>\}/);
  });

  it("xưởng có ĐƯỜNG RA: chip mở điều hướng", () => {
    const xuong = SRC("../simulations/domains/geometry/Scene3DExplorer.tsx");
    expect(xuong).toMatch(/onMoMenu/);
    expect(xuong).toContain("Mở điều hướng");
    const ws = SRC("./SimulationWorkspace.tsx");
    expect(ws).toMatch(/onMoMenu=\{openNav\}/);
    expect(ws).toMatch(/openSidebarDrawer/);
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
