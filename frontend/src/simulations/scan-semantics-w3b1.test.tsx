
import { describe, expect, it } from "vitest";


import { renderToString } from "react-dom/server";
import { arrayLegendItems } from "../components/ArrayView";

import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import { isScanFamily, scanInteractionOf } from "./domains/algorithm/decision";
import { registerAllSimulations } from "./index";

import type { AlgorithmSimState } from "./domains/algorithm";
import { ALGORITHM_IDS, type AlgorithmId } from "../core/types";


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
      /* W4B-2B §7 — bài PILOT gác vùng cam kết sau cổng Thí nghiệm, và SSR luôn
         thấy `labOpen = false` (state cục bộ, ARCHITECTURE_MAP §8 #13) ⇒ ở chế
         độ Quan sát số bề mặt cam kết là 0, không phải 1.

         Điều bất biến này thật sự bảo vệ là "KHÔNG BAO GIỜ HAI" — nó không hề
         đòi phải luôn có một. Nên đọc kỳ vọng từ CHÍNH bản khai policy: thêm
         target vào pilot thì test đi theo, không đỏ vì một lý do chẳng liên
         quan; mà lỡ có hai bề mặt thì vẫn đỏ như cũ. */
      /* Bất biến thật là "KHÔNG BAO GIỜ HAI", không phải "luôn có một". */
      expect(zones.reduce((a, b) => a + b, 0), `${id}: ${zones}`).toBeLessThanOrEqual(1);
      expect(html, id).not.toContain('class="predict-bar"');

      /* 2026-08-21 (Task 10b) — VIẾT LẠI. Bản cũ đòi `decision-strip` phải có
         mặt khi vùng cam kết bị gác. Hai tiền đề của nó đã mất: W13 gỡ hẳn vùng
         cam kết, và `ui.tsx` chỉ dựng `decision-strip` khi target KHÔNG thuộc
         họ scan/search/sort — vì ba dải họ đó tự chở phép so sánh
         ("không bao giờ hai kênh nói một điều").

         Thứ còn sống, và là thứ đáng khoá: QUAN HỆ ĐANG XÉT phải hiện ở ĐÚNG
         MỘT nơi. Với họ scan thì nơi đó là `scan-action`; đòi thêm
         `decision-strip` chính là đòi kênh thứ hai. */
      const coDaiHo = html.includes("scan-action");
      const coDaiQuyetDinh = html.includes("decision-strip");
      expect(
        Number(coDaiHo) + Number(coDaiQuyetDinh),
        `${id}: quan hệ đang xét phải hiện ở ĐÚNG MỘT dải`,
      ).toBe(1);
    }
  });
  /* (10)–(23) ĐÃ XOÁ 2026-08-21 (Task 10b).

     Toàn bộ khối đó kiểm VÒNG CAM KẾT có chấm điểm: `predict.check`,
     `submitPrediction`, `PredictionBar`, và việc phản hồi bị xoá khi tua/đặt
     lại. W13 gỡ năng lực đó có chủ đích, nên không còn hành vi nào để khoá.

     Thứ SỐNG SÓT của wave W3B-1 — ngôn ngữ thuyết minh phải nói theo cơ chế
     của từng target ("đã được đếm" chứ không phải "đã tìm thấy") — nằm ở các
     test (1)–(9) phía trên và giữ nguyên. */
});
