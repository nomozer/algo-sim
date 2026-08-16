import { describe, expect, it } from "vitest";
import { DOMAIN_BADGE, headerSubtitle } from "./header-identity";
import { registerAllSimulations } from "../simulations/index";
import { getSimulation, listSimulations } from "../simulations/registry";
import { offlineCatalog } from "../data/offline-catalog";
import type { Domain, SimulationModule } from "../simulations/types";

/**
 * W5Z — DẢI NHẬN DIỆN PHẢI GIỐNG NHAU Ở MỌI TARGET.
 *
 * ─── VÌ SAO CÓ CỔNG NÀY ────────────────────────────────────────────────────
 *
 * Người dùng bắt đúng một lớp lỗi mà không test nào bắt: "mỗi cái một design
 * riêng". Ba dòng đầu thẻ mô phỏng là thứ đọc trước tiên, và khi mỗi miền tự
 * quyết định nó trông thế nào thì bề mặt vỡ thành 24 kiểu — vừa khó dùng vừa
 * khiến mọi lần sửa phải đọc lại từng miền một.
 *
 * Đo trên cả 24 target (không phải soi ảnh một màn) ra bốn lệch THẬT:
 *   · `web` không có nhãn tiếng Việt ⇒ in "WEB" (`geometry` sẽ in "GEOMETRY");
 *   · 2 target có phụ đề LẶP NGUYÊN VĂN tiêu đề ngay bên dưới tiêu đề;
 *   · 3 target nhét bản liệt kê biến thể vào phụ đề, trong khi control ngay
 *     dưới sân khấu đã bày đúng các biến thể ấy BẰNG TIẾNG VIỆT;
 *   · phụ đề dài 12→64 ký tự, không có trần nào.
 *
 * ─── ĐIỀU CỐ Ý KHÔNG KHOÁ ─────────────────────────────────────────────────
 *
 * KHÔNG cấm mọi chữ tiếng Anh: "HTML/CSS", "TCP/IP", "RGB" là thuật ngữ chương
 * trình học, và "(AI tự dựng)" ở miền `generic` là DẤU TRUNG THỰC có chủ đích
 * (`docs/evaluation/m17/rc1/visual_stress_review.md`) — nói cho học sinh biết mô
 * phỏng này do AI dựng chứ không phải bản chuyên biệt đã kiểm. San phẳng nó là
 * xoá một quyết định đúng. Cổng này chỉ cấm thứ ĐÃ CÓ tên tiếng Việt ngay trên
 * cùng màn hình.
 */

registerAllSimulations();

/* DỰNG Ở TẦNG MODULE, KHÔNG TRONG `beforeAll` — `it.each(rows)` thu thập TRƯỚC
   mọi hook, nên rows rỗng lúc ấy sinh ĐÚNG 0 ca mà cả file vẫn XANH. Đã mắc đúng
   lỗi này ở W5E và W5N. */
const rows = (() => {
  const out: { simId: string; mod: SimulationModule; title: string }[] = [];
  const seen = new Set<string>();
  for (const e of offlineCatalog()) {
    if (seen.has(e.simId)) continue;
    const mod = getSimulation(e.simId) as SimulationModule | undefined;
    if (!mod) continue;
    seen.add(e.simId);
    out.push({ simId: e.simId, mod, title: String((e.envelope as { title: unknown }).title ?? "") });
  }
  return out;
})();

describe("W5Z · nhãn miền", () => {
  it("phép đo phủ cả danh mục — thiếu target là quét mù", () => {
    expect(rows.length).toBe(24);
  });

  it("MỌI miền đã đăng ký đều có nhãn, và nhãn KHÔNG phải id viết hoa", () => {
    const domains = new Set(
      listSimulations().map((s) => (getSimulation(s.id) as SimulationModule).domain),
    );
    expect(domains.size).toBeGreaterThan(5);

    /* "logic" là TỪ MƯỢN — tiếng Việt viết y nguyên, nên nhãn trùng id viết hoa
       ở đây là đúng chứ không phải rò định danh. Ghi ngoại lệ ra thành danh sách
       hẹp, KHÔNG bỏ phép kiểm: bỏ đi thì `web`→"WEB" và `geometry`→"GEOMETRY"
       lại lọt đúng như cũ. Thêm tên vào đây phải kèm lý do ngôn ngữ. */
    const TU_MUON = new Set(["logic"]);

    for (const d of domains) {
      const badge = DOMAIN_BADGE[d as Domain];
      expect(badge, `miền "${d}" chưa có nhãn tiếng Việt`).toBeTruthy();
      if (TU_MUON.has(d)) continue;
      /* Đây là chỗ bản cũ trượt: fallback `domain.toUpperCase()` trả một chuỗi
         "hợp lệ" nên mọi phép kiểm rỗng/khác-null đều xanh, trong khi thứ lên
         màn hình là định danh kỹ thuật. */
      expect(badge, `miền "${d}" đang dùng chính id viết hoa làm nhãn`).not.toBe(d.toUpperCase());
    }
  });
});

describe("W5Z · phụ đề cơ chế", () => {
  it("KHÔNG target nào để phụ đề lặp lại nguyên văn tiêu đề", () => {
    const dup = rows.filter((r) => headerSubtitle(r.mod.title, r.title) === null);
    /* Sau bản vá, hai ca lặp (`logic.and_gate`, `color.rgb_model`) vẫn LẶP ở dữ
       liệu — điều đổi là SHELL không dựng dòng đó nữa. Nên phép kiểm đúng là
       "shell trả null", không phải "dữ liệu hết trùng": ép 24 module đặt tên
       khác đi chỉ để tránh trùng là bịa thêm chữ cho học sinh đọc. */
    for (const r of dup) {
      expect(
        headerSubtitle(r.mod.title, r.title),
        `${r.simId}: phụ đề trùng tiêu đề mà shell vẫn dựng`,
      ).toBeNull();
    }
  });

  it("phép đo PHÂN BIỆT được: có target ẩn phụ đề, có target hiện", () => {
    /* Toàn ẩn hoặc toàn hiện đều là dấu hiệu hàm hỏng chứ không phải sự thật. */
    const hidden = rows.filter((r) => headerSubtitle(r.mod.title, r.title) === null);
    expect(hidden.length, "không target nào ẩn ⇒ luật không chạy").toBeGreaterThan(0);
    expect(hidden.length, "MỌI target đều ẩn ⇒ hàm nhận bừa").toBeLessThan(rows.length);
  });

  it("phụ đề KHÔNG liệt kê biến thể mà control đã bày bằng tiếng Việt", () => {
    /* Danh sách hẹp và có lý do: mỗi từ dưới đây ĐÃ có nhãn tiếng Việt hiển thị
       ngay dưới sân khấu ("Trước (gốc → trái → phải)", "BFS — theo chiều rộng",
       "Chọn giá trị và cơ số"). Cùng một khái niệm mang hai tên trên một màn
       hình là thứ làm học sinh tưởng đó là hai thứ khác nhau. */
    const CAM = ["preorder", "inorder", "postorder", "level-order", "level_order"];
    for (const r of rows) {
      const low = r.mod.title.toLowerCase();
      for (const t of CAM) {
        expect(low.includes(t), `${r.simId}: phụ đề còn "${t}" — control dưới sân khấu đã có nhãn tiếng Việt`).toBe(false);
      }
    }
  });

  it("phụ đề có TRẦN ĐỘ DÀI — một dòng, không phải một câu", () => {
    for (const r of rows) {
      expect(
        r.mod.title.length,
        `${r.simId}: phụ đề ${r.mod.title.length} ký tự (${JSON.stringify(r.mod.title)}) — quá dài so với phần còn lại`,
      ).toBeLessThanOrEqual(40);
    }
  });
});

describe("W5Z · hàm thuần headerSubtitle", () => {
  it("ẩn khi chỉ khác hoa/thường hoặc khoảng trắng thừa", () => {
    expect(headerSubtitle("Cổng logic AND", "cổng  logic and")).toBeNull();
    expect(headerSubtitle("  Mô hình màu RGB ", "Mô hình màu RGB")).toBeNull();
  });

  it("giữ nguyên chuỗi gốc (kể cả hoa/thường) khi nó nói thêm được", () => {
    expect(headerSubtitle("Tìm giá trị lớn nhất", "Tìm học sinh có điểm cao nhất"))
      .toBe("Tìm giá trị lớn nhất");
  });

  it("phụ đề rỗng ⇒ null, không phải chuỗi rỗng dựng span rỗng", () => {
    expect(headerSubtitle("", "Bất kỳ")).toBeNull();
    expect(headerSubtitle("   ", "Bất kỳ")).toBeNull();
  });
});
