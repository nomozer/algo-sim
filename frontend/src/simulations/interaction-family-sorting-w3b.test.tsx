import { describe, expect, it, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { SortActionZone } from "../components/SortActionZone";
import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import {
  decisionPointOf,
  isSortFamily,
  sortInteractionOf,
  stageInteractionsOf,
} from "./domains/algorithm/decision";
import { whatIfDragAllowed, whatIfPolicyOf } from "./domains/algorithm/interaction-policy";
import { registerAllSimulations } from "./index";
import { useAppStore } from "../state/store";
import type { AlgorithmSimState } from "./domains/algorithm";
import { ALGORITHM_IDS, type AlgorithmId } from "../core/types";
import type { SimulationEnvelope } from "./types";

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

const envOf = (id: AlgorithmId): SimulationEnvelope => ({
  status: "ok", simulation_id: `algorithm.${id}`, domain: "algorithm",
  visual_mode: "2d", title: "t", description: null, notes: null,
  config: {
    problem: { summary: "s", input: "i", output: "o" },
    algorithm_id: id, data: { array: ARR, order: "asc" },
    data_generated: false, notes: null,
  },
});

/* ══ 9–12. MODEL + ĐƯỜNG CHẤM ═════════════════════════════════════════════ */

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

  it("(12) engine là bên chấm duy nhất — đúng một đáp án correct", () => {
    for (const id of SORT) {
      const { mod, state } = build(id);
      const cur = at(state, firstSortDecision(state));
      const m = sortInteractionOf(cur)!;
      const verdicts = m.actions.map((a) => mod.predict!.check(cur, a.id).verdict);
      expect(verdicts.filter((v) => v === "correct").length, id).toBe(1);
      expect(verdicts.filter((v) => v === "incorrect").length, id).toBe(1);
    }
  });

  it("(12b) component không tự phán xử, không đọc expectedId", () => {
    const src = readFileSync(
      new URL("../components/SortActionZone.tsx", import.meta.url), "utf-8",
    ).replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
    expect(src).not.toContain("expectedId");
    expect(src).not.toMatch(/===\s*['"]yes['"]/);
    expect(src).toContain("onAct(a.id)");
  });
});

/* ══ 13–17. BẤT BIẾN CỦA ENGINE ═══════════════════════════════════════════ */

describe("W3B-sort · hành động của học sinh không đụng sự thật của engine", () => {
  it("(13)(14)(15) hành động SAI giữ nguyên cursor, trace và snapshot", () => {
    for (const id of SORT) {
      const { mod, state } = build(id);
      const d = firstSortDecision(state);
      const cur = at(state, d);
      const m = sortInteractionOf(cur)!;
      const wrong = m.actions.find(
        (a) => mod.predict!.check(cur, a.id).verdict === "incorrect",
      )!;
      const before = JSON.stringify(cur);

      const r = mod.predict!.check(cur, wrong.id);

      expect(r.verdict, id).toBe("incorrect");
      expect(cur.cursor, id).toBe(d);
      expect(JSON.stringify(cur), id).toBe(before);
    }
  });

  it("(16) hành động ĐÚNG cũng không tự tiến cursor", () => {
    for (const id of SORT) {
      const { mod, state } = build(id);
      const d = firstSortDecision(state);
      const cur = at(state, d);
      const m = sortInteractionOf(cur)!;
      const right = m.actions.find(
        (a) => mod.predict!.check(cur, a.id).verdict === "correct",
      )!;

      mod.predict!.check(cur, right.id);

      expect(cur.cursor, id).toBe(d);
      expect(JSON.stringify(cur.trace), id).toBe(JSON.stringify(state.trace));
    }
  });

  it("(17) bằng chứng KHÔNG có trong DOM trước khi học sinh hành động", () => {
    for (const id of SORT) {
      const { mod, config, state } = build(id);
      const cur = at(state, firstSortDecision(state));
      const m = sortInteractionOf(cur)!;
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={cur} busy={false} dispatch={() => {}} />,
      );
      for (const a of m.actions) {
        const core = mod.predict!.check(cur, a.id).message
          .replace(/^(Chính xác|Chưa đúng)\.\s*/, "");
        expect(core.length, id).toBeGreaterThan(10);
        expect(html, `${id}: lộ "${core}"`).not.toContain(core);
      }
      expect(html, id).not.toContain("Chính xác");
      expect(html, id).not.toContain("Chưa đúng");
    }
  });
});

/* ══ 18–19. BỀ MẶT CAM KẾT + VÒNG ĐỜI PHẢN HỒI ═══════════════════════════ */

describe("W3B-sort · một bề mặt cam kết, phản hồi sống đúng một bước", () => {
  beforeEach(() => useAppStore.getState().reset());

  it("(19) bước có SortActionZone thì KHÔNG dựng PredictionBar lẫn dải nhân quả", () => {
    for (const id of SORT) {
      const { mod, config, state } = build(id);
      const cur = at(state, firstSortDecision(state));
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={cur} busy={false} dispatch={() => {}} />,
      );
      /* W4B-2B §18 — `insertion_sort` là bài PILOT: vùng cam kết nay nằm sau cổng
         Thí nghiệm, mà SSR luôn thấy `labOpen = false`. Hai bài sắp xếp còn lại
         KHÔNG đổi hành vi (§25 — pilot hai bài, không rollout cả họ).
         Kỳ vọng đọc từ chính bản khai policy, không viết tay danh sách id. */
      const gated = whatIfPolicyOf(id as never).experimentGated === true;
      if (gated) {
        expect(html, id).not.toContain('aria-label="Thao tác sắp xếp"');
        // quan hệ ở lại Quan sát dù nút cam kết đã đi vào Thí nghiệm
        expect(html, id).toContain("decision-strip");
      } else {
        expect(html, id).toContain('aria-label="Thao tác sắp xếp"');
        expect(html, id).not.toContain("decision-strip");
      }
      /* KHÔNG đổi: bước này vẫn do sân khấu trình bày ⇒ shell không dựng
         PredictionBar. Cổng là chuyện trình bày, không đụng hợp đồng predict. */
      expect(mod.predict!.presentedInStage!(cur), id).toBe(true);
      expect(stageInteractionsOf(cur), id).toEqual(["sort"]);
    }
  });

  it("(18) phản hồi bị xoá khi Next / Back / scrub / Reset / đổi config", () => {
    for (const id of SORT) {
      const answer = () => {
        useAppStore.getState().loadEnvelope(envOf(id));
        const s0 = useAppStore.getState().active!.state as AlgorithmSimState;
        const d = firstSortDecision(s0);
        useAppStore.getState().goToStep(d);
        const m = sortInteractionOf(useAppStore.getState().active!.state as AlgorithmSimState)!;
        useAppStore.getState().submitPrediction(m.actions[0].id);
        expect(useAppStore.getState().prediction, id).not.toBeNull();
        return d;
      };

      const d = answer();
      useAppStore.getState().nextStep();
      expect(useAppStore.getState().prediction, `${id}: Next`).toBeNull();

      answer();
      useAppStore.getState().prevStep();
      expect(useAppStore.getState().prediction, `${id}: Back`).toBeNull();

      answer();
      useAppStore.getState().goToStep(d + 2);
      expect(useAppStore.getState().prediction, `${id}: scrub`).toBeNull();

      answer();
      useAppStore.getState().resetSim();
      expect(useAppStore.getState().prediction, `${id}: Reset`).toBeNull();
      expect((useAppStore.getState().active!.state as AlgorithmSimState).cursor).toBe(0);

      answer();
      useAppStore.getState().loadEnvelope(envOf("bubble_sort"));
      expect(useAppStore.getState().prediction, `${id}: đổi config`).toBeNull();
    }
  });

  it("(28) tự chạy KHÔNG bị vùng hành động chặn", () => {
    useAppStore.getState().loadEnvelope(envOf("selection_sort"));
    const s0 = useAppStore.getState().active!.state as AlgorithmSimState;
    const d = firstSortDecision(s0);
    useAppStore.getState().goToStep(d);
    const m = sortInteractionOf(useAppStore.getState().active!.state as AlgorithmSimState)!;
    useAppStore.getState().submitPrediction(m.actions[0].id);

    useAppStore.getState().setPlaying(true);
    useAppStore.getState().nextStep();

    expect(useAppStore.getState().playing).toBe(true);
    expect((useAppStore.getState().active!.state as AlgorithmSimState).cursor).toBe(d + 1);
    expect(useAppStore.getState().prediction).toBeNull();
  });
});

/* ══ 22–27. KÉO VÀ CAM KẾT ════════════════════════════════════════════════ */

describe("W3B-sort · kéo là thí nghiệm, nút là cam kết — không lẫn nhau", () => {
  beforeEach(() => useAppStore.getState().reset());

  /** Kéo được hay không: ArrayView chỉ đặt con trỏ "grab" khi `interactive`. */
  const invitesDrag = (html: string) => html.includes("cursor:grab");

  /* LUẬT gating kiểm bằng HÀM THUẦN, không qua SSR: zustand v5 trả
     `getInitialState()` làm server snapshot, nên `renderToString` LUÔN thấy
     `prediction = null` và nửa "sau khi cam kết" không thể quan sát được ở đây
     (ARCHITECTURE_MAP §8 #13 — SSR chỉ đi qua trạng thái đầu). Hành vi thật
     trong trình duyệt do §16 bảo chứng. */
  it("(22)(23) luật: khoá kéo khi còn cam kết chờ, mở lại sau khi đã chốt", () => {
    const base = { policyAllows: true, busy: false, last: false, challengeOpen: true };
    for (const id of SORT) {
      const { state } = build(id);
      const decision = at(state, firstSortDecision(state));

      expect(whatIfDragAllowed(decision, { ...base, answered: false }), `${id}: chưa chốt`)
        .toBe(false);
      expect(whatIfDragAllowed(decision, { ...base, answered: true }), `${id}: đã chốt`)
        .toBe(true);

      // Bước KHÔNG phải điểm quyết định: luật cũ giữ nguyên, không bị siết theo.
      const plain = at(state, 0);
      expect(sortInteractionOf(plain), `${id}: bước 0 không phải điểm quyết định`).toBeNull();
      expect(whatIfDragAllowed(plain, { ...base, answered: false }), `${id}: bước thường`)
        .toBe(true);

      // Các chốt cũ vẫn thắng, kể cả khi đã chốt cam kết.
      expect(whatIfDragAllowed(decision, { ...base, busy: true, answered: true })).toBe(false);
      expect(whatIfDragAllowed(decision, { ...base, last: true, answered: true })).toBe(false);
      expect(whatIfDragAllowed(decision, { ...base, policyAllows: false, answered: true }))
        .toBe(false);

      /* W12 §6 (Policy B) — THỬ THÁCH ĐÓNG thì đúng bước quyết định ấy vẫn kéo
         được, dù chưa chốt gì. Lý do §15 tồn tại là "đừng cho né cam kết", mà
         cam kết chỉ sống trong Thử thách; đóng nó lại thì không còn gì để né.
         Đây cũng là ĐỐI CHỨNG DƯƠNG của lỗi C trong ma trận W12-E: siết lại
         thành chặn-khi-đóng thì dòng này ĐỎ. */
      expect(whatIfDragAllowed(decision, { ...base, challengeOpen: false, answered: false }),
        `${id}: thử thách đóng ⇒ công cụ dùng được`).toBe(true);
    }
  });

  it("(22b) target ngoài cụm sắp xếp KHÔNG bị luật mới siết", () => {
    const base = { policyAllows: true, busy: false, last: false, answered: false, challengeOpen: true };
    const mod = makeAlgorithmModule("find_max");
    const r = mod.validateConfig({
      problem: { summary: "s", input: "i", output: "o" }, algorithm_id: "find_max",
      data: { array: ARR }, data_generated: false, notes: null,
    });
    if (!r.ok) throw new Error(r.error);
    const s = mod.init(r.config);
    for (let i = 0; i < s.trace.steps.length - 1; i += 1) {
      expect(whatIfDragAllowed(at(s, i), base), `find_max bước ${i}`).toBe(true);
    }
  });

  it("(23b) W12 §6 — DOM ở bước quyết định, THỬ THÁCH ĐÓNG: công cụ kéo hiện ra", () => {
    /* TIỀN ĐỀ ĐỔI, có chủ đích — và đây là chỗ ghi lại vì sao.
       Trước W12: bước quyết định KHÔNG mời kéo, kể cả khi không có câu hỏi nào
       đang chờ. Đo trên trình duyệt (ma trận 23×4) cho thấy hệ quả thật: 52/92
       dòng đọc ra "không có affordance", vì `renderToString` và trang thật đều
       dựng ở trạng thái THỬ THÁCH ĐÓNG. Học sinh mở bài ra chỉ thấy ô dự đoán.
       Nay: đóng thử thách ⇒ không có cam kết nào để né ⇒ công cụ phải dùng được.
       Luật hoãn-khi-đang-chờ vẫn sống, kiểm ở (22) trên hàm thuần. */
    for (const id of SORT) {
      const { config, state } = build(id);
      const html = renderToString(
        <AlgorithmWorkspace
          config={config} state={at(state, firstSortDecision(state))}
          busy={false} dispatch={() => {}}
        />,
      );
      expect(invitesDrag(html), `${id}: thử thách đóng mà vẫn không mời kéo`).toBe(true);
    }
  });

  it("(24) trả lời KHÔNG tạo nhánh what-if", () => {
    for (const id of SORT) {
      useAppStore.getState().reset();
      useAppStore.getState().loadEnvelope(envOf(id));
      const s0 = useAppStore.getState().active!.state as AlgorithmSimState;
      useAppStore.getState().goToStep(firstSortDecision(s0));
      const m = sortInteractionOf(useAppStore.getState().active!.state as AlgorithmSimState)!;

      useAppStore.getState().submitPrediction(m.actions[0].id);

      const st = useAppStore.getState().active!.state as AlgorithmSimState;
      expect(st.branch, `${id}: cam kết lại đẻ ra nhánh`).toBeNull();
    }
  });

  it("(25)(26)(27) kéo tạo nhánh · thoát nhánh về đúng chỗ · không nhánh lồng", () => {
    for (const id of SORT) {
      const { mod, state } = build(id);
      const d = firstSortDecision(state);
      const cur = at(state, d);

      const branched = mod.apply!(cur, { type: "whatif_swap", i: 0, j: 1 });
      expect(branched.branch, `${id}: kéo không tạo nhánh`).not.toBeNull();
      expect(branched.branch!.fromStep, id).toBe(d);

      // (27) trong nhánh, kéo tiếp KHÔNG đẻ nhánh lồng
      const again = mod.apply!(branched, { type: "whatif_swap", i: 2, j: 3 });
      expect(again, `${id}: nhánh lồng nhánh`).toBe(branched);

      // (26) thoát nhánh trả về đúng cursor canonical
      const exited = mod.apply!(branched, { type: "exit_branch" });
      expect(exited.branch, id).toBeNull();
      expect(exited.cursor, id).toBe(d);
      expect(JSON.stringify(exited.trace), id).toBe(JSON.stringify(state.trace));
    }
  });
});

/* ══ 29. BÀN PHÍM ═════════════════════════════════════════════════════════
 * Suite chạy trên `node` (không jsdom, wave này không thêm dependency) nên ở
 * đây khoá ĐIỀU KIỆN sinh ra hành vi phím; hành vi thật đo bằng bàn phím thật
 * trong Chrome ở §16.
 */

describe("W3B-sort · bàn phím", () => {
  it("(29) hành động là <button type=\"button\"> thật, không tabindex bẻ thứ tự", () => {
    for (const id of SORT) {
      const { state } = build(id);
      const m = sortInteractionOf(at(state, firstSortDecision(state)))!;
      const html = renderToString(
        <SortActionZone model={m} answered={false} busy={false} onAct={() => {}} feedback={null} />,
      );
      expect(html.split('type="button"').length - 1, id).toBe(m.actions.length);
      expect(html, id).not.toContain('role="button"');
      expect(html, id).not.toContain("tabindex");
      const order = m.actions.map((a) => html.indexOf(a.label));
      expect(order.every((p) => p >= 0), id).toBe(true);
      expect([...order].sort((x, y) => x - y), id).toEqual(order);
    }
  });

  it("(29b) sau khi chốt, nút đã chọn phân biệt được và KHÔNG chỉ bằng màu", () => {
    for (const id of SORT) {
      const { state } = build(id);
      const m = sortInteractionOf(at(state, firstSortDecision(state)))!;
      const picked = m.actions[1].id;
      const html = renderToString(
        <SortActionZone
          model={m} answered busy={false} onAct={() => {}}
          feedback={{ verdict: "correct", message: "…", answerId: picked }}
        />,
      );
      expect(html.split('data-chosen="true"').length - 1, id).toBe(1);
      expect(html.split('data-chosen="false"').length - 1, id).toBe(1);
      expect(html, id).toContain('aria-pressed="true"');
      expect(html, id).toContain("em đã chọn");
      expect(html, id).toContain(m.actions[0].label);
    }
  });
});
