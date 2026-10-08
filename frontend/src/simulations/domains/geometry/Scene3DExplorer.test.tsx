/**
 * KHỐI THĂM DÒ — cây, ô soi, chọn hai chiều. **0 mạng, 0 LLM, 0 WebGL.**
 *
 * ─── VÌ SAO KHÔNG DÙNG `fireEvent` ──────────────────────────────────────
 *
 * Kho này **không có** `@testing-library/react`, không có jsdom: mọi test
 * component đi qua `renderToString`. §11 của chỉ thị nói thẳng — đừng cài cả
 * một bộ hạ tầng test chỉ để tick vài ca. Nên phần "quyết định" được TÁCH RA
 * thành hàm thuần (`semanticTree`, `entitiesPresentAt`, `select`, `isolate`,
 * `visualTransformOf`) và kiểm thẳng ở đó, còn ở đây kiểm CẤU TRÚC đã dựng
 * ra và các ràng buộc đọc được từ mã nguồn.
 *
 * Phần duy nhất không kiểm tự động được: bấm chuột thật vào một mặt trong
 * khung 3D (cần WebGL + raycast). Nó khai là MANUAL_UI_DEMO, không tính là
 * test tự động.
 */
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Scene3D } from "./scene3d-model";
import { geometryStepCount, objectsAt, quantityChoices } from "./scene3d-model";
import { Scene3DExplorer } from "./Scene3DExplorer";
import { Scene3DPlayer } from "./scene3d-playback";
import { hasHiddenByDefault, quantitySources } from "./scene3d-annotations";
import {
  entitiesPresentAt,
  faceId,
  withSubEntities,
} from "./scene3d-subentities";
import {
  hide,
  isolate,
  reset,
  select,
  selectableIds,
  semanticTree,
  taoTrangThai,
} from "./interaction-state";

const CANH: Scene3D = {
  objects: [
    { id: "A", label: "A", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["0", "0", "0"], parent: "chop",
      display_group: ["given"], source: { assumption: "chọn A làm gốc" } },
    { id: "B", label: "B", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["1", "0", "0"], parent: "chop",
      display_group: ["given"], source: { fact_id: "ab_length" } },
    { id: "C", label: "C", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["0", "1", "0"], parent: "chop",
      display_group: ["given"], source: {} },
    { id: "S", label: "S", type: "point3", render: "point_marker", origin: "free",
      producer: null, depends: [], xyz: ["0", "0", "1"], parent: "chop",
      display_group: ["given"], source: {} },
    { id: "chop", label: "S.ABC", type: "solid", render: "mesh", origin: "derived",
      producer: "construct_solid", depends: ["A", "B", "C", "S"],
      vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
      vertex_ids: ["A", "B", "C", "S"],
      faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]],
      parent: null, display_group: ["solid"], source: {} },
    { id: "V", label: "V", type: "quantity", render: "readout", origin: "derived",
      producer: "measure.volume", depends: ["chop"], value: "1/6",
      parent: null, display_group: ["measurement"], source: {} },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Đặt hệ trục." },
    { step_index: 1, action: "CREATE", object: "chop", depends: ["A", "B", "C", "S"], explanation: "Dựng khối." },
    { step_index: 2, action: "MEASURE", object: "V", depends: ["chop"], explanation: "Đo thể tích." },
  ],
  free_objects: ["A", "B", "C", "S"],
};

const html = () => renderToString(<Scene3DExplorer scene={CANH} />);
const day = () => withSubEntities(CANH);

// ══ CÂY PHÂN RÃ — nay là NGĂN KÉO GỌI THEO NHU CẦU ════════════════════
//
// Bản trước đòi cây có mặt trong HTML ngay từ đầu. Wave xưởng đổi điều đó có
// chủ đích: cây là bảng gọi ra khi cần, nên mặc định nó KHÔNG dựng — đó là
// cách khung 3D lấy lại phần màn hình mà một sidebar luôn mở đang chiếm.
//
// Nội dung cây vẫn phải đúng, nên phép kiểm chuyển sang `semanticTree` —
// hàm THUẦN mà chính component gọi. Kiểm ở đó là kiểm cùng một sự thật, chỉ
// không phải qua một cú bấm mà `renderToString` không làm được.
describe("cây phân rã: dữ liệu đủ, nhưng gọi ra mới hiện", () => {
  const cay = () => semanticTree(day());

  it("mặc định KHÔNG dựng cây — canvas không bị bảng chiếm chỗ", () => {
    const h = html();
    expect(h).not.toContain("geo3d-tree-item");
    expect(h).not.toContain("geo3d-ngan");
    // …nhưng lối vào thì phải nhìn thấy được. W05: «Thành phần» nằm trong menu «Khám phá» của hàng trên.
    expect(h).toMatch(/data-mo-nhom="kham-pha"[^>]*>Khám phá/);
  });

  /* W17 · §15.4 / U-W17-1: hai công tắc nằm trong THANH CHIP có sẵn (không thêm nút nổi
   * che hình), là nút bật/tắt thật (`aria-pressed`), và BẬT mặc định. Cảnh của test mang nhãn
   * của cả hai loại — DESIGN_BRIEF §3.2: không có gì để bật thì công tắc VẮNG MẶT (Task 6). */
  const CANH_CO_SO_DO: Scene3D = {
    ...CANH,
    objects: [
      ...CANH.objects.map((o) => (o.id === "V" ? { ...o, annotation: {
        kind: "volume" as const, category: "result" as const, subject_ids: ["chop"], anchor: "solid" as const } } : o)),
      { id: "AB_length", label: "AB", notation: "AB", type: "quantity", render: "readout", origin: "free",
        producer: null, depends: [], value: "1", parent: null, display_group: ["given", "measurement"],
        source: {}, annotation: { kind: "length", category: "measurement", subject_ids: ["A", "B"],
          anchor: "segment" } },
    ],
  };

  /* W18 · §16.5 (thay U-W17-1): MỘT công tắc «Hiện tất cả», TẮT mặc định — mặc định hình chỉ mang
   * tên điểm và dữ kiện đề cho; đáp số và trung gian hiện khi chọn. Công tắc chỉ có mặt khi có nhãn
   * mà mặc định đang ẩn (DESIGN_BRIEF §3.2). */
  const thanhCua = (h: string) => h.slice(h.indexOf("geo3d-thanh-nut"), h.indexOf("geo3d-san"));

  /* W05: công tắc nay là mục `menuitemcheckbox` của menu «Hiển thị» (đóng khi SSR — thao tác thật ở đầu dò trình
     duyệt W05). Luật giữ nguyên và khoá ở hai chỗ kiểm được: điều kiện có mặt là `hasHiddenByDefault` (hàm thuần),
     mục chỉ được dựng dưới điều kiện ấy và mang trạng thái `xem.showAll` (mặc định tắt). */
  const ma = () => readFileSync(join(__dirname, "Scene3DExplorer.tsx"), "utf8");

  it("một công tắc «Hiện tất cả», tắt mặc định; không còn Số đo/Kết quả", () => {
    expect(hasHiddenByDefault(withSubEntities(CANH_CO_SO_DO))).toBe(true);
    expect(ma()).toMatch(/\.\.\.\(coAn \? \[\{ nhan: "Hiện tất cả số đo", chon: xem\.showAll/);
    expect(ma()).toContain("useState<AnnotationView>(DEFAULT_ANNOTATION_VIEW)");
    const thanh = thanhCua(renderToString(<Scene3DExplorer scene={CANH_CO_SO_DO} />));
    expect(thanh).toMatch(/data-mo-nhom="hien-thi"[^>]*>Hiển thị/);
    expect(thanh).not.toContain("Số đo");
    expect(thanh).not.toContain("Kết quả");
  });

  it("chỉ có dữ kiện (mặc định đã hiện hết) hoặc không có nhãn ⇒ không có công tắc", () => {
    const chiDuKien: Scene3D = { ...CANH_CO_SO_DO,
      objects: CANH_CO_SO_DO.objects.map((o) => (o.id === "V" ? { ...o, annotation: undefined } : o)) };
    expect(hasHiddenByDefault(withSubEntities(chiDuKien))).toBe(false);
    expect(hasHiddenByDefault(day())).toBe(false);
  });

  it("cây có đủ hạng mục Điểm, Cạnh, Mặt", () => {
    const nhan = new Set<string>();
    const di = (ns: ReturnType<typeof semanticTree>) => {
      for (const n of ns) { nhan.add(n.label); di(n.children); }
    };
    di(cay());
    for (const t of ["Điểm", "Cạnh", "Mặt"]) expect(nhan.has(t)).toBe(true);
  });

  it("bốn mặt và sáu cạnh là thực thể RIÊNG, chọn được từng cái", () => {
    const ids = selectableIds(cay());
    // 4 điểm + 1 khối + 1 đại lượng + 4 mặt + 6 cạnh = 16
    expect(ids).toHaveLength(16);
    expect(new Set(ids).size).toBe(16);
  });

  it("KHÔNG dựng hạng mục rỗng", () => {
    const nhan: string[] = [];
    const di = (ns: ReturnType<typeof semanticTree>) => {
      for (const n of ns) { nhan.push(n.label); di(n.children); }
    };
    di(cay());
    expect(nhan).not.toContain("Thiết diện");
  });

  it("cây và cảnh dày khớp nhau: mọi thực thể có đúng một nút", () => {
    const ids = day().objects.map((o) => o.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(selectableIds(cay()).sort()).toEqual([...ids].sort());
  });
});

// ══ MỘT THẨM QUYỀN CHỌN ══════════════════════════════════════════════
describe("một thẩm quyền chọn", () => {
  it("component KHÔNG giữ selection thứ hai", () => {
    const src = readFileSync(join(__dirname, "Scene3DExplorer.tsx"), "utf8");
    // Đúng MỘT `useState`, và nó giữ `InteractionState`. Thêm
    // `treeSelected`/`viewportSelected` là mời hai bản lệch nhau.
    // Đúng MỘT `useState<InteractionState>`. Xưởng nay còn hai `useState`
    // khác — ngăn kéo nào đang mở, và bật/tắt chế độ Chi tiết — nhưng chúng
    // giữ CÁCH BÀY, không giữ *đang chọn cái gì*. Ràng buộc là một thẩm quyền
    // CHỌN, không phải một `useState` duy nhất; đếm `useState` là đếm nhầm thứ.
    expect((src.match(/useState<InteractionState>/g) ?? []).length).toBe(1);
    expect((src.match(/selected_id:/g) ?? []).length).toBe(0);
    // BỎ CHÚ THÍCH trước khi soi tên cấm — docstring của chính file ấy NHẮC
    // `treeSelected`/`viewportSelected` để nói *đừng làm thế*, và một phép so
    // chuỗi thô sẽ bắt đúng lời cảnh báo. Kho này đã vấp lớp lỗi ấy một lần
    // với chữ `three` trong văn xuôi.
    const ma = src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    for (const cam of ["treeSelected", "viewportSelected", "setSelected"]) {
      expect(ma, `giữ selection thứ hai: ${cam}`).not.toContain(cam);
    }
    // Phép bỏ chú thích phải THẬT SỰ bỏ được — nếu không, test trên xanh vì
    // một lý do sai.
    expect(ma).not.toContain("mời hai bản lệch nhau");
  });

  it("cả cây lẫn khung nhìn đều báo về CÙNG một hàm `chon`", () => {
    const src = readFileSync(join(__dirname, "Scene3DExplorer.tsx"), "utf8");
    expect(src).toContain("onSelect={chon}");
    expect(src).toContain("onChon={chon}");
  });

  it("chọn là phép THUẦN — đổi id thì id cũ thôi được chọn", () => {
    const a = select(taoTrangThai(), "A");
    const b = select(a, faceId("chop", 1));
    expect(a.selected_id).toBe("A");
    expect(b.selected_id).toBe("chop::face:1");
  });
});

// ══ PHÁT LẠI — mặt có mặt cùng lúc với khối cha ══════════════════════
describe("bước dựng quyết định cái gì bấm được", () => {
  it("bước 0: khối và mặt của nó CHƯA có", () => {
    const co = entitiesPresentAt(day(), 0, objectsAt);
    expect(co.has("A")).toBe(true);
    expect(co.has("chop")).toBe(false);
    expect(co.has(faceId("chop", 0))).toBe(false);
  });

  it("bước 1: khối và MỌI mặt/cạnh của nó cùng có", () => {
    const co = entitiesPresentAt(day(), 1, objectsAt);
    expect(co.has("chop")).toBe(true);
    for (let i = 0; i < 4; i++) expect(co.has(faceId("chop", i))).toBe(true);
  });

  it("KHÔNG có timeline thứ hai: mặt không tự sinh sự kiện", () => {
    const ev = day().events;
    expect(ev).toHaveLength(CANH.events.length);
    expect(ev.some((e) => e.object?.includes("::"))).toBe(false);
  });
});

// ══ Ô SOI — đủ trả lời "vật này ở đâu ra" ════════════════════════════
describe("ô soi", () => {
  it("mặt biết cha và các đỉnh của nó", () => {
    const m = day().objects.find((o) => o.id === faceId("chop", 1))!;
    expect(m.parent).toBe("chop");
    expect(m.depends).toEqual(["A", "B", "S"]);
    expect(m.producer).toContain("face[1]");
  });

  it("điểm giữ được dữ kiện và giả thiết của đề", () => {
    const b = day().objects.find((o) => o.id === "B")!;
    expect(b.source!.fact_id).toBe("ab_length");
    const a = day().objects.find((o) => o.id === "A")!;
    expect(a.source!.assumption).toContain("gốc");
  });

  it("bề mặt học sinh KHÔNG lộ định danh kỹ thuật của hệ", () => {
    const h = html();
    for (const cam of ["simulation_id", "source_fact_id", "display_group",
                       "InteractionState", "visual_transform"]) {
      expect(h, `UI lộ ${cam}`).not.toContain(cam);
    }
  });
});

// ══ THAO TÁC XEM KHÔNG ĐỔI DỮ LIỆU ═══════════════════════════════════
describe("thao tác xem là phép thuần trên trạng thái nhìn", () => {
  it("cô lập rồi về mặc định ⇒ đúng trạng thái đầu", () => {
    let s = select(taoTrangThai(), faceId("chop", 1));
    s = isolate(s, [faceId("chop", 1), "A", "B", "S"]);
    s = hide(s, "C");
    expect(reset()).toEqual(taoTrangThai());
  });

  it("dựng cây hai lần cho cùng kết quả (tất định)", () => {
    expect(semanticTree(day())).toEqual(semanticTree(day()));
  });

  it("render KHÔNG chạm cảnh gốc", () => {
    const truoc = JSON.parse(JSON.stringify(CANH)) as Scene3D;
    html();
    expect(CANH).toEqual(truoc);
  });
});

// ══ KHÔNG GỌI MẠNG / LLM ═════════════════════════════════════════════
describe("tương tác không gọi gì ra ngoài", () => {
  it("không `fetch`, không `axios`, không client nào", () => {
    for (const f of ["Scene3DExplorer.tsx", "interaction-state.ts",
                     "scene3d-subentities.ts"]) {
      const src = readFileSync(join(__dirname, f), "utf8");
      for (const cam of ["fetch(", "axios", "XMLHttpRequest", "/api/"]) {
        expect(src, `${f} gọi ${cam}`).not.toContain(cam);
      }
    }
  });
});


// ══ §16 · HỢP ĐỒNG CỦA XƯỞNG ══════════════════════════════════════════════
describe("§16 · xưởng: canvas là màn hình, chữ gọi ra khi cần", () => {
  const src = readFileSync(join(__dirname, "Scene3DExplorer.tsx"), "utf8");
  const ma = src
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");

  it("MẶC ĐỊNH gần như không có chữ: không tiêu đề, không đoạn dẫn", () => {
    const h = html();
    expect(h).not.toContain("<h3");
    expect(h).not.toContain("<p class=\"geo3d-lead\"");
    // Ba thứ duy nhất được phép có chữ ở màn mặc định: thanh trên, nút nổi,
    // dòng bước ở đáy. Không có bảng nào mở sẵn.
    expect(h).not.toContain("geo3d-ngan");
    expect(h).not.toContain("geo3d-soi");
  });

  it("KHÔNG phơi metadata kỹ thuật ở màn mặc định", () => {
    const h = html();
    for (const cam of ["point3", "producer", "depends", "source_fact_id",
                       "origin", "construct_point", "measure."]) {
      expect(h, `màn mặc định lộ ${cam}`).not.toContain(cam);
    }
  });

  it("canvas TỒN TẠI, và ngăn kéo KHÔNG bóp nó lại", () => {
    expect(html()).toContain("geo3d-canvas");
    // Ngăn kéo và ô soi neo tuyệt đối vào sân khấu ⇒ phủ LÊN khung, không
    // chen cạnh nó. Một bảng chen cạnh là một sidebar, và sidebar là thứ
    // wave này gỡ đi. W4: cả hai là `BangNoi` — khung tuyệt đối chung `.geo3d-bang-noi`.
    const css = readFileSync(join(__dirname, "../../../styles/global.css"), "utf8");
    const i = css.indexOf("\n.geo3d-bang-noi {");
    expect(i).toBeGreaterThan(-1);
    expect(css.slice(i, i + 220)).toContain("position: absolute");
    for (const lop of ['className="geo3d-ngan"', 'className="geo3d-soi"']) {
      expect(src).toMatch(new RegExp(`<BangNoi[^>]*${lop}`));
    }
  });

  it("ngăn kéo KHÔNG giữ một bản chọn riêng", () => {
    // `ngan` chỉ giữ *bảng nào đang mở*. Nếu nó giữ thêm một id được chọn thì
    // cây và khung nhìn sẽ chỉ về hai vật khác nhau.
    // regular-square-pyramid-w01 §0.1-2: thêm ngăn «Đại lượng» — vẫn chỉ là TÊN ngăn đang mở.
    // W4: nhiều bảng cùng mở ⇒ một TẬP tên bảng; vẫn không giữ id nào được chọn.
    expect(ma).toContain('type BangThongTin = "de" | "thanh-phan" | "dai-luong"');
    expect(ma).toContain("useState<ReadonlySet<BangThongTin>>");
    for (const x of ["nganSelected", "treeSelected", "viewportSelected"]) {
      expect(ma, `ngăn kéo giữ chọn riêng: ${x}`).not.toContain(x);
    }
  });

  it("ô soi là NGỮ CẢNH: không chọn gì thì không có nút thao tác nào", () => {
    const h = html();
    for (const nut of ["Chỉ xem phần này", "Xem cấu tạo", "Ẩn"]) {
      expect(h, `nút ${nut} hiện khi chưa chọn gì`).not.toContain(nut);
    }
    // …nhưng thao tác TOÀN CẢNH thì luôn có, vì chúng luôn áp dụng được.
    expect(h).toContain("Tách khối");
    expect(h).toContain("Xem lại toàn hình");
  });

  it("phát lại dùng ĐÚNG `current_step` cũ, không đẻ dòng thời gian thứ hai", () => {
    expect(ma).toContain("tt.current_step");
    expect(ma).toContain("interaction={tt}");
    // Không có state bước riêng trong xưởng.
    expect(ma).not.toMatch(/useState[^\n]*[Ss]tep/);
  });

  it("chế độ Chi tiết KHÔNG làm mất dữ liệu — chỉ đổi ai được mời đọc", () => {
    // Cùng một `scene` đi vào; `chiTiet` chỉ gác phần HIỂN THỊ.
    expect(ma).toContain("{chiTiet &&");
    expect(ma).toContain("directDependencies(day, dangChon.id).map(ten)");
    // Chi tiết là bề mặt người dùng: không được in stable ID, enum kiểu hay
    // primitive nội bộ. Dữ liệu vẫn tồn tại nguyên vẹn trong model bên dưới.
    for (const raw of ["dangChon.type", "dangChon.producer", "source.fact_id",
                       "nut.type"]) {
      expect(ma).not.toContain(raw);
    }
    // Dữ liệu vẫn nguyên trong model dù chế độ nào.
    const o = day().objects.find((x) => x.id === "chop")!;
    expect(o.producer).toBe("construct_solid");
    expect(o.depends).toEqual(["A", "B", "C", "S"]);
  });

  it("thuật ngữ của HỌC SINH đến từ BACKEND, không từ một bảng ở đây", () => {
    /* Ca này trước đây gọi `_moTaNgan` và `_VAI_TRO` — hai bảng dịch
     * `producer`/`type` sang tiếng Việt **ở frontend**, tức một thẩm quyền đặt
     * tên thứ hai. Cả hai đã gỡ ở wave `DISPLAY_NAME_AUTHORITY_LEFTOVER`.
     *
     * Nay ca khoá đúng bất biến còn lại: dòng vai trò đọc thẳng `role` của
     * backend, và không có bảng nào ở đây dịch định danh máy sang tiếng người
     * học. Guard tổng quát nằm ở `semantic-dumb-frontend.test.ts`. */
    const src = readFileSync(
      new URL("./Scene3DExplorer.tsx", import.meta.url), "utf8");
    expect(src).toMatch(/dangChon\.role/);
    const ma = src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
    expect(ma).not.toContain("construct_point.");
    expect(ma).not.toContain("measure.volume");
  });
});

/* ── TÍCH HỢP · ĐỔI BÀI PHẢI TRẢ TRẠNG THÁI VỀ ĐẦU ───────────────────────
 *
 * Lỗi đo được trong trình duyệt trước khi có bản vá: mở một bài 12 bước, tua
 * tới bước 10, chọn một vật, tách khối, rồi mở một bài 6 bước thì màn hình
 * hiện **"Bước 10/6"** — một bước không tồn tại — ô soi vẫn mở trên một vật
 * mang cùng tên nhưng là vật KHÁC, và hình mở ra đã ở trạng thái tách sẵn.
 *
 * Nguyên nhân: `SimulationWorkspace` dựng `Scene3DExplorer` ở cùng vị trí cho
 * mọi bài nên React DÙNG LẠI component, và `InteractionState` không tự mất.
 *
 * Hai ca dưới soi MÃ NGUỒN vì cả hai chỗ sửa đều nằm ngoài đường SSR: hiệu
 * ứng reset chỉ chạy khi `scene` đổi, còn dòng chữ bước chỉ sai khi bước vượt
 * quá số bước — không trạng thái đầu nào chạm tới (bài học §8 anti-pattern
 * #11 của bản đồ kiến trúc). Bằng chứng hành vi là lượt kiểm trình duyệt.
 */
describe("tích hợp · trạng thái không được rớt sang bài mới", () => {
  const src = readFileSync(
    new URL("./Scene3DExplorer.tsx", import.meta.url), "utf8");

  it("có hiệu ứng trả trạng thái gắn với cảnh về đầu khi `scene` đổi", () => {
    // W4: các bảng thông tin đang mở (một TẬP, không còn một ngăn) gắn với cảnh ⇒ về rỗng khi đổi bài.
    // W4 · yêu cầu 5: nhóm đang mở của cây «Thành phần» cũng gắn với bài.
    expect(src).toMatch(
      /useEffect\(\(\) => \{\s*setTt\(taoTrangThai\(\)\);\s*setMoBang\(new Set\(\)\);\s*setMoNhom\(new Set\(\)\);\s*\}, \[scene\]\)/);
  });

  it("KHÔNG reset thứ thuộc về sở thích người dùng", () => {
    // `chiTiet` là mức chi tiết muốn đọc — không gắn với bài nào. Reset nó mỗi
    // lần đổi bài là bắt người dùng bật lại sau từng bài.
    const hieuUng = src.slice(src.indexOf("setTt(taoTrangThai())"));
    const than = hieuUng.slice(0, hieuUng.indexOf("[scene]"));
    expect(than).not.toContain("setChiTiet");
  });

  it("dòng chữ bước được KẸP — không bao giờ in một bước không tồn tại", () => {
    // W12: dòng chữ đếm bước DỰNG. Phép kẹp đi qua `geometryAnchor` (kẹp sự
    // kiện vào miền rồi về neo của bước dựng chứa nó), nên `current_step = 10`
    // trên một cảnh ngắn hơn vẫn in bước dựng CUỐI, không in "10/…".
    // W4: dòng chữ ấy dời vào thanh điều khiển của trình phát — kiểm bằng HÀNH VI ở đó, không bằng mã nguồn.
    expect(src).toMatch(/const buocHien = geometryAnchor\(day, tt\.current_step\);/);
    const n = geometryStepCount(CANH);
    const h = renderToString(<Scene3DPlayer scene={CANH} initialStep={10_000} />);
    expect(h.slice(h.indexOf("geo3d-controls"))).toContain(`Bước ${n}/${n}`);
  });
});

/* ══ W18 · §16.6 — MỘT NƠI GIẢI THÍCH ══════════════════════════════════════════════════════
 * Ô soi là bảng chi tiết của vật đang chọn (công thức, dữ kiện số, phụ thuộc). Lời giải đầy đủ thu
 * gọn mặc định; khi nó mở thì ô soi bỏ khối công thức — không hai bản sao cùng lúc. Mục Kết quả
 * (luôn hiện) chỉ mang `ký hiệu = giá trị` khi lời giải thu gọn. `same_as`: một dòng. */
const P18 = (id: string, xyz: [string, string, string]) => ({
  id, label: id, notation: id, type: "point3", render: "point_marker", origin: "free", producer: null,
  depends: [], xyz, parent: null, display_group: ["given"], source: {} });
const CANH_LG = {
  objects: [
    P18("A", ["0", "0", "0"]), P18("B", ["3", "0", "0"]), P18("C", ["0", "4", "0"]), P18("D", ["0", "0", "5"]),
    { id: "khoi", label: "Khối ABCD", notation: "ABCD", type: "solid", render: "mesh", origin: "derived",
      producer: "construct_solid", depends: ["A", "B", "C", "D"], vertex_ids: ["A", "B", "C", "D"],
      vertices: [["0", "0", "0"], ["3", "0", "0"], ["0", "4", "0"], ["0", "0", "5"]],
      faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]], parent: null, display_group: ["solid"], source: {} },
    { id: "AB_length", label: "AB", notation: "AB", type: "quantity", render: "readout", origin: "free",
      producer: null, depends: [], value: "3", exact: { kind: "rational", value: "3" }, parent: null,
      display_group: ["given"], source: {},
      annotation: { kind: "length", category: "measurement", role: "given", subject_ids: ["A", "B"], anchor: "segment" } },
    { id: "h", label: "Chiều cao", notation: "h", type: "quantity", render: "readout", origin: "derived",
      producer: "measure.distance", depends: ["A", "B"], value: "3", exact: { kind: "rational", value: "3" },
      parent: null, display_group: ["measurement"], source: {},
      annotation: { kind: "length", category: "measurement", role: "intermediate", subject_ids: ["A", "B"],
        anchor: "segment", same_as: "AB_length" } },
    { id: "V", label: "Thể tích ABCD", notation: "V", type: "quantity", render: "readout", origin: "derived",
      producer: "measure.volume", depends: ["khoi", "AB_length"], value: "10", exact: { kind: "rational", value: "10" },
      parent: null, display_group: ["target"], source: {},
      dependency_edges: [{ source_id: "AB_length", relation: "numerical" }],
      formula: { text: "V = 10/3 · AB = 10", references: [{ entity_id: "AB_length", display_label: "AB" }] },
      annotation: { kind: "volume", category: "result", role: "result", subject_ids: ["khoi"], anchor: "solid" } },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Dữ kiện.", semantic_kind: "EXPLANATION" },
    { step_index: 1, action: "CREATE", object: "khoi", depends: ["A", "B", "C", "D"], explanation: "Dựng khối.",
      semantic_kind: "GEOMETRY_CONSTRUCTION" },
    { step_index: 2, action: "MEASURE", object: "h", depends: ["A", "B"], explanation: "Đo h.", semantic_kind: "MEASUREMENT" },
    { step_index: 3, action: "MEASURE", object: "V", depends: ["khoi"], explanation: "Tính V.", semantic_kind: "MEASUREMENT" },
    { step_index: 4, action: "MEASURE", object: "V", depends: ["khoi"], explanation: "Kết luận.", semantic_kind: "FINAL_RESULT" },
  ],
  free_objects: ["A", "B", "C", "D", "AB_length"],
} as unknown as Scene3D;

describe("một nơi giải thích (§16.6)", () => {
  /* W05 · E: thẻ lời giải dưới mô phỏng ĐÃ GỠ — hai ca "thu gọn mặc định" / "mở ⇒ công thức về lời giải" nói về nó
     và đi cùng nó. Bất biến còn lại: ô soi là nơi DUY NHẤT mang công thức (`scene3d-focus-mode.test.tsx`), và
     `same_as` không đẻ mục thứ hai ở bảng «Đại lượng». */
  it("same_as: đại lượng đo lại đúng dữ kiện không có mục thứ hai ở «Đại lượng»", () => {
    const q = quantityChoices(CANH_LG, 4);
    const moi = [...q.results, ...q.steps, ...q.givens];
    expect(moi).toContain("AB_length");
    expect(moi).not.toContain("h");
  });

  it("nguồn của một đại lượng (cho ô soi): dữ kiện số trong chuỗi và đầu vào trực tiếp — do backend phát", () => {
    expect(quantitySources(CANH_LG, "V")).toEqual({ givens: ["AB_length"], inputs: ["AB_length"] });
    expect(quantitySources(CANH_LG, "AB_length")).toEqual({ givens: [], inputs: [] });
  });

  it("nhãn số đo bấm được: lớp nhãn không còn aria-hidden, mỗi nhãn là role=button có tabIndex, nghe bằng listener (không JSX onClick)", () => {
    const view = readFileSync(new URL("./scene3d-view.tsx", import.meta.url), "utf8");
    const lop = view.slice(view.indexOf('className="geo3d-so-do-lop"'), view.indexOf("</div>", view.indexOf('className="geo3d-so-do-lop"')));
    expect(lop).not.toContain('aria-hidden="true"');
    expect(lop).toContain('role="button"');
    expect(lop).toContain("tabIndex={0}");
    expect(view).toMatch(/addEventListener\("keydown"/);
  });
});
