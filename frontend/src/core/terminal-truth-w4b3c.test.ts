import { describe, expect, it } from "vitest";
import { ALGORITHM_IDS, type AlgorithmId } from "./types";
import { makeAlgorithmModule } from "../simulations/domains/algorithm";
import { activeTrace, type AlgorithmSimState } from "../simulations/domains/algorithm/model";
import { insertionHold } from "../simulations/domains/algorithm/ui";
import { offlineCatalog } from "../data/offline-catalog";
import { getSimulation, registerAllSimulations } from "../simulations";

/**
 * W4B-3C — SỰ THẬT Ở BƯỚC CUỐI.
 *
 * ─── QUAN SÁT GỐC ─────────────────────────────────────────────────────────
 *
 * Ảnh nghiệm thu `algorithm_insertion_sort-terminal` (bước 33/33) tuyên bố
 * *"Dãy đã sắp xếp tăng dần xong bằng phương pháp chèn."* nhưng vẫn vẽ một quân
 * bài giá trị 2 nằm NGOÀI dãy và một ô trống nét đứt trong dãy.
 *
 * ─── MẪU HỎNG (không phải lỗi của riêng insertion_sort) ───────────────────
 *
 * `TraceBuilder` chỉ có `setVar`, không có đường gỡ. Nên mọi biến mô tả một
 * THAO TÁC ĐANG DỞ sống tới hết trace:
 *   - `gia_tri_chen`   (insertion) — quân bài đang cầm ngoài dãy;
 *   - `vi_tri_cuc_tri` (selection) — vị trí cực trị của LƯỢT đang chạy.
 * Ở bước `done`, state có thẩm quyền TỰ MÂU THUẪN: kết quả nói xong, snapshot
 * nói đang giữ. Renderer vẽ trung thành cái nó được kể — nó KHÔNG sai.
 *
 * ─── VÌ SAO KHÔNG VÁ Ở RENDERER ───────────────────────────────────────────
 *
 * `if (bước cuối) ẩn quân bài` là dạy renderer nói dối hộ engine, và nó để
 * nguyên mâu thuẫn trong chính state mà `getExplainContext` gửi cho AI giải
 * thích. Chủ sở hữu là ENGINE: gỡ biến ĐÚNG LÚC thứ nó mô tả hết tồn tại.
 *
 * ─── BẤT BIẾN KHOÁ Ở ĐÂY ──────────────────────────────────────────────────
 *
 * Ở bước `done` của MỌI bài sắp xếp:
 *   1. dãy đã sắp đúng chiều khai báo;
 *   2. `done.result` nói đúng về dãy cuối;
 *   3. KHÔNG còn phần tử nào bị rút ra ngoài dãy (không hold, không gap);
 *   4. mọi phần tử được đánh dấu đã-sắp;
 *   5. hình chiếu của renderer ở bước cuối là RỖNG các hiện vật đang-dở.
 */

registerAllSimulations();

const SORTS: AlgorithmId[] = ["bubble_sort", "insertion_sort", "selection_sort"];
const ARRAY = [5, 2, 9, 1, 7, 3];

/** Biến mô tả thao tác ĐANG DỞ — khai ở đây, không suy từ tên. */
const IN_FLIGHT_VARS: Record<string, string> = {
  gia_tri_chen: "quân bài đang cầm ngoài dãy (insertion)",
  vi_tri_cuc_tri: "vị trí cực trị của lượt đang chạy (selection)",
};

function build(id: AlgorithmId, order: "asc" | "desc" = "asc") {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: {}, algorithm_id: id, data: { array: [...ARRAY], order },
    data_generated: false, notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  const s0 = mod.init(r.config) as AlgorithmSimState;
  const total = mod.timeline!.stepCount(s0);
  const terminal = mod.timeline!.goToStep(s0, total - 1) as AlgorithmSimState;
  return { mod, config: r.config, s0, total, terminal };
}

describe("W4B-3C · bước cuối của họ sắp xếp phải tự nhất quán", () => {
  for (const id of SORTS) {
    for (const order of ["asc", "desc"] as const) {
      it(`${id} (${order}): dãy đã sắp, không còn thao tác dang dở`, () => {
        const { terminal, total } = build(id, order);
        const trace = activeTrace(terminal);
        const step = trace.steps[total - 1];

        // (2) bước cuối PHẢI là `done`.
        const done = step.events.find((e) => e.type === "done");
        expect(done, `${id}: bước cuối không phát done`).toBeTruthy();

        // (1) dãy đã sắp đúng chiều.
        const arr = step.snapshot.array;
        const sorted = [...ARRAY].sort((a, b) => (order === "asc" ? a - b : b - a));
        expect(arr, `${id}: dãy cuối chưa sắp đúng chiều`).toEqual(sorted);

        // (3) KHÔNG còn biến thao-tác-đang-dở nào.
        for (const [v, why] of Object.entries(IN_FLIGHT_VARS)) {
          expect(step.snapshot.vars[v], `${id}: bước cuối còn khai ${v} — ${why}`)
            .toBeUndefined();
        }

        // (4) mọi phần tử đã được đánh dấu đã-sắp.
        for (let i = 0; i < arr.length; i += 1) {
          expect(step.snapshot.marks[i], `${id}: phần tử ${i + 1} chưa được đánh dấu đã sắp`)
            .toBe("sorted");
        }

        // (5) hình chiếu renderer ở bước cuối KHÔNG còn hiện vật đang-dở.
        expect(insertionHold(terminal, total - 1), `${id}: bước cuối vẫn vẽ quân bài + ô trống`)
          .toBeNull();
      });
    }
  }

  it("hình chiếu quân-bài-đang-giữ CHỈ tồn tại giữa lúc rút và lúc chèn", () => {
    /* Bất biến hẹp hơn và mạnh hơn "bước cuối sạch": mỗi bước có hold thì phải
       có một bước chèn PHÍA SAU nó. Hold không bao giờ được là trạng thái treo
       vĩnh viễn — đó chính là hình dạng của lỗi gốc. */
    const { s0, total, mod } = build("insertion_sort");
    const trace = activeTrace(s0);
    for (let i = 0; i < total; i += 1) {
      const at = mod.timeline!.goToStep(s0, i) as AlgorithmSimState;
      if (insertionHold(at, i) === null) continue;
      const laterInsert = trace.steps.slice(i).some((st) => st.events.some((e) => e.type === "insert"));
      expect(laterInsert, `bước ${i + 1}/${total}: đang giữ quân bài mà không còn bước chèn nào`)
        .toBe(true);
    }
  });

  it("TOÀN DANH MỤC: mọi mẫu có dòng thời gian đều tới được bước cuối ổn định", () => {
    /* W4B-3D — quét CẢ danh mục offline (nay đủ 23 target), không riêng họ
       thuật toán. Ba điều kiểm được mà không cần trình duyệt:
         1. đi tới bước cuối KHÔNG ném lỗi;
         2. bước cuối là ĐIỂM DỪNG — tiến thêm không đổi state nữa;
         3. state ở bước cuối là ỔN ĐỊNH — vào lại đúng bước ấy cho cùng kết quả.
       (2) là thứ dễ hỏng nhất khi thêm timeline mới: một `goToStep` không kẹp
       biên sẽ chạy quá cuối và đẻ ra bước rỗng. */
    for (const e of offlineCatalog()) {
      const mod = getSimulation(e.simId);
      if (!mod?.timeline) continue;
      const v = mod.validateConfig(e.envelope.config);
      expect(v.ok, `${e.id}: config mẫu không hợp lệ`).toBe(true);
      if (!v.ok) continue;
      const s0 = mod.init(v.config);
      const total = mod.timeline.stepCount(s0);
      expect(total, `${e.id}: timeline rỗng`).toBeGreaterThan(0);

      const last = mod.timeline.goToStep(s0, total - 1);
      expect(mod.timeline.currentStep(last), `${e.id}: không tới được bước cuối`).toBe(total - 1);

      const past = mod.timeline.goToStep(last, total);
      expect(mod.timeline.currentStep(past), `${e.id}: đi quá bước cuối không bị kẹp biên`)
        .toBe(total - 1);

      const again = mod.timeline.goToStep(s0, total - 1);
      expect(mod.timeline.currentStep(again), `${e.id}: bước cuối không ổn định`).toBe(total - 1);
    }
  });

  it("MỌI bài có timeline đều kết thúc bằng `done` và kết quả khớp state", () => {
    /* Quét cả họ thuật toán chứ không riêng sắp xếp: "kết quả nói một đằng,
       state một nẻo" là mẫu hỏng, không phải sự cố của một bài. */
    for (const id of ALGORITHM_IDS) {
      const needsTarget = id === "linear_search" || id === "binary_search";
      const mod = makeAlgorithmModule(id);
      const data: Record<string, unknown> = needsTarget
        ? { array: [1, 3, 5, 7, 9], target: 7 }
        : id === "sum_if" || id === "count_if"
          ? { array: [...ARRAY], condition: { op: ">", value: 3 } }
          : { array: [...ARRAY], order: "asc" };
      const r = mod.validateConfig({
        problem: {}, algorithm_id: id, data, data_generated: false, notes: null,
      });
      if (!r.ok) throw new Error(`${id}: ${r.error}`);
      const s = mod.init(r.config) as AlgorithmSimState;
      const total = mod.timeline!.stepCount(s);
      const last = activeTrace(s).steps[total - 1];
      const done = last.events.find((e) => e.type === "done");
      expect(done, `${id}: bước cuối không phát done`).toBeTruthy();
      if (done && done.type === "done") {
        expect(done.result.trim().length, `${id}: kết quả rỗng`).toBeGreaterThan(0);
      }
    }
  });
});
