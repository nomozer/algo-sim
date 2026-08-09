import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import { stageInteractionsOf } from "./domains/algorithm/decision";
import { whatIfPolicyOf } from "./domains/algorithm/interaction-policy";
import { ALGORITHM_IDS, type AlgorithmId } from "../core/types";
import type { AlgorithmSimState } from "./domains/algorithm";

/**
 * EXPERIMENT_IS_A_TOOL_NOT_A_CONTENT_PANEL (W4B-2V/C).
 *
 * ĐO ĐƯỢC TRƯỚC KHI SỬA (`docs/evaluation/m17/w4b2vc-experiment-tool/before/`):
 * mở cổng Thí nghiệm làm vùng làm việc **cao thêm 122–186px**, vì `framing`
 * (135–310 ký tự) được dựng trong một thẻ `.notes` có nền và padding. Đó là một
 * bài giảng thứ hai nằm dưới mô phỏng, không phải một công cụ.
 *
 * Bất biến: mở Thí nghiệm chỉ được THÊM **quyền hành động** — nút, phản hồi
 * ngắn, lối đóng — chứ không thêm một khối nội dung.
 *
 * ─── VÌ SAO KHÔNG ĐO BẰNG SỐ KÝ TỰ THÔ ─────────────────────────────────────
 * Chữ NÊU TÊN trạng thái là biểu diễn, không phải prose ("vùng xét 4–7", "Đã so
 * sánh 4"). Nên bất biến này nhắm đúng thứ đã đo được là thủ phạm: **đoạn văn
 * hướng dẫn**. Trần đặt ở 60 ký tự vì đó cũng là ngưỡng runner trình duyệt dùng
 * để đếm "khối chữ", nên test và phép đo nói cùng một ngôn ngữ.
 *
 * ─── RÀNG BUỘC KHÔNG ĐƯỢC ĐÁNH ĐỔI ─────────────────────────────────────────
 * Rút gọn chữ KHÔNG được làm mất phân biệt cam kết ↔ what-if (W4B-2D §7 cấm
 * trình bày kéo như "bước tiếp theo của thuật toán"). Ý đó nay sống ở `hint`,
 * chuỗi render ngay cạnh công cụ kéo — có test riêng ở `interaction-policy.test.ts`.
 * Cắt chữ mà đánh mất phân biệt đó là đổi một khối chữ lấy một hồi quy ngữ nghĩa.
 */

const CAP = 60;

const DATA: Partial<Record<AlgorithmId, Record<string, unknown>>> = {
  linear_search: { array: [4, 9, 2, 7, 5, 8], target: 7 },
  binary_search: { array: [2, 4, 5, 7, 8, 9], target: 8 },
  count_if: { array: [4, 9, 2, 7, 5, 8], condition: { op: ">=", value: 7 } },
  sum_if: { array: [4, 9, 2, 7, 5, 8], condition: { op: ">=", value: 7 } },
  insertion_sort: { array: [4, 9, 2, 7, 5, 8], order: "asc" },
  find_max: { array: [4, 9, 2, 7, 5, 8] },
  find_min: { array: [4, 9, 2, 7, 5, 8] },
};

const GATED = ALGORITHM_IDS.filter((id) => whatIfPolicyOf(id).experimentGated === true);

function build(id: AlgorithmId) {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: {}, algorithm_id: id, data: DATA[id]!, data_generated: false, notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) as AlgorithmSimState };
}

const at = (s: AlgorithmSimState, cursor: number): AlgorithmSimState => ({ ...s, cursor });

describe("W4B-2V/C · EXPERIMENT_IS_A_TOOL_NOT_A_CONTENT_PANEL", () => {
  it("mọi bài gác cổng đều có fixture — nếu thiếu, bất biến phủ hụt", () => {
    for (const id of GATED) expect(DATA[id], `thiếu fixture cho ${id}`).toBeTruthy();
    expect(GATED.length).toBeGreaterThan(0);
  });

  it(`framing là CÂU HỎI HÀNH ĐỘNG, không phải đoạn giảng (< ${CAP} ký tự)`, () => {
    for (const id of GATED) {
      const f = whatIfPolicyOf(id).framing;
      expect(f, `${id}: bài gác cổng phải có framing`).toBeTruthy();
      expect(f!.length, `${id}: framing dài ${f!.length} — đã thành đoạn giảng: "${f}"`)
        .toBeLessThan(CAP);
    }
  });

  it("khay Thí nghiệm KHÔNG dựng bằng thẻ nội dung `.notes`", () => {
    /* Khoá ở tầng mã nguồn: `.notes` là thẻ có nền + padding, dùng cho khối
       giải thích. Dùng lại nó cho công cụ là cách khối này phình lên lần trước. */
    const src = readFileSync(
      new URL("./domains/algorithm/ui.tsx", import.meta.url), "utf-8",
    ).replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    expect(src, "khay Thí nghiệm quay lại dùng `.notes`").not.toContain('className="notes"');
    expect(src).toContain('className="experiment-tray"');
  });

  it("Quan sát: nhiều nhất MỘT khối chữ dài — cổng chưa mở thì chưa có công cụ", () => {
    for (const id of GATED) {
      const { config, state } = build(id);
      let k = -1;
      for (let i = 0; i < state.trace.steps.length && k < 0; i += 1) {
        if (stageInteractionsOf(at(state, i)).length > 0) k = i;
      }
      if (k < 0) continue;
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={at(state, k)} busy={false} dispatch={() => {}} />,
      );
      const text = html.replace(/<[^>]+>/g, "|");
      const longBlocks = text.split("|").map((t) => t.trim()).filter((t) => t.length >= CAP);
      expect(longBlocks.length, `${id}: Quan sát có ${longBlocks.length} khối chữ dài:\n${longBlocks.join("\n")}`)
        .toBeLessThanOrEqual(1);
    }
  });

  it("teaser vẫn còn — cổng phải TÌM THẤY ĐƯỢC, gọn không có nghĩa là câm", () => {
    /* Đối trọng của bất biến trên: nếu chỉ tối ưu cho "ít chữ" thì cám dỗ kế
       tiếp là bỏ teaser, và nút Thí nghiệm thành nút bí ẩn — đúng thứ PhET/CLT
       đã bắt ở W4B-2B. */
    for (const id of GATED) {
      const p = whatIfPolicyOf(id);
      expect(p.challengeTeaser, `${id}: mất teaser`).toBeTruthy();
      expect(p.challengeLabel, `${id}: mất nhãn nút`).toBeTruthy();
    }
  });
});
