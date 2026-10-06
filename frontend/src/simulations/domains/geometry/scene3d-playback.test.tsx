import { afterEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  PLAYBACK_INTERVAL_MS,
  focusAt,
  geometryStepList,
  numericalBasis,
  isFirstStep,
  isLastStep,
  nextStep,
  prefersReducedMotion,
  prevStep,
  quantityChoices,
  type Scene3D,
} from "./scene3d-model";
import { Scene3DPlayer } from "./scene3d-playback";
import { quantitySources } from "./scene3d-annotations";
import { directDependencies } from "./interaction-state";

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

  it("bước cuối ⇒ nút Phát thành Xem lại, bấm được (w10)", () => {
    // Trước w10 nút Phát bị vô hiệu ở bước cuối: không có đường nào để học
    // sinh xem lại quá trình ngoài việc kéo thanh bước về đầu.
    const html = renderToString(<Scene3DPlayer scene={scene()} initialStep={1} />);
    const nut = /<button[^>]*aria-label="Xem lại quá trình dựng"[^>]*>/.exec(html)?.[0];
    expect(nut, "thiếu nút Xem lại ở bước cuối").toBeTruthy();
    expect(nut).not.toContain("disabled");
    expect(html).not.toContain("aria-label=\"Phát lại quá trình dựng\"");
  });

  it("bước đầu ⇒ nút lùi bị vô hiệu", () => {
    const html = renderToString(<Scene3DPlayer scene={scene()} />);
    expect(html).toMatch(/Bước trước[\s\S]{0,80}/);
    expect(html).toContain("disabled");
  });

  /* regular-square-pyramid-w01 · ROADMAP §0.1-8: dải «Đang dựng / Dựa trên» dưới khung đã GỠ — nó lặp dòng
   * thuyết minh và ô soi. Tên bước nay ở panel «Các bước dựng» (§0.1-3), phụ thuộc số ở «Dựa trên» của lời giải
   * đầy đủ và ô soi. Các test dưới giữ NỘI DUNG cũ (tên chứ không id IR; bước nhóm không tự nhận là dữ kiện; INIT
   * nói đúng là dữ kiện; nguồn số của thể tích không kèm khối) trên hai bề mặt mới ấy. */
  it("§0.1-8 · không còn dải «Đang dựng / Dựa trên» dưới thanh bước", () => {
    const html = renderToString(<Scene3DPlayer scene={scene()} initialStep={1} />);
    expect(html).not.toContain("Đang dựng");
    expect(html).not.toContain("geo3d-focus");
  });

  it("bước 0 nói rõ đây là dữ kiện đề cho, không phải chỗ trống", () => {
    const html = renderToString(<Scene3DPlayer scene={scene()} />);
    expect(html).toContain("dữ kiện đề cho");
  });

  /* ── (G1) DẢI TIÊU ĐIỂM TRA NGƯỢC SANG SIÊU DỮ LIỆU ───────────────────
   *
   * `focusAt` trả **id** — đúng, vì trace nói bằng id. Nhưng dải này là bề mặt
   * học sinh, và in id thẳng ra là cách `Đang dựng the_tich_sabcd` /
   * `Dựa trên S_ABCD` lên tới màn hình
   * (`GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT §4`).
   *
   * Cảnh dưới đây dựng đúng hình dạng ấy: id là tên biến IR, còn tên đọc được
   * và ký hiệu nằm ở `label`/`notation` do backend phát. */
  const canhCoTenXau = (): Scene3D => ({
    free_objects: ["S_ABCD"],
    objects: [
      { id: "S_ABCD", label: "Hình chóp S.ABCD", notation: "S.ABCD",
        type: "solid", render: "mesh", origin: "free", producer: null,
        depends: [], vertices: [], faces: [] },
      { id: "the_tich_sabcd", label: "Thể tích S.ABCD", notation: "V(S.ABCD)",
        type: "quantity", render: "readout", origin: "derived",
        producer: "measure.volume", depends: ["S_ABCD"],
        value: "8/3", exact: { kind: "rational", value: "8/3" } },
    ],
    events: [
      { step_index: 0, action: "INIT", object: null, depends: [],
        explanation: "Dữ kiện đề cho." },
      { step_index: 1, action: "MEASURE", object: "the_tich_sabcd",
        depends: ["S_ABCD"], explanation: "Đo thể tích." },
    ],
  });

  it("trình phát (cả panel các bước đang mở) không in tên biến IR", () => {
    const html = renderToString(
      <Scene3DPlayer scene={canhCoTenXau()} initialStep={1} stepsOpen />);
    expect(html).not.toContain("the_tich_sabcd");
    expect(html).not.toContain("S_ABCD");
  });

  it("nguồn số của một đại lượng (ô soi «Tính trực tiếp từ») tra id sang KÝ HIỆU, không in id IR (payload thật)", () => {
    // W05: thẻ lời giải (nơi dòng «Dựa trên:» từng sống) đã gỡ; nguồn số đọc ở ô soi khi chọn đại lượng, cùng
    // `quantitySources` và cùng cách gọi ngắn `reference`/`display_label` như ô soi (`ten` của xưởng).
    const that: Scene3D = JSON.parse(readFileSync(join(__dirname,
      "../../../../../docs/evaluation/geometry/runs/w11-pedagogical-polish/inputs/fixtures/rectangular_pyramid_positive.json"),
      "utf8")).envelope.scene3d;
    const theoId = new Map(that.objects.map((o) => [o.id, o]));
    const ten = (id: string) => {
      const o = theoId.get(id);
      return o?.reference?.trim() || o?.display_label?.trim() || o?.label?.trim() || "";
    };
    const q = quantityChoices(that, that.events.length - 1);
    const ds = [...q.results, ...q.steps].flatMap((id) => quantitySources(that, id).inputs.map(ten));
    expect(ds.length).toBeGreaterThan(0);
    for (const d of ds) expect(d).not.toMatch(/_/);
  });

  /* W17 · nhãn nhóm cạnh: một câu lệnh NHÓM (`construct_segment` có `items`) có biến
   * đích KHÔNG phải vật của cảnh. Bản W16 rơi về "— (dữ kiện đề cho)" cho mọi tên rỗng,
   * nên bước "Dựng các cạnh bên AD, BE, CF" tự nhận là dữ kiện đề cho. Tên hành động lấy
   * từ `display_label` do backend phát; câu "dữ kiện đề cho" chỉ thuộc bước INIT.
   * Như payload thật (lăng trụ), sự kiện nhóm đưa các đoạn con lên khung (`objects`) — không có
   * chúng, bước nhóm không đổi hình và dòng thời gian gộp nó vào INIT (Task 4 ruling). */
  const canhNhom = (): Scene3D => ({
    free_objects: ["A", "D"],
    objects: [
      { id: "A", label: "Điểm A", notation: "A", type: "point3", render: "point_marker",
        origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] },
      { id: "D", label: "Điểm D", notation: "D", type: "point3", render: "point_marker",
        origin: "free", producer: null, depends: [], xyz: ["0", "0", "5"] },
      { id: "AD", label: "Cạnh AD", notation: "AD", type: "segment3", render: "segment",
        origin: "derived", producer: "construct_segment", depends: ["A", "D"],
        point_a: ["0", "0", "0"], point_b: ["0", "0", "5"] },
    ],
    events: [
      { step_index: 0, action: "INIT", object: null, depends: [],
        explanation: "Dữ kiện đề cho: AD = 5.", semantic_kind: "EXPLANATION" },
      { step_index: 1, action: "CREATE", object: "canh_ben", objects: ["AD"], depends: ["A", "D"],
        explanation: "Dựng các cạnh bên AD.", display_label: "Các cạnh bên AD",
        semantic_kind: "GEOMETRY_CONSTRUCTION" },
    ],
  });

  it("W17 · bước dựng NHÓM cạnh nói tên hành động, không tự nhận là dữ kiện đề cho", () => {
    const ds = geometryStepList(canhNhom());
    expect(ds.at(-1)?.label).toBe("Các cạnh bên AD");
    expect(ds.at(-1)?.label.toLowerCase()).not.toContain("dữ kiện đề cho");
    const html = renderToString(<Scene3DPlayer scene={canhNhom()} initialStep={1} stepsOpen />);
    expect(html).toContain("Các cạnh bên AD");
  });

  it("W17 · bước INIT vẫn nói đúng là dữ kiện đề cho", () => {
    expect(geometryStepList(canhNhom())[0].label.toLowerCase()).toContain("dữ kiện đề cho");
  });

  /* w11 (review W10-H3): bước đo thể tích "Dựa trên" ĐÚNG các đại lượng số
   * trực tiếp — diện tích đáy và chiều cao, theo thứ tự chữ công thức — không
   * phải khối (ngữ cảnh cấu trúc). Bước không có nguồn số giữ phụ thuộc hình. */
  const canhTheTich = (): Scene3D => ({
    free_objects: ["khoi", "SA_length"],
    objects: [
      { id: "khoi", label: "Hình chóp S.ABC", notation: "S.ABC", reference: "S.ABC",
        type: "solid", render: "mesh", origin: "derived", producer: null,
        depends: [], vertices: [], faces: [] },
      { id: "SA_length", label: "SA", notation: "SA", reference: "SA", type: "quantity",
        render: "readout", origin: "free", producer: null, depends: [], value: "5" },
      { id: "dt", label: "Diện tích ABC", notation: "S(ABC)", reference: "S(ABC)",
        type: "quantity", render: "readout", origin: "derived", producer: "measure.area",
        depends: ["khoi"], value: "6" },
      { id: "tt", label: "Thể tích S.ABC", notation: "V(S.ABC)", reference: "V(S.ABC)",
        type: "quantity", render: "readout", origin: "derived", producer: "measure.volume",
        depends: ["SA_length", "dt", "khoi"], value: "10",
        dependency_edges: [
          { source_id: "SA_length", relation: "numerical" },
          { source_id: "dt", relation: "numerical" },
          { source_id: "khoi", relation: "structural" }],
        formula: { text: "V = 1/3 × S(ABC) × SA = 10", references: [
          { entity_id: "dt", display_label: "S(ABC)", relation: "numerical" },
          { entity_id: "SA_length", display_label: "SA", relation: "numerical" }] } },
    ],
    events: [
      { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
      { step_index: 1, action: "MEASURE", object: "dt", depends: ["khoi"], explanation: "" },
      { step_index: 2, action: "MEASURE", object: "tt",
        depends: ["khoi", "dt", "SA_length"], explanation: "" },
    ],
  });
  it("nguồn số của bước thể tích là S(ABC), SA — không kèm khối", () => {
    const s = canhTheTich();
    expect(numericalBasis(s, s.objects.find((o) => o.id === "tt"))).toEqual(["dt", "SA_length"]);
  });

  it("bước không có nguồn số vẫn còn phụ thuộc hình học (ô soi «Dựa trên» đọc nó)", () => {
    const s = canhTheTich();
    expect(numericalBasis(s, s.objects.find((o) => o.id === "dt"))).toEqual([]);
    expect(directDependencies(s, "dt")).toEqual(["khoi"]);
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
    //
    // THÊM `./interaction-state` (2026-08-29), và đây là quyết định được nói
    // ra: trình phát nay nhận CHẾ ĐỘ ĐIỀU KHIỂN NGOÀI để `current_step` sống
    // cùng một chỗ với `selected_id`. Hai bản `step` là chỗ cây phân rã và
    // khung nhìn sẽ chỉ về hai bước khác nhau. Nhập ấy chỉ là một `type` —
    // test dưới vẫn khoá "đúng hai `useState`" và "không đọc trường hình học".
    //
    // THÊM `./scene3d-solution` (W12), cũng nói ra: bảng lời giải nằm NGAY
    // DƯỚI thanh bước và đồng bộ với bước dựng đang xem, nên trình phát là chỗ
    // đặt nó. Bảng tự giữ trạng thái gập của nó — hai `useState` ở đây không đổi.
    //
    // THÊM `./scene3d-annotations` (W17), nói ra: CHỈ một `type` — công tắc Số
    // đo/Kết quả do xưởng giữ, trình phát chuyển tiếp nguyên xuống khung nhìn.
    //
    // THÊM `./scene3d-floating-panel` (regular-square-pyramid-w02 · B), nói ra: bảng «Các bước dựng» nổi trên
    // khung thay cột lưới W1. Nó chỉ là khung trình bày (kéo, kẹp, đóng) quanh danh sách bước; nó không đọc cảnh.
    // THÊM `./scene3d-auxiliary` (W2 · D), nói ra: chỉ để NHÓM các bước dựng hình phụ (AC, BD) với bước dùng
    // chúng (O) trong danh sách — mỗi bước con vẫn là một nút đặt đúng neo, không đổi timeline.
    // BỎ `./scene3d-solution` (regular-square-pyramid-w05 · E): thẻ lời giải dưới thanh bước đã gỡ.
    const imports = [...src.matchAll(/from ["']([^"']+)["']/g)].map((m) => m[1]);
    expect(imports.sort()).toEqual([
      "../../../components/icons", "./interaction-state", "./scene3d-annotations",
      "./scene3d-auxiliary", "./scene3d-floating-panel", "./scene3d-model", "./scene3d-view", "react",
    ]);
  });

  it("chỉ có ĐÚNG ba `useState`: bước, trạng thái phát, panel các bước mở/đóng", () => {
    // Thêm state là dấu hiệu playback bắt đầu sở hữu một thứ khác ngoài thời gian — và đó là lúc nó trượt
    // thành công cụ dựng hình. Cái thứ ba (regular-square-pyramid-w01, §0.1-3) là sở thích TRÌNH BÀY: panel
    // «Các bước dựng» mở hay đóng, dự phòng khi xưởng không giữ; nó không chạm hình hay bước. Cái thứ tư của W2 · B
    // (chỗ người học kéo bảng nổi tới) chuyển sang host bảng nổi chung của xưởng ở W4 — trình phát không giữ nó nữa.
    expect((src.match(/useState/g) ?? []).length).toBe(4); // 1 import + 3 dùng
    expect(src).toMatch(/const \[moBuocTrong, setMoBuocTrong\] = useState\(false\)/);
    expect(src).not.toMatch(/viTriBuoc/);
  });

  it("`scene` đi vào và đi ra NGUYÊN VẸN cùng tham chiếu", () => {
    const s = scene();
    const truoc = JSON.stringify(s);
    renderToString(<Scene3DPlayer scene={s} initialStep={1} />);
    expect(JSON.stringify(s)).toBe(truoc);
  });
});
