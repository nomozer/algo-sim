import { afterEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  PLAYBACK_INTERVAL_MS,
  focusAt,
  isFirstStep,
  isLastStep,
  nextStep,
  prefersReducedMotion,
  prevStep,
  type Scene3D,
} from "./scene3d-model";
import { Scene3DPlayer } from "./scene3d-playback";

/**
 * PHASE 5E — phát lại quá trình dựng.
 *
 * Ranh giới trung tâm, và nó kiểm được: **playback chỉ phát ra một số nguyên**.
 * Người học điều khiển THỜI GIAN và GÓC NHÌN; nội dung toán học thì không.
 */

function scene(): Scene3D {
  return {
    free_objects: ["A", "B"],
    objects: [
      { id: "A", label: "A", type: "point3", render: "point_marker",
        origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] },
      { id: "B", label: "B", type: "point3", render: "point_marker",
        origin: "free", producer: null, depends: [], xyz: ["1", "0", "0"] },
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

afterEach(() => {
  vi.unstubAllGlobals();
});

// ══ ĐIỀU HƯỚNG BƯỚC — hàm thuần ═════════════════════════════════════════
describe("(5E) điều hướng bước", () => {
  const s = scene();

  it("tiến/lùi và kẹp ở hai đầu", () => {
    expect(nextStep(s, 0)).toBe(1);
    expect(nextStep(s, 1)).toBe(1);
    expect(prevStep(s, 1)).toBe(0);
    expect(prevStep(s, 0)).toBe(0);
  });

  it("biết đâu là đầu, đâu là cuối", () => {
    expect(isFirstStep(s, 0)).toBe(true);
    expect(isLastStep(s, 1)).toBe(true);
    expect(isLastStep(s, 0)).toBe(false);
  });

  it("cảnh RỖNG không làm vỡ điều hướng", () => {
    const rong: Scene3D = { objects: [], events: [], free_objects: [] };
    expect(nextStep(rong, 0)).toBe(0);
    expect(isLastStep(rong, 0)).toBe(true);
  });

  it("nêu đúng đối tượng đang dựng và thứ nó dựa trên", () => {
    expect(focusAt(s, 1)).toEqual({ created: "M", depends: ["A", "B"] });
    expect(focusAt(s, 0)).toEqual({ created: null, depends: [] });
  });
});

// ══ GIẢM CHUYỂN ĐỘNG — lỗ mà CSS không phủ được ═════════════════════════
describe("(5E) tôn trọng giảm chuyển động ở tầng JS", () => {
  it("SSR (không có window) ⇒ false, không tự suy diễn", () => {
    // Không suy diễn sở thích của một người chưa có mặt.
    expect(prefersReducedMotion()).toBe(false);
  });

  it("matchMedia báo reduce ⇒ true", () => {
    vi.stubGlobal("window", {
      matchMedia: (q: string) => ({ matches: q.includes("reduce") }),
    });
    expect(prefersReducedMotion()).toBe(true);
  });

  it("matchMedia ném lỗi ⇒ false, KHÔNG làm vỡ giao diện", () => {
    vi.stubGlobal("window", {
      matchMedia: () => { throw new Error("không hỗ trợ"); },
    });
    expect(prefersReducedMotion()).toBe(false);
  });

  it("bật giảm chuyển động ⇒ KHÔNG có nút Phát, vẫn đi được từng bước", () => {
    // Tự động chạy các bước là hoạt cảnh do JS phát; khối
    // `@media (prefers-reduced-motion)` trong CSS không chạm tới được. Bỏ qua
    // chỗ này thì người đã tắt chuyển động vẫn nhận đúng thứ họ tắt.
    vi.stubGlobal("window", {
      matchMedia: (q: string) => ({ matches: q.includes("reduce") }),
    });
    const html = renderToString(<Scene3DPlayer scene={scene()} />);
    expect(html).not.toContain("aria-label=\"Phát lại quá trình dựng\"");
    expect(html).toContain("Bước trước");
    expect(html).toContain("Bước sau");
  });
});

// ══ VỎ ĐIỀU KHIỂN ═══════════════════════════════════════════════════════
describe("(5E) vỏ điều khiển", () => {
  it("có đủ prev · play · next · chọn bước", () => {
    const html = renderToString(<Scene3DPlayer scene={scene()} />);
    expect(html).toContain("Bước trước");
    expect(html).toContain("aria-label=\"Phát lại quá trình dựng\"");
    expect(html).toContain("Bước sau");
    expect(html).toContain('type="range"');
  });

  it("bước đầu ⇒ nút lùi bị vô hiệu", () => {
    const html = renderToString(<Scene3DPlayer scene={scene()} />);
    expect(html).toMatch(/Bước trước[\s\S]{0,80}/);
    expect(html).toContain("disabled");
  });

  it("nêu đối tượng đang dựng và phụ thuộc của nó", () => {
    const html = renderToString(<Scene3DPlayer scene={scene()} initialStep={1} />);
    expect(html).toContain("Đang dựng");
    expect(html).toContain("Dựa trên");
    expect(html).toContain("A, B");
  });

  it("bước 0 nói rõ đây là dữ kiện đề cho, không phải chỗ trống", () => {
    const html = renderToString(<Scene3DPlayer scene={scene()} />);
    expect(html).toContain("dữ kiện đề cho");
  });

  it("mọi điều khiển đều có nhãn cho trình đọc màn hình", () => {
    const html = renderToString(<Scene3DPlayer scene={scene()} />);
    for (const nhan of ["Bước trước", "Bước sau", "Chọn bước dựng",
                        "Điều khiển bước dựng"]) {
      expect(html).toContain(`aria-label="${nhan}`);
    }
    expect(html).toContain('role="group"');
  });

  it("nhịp phát đủ chậm để đọc lời kể", () => {
    expect(PLAYBACK_INTERVAL_MS).toBeGreaterThanOrEqual(1000);
  });
});

// ══ RANH GIỚI — KHÔNG PHẢI GEOGEBRA ═════════════════════════════════════
describe("(5E) playback chỉ đổi MỘT SỐ NGUYÊN", () => {
  const src = readFileSync(join(__dirname, "scene3d-playback.tsx"), "utf8");

  it("KHÔNG có công cụ dựng hình / kéo thả / nhập lệnh", () => {
    // Hình chỉ có thể đến từ một chương trình đã qua thẩm định. Đó là toàn bộ
    // khác biệt giữa hệ này và một phần mềm vẽ hình.
    for (const cam of ["DragControls", "TransformControls", "Raycaster",
                       "onPointerDown", "onPointerMove", "onDrag",
                       'type="text"', "textarea", "contentEditable"]) {
      expect(src, `playback dùng ${cam}`).not.toContain(cam);
    }
  });

  it("KHÔNG đụng toạ độ hay đối tượng của cảnh", () => {
    for (const cam of ["xyz", "normal", "direction", "vertices", "faces",
                       "polygon", "toNumber", "toVec3"]) {
      expect(src, `playback đọc ${cam}`).not.toContain(cam);
    }
  });

  it("KHÔNG import three — nó không vẽ gì cả", () => {
    // Danh sách TRẮNG, không phải danh sách đen: thêm một nguồn mới phải là
    // quyết định được nói ra. `components/icons` có mặt vì `ui-hygiene.test.ts`
    // CẤM ký tự Unicode làm icon — nó bắt được `▶`/`❚❚` tôi viết ở bản đầu.
    const imports = [...src.matchAll(/from ["']([^"']+)["']/g)].map((m) => m[1]);
    expect(imports.sort()).toEqual([
      "../../../components/icons", "./scene3d-model", "./scene3d-view", "react",
    ]);
  });

  it("chỉ có ĐÚNG hai `useState`: bước và trạng thái phát", () => {
    // Thêm state thứ ba là dấu hiệu playback bắt đầu sở hữu một thứ khác ngoài
    // thời gian — và đó là lúc nó trượt thành công cụ dựng hình.
    expect((src.match(/useState/g) ?? []).length).toBe(3); // 1 import + 2 dùng
  });

  it("`scene` đi vào và đi ra NGUYÊN VẸN cùng tham chiếu", () => {
    const s = scene();
    const truoc = JSON.stringify(s);
    renderToString(<Scene3DPlayer scene={s} initialStep={1} />);
    expect(JSON.stringify(s)).toBe(truoc);
  });
});
