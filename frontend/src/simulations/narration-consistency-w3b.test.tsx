import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { NarrationSlot } from "../components/SimulationWorkspace";
import { makeAlgorithmModule } from "./domains/algorithm";
import {
  hasStageInteraction,
  scanInteractionOf,
  searchInteractionOf,
} from "./domains/algorithm/decision";
import type { AlgorithmSimState } from "./domains/algorithm";
import { ALGORITHM_IDS, type AlgorithmId } from "../core/types";

/**
 * WAVE 3B §5 — HAI LỖI NARRATION, HAI CONTRACT ĐỘC LẬP.
 *
 * A. INDEX_VOCABULARY_CONSISTENCY — `elem()` cũ trả `a[1] = 9` khi đề không có
 *    nhãn, trong khi mọi bề mặt khác nói "vị trí 3". Hai cách đếm hiện cùng lúc
 *    trên một màn hình, và ở hai câu thì nằm cạnh nhau trong CÙNG một câu
 *    ("là a[3] = 11, ở vị trí thứ 4"). Lỗi này CHỈ có ở nhánh không-nhãn — nên
 *    mọi test dưới đây chạy CẢ HAI nhánh, không chỉ nhánh dễ thấy.
 *
 * B. DECISION_FACT_DUPLICATION — ở bước có vùng hành động, vùng đó đã sở hữu
 *    ứng viên/phép so sánh/biến tích luỹ; khe thuyết minh kể lại đúng ba thứ ấy.
 *
 * VÌ SAO KHÔNG DÙNG `narration.includes(stateLine)`: hai chuỗi không bao giờ
 * giống nhau nguyên văn, nên phép so sánh chuỗi luôn XANH mà lỗi còn nguyên
 * (đã tự mắc đúng bẫy này ở W3B-1). Test phải so DỮ KIỆN lấy từ interaction
 * model, trên fixture có các giá trị số phân biệt để không có trùng token.
 */

/** Giá trị PHÂN BIỆT ĐÔI MỘT — token trùng nhau thì phép so dữ kiện vô nghĩa. */
const ARR = [4, 9, 2, 11, 7, 5];
const SORTED = [2, 4, 5, 7, 9, 11];
const LABELS = ["An", "Bình", "Chi", "Dũng", "Hà", "Lan"];

const EXTRA: Record<string, Record<string, unknown>> = {
  count_if: { condition: { op: ">=", value: 7 } },
  sum_if: { condition: { op: ">=", value: 7 } },
  linear_search: { target: 11 },
  binary_search: { array: SORTED, target: 7 },
  bubble_sort: { order: "asc" },
  insertion_sort: { order: "asc" },
  selection_sort: { order: "asc" },
};

function build(id: AlgorithmId, withLabels: boolean) {
  const mod = makeAlgorithmModule(id);
  const extra = EXTRA[id] ?? {};
  const array = (extra.array as number[] | undefined) ?? ARR;
  const r = mod.validateConfig({
    problem: { summary: "s", input: "i", output: "o" },
    algorithm_id: id,
    data: { array, ...extra, ...(withLabels ? { labels: LABELS } : {}) },
    data_generated: false,
    notes: null,
  });
  if (!r.ok) throw new Error(`${id} (labels=${withLabels}): ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) };
}

const at = (s: AlgorithmSimState, cursor: number): AlgorithmSimState => ({ ...s, cursor });

/** Mọi chuỗi hiện ra với học sinh, của mọi bước. */
function shownTexts(id: AlgorithmId, withLabels: boolean): string[] {
  const { mod, config, state } = build(id, withLabels);
  const out: string[] = [];
  for (let i = 0; i < state.trace.steps.length; i += 1) {
    const n = mod.narrate!(at(state, i), config);
    if (n) out.push(n.text);
    const done = state.trace.steps[i].events.find((e) => e.type === "done");
    if (done && done.type === "done") out.push(done.result);
  }
  return out;
}

const BOTH: Array<[string, boolean]> = [["không nhãn", false], ["có nhãn", true]];

/* ══ A. INDEX VOCABULARY ═══════════════════════════════════════════════════ */

describe("W3B §5.1 · cách gọi vị trí nhất quán", () => {
  it("(1) nhánh KHÔNG NHÃN: không còn chỉ số 0-based nào lọt ra bề mặt học sinh", () => {
    for (const id of ALGORITHM_IDS) {
      for (const text of shownTexts(id, false)) {
        expect(text, `${id}: "${text}"`).not.toMatch(/a\[\d+\]/);
      }
    }
  });

  it("(2) nhánh CÓ NHÃN: câu nào gọi tên phần tử thì kèm giá trị, không thêm chỉ số thừa", () => {
    for (const id of ALGORITHM_IDS) {
      for (const text of shownTexts(id, true)) {
        expect(text, `${id}: "${text}"`).not.toMatch(/a\[\d+\]/);
        // Câu dùng nhãn phải mang theo giá trị — nhãn trần không nói được gì
        // về dữ liệu, mà đây là bề mặt duy nhất nối đề bài với sân khấu.
        for (const l of LABELS) {
          if (!text.includes(`${l} (`)) continue;
          expect(text, `${id}: "${text}" — nhãn không kèm giá trị`).toMatch(
            new RegExp(`${l} \\(\\d`),
          );
        }
      }
    }
  });

  it("(2b) đề CÓ NHÃN: tên phần tử vẫn còn trên bề mặt học sinh sau khi ẩn thuyết minh", () => {
    /* §5.2 ẩn thuyết minh ở bước quyết định — mà với đề có nhãn, đó từng là câu
       DUY NHẤT gọi tên phần tử. Dữ kiện phải CHUYỂN sang vùng hành động, không
       được biến mất: nếu không, học sinh đọc "Phần tử vị trí 2" trong khi cột
       trên sân khấu ghi "Bình". */
    for (const id of ["find_max", "find_min", "count_if", "sum_if"] as AlgorithmId[]) {
      const { state } = build(id, true);
      let named = 0;
      for (let i = 0; i < state.trace.steps.length; i += 1) {
        const m = scanInteractionOf(at(state, i));
        if (!m) continue;
        if (LABELS.some((l) => m.candidateLabel.includes(l))) named += 1;
      }
      expect(named, `${id}: vùng hành động không gọi tên phần tử nào`).toBeGreaterThan(0);
    }
  });

  it("(3) không câu nào nói vị trí hai lần (không lặp vị trí)", () => {
    for (const [name, withLabels] of BOTH) {
      for (const id of ALGORITHM_IDS) {
        for (const text of shownTexts(id, withLabels)) {
          const hits = text.match(/vị trí(?: thứ)? \d+/g) ?? [];
          const distinct = new Set(hits);
          // hai lần nói vị trí chỉ chấp nhận được khi là HAI vị trí khác nhau
          // (vd "từ vị trí 1 đến vị trí 6"), không phải nhắc lại cùng một chỗ.
          expect(hits.length, `${id}/${name}: "${text}"`).toBe(distinct.size);
        }
      }
    }
  });

  it("(3b) vị trí hiển thị luôn đếm TỪ 1 — không bao giờ có 'vị trí 0'", () => {
    for (const [name, withLabels] of BOTH) {
      for (const id of ALGORITHM_IDS) {
        for (const text of shownTexts(id, withLabels)) {
          expect(text, `${id}/${name}: "${text}"`).not.toMatch(/vị trí(?: thứ)? 0\b/);
        }
      }
    }
  });
});

/* ══ B. DECISION FACT DUPLICATION ══════════════════════════════════════════ */

/** Dữ kiện quyết định LẤY TỪ MODEL, không chép tay. */
function decisionFacts(state: AlgorithmSimState): string[] | null {
  const scan = scanInteractionOf(state);
  if (scan) return [scan.candidateValue, scan.accumulatorValue, scan.expression];
  const search = searchInteractionOf(state);
  if (search) return [search.currentValue, search.targetValue];
  return null;
}

describe("W3B §5.2 · dữ kiện quyết định chỉ thuộc MỘT chỗ", () => {
  it("(4)(5)(6) bước có vùng hành động: khe thuyết minh không mang lại dữ kiện của vùng đó", () => {
    for (const [name, withLabels] of BOTH) {
      for (const id of ALGORITHM_IDS) {
        const { mod, config, state } = build(id, withLabels);
        for (let i = 0; i < state.trace.steps.length; i += 1) {
          const cur = at(state, i);
          const facts = decisionFacts(cur);
          if (!facts) continue;

          const n = mod.narrate!(cur, config);
          if (n === null) continue; // không dựng khe ⇒ không thể lặp
          for (const f of facts) {
            expect(n.text, `${id}/${name} bước ${i}: lặp dữ kiện "${f}"`).not.toContain(f);
          }
        }
      }
    }
  });

  it("(6b) phép đo đi qua DỮ KIỆN — fixture có giá trị phân biệt đôi một", () => {
    // Nếu fixture có giá trị trùng, một token có thể khớp vì lý do khác và test
    // (4)(5) sẽ đỏ/xanh vì nhầm lẫn chứ không vì lỗi thật.
    expect(new Set(ARR).size).toBe(ARR.length);
    expect(new Set(SORTED).size).toBe(SORTED.length);
    expect(new Set(LABELS).size).toBe(LABELS.length);
  });

  it("(7) bước KHÔNG có vùng hành động vẫn có thuyết minh, và không rỗng", () => {
    /* W4B-2T — MỘT NGOẠI LỆ CÓ TÊN: BƯỚC CUỐI.
     *
     * Ý của luật này là *"không để bước nào câm khi không có bề mặt nào khác kể
     * nó"*. Ở bước `done`, `.result-banner` LÀ bề mặt kể nó — nên tiền đề "không
     * có vùng hành động ⇒ không ai nói" không còn đúng ở đúng bước ấy. Đo được
     * ở cả 8 bài: dải kết quả và khe thuyết minh in cùng một câu (4 bài trùng
     * từng ký tự). Xem `processLeadOf`.
     *
     * Nới đúng một bước, và ca "câm" vẫn bị chặn ở phần dưới: bước cuối phải có
     * NGƯỜI KỂ, chỉ là không nhất thiết là khe thuyết minh. */
    for (const [name, withLabels] of BOTH) {
      for (const id of ALGORITHM_IDS) {
        const { mod, config, state } = build(id, withLabels);
        let described = 0;
        for (let i = 0; i < state.trace.steps.length; i += 1) {
          const cur = at(state, i);
          if (hasStageInteraction(cur)) continue;
          const step = state.trace.steps[i];
          const done = step.events.find((e) => e.type === "done");
          const n = mod.narrate!(cur, config);

          if (done && done.type === "done") {
            // Bước cuối: dải kết quả sở hữu câu kết. Khe thuyết minh chỉ được
            // giữ phần TIẾN TRÌNH, và tuyệt đối không lặp lại kết quả.
            expect(done.result.trim().length, `${id}/${name}: bước cuối không có người kể`)
              .toBeGreaterThan(0);
            if (n !== null) {
              expect(n.text, `${id}/${name}: thuyết minh lặp lại kết quả ở bước cuối`)
                .not.toContain(done.result);
              expect(n.text.trim().length).toBeGreaterThan(0);
              described += 1;
            }
            continue;
          }

          expect(n, `${id}/${name} bước ${i}: mất thuyết minh ở bước không có vùng hành động`)
            .not.toBeNull();
          expect(n!.text.trim().length, `${id}/${name} bước ${i}: chuỗi rỗng`).toBeGreaterThan(0);
          described += 1;
        }
        expect(described, `${id}/${name}: không còn bước nào có thuyết minh`).toBeGreaterThan(0);
      }
    }
  });

  it("(7c) KHÔNG TRÙNG NGHĨA Ở BƯỚC CUỐI — kết quả chỉ có MỘT chủ sở hữu", () => {
    /* Đây là bất biến mới của W4B-2T, phát biểu trên TOÀN họ thuật toán chứ
       không trên một bài làm chứng. Trước wave này cả 8 bài đều đỏ. */
    for (const id of ALGORITHM_IDS) {
      const { mod, config, state } = build(id, true);
      const last = state.trace.steps.length - 1;
      const step = state.trace.steps[last];
      const done = step.events.find((e) => e.type === "done");
      if (!done || done.type !== "done") continue;
      const n = mod.narrate!(at(state, last), config);
      if (n === null) continue; // thuyết minh nhả hẳn — dải kết quả kể một mình
      expect(n.text, `${id}: kết quả in hai lần ở bước cuối`).not.toContain(done.result);
    }
  });

  it("(7b) null → shell KHÔNG dựng khe (không để lại khe trắng)", () => {
    // Chuỗi rỗng và null trông giống nhau trong code, khác hẳn trên màn hình.
    expect(renderToString(<NarrationSlot narration={null} />)).toBe("");
    expect(renderToString(<NarrationSlot narration={{ text: "x", fromLearner: false }} />))
      .toContain("narration-bar");
  });

  it("(8) lọc ở TRÌNH BÀY — engine narration thô và cấu trúc trace không đổi", () => {
    for (const [name, withLabels] of BOTH) {
      for (const id of ALGORITHM_IDS) {
        const { mod, config, state } = build(id, withLabels);

        /* Dấu vân tay CẤU TRÚC: mọi thứ engine sở hữu, không gồm chữ trình bày. */
        const digest = (s: AlgorithmSimState) => JSON.stringify(s.trace.steps.map((st) => ({
          line: st.line,
          events: st.events,
          array: st.snapshot.array,
          vars: st.snapshot.vars,
          marks: st.snapshot.marks,
          ids: st.snapshot.ids,
          narration: st.narration,
        })));

        const before = digest(state);
        for (let i = 0; i < state.trace.steps.length; i += 1) {
          mod.narrate!(at(state, i), config);
        }
        expect(digest(state), `${id}/${name}: narrate() đụng vào state`).toBe(before);

        /* Và ở đúng những bước bị ẩn, chuỗi GỐC của engine vẫn còn nguyên —
           tức là đã LỌC ở tầng trình bày chứ không viết lại engine. (Không
           khẳng định "engine còn câu hỏi": `binary_search` cố ý đặt điểm quyết
           định ở bước LẤY MID, narration trung lập, không phải câu hỏi.) */
        for (let i = 0; i < state.trace.steps.length; i += 1) {
          if (mod.narrate!(at(state, i), config) !== null) continue;
          expect(
            state.trace.steps[i].narration.trim().length,
            `${id}/${name} bước ${i}: engine mất chuỗi gốc khi bị ẩn`,
          ).toBeGreaterThan(0);
        }
      }
    }
  });
});
