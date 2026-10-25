import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { renderToString } from "react-dom/server";
import { PHONG_CACH_SCENE3D } from "./scene3d-roles";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  LINE_DISPLAY_HALF_LENGTH,
  PLANE_DISPLAY_SIZE,
  RENDER_KINDS,
  cauTrucGocNhin,
  clampStep,
  diemChoDuong,
  diemNeoNhanMatPhang,
  doanDuongThang,
  highlightedAt,
  moRongDaGiacMatPhang,
  narrationAt,
  objectsAt,
  solutionAt,
  stepCount,
  toNumber,
  toVec3,
  type Scene3D,
  type ExactVec3,
} from "./scene3d-model";
import {
  GEOMETRY_WEBGL_FALLBACK,
  Scene3DWorkspace,
  buildObject3D,
  chonCuThe,
  dungLuoiNenSuPham,
  semanticIdOf,
  vatNhanChung,
  datCoGocVuong,
  DO_MO_TOI_THIEU,
  updateCanonicalEdgeVisibility,
} from "./scene3d-view";

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
  it("đúng mười một loại, không hơn", () => {
    // `circle` + `curved_solid` thêm 2026-09-03 — HAI, không phải ba: một
    // loại vẽ chở cả cầu/trụ/nón, phân biệt bằng `curved_kind` trong dữ liệu.
    //
    // `ellipse` thêm 2026-09-07 (thiết diện xiên của hình trụ). Nó KHÔNG mượn
    // `circle`, và đó là ngữ nghĩa chứ không phải trang trí: một đường tròn
    // vẽ được từ MỘT bán kính, một elip cần hai bán trục VÀ biết nó xoay thế
    // nào trong mặt phẳng của nó.
    //
    // `segment` thêm 2026-09-25: đoạn thẳng chuẩn tắc hữu hạn (`segment3`/`construct_segment`),
    // có hai đầu mút xác định (`point_a`, `point_b`), phân biệt với đường thẳng toán học vô hạn (`line`).
    expect([...RENDER_KINDS]).toEqual([
      "point_marker", "line", "segment", "surface", "mesh", "polygon", "readout",
      "circle", "ellipse", "curved_solid",
      // KHÔNG phải một loại hình vẽ mới: `non_visual` là lời khai *"vật này
      // không có hình đúng trên khung"* — hiện chỉ vectơ, vì một vectơ tự do
      // không có vị trí. Trước 2026-09-02 vectơ đi qua dưới lốt `point3` và
      // hiện thành một chấm ở toạ độ bằng THÀNH PHẦN của nó.
      "non_visual",
    ]);
  });

  it("KHÔNG có primitive ngoài hợp đồng ngữ nghĩa", () => {
    const src = readFileSync(join(__dirname, "scene3d-view.tsx"), "utf8");
    // Luật KHÔNG đổi: renderer chỉ được vẽ thứ mà một chương trình TẠO RA
    // ĐƯỢC. Thêm một primitive không có ngữ nghĩa sau lưng là đẻ ra năng lực
    // giả — người học nhìn thấy một hình mà hệ không tính được gì trên nó.
    //
    // 2026-09-03: `CylinderGeometry`/`ConeGeometry`/`SphereGeometry` rời khỏi
    // danh sách cấm vì `construct_curved_solid` nay TẠO RA chúng thật. Bốn cái
    // còn lại vẫn cấm — không `curved_kind` nào sinh ra chúng.
    for (const cam of ["TorusGeometry", "TubeGeometry", "LatheGeometry",
                       "ExtrudeGeometry", "ShapeGeometry"]) {
      expect(src).not.toContain(cam);
    }
  });

  it("mỗi primitive cong PHẢI có một `curved_kind` ở backend đỡ lưng", () => {
    // Cổng thay thế, và nó CHẶT HƠN danh sách cấm cũ: thay vì liệt kê thứ
    // không được dùng (một danh sách sẽ luôn thiếu), nó đòi chiều ngược lại —
    // mọi hình cong renderer vẽ phải truy được về thẩm quyền loại khối.
    const src = readFileSync(join(__dirname, "scene3d-view.tsx"), "utf8");
    const py = readFileSync(
      join(__dirname, "../../../../../backend/app/simulation/geometry/curved.py"),
      "utf8",
    );
    const dungToi = ["Sphere", "Cylinder", "Cone"].filter((g) =>
      src.includes(`${g}Geometry`),
    );
    expect(dungToi.length).toBeGreaterThan(0);
    for (const g of dungToi) {
      // `SphereGeometry` ↔ `"ball"`; hai cái kia trùng tên với `curved_kind`.
      const loai = g === "Sphere" ? "ball" : g.toLowerCase();
      expect(py, `renderer vẽ ${g} mà backend không có loại '${loai}'`)
        .toContain(`"${loai}"`);
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
    // W17: lớp nhãn số đo cũng là phía trình bày — điểm neo chỉ là trung bình toạ độ backend phát.
    const soDo = readFileSync(join(__dirname, "scene3d-annotations.ts"), "utf8");
    // W2 · D: hình phụ cũng là phía trình bày — chỉ quyết dựng hay không.
    const phu = readFileSync(join(__dirname, "scene3d-auxiliary.ts"), "utf8");
    for (const cam of [".cross(", ".dot(", "Plane(", "distanceTo", "angleTo",
                       "projectOnPlane"]) {
      expect(view, `view dùng ${cam}`).not.toContain(cam);
      expect(model, `model dùng ${cam}`).not.toContain(cam);
      expect(soDo, `scene3d-annotations dùng ${cam}`).not.toContain(cam);
      expect(phu, `scene3d-auxiliary dùng ${cam}`).not.toContain(cam);
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
      // `./scene3d-subentities` THÊM 2026-08-30, và đây là quyết định được
      // nói ra: khung nhìn nay hỏi CÙNG một thẩm quyền "vật nào đang có mặt"
      // với cây phân rã. Trước đó nó tự hỏi `objectsAt`, và mặt/cạnh — vốn
      // không có sự kiện timeline riêng — không bao giờ được dựng, nên raycast
      // chỉ trúng khối. Module ấy THUẦN: có test riêng buộc nó không nhập
      // three, không toán hình học.
      // `./pick-target` THÊM 2026-08-30: ĐÍCH BẤM tách khỏi cỡ nhìn. Module
      // thuần, không three, không toán hình học — có test riêng khoá điều đó.
      // `./scene3d-presentation` và `./scene3d-camera` THÊM ở lượt hoàn thiện
      // trình bày. Cả hai THUẦN và cả hai chỉ trả về QUYẾT ĐỊNH HIỂN THỊ:
      // gọi một vật bằng ký hiệu nào, có vẽ nó lên khung mặc định không, ẩn
      // nhãn nào khi hai nhãn chồng nhau, và đặt camera ở đâu cho hình vừa
      // khung. Không cái nào đọc `Scene3D` để suy ra một quan hệ hình học,
      // không cái nào sinh toạ độ mới. Hai test ngay dưới khoá điều đó.
      // `./polygon-triangulate` THÊM 2026-09-07
      // (`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION`), và nó THUẦN theo đúng
      // nghĩa guard này bảo vệ: nó KHÔNG quyết định gì về hình. Thứ tự đỉnh
      // quanh mặt do kernel quyết; module chỉ **nối** chúng lại, và mọi tam
      // giác nó trả về là ba CHỈ SỐ vào chính mảng đầu vào — không một toạ độ
      // nào do frontend sinh ra.
      //
      // Vì sao phải có: quạt tam giác cũ chỉ đúng với mặt LỒI, còn mặt lõm bị
      // nó **lấp mất phần lõm**. Sửa thể tích ở kernel mà để renderer lấp
      // phần lõm là chữa nửa bệnh — con số đúng, thứ học sinh NHÌN THẤY vẫn
      // sai. Test riêng của module khoá tính thuần ấy.
      //
      // `./scene3d-roles` THÊM ở W12: bảng MÀU VAI TRÒ dùng chung với bảng
      // lời giải — chỉ hằng số màu, không three, không toán hình học. Tách ra
      // để một màu mang MỘT nghĩa ở cả khung 3D lẫn CSS (test đồng bộ riêng).
      //
      // `./scene3d-annotations` THÊM ở W17 (§15.4), nói ra: nhãn số đo trên
      // hình. Module THUẦN, không three; nó chỉ quyết nhãn nào hiện ở bước nào
      // (luật khả dụng của lớp lời giải), neo ở đâu (TRUNG BÌNH toạ độ backend
      // phát — không chân đường vuông góc, không giao điểm) và đặt hộp chữ
      // tránh nhau. Chủ thể do backend gắn; giá trị là chữ payload. Quét chuỗi
      // cấm ở test "không tích có hướng…" phía trên nay soi cả module này.
      //
      // `./scene3d-auxiliary` THÊM ở regular-square-pyramid-w02 · D, nói ra:
      // hình phụ (vai CONSTRUCT_AUXILIARY_GEOMETRY của backend) nào ẩn ở bước
      // nào. THUẦN, không three, không toạ độ: chỉ đọc vai trò, `depends` và
      // tập vật có mặt theo bước — quyết DỰNG hay KHÔNG, không tính hình.
      //
      // `./scene3d-chart` THÊM ở exact-dimensions, nói ra: BIÊN HIỂN THỊ của khung affine. Metric khung G do
      // backend tính CHÍNH XÁC (`geometry/metric.py`) và phát ở `chart_metric`; module chỉ áp ánh xạ tuyến tính T
      // (Tᵀ·T = G) cho toạ độ để vẽ hình Euclid — không suy quan hệ, không quyết một sự kiện hình học, không đáp số;
      // cảnh không metric đi qua NGUYÊN VẸN. View chỉ nhập `maTranKhung4` cho ảnh chụp camera của bộ đo.
      expect(["react", "three", "three/addons/controls/OrbitControls.js",
              "./scene3d-model", "./interaction-state",
              "./scene3d-subentities", "./pick-target",
              "./scene3d-presentation", "./scene3d-camera",
              "./scene3d-edge-visibility",
              "./polygon-triangulate", "./scene3d-roles",
              "./scene3d-annotations", "./scene3d-auxiliary", "./scene3d-chart"]).toContain(i);
    }
  });

  it("`scene3d-presentation` là quy tắc TRÌNH BÀY thuần — không three, không toán hình học", () => {
    const src = readFileSync(join(__dirname, "scene3d-presentation.ts"), "utf8");
    expect(src).not.toMatch(/from ["']three/);
    for (const cam of ["intersect", "project_onto", "midpoint", "distance_sq",
                       "predicates", "kernel", "Fraction"]) {
      expect(src.includes(cam), `không được nhắc ${cam}`).toBe(false);
    }
    // Nó chỉ nhập KIỂU, không nhập giá trị nào từ mô hình cảnh.
    expect(src).toMatch(/import type \{ SceneObject \} from "\.\/scene3d-model"/);
  });

  it("`scene3d-camera` chỉ đặt KHUNG NHÌN, và không bao giờ trả NaN", async () => {
    const src = readFileSync(join(__dirname, "scene3d-camera.ts"), "utf8");
    expect(src).not.toMatch(/from ["']three/);
    expect(src).not.toMatch(/from ["']\.\/scene3d-model/);

    const m = await import("./scene3d-camera");
    // Hộp bao suy biến về MỘT ĐIỂM: bán kính 0. Không được ra NaN, và phải
    // lùi về khoảng cách tối thiểu thay vì đặt camera trùng điểm nhìn.
    const mot = m.khungNhinVua(
      { min: [1, 1, 1], max: [1, 1, 1] }, 50, 16 / 9);
    expect(mot).not.toBeNull();
    for (const v of [...mot!.viTri, ...mot!.nhinVao]) expect(Number.isFinite(v)).toBe(true);

    // Đầu vào hỏng ⇒ `null` để nơi gọi GIỮ NGUYÊN khung nhìn, chứ không nhảy
    // tới một chỗ vô nghĩa.
    expect(m.khungNhinVua(null, 50, 1)).toBeNull();
    expect(m.khungNhinVua({ min: [0, 0, 0], max: [1, 1, 1] }, 0, 1)).toBeNull();
    expect(m.khungNhinVua({ min: [0, 0, 0], max: [1, 1, 1] }, 50, 0)).toBeNull();
    expect(m.hopBaoCuaDiem([[0, 0, Number.NaN]])).toBeNull();
    expect(m.hopBaoCuaDiem([])).toBeNull();

    // Hộp to hơn ⇒ camera lùi xa hơn. Đây là toàn bộ điều "vừa khung" nghĩa là.
    const gan = m.khungNhinVua({ min: [-1, -1, -1], max: [1, 1, 1] }, 50, 16 / 9)!;
    const xa = m.khungNhinVua({ min: [-10, -10, -10], max: [10, 10, 10] }, 50, 16 / 9)!;
    expect(Math.hypot(...xa.viTri)).toBeGreaterThan(Math.hypot(...gan.viTri));

    // Hướng nhìn mặc định không suy biến: tránh trùng phương với đường chéo đáy x=y
    const vuong = m.khungNhinVua({ min: [0, 0, 0], max: [3, 3, 6] }, 50, 16 / 9)!;
    const huongX = vuong.viTri[0] - vuong.nhinVao[0];
    const huongY = vuong.viTri[1] - vuong.nhinVao[1];
    expect(Math.abs(huongY / huongX - 1)).toBeGreaterThan(0.3);
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
    // Soi TÊN TRƯỜNG khai báo, không soi mọi chữ: bản cũ cấm cả chuỗi con
    // `boundary`, nên bắt oan `boundary_edge_ids` — danh sách ID cạnh (topo),
    // không phải một biên hình học. Biên hình học vẫn bị cấm như trước.
    const truongKhai = (src: string) =>
      [...src.matchAll(/^\s*(?:readonly\s+)?([A-Za-z_]\w*)\??\s*:/gm)].map((m) => m[1]);
    const BIEN_HINH_HOC = new Set(["boundary", "corners", "extent", "bounds"]);
    const cam = (src: string) => truongKhai(src).filter((n) => BIEN_HINH_HOC.has(n));
    expect(cam("  boundary: Vec3[];\n  corners?: string[];\n  extent: number;"))
      .toEqual(["boundary", "corners", "extent"]);
    expect(cam("  boundary_edge_ids?: string[];\n  // boundary: chỉ là lời bình")).toEqual([]);
    expect(truongKhai(model), "cửa sổ chứng: bộ đọc phải thấy trường thật")
      .toContain("boundary_edge_ids");
    expect(cam(model)).toEqual([]);
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


// ══ I–L · DỰNG và CHỌN thực thể con ══════════════════════════════════════
//
// Demo tay: 144 cú bấm thật chỉ trúng KHỐI, không trúng mặt nào. Hai nguyên
// nhân, và cả hai đóng ở đây: (a) mặt chưa từng được dựng thành `Object3D`,
// (b) kể cả khi dựng, tia trúng cả mặt lẫn khối và bản cũ lấy `trung[0]`.
describe("(5E) thực thể con: dựng riêng và chọn riêng", () => {
  const view = readFileSync(join(__dirname, "scene3d-view.tsx"), "utf8");

  const khoi = {
    id: "chop", label: "S.ABC", type: "solid", render: "mesh" as const,
    origin: "derived" as const, producer: "construct_solid",
    depends: ["A", "B", "C", "S"],
    vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]] as ExactVec3[],
    vertex_ids: ["A", "B", "C", "S"],
    faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]],
  };

  it("I0 · ĐƯỜNG vô hạn vẽ quanh VÙNG HÌNH, không cố định ±6 (giao tuyến vô hình, run hybrid-semantic-hardening)", () => {
    // Cảnh Hybrid cỡ ~1 đơn vị: giao tuyến (SAB) ∩ (SCD) qua S = (0,0,1), phương AB. Đoạn cố định ±6 đâm qua chỗ
    // camera đứng; SwiftShader bỏ trắng cả nét, GPU thật vẽ một vệt loe tới mép khung.
    const gt = {
      id: "gt_f5", label: "Giao tuyến", type: "line3", render: "line" as const, origin: "derived" as const,
      producer: "intersect_plane_plane", depends: [],
      point: ["0", "0", "1"] as ExactVec3, direction: ["-1", "0", "0"] as ExactVec3,
    };
    const hinh: [number, number, number][] = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1]];
    const dau = (o: ReturnType<typeof buildObject3D>) => {
      const net = o!.getObjectByName("line:gt_f5:thay") as unknown as { geometry: { getAttribute(n: string): { getX(i: number): number; getY(i: number): number; getZ(i: number): number } } };
      const p = net.geometry.getAttribute("position");
      return [0, 1].map((i) => [p.getX(i), p.getY(i), p.getZ(i)]);
    };
    const [a, b] = dau(buildObject3D(gt, false, undefined, hinh));
    // Trong vùng hình (theo phương đường: hình chiếu [0, 1], lề `PLANE_PATCH_MARGIN`), không ra tới ±6.
    for (const p of [a, b]) expect(Math.abs(p[0])).toBeLessThan(2);
    expect(Math.abs(a[0] - b[0])).toBeGreaterThanOrEqual(1);
    // Hình học giữ nguyên: hai đầu mút vẫn nằm trên ĐÚNG đường qua S, phương (±1, 0, 0).
    for (const p of [a, b]) expect([p[1], p[2]]).toEqual([0, 1]);
    // Không có điểm nền (nơi gọi cũ) ⇒ rơi về độ dài cố định như trước.
    const [c, d] = dau(buildObject3D(gt, false));
    expect(Math.abs(c[0] - d[0])).toBeCloseTo(2 * LINE_DISPLAY_HALF_LENGTH);
  });

  it("I1 · độ dài tối thiểu của đoạn đường thẳng theo TỈ LỆ cảnh (review S2)", () => {
    const d = (s: number, huong: [number, number, number], diem: [number, number, number][]) => {
      const r = doanDuongThang([0, 0, 0], huong, diem)!;
      return Math.hypot(r[1][0] - r[0][0], r[1][1] - r[0][1], r[1][2] - r[0][2]) / s;
    };
    // cảnh cỡ 0,05: đường theo chiều mỏng không được dài gấp hàng chục lần cảnh (lại đâm qua camera)
    const nho = 0.05;
    expect(d(nho, [0, 0, 1], [[0, 0, 0], [nho, 0, 0], [nho, nho, 0], [0, nho, 0]])).toBeLessThan(3);
    // cảnh cỡ 100, đường thẳng đứng mà chỉ có điểm đáy: không còn là một mẩu dài 2
    const lon = 100;
    expect(d(lon, [0, 0, 1], [[0, 0, 0], [lon, 0, 0], [lon, lon, 0], [0, lon, 0]])).toBeGreaterThan(0.5);
  });

  it("I · MẶT dựng thành một Object3D mang đúng id `chop::face:n`", () => {
    const m = {
      id: "chop::face:1", label: "ABS", type: "face", render: "polygon" as const,
      origin: "derived" as const, producer: "construct_solid.face[1]",
      depends: ["A", "B", "S"],
      polygon: [["0", "0", "0"], ["1", "0", "0"], ["0", "0", "1"]] as ExactVec3[],
    };
    const o = buildObject3D(m, false);
    expect(o).not.toBeNull();
    expect(o!.name).toBe("face:chop::face:1");
    expect(semanticIdOf(o!.name)).toBe("chop::face:1");
    // ĐẶC, không phải đường viền: một nét 1px gần như không bấm trúng.
    expect(o!.type).toBe("Mesh");
  });

  it("J · CẠNH dựng riêng và mang đúng id", () => {
    const e = {
      id: "chop::edge:A-B", label: "AB", type: "edge", render: "line" as const,
      origin: "derived" as const, producer: "construct_solid.edge",
      depends: ["A", "B"],
      polygon: [["0", "0", "0"], ["1", "0", "0"]] as ExactVec3[],
    };
    const o = buildObject3D(e, false);
    expect(o).not.toBeNull();
    expect(semanticIdOf(o!.name)).toBe("chop::edge:A-B");
  });

  it("K · tia trúng cả mặt lẫn khối ⇒ chọn MẶT, không rơi về khối", () => {
    expect(chonCuThe(["chop::face:1", "chop"])).toBe("chop::face:1");
    expect(chonCuThe(["chop", "chop::face:1"])).toBe("chop::face:1");
  });

  it("L · tia trúng cả cạnh lẫn khối ⇒ chọn CẠNH", () => {
    expect(chonCuThe(["chop::edge:A-B", "chop"])).toBe("chop::edge:A-B");
  });

  it("K2 · ĐIỂM gần hơn thì THẮNG mặt — không nhảy qua nó", () => {
    // Đây là lỗi bản sửa thứ nhất: luật "lấy vật con đầu tiên" bỏ qua đỉnh
    // (đỉnh không có `::`) để lấy mặt phía sau. Demo tay đo 0/144 cú bấm
    // trúng điểm. Thứ tự KHOẢNG CÁCH phải được giữ.
    expect(chonCuThe(["A", "chop::face:1", "chop"])).toBe("A");
    expect(chonCuThe(["chop::edge:A-B", "A", "chop"])).toBe("chop::edge:A-B");
  });

  it("K3 · không có vật con ⇒ KHỐI vẫn chọn được như thường", () => {
    expect(chonCuThe(["chop"])).toBe("chop");
    expect(chonCuThe([])).toBeNull();
  });

  it("luật chọn nằm TRONG view, không chỉ trong test", () => {
    expect(view).toContain("chonCuThe(ids,");
    expect(view).not.toContain("pickSemanticId(trung[0]");
  });

  it("khung nhìn hỏi CÙNG thẩm quyền có-mặt với cây", () => {
    expect(view).toContain("entitiesPresentAt(scene, buoc, objectsAt)");
    // Không còn bản sao logic presence riêng cho renderer.
    expect(view).not.toContain("new Set(hienTai.map");
  });

  it("khối vẫn dựng được — thực thể con KHÔNG thay nó", () => {
    const o = buildObject3D(khoi, false);
    expect(o).not.toBeNull();
    expect(semanticIdOf(o!.name)).toBe("chop");
  });

  it("dịch chuyển TRÌNH BÀY không đi qua bộ phân tích phân số", () => {
    // `toNumber("0.244949")` ném — và đó là cái đã làm sập khung 3D.
    expect(view).not.toContain("toNumber(bd.translate");
    // Vị trí trình bày đi qua ĐÚNG MỘT hàm. Bản trước ghim nguyên văn dòng
    // `obj.position.set(bd.translate[0]`, và khi phép đặt vị trí dời vào
    // `datViTriTrinhBay` thì guard đỏ vì một lý do chẳng liên quan tới thứ
    // nó bảo vệ. Ghim Ý ĐỊNH, đừng ghim chính tả.
    expect(view).toContain("datViTriTrinhBay(obj,");
  });

  it("vị trí trình bày CỘNG vào vị trí gốc, không GHI ĐÈ nó", () => {
    // Ghi đè kéo mọi ĐIỂM về gốc toạ độ — đường/mặt/khối thì vô hại vì toạ độ
    // nướng trong `BufferGeometry`, nên lỗi im lặng với 4/5 loại vật.
    expect(view).toContain("obj.position.x + bd.translate[0]");
  });
});

/**
 * `NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` §9 — KHỐI LÕM phải TRÔNG ĐÚNG.
 *
 * Đo trên buffer THẬT mà `buildObject3D` phát ra, không đo trên module chia
 * tam giác. Lý do: `polygon-triangulate.test.ts` chứng minh module đúng, còn
 * bộ này chứng minh **renderer gọi nó**. Trả `scene3d-view` về quạt tam giác
 * thì đúng ba ô dưới đây đỏ — đó là phép tiêm ⑤ của wave.
 *
 * Khối: chóp đáy LÕM `A(0,0,0) B(4,0,0) C(4,4,0) D(2,1,0) E(0,4,0)`,
 * đỉnh `S(2,1/2,6)` — cùng bộ toạ độ với `test_nonconvex_polyhedron_volume.py`.
 * Đáy có diện tích **10**.
 *
 * ĐO ĐƯỢC khi tiêm quạt lại (2026-09-07): đáy phủ **22**, lệch `+12`. Con số
 * `14` trong `polygon-triangulate.test.ts` là của winding bắt đầu ở `A`; mặt
 * đáy của khối khai theo chiều `(4,3,2,1,0)` nên gốc quạt là `E`, và quạt từ
 * `E` phủ nhiều hơn. Cùng một lỗi, hai con số — ghi cả hai để lần sau không ai
 * tưởng một trong hai là số sai.
 */
describe("(5D-lõm) renderer trình bày ĐÚNG phần lõm", () => {
  const khoiLom = {
    id: "lom", label: "S.ABCDE", type: "solid", render: "mesh" as const,
    origin: "derived" as const, producer: "construct_solid",
    depends: ["A", "B", "C", "D", "E", "S"],
    vertices: [["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"],
               ["2", "1", "0"], ["0", "4", "0"], ["2", "1/2", "6"]] as ExactVec3[],
    vertex_ids: ["A", "B", "C", "D", "E", "S"],
    faces: [[4, 3, 2, 1, 0], [0, 1, 5], [1, 2, 5], [2, 3, 5], [3, 4, 5], [4, 0, 5]],
  };

  /** Mọi tam giác trong buffer vị trí của khối, gom theo bộ ba. */
  function tamGiacCuaKhoi(): [number, number, number][][] {
    const o = buildObject3D(khoiLom, false);
    expect(o).not.toBeNull();
    const ra: [number, number, number][][] = [];
    o!.traverse((con) => {
      const g = (con as { geometry?: { attributes?: Record<string, unknown> } }).geometry;
      const p = g?.attributes?.position as { array?: ArrayLike<number> } | undefined;
      // Chỉ lấy MESH; `EdgesGeometry` của khung cạnh cũng có `position`.
      if (!p?.array || !(con as { isMesh?: boolean }).isMesh) return;
      /* …và BỎ lớp chiều sâu. Nó là bản sao VÔ HÌNH dùng CHUNG hình học với
         khối, dựng ra để đường biết mình có bị che không
         (`SCENE3D_DYNAMIC_HIDDEN_LINES`). Đếm nó vào đây thì mọi con số tam
         giác nhân đôi, và phép đo diện tích chiếu mất nghĩa — nó không thêm
         một tam giác nào của KHỐI. */
      if (con.userData?.chieuSau) return;
      /* Cùng lý do với lượt MẶT SAU của vỏ SGK (`voKhoiHaiLuot`): một mesh dùng CHUNG hình học với mặt trước,
         chỉ khác `side` — không thêm tam giác nào của khối. */
      if (con.userData?.voKhoiMatSau) return;
      const a = p.array;
      for (let i = 0; i + 8 < a.length; i += 9) {
        ra.push([[a[i], a[i + 1], a[i + 2]],
                 [a[i + 3], a[i + 4], a[i + 5]],
                 [a[i + 6], a[i + 7], a[i + 8]]]);
      }
    });
    return ra;
  }

  /** Tam giác của ĐÁY = ba đỉnh đều nằm trên `z = 0`. */
  function tamGiacDay() {
    return tamGiacCuaKhoi().filter((t) => t.every((p) => Math.abs(p[2]) < 1e-9));
  }

  const dienTich2D = (t: [number, number, number][]) =>
    Math.abs((t[1][0] - t[0][0]) * (t[2][1] - t[0][1])
      - (t[1][1] - t[0][1]) * (t[2][0] - t[0][0])) / 2;

  /** Điểm có nằm trong đa giác đáy không — ray casting, đáy nằm trên Oxy. */
  const DAY: [number, number][] = [[0, 0], [4, 0], [4, 4], [2, 1], [0, 4]];
  function trongDay(x: number, y: number): boolean {
    let trong = false;
    for (let i = 0, j = DAY.length - 1; i < DAY.length; j = i, i += 1) {
      const [xi, yi] = DAY[i];
      const [xj, yj] = DAY[j];
      if ((yi > y) !== (yj > y)
        && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) trong = !trong;
    }
    return trong;
  }

  it("RENDERED_PROJECTED_AREA = 10 — không phải 14 của quạt", () => {
    const tong = tamGiacDay().reduce((s, t) => s + dienTich2D(t), 0);
    expect(tong).toBeCloseTo(10, 9);
  });

  it("NOTCH_REMAINS_EMPTY — phần lõm KHÔNG bị tam giác nào lấp", () => {
    // `(2, 5/3)` là trọng tâm của tam giác `A-C-D` — mảnh mà quạt cũ vẽ ra và
    // nằm HOÀN TOÀN ngoài đáy. Đã kiểm: điểm này ngoài đa giác.
    expect(trongDay(2, 5 / 3)).toBe(false);
    for (const t of tamGiacDay()) {
      const g: [number, number] = [(t[0][0] + t[1][0] + t[2][0]) / 3,
                                   (t[0][1] + t[1][1] + t[2][1]) / 3];
      // Không tam giác nào CHỨA điểm lõm: dùng dấu của ba tích có hướng.
      const d = (u: number[], v: number[]) =>
        (v[0] - u[0]) * (5 / 3 - u[1]) - (v[1] - u[1]) * (2 - u[0]);
      const s = [d(t[0], t[1]), d(t[1], t[2]), d(t[2], t[0])];
      expect(s.some((z) => z < -1e-9) && s.some((z) => z > 1e-9)).toBe(true);
      // …và chính tam giác ấy phải nằm TRONG đáy.
      expect(trongDay(g[0], g[1])).toBe(true);
    }
  });

  it("TRIANGLE_OVERLAP_OUTSIDE_FACE = 0", () => {
    // Mọi tam giác nằm trong đáy (ô trên) + tổng diện tích đúng bằng diện
    // tích đáy ⇒ không mảnh nào chồng lên mảnh nào. Quạt cũ vi phạm CẢ HAI:
    // `A-C-D` ra ngoài, còn `A-B-C` và `A-D-E` chồng nhau.
    const tong = tamGiacDay().reduce((s, t) => s + dienTich2D(t), 0);
    expect(tong - 10).toBeCloseTo(0, 9);
    expect(tamGiacDay()).toHaveLength(3);
  });

  it("mặt bên vẫn dựng đủ — sửa đáy không được nuốt mặt nào", () => {
    // 3 tam giác đáy + 5 mặt bên tam giác.
    expect(tamGiacCuaKhoi()).toHaveLength(8);
  });

  it("renderer gọi ĐÚNG thẩm quyền chia tam giác, không tự quạt lại", () => {
    const view = readFileSync(join(__dirname, "scene3d-view.tsx"), "utf8");
    expect(view).toContain("chiaTamGiac(mat)");
    expect(view).toContain("chiaTamGiac(pts)");
    // Quạt cũ: `for (let i = 1; i < …length - 1` ngay trong khung nhìn.
    expect(view).not.toMatch(/for \(let i = 1; i < \w+\.length - 1/);
  });

  it("FINDING-D1/D2: mặt con có `display_role === 'hit_proxy'` giữ nguyên Mesh bắt chuột nhưng không nhuộm màu khi chưa chọn, và tô nổi bật khi được chọn", () => {
    const m = {
      id: "chop::face:1", label: "ABS", type: "face", render: "polygon" as const,
      display_role: "hit_proxy" as const,
      origin: "derived" as const, producer: "construct_solid.face[1]",
      depends: ["A", "B", "S"],
      polygon: [["0", "0", "0"], ["1", "0", "0"], ["0", "0", "1"]] as ExactVec3[],
    };
    const thuong = buildObject3D(m, false) as unknown as {
      name: string; type: string; material: { opacity: number; colorWrite: boolean };
    };
    expect(thuong.name).toBe("face:chop::face:1");
    expect(thuong.type).toBe("Mesh");
    expect(thuong.material.opacity).toBe(0);
    expect(thuong.material.colorWrite).toBe(false);

    const chon = buildObject3D(m, true) as unknown as {
      material: { opacity: number; colorWrite: boolean };
    };
    expect(chon.material.opacity).toBe(0.18);
    expect(chon.material.colorWrite).toBe(true);
  });

  it("W2 / FINDING-C2: miếng mặt phẳng co giãn theo bán kính điểm định nghĩa (không ép tối thiểu 2 đơn vị trên hình đơn vị) và có độ đục thụ động ≤ 0.12", async () => {
    const M = await import("./scene3d-model");
    const k = M.khungMatPhang([0, 0, 0], [0, 0, 1], [[0, 0, 0], [1, 0, 0], [0, 1, 0]]);
    expect(k).not.toBeNull();
    // Đường chéo tam giác vuông cạnh 1 là √2 ≈ 1.414 ⇒ bán kính từ tâm hộp bao là √2/2 ≈ 0.707, nhân 2 * 1.15 ≈ 1.626 < 2
    expect(k!.canh).toBeLessThan(1.8);
    expect(k!.canh).toBeGreaterThan(1.4);

    const mp = {
      id: "mp1_gt_g", label: "(SAC)", type: "plane3", render: "surface" as const,
      origin: "derived" as const, producer: "construct_plane",
      depends: ["A", "C", "S"],
      point: ["0", "0", "0"] as ExactVec3,
      normal: ["0", "1", "0"] as ExactVec3,
    };
    const mesh = buildObject3D(mp, false, undefined, [[0, 0, 0], [1, 0, 0], [0, 0, 1]]) as unknown as {
      material: { opacity: number };
    };
    expect(mesh.material.opacity).toBeLessThanOrEqual(0.12);
  });

  it("VISUAL-FE-1: đường thẳng đi qua ≥2 điểm trên hình (`S`, `H`) lấy tâm theo đoạn trên đường, không bị đỉnh ngoài đường (`B`, `C`) kéo lệch", () => {
    const diem: [number, number, number][] = [
      [0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0], [0, 0, 3], [1, 0, 3],
    ];
    const [a, b] = doanDuongThang([0, 0, 3], [-1, 0, 0], diem)!;
    const tamX = (a[0] + b[0]) / 2;
    const dai = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
    // Đoạn SH trên đường là x ∈ [0, 1] ⇒ tâm phải ở x = 0.5, đối xứng hai đầu, tổng độ dài gọn (< 2.2)
    expect(tamX).toBeCloseTo(0.5, 6);
    expect(dai).toBeGreaterThan(1.2);
    expect(dai).toBeLessThan(2.2);
  });

  it("FE-4 (review tích hợp): đoạn hiển thị của đường chỉ căn theo các điểm của hình nằm trên đường — điểm neo xa hình không kéo lệch", () => {
    // Đường y = z = 0 neo tại x = 10 (một điểm bất kỳ backend chọn); trên đường có A(0) và B(2) của hình.
    const diem: [number, number, number][] = [[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0], [0, 0, 3]];
    const [a, b] = doanDuongThang([10, 0, 0], [1, 0, 0], diem)!;
    const xs = [a[0], b[0]].sort((p, q) => p - q);
    expect((xs[0] + xs[1]) / 2).toBeCloseTo(1, 6);      // tâm giữa A và B
    expect(xs[0]).toBeLessThan(0);                      // hai đầu vẫn vượt qua A và B: đường, không phải đoạn
    expect(xs[1]).toBeGreaterThan(2);
    expect(xs[1]).toBeLessThan(10);                     // không kéo tới điểm neo
  });

  it("FE-4 (review tích hợp): chân vuông góc NGOÀI cạnh (không phải điểm của cảnh) vẫn nằm trong phần vẽ của đường", () => {
    // d(A, BC): chân H = (1,−1,0) nằm ngoài đoạn BC; H chỉ có trong nhân chứng của đại lượng, không là vật của cảnh.
    const p = (id: string, xyz: number[]) => ({ id, type: "point3", render: "point", depends: [], xyz: xyz.map(String) });
    const objects = [p("A", [0, 0, 0]), p("B", [2, 0, 0]), p("C", [3, 1, 0]), p("S", [1, 0, 2]),
      { id: "dt", type: "line3", render: "line", depends: ["B", "C"], point: ["2", "0", "0"], direction: ["1", "1", "0"] },
      { id: "kq", type: "scalar", render: "non_visual", depends: ["A", "dt"],
        annotation: { witness: { from: "A", foot: ["1", "-1", "0"], on: "dt", marker: { u: ["1", "1", "0"], v: ["-1", "1", "0"] } } } },
    ] as unknown as Scene3D["objects"];
    const [a, b] = doanDuongThang([2, 0, 0], [1, 1, 0], diemChoDuong(objects, "dt"))!;
    const t = (q: number[]) => ((q[0] - 2) + q[1]) / Math.SQRT2;   // toạ độ dọc đường tính từ B
    const [lo, hi] = [t(a), t(b)].sort((x, y) => x - y);
    expect(lo).toBeLessThan(-Math.SQRT2);               // H (t = −√2) ở trong phần vẽ, kèm phần kéo dài
    expect(hi).toBeGreaterThan(Math.SQRT2);             // C (t = √2) cũng vậy
  });

  it("VISUAL-FE-4: mặt phẳng có ≥3 điểm không thẳng hàng nằm trên nó dựng đúng miền đa giác phẳng của các điểm đó, không thò góc vuông xuống dưới đáy", () => {
    const mp = {
      id: "mp_q", label: "(SAB)", type: "plane3", render: "surface" as const,
      origin: "derived" as const, producer: "construct_plane",
      depends: ["A", "B", "S"],
      point: ["0", "0", "0"] as ExactVec3,
      normal: ["0", "-3", "0"] as ExactVec3,
    };
    const diem: [number, number, number][] = [
      [0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0], [0, 0, 3],
    ];
    const mesh = buildObject3D(mp, "dich", undefined, diem)!;
    mesh.updateMatrixWorld(true);
    const pos = (mesh as unknown as { geometry: { getAttribute(n: string): { count: number; getX(i: number): number; getY(i: number): number; getZ(i: number): number } } })
      .geometry.getAttribute("position");
    expect(pos.count).toBe(3);
    for (let i = 0; i < pos.count; i++) {
      expect(pos.getZ(i)).toBeGreaterThanOrEqual(-1e-6);
      expect(pos.getX(i)).toBeGreaterThanOrEqual(-1e-6);
    }
  });

  it("VISUAL-FE-6: ký hiệu góc vuông tại chân H trùng đầu mút B' trên đường BB' quay vào trong đoạn BB' (z ≤ 5), không chĩa ra ngoài khối (z > 5)", () => {
    const w = {
      id: "perpendicular:H",
      vai: "hinh_chieu" as const,
      from: [1.5, 2, 5] as [number, number, number],
      foot: [3, 0, 5] as [number, number, number],
      u: [0, 0, 5] as [number, number, number],
      v: [-1.5, 2, 0] as [number, number, number],
    };
    const diem: [number, number, number][] = [
      [0, 0, 0], [3, 0, 0], [3, 4, 0], [0, 4, 0],
      [0, 0, 5], [3, 0, 5], [3, 4, 5], [0, 4, 5],
    ];
    const nhom = vatNhanChung(w, diem, 0x0284c7, false);
    const goc = nhom.children[1] as unknown as {
      geometry: { getAttribute(n: string): { count: number; getZ(i: number): number } };
      material: { color: { getHex(): number } };
    };
    const pos = goc.geometry.getAttribute("position");
    expect(pos.count).toBe(3);
    expect(pos.getZ(0)).toBeLessThan(5 - 1e-3);
    expect(pos.getZ(1)).toBeLessThan(5 - 1e-3);
    expect(goc.material.color.getHex()).toBe(0x0284c7);
    const cham = nhom.children[2] as unknown as {
      position: { x: number; y: number; z: number };
      userData: { dauDinh?: string };
    };
    expect(cham.userData.dauDinh).toBe("thuong");
    expect([cham.position.x, cham.position.y, cham.position.z]).toEqual([3, 0, 5]);
  });

  it("P1-CORRECTNESS: ký hiệu góc vuông point-to-plane tại chân H nằm trên cạnh biên của mặt phẳng đích (như H trên A'B' của (ABB')) bám dọc cạnh biên đó, trực giao với MH (dot = 0) và nối liền nét đứt đầu tiên từ H", () => {
    const w = {
      id: "kq_q",
      vai: "khoang_cach" as const,
      from: [1.5, Math.sqrt(3) / 2, 3] as [number, number, number],
      foot: [1.5, 0, 3] as [number, number, number],
      u: [-1.5, 0, -3] as [number, number, number],
      v: [0, Math.sqrt(3) / 2, 0] as [number, number, number],
    };
    const diem: [number, number, number][] = [
      [0, 0, 0], [2, 0, 0], [1, Math.sqrt(3), 0],
      [0, 0, 3], [2, 0, 3], [1, Math.sqrt(3), 3],
      [1.5, Math.sqrt(3) / 2, 3], [1.5, 0, 3],
    ];
    const nhom = vatNhanChung(w, diem, 0x0284c7, false);
    const doan = nhom.children[0] as unknown as {
      geometry: { getAttribute(n: string): { getX(i: number): number; getY(i: number): number; getZ(i: number): number } };
      material: { dashSize: number };
    };
    const goc = nhom.children[1] as unknown as {
      geometry: { getAttribute(n: string): { count: number; getX(i: number): number; getY(i: number): number; getZ(i: number): number } };
    };
    const posDoan = doan.geometry.getAttribute("position");
    // Đoạn nét đứt bắt đầu từ chân H để nét đầu tiên luôn nối liền với ký hiệu góc vuông tại H
    expect([posDoan.getX(0), posDoan.getY(0), posDoan.getZ(0)]).toEqual([1.5, 0, 3]);
    const pos = goc.geometry.getAttribute("position");
    expect(pos.count).toBe(3);
    const uVec = [pos.getX(0) - w.foot[0], pos.getY(0) - w.foot[1], pos.getZ(0) - w.foot[2]];
    const vVec = [pos.getX(2) - w.foot[0], pos.getY(2) - w.foot[1], pos.getZ(2) - w.foot[2]];
    // uVec phải nằm dọc cạnh A'B' (y = 0, z = 3 ⇒ uVec[1] = 0, uVec[2] = 0, uVec[0] < 0) thay vì chéo xuống A(0,0,0)
    expect(Math.abs(uVec[1])).toBeLessThan(1e-9);
    expect(Math.abs(uVec[2])).toBeLessThan(1e-9);
    expect(uVec[0]).toBeLessThan(-1e-3);
    // Hai cạnh của ký hiệu góc vuông trực giao tuyệt đối trong không gian thế giới (dot = 0) và có cùng độ dài s
    const dotUV = uVec[0] * vVec[0] + uVec[1] * vVec[1] + uVec[2] * vVec[2];
    expect(Math.abs(dotUV)).toBeLessThan(1e-9);
    const s = Math.hypot(vVec[0], vVec[1], vVec[2]);
    expect(Math.hypot(uVec[0], uVec[1], uVec[2])).toBeCloseTo(s, 6);
    // Nét đứt đầu tiên từ H dài hơn s để đầu mút chan + v1 luôn chạm vào nét, không rơi vào khoảng trống
    expect(doan.material.dashSize).toBeGreaterThanOrEqual(s * 1.04);
  });

  it("SGK: ký hiệu vuông góc có cạnh ≈ 16 px trên khung 720 px, giữ trực giao quanh chân, dấu lặp cùng chân/phương bị ẩn", () => {
    const w = {
      id: "perpendicular:H", vai: "hinh_chieu" as const,
      from: [0, 3, 0] as [number, number, number], foot: [0, 0, 0] as [number, number, number],
      u: [1, 0, 0] as [number, number, number], v: [0, 3, 0] as [number, number, number],
    };
    const diem: [number, number, number][] = [[0, 0, 0], [4, 0, 0], [0, 4, 0], [0, 0, 4]];
    const root = new THREE.Group();
    const a = vatNhanChung(w, diem, 0x0f766e, false);
    const b = vatNhanChung({ ...w, id: "perpendicular:H2" }, diem, 0x0f766e, false);
    root.add(a, b);
    const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    cam.position.set(0, 0, 10);
    cam.lookAt(0, 0, 0);
    cam.updateMatrixWorld(true);
    expect(datCoGocVuong([root], cam, 720)).toBe(1);
    const goc = a.children[1] as THREE.Line;
    expect(goc.visible).toBe(true);
    expect((b.children[1] as THREE.Line).visible).toBe(false);
    goc.updateMatrixWorld(true);
    const p = goc.geometry.getAttribute("position");
    const diemManHinh = (i: number) => {
      const q = new THREE.Vector3().fromBufferAttribute(p, i).applyMatrix4(goc.matrixWorld).project(cam);
      return [q.x * 360, q.y * 360];
    };
    const chan = new THREE.Vector3(0, 0, 0).project(cam);
    const [x0, y0] = diemManHinh(0);
    const [x2, y2] = diemManHinh(2);
    // Target leg = rightAngle.perCanvasHeight × 720, clamped to [minPx, maxPx]. Owner 2026-10-26: readable on mobile —
    // at least 12 px, 15.84 px on a 720 px canvas (was 8–12 px, 10.08 px here).
    const cfgVuong = PHONG_CACH_SCENE3D.rightAngle;
    const L = Math.min(cfgVuong.maxPx, Math.max(cfgVuong.minPx, cfgVuong.perCanvasHeight * 720));
    expect(cfgVuong.minPx).toBeGreaterThanOrEqual(12);
    expect(L).toBeCloseTo(15.84, 2);
    expect(Math.hypot(x0 - chan.x * 360, y0 - chan.y * 360)).toBeCloseTo(L, 2);
    expect(Math.hypot(x2 - chan.x * 360, y2 - chan.y * 360)).toBeCloseTo(L, 2);
    expect((x0 - chan.x * 360) * (x2 - chan.x * 360) + (y0 - chan.y * 360) * (y2 - chan.y * 360)).toBeCloseTo(0, 6);
    const s = L * 10 / (360 / Math.tan((25 * Math.PI) / 180));
    expect((a.userData.corner as number[]).map((x) => +x.toFixed(4))).toEqual([+s.toFixed(4), +s.toFixed(4), 0]);

    // With the orbit target: a pure ORBIT (same target depth) keeps the world size — no coordinate rewrite, so no
    // GPU buffer reallocation (scene3d-orbit-gate); a ZOOM (target depth changes) recomputes it.
    // Target ≠ foot, so an orbit really changes the foot's depth (10 → 9.6).
    const tam = new THREE.Vector3(0, 0, -2);
    cam.lookAt(tam); cam.updateMatrixWorld(true);
    datCoGocVuong([root], cam, 720, tam);
    const coDau = goc.scale.x;
    cam.position.set(7.2, 0, 7.6); cam.lookAt(tam); cam.updateMatrixWorld(true);   // |cam − target| = 12: orbit
    datCoGocVuong([root], cam, 720, tam);
    expect(goc.scale.x).toBe(coDau);
    cam.position.set(0, 0, 4); cam.lookAt(tam); cam.updateMatrixWorld(true);       // zoom: foot depth 10 → 4
    datCoGocVuong([root], cam, 720, tam);
    expect(goc.scale.x).toBeCloseTo(coDau * 0.4, 6);

    // Review I1: the duplicate key is WORLD-space and the strongest mark wins. A faded copy met first must yield to
    // a full-opacity one; the same local foot under a translated (exploded) parent is a different mark.
    const root2 = new THREE.Group();
    const diu = vatNhanChung({ ...w, id: "perpendicular:diu" }, diem, 0x0f766e, true);
    const dam = vatNhanChung({ ...w, id: "perpendicular:dam" }, diem, 0x0f766e, false);
    const tach = new THREE.Group();
    tach.position.set(5, 0, 0);
    tach.add(vatNhanChung({ ...w, id: "perpendicular:tach" }, diem, 0x0f766e, false));
    root2.add(diu, dam, tach);
    expect(datCoGocVuong([root2], cam, 720, tam)).toBe(2);
    expect((diu.children[1] as THREE.Line).visible).toBe(false);
    expect((dam.children[1] as THREE.Line).visible).toBe(true);
    expect((tach.children[0].children[1] as THREE.Line).visible).toBe(true);
  });

  it("Owner 2026-10-26: one backend relation (4 lateral edges ⊥ base) shows ONE mark by default, stable under small turns; emphasis keeps its own", () => {
    const sc = JSON.parse(readFileSync(join(__dirname,
      "../../../../../docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs/fixtures/cuboid_positive.json"), "utf8")).envelope.scene3d as Scene3D;
    const ben = sc.objects.filter((o) => o.perpendicular_witness?.rule === "prism_lateral_altitude");
    expect(ben.map((o) => o.id).sort()).toEqual(["canh_ben_A_A_prime", "canh_ben_B_B_prime", "canh_ben_C_C_prime", "canh_ben_D_D_prime"]);
    const dung = (nhan: string | null) => {
      const root = new THREE.Group();
      for (const o of ben) root.add(buildObject3D(o, o.id === nhan)!);
      return root;
    };
    const hienTai = (root: THREE.Group) => {
      const ra: string[] = [];
      root.traverse((n) => { if (n.name.startsWith("perp_marker:") && n.visible) ra.push(n.name.slice("perp_marker:".length)); });
      return ra.sort();
    };
    const cam = new THREE.PerspectiveCamera(45, 1, 0.1, 200);
    const nhin = (goc: number) => {
      cam.position.set(1.5 + 13 * Math.cos(goc), 2 + 13 * Math.sin(goc), 9); cam.lookAt(1.5, 2, 2.5); cam.updateMatrixWorld(true);
    };
    // Independent openness of each REAL 3D mark as the viewer sees it: a small square of area A at distance r and
    // view-axis depth z projects to f²·A·|n·e|·r/z³; relative to its depth-scaled size that is |n·e|·r/z
    // (n = u×v of the backend directions, e = unit foot → eye). Computed from the camera's forward axis, no projection.
    const mo = (o: (typeof ben)[number]) => {
      const pw = o.perpendicular_witness!;
      const v3 = (p: string[]) => new THREE.Vector3(...p.map((s) => { const [a, b] = s.split("/"); return Number(a) / Number(b ?? 1); }));
      const n = v3(pw.marker.u).normalize().cross(v3(pw.marker.v).normalize());
      const toi = cam.position.clone().sub(v3(pw.foot));
      const z = -toi.dot(cam.getWorldDirection(new THREE.Vector3()));
      return Math.abs(n.dot(toi.clone().normalize())) * (toi.length() / z);
    };
    const tot = () => [...ben].sort((a, b) => mo(b) - mo(a))[0].id;
    const root = dung(null);
    nhin(-0.6);
    expect(datCoGocVuong([root], cam, 720)).toBe(1);
    expect(hienTai(root)).toEqual([tot()]);                       // the most open real mark, not the nearest corner
    // Sweep the orbit: the shown mark changes only when another is clearly (> 25 %) more open — never on a near tie.
    let dangHien = tot(), daGiu = 0, daDoi = 0;
    for (let g = -0.6; g < 5.6; g += 0.05) {
      nhin(g);
      datCoGocVuong([root], cam, 720);
      const [moi] = hienTai(root);
      const ratio = mo(ben.find((o) => o.id === tot())!) / mo(ben.find((o) => o.id === dangHien)!);
      if (moi === dangHien && tot() !== dangHien) { expect(ratio).toBeLessThanOrEqual(1.25 + 1e-6); daGiu += 1; }
      if (moi !== dangHien) { expect(moi).toBe(tot()); expect(ratio).toBeGreaterThan(1.25 - 1e-6); daDoi += 1; dangHien = moi; }
    }
    expect(daGiu).toBeGreaterThan(0);                             // hysteresis really exercised
    expect(daDoi).toBeGreaterThan(0);                             // and the mark does follow a clearly better corner
    // With the real solid, a lateral edge that is entirely hidden never carries the representative mark.
    const voi = new THREE.Group();
    voi.add(buildObject3D(sc.objects.find((o) => o.type === "solid")!, false)!);
    for (const o of ben) voi.add(buildObject3D(o, false)!);
    const canhCua = (o: (typeof ben)[number]) => (id: string) => o.depends.every((v) => id.split("::edge:")[1]?.split("-").includes(v));
    // The workspace turns a segment that coincides with a solid edge into a hit proxy (`doanNhuongCanh`), which is
    // never classified itself — found in the browser: the representative sat on hidden DD′. Both paths are checked.
    const voiProxy = new THREE.Group();
    voiProxy.add(buildObject3D(sc.objects.find((o) => o.type === "solid")!, false)!);
    for (const o of ben) voiProxy.add(buildObject3D({ ...o, display_role: "hit_proxy" }, false)!);
    for (const goc of [voi, voiProxy]) {
      let daThayAn = false;
      for (let g = -0.6; g < 5.6; g += 0.4) {
        nhin(g);
        const audit = updateCanonicalEdgeVisibility(goc, cam);
        datCoGocVuong([goc], cam, 720);
        const [hienVoi] = hienTai(goc as unknown as THREE.Group);
        const an = (o: (typeof ben)[number]) => audit.hidden_edge_ids.some(canhCua(o));
        daThayAn ||= ben.some(an);
        expect([g, hienVoi, an(ben.find((o) => o.id === hienVoi)!)]).toEqual([g, hienVoi, false]);
      }
      expect(daThayAn).toBe(true);                                // some lateral edge really was hidden on the sweep
    }
    // Looking straight down, every lateral mark lies in a vertical plane seen edge-on: its square collapses into a line.
    // Nothing is drawn by default (never a fake screen square); the emphasised edge still shows its own mark.
    cam.position.set(1.5, 2.2, 22); cam.lookAt(1.5, 2, 2.5); cam.updateMatrixWorld(true);
    expect(Math.max(...ben.map(mo))).toBeLessThan(DO_MO_TOI_THIEU);
    expect(datCoGocVuong([dung(null)], cam, 720)).toBe(0);
    const nhanTren = dung("canh_ben_B_B_prime");
    datCoGocVuong([nhanTren], cam, 720);
    expect(hienTai(nhanTren)).toEqual(["canh_ben_B_B_prime"]);
    // The edge being taught (emphasised) always shows its own mark, wherever the camera is.
    nhin(-0.6);
    const nhanA = dung("canh_ben_A_A_prime");
    datCoGocVuong([nhanA], cam, 720);
    expect(hienTai(nhanA)).toEqual(["canh_ben_A_A_prime"]);
    // A relation is never deleted, only one representative is shown: different relations keep their own marks.
    const khac = dung(null);
    const ma = khac.getObjectByName("perp_marker:canh_ben_D_D_prime")!;
    (ma.userData.gocVuongDonVi as { nhomQuanHe?: string }).nhomQuanHe = "line_perpendicular_plane|other_rule|other_plane";
    datCoGocVuong([khac], cam, 720);
    const totABC = ben.filter((o) => o.id !== "canh_ben_D_D_prime").sort((a, b) => mo(b) - mo(a))[0].id;
    expect(hienTai(khac)).toEqual([totABC, "canh_ben_D_D_prime"].sort());
  });

  it("nhân chứng vuông góc trên khối đơn vị co giãn chu kỳ nét đứt và ô góc vuông theo đường kính cảnh, không phình quá khổ", () => {
    const w = {
      id: "perpendicular:H",
      vai: "hinh_chieu" as const,
      from: [1, 1, 0] as [number, number, number],
      foot: [0, -0.2, 0.4] as [number, number, number],
      u: [0, 1, 1] as [number, number, number],
      v: [1, 1.2, -0.4] as [number, number, number],
    };
    const diem: [number, number, number][] = [
      [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
    ];
    const nhom = vatNhanChung(w, diem, 0xc2410c, false);
    const doan = nhom.children[0] as unknown as { material: { dashSize: number; gapSize: number } };
    const goc = nhom.children[1] as unknown as {
      geometry: { getAttribute(n: string): { getX(i: number): number; getY(i: number): number; getZ(i: number): number } };
    };
    expect(doan.material.dashSize).toBeLessThanOrEqual(0.08);
    expect(doan.material.dashSize).toBeGreaterThanOrEqual(0.04);
    const pos = goc.geometry.getAttribute("position");
    const canhO = Math.hypot(
      pos.getX(0) - w.foot[0],
      pos.getY(0) - w.foot[1],
      pos.getZ(0) - w.foot[2],
    );
    expect(canhO).toBeLessThanOrEqual(0.14);
    expect(canhO).toBeGreaterThanOrEqual(0.06);
  });

  it("mặt phẳng toán học (SAB) và mặt phẳng phụ dựng tấm tứ giác/hình bình hành 4 đỉnh đồng phẳng cân đối, không đầu nhọn tam giác và không tô chồng 2 lớp", () => {
    const diem: [number, number, number][] = [
      [0, 0, 0], [4, 0, 0], [4, 3, 0], [0, 3, 0], [0, 0, 4],
    ];
    const p0: [number, number, number] = [0, 0, 0];
    const n: [number, number, number] = [0, -1, 0];
    const moRong = moRongDaGiacMatPhang(p0, n, diem);
    expect(moRong).not.toBeNull();
    // Phải là tứ giác 4 đỉnh cân đối (hình chữ nhật trong 3D / hình bình hành trên hình chiếu), không phải tam giác 3 đỉnh có đầu nhọn
    expect(moRong!).toHaveLength(4);
    for (let i = 0; i < 4; i++) {
      const p = moRong![i];
      // Đồng phẳng tuyệt đối với (SAB) (y = 0) và không thò xuống dưới đáy (z >= 0)
      expect(Math.abs(p[1])).toBeLessThan(1e-6);
      expect(p[2]).toBeGreaterThanOrEqual(-1e-6);
      // Kiểm tra góc trong tại mỗi đỉnh không có góc nhọn bất thường (hai cạnh liên tiếp vuông góc trong 3D)
      const prev = moRong![(i + 3) % 4];
      const next = moRong![(i + 1) % 4];
      const ePrev = [p[0] - prev[0], p[1] - prev[1], p[2] - prev[2]];
      const eNext = [next[0] - p[0], next[1] - p[1], next[2] - p[2]];
      const dotEdges = ePrev[0] * eNext[0] + ePrev[1] * eNext[1] + ePrev[2] * eNext[2];
      expect(Math.abs(dotEdges)).toBeLessThan(1e-6);
    }
    const xSpan = Math.max(...moRong!.map((p) => p[0])) - Math.min(...moRong!.map((p) => p[0]));
    expect(xSpan).toBeGreaterThan(4.2);

    // Mặt phẳng phụ qua B(2,0,0) vuông góc với SC (normal = [2, 2, -4]) cũng phải là tấm 4 đỉnh đồng phẳng, không cánh nhọn
    const mpPhu = moRongDaGiacMatPhang([2, 0, 0], [2, 2, -4], [
      [0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0], [0, 0, 4],
    ]);
    expect(mpPhu).not.toBeNull();
    expect(mpPhu!).toHaveLength(4);
    for (const p of mpPhu!) {
      expect(Math.abs(2 * (p[0] - 2) + 2 * p[1] - 4 * p[2])).toBeLessThan(1e-6);
      expect(p[2]).toBeGreaterThanOrEqual(-1e-6);
    }

    const neo = diemNeoNhanMatPhang(p0, n, diem);
    expect(neo).not.toBeNull();
    expect(Math.abs(neo![1])).toBeLessThan(1e-6);
    for (const d of diem) {
      expect(Math.hypot(neo![0] - d[0], neo![1] - d[1], neo![2] - d[2])).toBeGreaterThan(0.25);
    }

    const sabObj = buildObject3D({
      id: "sab",
      label: "Mặt phẳng (SAB)",
      notation: "(SAB)",
      type: "plane3",
      render: "surface",
      origin: "derived",
      producer: "plane_through",
      depends: ["S", "A", "B"],
      point: ["0", "0", "0"],
      normal: ["0", "-1", "0"],
    }, false, undefined, diem) as unknown as {
      material: { opacity: number; colorWrite: boolean };
      children: { name: string; userData: Record<string, unknown>; children: { name: string }[] }[];
    };
    expect(sabObj).not.toBeNull();
    // Mesh gốc không tô chồng tam giác đậm bên trong tấm tứ giác mở rộng
    expect(sabObj.material.opacity).toBe(0);
    expect(sabObj.material.colorWrite).toBe(false);
    const sheet = sabObj.children.find((c) => c.name === "plane_sheet:sab");
    expect(sheet).toBeDefined();
    const border = sheet!.children.find((c) => c.name === "plane_border:sab");
    expect(border).toBeDefined();
    expect((sheet!.userData.nonCanonicalLoop as { isPlaneBorder?: boolean })?.isPlaneBorder).toBe(true);
  });

  it("P1 property test: moRongDaGiacMatPhang luôn đồng phẳng tuyệt đối cho mặt phẳng ngang, đứng, nghiêng, gần ngang (0.98 < |u_z| < 1), gần đứng, đổi quy mô và hoán đổi thứ tự điểm", () => {
    type Vec = [number, number, number];
    const kiemDongPhang = (origin: Vec, normal: Vec, diem: Vec[], scale = 1) => {
      const nLen = Math.hypot(normal[0], normal[1], normal[2]);
      const u: Vec = [normal[0] / nLen, normal[1] / nLen, normal[2] / nLen];
      const sheet = moRongDaGiacMatPhang(origin, normal, diem);
      expect(sheet).not.toBeNull();
      expect(sheet!.length).toBeGreaterThanOrEqual(3);
      const tol = 1e-8 * Math.max(scale, 1e-6);
      for (const v of sheet!) {
        const dot = (v[0] - origin[0]) * u[0] + (v[1] - origin[1]) * u[1] + (v[2] - origin[2]) * u[2];
        expect(Math.abs(dot)).toBeLessThanOrEqual(tol);
      }
      return sheet!;
    };

    const khungChuan: Vec[] = [[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0], [0, 0, 4]];

    // 1. Mặt phẳng ngang chính xác (z = 2 và z = 0)
    kiemDongPhang([0, 0, 2], [0, 0, 1], [...khungChuan, [0, 0, 2], [1, 0, 2], [0, 1, 2]]);
    kiemDongPhang([0, 0, 0], [0, 0, -4], khungChuan);

    // 2. Mặt phẳng đứng (u_z = 0)
    kiemDongPhang([0, 0, 0], [0, -1, 0], khungChuan);
    kiemDongPhang([0, 0, 0], [3, -4, 0], [...khungChuan, [4, 3, 2]]);

    // 3. Mặt phẳng nghiêng tổng quát
    kiemDongPhang([2, 0, 0], [2, 2, -4], khungChuan);
    kiemDongPhang([1, 1, 1], [1, -2, 3], khungChuan);

    // 4. Mặt phẳng gần ngang: 0.98 < |u_z| < 1 (không được làm phẳng thành mặt XY làm lệch đồng phẳng!)
    // Với normal = [0.15, -0.08, 1], |u_z| = 1 / sqrt(1.0289) ≈ 0.98585 > 0.98
    const nGanNgang1: Vec = [0.15, -0.08, 1];
    const diemGanNgang1: Vec[] = [
      [0, 0, 1],
      [2, 0, 1 - 0.30],
      [0, 2, 1 + 0.16],
      [0, 0, 0],
      [0, 0, 4],
    ];
    kiemDongPhang([0, 0, 1], nGanNgang1, diemGanNgang1);
    // Với normal = [0.04, 0.03, -1], |u_z| = 1 / sqrt(1.0025) ≈ 0.99875 > 0.98 (qua < 3 điểm của hình)
    kiemDongPhang([1, 1, 1.5], [0.04, 0.03, -1], khungChuan);

    // 5. Mặt phẳng gần đứng (0 < |u_z| << 1)
    kiemDongPhang([1, 0, 1], [1, -1, 0.01], khungChuan);
    kiemDongPhang([0, 0, 0], [0, -1, 0.005], [
      [0, 0, 0], [2, 0, 0], [0, 0.02, 4], [2, 2, 0], [0, 2, 0],
    ]);

    // 6. Thay đổi quy mô (scale = 1e-3, 1, 1e3) và hoán đổi thứ tự điểm xác định / đảo pháp tuyến
    for (const scale of [1e-3, 1, 1e3]) {
      const dScaled: Vec[] = khungChuan.map(([x, y, z]) => [x * scale, y * scale, z * scale]);
      kiemDongPhang([0, 0, 0], [0, -1, 0], dScaled, scale);
      kiemDongPhang([0, 0, 1 * scale], nGanNgang1, diemGanNgang1.map(([x, y, z]) => [x * scale, y * scale, z * scale]), scale);
    }

    // Hoán đổi thứ tự điểm và đổi điểm gốc trên mặt phẳng (SAB) phải cho cùng tập 4 đỉnh 3D
    const s1 = kiemDongPhang([0, 0, 0], [0, -1, 0], [[0, 0, 0], [2, 0, 0], [0, 0, 4], [2, 2, 0], [0, 2, 0]]);
    const s2 = kiemDongPhang([0, 0, 4], [0, 8, 0], [[0, 0, 4], [0, 2, 0], [2, 0, 0], [0, 0, 0], [2, 2, 0]]);
    const normSet = (pts: Vec[]) => pts.map((p) => p.map((v) => (Math.abs(v) < 1e-9 ? "0.000000" : v.toFixed(6))).join(",")).sort();
    expect(normSet(s1)).toEqual(normSet(s2));
  });

  it("solutionAt nhận diện đối tượng kết quả MEASURE kể cả khi thiếu trường type tường minh", () => {
    const s: Scene3D = {
      free_objects: ["A", "B", "S"],
      objects: [
        { id: "A", label: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] },
        { id: "sbc", label: "Mặt phẳng (SBC)", type: "plane3", render: "surface", origin: "derived", producer: "plane", depends: ["S", "B", "C"] },
        { id: "kc", label: "d(A,(SBC)) = 12/5", render: "readout", origin: "derived", producer: "distance", depends: ["ah", "sbc"], value: "12/5" } as never,
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Đầu." },
        { step_index: 1, action: "MEASURE", object: "kc", depends: ["ah", "sbc"], explanation: "Kết luận." },
      ],
    };
    expect(solutionAt(s, 0).results).toEqual([]);
    expect(solutionAt(s, 1).results.map((r) => r.id)).toEqual(["kc"]);
    expect(solutionAt(s, 1).results[0].text).toBe("Kết luận.");
  });

  it("lưới nền sư phạm 8x8 nằm dưới đáy hình, vô hiệu raycast và dịu đi khi mặt phẳng toán học nổi bật", () => {
    const diem: [number, number, number][] = [
      [0, 0, 0], [4, 0, 0], [4, 3, 0], [0, 3, 0], [0, 0, 4],
    ];
    const luoiBinhThuong = dungLuoiNenSuPham(diem, 1);
    const luoiDiu = dungLuoiNenSuPham(diem, 0.55);
    expect(luoiBinhThuong).not.toBeNull();
    expect(luoiBinhThuong!.name).toBe("luoi_nen_su_pham");
    expect(luoiBinhThuong!.children).toHaveLength(3);
    for (let i = 0; i < 3; i++) {
      const segA = luoiBinhThuong!.children[i] as unknown as {
        geometry: { getAttribute(n: string): { getZ(k: number): number } };
        material: { opacity: number };
        raycast: (...args: unknown[]) => void;
      };
      const segB = luoiDiu!.children[i] as unknown as { material: { opacity: number } };
      expect(segA.geometry.getAttribute("position").getZ(0)).toBeLessThan(0);
      expect(segB.material.opacity).toBeLessThan(segA.material.opacity);
    }
  });

  it("cauTrucGocNhin bổ sung mặt phẳng chéo chưa thuộc mặt khối vào danh sách mặt để camera tránh nhìn suy biến", () => {
    const objects = [
      { id: "A", label: "A", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] },
      { id: "C", label: "C", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["4", "3", "0"] },
      { id: "S", label: "S", type: "point3", render: "point_marker", origin: "free", producer: null, depends: [], xyz: ["0", "0", "4"] },
      {
        id: "sac", label: "(SAC)", type: "plane3", render: "surface", origin: "derived", producer: "plane_through",
        depends: ["S", "A", "C"], point: ["0", "0", "0"], normal: ["3", "-4", "0"],
      },
    ] as never;
    const t = cauTrucGocNhin(objects);
    expect(t.mat).toHaveLength(1);
    expect(t.mat[0]).toHaveLength(3);
  });
});
