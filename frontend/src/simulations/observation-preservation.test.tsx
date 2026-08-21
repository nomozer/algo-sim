import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";

import { searchInteractionOf, decisionPointOf } from "./domains/algorithm/decision";
import { whatIfPolicyOf } from "./domains/algorithm/interaction-policy";
import type { AlgorithmSimState } from "./domains/algorithm";
import type { AlgorithmId } from "../core/types";

/**
 * CORE_OBSERVATION_STATE_PRESERVED_UNDER_GATING (W4B-2V, root cause #1).
 *
 * SỰ CỐ ĐƯỢC KHOÁ Ở ĐÂY. W4B-2D thêm `&& commitmentVisible` để gác **nút cam
 * kết**, nhưng đặt điều kiện đó TRÊN cả `SearchStateView` — component vốn sở
 * hữu cả trạng thái quan sát lẫn điều khiển. Hệ quả: gác quyền hành động thì
 * mất luôn chip vị trí/đích/vùng xét và khối chi phí. Với tìm tuần tự thì chi
 * phí CHÍNH LÀ cơ chế đáng học — và `interaction-policy.ts` đã viện dẫn đúng
 * khối đó để biện minh cho việc gác kéo. Cổng lấy mất thứ nó dựa vào.
 *
 * Chiều ngược lại cũng hỏng: `expression` ("7 = 9 ?") sống ở dải nhân quả, mà
 * dải bị tắt đúng khi vùng cam kết bật ⇒ **mở** Thí nghiệm lại làm mất quan hệ.
 *
 * Luật: **cổng gác QUYỀN HÀNH ĐỘNG, không gác THÔNG TIN.**
 *
 * ─── VÌ SAO CHỨNG MINH THEO CẤU TRÚC, KHÔNG SO HAI LẦN RENDER ──────────────
 * `labOpen` là `useState` cục bộ nên SSR luôn thấy `false`
 * (`ARCHITECTURE_MAP §8` #13) — không render được trạng thái "đã mở" mà không
 * giả lập, và giả lập thì test lại kiểm cái giả lập. Thay vào đó chứng minh hai
 * mệnh đề, và tính đơn điệu SUY RA từ chúng cho MỌI state chứ không riêng
 * fixture:
 *
 *   (1) mọi probe cơ chế lõi đều nằm trong phần KHÔNG bị gác;
 *   (2) phần BỊ gác không chứa probe lõi nào.
 *   ⇒ mở cổng chỉ THÊM quyền hành động, không thể dời/lấy mất thông tin.
 *
 * Bản render thật lúc cổng mở do runner trình duyệt phủ.
 *
 * ─── PRESENTATION_COPY_TRANSITION (ngoại lệ có tên) ────────────────────────
 * Teaser ↔ framing ↔ nhãn nút ↔ lời hướng dẫn ↔ phản hồi **được phép** đổi khi
 * mở/đóng cổng. Chúng là lời mời và lời chấm, không phải trạng thái cơ chế.
 * Bất biến này CỐ Ý không phát biểu trên "mọi DOM nhìn thấy" — công thức tập
 * con nghĩa đen đó sẽ đỏ trên hành vi đang đúng, và cám dỗ kế tiếp là nới lỏng
 * chính bất biến.
 */

const SEARCH: Array<[AlgorithmId, Record<string, unknown>]> = [
  ["linear_search", { array: [4, 9, 2, 7, 5, 8], target: 7 }],
  ["binary_search", { array: [2, 4, 5, 7, 8, 9], target: 8 }],
];

function build(id: AlgorithmId, data: Record<string, unknown>) {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: { summary: "s", input: "i", output: "o" },
    algorithm_id: id, data, data_generated: false, notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) as AlgorithmSimState };
}

const at = (s: AlgorithmSimState, cursor: number): AlgorithmSimState => ({ ...s, cursor });
const seen = (html: string) => html.replaceAll("<!-- -->", "");

function firstActionable(s: AlgorithmSimState): number {
  for (let i = 0; i < s.trace.steps.length; i += 1) {
    if (searchInteractionOf(at(s, i))) return i;
  }
  throw new Error("không tìm được bước cam kết");
}

/**
 * PROBE CƠ CHẾ LÕI — suy từ CHÍNH state của engine, không phải chuỗi viết tay.
 *
 * Chỉ probe thứ thực sự thuộc cơ chế của bài đó (§4/§17): đối tượng đang xét,
 * vai trò, quan hệ, tiến độ/chi phí. KHÔNG probe teaser/nhãn nút/hướng dẫn.
 */
function coreProbes(id: AlgorithmId, s: AlgorithmSimState): Record<string, string> {
  const m = searchInteractionOf(s);
  if (!m) throw new Error("bước này không có mô hình tìm kiếm");
  const d = decisionPointOf(s);
  const p: Record<string, string> = {
    "giá trị cần tìm": m.targetValue,
    "phần tử đang xét": m.currentValue,
    "quan hệ đang xét": d ? d.expression : "",
  };
  if (m.activeRange) {
    p["vùng xét (biên trái)"] = String(m.activeRange.left + 1);
    p["vùng xét (biên phải)"] = String(m.activeRange.right + 1);
  } else {
    p["vị trí hiện tại"] = String(m.currentIndex + 1);
  }
  if (m.cost) {
    p["chi phí: đã so sánh"] = String(m.cost.comparisonsDone);
    p["chi phí: xấu nhất"] = String(m.cost.worstCaseComparisons);
  }
  if (m.precondition) p["tiền đề"] = m.precondition;
  if (id === "binary_search") {
    expect(m.activeRange, "fixture nhị phân mất vùng xét").toBeTruthy();
  }
  return p;
}

const ZONE_LABELS = [
  "Thao tác với biến tích luỹ",
  "Thao tác sắp xếp",
  "Thao tác với bước tìm kiếm",
];
const surfaceCount = (html: string) =>
  ZONE_LABELS.reduce((n, l) => n + (html.split(`aria-label="${l}"`).length - 1), 0);

describe("W4B-2V · CORE_OBSERVATION_STATE_PRESERVED_UNDER_GATING", () => {
  it("cả hai bài tìm kiếm ĐANG gác cổng — nếu không, bất biến này vô nghĩa", () => {
    for (const [id] of SEARCH) {
      expect(whatIfPolicyOf(id).experimentGated, `${id} không còn gác cổng`).toBe(true);
    }
  });

  it("(1) MỌI probe cơ chế lõi đọc được ở Quan sát, khi cổng đang ĐÓNG", () => {
    for (const [id, data] of SEARCH) {
      const { config, state } = build(id, data);
      const k = firstActionable(state);
      const cur = at(state, k);
      const html = seen(renderToString(
        <AlgorithmWorkspace config={config} state={cur} busy={false} dispatch={() => {}} />,
      ));
      for (const [name, needle] of Object.entries(coreProbes(id, cur))) {
        expect(html, `${id}: Quan sát mất "${name}" (cần thấy “${needle}”)`).toContain(needle);
      }
    }
  });

  it("Quan sát KHÔNG có bề mặt cam kết nào", () => {
    for (const [id, data] of SEARCH) {
      const { config, state } = build(id, data);
      const cur = at(state, firstActionable(state));
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={cur} busy={false} dispatch={() => {}} />,
      );
      expect(surfaceCount(html), `${id}: Quan sát bày cam kết`).toBe(0);
    }
  });

  /**
   * (2) VẾ QUYẾT ĐỊNH TÍNH ĐƠN ĐIỆU. Phần bị cổng gác chỉ được chứa quyền hành
   * động. Nếu một probe lõi lọt vào đây thì mở/đóng cổng lại đổi lượng thông
   * tin — đúng lỗi W4B-2D. Kiểm trên CHÍNH component mà cổng bật/tắt.
   */
  /* it("(2) vùng cam kết KHÔNG chứa probe cơ chế lõi nào…") ĐÃ XOÁ 2026-08-21 (Task 10b).
     Khai niem W13 da go: cong Thi nghiem dang PANEL / che do Thu thach / vung cam ket. */

  /* it("cổng vẫn còn tác dụng: vùng cam kết dựng được và mang đúng hành …") ĐÃ XOÁ 2026-08-21 (Task 10b).
     Khai niem W13 da go: cong Thi nghiem dang PANEL / che do Thu thach / vung cam ket. */

  it("Quan sát KHÔNG rò đáp án dù trạng thái nay hiện đầy đủ", () => {
    /* Tách trạng thái ra khỏi cổng KHÔNG được kéo theo đáp án. */
    for (const [id, data] of SEARCH) {
      const { config, state } = build(id, data);
      const cur = at(state, firstActionable(state));
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={cur} busy={false} dispatch={() => {}} />,
      );
      for (const leak of ["correctActionId", "expectedId", "expectedAction", "đáp án"]) {
        expect(html, `${id}: rò "${leak}"`).not.toContain(leak);
      }
      // nhãn hành động là quyền hành động ⇒ không được có ở Quan sát
      for (const a of searchInteractionOf(cur)!.actions) {
        expect(html, `${id}: nhãn hành động lọt ra Quan sát`).not.toContain(a.label);
      }
    }
  });

  it("PRESENTATION_COPY_TRANSITION: teaser/framing KHÔNG phải trạng thái lõi", () => {
    /* Ghi bằng test để không ai âm thầm đưa chúng vào tập probe rồi phải nới
       lỏng bất biến khi teaser đổi thành framing lúc mở cổng. */
    for (const [id, data] of SEARCH) {
      const p = whatIfPolicyOf(id);
      expect(p.challengeTeaser, `${id}: thiếu teaser`).toBeTruthy();
      expect(p.framing, `${id}: thiếu framing`).toBeTruthy();
      const { state } = build(id, data);
      const cur = at(state, firstActionable(state));
      const probes = Object.values(coreProbes(id, cur));
      expect(probes, `${id}: teaser bị coi là trạng thái lõi`).not.toContain(p.challengeTeaser);
      expect(probes, `${id}: framing bị coi là trạng thái lõi`).not.toContain(p.framing);
    }
  });
});
