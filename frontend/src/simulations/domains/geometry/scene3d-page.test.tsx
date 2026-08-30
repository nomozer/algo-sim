import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { Scene3DExplorer } from "./Scene3DExplorer";
import { hopLeScene3D, type Scene3D } from "./scene3d-model";

/**
 * XƯỞNG 3D LÀ TRANG — kế thừa `Scene3DSection.test.tsx` (Phase 5F), viết lại
 * cho kiến trúc đã ĐẢO NGƯỢC ngày 2026-08-30.
 *
 * ─── CÁI GÌ ĐỔI, VÀ VÌ SAO TEST CŨ PHẢI ĐI THEO ─────────────────────────
 *
 * Bản 5F khoá đúng một câu: *"cảnh 3D là VÙNG THÊM VÀO thẻ mô phỏng, shell chỉ
 * thêm một dòng `<Scene3DSection/>`"*. Câu ấy đúng khi hình học là phần phụ của
 * một sản phẩm Tin học. Nay hình học LÀ sản phẩm, và hệ quả đo được của kiến
 * trúc cũ là: học sinh mở một bài thiết diện thì thấy — theo đúng thứ tự đọc —
 * tiêu đề, nhãn miền, renderer 2D của route ngữ nghĩa, khay điều khiển, panel
 * Giải thích, rồi mới tới cái hình. Thứ cả bài nói về nằm dưới nếp gấp.
 *
 * Nên test này khoá **bất biến còn đúng**, không khoá hình dạng đã đổi:
 *
 *   ① BIÊN NHẬN fail-closed — không đổi một chữ so với 5F.
 *   ② Đường 2D cũ NGUYÊN VẸN — bài không có `scene3d` không thấy gì khác.
 *   ③ Rẽ nhánh theo cảnh ĐÃ DỰNG, không theo `visual_mode` được KHAI.
 *   ④ Canvas đứng trước mọi bảng chữ trong thứ tự đọc.
 */

function scene(): Scene3D {
  return {
    free_objects: ["A", "B"],
    objects: [
      { id: "A", label: "A", type: "point3", render: "point_marker",
        origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] },
      { id: "M", label: "M", type: "point3", render: "point_marker",
        origin: "derived", producer: "construct_point.midpoint",
        depends: ["A", "B"], xyz: ["1/2", "0", "0"] },
    ],
    events: [
      { step_index: 0, action: "INIT", object: null, depends: [],
        explanation: "Khởi tạo dữ kiện đề cho." },
      { step_index: 1, action: "CREATE", object: "M", depends: ["A", "B"],
        explanation: "Dựng điểm M là trung điểm AB." },
    ],
  };
}

// ══ ① BIÊN NHẬN ═════════════════════════════════════════════════════════
describe("biên nhận fail-closed", () => {
  it("cảnh hợp lệ ⇒ nhận", () => {
    expect(hopLeScene3D(scene())).toBe(true);
  });

  it.each([
    ["undefined", undefined],
    ["null", null],
    ["chuỗi", "scene"],
    ["số", 42],
    ["object rỗng", {}],
    ["thiếu events", { objects: [1], free_objects: [] }],
    ["objects rỗng", { objects: [], events: [{}], free_objects: [] }],
    ["events rỗng", { objects: [{}], events: [], free_objects: [] }],
    ["free_objects không phải mảng", { objects: [{}], events: [{}], free_objects: 0 }],
  ])("hình dạng lạ (%s) ⇒ TỪ CHỐI", (_ten, x) => {
    expect(hopLeScene3D(x)).toBe(false);
  });
});

// ══ ④ XƯỞNG ════════════════════════════════════════════════════════════
describe("xưởng — hợp đồng, không phải bài đọc", () => {
  it("tự có nhãn, KHÔNG mở đầu bằng một khối văn bản", () => {
    const html = renderToString(<Scene3DExplorer scene={scene()} />);
    expect(html).not.toContain("<h3");
    expect(html).not.toContain("kiểm chứng");
  });

  it("dựng luôn trình phát bên trong", () => {
    expect(renderToString(<Scene3DExplorer scene={scene()} />))
      .toContain("Bước trước");
  });

  it("canvas đứng TRƯỚC mọi bảng chữ trong thứ tự đọc", () => {
    const html = renderToString(<Scene3DExplorer scene={scene()} />);
    const iCanvas = html.indexOf("geo3d-canvas");
    const iThanhPhan = html.indexOf("Thành phần");
    expect(iCanvas).toBeGreaterThan(-1);
    expect(html).not.toContain("geo3d-ngan");
    expect(iThanhPhan).toBeGreaterThan(-1);
  });

  it("đề bài KHÔNG đổ ra màn hình, chỉ có nút gọi", () => {
    const de = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a.";
    const html = renderToString(<Scene3DExplorer scene={scene()} de={de} />);
    expect(html).toContain("Xem đề");
    expect(html).not.toContain(de);
  });
});

// ══ ②③ SHELL ═══════════════════════════════════════════════════════════
describe("shell — xưởng 3D chiếm trang, đường 2D nguyên vẹn", () => {
  const nguyen = readFileSync(
    join(__dirname, "../../../components/SimulationWorkspace.tsx"), "utf8");
  /* SOI MÃ, KHÔNG SOI LỜI. Bản đầu quét thẳng file và ĐỎ ngay — vì chính
     CHÚ THÍCH giải thích *"vì sao KHÔNG dùng `visual_mode === '3d'`"* khớp
     mẫu cấm. Guard khoá chính tả thay vì khoá ý định là guard sẽ nói dối theo
     cả hai chiều: đỏ oan như ở đây, và xanh oan khi ai đó viết luật cấm trong
     một chuỗi. Bóc chú thích trước là cách rẻ nhất để nó hỏi đúng câu. */
  const shell = nguyen
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");

  it("bóc chú thích KHÔNG làm rỗng phép đo", () => {
    // Rỗng-là-hỏng: regex bóc sai thì mọi khẳng định `not.toMatch` dưới đây
    // xanh vì không còn gì để khớp.
    expect(shell).toContain("export function SimulationWorkspace");
    expect(shell.length).toBeGreaterThan(2000);
  });

  it("rẽ nhánh theo CẢNH ĐÃ DỰNG, không theo `visual_mode` được KHAI", () => {
    // `visual_mode` là thứ backend KHAI — khai được thì khai sai được. Một
    // cảnh đã dựng thì hoặc có hoặc không, và `hopLeScene3D` là chỗ hỏi.
    expect(shell).toMatch(/hopLeScene3D\(canh3d\)/);
    expect(shell).not.toMatch(/visual_mode\s*===\s*["']3d["']/);
  });

  it("KHÔNG còn dựng cảnh 3D như một vùng phụ dưới thẻ", () => {
    // Hồi quy của chính kiến trúc vừa bỏ: gắn lại `<Scene3DSection/>` vào thẻ
    // là đưa cái hình trở xuống dưới nếp gấp.
    expect(shell).not.toMatch(/<Scene3DSection\b/);
  });

  it("nhánh 3D trả về TRƯỚC khi dựng thẻ mô phỏng 2D", () => {
    const iNhanh = shell.indexOf("hopLeScene3D(canh3d)");
    const iThe = shell.indexOf('className="card card-elevated workspace-card"');
    expect(iNhanh).toBeGreaterThan(-1);
    expect(iThe).toBeGreaterThan(-1);
    expect(iNhanh).toBeLessThan(iThe);
  });

  it("KHÔNG đụng công tắc 2D/3D", () => {
    // Cảnh 3D không tranh chỗ với `VisualModeToggle`: nhét nó vào đó là đổi ý
    // nghĩa của `visual_modes` cho mọi target còn lại.
    expect(shell).not.toMatch(/VisualModeToggle[^\n]*Scene3D/);
  });
});
