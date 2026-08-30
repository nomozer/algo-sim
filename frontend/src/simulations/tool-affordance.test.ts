/**
 * tool-affordance.test.ts — W12 §6/§11: CÔNG CỤ CÓ DÙNG ĐƯỢC KHI THỬ THÁCH ĐÓNG?
 *
 * ─── VÌ SAO CÓ TEST NÀY ────────────────────────────────────────────────────
 *
 * Quan sát của người dùng: `algorithm.find_max` đọc ra "nhìn hình → đọc câu hỏi
 * → bấm một trong hai nút" — tức một bài kiểm tra, không phải một công cụ.
 *
 * Truy nguyên bằng trình duyệt (`certify-viewports-w12.mjs`, 23×4) chứ không
 * bằng suy đoán: **52/92 dòng** không có affordance nào ngoài thanh điều khiển.
 * Nguyên nhân KHÔNG phải renderer hỏng — mà là hai miền cùng đòi `exploreOpen`
 * trước khi dựng công cụ, trong khi trang vừa mở thì cờ đó là `false`.
 *
 * Nên test này khoá LUẬT, không khoá pixel: chỗ nào nhìn thấy được thì
 * `certify-viewports-w12.mjs` đo; ở đây kiểm điều kiện sinh ra nó.
 */
import { beforeEach, describe, expect, it } from "vitest";
import { toolAffordanceOpen } from "./tool-affordance";
import { whatIfDragAllowed, whatIfPolicyOf } from "./domains/algorithm/interaction-policy";
import { makeAlgorithmModule } from "./domains/algorithm/index";
import { registerAllSimulations } from "./index";
import { listSimulations } from "./registry";
import { offlineCatalog } from "../data/offline-catalog";
import { useAppStore } from "../state/store";
import type { AlgorithmId } from "../core/types";
import type { AlgorithmSimState } from "./domains/algorithm/model";

/**
 * `mode: "hidden"` — hai bài mà kéo cột là TRANG TRÍ, khai kèm lý do cơ chế.
 *
 * Không phải ngoại lệ để dễ xanh: `runSumIf`/`runCountIf` không phát sự kiện
 * đổi chỗ nào, nên một cột kéo được ở đó sẽ hứa một cơ chế không tồn tại. Công
 * cụ thật của hai bài này là ĐIỀU KIỆN (`set_param`), không phải thứ tự dãy.
 */
const DRAG_IS_DECORATION: Record<string, string> = {
  sum_if: "tổng theo điều kiện không phụ thuộc thứ tự — công cụ là ngưỡng, không phải cột",
  count_if: "đếm theo điều kiện không phụ thuộc thứ tự — công cụ là ngưỡng, không phải cột",
};

const ALGORITHM_TARGETS: AlgorithmId[] = [
  "bubble_sort", "insertion_sort", "selection_sort",
  "linear_search", "binary_search",
  "find_max", "find_min", "sum_if", "count_if",
];

const DATA: Record<string, Record<string, unknown>> = {
  bubble_sort: { array: [3, 1, 2], order: "asc" },
  insertion_sort: { array: [3, 1, 2], order: "asc" },
  selection_sort: { array: [3, 1, 2], order: "asc" },
  linear_search: { array: [4, 9, 7], target: 9 },
  binary_search: { array: [1, 3, 5, 7, 9], target: 3 },
  find_max: { array: [7, 9, 6] },
  find_min: { array: [7, 9, 6] },
  sum_if: { array: [5, 8, 3], condition: { op: ">", value: 4 } },
  count_if: { array: [5, 8, 3], condition: { op: ">", value: 4 } },
};

function stateOf(id: AlgorithmId, cursor: number): AlgorithmSimState {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: {}, algorithm_id: id, data: DATA[id], data_generated: false, notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  return mod.timeline!.goToStep(mod.init(r.config), cursor) as AlgorithmSimState;
}

describe("W12 §6 → W13 — luật hiện công cụ, sau khi Thử thách bị gỡ", () => {
  /* VIẾT LẠI 2026-08-21 (Task 10b). Bản cũ kiểm ba nhánh của Policy B:
     "thử thách đóng ⇒ hiện", "thử thách mở ⇒ siết", "mở Khám phá thì được lại".
     W13 gỡ hẳn Thử thách nên hai nhánh sau KHÔNG CÒN ĐỐI TƯỢNG, và chính
     `tool-affordance.ts` đã co hợp đồng lại còn `{ busy }`.

     Thứ còn sống — và là thứ luôn đúng bất kể có bao nhiêu chế độ: ENGINE ĐANG
     CHẠY THÌ CÔNG CỤ NGHỈ. */

  it("mở bài ra là dùng được ngay — không cần mở chế độ nào trước", () => {
    expect(toolAffordanceOpen({ busy: false })).toBe(true);
  });

  it("engine đang chạy ⇒ mọi công cụ nghỉ", () => {
    expect(toolAffordanceOpen({ busy: true })).toBe(false);
  });

  /* ĐỐI CHỨNG DƯƠNG — một luật chỉ có giá trị nếu nó ĐỎ ĐƯỢC.
     Bản cài trước W12 đòi `exploreOpen`, nên ngay lúc mở bài nó giấu công cụ:
     đúng nguyên nhân của 52/92 dòng hỏng đo được trên trình duyệt. Giữ đối
     chứng này vì nó vẫn chứng minh được luật hiện tại KHÁC bản cũ. */
  it("(đối chứng) bản cài CŨ đòi mở Khám phá trước sẽ giấu mất công cụ", () => {
    const luatCu = (i: { exploreOpen: boolean; busy: boolean }) => i.exploreOpen && !i.busy;
    expect(toolAffordanceOpen({ busy: false })).toBe(true);
    expect(
      luatCu({ exploreOpen: false, busy: false }),
      "bản cũ vẫn cho công cụ hiện ⇒ đối chứng vô nghĩa",
    ).toBe(false);
  });
});

describe("W12 §11 — quét CẢ HỌ thuật toán, không kết luận từ một bài", () => {
  it.each(ALGORITHM_TARGETS)("%s: mở bài ra là công cụ có mặt (hoặc khai rõ vì sao không)", (id) => {
    const policy = whatIfPolicyOf(id);
    const state = stateOf(id, 1);
    const allowed = policy.mode === "hidden"
      ? false
      : whatIfDragAllowed(state, {
          policyAllows: toolAffordanceOpen({ busy: false }),
          busy: false, last: false,
        });

    if (id in DRAG_IS_DECORATION) {
      expect(policy.mode, `${id} khai là trang trí thì phải là hidden`).toBe("hidden");
      expect(DRAG_IS_DECORATION[id].length, `${id}: lý do quá ngắn để kiểm được`)
        .toBeGreaterThan(40);
      expect(allowed).toBe(false);
      return;
    }
    expect(allowed, `${id}: mở bài ra mà công cụ vẫn bị giấu`).toBe(true);
  });

  it("danh sách trang trí chỉ được NGẮN ĐI — thêm dòng là tự khai vừa giấu công cụ", () => {
    /* Cùng kỉ luật với `KNOWN_GAPS` của `code-index-sync.test.ts`: một ngoại lệ
       không có trần thì sẽ lớn dần cho tới khi luật không còn nghĩa. */
    expect(Object.keys(DRAG_IS_DECORATION)).toEqual(["sum_if", "count_if"]);
  });
});

/* ══ W12-B · ĐÓNG THỬ THÁCH KHÔNG ĐƯỢC ĐỤNG VÀO SỰ THẬT ═══════════════════
 *
 * Hợp đồng Khám phá/Thử thách đòi bốn điều, và ba đã có chủ khoá:
 *
 *   THỬ THÁCH ĐÓNG  ⇒ công cụ chính còn nguyên   → `toolAffordanceOpen` (trên)
 *   HAI CỜ ĐỘC LẬP                               → `explore-ownership-w4b3a §2`
 *   ĐÓNG KHÁM PHÁ   ⇒ chỉ đổi hiển thị           → `explore-ownership-w4b3a §1`
 *   ĐÓNG THỬ THÁCH  ⇒ KHÔNG đổi state canonical  → CHƯA AI KHOÁ (ở đây)
 *
 * Vì sao điều thứ tư nguy hiểm hơn ba điều kia: `challengeOpen` là cờ DUY NHẤT
 * nằm cạnh `prediction` trong store, nên một lần "dọn dẹp cho sạch" (xoá dự
 * đoán ⇒ dựng lại state ⇒ mất cursor) là sửa đúng một dòng và không test nào
 * đỏ. Học sinh sẽ thấy mô phỏng nhảy về bước 0 mỗi lần đóng thử thách.
 *
 * Quét CẢ danh mục chứ không một bài: bất biến này thuộc store (mù domain), nên
 * một bài xanh không nói gì về 22 bài kia — và store là chỗ dễ thêm nhánh theo
 * miền nhất.
 */
describe("W12-B · chế độ là TRÌNH BÀY, không phải sự thật", () => {
  beforeEach(() => {
    if (listSimulations().length === 0) registerAllSimulations();
  });

  /* Danh mục mẫu có NHIỀU bài cho cùng một target (mỗi target ≥1 đề), nên quét
     theo `simId` duy nhất — quét theo số bài mẫu sẽ đo nhầm một đại lượng khác
     và trôi mỗi lần ai đó thêm một đề. */
  const CATALOG = [...new Set(offlineCatalog().map((x) => x.simId))].sort();

  it("danh mục mẫu vẫn phủ đủ 24 target — quét hẹp đi là quét mù", () => {
    // 23 (W12) + `color.rgb_model` (W5A).
    // 24 (Tin học) + `generic.semantic_program` — target HÌNH HỌC, vào danh
    // mục từ 2026-08-30 nhờ bài mẫu sinh từ kernel. Nó đi qua ĐÚNG những
    // phép soát này chứ không được miễn: miễn một target là mở lại đúng chỗ
    // mù mà các test ở đây sinh ra để bịt.
    expect(CATALOG.length).toBe(25);
  });

  /* VIẾT LẠI 2026-08-21 (Task 10b) — CHUYỂN CHỦ THỂ, GIỮ BẤT BIẾN.
     Bản cũ chạy luật này qua `setChallengeOpen`, mà W13 đã gỡ Thử thách. Nhưng
     bất biến thì KHÔNG chết theo: "chế độ là TRÌNH BÀY, không phải sự thật" vẫn
     phải đúng với mọi chế độ còn lại. `exploreOpen` mang đúng vai đó, nên luật
     dời sang nó thay vì bị xoá cùng chế độ cũ. */
  it.each(CATALOG)("%s: mở rồi đóng Khám phá KHÔNG dựng lại state canonical", (simId) => {
    const e = offlineCatalog().find((x) => x.simId === simId)!;
    useAppStore.getState().loadEnvelope(e.envelope);

    const before = useAppStore.getState().active!;
    useAppStore.getState().setExploreOpen(true);
    expect(useAppStore.getState().active!.state, `${simId}: MỞ Khám phá đã dựng lại state`)
      .toBe(before.state);

    useAppStore.getState().setExploreOpen(false);
    const after = useAppStore.getState().active!;
    // So bằng THAM CHIẾU: state canonical không được dựng lại, kể cả thành một
    // đối tượng "bằng giá trị" — dựng lại là mất mọi thứ engine đang giữ.
    expect(after.state, `${simId}: ĐÓNG Khám phá đã dựng lại state`).toBe(before.state);
    expect(after.config, `${simId}: đóng Khám phá đã đụng config`).toBe(before.config);
    expect(useAppStore.getState().exploreOpen).toBe(false);
  });

  it("(đối chứng) một `setExploreOpen` có 'dọn dẹp' sẽ làm luật này ĐỎ", () => {
    /* Bản cài sai hợp lý nhất — đóng chế độ thì dựng lại mô hình cho sạch —
       phải phá được khẳng định ở trên. Không dựng lại được cảnh đó thì test
       trên chỉ đang mô tả chính nó (`ARCHITECTURE_MAP §8` #14). */
    const e = offlineCatalog().find((x) => x.simId === "algorithm.find_max")!;
    useAppStore.getState().loadEnvelope(e.envelope);
    const before = useAppStore.getState().active!.state;

    // Đây CHÍNH LÀ thứ luật cấm, gọi thẳng qua API công khai của store.
    useAppStore.getState().resetSim();
    expect(useAppStore.getState().active!.state, "đối chứng vô nghĩa: dựng lại mà state y nguyên")
      .not.toBe(before);
  });
});
