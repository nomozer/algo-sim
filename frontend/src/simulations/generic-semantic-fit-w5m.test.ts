import { describe, expect, it } from "vitest";
import { OFFLINE_SAMPLES } from "../data/sim-samples";

/**
 * W5M (Phase M) — CẢNH GENERIC PHẢI TÍNH ĐƯỢC MỘT THỨ GÌ ĐÓ.
 *
 * ─── VẤN ĐỀ ────────────────────────────────────────────────────────────────
 *
 * `generic.rule_scene` tự khai là catch-all: *"dùng khi bài KHÔNG khớp mô phỏng
 * chuyên biệt nào"*. Đó là chỗ "gượng ép mô phỏng" sinh ra — đề không có cơ chế
 * ẩn nào vẫn được mặc cho bộ áo "cảnh có nút bấm", thay vì được TỪ CHỐI thật
 * thà bằng `capability_gap`.
 *
 * `COVERAGE.md` đã định nghĩa ranh giới: *"bài không có cơ chế ẩn thì mô phỏng
 * chỉ là trang trí"*. Test này nâng câu đó từ tài liệu thành cổng chạy được.
 *
 * ─── TIÊU CHÍ, DẪN XUẤT TỪ CHÍNH DSL ───────────────────────────────────────
 *
 * Không cần phán đoán thẩm mỹ. Spec generic có `rules` (boolean / weighted_sum)
 * thì có PHÉP TÍNH: đổi đầu vào ⇒ engine tính lại kết luận. Spec chỉ có
 * `processes` (reveal/move) thì không tính gì — nó hé lộ các frame dựng sẵn,
 * tức MINH HOẠ, không phải mô phỏng
 * (`SIMULATION_VS_ILLUSTRATION_CONTRACT.md`).
 *
 * ─── KIỂM KÊ TẠI THỜI ĐIỂM VIẾT (W5M bước 1) ───────────────────────────────
 *
 *   GENERIC_RULE_SPEC     boolean not+and   CÔNG KHAI   SEMANTIC_FIT
 *   GENERIC_AND_SPEC      boolean and       nội bộ      SEMANTIC_FIT (parity)
 *   GENERIC_BINARY_SPEC   weighted_sum      nội bộ      SEMANTIC_FIT (parity)
 *   GENERIC_PACKET_SPEC   —                 nội bộ      reveal-only
 *   GENERIC_REVEAL_SPEC   —                 nội bộ      reveal-only
 *
 * Mọi cảnh reveal-only đều là fixture NỘI BỘ, không bài nào tới tay học sinh —
 * nên ở tầng bài mẫu hệ đang trung thực. W4B-3F đã gỡ ca công khai duy nhất
 * ("Trang giới thiệu (từng bước)" — một `reveal_sequence` bịa trục thời gian
 * cho HTML). Test này giữ cho nó không quay lại.
 *
 * ⚠️ LỖ HỔNG CÒN LẠI, KHÔNG THUỘC TẦM TEST NÀY: đường AI. Một spec do LLM sinh
 * với `rules` rỗng + `processes` reveal sẽ ra đúng cảnh hé lộ không tính gì, và
 * nó KHÔNG đi qua `OFFLINE_SAMPLES`. Cổng cho đường đó phải nằm ở validator
 * generic phía server (`dsl/validator.py`) — W5M bước 2.
 */

interface GenericSpec {
  rules?: unknown[];
  processes?: unknown[];
  objects?: unknown[];
}

const GENERIC = OFFLINE_SAMPLES.filter(
  (s) => (s.envelope as { simulation_id?: string }).simulation_id === "generic.rule_scene",
);

/** Công khai = học sinh mở được từ Thư viện (`visibility` không khai ⇒ public). */
const isPublic = (s: (typeof OFFLINE_SAMPLES)[number]) => (s.visibility ?? "public") === "public";

const specOf = (s: (typeof OFFLINE_SAMPLES)[number]): GenericSpec =>
  (s.envelope as { config: GenericSpec }).config;

/** Có PHÉP TÍNH không — dẫn xuất từ DSL, không phán đoán thẩm mỹ. */
const computes = (spec: GenericSpec) => Array.isArray(spec.rules) && spec.rules.length > 0;

describe("W5M · cảnh generic công khai phải TÍNH được một thứ gì đó", () => {
  it("phép đo có đối tượng — không cảnh generic nào thì cổng này rỗng", () => {
    expect(GENERIC.length, "không còn bài generic nào để đo").toBeGreaterThan(0);
  });

  it.each(GENERIC.filter(isPublic).map((s) => s.id))(
    "%s: bài generic CÔNG KHAI khai được ít nhất một quy tắc tính",
    (id) => {
      const sample = GENERIC.find((s) => s.id === id)!;
      const spec = specOf(sample);
      expect(
        computes(spec),
        `${id}: cảnh chỉ hé lộ frame, không tính gì ⇒ đây là MINH HOẠ, không phải ` +
          "mô phỏng. Bài như thế phải là fixture nội bộ, hoặc bị từ chối bằng " +
          "`capability_gap` — không được bày cho học sinh.",
      ).toBe(true);
    },
  );

  it("(đối chứng) phép đo PHÂN BIỆT được hai loại, không phải luôn đúng", () => {
    /* Nếu mọi spec đều có `rules` thì khẳng định trên xanh vì lý do rỗng. Danh
       mục phải chứa CẢ hai loại thì cổng mới có nghĩa — và đúng là có: hai
       fixture nội bộ là reveal-only. */
    const revealOnly = GENERIC.filter((s) => !computes(specOf(s)));
    expect(revealOnly.length, "không còn cảnh reveal-only nào ⇒ đối chứng vô nghĩa")
      .toBeGreaterThan(0);
    for (const s of revealOnly) {
      expect(isPublic(s), `${s.id}: cảnh reveal-only mà đang CÔNG KHAI`).toBe(false);
    }
  });
});
