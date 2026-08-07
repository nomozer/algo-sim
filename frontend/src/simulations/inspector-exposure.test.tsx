import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import { offlineCatalog } from "../data/offline-catalog";
import { getSimulation, registerAllSimulations } from "./index";

/**
 * W4B-1B §14 — AUDIT LỘ ĐÁP ÁN, mở rộng từ một ca thành một bất biến.
 *
 * Ca gốc: inspector của `network.graph_traversal` in TOÀN BỘ thứ tự thăm và
 * đường đi ngay ở bước 1/8. Module anh em `tree.traversal` đã sửa đúng lỗi đó ở
 * M17-VR1 nhưng không ai kiểm các bề mặt còn lại — đúng hình dạng
 * `ARCHITECTURE_MAP §8` anti-pattern #10 (vá một bề mặt, quên bề mặt anh em).
 *
 * Nên thay vì sửa một chỗ, khoá luôn LUẬT: với mọi mô phỏng CÓ dòng thời gian,
 * panel Quan sát ở bước ĐẦU không được giống hệt ở bước CUỐI. Giống hệt nghĩa
 * là nó không đọc `cursor` — tức đang hiển thị cùng một lượng thông tin bất kể
 * học sinh đã đi tới đâu, và với inspector có công bố kết quả thì đó chính là
 * lộ đáp án.
 *
 * Đây là điều kiện CẦN, không phải đủ: nó bắt được lớp lỗi "inspector mù bước",
 * không chứng minh mọi inspector đều hiện dần đúng mức.
 */

registerAllSimulations();

interface Subject {
  id: string;
  simId: string;
  title: string;
  first: string;
  last: string;
  steps: number;
}

/**
 * `offlineCatalog()` chỉ phủ 13/22 target — nó là danh mục MẪU cho học sinh,
 * không phải danh sách năng lực. Lượt đầu viết audit này chỉ dựa vào nó, và
 * kiểm chứng bằng tiêm lỗi cho thấy guard KHÔNG đỏ: `network.graph_traversal`
 * không có mẫu nào trong danh mục nên bị bỏ qua IM LẶNG — đúng target mà audit
 * được viết ra để canh. Bổ sung tường minh những target thiếu mẫu, và §14 dưới
 * đây khẳng định audit thật sự nhìn thấy chúng.
 */
const EXTRA_SUBJECTS: { simId: string; id: string; title: string; config: unknown }[] = [
  {
    simId: "network.graph_traversal",
    id: "audit-graph-traversal",
    title: "Duyệt đồ thị (fixture audit)",
    config: {
      nodes: [{ id: "A" }, { id: "B" }, { id: "C" }, { id: "D" }],
      edges: [["A", "B"], ["A", "C"], ["B", "D"]],
      directed: false,
      start: "A",
      goal: "D",
      variant: "bfs",
      notes: null,
    },
  },
];

const entries = [
  ...offlineCatalog().map((e) => ({
    id: e.id,
    simId: e.simId,
    title: e.title,
    config: e.envelope.config as unknown,
  })),
  ...EXTRA_SUBJECTS,
];

const subjects: Subject[] = [];
for (const entry of entries) {
  const mod = getSimulation(entry.simId);
  if (!mod || !mod.timeline || !mod.Inspector) continue;
  const parsed = mod.validateConfig(entry.config);
  if (!parsed.ok) continue;
  const state = mod.init(parsed.config);
  const total = mod.timeline.stepCount(state);
  if (total < 2) continue;
  // Gán ra biến cục bộ: TS không thu hẹp được thuộc tính optional qua closure.
  const Inspector = mod.Inspector;
  const timeline = mod.timeline;
  const render = (cursor: number) =>
    renderToString(
      <Inspector
        config={parsed.config}
        state={timeline.goToStep(state, cursor)}
        busy={false}
        dispatch={() => {}}
      />,
    ).replace(/<!--.*?-->/g, "");
  subjects.push({
    id: entry.id,
    simId: entry.simId,
    title: entry.title,
    first: render(0),
    last: render(total - 1),
    steps: total,
  });
}

describe("§14 — panel Quan sát không được mù bước (audit toàn danh mục offline)", () => {
  it("có đủ chủ thể để phép đo có nghĩa", () => {
    expect(subjects.length).toBeGreaterThanOrEqual(8);
  });

  it("mỗi mô phỏng CÓ timeline: Quan sát ở bước đầu KHÁC bước cuối", () => {
    const blind = subjects.filter((s) => s.first === s.last);
    expect(
      blind.map((s) => `${s.simId} (${s.id})`),
      "inspector không đọc cursor — hiển thị như nhau ở mọi bước",
    ).toEqual([]);
  });

  it("graph_traversal: bước đầu KHÔNG chứa thứ tự thăm đầy đủ (ca gốc)", () => {
    const s = subjects.find((x) => x.simId === "network.graph_traversal");
    // KHÔNG bỏ qua im lặng: nếu audit không nhìn thấy target này thì chính
    // audit hỏng, và phải đỏ ở đây chứ không phải xanh giả.
    expect(s, "audit không phủ network.graph_traversal — guard vô hiệu").toBeDefined();
    if (!s) return;
    expect(s.first).toContain("Đã thăm");
    expect(s.first).not.toContain("Đường đi:");
    expect(s.last).not.toContain("(engine)");
  });

  it("không inspector nào rò định danh kĩ thuật ra màn hình học sinh", () => {
    for (const s of subjects) {
      for (const html of [s.first, s.last]) {
        expect(html, `${s.simId} rò simulation_id`).not.toMatch(
          /(algorithm|network|binary|logic|tree|database|generic)\.[a-z_]+/,
        );
        expect(html, `${s.simId} rò thuật ngữ engine`).not.toContain("(engine)");
      }
    }
  });
});
