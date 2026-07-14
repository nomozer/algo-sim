import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./index";
import { AlgorithmWorkspace } from "./ui";
import type { AlgorithmSimState } from "./model";
import { activeTrace } from "./model";
import type { AlgorithmId } from "../../../core/types";

/**
 * M9-S1 — UI theo chính sách tương tác + dải nhân quả dùng chung.
 *
 * (19) Ở một điểm quyết định, các biểu diễn liên kết phải cùng kể MỘT sự kiện:
 * dải nhân quả (expression) dùng đúng giá trị mà sự kiện compare của trace nêu.
 */

function stateAt(algorithmId: AlgorithmId, data: Record<string, unknown>, cursor: number): AlgorithmSimState {
  const mod = makeAlgorithmModule(algorithmId);
  const r = mod.validateConfig({ problem: {}, algorithm_id: algorithmId, data, data_generated: false, notes: null });
  if (!r.ok) throw new Error(r.error);
  return mod.timeline!.goToStep(mod.init(r.config), cursor) as AlgorithmSimState;
}

function html(algorithmId: AlgorithmId, data: Record<string, unknown>, cursor: number): string {
  const mod = makeAlgorithmModule(algorithmId);
  const r = mod.validateConfig({ problem: {}, algorithm_id: algorithmId, data, data_generated: false, notes: null });
  if (!r.ok) throw new Error(r.error);
  const s = stateAt(algorithmId, data, cursor);
  return renderToString(
    <AlgorithmWorkspace config={r.config} state={s} busy={false} dispatch={() => {}} />,
  );
}

describe("gating swap trong AlgorithmWorkspace", () => {
  it("bubble_sort (free): hiện gợi ý kéo-thả", () => {
    const h = html("bubble_sort", { array: [1, 3, 2], order: "asc" }, 1);
    expect(h).toContain("Kéo một cột");
  });

  it("(17) sum_if (hidden): KHÔNG gợi ý kéo-thả, KHÔNG nút thí nghiệm", () => {
    const h = html("sum_if", { array: [5, 8, 3], condition: { op: ">", value: 4 } }, 1);
    expect(h).not.toContain("Kéo một cột");
    expect(h).not.toContain("Thí nghiệm");
  });

  it("(16) binary_search (challenge): không gợi ý kéo tự do; CÓ nút thí nghiệm phá tiền điều kiện", () => {
    const h = html("binary_search", { array: [1, 3, 5, 7, 9, 11, 13], target: 3 }, 1);
    expect(h).not.toContain("Kéo một cột");
    expect(h).toContain("Thí nghiệm");
    expect(h).toContain("sắp thứ tự");
  });

  it("find_max (challenge): có nút thí nghiệm phá bất biến, không kéo tự do mặc định", () => {
    const h = html("find_max", { array: [7.5, 9, 6] }, 1);
    expect(h).not.toContain("Kéo một cột");
    expect(h).toContain("Thí nghiệm");
  });

  it("linear_search (framed): kéo được nhưng khung câu hỏi là CHI PHÍ tìm kiếm", () => {
    const h = html("linear_search", { array: [4, 9, 7], target: 9 }, 1);
    expect(h).toContain("sớm hơn"); // khung: đưa target sớm/muộn → số lần so sánh đổi
  });
});

describe("(19) dải nhân quả — khớp sự kiện trace hiện tại", () => {
  it("bước quyết định find_max: expression chứa đúng hai giá trị mà event compare nêu", () => {
    const s = stateAt("find_max", { array: [7.5, 9, 6] }, 1);
    const step = activeTrace(s).steps[1];
    const cmp = step.events.find((e) => e.type === "compare") as { i: number; j: number };
    const vi = step.snapshot.array[cmp.i];
    const vj = step.snapshot.array[cmp.j];

    const h = html("find_max", { array: [7.5, 9, 6] }, 1);
    expect(h).toContain("decision-strip");
    // expression của dải dùng ĐÚNG hai giá trị của event (9 và 7,5) — SSR escape ">"
    expect(h).toMatch(new RegExp(`${vi}\\s*&gt;\\s*${String(vj).replace(".", ",")}`));
  });

  it("bước hệ quả find_max (cập nhật max): dải nói rõ nhân quả trước → sau", () => {
    const h = html("find_max", { array: [7.5, 9, 6] }, 2);
    expect(h).toContain("decision-strip");
    expect(h).toContain("→");
    expect(h).toContain("max");
  });
});
