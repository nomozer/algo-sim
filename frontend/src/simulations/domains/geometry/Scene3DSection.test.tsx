import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { Scene3DSection, hopLeScene3D } from "./Scene3DSection";
import type { Scene3D } from "./scene3d-model";

/**
 * PHASE 5F — vùng "Quá trình dựng hình 3D" trong thẻ mô phỏng.
 *
 * Hai thứ file này khoá:
 *
 *   ① BIÊN NHẬN fail-closed. `envelope.scene3d` đến qua mạng, nên hình dạng
 *     phải kiểm TẠI CHỖ NHẬN. Lạ ⇒ không dựng vùng nào — bày một khung 3D
 *     rỗng là mời người học đi tìm thứ không có.
 *   ② Đường 2D cũ NGUYÊN VẸN. Bài Tin học không có `scene3d` ⇒ không thấy gì
 *     đổi, và điều đó phải kiểm được chứ không phải tin.
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

describe("(5F) biên nhận fail-closed", () => {
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
    expect(renderToString(<Scene3DSection scene={x} />)).toBe("");
  });
});

describe("(5F) vùng hiển thị", () => {
  it("có tiêu đề vùng và nói rõ hình từ đâu ra", () => {
    const html = renderToString(<Scene3DSection scene={scene()} />);
    expect(html).toContain("Quá trình dựng hình 3D");
    // Không có câu này, khung 3D đọc như một hình ai đó ngồi dựng sẵn — mất
    // đúng thứ phân biệt hệ này với một phần mềm vẽ hình.
    expect(html).toContain("kiểm chứng");
    expect(html).toContain("không sửa được");
  });

  it("dựng luôn trình phát bên trong", () => {
    const html = renderToString(<Scene3DSection scene={scene()} />);
    expect(html).toContain("Bước trước");
    expect(html).toContain("Đang dựng");
  });

  it("vùng có nhãn cho trình đọc màn hình", () => {
    const html = renderToString(<Scene3DSection scene={scene()} />);
    expect(html).toContain('aria-labelledby="geo3d-heading"');
  });
});

describe("(5F) không lấn sang đường 2D", () => {
  const shell = readFileSync(
    join(__dirname, "../../../components/SimulationWorkspace.tsx"), "utf8");

  it("shell chỉ thêm MỘT dòng dựng vùng, không sửa renderer nào", () => {
    expect(shell).toContain("<Scene3DSection scene=");
    // Không đụng công tắc 2D/3D: cảnh 3D là vùng THÊM VÀO, không phải một chế
    // độ tranh chỗ. Ai đó nhét nó vào `VisualModeToggle` là đổi ý nghĩa của
    // `visual_modes` cho cả 24 target Tin học.
    expect(shell).not.toMatch(/VisualModeToggle[^\n]*Scene3D/);
  });

  it("component tự trả null khi không có cảnh — shell không phải biết luật", () => {
    expect(renderToString(<Scene3DSection scene={undefined} />)).toBe("");
  });
});
