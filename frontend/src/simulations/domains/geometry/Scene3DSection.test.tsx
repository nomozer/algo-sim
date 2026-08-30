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

describe("(5F) vùng hiển thị — HỢP ĐỒNG XƯỞNG, không phải bài đọc", () => {
  // ─── VÌ SAO BA KHẲNG ĐỊNH CŨ ĐỔI ─────────────────────────────────────
  //
  // Bản trước đòi một `<h3>` "Quá trình dựng hình 3D" cộng một đoạn dẫn ba
  // dòng NGAY ĐẦU vùng. Cả hai đều đúng về nội dung, và cả hai đẩy khung 3D
  // xuống dưới nếp gấp trên laptop. Wave này đổi vùng từ *một mục có hình*
  // thành *một xưởng*: câu "hình từ đâu ra" chuyển vào nút «Chi tiết», và
  // vùng nhận nhãn bằng `aria-label` thay vì trỏ tới một tiêu đề không còn.
  //
  // Điều KHÔNG đổi, và test vẫn giữ: vùng phải tự giới thiệu cho trình đọc
  // màn hình, và trình phát phải nằm ngay trong đó.
  it("vùng tự có nhãn, KHÔNG mở đầu bằng một khối văn bản", () => {
    const html = renderToString(<Scene3DSection scene={scene()} />);
    expect(html).toContain('aria-label="Xưởng hình 3D"');
    expect(html).not.toContain("<h3");
    // Không còn đoạn dẫn giải thích kiến trúc ở đầu vùng.
    expect(html).not.toContain("kiểm chứng");
  });

  it("dựng luôn trình phát bên trong", () => {
    const html = renderToString(<Scene3DSection scene={scene()} />);
    expect(html).toContain("Bước trước");
  });

  it("canvas đứng TRƯỚC mọi bảng chữ trong thứ tự đọc", () => {
    const html = renderToString(<Scene3DSection scene={scene()} />);
    const iCanvas = html.indexOf("geo3d-canvas");
    const iThanhPhan = html.indexOf("Thành phần");
    expect(iCanvas).toBeGreaterThan(-1);
    // Nút gọi bảng đứng ở thanh trên, còn BẢNG thì chưa dựng — nên thứ duy
    // nhất giữa canvas và người đọc là một hàng chip.
    expect(html).not.toContain("geo3d-ngan");
    expect(iThanhPhan).toBeGreaterThan(-1);
  });

  it("đề bài KHÔNG đổ ra màn hình, chỉ có nút gọi", () => {
    const de = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a.";
    const html = renderToString(<Scene3DSection scene={scene()} de={de} />);
    expect(html).toContain("Xem đề");
    expect(html).not.toContain(de);
  });
});

describe("(5F) không lấn sang đường 2D", () => {
  const shell = readFileSync(
    join(__dirname, "../../../components/SimulationWorkspace.tsx"), "utf8");

  it("shell chỉ thêm MỘT dòng dựng vùng, không sửa renderer nào", () => {
    // Khớp theo TÊN THẺ, không theo nguyên văn một dòng: JSX nay xuống dòng
    // vì có thêm prop `de`, và một phép so nguyên văn sẽ đỏ vì cách xuống
    // dòng chứ không vì thứ nó bảo vệ.
    expect(shell).toMatch(/<Scene3DSection\b/);
    expect((shell.match(/<Scene3DSection\b/g) ?? []).length).toBe(1);
    // Không đụng công tắc 2D/3D: cảnh 3D là vùng THÊM VÀO, không phải một chế
    // độ tranh chỗ. Ai đó nhét nó vào `VisualModeToggle` là đổi ý nghĩa của
    // `visual_modes` cho cả 24 target Tin học.
    expect(shell).not.toMatch(/VisualModeToggle[^\n]*Scene3D/);
  });

  it("component tự trả null khi không có cảnh — shell không phải biết luật", () => {
    expect(renderToString(<Scene3DSection scene={undefined} />)).toBe("");
  });
});
