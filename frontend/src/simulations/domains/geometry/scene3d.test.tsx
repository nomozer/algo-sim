import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  LINE_DISPLAY_HALF_LENGTH,
  PLANE_DISPLAY_SIZE,
  RENDER_KINDS,
  clampStep,
  highlightedAt,
  narrationAt,
  objectsAt,
  stepCount,
  toNumber,
  toVec3,
  type Scene3D,
} from "./scene3d-model";
import { GEOMETRY_WEBGL_FALLBACK, Scene3DWorkspace, buildObject3D } from "./scene3d-view";

/**
 * PHASE 5D — renderer 3D đọc Scene3D.
 *
 * Thứ bộ test này khoá chặt nhất KHÔNG phải hình ảnh (không chấm bằng "nhìn
 * đẹp" — `COVERAGE.md` cấm) mà là bốn ranh giới:
 *
 *   ① renderer KHÔNG chứa phép toán hình học
 *   ② float chỉ xuất hiện ở `toNumber`, không sớm hơn
 *   ③ không primitive nào ngoài `RENDER_KINDS`
 *   ④ timeline giữ đúng thứ tự dựng, cùng state cho cùng kết quả
 */

/** Cảnh dựng tay theo đúng hình dạng `scene3d.build_scene3d` ở backend. */
function scene(): Scene3D {
  return {
    free_objects: ["A", "B", "C", "S"],
    objects: [
      { id: "A", label: "A", type: "point3", render: "point_marker",
        origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] },
      { id: "B", label: "B", type: "point3", render: "point_marker",
        origin: "free", producer: null, depends: [], xyz: ["1", "0", "0"] },
      { id: "C", label: "C", type: "point3", render: "point_marker",
        origin: "free", producer: null, depends: [], xyz: ["1", "1", "0"] },
      { id: "S", label: "S", type: "point3", render: "point_marker",
        origin: "free", producer: null, depends: [], xyz: ["0", "0", "2"] },
      { id: "M", label: "M", type: "point3", render: "point_marker",
        origin: "derived", producer: "construct_point.midpoint",
        depends: ["A", "B"], xyz: ["1/2", "0", "0"] },
      { id: "d", label: "AS", type: "line3", render: "line", origin: "derived",
        producer: "construct_line", depends: ["A", "S"],
        point: ["0", "0", "0"], direction: ["0", "0", "2"] },
      { id: "day", label: "(ABC)", type: "plane3", render: "surface",
        origin: "derived", producer: "construct_plane", depends: ["A", "B", "C"],
        point: ["0", "0", "0"], normal: ["0", "0", "1"] },
      { id: "chop", label: "S.ABC", type: "solid", render: "mesh",
        origin: "derived", producer: "construct_solid",
        depends: ["A", "B", "C", "S"],
        vertices: [["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "0", "2"]],
        faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [2, 0, 3]] },
      { id: "td", label: "thiết diện", type: "section", render: "polygon",
        origin: "derived", producer: "construct_section", depends: ["chop", "day"],
        polygon: [["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"]], closed: true },
      { id: "V", label: "Thể tích", type: "quantity", render: "readout",
        origin: "derived", producer: "measure.volume", depends: ["chop"],
        value: "1/3" },
    ],
    events: [
      { step_index: 0, action: "INIT", object: null, depends: [],
        explanation: "Khởi tạo dữ kiện đề cho." },
      { step_index: 1, action: "CREATE", object: "M", depends: ["A", "B"],
        explanation: "Dựng điểm M = (1/2, 0, 0)." },
      { step_index: 2, action: "CREATE", object: "d", depends: ["A", "S"],
        explanation: "Dựng đường thẳng AS." },
      { step_index: 3, action: "CREATE", object: "day", depends: ["A", "B", "C"],
        explanation: "Dựng mặt phẳng (ABC)." },
      { step_index: 4, action: "CREATE", object: "chop", depends: ["A", "B", "C", "S"],
        explanation: "Dựng khối S.ABC." },
      { step_index: 5, action: "EXTEND", object: "td", depends: ["chop", "day"],
        explanation: "Trên mặt thứ 1, nối hai giao điểm." },
      { step_index: 6, action: "MEASURE", object: "V", depends: ["chop"],
        explanation: "Thể tích khối = 1/3." },
    ],
  };
}

// ══ ② EXACT VALUE — float chỉ ở `toNumber` ══════════════════════════════
describe("(5D) toạ độ chính xác tới tận GPU", () => {
  it("phân số đọc đúng, không qua eval và không ra NaN", () => {
    expect(toNumber("0")).toBe(0);
    expect(toNumber("2")).toBe(2);
    expect(toNumber("1/2")).toBe(0.5);
    expect(toNumber("-3/4")).toBe(-0.75);
    expect(toVec3(["1/2", "0", "-2"])).toEqual([0.5, 0, -2]);
  });

  it("chuỗi hỏng NÉM thay vì trả NaN", () => {
    // Một NaN lọt vào buffer three.js làm cả mesh biến mất KHÔNG BÁO GÌ, và
    // truy ngược từ một khung hình trống về một chuỗi sai là chỗ tốn giờ nhất.
    for (const xau of ["", "abc", "1/0", "0.5", "1/2/3", "∞"]) {
      expect(() => toNumber(xau)).toThrow();
    }
  });

  it("model KHÔNG số hoá float ở đâu ngoài `toNumber`", () => {
    const src = readFileSync(join(__dirname, "scene3d-model.ts"), "utf8");
    const sau = src.slice(src.indexOf("export function toVec3"));
    // `parseFloat`/`Number(` ngoài `toNumber` là dấu hiệu ai đó hoá float sớm.
    expect(sau).not.toMatch(/parseFloat|\bNumber\s*\(/);
  });

  it("cảnh giữ nguyên chuỗi phân số, không đổi kiểu", () => {
    const o = scene().objects.find((x) => x.id === "M")!;
    expect(o.xyz).toEqual(["1/2", "0", "0"]);
    expect(typeof o.xyz![0]).toBe("string");
  });
});

// ══ ③ KHÔNG PRIMITIVE MỚI ═══════════════════════════════════════════════
describe("(5D) tập hình vẽ đóng", () => {
  it("đúng sáu loại, không hơn", () => {
    expect([...RENDER_KINDS]).toEqual([
      "point_marker", "line", "surface", "mesh", "polygon", "readout",
    ]);
  });

  it("KHÔNG có primitive ngoài hợp đồng ngữ nghĩa", () => {
    const src = readFileSync(join(__dirname, "scene3d-view.tsx"), "utf8");
    // Thêm ở tầng TRÌNH BÀY là để renderer vẽ được thứ mà không chương trình
    // nào tạo ra nổi — năng lực giả.
    for (const cam of ["CylinderGeometry", "TorusGeometry", "ConeGeometry",
                       "TubeGeometry", "LatheGeometry", "ExtrudeGeometry"]) {
      expect(src).not.toContain(cam);
    }
  });

  it("`readout` KHÔNG dựng hình trong không gian", () => {
    const o = scene().objects.find((x) => x.id === "V")!;
    // Một đại lượng đo được không có vị trí hình học. Vẽ bừa một nhãn lơ lửng
    // là đặt một con số vào chỗ không có nghĩa.
    expect(buildObject3D(o, false)).toBeNull();
  });
});

// ══ ① RENDERER KHÔNG TÍNH HÌNH HỌC ══════════════════════════════════════
describe("(5D) ranh giới: renderer không suy luận hình học", () => {
  const view = readFileSync(join(__dirname, "scene3d-view.tsx"), "utf8");
  const model = readFileSync(join(__dirname, "scene3d-model.ts"), "utf8");

  it("không tích có hướng, không giao điểm, không tích vô hướng", () => {
    for (const cam of [".cross(", ".dot(", "Plane(", "distanceTo", "angleTo",
                       "projectOnPlane"]) {
      expect(view, `view dùng ${cam}`).not.toContain(cam);
      expect(model, `model dùng ${cam}`).not.toContain(cam);
    }
  });

  /**
   * ─── NỚI CÓ CHỦ ĐÍCH, 2026-08-29: `Raycaster` RỜI KHỎI DANH SÁCH CẤM ────
   *
   * Bản đầu cấm luôn `Raycaster`/`intersect`/`Ray(` trong view. Danh sách ấy
   * gộp HAI thứ khác hẳn nhau dưới một cái tên:
   *
   *   ① SUY LUẬN HÌNH HỌC CỦA ĐỀ — tự tính giao tuyến, chân đường cao, góc.
   *      Vẫn CẤM TUYỆT ĐỐI, và đó là toàn bộ luận điểm của đề tài.
   *   ② PICKING — ánh xạ một điểm ảnh về TÊN của một vật đã có trên cảnh.
   *      Không có cách nào chọn vật trong 3D mà không làm việc này, và nó
   *      không kết luận gì về hình: đầu ra là một CHUỖI id.
   *
   * Nên thay vì cấm theo chữ, khoá theo ĐẦU RA: xem test kế tiếp.
   */
  it("raycast CHỈ được dùng để lấy ID, không để lấy toạ độ", () => {
    // Kết quả raycast phải đi thẳng vào `pickSemanticId`. Nếu ai đó đọc
    // `.point` (toạ độ va chạm) thì renderer đã bắt đầu sinh ra vị trí hình
    // học từ một cú bấm chuột — đúng thứ ranh giới này cấm.
    expect(view).toContain("pickSemanticId(");
    expect(view).not.toContain(".point;");
    expect(view).not.toMatch(/intersect\w*\([^)]*\)\s*\[0\]\.point/);
    // Và `Raycaster` chỉ được xuất hiện trong view, KHÔNG trong model thuần.
    expect(model).not.toContain("Raycaster");
    expect(model).not.toContain("intersect");
  });

  it("không import kernel/validator/oracle — chỉ nguồn THUẦN của miền", () => {
    const imports = [...view.matchAll(/from ["']([^"']+)["']/g)].map((m) => m[1]);
    for (const i of imports) {
      expect(["react", "three", "three/addons/controls/OrbitControls.js",
              "./scene3d-model", "./interaction-state"]).toContain(i);
    }
  });

  it("`interaction-state` là mô hình THUẦN — không three, không kernel", () => {
    // Nó được thêm vào danh sách nhập hợp lệ ở test trên, nên phải tự chứng
    // minh mình cùng hạng với `scene3d-model`: không chạm WebGL, không chạm
    // toán hình học nào.
    const tt = readFileSync(join(__dirname, "interaction-state.ts"), "utf8");
    const imports = [...tt.matchAll(/from ["']([^"']+)["']/g)].map((m) => m[1]);
    expect(imports).toEqual(["./scene3d-model"]);
    for (const cam of [".cross(", ".dot(", "Raycaster", "intersect",
                       "distanceTo", "angleTo"]) {
      expect(tt, `interaction-state dùng ${cam}`).not.toContain(cam);
    }
  });

  it("model KHÔNG import three — tách để test được mà không cần WebGL", () => {
    // Kiểm IMPORT, không kiểm chuỗi thô: chữ `three` có mặt trong văn xuôi
    // docstring (`… → three.js`), nên `toContain` bắt oan chính lời giải thích
    // vì sao ranh giới tồn tại.
    const imports = [...model.matchAll(/from ["']([^"']+)["']/g)].map((m) => m[1]);
    expect(imports).toEqual([]);
  });

  it("kích thước mặt phẳng/đường là hằng TRÌNH BÀY, không phải toán học", () => {
    // `plane3`/`line3` VÔ HẠN; backend cố ý không gửi biên. Đổi hai hằng này
    // không đổi một mệnh đề toán học nào — đó là bằng chứng chúng đúng chỗ.
    expect(PLANE_DISPLAY_SIZE).toBeGreaterThan(0);
    expect(LINE_DISPLAY_HALF_LENGTH).toBeGreaterThan(0);
    expect(model).not.toMatch(/boundary|corners|extent/);
  });
});

// ══ ④ TIMELINE — thứ tự dựng và tính ổn định ════════════════════════════
describe("(5D) mô phỏng QUÁ TRÌNH hình thành", () => {
  const s = scene();

  it("bước 0 chỉ có dữ kiện đề cho, chưa có gì dựng ra", () => {
    // Chiếu thẳng trạng thái CUỐI ra màn hình thì học sinh thấy ngay hình hoàn
    // chỉnh, và toàn bộ mục tiêu sư phạm biến mất.
    expect(objectsAt(s, 0).map((o) => o.id)).toEqual(["A", "B", "C", "S"]);
  });

  it("mỗi bước thêm đúng đối tượng của bước đó", () => {
    expect(objectsAt(s, 1).map((o) => o.id)).toContain("M");
    expect(objectsAt(s, 1).map((o) => o.id)).not.toContain("d");
    expect(objectsAt(s, 3).map((o) => o.id)).toContain("day");
    expect(objectsAt(s, 3).map((o) => o.id)).not.toContain("chop");
  });

  it("bước cuối có đủ mọi đối tượng", () => {
    expect(objectsAt(s, stepCount(s) - 1)).toHaveLength(s.objects.length);
  });

  it("thứ tự dựng KHÔNG bị đảo", () => {
    const xuatHien = (id: string) =>
      s.events.findIndex((e) => e.object === id);
    expect(xuatHien("M")).toBeLessThan(xuatHien("day"));
    expect(xuatHien("day")).toBeLessThan(xuatHien("chop"));
    expect(xuatHien("chop")).toBeLessThan(xuatHien("td"));
  });

  it("làm nổi bật đối tượng vừa dựng VÀ thứ nó phụ thuộc", () => {
    expect(highlightedAt(s, 1).sort()).toEqual(["A", "B", "M"]);
    expect(highlightedAt(s, 0)).toEqual([]);
  });

  it("lời kể theo đúng bước, do engine sinh", () => {
    expect(narrationAt(s, 1)).toContain("M");
    expect(narrationAt(s, 6)).toContain("1/3");
  });

  it("bước ngoài biên bị kẹp, không vỡ", () => {
    expect(clampStep(s, -5)).toBe(0);
    expect(clampStep(s, 999)).toBe(stepCount(s) - 1);
    expect(objectsAt(s, 999)).toHaveLength(s.objects.length);
  });

  it("cảnh RỖNG không làm vỡ gì", () => {
    const rong: Scene3D = { objects: [], events: [], free_objects: [] };
    expect(stepCount(rong)).toBe(0);
    expect(objectsAt(rong, 0)).toEqual([]);
    expect(narrationAt(rong, 0)).toBe("");
  });

  it("CÙNG state cho CÙNG kết quả — không phụ thuộc thứ tự gọi", () => {
    const a = objectsAt(scene(), 4).map((o) => o.id);
    const b = objectsAt(scene(), 4).map((o) => o.id);
    expect(a).toEqual(b);
    // Gọi xen kẽ các bước khác không được làm lệch kết quả.
    objectsAt(s, 0); objectsAt(s, 6);
    expect(objectsAt(s, 4).map((o) => o.id)).toEqual(a);
  });
});

// ══ VỎ HIỂN THỊ ═════════════════════════════════════════════════════════
describe("(5D) vỏ renderer", () => {
  it("SSR ra được vỏ + lời kể + số bước, không cần WebGL", () => {
    const html = renderToString(<Scene3DWorkspace scene={scene()} step={1} />);
    expect(html).toContain("Dựng điểm M");
    expect(html).toContain("Bước 2/7");
  });

  it("đại lượng hiện ở bảng chữ, không nằm trong khung 3D", () => {
    const html = renderToString(<Scene3DWorkspace scene={scene()} step={6} />);
    expect(html).toContain("Thể tích");
    expect(html).toContain("1/3");
  });

  it("có lối thoát khi WebGL không khả dụng", () => {
    expect(GEOMETRY_WEBGL_FALLBACK).toContain("WebGL");
  });

  it("KHÔNG có toolbar / ô nhập lệnh / nút tạo hình", () => {
    const src = readFileSync(join(__dirname, "scene3d-view.tsx"), "utf8");
    // Hình ở đây KHÔNG dựng được bằng chuột — nó chỉ đến từ một chương trình
    // đã qua thẩm định. Người học điều khiển THỜI GIAN và GÓC NHÌN.
    for (const cam of ["<button", "<input", "<select", "onPointerDown",
                       "onClick={", "DragControls", "TransformControls"]) {
      expect(src).not.toContain(cam);
    }
  });
});
