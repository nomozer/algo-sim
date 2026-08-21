import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import { decisionPointOf, narrationWithoutPrompt } from "./domains/algorithm/decision";
import { ArrayView, arrayLegendItems } from "../components/ArrayView";
import { BoolDagWorkspace, makeBoolDagModule } from "./domains/logic/dag-module";
import { registerAllSimulations } from "./index";

import type { AlgorithmSimState } from "./domains/algorithm";


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

    /* trước W1: 3*134 + 2*96 = 594. Sau W1: 3*134 + 2*130 = 662.
       W4B-4D: +2*16 lề trong = 694 — khung nét đứt của cổng ĐẦU RA vẽ ra ngoài
       hộp node 7px, và viewBox không có lề thì nó bị CẮT (đo được trong Chrome:
       mực chạm 101% bề rộng thẻ ở 768px). Con số vẫn khoá cứng vì điều đáng giữ
       là "bề rộng tăng do BỐ CỤC, không do scale" — mà một cú phóng viewBox
       cũng làm số này tăng, nên vế thứ hai bên dưới mới là vế phân biệt. */
    expect(w).toBe(694);
    // node giữ nguyên 134 — bề rộng tăng do DÂY dài ra, không do scale
    expect(svg).toContain('width="134"');
  });
});

/* ── 3b. THU GỌN LÀ BẢO ĐẢM CẤU TRÚC, KHÔNG PHẢI SO CHUỖI ────────────────── */

/* describe "W1 · checkpoint luôn bắt đầu ở trạng thái thu gọn" ĐÃ GỠ 2026-08-21
   (Task 10b): "checkpoint" ở đây là ô dự đoán, mà W13 gỡ hẳn. Không còn thứ gì
   để bắt đầu ở trạng thái thu gọn. */

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

/* describe "W1 · reset trả PredictionBar về thu gọn & chưa trả lời" GỠ 2026-08-21
   (Task 10b): `PredictionBar` và `prediction` đều đã bị W13 xoá, nên không còn
   trạng thái trả lời nào để reset. Vế "reset đưa mô phỏng về bước đầu" KHÔNG
   mất — `workspace-lifecycle.test.ts` khoá nó. */

/* ── 5. W4B-2B §9 — PANEL GIẢI THÍCH KHÔNG CHÉP LẠI HEADER WORKSPACE ─────────
 *
 * Panel nay ĐÓNG mặc định (W4B-2B §8), nên nội dung của nó phải ĐÀO SÂU chứ
 * không lặp trang chính. Hai thứ header đã sở hữu:
 *
 *  - `SimulationWorkspace` dựng `<h2 class="workspace-title">{envelope.title}</h2>`
 *    và `offline-catalog.ts` đặt `envelope.title = analysis.problem.summary`
 *    ⇒ `problem.summary` in trong panel là HAI `<h2>` chữ y hệt trên một màn;
 *  - header còn in `mod.title` = `ALGORITHM_NAMES[algorithm_id]`, mà panel vừa
 *    có hàng "Thuật toán" in cùng bảng tên đó VỪA có đầu mục "THUẬT TOÁN" của
 *    khối mã giả — một ý ba lần trong một cột hẹp.
 *
 * Khoá bằng cách render THẲNG `AlgorithmInspector` (không đi qua `App`: SSR chỉ
 * thấy trạng thái đầu — anti-pattern #8). Test khẳng định cả hai chiều: chuỗi
 * của header BIẾN MẤT, còn phần header không nói (Input/Output/Dữ liệu/BIẾN)
 * thì CÒN NGUYÊN — nếu không đây sẽ thành test "xoá càng nhiều càng tốt".
 */
describe("W4B-2B §9 · Giải thích đào sâu, không chép lại header", () => {
  const SUMMARY = "Tìm học sinh có điểm kiểm tra cao nhất trong tổ 8 bạn";

  function inspectorHtml(id: string, data: Record<string, unknown> = {}): string {
    const mod = makeAlgorithmModule(id as never);
    const r = mod.validateConfig({
      problem: { summary: SUMMARY, input: "Danh sách điểm 8 bạn", output: "Điểm cao nhất" },
      algorithm_id: id,
      data: { array: ARR, ...data },
      data_generated: false,
      notes: null,
    });
    if (!r.ok) throw new Error(r.error);
    const state = mod.init(r.config);
    const Inspector = mod.Inspector!;
    return renderToString(
      <Inspector config={r.config} state={{ ...state, cursor: 3 }} busy={false} dispatch={() => {}} />,
    );
  }

  it("không in lại tiêu đề bài toán (header đã sở hữu nó)", () => {
    expect(inspectorHtml("find_max")).not.toContain(SUMMARY);
  });

  it("không in lại tên thuật toán (header + đầu mục mã giả đã nói)", () => {
    expect(inspectorHtml("find_max")).not.toContain("Tìm giá trị lớn nhất");
    expect(inspectorHtml("insertion_sort", { order: "asc" })).not.toContain("Sắp xếp chèn");
  });

  it("VẪN giữ thứ header KHÔNG nói: Input, Output, dữ liệu, biến, mã giả", () => {
    const html = inspectorHtml("find_max");
    for (const needle of ["Input", "Output", "Dữ liệu", "BIẾN", "THUẬT TOÁN"]) {
      expect(html, `mất mục "${needle}"`).toContain(needle);
    }
  });

  it("nhãn BIẾN biến mất cùng nội dung khi bước chưa có biến nào", () => {
    const mod = makeAlgorithmModule("find_max" as never);
    const r = mod.validateConfig({
      problem: { summary: SUMMARY, input: "i", output: "o" },
      algorithm_id: "find_max",
      data: { array: ARR },
      data_generated: false,
      notes: null,
    });
    if (!r.ok) throw new Error(r.error);
    const state = mod.init(r.config);
    const empty = { ...state } as AlgorithmSimState;
    const steps = empty.trace.steps.map((s, i) =>
      i === 0 ? { ...s, snapshot: { ...s.snapshot, vars: {} } } : s,
    );
    const Inspector = mod.Inspector!;
    const html = renderToString(
      <Inspector
        config={r.config}
        state={{ ...empty, trace: { ...empty.trace, steps }, cursor: 0 }}
        busy={false}
        dispatch={() => {}}
      />,
    );
    expect(html).not.toContain("BIẾN");
  });
});

/* ── 6. W4B-2B §10 — "ĐANG XÉT" ≠ "MAX HIỆN TẠI" TRÊN SÂN KHẤU ──────────────
 *
 * Khe hở ĐO ĐƯỢC (ảnh `observe-baseline/find-max-explain-closed`, bước 5/10,
 * Explain ĐÓNG): sự kiện `compare` mang hai chỉ số — `i` là phần tử đang xét,
 * `j` là ứng viên tốt nhất — nhưng `columnState` trả CÙNG style cho cả hai, kể
 * cả con trỏ ▲. Học sinh nhìn hai cột xanh y hệt nhau đúng lúc câu hỏi là "cái
 * đang xét có hơn max không?".
 *
 * Đồng thời chú giải ĐÃ hứa hai mục riêng (`arrayLegendItems` đọc mark
 * `considering` → "max hiện tại"), nên trước bản vá chú giải nói dối.
 *
 * Khoá cả ba mệnh đề, không chỉ "có hai màu":
 *  a. hai vai trò cho ra HAI tông khác nhau;
 *  b. con trỏ ▲ chỉ ĐÚNG MỘT cột (chỗ thuật toán đang đứng);
 *  c. tông của cột ứng viên KHỚP tông mà chú giải dùng cho "max hiện tại".
 */
describe("W4B-2B §10 · find_max: đang xét và max hiện tại phân biệt được", () => {
  const CURSOR_PATH = /d="M [\d.]+ [\d.]+ l -6 9 h 12 z"/g;

  function compareStepOf(id: "find_max" | "find_min") {
    const st = algoState(id);
    const step = st.trace.steps.find((s) => s.events.some((e) => e.type === "compare"));
    if (!step) throw new Error(`${id}: không có bước so sánh nào`);
    return step;
  }

  it("bước so sánh: cột đang xét và cột ứng viên KHÁC tông", () => {
    const html = renderToString(<ArrayView step={compareStepOf("find_max")} labels={null} />);
    expect(html, "mất tông của cột đang xét").toContain("var(--accent-sky)");
    expect(html, "cột max vẫn bị nhuộm cùng tông với cột đang xét")
      .toContain("var(--accent-teal)");
  });

  it("con trỏ ▲ chỉ đúng MỘT cột — không chỉ hai chỗ cùng lúc", () => {
    const html = renderToString(<ArrayView step={compareStepOf("find_max")} labels={null} />);
    expect((html.match(CURSOR_PATH) ?? []).length).toBe(1);
  });

  it("chú giải KHÔNG nói dối: có mục riêng cho max hiện tại", () => {
    const st = algoState("find_max");
    const items = arrayLegendItems(st.trace.steps, { algorithmId: "find_max", hasGap: false });
    const labels = items.map((i) => i.label);
    expect(labels).toContain("đang xét / so sánh");
    expect(labels).toContain("max hiện tại");
    // tông của mục "max hiện tại" phải là tông mà sân khấu THẬT SỰ dùng
    expect(items.find((i) => i.label === "max hiện tại")!.tone).toBe("considering");
  });

  it("find_min hưởng cùng bản vá (cùng engine runFindExtreme)", () => {
    const html = renderToString(<ArrayView step={compareStepOf("find_min")} labels={null} />);
    expect(html).toContain("var(--accent-teal)");
    expect((html.match(CURSOR_PATH) ?? []).length).toBe(1);
  });

  it("bài KHÔNG dùng mark `considering` giữ nguyên hành vi cũ (2 cột so sánh)", () => {
    // bubble_sort so sánh hai phần tử NGANG VAI — cả hai đều phải là "đang xét".
    const st = algoState("bubble_sort", { order: "asc" });
    const step = st.trace.steps.find((s) => s.events.some((e) => e.type === "compare"))!;
    const html = renderToString(<ArrayView step={step} labels={null} />);
    expect(html).not.toContain("var(--accent-teal)");
    expect((html.match(CURSOR_PATH) ?? []).length).toBe(2);
  });
});
