import { beforeEach, describe, expect, it } from "vitest";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { offlineCatalog } from "../data/offline-catalog";
import { candidateActions } from "./action-probe";
import { transportModeOf } from "./transport-policy";
import type { SimulationModule } from "./types";

/**
 * W5E (Phase E) — KHÁM PHÁ ≠ TRACE.
 *
 * ─── LUẬT ─────────────────────────────────────────────────────────────────
 *
 *   KHÁM PHÁ = trạng thái HIỆN TẠI của mô hình, đầy đủ, đã tất định.
 *   TRACE    = TIÊU ĐIỂM giải thích trên chính quá trình đó.
 *
 * Con trỏ trace được phép chọn *kể tới đâu*. Nó KHÔNG được phép biến một giá
 * trị engine ĐÃ TÍNH thành "chưa biết" sau khi học sinh vừa hỏi.
 *
 * ─── LỖI THẬT ĐÃ BẮT ĐƯỢC ─────────────────────────────────────────────────
 *
 * `logic.boolean_dag`: `apply` trả `initFromValues(...)` mà hàm đó đặt
 * `cursor: 0`. Học sinh bật một đầu vào — thao tác Khám phá DUY NHẤT của bài —
 * và cả mạch sập về `?`, dù `nodeOutputs` ngay lúc ấy đã giữ trọn đáp án. Câu
 * hỏi "nếu đổi thì sao?" được trả lời bằng "chưa biết".
 *
 * Đây là chuyện ĐÚNG SAI của bề mặt, không phải tiện dụng: engine biết mà màn
 * hình nói không biết thì luận điểm "engine tất định sở hữu kết quả" bị phản
 * chứng ngay chỗ học sinh nhìn vào.
 */

/* ĐĂNG KÝ Ở TẦNG MODULE, KHÔNG Ở `beforeEach` — và đây là lỗi đã bắt được ngay
   trong wave này, không phải phòng xa. `it.each(targets())` được dựng lúc THU
   THẬP test, tức TRƯỚC mọi `beforeEach`; để registry rỗng lúc ấy thì `targets()`
   trả mảng rỗng, `it.each` sinh ĐÚNG 0 ca, và cả file vẫn báo XANH. Một lượt
   chạy rỗng màu xanh là điều tệ nhất một bộ chọn có thể làm (`TEST_TIERS.md`). */
registerAllSimulations();

beforeEach(() => {
  if (listSimulations().length === 0) registerAllSimulations();
});

/**
 * ─── VÌ SAO KHÔNG QUÉT BẰNG "CON TRỎ CÓ VỀ 0 KHÔNG" ───────────────────────
 *
 * Bản đầu của test này quét đúng thế, và nó bắt NHẦM năm target: `sum_if`,
 * `count_if`, `base_conversion`, `character_encoding`, `relational_table_query`
 * đều đưa con trỏ về 0 sau một thao tác — nhưng cả năm đều khai
 * `OPTIONAL_TRACE`, tức **kết quả đọc được NGAY ở bước 0**. Ở đó con trỏ về đầu
 * không giấu gì cả.
 *
 * Tức "con trỏ về 0" chỉ là dấu hiệu GIÁN TIẾP, và nó đo sai đại lượng. Đại
 * lượng đúng là: **thứ engine đã tính có hiện ra trên màn hình không.**
 *
 * Nên luật được phát biểu lại như một phép đối chiếu KHAI BÁO ↔ HÀNH VI:
 *
 *   khai `OPTIONAL_TRACE`  ⇒  hứa "kết quả đọc được ngay, trace chỉ giải thích"
 *   ⇒ sau một thao tác của học sinh, kết quả PHẢI hiện ra.
 *
 * `logic.boolean_dag` khai đúng lời hứa ấy (`transport-policy.ts`: *"Đầu ra của
 * mạch tính được ngay khi đổi đầu vào"*) trong khi renderer của nó lại bày `?`
 * — khai một đằng, làm một nẻo. Đó mới là lỗi, và nó nằm ở BỀ MẶT chứ không
 * nằm ở con trỏ.
 */

/**
 * Target KHÔNG dùng khe thuyết minh dùng chung của shell, nên phép đo dựa trên
 * `narrate` đọc không được chúng. Khai tường minh — danh sách chỉ được NGẮN ĐI.
 *
 * Chúng KHÔNG được miễn khỏi LUẬT, chỉ nằm ngoài tầm của PHÉP ĐO này; chỗ kiểm
 * của chúng là guard riêng của miền.
 */
const NO_SHELL_NARRATION = ["binary.base_conversion", "generic.rule_scene"];

/** Bài mẫu đầu tiên của mỗi target — không dựng fixture riêng. */
function targets(): { simId: string; config: unknown; mod: SimulationModule }[] {
  const seen = new Set<string>();
  const out: { simId: string; config: unknown; mod: SimulationModule }[] = [];
  for (const e of offlineCatalog()) {
    if (seen.has(e.simId)) continue;
    const mod = getSimulation(e.simId) as SimulationModule | undefined;
    if (!mod) continue;
    const r = mod.validateConfig((e.envelope as { config: unknown }).config);
    if (!r.ok) continue;
    seen.add(e.simId);
    out.push({ simId: e.simId, config: r.config, mod });
  }
  return out;
}

describe("W5E · khai `OPTIONAL_TRACE` thì phải TRẢ LỜI được ngay", () => {
  const OPTIONAL = targets().filter((t) => transportModeOf(t.simId) === "OPTIONAL_TRACE");

  it("phép đo phủ cả danh mục, và có target để đo (thiếu là quét mù)", () => {
    // 24 (Tin học) + `generic.semantic_program` — target HÌNH HỌC, vào danh
    // mục từ 2026-08-30 nhờ bài mẫu sinh từ kernel. Nó đi qua ĐÚNG những
    // phép soát này chứ không được miễn: miễn một target là mở lại đúng chỗ
    // mù mà các test ở đây sinh ra để bịt.
    expect(targets().length).toBe(25);
    expect(OPTIONAL.length, "không target nào khai OPTIONAL_TRACE ⇒ phép đo rỗng")
      .toBeGreaterThan(5);
  });

  it.each(OPTIONAL.map((t) => t.simId))(
    "%s: sau thao tác của học sinh, kết quả engine KHÔNG bị con trỏ giấu lại",
    (simId) => {
      const { mod, config } = targets().find((x) => x.simId === simId)!;
      if (!mod.timeline || !mod.apply) return;

      const s0 = mod.init(config);
      const acted = candidateActions(config)
        .map((a) => { try { return mod.apply!(s0, a); } catch { return s0; } })
        .find((s) => s !== s0);
      if (!acted) return; // không thao tác được ⇒ ngoài phạm vi luật này

      /* Điều phải đúng: ở CHÍNH con trỏ sau thao tác, bề mặt nói được kết quả.
         Đo qua `narrate` — khe chữ DUY NHẤT của shell, và là thứ học sinh đọc.
         Một bài giấu kết quả sẽ nói về "bước đang xét", không nói được đáp số. */
      const text = mod.narrate?.(acted, config as never)?.text ?? "";

      if (!text) {
        /* KHÔNG dùng khe thuyết minh của shell ⇒ phép đo này ĐỌC KHÔNG ĐƯỢC nó.
           Khai ra thay vì lặng lẽ cho qua: một target trượt khỏi phép đo mà
           không ai biết thì "cả họ đã kiểm" là một câu nói quá. */
        expect(
          NO_SHELL_NARRATION,
          `${simId}: không có thuyết minh shell mà chưa được khai — phép đo đang bỏ sót nó trong im lặng`,
        ).toContain(simId);
        return;
      }

      expect(
        text,
        `${simId}: khai OPTIONAL_TRACE nhưng bề mặt còn nói "chưa biết" sau thao tác`,
      ).not.toMatch(/\?\s*$|chưa tới lượt|chưa biết/);
    },
  );
});

/* ══ CA CỤ THỂ: mạch logic — ĐÃ ĐÓNG (W5E) ══════════════════════════════
 *
 * Lỗi: `apply` trả `initFromValues(...)` vốn đặt `cursor: 0`, nên bật một đầu
 * vào — thao tác Khám phá DUY NHẤT của bài — đẩy cả mạch về `?` dù
 * `nodeOutputs` ngay lúc ấy đã giữ trọn đáp án tất định.
 *
 * Sửa bằng cách TÁCH HAI TÍN HIỆU (`BoolDagState.exploreReveal`), vì sân khấu
 * và bảng chân trị làm hai việc khác nhau mà trước đó cùng đọc mỗi `cursor`:
 *   sân khấu      → trả lời câu học sinh vừa hỏi (bộ đầu vào ĐANG đặt);
 *   bảng chân trị → giữ hé lộ dần, vì học sinh CHƯA hỏi các bộ còn lại.
 *
 * Khoá tại `domains/logic/dag.test.tsx` (nơi có sẵn fixture + render SSR của
 * miền): hai test `W5E — …`, kèm phân loại ba khẳng định cũ thành
 * OLD_PRODUCT_CONTRACT / STILL_VALID_INVARIANT.
 */
