import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import { SearchStateView } from "../components/SearchStateView";
import { searchInteractionOf, stageInteractionsOf } from "./domains/algorithm/decision";
import { whatIfPolicyOf } from "./domains/algorithm/interaction-policy";
import { ALGORITHM_IDS, type AlgorithmId } from "../core/types";
import type { AlgorithmSimState } from "./domains/algorithm";

/**
 * EXPERIMENT_IS_A_TOOL_NOT_A_CONTENT_PANEL — W4B-2V/C2.
 *
 * VÌ SAO BẢN TRƯỚC CHƯA ĐỦ. Wave C rút chữ và giảm chiều cao 39–50%, rồi tuyên
 * bố "Tool Mode". Ảnh chụp cho thấy nó vẫn là **một tấm nội dung, chỉ nhỏ hơn**:
 * `.action-zone` là `<section>` block mang `background: canvas-soft` + `border`
 * + `padding md lg` + `flex-direction: column`, nên nó vẫn trải gần hết bề
 * ngang. Bớt px và bớt câu là **điều kiện cần, không đủ** — chính vì thế các
 * assert dưới đây kiểm **CẤU TRÚC và QUYỀN SỞ HỮU**, không kiểm số ký tự.
 *
 * Hợp đồng được khoá:
 *  - `EXPERIMENT_IS_A_TOOL_NOT_A_CONTENT_PANEL`
 *  - `EXPERIMENT_CLOSE_CONTROL_LIVES_INSIDE_TOOL`
 *  - `NO_SEPARATE_EXPERIMENT_FRAMING_ROW`
 *  - `EXPERIMENT_DOES_NOT_DUPLICATE_CORE_OBSERVATION_STATE`
 *  - `EXPERIMENT_FEEDBACK_ATTACHED_TO_TOOL`
 *  - `DESCRIPTIVE_EXPERIMENT_AFFORDANCE_EXISTS`
 *
 * `labOpen` là `useState` cục bộ nên SSR không mở được công cụ
 * (`ARCHITECTURE_MAP §8` #13). Ở đây khoá **cấu trúc mã nguồn + hợp đồng
 * component**; hình học thật (bề rộng, số hàng, close nằm trong khung công cụ)
 * do runner trình duyệt đo — `docs/evaluation/m17/w4b2vc2-tool-mode/`.
 */

const UI_SRC = readFileSync(
  new URL("./domains/algorithm/ui.tsx", import.meta.url), "utf-8",
);
/** Bóc chú thích: repo CỐ Ý nhắc tên thứ đã bỏ để ghi lại vì sao bỏ. */
const UI = UI_SRC.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
const CSS = readFileSync(new URL("../styles/global.css", import.meta.url), "utf-8");

const GATED = ALGORITHM_IDS.filter((id) => whatIfPolicyOf(id).experimentGated === true);

const DATA: Partial<Record<AlgorithmId, Record<string, unknown>>> = {
  linear_search: { array: [4, 9, 2, 7, 5, 8], target: 7 },
  binary_search: { array: [2, 4, 5, 7, 8, 9], target: 8 },
  count_if: { array: [4, 9, 2, 7, 5, 8], condition: { op: ">=", value: 7 } },
  sum_if: { array: [4, 9, 2, 7, 5, 8], condition: { op: ">=", value: 7 } },
  insertion_sort: { array: [4, 9, 2, 7, 5, 8], order: "asc" },
  find_max: { array: [4, 9, 2, 7, 5, 8] },
  find_min: { array: [4, 9, 2, 7, 5, 8] },
  // W4B-2I: hai bài sắp xếp cuối vào cổng ⇒ bất biến này phủ tới chúng. Guard
  // "thiếu fixture" ở ngay dưới là thứ bắt được thiếu sót này, không phải tôi.
  bubble_sort: { array: [4, 9, 2, 7, 5, 8], order: "asc" },
  selection_sort: { array: [4, 9, 2, 7, 5, 8], order: "asc" },
};

function build(id: AlgorithmId) {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: {}, algorithm_id: id, data: DATA[id]!, data_generated: false, notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) as AlgorithmSimState };
}
const at = (s: AlgorithmSimState, cursor: number): AlgorithmSimState => ({ ...s, cursor });

function actionableStep(s: AlgorithmSimState): number {
  for (let i = 0; i < s.trace.steps.length; i += 1) {
    if (stageInteractionsOf(at(s, i)).length > 0) return i;
  }
  return -1;
}

describe("W4B-2V/C2 · EXPERIMENT_IS_A_TOOL_NOT_A_CONTENT_PANEL", () => {
  it("mọi bài gác cổng đều có fixture — thiếu thì bất biến phủ hụt", () => {
    for (const id of GATED) expect(DATA[id], `thiếu fixture ${id}`).toBeTruthy();
    expect(GATED.length).toBeGreaterThan(0);
  });

  it("công cụ KHÔNG dựng bằng chrome thẻ (`.notes` / `.experiment-tray` / `.card`)", () => {
    for (const dead of ['className="notes"', 'className="experiment-tray"', 'experiment-tray-close']) {
      expect(UI, `chrome thẻ quay lại: ${dead}`).not.toContain(dead);
    }
    expect(UI, "mất chủ sở hữu công cụ").toContain('className="experiment-tool"');
  });

  it("chrome CÔNG CỤ gỡ nền/viền/padding và xếp NGANG — khác hẳn chrome thẻ", () => {
    /* Đây là khác biệt panel ↔ tool, và nó sống ở CSS chứ không ở JSX. Kiểm
       thẳng luật: `.action-zone` giữ thẻ; `.is-tool` phải huỷ nó. */
    const tool = CSS.slice(CSS.indexOf(".action-zone.is-tool"));
    const rule = tool.slice(0, tool.indexOf("}"));
    for (const kill of ["padding: 0", "background: none", "border: none", "flex-direction: row"]) {
      expect(rule, `.is-tool thiếu "${kill}" — vẫn là thẻ`).toContain(kill);
    }
    const wrap = CSS.slice(CSS.indexOf(".experiment-tool {"));
    const wrapRule = wrap.slice(0, wrap.indexOf("}"));
    expect(wrapRule, "công cụ vẫn rộng theo khung chứa").toContain("width: fit-content");
    expect(wrapRule, "công cụ không xếp inline").toContain("inline-flex");
  });

  it("zone nhận chrome DẪN XUẤT từ capability, không từ tên bài", () => {
    expect(UI).toMatch(/chrome:\s*\(gated \? "tool" : "panel"\)/);
    expect(UI, "shell quyết định theo định danh bài").not.toMatch(/algorithm_id\s*===\s*["']/);
    const z = renderToString(
      <SearchStateView
        model={searchInteractionOf(at(build("binary_search").state, actionableStep(build("binary_search").state)))!} />,
    );
    expect(z).toContain("is-tool");
  });

  it("EXPERIMENT_CLOSE_CONTROL_LIVES_INSIDE_TOOL — không có hàng đóng riêng", () => {
    const tool = UI.slice(UI.indexOf('className="experiment-tool"'));
    const block = tool.slice(0, tool.indexOf("</div>"));
    expect(block, "lối đóng nằm ngoài công cụ").toContain("experiment-tool-close");
    /* W4B-3A: công cụ này bọc vùng CAM KẾT, nên nó thuộc chế độ Thử thách —
       nhãn đóng nói đúng chế độ mình đóng. */
    expect(block).toContain('aria-label="Đóng thử thách"');
  });

  it("NO_SEPARATE_EXPERIMENT_FRAMING_ROW — framing là TÊN KHẢ TRUY CẬP", () => {
    /* `framing` được phép tồn tại, nhưng không được là một hàng chữ. Cách duy
       nhất nó xuất hiện trong JSX phải là `aria-label`. */
    const uses = [...UI.matchAll(/policy\.framing/g)].length;
    expect(uses, "framing xuất hiện nhiều hơn một chỗ").toBe(1);
    expect(UI).toContain("aria-label={policy.framing}");
    expect(UI, "framing bị in thành nội dung").not.toContain("{policy.framing}<");
    expect(UI).not.toContain("<strong>{policy.framing}</strong>");
  });

  it("DESCRIPTIVE_EXPERIMENT_AFFORDANCE_EXISTS — cổng tự mô tả, không bí ẩn", () => {
    /* Đối trọng bắt buộc của việc bỏ hàng teaser: nếu chỉ tối ưu cho gọn thì
       nút thành bí ẩn — lỗi PhET/CLT đã bắt ở W4B-2B. Nhãn phải MÔ TẢ, và
       teaser vẫn tới được người dùng qua `title`. */
    /* W4B-3A — teaser không còn là `title` của một nút do sân khấu dựng; nó là
       `hint` của CÂU MỜI, và `SimulationControls` đặt nó vào `title`/`aria-label`
       của lối vào. Bất biến "cổng tự mô tả" giữ nguyên, chỉ đổi chủ. */
    const controls = readFileSync(
      new URL("../components/SimulationControls.tsx", import.meta.url), "utf-8",
    );
    /* W4B-3B — nhãn HIỂN THỊ rút gọn ("Khám phá"/"Thử thách") để dải điều khiển
       không xuống dòng ở 1366, nhưng TÊN KHẢ TRUY CẬP phải mang cả câu đầy đủ
       LẪN câu mời-thử. Khoá đúng chỗ đó, không khoá chuỗi hiển thị. */
    expect(controls, "tên khả truy cập không gộp nhãn đầy đủ + câu mời")
      .toContain("const full = [entry.label, entry.hint]");
    expect(controls, "câu mời không tới được chuột").toContain("title={open ? undefined : describe}");
    /* W5G — HỢP ĐỒNG ĐỔI: không còn nút mờ thường trực. Lối vào không dùng được
       thì VẮNG MẶT, nên `unavailableHint` thôi được đọc và khẳng định cũ ("nút
       mờ phải nói vì sao") trở thành vô nghĩa — giữ nó lại là giữ một guard chỉ
       còn quét một chuỗi trong chú thích. */
    expect(controls, "lối vào không dùng được vẫn còn được dựng")
      .toContain("if (entry.available === false && !open) return null;");
    expect(controls, "còn khoá nút phụ bằng `disabled` ⇒ nút mờ quay lại")
      .not.toContain("disabled={disabled}");
    expect(controls, "câu mời không tới được công nghệ hỗ trợ")
      .toContain("aria-label={open ? undefined : describe}");
    for (const id of GATED) {
      expect(whatIfPolicyOf(id).challengeTeaser, `${id}: mất teaser`).toBeTruthy();
    }
    for (const id of GATED) {
      const p = whatIfPolicyOf(id);
      expect(p.challengeLabel, `${id}: mất nhãn`).toBeTruthy();
      expect(p.challengeLabel!.length, `${id}: nhãn quá cụt để tự mô tả`).toBeGreaterThan(14);
      expect(p.challengeTeaser, `${id}: mất teaser`).toBeTruthy();
    }
  });

  it("EXPERIMENT_DOES_NOT_DUPLICATE_CORE_OBSERVATION_STATE", () => {
    /* Công cụ sở hữu HÀNH ĐỘNG; trạng thái đã nằm ở Quan sát. Chép lại vào
       công cụ là cách nó phình lên lần nữa. */
    for (const id of ["linear_search", "binary_search"] as AlgorithmId[]) {
      const { state } = build(id);
      const k = actionableStep(state);
      const zone = renderToString(
        <SearchStateView
          model={searchInteractionOf(at(state, k))!} />,
      );
      for (const dup of ["search-state", "search-cost", "search-precondition", "scan-chip"]) {
        expect(zone, `${id}: công cụ chép lại "${dup}" của Quan sát`).not.toContain(dup);
      }
    }
  });

  it("EXPERIMENT_FEEDBACK_ATTACHED_TO_TOOL — phản hồi ở TRONG zone", () => {
    const { state } = build("binary_search");
    const k = actionableStep(state);
    const zone = renderToString(
      <SearchStateView
        model={searchInteractionOf(at(state, k))!} />,
    );
    expect(zone).toContain("predict-result");
    expect(zone.indexOf("predict-result"), "phản hồi rơi ra ngoài zone")
      .toBeLessThan(zone.lastIndexOf("</section>"));
  });

  it("Quan sát vẫn sạch: 0 bề mặt cam kết, nhiều nhất một khối chữ dài", () => {
    for (const id of GATED) {
      const { config, state } = build(id);
      const k = actionableStep(state);
      if (k < 0) continue;
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={at(state, k)} busy={false} dispatch={() => {}} />,
      );
      expect(html, `${id}: Quan sát bày cam kết`).not.toContain('aria-label="Thao tác');
      const blocks = html.replace(/<[^>]+>/g, "|").split("|")
        .map((t) => t.trim()).filter((t) => t.length >= 60);
      expect(blocks.length, `${id}: ${blocks.length} khối chữ dài:\n${blocks.join("\n")}`)
        .toBeLessThanOrEqual(1);
    }
  });
});
