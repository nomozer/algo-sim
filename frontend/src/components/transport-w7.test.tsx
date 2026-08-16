import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import {
  TRANSPORT_POLICY,
  transportModeOf,
  transportReasonOf,
} from "../simulations/transport-policy";
import { registerAllSimulations } from "../simulations/index";
import { listSimulations } from "../simulations/registry";

/**
 * WAVE 7 — KHAY ĐIỀU KHIỂN THUỘC WORKSPACE, KHÔNG THUỘC KHUNG CƠ CHẾ.
 *
 * ─── KHIẾM KHUYẾT ĐÃ ĐO ───────────────────────────────────────────────────
 *
 * `measure-transport-w7.mjs` ở 1920 (HEAD 104c752): bề rộng cơ chế trải
 * 600 → 1449px, và khay điều khiển trải **đúng 849px y hệt** — bám 1:1. Đổi từ
 * cổng AND sang bài CSS thì dải điều khiển phình gấp 2,4 lần và nút Chạy nhảy
 * chỗ. Không có mặt phẳng ổn định nào để tì mắt vào.
 *
 * Nguyên nhân là một quyết định CÓ CHỦ ĐÍCH của M19: đặt cả thẻ lẫn khay vào
 * cùng một cột `auto` để hai bên tự bằng nhau (giữ W4B-3H, khay không lệch mép
 * so với thẻ). W7 đảo nó: khay có bề rộng riêng theo chính sách workspace, và
 * thứ W4B-3H thật sự cần vẫn giữ được vì cả hai cùng căn GIỮA — thẳng TÂM thay
 * vì thẳng MÉP TRÁI. Thẳng tâm bền hơn vì nó đúng ở mọi bề rộng cơ chế.
 */

// ── 1. CHÍNH SÁCH, KHÔNG PHẢI SUY DIỄN KĨ THUẬT (§9) ────────────────────────

describe("W7 §9 — chế độ transport là chính sách sư phạm", () => {
  it("mọi target công khai đều được KHAI chế độ", () => {
    if (listSimulations().length === 0) registerAllSimulations();
    const missing = listSimulations().map((m) => m.id).filter((id) => !transportModeOf(id));
    expect(missing, `target chưa khai chế độ transport:\n${missing.join("\n")}`).toEqual([]);
  });

  it("giữ đúng 13 / 7 / 4 (Wave 6 chốt 13/7/3; W5A thêm color.rgb_model)", () => {
    const counts = Object.values(TRANSPORT_POLICY).reduce<Record<string, number>>(
      (acc, [mode]) => ({ ...acc, [mode]: (acc[mode] ?? 0) + 1 }), {});
    /* W5A — `color.rgb_model` vào RESET_ONLY, KHÔNG vào OPTIONAL_TRACE: trộn
       màu không có tiến trình nào để giải thích thêm, nên một lối vào 'xem
       cách thực hiện' ở đó sẽ mở ra khoảng trống. */
    expect(counts).toEqual({ FULL_TRACE: 13, OPTIONAL_TRACE: 7, RESET_ONLY: 4 });
    expect(Object.keys(TRANSPORT_POLICY)).toHaveLength(24);
  });

  it("mỗi khai báo phải nêu LÝ DO CƠ CHẾ kiểm chứng được", () => {
    for (const id of Object.keys(TRANSPORT_POLICY)) {
      const why = transportReasonOf(id)!;
      expect(why.length, `${id}: lý do quá ngắn`).toBeGreaterThan(60);
      for (const lazy of ["renderer đang", "hiện tại đang", "theo lịch sử", "vì có timeline"]) {
        expect(why, `${id}: lý do né cơ chế`).not.toContain(lazy);
      }
    }
  });

  it("KHÔNG target nào chưa khai mà vẫn có mặc định im lặng", () => {
    expect(transportModeOf("khong.ton.tai")).toBeNull();
    expect(transportReasonOf("khong.ton.tai")).toBeNull();
  });

  it("dải điều khiển KHÔNG phân loại bằng `stepCount` nữa", () => {
    /* §9: chế độ không được suy từ thuộc tính kĩ thuật. `stepCount` vẫn được
       phép dùng cho câu hẹp "có gì để tua không", nhưng phải đi kèm chế độ đã
       khai — không được đứng một mình làm phép phân loại. */
    const src = readFileSync(new URL("./SimulationControls.tsx", import.meta.url)
      .pathname.replace(/^\/([A-Za-z]:)/, "$1"), "utf-8");
    const body = src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    expect(body, "phải đọc chính sách").toMatch(/transportModeOf\(/);
    expect(body, "quyết định hiển thị phải kết hợp chế độ ĐÃ KHAI")
      .toMatch(/mode === "FULL_TRACE"/);
    /* LỖ NÀY DO TIÊM LỖI TÌM RA: thay `declaredMode ?? …` bằng suy diễn thuần
       `stepsAvailable ? …` vẫn giữ nguyên hai dòng trên, nên guard cũ xanh.
       Phải khoá chính PHÉP GÁN: chế độ đã khai phải là vế ĐẦU. */
    expect(body, "`mode` phải lấy từ chính sách trước, suy diễn chỉ là lưới an toàn")
      .toMatch(/const mode = declaredMode \?\?/);
  });
});

// ── 2. QUYỀN SỞ HỮU BỀ RỘNG (§1/§4/§10) ─────────────────────────────────────

describe("W7 §10 — bề rộng khay tách khỏi bề rộng cơ chế", () => {
  const css = () => readFileSync(new URL("../styles/global.css", import.meta.url)
    .pathname.replace(/^\/([A-Za-z]:)/, "$1"), "utf-8");

  it("khay có bề rộng RIÊNG theo chính sách workspace", () => {
    const block = css().slice(css().indexOf("\n.panel-controls {"));
    const decl = block.slice(0, block.indexOf("\n}"));
    expect(decl, "khay phải lấy bề rộng từ token chính sách")
      .toMatch(/width:\s*min\(100%,\s*var\(--transport-max\)\)/);
    expect(decl, "khay phải tự căn giữa").toMatch(/justify-self:\s*center/);
  });

  it("cột nội dung có SÀN bằng chính sách khay", () => {
    /* Không có sàn thì cột co đúng bằng thẻ, và khay `width: 100%` co theo —
       đo được: cơ chế 600px thì khay cũng 600px, tức bản vá vô hiệu. */
    /* CẢ HAI biến thể lưới phải có sàn. Bản đầu chỉ đòi mẫu xuất hiện MỘT lần,
       nên bỏ sàn ở biến thể có panel phải vẫn xanh nhờ biến thể `right-closed`
       — mà biến thể bị bỏ mới là cái đang dùng khi mở panel. */
    const floors = css().match(/minmax\(min\(100%, var\(--transport-max\)\), auto\)/g) ?? [];
    expect(floors.length, "thiếu sàn ở một biến thể lưới").toBeGreaterThanOrEqual(2);
  });

  it("token chính sách tồn tại (var() trỏ token ma là lỗi IM LẶNG)", () => {
    const tokens = readFileSync(new URL("../styles/tokens.css", import.meta.url)
      .pathname.replace(/^\/([A-Za-z]:)/, "$1"), "utf-8");
    expect(tokens).toMatch(/--transport-max:\s*\d+px/);
  });

  it("thẻ cơ chế tự căn giữa trong cột đã nới", () => {
    const block = css().slice(css().indexOf("\n.panel-center {"));
    expect(block.slice(0, block.indexOf("\n}"))).toMatch(/align-items:\s*center/);
  });
});

// ── 3. DÒNG THỜI GIAN TUỲ CHỌN: MỞ ĐƯỢC THÌ ĐÓNG ĐƯỢC (§7/§16) ──────────────

describe("W7 §7 — dòng thời gian tuỳ chọn gập mặc định", () => {
  const src = () => readFileSync(new URL("./SimulationControls.tsx", import.meta.url)
    .pathname.replace(/^\/([A-Za-z]:)/, "$1"), "utf-8");

  it("có lối VÀO và lối RA, và chỉ dựng cho chế độ tuỳ chọn", () => {
    const body = src().replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    expect(body).toContain("Xem cách thực hiện");
    expect(body).toContain("Ẩn các bước");
    expect(body, "lối vào chỉ dành cho OPTIONAL_TRACE")
      .toMatch(/mode === "OPTIONAL_TRACE" && stepsAvailable/);
  });

  it("mở/đóng dòng thời gian KHÔNG đụng store (§16 tool state authoritative)", () => {
    /* Trạng thái mở/gập là TRÌNH BÀY thuần. Đưa vào store là mở đường cho một
       lượt set() vô tình chạm vào `active` — và §16 đòi tham số công cụ không
       được đổi khi học sinh mở dòng thời gian. */
    const body = src();
    expect(body).toMatch(/const \[traceOpen, setTraceOpen\] = useState\(false\)/);
    expect(body, "traceOpen không được nằm trong store").not.toMatch(/s\.traceOpen/);
  });

  it("RESET_ONLY KHÔNG dựng lối vào dòng thời gian", () => {
    /* Cơ chế của chúng không có tiến trình nào để xem, nên một nút "Xem cách
       thực hiện" ở đó là lời hứa suông. */
    for (const id of ["logic.and_gate", "binary.decimal_to_binary", "web.style_model"]) {
      expect(transportModeOf(id), id).toBe("RESET_ONLY");
    }
  });
});
