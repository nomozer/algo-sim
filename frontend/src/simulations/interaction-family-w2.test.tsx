import { describe, expect, it, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import { isSearchFamily, searchInteractionOf } from "./domains/algorithm/decision";
import { registerAllSimulations } from "./index";
import { useAppStore } from "../state/store";
import type { AlgorithmSimState } from "./domains/algorithm";
import type { AlgorithmId } from "../core/types";
import type { SimulationEnvelope } from "./types";

registerAllSimulations();

/**
 * INTERACTION-FAMILY WAVE 2 — CỤM TÌM KIẾM.
 *
 * Hai target dùng CHUNG một primitive nhưng KHÁC nhiệm vụ, vì cơ chế ẩn khác
 * nhau: tuần tự nhắm CHI PHÍ, nhị phân nhắm VÙNG BỊ LOẠI. Test viết theo cụm
 * ở chỗ dùng chung, và tách ở chỗ hai bài thật sự khác.
 */

/** Dãy CHƯA sắp — hợp lệ cho tuần tự. */
const ARR = [7.5, 9, 6.5, 8, 5.5, 8.5, 7, 6];
/** Dãy ĐÃ sắp — bắt buộc cho nhị phân (tiền đề). */
const SORTED = [...ARR].sort((a, b) => a - b);
/** Dãy đã sắp CÓ PHẦN TỬ TRÙNG — dùng cho chính sách trùng lặp. */
const DUPES = [2, 5, 5, 5, 9];

function build(id: AlgorithmId, data: Record<string, unknown>) {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: { summary: "s", input: "i", output: "o" },
    algorithm_id: id,
    data,
    data_generated: false,
    notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) };
}

const at = (s: AlgorithmSimState, c: number): AlgorithmSimState => ({ ...s, cursor: c });

function firstDecision(s: AlgorithmSimState): number {
  for (let i = 0; i < s.trace.steps.length; i += 1) {
    if (searchInteractionOf(at(s, i))) return i;
  }
  throw new Error("không có bước quyết định");
}

const LINEAR = { array: ARR, target: 8 };
const BINARY = { array: SORTED, target: 8 };

/* ── 1. MỘT PRIMITIVE, HAI NHIỆM VỤ ──────────────────────────────────────── */

describe("W2 · một primitive phục vụ hai thuật toán tìm kiếm", () => {
  it("cả hai target sinh được model; target ngoài cụm thì không", () => {
    for (const [id, data] of [["linear_search", LINEAR], ["binary_search", BINARY]] as const) {
      const { state } = build(id as AlgorithmId, data);
      expect(searchInteractionOf(at(state, firstDecision(state))), id).not.toBeNull();
      expect(isSearchFamily(id)).toBe(true);
    }
    for (const id of ["find_max", "count_if", "bubble_sort"] as AlgorithmId[]) {
      expect(isSearchFamily(id), id).toBe(false);
      const extra = id === "count_if"
        ? { array: ARR, condition: { op: ">=", value: 7 } }
        : id === "bubble_sort" ? { array: ARR, order: "asc" } : { array: ARR };
      const { state } = build(id, extra);
      for (let i = 0; i < state.trace.steps.length; i += 1) {
        expect(searchInteractionOf(at(state, i)), `${id}#${i}`).toBeNull();
      }
    }
  });

  it("tuần tự: hai hành động tìm-thấy / tiếp-tục, KÈM khối chi phí", () => {
    const { state } = build("linear_search", LINEAR);
    const m = searchInteractionOf(at(state, firstDecision(state)))!;
    expect(m.actions.map((a) => a.semanticAction)).toEqual(["found", "continue"]);
    expect(m.actions.map((a) => a.visualRole)).toEqual(["current-item", "continue-region"]);
    expect(m.cost).toBeDefined();
    expect(m.cost!.worstCaseComparisons).toBe(ARR.length);
    expect(m.activeRange).toBeUndefined();
  });

  it("nhị phân: hành động KHÔNG GIAN + vùng xét, KHÔNG có khối chi phí", () => {
    const { state } = build("binary_search", BINARY);
    const m = searchInteractionOf(at(state, firstDecision(state)))!;
    expect(m.cost).toBeUndefined();
    expect(m.activeRange).toBeDefined();
    expect(m.activeRange!.left).toBe(0);
    expect(m.activeRange!.right).toBe(SORTED.length - 1);
    for (const a of m.actions) {
      expect(["left-region", "middle-item", "right-region"]).toContain(a.visualRole);
    }
  });
});

/* ── 2. CHI PHÍ DẪN XUẤT, KHÔNG CHẠY LẠI THUẬT TOÁN ──────────────────────── */

describe("W2 · chi phí tìm kiếm tuần tự dẫn xuất từ dữ liệu canonical", () => {
  it("đã so sánh = vars.i + 1; chưa xét = n − đã so sánh; xấu nhất = n", () => {
    const { state } = build("linear_search", LINEAR);
    let seen = 0;
    for (let i = 0; i < state.trace.steps.length; i += 1) {
      const m = searchInteractionOf(at(state, i));
      if (!m) continue;
      seen += 1;
      const vi = state.trace.steps[i].snapshot.vars["i"] as number;
      expect(m.cost!.comparisonsDone, `bước ${i}`).toBe(vi + 1);
      expect(m.cost!.remainingCandidates).toBe(ARR.length - (vi + 1));
      expect(m.cost!.worstCaseComparisons).toBe(ARR.length);
    }
    expect(seen).toBeGreaterThan(1);
  });

  it("chi phí TĂNG dần theo bước — học sinh thấy được cái giá của việc duyệt", () => {
    const { state } = build("linear_search", LINEAR);
    const done: number[] = [];
    for (let i = 0; i < state.trace.steps.length; i += 1) {
      const m = searchInteractionOf(at(state, i));
      if (m) done.push(m.cost!.comparisonsDone);
    }
    for (let k = 1; k < done.length; k += 1) expect(done[k]).toBeGreaterThan(done[k - 1]);
  });
});

/* ── 3. ĐẢO NGHĨA: "LOẠI NỬA NÀO" ↔ "TÌM TIẾP Ở ĐÂU" ─────────────────────── */

describe("W2 · nhị phân — ánh xạ loại-nửa sang tìm-tiếp KHÔNG được đảo sai", () => {
  /* `binaryDecision` hỏi "phần nào BỊ LOẠI": option `left` = nửa TRÁI bị loại,
     tức việc tìm kiếm đi tiếp sang PHẢI. Ánh xạ tên-sang-tên (`left→search-left`)
     sẽ dạy học sinh ngược hẳn cơ chế. Đây là test đắt giá nhất của wave. */
  it("option 'left' (nửa trái bị loại) phải mang nghĩa search-right", () => {
    const { state } = build("binary_search", BINARY);
    const m = searchInteractionOf(at(state, firstDecision(state)))!;
    const left = m.actions.find((a) => a.id === "left");
    const right = m.actions.find((a) => a.id === "right");
    if (left) {
      expect(left.semanticAction).toBe("search-right");
      expect(left.visualRole).toBe("right-region");
      expect(left.label).toContain("PHẢI");
    }
    if (right) {
      expect(right.semanticAction).toBe("search-left");
      expect(right.visualRole).toBe("left-region");
      expect(right.label).toContain("TRÁI");
    }
    expect(left || right).toBeTruthy();
  });

  it("id hành động vẫn khớp option engine ⇒ chấm qua đúng predict.check", () => {
    for (const [id, data] of [["linear_search", LINEAR], ["binary_search", BINARY]] as const) {
      const { mod, state } = build(id as AlgorithmId, data);
      const cur = at(state, firstDecision(state));
      const m = searchInteractionOf(cur)!;
      const optionIds = mod.predict!.challenge(cur)!.options.map((o) => o.id).sort();
      expect(m.actions.map((a) => a.id).sort(), id).toEqual(optionIds);
    }
  });

  it("đúng một hành động được chấm correct, phần còn lại incorrect", () => {
    for (const [id, data] of [["linear_search", LINEAR], ["binary_search", BINARY]] as const) {
      const { mod, state } = build(id as AlgorithmId, data);
      const cur = at(state, firstDecision(state));
      const m = searchInteractionOf(cur)!;
      const verdicts = m.actions.map((a) => mod.predict!.check(cur, a.id).verdict);
      expect(verdicts.filter((v) => v === "correct").length, id).toBe(1);
    }
  });
});

/* ── 4. MODEL KHÔNG MANG ĐÁP ÁN ──────────────────────────────────────────── */

describe("W2 · renderer không biết đáp án", () => {
  it("model không có correctActionId / evidence / resultIndex", () => {
    for (const [id, data] of [["linear_search", LINEAR], ["binary_search", BINARY]] as const) {
      const { state } = build(id as AlgorithmId, data);
      const keys = Object.keys(
        searchInteractionOf(at(state, firstDecision(state)))! as unknown as Record<string, unknown>,
      );
      for (const forbidden of ["correctActionId", "evidence", "resultIndex", "expectedId"]) {
        expect(keys, `${id}: ${forbidden}`).not.toContain(forbidden);
      }
    }
  });

  it("component không tự so sánh, không tự quyết định trái/phải", () => {
    const src = readFileSync(
      new URL("../components/SearchActionZone.tsx", import.meta.url), "utf-8",
    ).replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
    expect(src).not.toContain("expectedId");
    expect(src).not.toMatch(/===\s*target/);
    expect(src).not.toMatch(/[<>]=?\s*targetValue/);
    expect(src).toContain("onAct(a.id)");
  });

  it("hành động sai không đụng state canonical", () => {
    for (const [id, data] of [["linear_search", LINEAR], ["binary_search", BINARY]] as const) {
      const { mod, state } = build(id as AlgorithmId, data);
      const cur = at(state, firstDecision(state));
      const before = JSON.stringify(cur);
      for (const a of searchInteractionOf(cur)!.actions) mod.predict!.check(cur, a.id);
      expect(JSON.stringify(cur), id).toBe(before);
    }
  });
});

/* ── 5. TIỀN ĐỀ VÀ CHÍNH SÁCH PHẦN TỬ TRÙNG ──────────────────────────────── */

describe("W2 · tiền đề dãy đã sắp được NÓI RA cho học sinh", () => {
  it("nhị phân nêu tiền đề; tuần tự thì không (nó không có tiền đề nào)", () => {
    const bin = build("binary_search", BINARY);
    const lin = build("linear_search", LINEAR);
    expect(searchInteractionOf(at(bin.state, firstDecision(bin.state)))!.precondition)
      .toContain("sắp xếp tăng dần");
    expect(searchInteractionOf(at(lin.state, firstDecision(lin.state)))!.precondition).toBeNull();
  });

  it("tiền đề hiện trên sân khấu, không nằm im trong validator", () => {
    const { config, state } = build("binary_search", BINARY);
    const html = renderToString(
      <AlgorithmWorkspace config={config} state={at(state, firstDecision(state))}
        busy={false} dispatch={() => {}} />,
    );
    /* W4B-2D: tiền đề KHÔNG còn sống trong vùng cam kết. Cổng Thí nghiệm ẩn
       vùng đó ở Quan sát, nên nếu tiền đề vẫn nằm bên trong thì nó biến mất
       theo — cổng lấy mất một dữ kiện thuần quan sát (§29). Nay nó là
       `SearchPrecondition` riêng, và đây là khẳng định MẠNH HƠN bản cũ: tiền đề
       phải đọc được NGAY Ở QUAN SÁT, khi chưa hề mở công cụ nào. */
    expect(html, "Quan sát mất tiền đề").toContain("search-precondition");
    expect(html).toContain("sắp xếp tăng dần");
    expect(html, "vùng cam kết chưa bị gác").not.toContain("search-action");
  });

  it("tiền đề chỉ nói MỘT lần — teaser thí nghiệm không nhắc lại", () => {
    /* Ảnh nghiệm thu Chrome bắt được: tiền đề hiện cả trong vùng hành động lẫn
       trong teaser "Tìm nhị phân chỉ đúng khi dãy đã được sắp thứ tự…" — cùng
       một ý, hai chỗ, trên một màn hình. */
    const { config, state } = build("binary_search", BINARY);
    const html = renderToString(
      <AlgorithmWorkspace config={config} state={at(state, firstDecision(state))}
        busy={false} dispatch={() => {}} />,
    );
    const text = html.replace(/<[^>]+>/g, " ");
    const hits = text.split("chỉ đúng khi dãy").length - 1;
    expect(hits).toBe(1);
  });
});

describe("W2 · chính sách phần tử trùng", () => {
  it("FIRST_MATCH — tuần tự luôn dừng ở vị trí xuất hiện SỚM NHẤT", () => {
    const { state } = build("linear_search", { array: DUPES, target: 5 });
    const last = state.trace.steps[state.trace.steps.length - 1];
    const found = Object.entries(last.snapshot.marks).filter(([, m]) => m === "found");
    expect(found.length).toBe(1);
    expect(Number(found[0][0])).toBe(DUPES.indexOf(5)); // = 1
  });

  it("ANY_MATCH_BY_MIDPOINT — nhị phân trả MỘT vị trí khớp, không hứa vị trí đầu", () => {
    const { state } = build("binary_search", { array: DUPES, target: 5 });
    const last = state.trace.steps[state.trace.steps.length - 1];
    const found = Object.entries(last.snapshot.marks).filter(([, m]) => m === "found");
    expect(found.length).toBe(1);
    const idx = Number(found[0][0]);
    // giá trị TẠI vị trí đó đúng là giá trị cần tìm…
    expect(DUPES[idx]).toBe(5);
    // …nhưng KHÔNG bảo đảm là vị trí đầu tiên: ở fixture này mid rơi vào giữa
    expect(idx).not.toBe(DUPES.indexOf(5));
  });

  it("chuỗi kết quả TRUNG TÍNH — không tuyên bố 'vị trí đầu tiên'", () => {
    const { state } = build("binary_search", { array: DUPES, target: 5 });
    const done = state.trace.steps[state.trace.steps.length - 1].events
      .find((e) => e.type === "done");
    const text = done && done.type === "done" ? done.result : "";
    expect(text).toContain("Tìm thấy");
    expect(text).not.toContain("đầu tiên");
  });
});

/* ── 6. MỘT BƯỚC, MỘT HÌNH THỨC CAM KẾT ──────────────────────────────────── */

describe("W2 · không hiện hai hình thức cam kết cùng lúc", () => {
  it("bước có vùng hành động → presentedInStage true, và không dựng dải nhân quả", () => {
    for (const [id, data] of [["linear_search", LINEAR], ["binary_search", BINARY]] as const) {
      const { mod, config, state } = build(id as AlgorithmId, data);
      const cur = at(state, firstDecision(state));
      expect(mod.predict!.presentedInStage!(cur), id).toBe(true);
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={cur} busy={false} dispatch={() => {}} />,
      );
      /* W4B-2D — BẤT BIẾN ĐỔI HÌNH, KHÔNG YẾU ĐI.
         Bản cũ: "có vùng hành động ⇒ có `search-action`, không dải nhân quả".
         Nay hai bài này gác cổng, nên ở QUAN SÁT đúng ra phải là điều NGƯỢC
         LẠI: không vùng cam kết, mà quan hệ thì Ở LẠI. Thứ được giữ nguyên là
         cái đáng giữ — KHÔNG BAO GIỜ dựng cả hai cùng lúc. Bản render có mở
         Thí nghiệm do runner trình duyệt phủ (`labOpen` là useState cục bộ,
         SSR luôn thấy false — ARCHITECTURE_MAP §8 #13). */
      const zone = html.includes('aria-label="Thao tác với bước tìm kiếm"');
      /* W4B-2V: quan hệ + chip trạng thái nay sống ở `.search-observe`, LUÔN
         hiện. Dải nhân quả không còn dựng cho họ này ⇒ hai kênh không nói cùng
         một điều nữa. Bất biến giữ nguyên tinh thần: bước quyết định không bao
         giờ trống, và không bao giờ có hai kênh trùng. */
      const observe = html.includes("search-observe");
      expect(observe, `${id}: mất khối trạng thái quan sát`).toBe(true);
      expect(html.includes("decision-strip"), `${id}: dựng hai kênh quan hệ`).toBe(false);
      expect(zone && observe && html.includes("decision-strip"), `${id}: ba kênh`).toBe(false);
      expect(zone, `${id}: bài đã gác cổng mà Quan sát vẫn bày cam kết`).toBe(false);
    }
  });

  it("bước cuối không phải điểm quyết định → trả lại UI dùng chung", () => {
    const { mod, state } = build("linear_search", LINEAR);
    expect(mod.predict!.presentedInStage!(at(state, state.trace.steps.length - 1))).toBe(false);
  });
});

/* ── 7. VÒNG LẶP QUA STORE ───────────────────────────────────────────────── */

describe("W2 · nộp qua store không đụng mô phỏng canonical", () => {
  beforeEach(() => useAppStore.getState().reset());

  it("chốt hành động → prediction có kết quả, active.state nguyên vẹn", () => {
    const env: SimulationEnvelope = {
      status: "ok", simulation_id: "algorithm.binary_search", domain: "algorithm",
      visual_mode: "2d", title: "t", description: null, notes: null,
      config: {
        problem: { summary: "s", input: "i", output: "o" },
        algorithm_id: "binary_search", data: BINARY, data_generated: false, notes: null,
      },
    };
    useAppStore.getState().loadEnvelope(env);
    const s0 = useAppStore.getState().active!.state as AlgorithmSimState;
    useAppStore.getState().goToStep(firstDecision(s0));

    const before = JSON.stringify(useAppStore.getState().active!.state);
    const m = searchInteractionOf(useAppStore.getState().active!.state as AlgorithmSimState)!;
    useAppStore.getState().submitPrediction(m.actions[0].id);

    expect(useAppStore.getState().prediction).not.toBeNull();
    expect(JSON.stringify(useAppStore.getState().active!.state)).toBe(before);
  });
});
