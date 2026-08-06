import { describe, expect, it, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { arrayLegendItems } from "../components/ArrayView";
import { ScanActionZone } from "../components/ScanActionZone";
import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import { isScanFamily, scanInteractionOf } from "./domains/algorithm/decision";
import { registerAllSimulations } from "./index";
import { useAppStore } from "../state/store";
import type { AlgorithmSimState } from "./domains/algorithm";
import { ALGORITHM_IDS, type AlgorithmId } from "../core/types";
import type { SimulationEnvelope } from "./types";

registerAllSimulations();

/**
 * WAVE 3B-1 — NGỮ NGHĨA CHÚ GIẢI + KHẢ DỤNG CỦA VÙNG HÀNH ĐỘNG.
 *
 * Hai lỗi wave này đóng, cả hai đều đo được trong Chrome trước khi sửa:
 *
 * W3A-001/002 — `found` là MỘT mark canonical phục vụ nhiều cơ chế khác nhau,
 * nhưng chú giải gọi nó là "đã tìm thấy" ở mọi bài. `count_if` đánh dấu phần tử
 * nó vừa ĐẾM, `sum_if` phần tử vừa CỘNG, `find_max` phần tử được CHỌN làm max —
 * không bài nào đi tìm một giá trị cho trước. Nhãn sai dạy sai cơ chế.
 *
 * W3B1-SEL — chốt hành động xong thì hai nút chỉ khác nhau ở `disabled`; học
 * sinh mất dấu lựa chọn của chính mình, nên nửa sau của vòng lặp học tập
 * (đối chiếu cam kết với phán quyết) không thực hiện được.
 *
 * Cả hai sửa ở TẦNG TRÌNH BÀY. Mark canonical, trace, timeline và đường chấm
 * `predict.check` không đổi một ký tự — phần lớn test dưới đây tồn tại để khoá
 * đúng điều đó.
 */

const SCAN: Array<[AlgorithmId, Record<string, unknown>]> = [
  ["find_max", {}],
  ["find_min", {}],
  ["count_if", { condition: { op: ">=", value: 7 } }],
  ["sum_if", { condition: { op: ">=", value: 7 } }],
];

/** Dữ liệu bắt buộc theo từng target — một nguồn, dùng cho cả test completeness. */
const DATA_FOR: Partial<Record<AlgorithmId, Record<string, unknown>>> = Object.fromEntries(SCAN);

/** Nhãn ngữ nghĩa của ba vùng hành động — hợp đồng với người dùng, không phải CSS. */
const ZONE_LABELS = [
  "Thao tác với biến tích luỹ",
  "Thao tác với bước tìm kiếm",
  "Thao tác sắp xếp",
];

const ARR = [7.5, 9, 6.5, 8, 5.5, 8.5, 7, 6];

function build(id: AlgorithmId, data: Record<string, unknown>) {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: { summary: "s", input: "i", output: "o" },
    algorithm_id: id,
    data: { array: ARR, ...data },
    data_generated: false,
    notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) };
}

const at = (s: AlgorithmSimState, cursor: number): AlgorithmSimState => ({ ...s, cursor });

function firstDecision(s: AlgorithmSimState): number {
  for (let i = 0; i < s.trace.steps.length; i += 1) {
    if (scanInteractionOf(at(s, i))) return i;
  }
  throw new Error("không tìm được bước quyết định");
}

/** Nhãn chú giải của một target, suy từ trace THẬT của chính nó. */
function legendLabels(id: AlgorithmId, data: Record<string, unknown>): string[] {
  const { state } = build(id, data);
  return arrayLegendItems(state.trace.steps, { algorithmId: id, hasGap: false })
    .map((i) => i.label);
}

/* ══ 1–8. NGỮ NGHĨA CHÚ GIẢI ═══════════════════════════════════════════════ */

describe("W3B-1 · chú giải nói đúng cơ chế của từng bài", () => {
  it("(1) count_if KHÔNG còn nói 'đã tìm thấy'", () => {
    expect(legendLabels("count_if", { condition: { op: ">=", value: 7 } }))
      .not.toContain("đã tìm thấy");
  });

  it("(2) count_if nói 'đã được đếm'", () => {
    expect(legendLabels("count_if", { condition: { op: ">=", value: 7 } }))
      .toContain("đã được đếm");
  });

  it("(3) sum_if KHÔNG còn nói 'đã tìm thấy'", () => {
    expect(legendLabels("sum_if", { condition: { op: ">=", value: 7 } }))
      .not.toContain("đã tìm thấy");
  });

  it("(4) sum_if nói 'đã được cộng vào tổng'", () => {
    expect(legendLabels("sum_if", { condition: { op: ">=", value: 7 } }))
      .toContain("đã được cộng vào tổng");
  });

  it("(5) find_max nói bằng ngôn ngữ của max, không phải của tìm kiếm", () => {
    const labels = legendLabels("find_max", {});
    expect(labels).not.toContain("đã tìm thấy");
    expect(labels).toContain("đã chọn làm max");
    // `considering` giữ ĐÚNG MỘT ô — ô đang giữ vai max — nên nó là một phần
    // tử cụ thể, không phải "vùng".
    expect(labels).toContain("max hiện tại");
    expect(labels).not.toContain("vùng đang xét");
  });

  it("(6) find_min nói bằng ngôn ngữ của min", () => {
    const labels = legendLabels("find_min", {});
    expect(labels).not.toContain("đã tìm thấy");
    expect(labels).toContain("đã chọn làm min");
    expect(labels).toContain("min hiện tại");
  });

  it("(7) target NGOÀI phạm vi giữ nguyên chú giải cũ", () => {
    const sorted = [...ARR].sort((a, b) => a - b);
    // Hai bài THẬT SỰ đi tìm một giá trị cho trước — "đã tìm thấy" vẫn đúng.
    for (const id of ["linear_search", "binary_search"] as AlgorithmId[]) {
      expect(legendLabels(id, { array: sorted, target: 8 }), id).toContain("đã tìm thấy");
    }
    for (const id of ["bubble_sort", "insertion_sort", "selection_sort"] as AlgorithmId[]) {
      expect(legendLabels(id, { order: "asc" }), id).toContain("phần đã sắp xong");
    }
    // Fallback: id lạ (target tương lai) vẫn có nhãn, không rơi vào undefined.
    const { state } = build("count_if", { condition: { op: ">=", value: 7 } });
    const unknown = arrayLegendItems(state.trace.steps, {
      algorithmId: "target_chua_ton_tai", hasGap: false,
    }).map((i) => i.label);
    expect(unknown).toContain("đã tìm thấy");
    expect(unknown.every((l) => typeof l === "string" && l.length > 0)).toBe(true);
  });

  /* COMPLETENESS (W3B §4) — bảng nhãn phải PHỦ HẾT cụm quét dãy.
   *
   * Test 1–6 khoá bốn target đang có; test này khoá điều khác: thêm thành viên
   * thứ năm vào `SCAN_FAMILY` mà quên thêm nhãn thì nó rơi êm về fallback
   * "đã tìm thấy" và **không có gì báo**. Nguồn sự thật là `isScanFamily`, nên
   * test đi qua đúng cái set mà production dùng, không phải một danh sách chép tay.
   */
  it("(8b) MỌI thành viên cụm quét dãy đều có nhãn tường minh — không ai rơi về fallback", () => {
    const members = ALGORITHM_IDS.filter((id) => isScanFamily(id));
    expect(members.length).toBeGreaterThanOrEqual(4);

    for (const id of members) {
      const labels = legendLabels(id, DATA_FOR[id] ?? {});
      expect(labels, `${id}: không sinh được chú giải`).not.toHaveLength(0);
      expect(labels, `${id} rơi về fallback "đã tìm thấy" — thiếu entry trong FOUND_LABEL`)
        .not.toContain("đã tìm thấy");
    }
  });

  it("(8) mapping là TRÌNH BÀY — mark canonical không đổi", () => {
    for (const [id, data] of SCAN) {
      const { state } = build(id, data);
      const marksBefore = JSON.stringify(state.trace.steps.map((s) => s.snapshot.marks));

      const labels = arrayLegendItems(state.trace.steps, { algorithmId: id, hasGap: false });
      expect(labels.length, id).toBeGreaterThan(0);

      // engine vẫn phát đúng mark `found`; chỉ TÊN GỌI của nó đổi
      const all = new Set(state.trace.steps.flatMap((s) => Object.values(s.snapshot.marks)));
      expect([...all], id).toContain("found");
      expect(JSON.stringify(state.trace.steps.map((s) => s.snapshot.marks)), id).toBe(marksBefore);
    }
  });
});

/* ══ 9–14. CAM KẾT: MỘT BỀ MẶT, KHÔNG LỘ ĐÁP ÁN, CÒN DẤU LỰA CHỌN ═════════ */

describe("W3B-1 · vùng hành động giữ đúng ranh giới cam kết", () => {
  it("(9) một điểm quyết định chỉ có ĐÚNG MỘT bề mặt cam kết", () => {
    for (const [id, data] of SCAN) {
      const { config, state } = build(id, data);
      const html = renderToString(
        <AlgorithmWorkspace
          config={config} state={at(state, firstDecision(state))} busy={false} dispatch={() => {}}
        />,
      );
      /* Đếm theo NHÃN NGỮ NGHĨA, không theo class: class đổi khi refactor CSS
         (đã xảy ra ở W3B §10 khi ba vùng dùng chung `.action-zone`), còn
         `aria-label` là hợp đồng với người dùng nên nó ổn định hơn. */
      const zones = ZONE_LABELS.map((l) => html.split(`aria-label="${l}"`).length - 1);
      expect(zones.reduce((a, b) => a + b, 0), `${id}: ${zones}`).toBe(1);
      expect(html, id).not.toContain('class="predict-bar"');
      expect(html, id).not.toContain("decision-strip");
    }
  });

  it("(10) shell KHÔNG dựng PredictionBar khi vùng hành động đã hiện", () => {
    for (const [id, data] of SCAN) {
      const { mod, state } = build(id, data);
      expect(mod.predict!.presentedInStage!(at(state, firstDecision(state))), id).toBe(true);
    }
    // …và shell thật sự tôn trọng cờ đó trước khi dựng PredictionBar.
    const shell = readFileSync(
      new URL("../components/SimulationWorkspace.tsx", import.meta.url), "utf-8",
    );
    expect(shell).toMatch(/!mod\.predict\?\.presentedInStage\?\.\(active\.state\)/);
  });

  it("(11) hành động SAI không đổi bất kỳ sự thật nào của engine", () => {
    for (const [id, data] of SCAN) {
      const { mod, state } = build(id, data);
      const cur = at(state, firstDecision(state));
      const m = scanInteractionOf(cur)!;
      const wrong = m.actions.find(
        (a) => mod.predict!.check(cur, a.id).verdict === "incorrect",
      )!;
      const before = JSON.stringify(cur);

      const r = mod.predict!.check(cur, wrong.id);

      expect(r.verdict, id).toBe("incorrect");
      expect(JSON.stringify(cur), id).toBe(before);
    }
  });

  it("(12) hành động ĐÚNG cũng không tự tiến cursor", () => {
    for (const [id, data] of SCAN) {
      const { mod, state } = build(id, data);
      const d = firstDecision(state);
      const cur = at(state, d);
      const m = scanInteractionOf(cur)!;
      const right = m.actions.find(
        (a) => mod.predict!.check(cur, a.id).verdict === "correct",
      )!;

      mod.predict!.check(cur, right.id);

      expect(cur.cursor, id).toBe(d);
      expect(JSON.stringify(cur.trace), id).toBe(JSON.stringify(state.trace));
    }
  });

  it("(13) bằng chứng KHÔNG có trong DOM trước khi học sinh hành động", () => {
    for (const [id, data] of SCAN) {
      const { mod, config, state } = build(id, data);
      const cur = at(state, firstDecision(state));
      const m = scanInteractionOf(cur)!;
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={cur} busy={false} dispatch={() => {}} />,
      );
      for (const a of m.actions) {
        const evidence = mod.predict!.check(cur, a.id).message;
        // câu bằng chứng bỏ tiền tố phán quyết ("Chính xác. " / "Chưa đúng. ")
        const core = evidence.replace(/^(Chính xác|Chưa đúng)\.\s*/, "");
        expect(core.length, id).toBeGreaterThan(10);
        expect(html, `${id}: ${core}`).not.toContain(core);
      }
      expect(html, id).not.toContain("Chính xác");
      expect(html, id).not.toContain("Chưa đúng");
    }
  });

  it("(14) sau khi chốt, nút đã chọn phân biệt được — và KHÔNG chỉ bằng màu", () => {
    for (const [id, data] of SCAN) {
      const { state } = build(id, data);
      const m = scanInteractionOf(at(state, firstDecision(state)))!;
      const picked = m.actions[1].id;
      const html = renderToString(
        <ScanActionZone
          model={m} answered busy={false} onAct={() => {}}
          feedback={{ verdict: "correct", message: "…", answerId: picked }}
        />,
      );

      // đúng MỘT nút mang dấu đã chọn
      expect(html.split('data-chosen="true"').length - 1, id).toBe(1);
      expect(html.split('data-chosen="false"').length - 1, id).toBe(1);
      expect(html, id).toContain('aria-pressed="true"');
      expect(html, id).toContain('aria-pressed="false"');
      // dấu hiệu CHỮ, không phụ thuộc vào việc phân biệt được màu
      expect(html, id).toContain("em đã chọn");
      // nút còn lại vẫn đọc được (có mặt, có nhãn) chứ không bị ẩn đi
      expect(html, id).toContain(m.actions[0].label);
    }
  });

  it("(14b) chưa chốt thì KHÔNG nút nào mang trạng thái đã chọn", () => {
    const { state } = build("find_max", {});
    const m = scanInteractionOf(at(state, firstDecision(state)))!;
    const html = renderToString(
      <ScanActionZone model={m} answered={false} busy={false} onAct={() => {}} feedback={null} />,
    );
    expect(html).not.toContain("data-chosen");
    expect(html).not.toContain("aria-pressed");
    expect(html).not.toContain("em đã chọn");
  });

  it("(14c) vùng hành động không bao giờ đọc `expectedId`", () => {
    const src = readFileSync(
      new URL("../components/ScanActionZone.tsx", import.meta.url), "utf-8",
    ).replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
    expect(src).not.toContain("expectedId");
    expect(src).toContain("feedback?.answerId");
  });
});

/* ══ 15–20. VÒNG ĐỜI PHẢN HỒI + AUTOPLAY (qua store thật) ═════════════════ */

const envOf = (id: AlgorithmId, data: Record<string, unknown>): SimulationEnvelope => ({
  status: "ok", simulation_id: `algorithm.${id}`, domain: "algorithm",
  visual_mode: "2d", title: "t", description: null, notes: null,
  config: {
    problem: { summary: "s", input: "i", output: "o" },
    algorithm_id: id,
    data: { array: ARR, ...data },
    data_generated: false, notes: null,
  },
});

/** Nạp một target, đứng ở điểm quyết định và CHỐT một hành động. */
function answerAtDecision(id: AlgorithmId, data: Record<string, unknown>): number {
  const store = useAppStore.getState();
  store.loadEnvelope(envOf(id, data));
  const s0 = useAppStore.getState().active!.state as AlgorithmSimState;
  const d = firstDecision(s0);
  useAppStore.getState().goToStep(d);
  const m = scanInteractionOf(useAppStore.getState().active!.state as AlgorithmSimState)!;
  useAppStore.getState().submitPrediction(m.actions[0].id);
  expect(useAppStore.getState().prediction).not.toBeNull();
  return d;
}

describe("W3B-1 · phản hồi sống đúng một bước, không đeo bám timeline", () => {
  beforeEach(() => useAppStore.getState().reset());

  it("(15) Next xoá phản hồi", () => {
    answerAtDecision("count_if", { condition: { op: ">=", value: 7 } });
    useAppStore.getState().nextStep();
    expect(useAppStore.getState().prediction).toBeNull();
  });

  it("(16) Back xoá phản hồi", () => {
    answerAtDecision("count_if", { condition: { op: ">=", value: 7 } });
    useAppStore.getState().prevStep();
    expect(useAppStore.getState().prediction).toBeNull();
  });

  it("(17) tua timeline (scrub) xoá phản hồi", () => {
    const d = answerAtDecision("sum_if", { condition: { op: ">=", value: 7 } });
    useAppStore.getState().goToStep(d + 2);
    expect(useAppStore.getState().prediction).toBeNull();
  });

  it("(18) Đặt lại xoá phản hồi và đưa mô phỏng về bước đầu", () => {
    answerAtDecision("find_max", {});
    useAppStore.getState().resetSim();
    expect(useAppStore.getState().prediction).toBeNull();
    expect((useAppStore.getState().active!.state as AlgorithmSimState).cursor).toBe(0);
  });

  it("(19) đổi config (nạp envelope khác) xoá phản hồi", () => {
    answerAtDecision("find_max", {});
    useAppStore.getState().loadEnvelope(envOf("find_min", {}));
    expect(useAppStore.getState().prediction).toBeNull();
  });

  it("(20) tự chạy KHÔNG bị vùng hành động chặn", () => {
    const d = answerAtDecision("find_min", {});
    useAppStore.getState().setPlaying(true);
    expect(useAppStore.getState().playing).toBe(true);

    // vòng tự chạy gọi nextStep() — bước vẫn tiến dù vừa chốt một hành động
    useAppStore.getState().nextStep();
    expect((useAppStore.getState().active!.state as AlgorithmSimState).cursor).toBe(d + 1);
    expect(useAppStore.getState().prediction).toBeNull();
    expect(useAppStore.getState().playing).toBe(true);
  });
});

/* ══ 21–23. BÀN PHÍM ══════════════════════════════════════════════════════
 *
 * Suite này chạy trên môi trường `node` (không jsdom — và wave này KHÔNG thêm
 * dependency), nên ở đây khoá ĐIỀU KIỆN sinh ra hành vi phím, còn hành vi thật
 * (Tab · Shift+Tab · Enter · Space) đo bằng bàn phím thật trong Chrome ở §12.
 */

describe("W3B-1 · bàn phím", () => {
  it("(21) phím tắt toàn cục nhường phím cho control đang focus (Space ≠ tự chạy)", () => {
    const src = readFileSync(
      new URL("../components/SimulationControls.tsx", import.meta.url), "utf-8",
    );
    // guard theo NĂNG LỰC tự xử lý Enter/Space — `button` phải nằm trong đó,
    // nếu không Space trên nút hành động sẽ bật Tự chạy và mất câu trả lời.
    expect(src).toMatch(/closest\?\.\(\s*['"`][^'"`]*button/);
  });

  it("(22) hành động là <button type=\"button\"> THẬT — Enter/Space là hành vi gốc", () => {
    const { state } = build("sum_if", { condition: { op: ">=", value: 7 } });
    const m = scanInteractionOf(at(state, firstDecision(state)))!;
    const html = renderToString(
      <ScanActionZone model={m} answered={false} busy={false} onAct={() => {}} feedback={null} />,
    );
    expect(html.split('type="button"').length - 1).toBe(m.actions.length);
    // không có div/span giả làm nút — control giả phải tự cài phím, control
    // gốc thì không cần, và đây là control gốc.
    expect(html).not.toContain('role="button"');
  });

  it("(23) thứ tự Tab = thứ tự đọc, không có tabindex nào bẻ lại", () => {
    const { state } = build("find_max", {});
    const m = scanInteractionOf(at(state, firstDecision(state)))!;
    const html = renderToString(
      <ScanActionZone model={m} answered={false} busy={false} onAct={() => {}} feedback={null} />,
    );
    expect(html).not.toContain("tabindex");
    const order = m.actions.map((a) => html.indexOf(a.label));
    expect(order.every((p) => p >= 0)).toBe(true);
    expect([...order].sort((x, y) => x - y)).toEqual(order);
  });
});
