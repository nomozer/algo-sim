import { describe, expect, it, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import {
  challengeEntry,
  challengeSurfaceVisible,
} from "../components/SimulationWorkspace";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import { isScanFamily, scanInteractionOf, stageInteractionsOf } from "./domains/algorithm/decision";
import { commitmentSurfaceVisible, whatIfPolicyOf } from "./domains/algorithm/interaction-policy";
import { registerAllSimulations } from "./index";
import { useAppStore } from "../state/store";
import type { AlgorithmSimState } from "./domains/algorithm";
import { ALGORITHM_IDS, type AlgorithmId } from "../core/types";
import type { SimulationEnvelope } from "./types";

registerAllSimulations();

/**
 * INTERACTION-FAMILY WAVE 1 — CỤM "QUÉT DÃY + BIẾN TÍCH LUỸ".
 *
 * Wave này chứng minh MỘT thiết kế tương tác phục vụ BỐN bài cùng cơ chế, nên
 * test cũng viết theo cụm: cùng một bộ khẳng định chạy trên cả bốn target, thay
 * vì bốn bộ test song song.
 *
 * Ranh giới phải giữ:
 * - engine tất định là bên DUY NHẤT phán đúng/sai (bất biến #11);
 * - hành động sai KHÔNG đổi state canonical (CORRECTNESS §4: học sinh được sai);
 * - dữ liệu của renderer KHÔNG mang đáp án;
 * - một bước chỉ có MỘT hình thức cam kết.
 */

const SCAN: Array<[AlgorithmId, Record<string, unknown>]> = [
  ["find_max", {}],
  ["find_min", {}],
  ["count_if", { condition: { op: ">=", value: 7 } }],
  ["sum_if", { condition: { op: ">=", value: 7 } }],
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

/** Bước quyết định đầu tiên của một target — nơi cơ chế thật sự diễn ra. */
function firstDecision(s: AlgorithmSimState): number {
  for (let i = 0; i < s.trace.steps.length; i += 1) {
    if (scanInteractionOf(at(s, i))) return i;
  }
  throw new Error("không tìm được bước quyết định");
}

/* ── 1. MỘT PRIMITIVE, BỐN TARGET ────────────────────────────────────────── */

describe("W1-IF · một mô hình tương tác phục vụ cả bốn target", () => {
  it("cả bốn target đều sinh được mô hình, với đúng hai hành động update/keep", () => {
    for (const [id, data] of SCAN) {
      const { state } = build(id, data);
      const m = scanInteractionOf(at(state, firstDecision(state)))!;
      expect(m, id).not.toBeNull();
      expect(m.actions.map((a) => a.tone), id).toEqual(["update", "keep"]);
      // nhãn nói bằng ngôn ngữ CƠ CHẾ, không phải "Có"/"Không"
      for (const a of m.actions) {
        expect(a.label, `${id}: ${a.label}`).not.toBe("Có");
        expect(a.label, `${id}: ${a.label}`).not.toBe("Không");
        expect(a.label.length, `${id}: nhãn rỗng`).toBeGreaterThan(3);
      }
      // ứng viên và biến tích luỹ đều có giá trị hiện tại
      expect(m.candidateValue, id).not.toBe("");
      expect(m.accumulatorValue, id).not.toBe("");
    }
  });

  it("target NGOÀI cụm không sinh mô hình — wave không lan sang họ khác", () => {
    for (const id of ["binary_search", "linear_search", "bubble_sort", "insertion_sort", "selection_sort"] as AlgorithmId[]) {
      expect(isScanFamily(id), id).toBe(false);
      const extra = id === "binary_search" || id === "linear_search"
        ? { array: [...ARR].sort((a, b) => a - b), target: 8 }
        : { order: "asc" };
      const { state } = build(id, extra);
      for (let i = 0; i < state.trace.steps.length; i += 1) {
        expect(scanInteractionOf(at(state, i)), `${id} bước ${i}`).toBeNull();
      }
    }
  });
});

/* ── 2. RENDERER KHÔNG BIẾT ĐÁP ÁN ───────────────────────────────────────── */

describe("W1-IF · dữ liệu renderer không mang đáp án", () => {
  it("mô hình KHÔNG có correctActionId lẫn evidence", () => {
    for (const [id, data] of SCAN) {
      const { state } = build(id, data);
      const m = scanInteractionOf(at(state, firstDecision(state)))! as unknown as Record<string, unknown>;
      expect(Object.keys(m), id).not.toContain("correctActionId");
      expect(Object.keys(m), id).not.toContain("evidence");
      expect(Object.keys(m), id).not.toContain("expectedId");
    }
  });

  it("HTML của bước chưa trả lời không chứa bằng chứng nhân quả", () => {
    const { mod, config, state } = build("find_max", {});
    const cur = at(state, firstDecision(state));
    const html = renderToString(
      <AlgorithmWorkspace config={config} state={cur} busy={false} dispatch={() => {}} />,
    );
    // `evidence` chỉ được sinh ra khi CHẤM, và chỉ hiện sau khi học sinh chốt
    const evidence = mod.predict!.check(cur, "yes").message;
    expect(evidence.length).toBeGreaterThan(10);
    expect(html).not.toContain("nên max được cập nhật");
    expect(html).not.toContain("Chính xác");
  });

  it("component không tự phán xử — nó chỉ phát hành động và hiển thị phản hồi", () => {
    const src = readFileSync(
      new URL("../components/ScanActionZone.tsx", import.meta.url), "utf-8",
    ).replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
    expect(src).not.toContain("expectedId");
    expect(src).not.toMatch(/===\s*['"]yes['"]/);
    expect(src).toContain("onAct(a.id)");
  });
});

/* ── 3. ENGINE VẪN LÀ BÊN DUY NHẤT PHÁN ĐÚNG/SAI ─────────────────────────── */

describe("W1-IF · chấm bằng engine tất định, qua đúng một đường", () => {
  it("hành động đúng → correct; hành động sai → incorrect; cả hai đều từ predict.check", () => {
    for (const [id, data] of SCAN) {
      const { mod, state } = build(id, data);
      const cur = at(state, firstDecision(state));
      const m = scanInteractionOf(cur)!;

      const update = mod.predict!.check(cur, m.actions[0].id);
      const keep = mod.predict!.check(cur, m.actions[1].id);
      // đúng một trong hai là correct — engine quyết, test không giả định cái nào
      expect([update.verdict, keep.verdict].sort(), id).toEqual(["correct", "incorrect"]);
      expect(update.message.length, id).toBeGreaterThan(10);
    }
  });

  it("hành động SAI không đụng state canonical", () => {
    for (const [id, data] of SCAN) {
      const { mod, state } = build(id, data);
      const cur = at(state, firstDecision(state));
      const m = scanInteractionOf(cur)!;
      const before = JSON.stringify(cur);

      mod.predict!.check(cur, m.actions[0].id);
      mod.predict!.check(cur, m.actions[1].id);

      expect(JSON.stringify(cur), id).toBe(before);
    }
  });

  it("id hành động khớp option của DecisionPoint — không có đường chấm thứ hai", () => {
    for (const [id, data] of SCAN) {
      const { mod, state } = build(id, data);
      const cur = at(state, firstDecision(state));
      const m = scanInteractionOf(cur)!;
      const optionIds = mod.predict!.challenge(cur)!.options.map((o) => o.id);
      expect(m.actions.map((a) => a.id), id).toEqual(optionIds);
    }
  });
});

/* ── 4. MỘT BƯỚC, MỘT HÌNH THỨC CAM KẾT ──────────────────────────────────── */

describe("W1-IF · không bao giờ hiện hai hình thức cùng lúc", () => {
  it("bước có vùng hành động thì module khai presentedInStage = true", () => {
    for (const [id, data] of SCAN) {
      const { mod, state } = build(id, data);
      const d = firstDecision(state);
      expect(mod.predict!.presentedInStage!(at(state, d)), id).toBe(true);
      // bước cuối không phải điểm quyết định → trả về UI dùng chung như cũ
      expect(mod.predict!.presentedInStage!(at(state, state.trace.steps.length - 1)), id).toBe(false);
    }
  });

  /* ── W3B §14 — LOCK CŨ ĐÃ ĐƯỢC THAY, CÓ CHỦ ĐÍCH ────────────────────────
   *
   * Bản cũ khoá "bubble_sort không bao giờ presentedInStage". Từ W3B, sắp xếp
   * CÓ vùng hành động nên khẳng định đó sai theo thiết kế. Không thay bằng một
   * target khác rồi tiếp tục `expect(false)`: cụm tìm kiếm cũng có vùng hành
   * động, nên trò đó chỉ dời cái lock tới chỗ sắp sai tiếp.
   *
   * Thay bằng BẤT BIẾN TỔNG QUÁT — thứ vẫn đúng khi có thêm cụm cơ chế mới:
   * một bước có TỐI ĐA MỘT mô hình, và `presentedInStage` phải khớp đúng với
   * việc có hay không có mô hình đó.
   */
  it("mọi target · mọi bước: tối đa MỘT mô hình tương tác sân khấu", () => {
    for (const id of ALGORITHM_IDS) {
      const extra =
        id === "binary_search" || id === "linear_search"
          ? { array: [...ARR].sort((a, b) => a - b), target: 8 }
          : id === "count_if" || id === "sum_if"
            ? { condition: { op: ">=", value: 7 } }
            : id === "bubble_sort" || id === "insertion_sort" || id === "selection_sort"
              ? { order: "asc" }
              : {};
      const { state } = build(id, extra);
      for (let i = 0; i < state.trace.steps.length; i += 1) {
        const present = stageInteractionsOf(at(state, i));
        expect(present.length, `${id} bước ${i}: ${present.join("+")}`).toBeLessThanOrEqual(1);
      }
    }
  });

  it("presentedInStage khớp ĐÚNG việc có mô hình hay không", () => {
    for (const id of ALGORITHM_IDS) {
      const extra =
        id === "binary_search" || id === "linear_search"
          ? { array: [...ARR].sort((a, b) => a - b), target: 8 }
          : id === "count_if" || id === "sum_if"
            ? { condition: { op: ">=", value: 7 } }
            : id === "bubble_sort" || id === "insertion_sort" || id === "selection_sort"
              ? { order: "asc" }
              : {};
      const { mod, state } = build(id, extra);
      for (let i = 0; i < state.trace.steps.length; i += 1) {
        const cur = at(state, i);
        expect(mod.predict!.presentedInStage!(cur), `${id} bước ${i}`)
          .toBe(stageInteractionsOf(cur).length === 1);
      }
    }
  });

  it("shell tôn trọng presentedInStage trước khi dựng PredictionBar", () => {
    /* W4B-2U2: luật giữ nguyên, chỗ ở đổi. Bản cũ khớp REGEX trên mã nguồn của
       một biểu thức inline trong JSX — nên nó đỏ ngay khi biểu thức được tách
       thành hàm thuần, dù hành vi không đổi một chút nào. Test khoá HÌNH DẠNG MÃ
       chặn đúng loại refactor nó lẽ ra phải bảo vệ.
       Nay khẳng định vào HÀNH VI qua chủ sở hữu `challengeSurfaceVisible`.

       W4B-3A — TÁCH CỬA KHỎI PHÒNG. `presentedInStage` chỉ được phép tắt BỀ MẶT
       thứ hai (`PredictionBar`); nó KHÔNG được tắt LỐI VÀO. Bản trước áp nó cho
       cả hai, nên ở đúng những bước có vùng cam kết thì shell không dựng lối
       vào nào — và họ thuật toán phải tự dựng lấy một nút, chính là dải
       `experimentTrigger` nằm dưới mô hình. */
    const cap = { challenge: () => null, check: () => ({ verdict: "unsupported_to_verify" as const, answerId: "x", message: "" }) };
    const presented = { predict: { ...cap, presentedInStage: () => true } };
    const notPresented = { predict: { ...cap, presentedInStage: () => false } };

    // Module tự bày cam kết trên sân khấu ⇒ shell KHÔNG dựng bề mặt thứ hai,
    // kể cả khi Thử thách đang mở.
    expect(challengeSurfaceVisible(presented, {}, true)).toBe(false);
    // …nhưng LỐI VÀO vẫn còn: đó là cửa, không phải bề mặt.
    expect(challengeEntry(presented, {}, {})).not.toBeNull();

    // Không tự bày ⇒ bề mặt dùng chung thuộc về Thử thách, không thuộc Quan sát.
    expect(challengeSurfaceVisible(notPresented, {}, false)).toBe(false);
    expect(challengeSurfaceVisible(notPresented, {}, true)).toBe(true);
  });

  /* ── BẤT BIẾN BỀ MẶT CAM KẾT (W4B-2D §2) ────────────────────────────────
   *
   *   COMMITMENT_SURFACE_COUNT <= 1
   *
   * LỊCH SỬ CỦA CHÍNH TEST NÀY, và vì sao nó được viết lại:
   * bản cũ khoá luật bằng cách chọn một bài LÀM CHỨNG chưa gác cổng rồi render
   * SSR. Bài đó đã phải đổi BA lần khi từng họ lần lượt gác cổng
   * (`find_max` → `sum_if` → `linear_search`), và sẽ hết bài ngay khi họ tìm
   * kiếm được gác. Đổi lần thứ tư là chữa triệu chứng.
   *
   * Nay luật có chủ sở hữu gọi tên được: `commitmentSurfaceVisible(policy, labOpen)`
   * ở `interaction-policy.ts` — CÙNG hàm mà `AlgorithmWorkspace` gọi, không phải
   * bản sao dành riêng cho test.
   *
   * Bốn ca, và cách mỗi ca được phủ:
   *   A. gated=false, có điểm quyết định        → 1 bề mặt   (hàm thuần + SSR)
   *   B. gated=true, labOpen=false               → 0 bề mặt   (hàm thuần + SSR)
   *   C. gated=true, labOpen=true, có quyết định → 1 bề mặt   (hàm thuần; bản
   *      RENDER do runner trình duyệt phủ, vì `labOpen` là useState cục bộ và
   *      SSR luôn thấy `false` — ARCHITECTURE_MAP §8 #13. KHÔNG giả lập nó bằng
   *      renderToString, và KHÔNG đưa labOpen lên store chỉ để test dễ hơn.)
   *   D. không có điểm quyết định               → 0 bề mặt   (SSR)
   */
  const ZONE_LABELS = [
    "Thao tác với biến tích luỹ",
    "Thao tác với bước tìm kiếm",
    "Thao tác sắp xếp",
  ];
  const surfaceCount = (html: string) =>
    ZONE_LABELS.reduce((n, l) => n + (html.split(`aria-label="${l}"`).length - 1), 0);

  it("(A/B) luật thuần: gated quyết định bề mặt cam kết, không phụ thuộc bài nào", () => {
    const ungated = { mode: "free", rationale: "r" } as const;
    const gated = { mode: "free", rationale: "r", experimentGated: true } as const;
    // A — chưa gác cổng thì bề mặt luôn có mặt, kể cả khi chưa mở Thí nghiệm
    expect(commitmentSurfaceVisible(ungated, false)).toBe(true);
    expect(commitmentSurfaceVisible(ungated, true)).toBe(true);
    // B — gác cổng mà chưa mở ⇒ không bề mặt nào
    expect(commitmentSurfaceVisible(gated, false)).toBe(false);
    // C — gác cổng và đã mở ⇒ có bề mặt
    expect(commitmentSurfaceVisible(gated, true)).toBe(true);
  });

  it("(A) bài CHƯA gác cổng ở điểm quyết định: đúng MỘT bề mặt, không kèm dải nhân quả", () => {
    /* Đọc kỳ vọng từ chính bản khai policy: bài nào chưa gác cổng cũng được, và
       nếu một ngày KHÔNG còn bài nào chưa gác thì test tự bỏ qua thay vì đỏ vì
       một lý do chẳng liên quan. */
    const ungated = ALGORITHM_IDS.filter((id) => !whatIfPolicyOf(id).experimentGated);
    if (ungated.length === 0) return;
    for (const id of ungated) {
      const extra = id === "binary_search" || id === "linear_search"
        ? { array: [...ARR].sort((x, y) => x - y), target: 8 }
        : { order: "asc" };
      const { config, state } = build(id, extra);
      let d = -1;
      for (let i = 0; i < state.trace.steps.length && d < 0; i += 1) {
        if (stageInteractionsOf(at(state, i)).length > 0) d = i;
      }
      if (d < 0) continue;
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={at(state, d)} busy={false} dispatch={() => {}} />,
      );
      expect(surfaceCount(html), `${id}: số bề mặt cam kết`).toBe(1);
      // một bề mặt một lúc ⇒ dải nhân quả không được dựng song song
      expect(html, `${id}: dựng cả hai`).not.toContain("decision-strip");
    }
  });

  it("(B) bài ĐÃ gác cổng ở Quan sát: KHÔNG bề mặt nào, nhưng quan hệ ở lại", () => {
    const gated = ALGORITHM_IDS.filter((id) => whatIfPolicyOf(id).experimentGated);
    expect(gated.length, "không còn bài gác cổng nào — bất biến mất ý nghĩa").toBeGreaterThan(0);
    for (const id of gated) {
      /* W4B-2D: họ tìm kiếm nay nằm trong `gated`, nên nhánh này phải cấp
         `target` (và dãy ĐÃ SẮP cho nhị phân) — giống hệt ca (A) bên trên. */
      const extra = id.endsWith("_sort")
        ? { order: "asc" }
        : id === "count_if" || id === "sum_if"
          ? { condition: { op: ">=", value: 7 } }
          : id === "binary_search" || id === "linear_search"
            ? { array: [...ARR].sort((x, y) => x - y), target: 8 }
            : {};
      const { config, state } = build(id, extra);
      let d = -1;
      for (let i = 0; i < state.trace.steps.length && d < 0; i += 1) {
        if (stageInteractionsOf(at(state, i)).length > 0) d = i;
      }
      if (d < 0) continue;
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={at(state, d)} busy={false} dispatch={() => {}} />,
      );
      expect(surfaceCount(html), `${id}: Quan sát vẫn còn bề mặt cam kết`).toBe(0);
      // W4B-2V: họ tìm kiếm dời quan hệ sang `.search-observe` (ngoài cổng).
      expect(
        html.includes("decision-strip") || html.includes("search-observe"),
        `${id}: cổng đã lấy mất quan hệ`,
      ).toBe(true);
      /* W4B-3A — đường vào KHÔNG còn nằm trong HTML của sân khấu; đó chính là
         dải đã gỡ. Hỏi chủ sở hữu mới, và hỏi cả tính KHẢ DỤNG: ở đúng bước có
         vùng cam kết thì lối vào phải mời được (không mờ), nếu không thì bề mặt
         đã bị gác sau một cửa khoá. */
      const entry = challengeEntry(makeAlgorithmModule(id), at(state, d), config);
      expect(entry, `${id}: mất đường vào Thử thách`).not.toBeNull();
      expect(entry!.available, `${id}: cửa khoá ngay tại bước có cam kết`).not.toBe(false);
    }
  });

  it("(D) bước KHÔNG phải điểm quyết định: không bề mặt cam kết nào", () => {
    for (const [id, data] of SCAN) {
      const { config, state } = build(id, data);
      const html = renderToString(
        <AlgorithmWorkspace config={config} state={at(state, 0)} busy={false} dispatch={() => {}} />,
      );
      expect(surfaceCount(html), `${id} bước 0`).toBe(0);
    }
  });

  it("bất biến vẫn bắt được LỖI THỪA: hai bề mặt cùng lúc là đỏ", () => {
    /* Phép đếm phải thật sự đếm. Ghép hai đoạn HTML có nhãn vùng khác nhau —
       nếu `surfaceCount` chỉ trả 0/1 thì nó không bao giờ bắt được ca THỪA. */
    const fake = '<div aria-label="Thao tác sắp xếp"></div>'
      + '<div aria-label="Thao tác với bước tìm kiếm"></div>';
    expect(surfaceCount(fake)).toBe(2);
  });
});

/* ── 5. VÒNG LẶP QUA STORE: PHẢN HỒI LÀ DỮ LIỆU, MÔ PHỎNG KHÔNG ĐỔI ─────── */

describe("W1-IF · nộp qua store không đụng mô phỏng canonical", () => {
  beforeEach(() => useAppStore.getState().reset());

  it("chốt hành động → prediction có kết quả, active.state nguyên vẹn", () => {
    const env: SimulationEnvelope = {
      status: "ok", simulation_id: "algorithm.count_if", domain: "algorithm",
      visual_mode: "2d", title: "t", description: null, notes: null,
      config: {
        problem: { summary: "s", input: "i", output: "o" },
        algorithm_id: "count_if",
        data: { array: ARR, condition: { op: ">=", value: 7 } },
        data_generated: false, notes: null,
      },
    };
    useAppStore.getState().loadEnvelope(env);
    const s0 = useAppStore.getState().active!.state as AlgorithmSimState;
    const d = firstDecision(s0);
    useAppStore.getState().goToStep(d);

    const engineBefore = JSON.stringify(useAppStore.getState().active!.state);
    const m = scanInteractionOf(useAppStore.getState().active!.state as AlgorithmSimState)!;
    useAppStore.getState().submitPrediction(m.actions[0].id);

    expect(useAppStore.getState().prediction).not.toBeNull();
    expect(JSON.stringify(useAppStore.getState().active!.state)).toBe(engineBefore);
  });
});
