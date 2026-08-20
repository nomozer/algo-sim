import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { makeAlgorithmModule } from "./domains/algorithm";
import {
  decisionPointOf,
  isSortFamily,
  sortInteractionOf,
  stageInteractionsOf,
} from "./domains/algorithm/decision";
import { registerAllSimulations } from "./index";
import type { AlgorithmSimState } from "./domains/algorithm";
import { ALGORITHM_IDS, type AlgorithmId } from "../core/types";

registerAllSimulations();

/**
 * WAVE 3B — CỤM SẮP XẾP, INTERACTION FAMILY CUỐI CÙNG.
 *
 * Ba bài, ba cơ chế, MỘT primitive — giống hệt cách cụm quét dãy và cụm tìm
 * kiếm đã làm. Điều wave này phải chứng minh thêm, và là điều dễ vỡ nhất:
 *
 * KÉO VÀ CAM KẾT KHÔNG ĐƯỢC MANG HAI NGHĨA CÙNG LÚC. Kéo cột đã có nghĩa từ
 * trước (thí nghiệm what-if → fork nhánh). Nếu cam kết cũng là kéo thì cùng một
 * cử chỉ, cùng hai cột, cùng một bước lại cho hai kết cục khác nhau. Nên: cam
 * kết là NÚT và đi qua `predict.check`; kéo giữ nguyên nghĩa thí nghiệm nhưng
 * bị KHOÁ tới khi học sinh đã chốt.
 */

const SORT: AlgorithmId[] = ["bubble_sort", "selection_sort", "insertion_sort"];
const ARR = [4, 9, 2, 11, 7, 5];

function build(id: AlgorithmId) {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: { summary: "s", input: "i", output: "o" },
    algorithm_id: id,
    data: { array: ARR, order: "asc" },
    data_generated: false,
    notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) };
}

const at = (s: AlgorithmSimState, cursor: number): AlgorithmSimState => ({ ...s, cursor });

function firstSortDecision(s: AlgorithmSimState): number {
  for (let i = 0; i < s.trace.steps.length; i += 1) {
    if (sortInteractionOf(at(s, i))) return i;
  }
  throw new Error("không tìm được bước quyết định sắp xếp");
}

/* ══ 9–12b. MÔ HÌNH SẮP XẾP ═══════════════════════════════════════════════
   Đường CHẤM ĐIỂM đã xoá ở Task 10b: W13 gỡ `predict` có chủ đích. */

describe("W3B-sort · một primitive, ba cơ chế", () => {
  it("(9) ba target đều sinh mô hình, mỗi bài đúng `kind` của cơ chế mình", () => {
    const kinds: Record<string, string> = {
      bubble_sort: "compare-pair",
      selection_sort: "select-candidate",
      insertion_sort: "shift-or-stop",
    };
    for (const id of SORT) {
      const { state } = build(id);
      const m = sortInteractionOf(at(state, firstSortDecision(state)))!;
      expect(m, id).not.toBeNull();
      expect(m.kind, id).toBe(kinds[id]);
      expect(m.actions.map((a) => a.tone), id).toEqual(["update", "keep"]);
      expect(m.facts.length, `${id}: không có dữ kiện hiện trạng`).toBeGreaterThan(0);
      for (const a of m.actions) {
        // nói bằng ngôn ngữ CƠ CHẾ, không phải "Có"/"Không"
        expect(a.label, `${id}: ${a.label}`).not.toBe("Có");
        expect(a.label, `${id}: ${a.label}`).not.toBe("Không");
        expect(a.label.length, `${id}: nhãn rỗng`).toBeGreaterThan(5);
      }
    }
  });

  /* ── CHỐNG "VÙNG HÀNH ĐỘNG BIẾN MẤT KHÔNG BÁO" ─────────────────────────
   *
   * Bất biến "≤ 1 mô hình" chỉ bắt được ca THỪA, không bắt được ca THIẾU: nếu
   * `sortInteractionOf` trả `null` ở một bước ĐANG CÓ điểm quyết định — vì
   * engine đổi hình dạng sự kiện, vì thiếu một biến, vì một nhánh `return null`
   * mới — thì vùng hành động lặng lẽ mất và học sinh mất luôn chỗ cam kết, mà
   * mọi test hiện có vẫn xanh. Đây là rủi ro tôi đã tự nêu ở báo cáo W3B (§Y.3).
   *
   * Quét MỌI bước của cả ba target và khoá chiều ngược lại: có DecisionPoint ⇒
   * phải có ĐÚNG MỘT mô hình sân khấu, và id hành động phải khớp option.
   */
  it("(9d) MỌI bước có DecisionPoint đều có ĐÚNG MỘT mô hình sân khấu", () => {
    for (const id of SORT) {
      const { state } = build(id);
      let decisions = 0;

      for (let i = 0; i < state.trace.steps.length; i += 1) {
        const cur = at(state, i);
        const d = decisionPointOf(cur);
        if (!d) continue;
        decisions += 1;

        const m = sortInteractionOf(cur);
        expect(m, `${id} bước ${i}: có DecisionPoint nhưng KHÔNG có mô hình sắp xếp`)
          .not.toBeNull();

        const present = stageInteractionsOf(cur);
        expect(present, `${id} bước ${i}: ${present.join("+")}`).toEqual(["sort"]);

        expect(m!.actions.map((a) => a.id), `${id} bước ${i}: action id lệch option`)
          .toEqual(d.options.map((o) => o.id));
        expect(m!.actions.length, `${id} bước ${i}`).toBe(d.options.length);
      }

      // Bài không có điểm quyết định nào thì phép quét trên chẳng khoá được gì.
      expect(decisions, `${id}: không quét được bước quyết định nào`).toBeGreaterThan(0);
    }
  });

  it("(9e) chiều ngược lại: có mô hình sắp xếp ⇒ phải có DecisionPoint", () => {
    for (const id of SORT) {
      const { state } = build(id);
      for (let i = 0; i < state.trace.steps.length; i += 1) {
        const cur = at(state, i);
        if (!sortInteractionOf(cur)) continue;
        expect(decisionPointOf(cur), `${id} bước ${i}: mô hình không có điểm quyết định`)
          .not.toBeNull();
      }
    }
  });

  it("(9b) target NGOÀI cụm không sinh mô hình sắp xếp", () => {
    for (const id of ALGORITHM_IDS) {
      if (SORT.includes(id)) continue;
      expect(isSortFamily(id), id).toBe(false);
    }
  });

  it("(9c) selection nêu ranh giới phần chưa sắp; insertion nêu quân bài đang giữ", () => {
    const sel = build("selection_sort");
    const mSel = sortInteractionOf(at(sel.state, firstSortDecision(sel.state)))!;
    expect(mSel.facts.some((f) => f.label.includes("chưa sắp"))).toBe(true);

    const ins = build("insertion_sort");
    const mIns = sortInteractionOf(at(ins.state, firstSortDecision(ins.state)))!;
    expect(mIns.facts.some((f) => f.label.includes("Đang giữ"))).toBe(true);
  });

  it("(10) mô hình KHÔNG mang đáp án dưới bất kỳ tên nào", () => {
    for (const id of SORT) {
      const { state } = build(id);
      const m = sortInteractionOf(at(state, firstSortDecision(state)))! as unknown as
        Record<string, unknown>;
      for (const forbidden of ["expectedId", "correctActionId", "evidence", "result"]) {
        expect(Object.keys(m), `${id}: lộ ${forbidden}`).not.toContain(forbidden);
      }
    }
  });

  it("(11) action id KHỚP option id của DecisionPoint", () => {
    for (const id of SORT) {
      const { state } = build(id);
      const cur = at(state, firstSortDecision(state));
      const m = sortInteractionOf(cur)!;
      expect(m.actions.map((a) => a.id), id).toEqual(decisionPointOf(cur)!.options.map((o) => o.id));
    }
  });

  /* (12) "engine là bên chấm duy nhất" ĐÃ XOÁ 2026-08-21 (Task 10b): nó kiểm
     `predict.check(...).verdict`, tức đường CHẤM ĐIỂM mà W13 gỡ có chủ đích.
     Không có bên chấm nào nữa thì không còn gì để khoá là "duy nhất". */

  it("(12b) component không tự phán xử, không đọc expectedId", () => {
    const src = readFileSync(
      new URL("../components/SortActionZone.tsx", import.meta.url), "utf-8",
    ).replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
    expect(src).not.toContain("expectedId");
    expect(src).not.toMatch(/===\s*['"]yes['"]/);
    /* `onAct(a.id)` ĐÃ BỎ khỏi assertion 2026-08-21 (Task 10b): W13 gỡ luôn
       hàng nút hành động, nên component nay chỉ TRÌNH BÀY trạng thái sắp xếp.
       Không còn nút thì không còn gì để "phát đúng id" — nhưng hai assertion
       trên vẫn giữ nguyên giá trị: component KHÔNG được biết đáp án. */
  });
});
