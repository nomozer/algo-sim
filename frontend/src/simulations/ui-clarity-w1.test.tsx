import { describe, expect, it, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import { decisionPointOf, narrationWithoutPrompt } from "./domains/algorithm/decision";
import { arrayLegendItems } from "../components/ArrayView";
import { BoolDagWorkspace, makeBoolDagModule } from "./domains/logic/dag-module";
import { registerAllSimulations } from "./index";
import { useAppStore } from "../state/store";
import type { AlgorithmSimState } from "./domains/algorithm";
import type { SimulationEnvelope } from "./types";

registerAllSimulations();

/**
 * UI CLARITY WAVE 1 — TEST KHOÁ NGUYÊN NHÂN.
 *
 * Mỗi khối dưới đây khoá đúng NGUYÊN NHÂN của một lỗi đã ĐO ĐƯỢC trong Chrome
 * tại `main@1c9f9d5`, không khoá triệu chứng:
 *
 *  1. câu hỏi dự đoán nhắc lại nguyên state line → "(vị trí 2)" hiện 2 lần;
 *  2. chú giải sân khấu thuật toán gắn với `hold` → chỉ hiện ở sắp xếp chèn,
 *     và biến mất ngay khi quân bài đáp xuống;
 *  3. bảng "Chi tiết các cổng" để `open` → sơ đồ mạch tụt còn 26% thẻ.
 */

const ARR = [7.5, 9, 6.5, 8, 5.5, 8.5, 7, 6];

function algoState(id: string, data: Record<string, unknown> = {}): AlgorithmSimState {
  const mod = makeAlgorithmModule(id as never);
  const r = mod.validateConfig({
    problem: { summary: "s", input: "i", output: "o" },
    algorithm_id: id,
    data: { array: ARR, ...data },
    data_generated: false,
    notes: null,
  });
  if (!r.ok) throw new Error(r.error);
  return mod.init(r.config);
}

function at(state: AlgorithmSimState, cursor: number): AlgorithmSimState {
  return { ...state, cursor };
}

/* ── 1. MỘT NGUỒN CÂU HỎI ────────────────────────────────────────────────── */

describe("W1 · một nguồn câu hỏi — prompt KHÔNG nhắc lại state line", () => {
  it("find_max: câu hỏi chỉ hỏi; vị trí và giá trị hiện tại thuộc state line", () => {
    const s = algoState("find_max");
    const d = decisionPointOf(at(s, 1))!;
    expect(d).not.toBeNull();

    // prompt vẫn nêu đúng cơ chế đang hỏi
    expect(d.question).toContain("cập nhật");
    expect(d.question.toLowerCase()).toContain("max");

    // …nhưng KHÔNG mang theo trạng thái: đó là việc của `consideration`
    expect(d.question).not.toContain("vị trí");
    expect(d.question).not.toContain("đang là");
    expect(d.consideration).toContain("vị trí");
    expect(d.consideration).toContain("max hiện tại");
  });

  it("chuỗi '(vị trí n)' chỉ xuất hiện MỘT lần trên toàn bộ sân khấu", () => {
    const mod = makeAlgorithmModule("find_max");
    const r = mod.validateConfig({
      problem: { summary: "s", input: "i", output: "o" },
      algorithm_id: "find_max", data: { array: ARR }, data_generated: false, notes: null,
    });
    if (!r.ok) throw new Error(r.error);
    const state = at(mod.init(r.config), 1);
    const d = decisionPointOf(state)!;

    const html = renderToString(
      <AlgorithmWorkspace config={r.config} state={state} busy={false} dispatch={() => {}} />,
    );
    const text = html.replace(/<[^>]+>/g, " ").replace(/<!--.*?-->/g, "");

    // dải nhân quả nói vị trí đúng một lần; prompt không nói lại
    const occurrences = text.split("vị trí").length - 1;
    expect(occurrences).toBe(1);
    expect(d.question).not.toContain("vị trí");
  });

  it("thuyết minh MÔ TẢ bước, không hỏi lại — engine giữ nguyên chuỗi gốc", () => {
    const mod = makeAlgorithmModule("find_max");
    const r = mod.validateConfig({
      problem: { summary: "s", input: "i", output: "o" },
      algorithm_id: "find_max", data: { array: ARR }, data_generated: false, notes: null,
    });
    if (!r.ok) throw new Error(r.error);
    const base = mod.init(r.config);

    for (let i = 0; i < base.trace.steps.length; i += 1) {
      const n = mod.narrate!(at(base, i), r.config);
      /* W3B §5.2 — bước CÓ vùng hành động thì shell không dựng khe thuyết minh
         (null), vì vùng hành động đã mang ứng viên/so sánh/biến tích luỹ rồi.
         Bước còn lại vẫn phải MÔ TẢ, và vẫn không được hỏi. */
      if (n === null) continue;
      expect(n.text.trimEnd().endsWith("?"), `bước ${i}: "${n.text}"`).toBe(false);
      expect(n.text.length, `bước ${i}: chuỗi rỗng để lại khe trắng`).toBeGreaterThan(0);
    }

    // …nhưng SỰ THẬT của engine không đổi: bước quyết định vẫn giữ chuỗi gốc
    const raw = base.trace.steps[1].narration;
    expect(raw).toContain("max có được cập nhật không?");
    /* W3B §5.1 — khoá HÀNH VI của phép cắt, không khoá wording của narration.
       Bản cũ ghim nguyên văn "So sánh a[1] = 9 với max = 7,5.", nên mọi lần sửa
       cách gọi vị trí đều làm test này đỏ vì một lý do chẳng liên quan gì tới
       điều nó muốn bảo vệ. */
    const shown = narrationWithoutPrompt(raw);
    expect(shown).not.toContain("có được cập nhật không?");
    expect(shown.trimEnd().endsWith("?")).toBe(false);
    expect(raw.startsWith(shown.slice(0, -1))).toBe(true);
    // chuỗi không phải câu hỏi thì giữ nguyên từng ký tự
    expect(narrationWithoutPrompt(base.trace.steps[0].narration))
      .toBe(base.trace.steps[0].narration);
  });

  it("mọi họ thuật toán: prompt ngắn hơn state line + evidence (chỉ hỏi, không kể)", () => {
    const cases: Array<[string, Record<string, unknown>, number]> = [
      ["find_max", {}, 1],
      ["find_min", {}, 1],
      ["bubble_sort", { order: "asc" }, 1],
      ["selection_sort", { order: "asc" }, 2],
      ["insertion_sort", { order: "asc" }, 2],
    ];
    for (const [id, data, cursor] of cases) {
      const s = algoState(id, data);
      const d = decisionPointOf(at(s, cursor));
      if (!d) continue;
      expect(d.question.length, `${id}: prompt phải ngắn`).toBeLessThan(60);
      expect(d.question).not.toContain("Đang xét");
    }
  });
});

/* ── 2. CHÚ GIẢI ỔN ĐỊNH SUỐT TIMELINE ───────────────────────────────────── */

describe("W1 · chú giải sân khấu thuật toán", () => {
  it("hiện ở MỌI bước, không phụ thuộc có held item", () => {
    const mod = makeAlgorithmModule("find_max");
    const r = mod.validateConfig({
      problem: { summary: "s", input: "i", output: "o" },
      algorithm_id: "find_max", data: { array: ARR }, data_generated: false, notes: null,
    });
    if (!r.ok) throw new Error(r.error);
    const base = mod.init(r.config);

    // find_max KHÔNG BAO GIỜ có held item — trước W1 nghĩa là không bao giờ có chú giải
    for (const cursor of [0, 1, 5, base.trace.steps.length - 1]) {
      const html = renderToString(
        <AlgorithmWorkspace config={r.config} state={at(base, cursor)} busy={false} dispatch={() => {}} />,
      );
      expect(html, `bước ${cursor} phải có chú giải`).toContain("stage-legend");
    }
  });

  it("chỉ liệt kê trạng thái mà target THẬT SỰ dùng", () => {
    const findMax = algoState("find_max");
    // binary_search đòi dãy ĐÃ SẮP — dùng đúng dãy đó, không nới ràng buộc engine.
    const binary = algoState("binary_search", { array: [...ARR].sort((a, b) => a - b), target: 8 });

    const lMax = arrayLegendItems(findMax.trace.steps, { algorithmId: "find_max", hasGap: false });
    const lBin = arrayLegendItems(binary.trace.steps, { algorithmId: "binary_search", hasGap: false });

    expect(lMax.some((i) => i.tone === "scan")).toBe(true);

    /* CÙNG mark `eliminated`, HAI nghĩa — nhãn phải khác nhau, nếu không học
       sinh mang nghĩa "bị loại" của tìm kiếm nhị phân sang find_max. Đây chính
       là lỗi "một màu nhiều nghĩa" mà audit ngôn ngữ màu đã đo được. */
    const labMax = lMax.find((i) => i.tone === "eliminated")!.label;
    const labBin = lBin.find((i) => i.tone === "eliminated")!.label;
    expect(labMax).toBe("đã duyệt qua");
    expect(labBin).toBe("nửa đã bị loại");
    expect(labMax).not.toBe(labBin);
  });

  it("ô trống chỉ xuất hiện khi thật sự đang giữ quân bài", () => {
    const s = algoState("insertion_sort", { order: "asc" });
    expect(arrayLegendItems(s.trace.steps, { algorithmId: "insertion_sort", hasGap: true }).some((i) => i.tone === "gap")).toBe(true);
    expect(arrayLegendItems(s.trace.steps, { algorithmId: "insertion_sort", hasGap: false }).some((i) => i.tone === "gap")).toBe(false);
  });

  it("danh sách rỗng → không dựng chú giải rỗng", () => {
    expect(arrayLegendItems([], { algorithmId: "find_max", hasGap: false })).toEqual([]);
  });
});

/* ── 3. BOOLEAN_DAG: BẢNG TRA CỨU GẬP MẶC ĐỊNH ───────────────────────────── */

const DAG_SAMPLE = {
  inputs: [{ id: "A", value: 1 }, { id: "B", value: 0 }, { id: "C", value: 1 }],
  gates: [
    { id: "g1", op: "AND", inputs: ["A", "B"] },
    { id: "g2", op: "NOT", inputs: ["C"] },
    { id: "g3", op: "OR", inputs: ["g1", "g2"] },
  ],
  output: "g3",
};

describe("W1 · boolean_dag — bảng chi tiết là tra cứu phụ", () => {
  it("<details> GẬP mặc định, nhưng vẫn nằm trong DOM (dữ liệu không mất)", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(DAG_SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const html = renderToString(
      <BoolDagWorkspace config={v.config} state={mod.init(v.config)} busy={false} dispatch={() => {}} />,
    );

    expect(html).toContain("gate-detail--fold");
    // KHÔNG có thuộc tính `open` trên thẻ details
    expect(/<details[^>]*\sopen/.test(html)).toBe(false);
    // nhưng nội dung bảng vẫn được render (hợp đồng authenticity giữ nguyên)
    expect(html).toContain("Chi tiết các cổng");
    expect(html).toContain("g3");
  });

  it("sơ đồ dùng thêm bề ngang mà KHÔNG phóng to node/chữ", () => {
    const mod = makeBoolDagModule();
    const v = mod.validateConfig(DAG_SAMPLE);
    if (!v.ok) throw new Error(v.error);
    const svg = renderToString(<BoolDagWorkspace config={v.config} state={mod.init(v.config)} busy={false} dispatch={() => {}} />);
    const vb = /viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"/.exec(svg)!;
    const w = Number(vb[1]);

    // trước W1: 3*134 + 2*96 = 594. Sau W1: 3*134 + 2*130 = 662.
    expect(w).toBe(662);
    // node giữ nguyên 134 — bề rộng tăng do DÂY dài ra, không do scale
    expect(svg).toContain('width="134"');
  });
});

/* ── 3b. THU GỌN LÀ BẢO ĐẢM CẤU TRÚC, KHÔNG PHẢI SO CHUỖI ────────────────── */

describe("W1 · checkpoint luôn bắt đầu ở trạng thái thu gọn", () => {
  it("shell gắn key theo BƯỚC nên rời bước rồi quay lại vẫn thu gọn", () => {
    /* Bản đầu của W1 khoá trạng thái mở theo NỘI DUNG câu hỏi. Đo trong Chrome
       bắt được lỗi: rời bước 1 rồi quay lại bước 1 thì câu hỏi y hệt ⇒ bar vẫn
       mở. Nay `SimulationWorkspace` gắn `key={timeline.currentStep(state)}`, tức
       mỗi lần vào một bước là một mount mới. Khoá bằng chính mã nguồn shell —
       component không tự chứng minh được điều này qua SSR. */
    const src = readFileSync(
      new URL("../components/SimulationWorkspace.tsx", import.meta.url), "utf-8",
    );
    expect(src).toMatch(/key=\{mod\.timeline \? mod\.timeline\.currentStep\(active\.state\)/);

    // và PredictionBar dựa vào mount đó: cờ nội bộ, KHÔNG so chuỗi câu hỏi
    const bar = readFileSync(
      new URL("../components/PredictionBar.tsx", import.meta.url), "utf-8",
    ).replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
    expect(bar).toContain("useState(false)");
    expect(bar).not.toContain("challenge.question)");
  });
});

/* ── 3c. PHÍM TẮT TOÀN CỤC KHÔNG CƯỚP PHÍM CỦA CONTROL ĐANG FOCUS ────────── */

describe("W1 · Space trên nút đáp án phải trả lời, không bật Tự chạy", () => {
  it("guard phím tắt che MỌI control tự xử lý Enter/Space, không riêng role=button", () => {
    /* Đo trong Chrome: bấm Space khi focus ở nút đáp án làm `playing = true`
       và câu trả lời mất trắng. Guard cũ chỉ che `[role="button"]` (viết cho ca
       boolean_dag), nên `<button>` thật của PredictionBar lọt qua. */
    const src = readFileSync(
      new URL("../components/SimulationControls.tsx", import.meta.url), "utf-8",
    );
    const guard = /closest\?\.\(([^)]+)\)/.exec(src)?.[1] ?? "";
    expect(guard).toContain("button");
    expect(guard).toContain('[role="button"]');
    // native <button> phải được kể tên tách khỏi role, nếu không ca W1 lại lọt
    expect(guard).toMatch(/(^|['"\s,])button\s*,/);
  });
});

/* ── 4. RESET XOÁ TRẠNG THÁI TRẢ LỜI ─────────────────────────────────────── */

describe("W1 · reset trả PredictionBar về thu gọn & chưa trả lời", () => {
  beforeEach(() => useAppStore.getState().reset());

  it("runtime reset xoá prediction", () => {
    const env: SimulationEnvelope = {
      status: "ok", simulation_id: "algorithm.find_max", domain: "algorithm",
      visual_mode: "2d", title: "t", description: null, notes: null,
      config: {
        problem: { summary: "s", input: "i", output: "o" },
        algorithm_id: "find_max", data: { array: ARR }, data_generated: false, notes: null,
      },
    };
    useAppStore.getState().loadEnvelope(env);
    useAppStore.getState().goToStep(1);
    useAppStore.getState().submitPrediction("yes");
    expect(useAppStore.getState().prediction).not.toBeNull();

    useAppStore.getState().resetSim();
    expect(useAppStore.getState().prediction).toBeNull();
    // và cursor về đầu ⇒ câu hỏi đổi ⇒ bar tự thu gọn (khoá mở theo câu hỏi)
    expect((useAppStore.getState().active!.state as AlgorithmSimState).cursor).toBe(0);
  });
});
