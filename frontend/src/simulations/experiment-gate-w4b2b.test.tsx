import { describe, expect, it, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./domains/algorithm";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import {
  scanInteractionOf,
  searchInteractionOf,
  sortInteractionOf,
  stageInteractionsOf,
} from "./domains/algorithm/decision";
import { whatIfPolicyOf } from "./domains/algorithm/interaction-policy";
import { registerAllSimulations } from "./index";
import { useAppStore } from "../state/store";
import type { AlgorithmSimState } from "./domains/algorithm";
import { ALGORITHM_IDS, type AlgorithmId } from "../core/types";
import type { SimulationEnvelope } from "./types";

registerAllSimulations();

/**
 * W4B-2B — CỔNG THÍ NGHIỆM (PILOT `find_max` + `insertion_sort`).
 *
 * Vòng học được nhắm tới: QUAN SÁT → học sinh TỰ MỞ Thí nghiệm → công cụ cam kết
 * hiện ra → `submitPrediction` → `predict.check` → phản hồi.
 *
 * Điều khó nhất phải khoá không phải "nút có ẩn không", mà là RANH GIỚI SỞ HỮU:
 * cổng là TRÌNH BÀY THUẦN, nên nó không được chạm engine state, không được đẻ
 * thêm một bên chấm đúng/sai, và không được lộ đáp án sớm.
 */

const ARR = [7.5, 9, 6.5, 8, 5.5, 8.5, 7, 6];
const SORT_ARR = [4, 9, 2, 11, 7, 5];

/** Hai bài pilot — đọc từ CHÍNH bản khai, không chép tay danh sách id. */
const GATED = ALGORITHM_IDS.filter((id) => whatIfPolicyOf(id).experimentGated === true);

/* W4B-2D: họ tìm kiếm cần `target`, và nhị phân cần dãy ĐÃ SẮP (validator từ
   chối dãy chưa sắp). Trước wave này hai bài đó chưa gác cổng nên không lượt
   nào của `GATED` chạm tới chúng; nay có. */
const SORTED_ARR = [...ARR].sort((a, b) => a - b);

/**
 * Dữ liệu hợp lệ TỐI THIỂU cho một bài — MỘT nguồn duy nhất.
 *
 * Trước W4B-2D khối envelope ở §13 dựng lại dữ liệu bằng tay, nên khi họ tìm
 * kiếm vào `GATED` thì `build()` được vá còn khối kia thì không: `loadEnvelope`
 * lặng lẽ trả `active = null` và test đổ ở `.state` với một thông báo chẳng liên
 * quan. Hai bản sao của cùng một tri thức là một bản sẽ hết hạn.
 */
function dataFor(id: AlgorithmId, extra: Record<string, unknown> = {}) {
  return {
    array: id.endsWith("_sort") ? SORT_ARR : id === "binary_search" ? SORTED_ARR : ARR,
    ...(id.endsWith("_sort") ? { order: "asc" } : {}),
    ...(id === "count_if" || id === "sum_if" ? { condition: { op: ">=", value: 7 } } : {}),
    ...(id === "linear_search" || id === "binary_search" ? { target: 8 } : {}),
    ...extra,
  };
}

function build(id: AlgorithmId, data: Record<string, unknown> = {}) {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: { summary: "s", input: "i", output: "o" },
    algorithm_id: id,
    data: dataFor(id, data),
    data_generated: false,
    notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) };
}

const at = (s: AlgorithmSimState, cursor: number): AlgorithmSimState => ({ ...s, cursor });

/**
 * Bóc chú thích trước khi quét mã nguồn: repo này CỐ Ý nhắc tên thứ đã cấm trong
 * chú thích để ghi lại vì sao cấm (`ui.tsx` viết thẳng "không có
 * `if (moduleId === ...)` nào trong shell"). Quét cả chú thích thì test tự bắt
 * chính lời giải thích của nó — đúng khuôn `code()` ở `ui-hygiene.test.ts`.
 */
function code(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
}

/**
 * Bước quyết định đầu tiên — dùng chính hàm mà production dùng.
 *
 * W4B-2D: đổi sang `stageInteractionsOf` (phủ scan + SEARCH + sort) thay vì gọi
 * tay hai hàm. Bản cũ liệt kê hai họ đang được gác lúc đó, nên khi họ tìm kiếm
 * vào `GATED` thì mọi lượt của nó ném "không tìm được bước có thể cam kết" —
 * một danh sách chép tay lại hết hạn đúng lúc nó cần đúng nhất.
 */
function firstActionable(s: AlgorithmSimState): number {
  for (let i = 0; i < s.trace.steps.length; i += 1) {
    if (stageInteractionsOf(at(s, i)).length > 0) return i;
  }
  throw new Error("không tìm được bước có thể cam kết");
}

/**
 * Mô hình tương tác của bước — BẤT KỂ họ nào. Trước W4B-2D các chỗ dùng đều
 * viết `scanInteractionOf(cur) ?? sortInteractionOf(cur)`, tức chép tay danh
 * sách họ tại thời điểm viết; thêm họ thứ ba là ba chỗ cùng hỏng.
 */
function stageModel(s: AlgorithmSimState): { actions: { id: string }[] } {
  const m = scanInteractionOf(s) ?? searchInteractionOf(s) ?? sortInteractionOf(s);
  if (!m) throw new Error("bước này không có mô hình tương tác");
  return m;
}

const observeHtml = (id: AlgorithmId) => {
  const { config, state } = build(id);
  return renderToString(
    <AlgorithmWorkspace
      config={config}
      state={at(state, firstActionable(state))}
      busy={false}
      dispatch={() => {}}
    />,
  );
};

/* ══ 1. PILOT ĐÚNG HAI BÀI ════════════════════════════════════════════════ */

describe("W4B-2B · cổng là PILOT, không phải rollout cả họ", () => {
  it("W4B-2D: đúng BẢY target được gác — quét dãy + insertion_sort + họ tìm kiếm", () => {
    expect([...GATED].sort()).toEqual([
      "binary_search", "count_if", "find_max", "find_min",
      "insertion_sort", "linear_search", "sum_if",
    ]);
  });

  it("HAI bài sắp xếp còn lại KHÔNG bị kéo theo — họ sắp xếp là wave sau", () => {
    /* §31/§33: mở rộng dừng đúng ở họ tìm kiếm. `bubble_sort`/`selection_sort`
       phải giữ nguyên hành vi — vùng cam kết vẫn hiện thẳng ở Quan sát, không
       có cổng nào. Đây cũng là thứ giữ cho ca (A) của bất biến bề mặt cam kết
       còn bài làm chứng. */
    for (const id of ["bubble_sort", "selection_sort"] as AlgorithmId[]) {
      expect(whatIfPolicyOf(id).experimentGated, `${id} bị kéo vào wave này`).toBeUndefined();
    }
  });

  it("§12/§16 — gác cổng KHÔNG bật kéo cho bài `hidden`", () => {
    /* count_if/sum_if: kéo là trang trí (bất biến theo thứ tự duyệt). Thứ tự
       kiểm trong `ui.tsx` đặt `hidden` TRƯỚC cổng; test này khoá đúng thứ tự đó
       ở tầng khai báo để không ai đảo nó rồi biến đếm thành bài kéo-thả. */
    for (const id of ["count_if", "sum_if"] as AlgorithmId[]) {
      const p = whatIfPolicyOf(id);
      expect(p.experimentGated, `${id}`).toBe(true);
      expect(p.mode, `${id}: mode đổi ⇒ kéo có thể bật theo`).toBe("hidden");
    }
  });

  it("shell KHÔNG quyết định bằng tên bài — cổng dẫn xuất từ policy", () => {
    const src = code(readFileSync(new URL("./domains/algorithm/ui.tsx", import.meta.url), "utf-8"));
    // anti-pattern #2: mọi quyết định suy từ capability, không từ định danh bài
    expect(src).not.toMatch(/algorithm_id\s*===\s*["']/);
    expect(src).not.toMatch(/moduleId\s*===\s*["']/);
    expect(src).toMatch(/policy\.experimentGated/);
  });
});

/* ══ 2. QUAN SÁT SẠCH, NHƯNG KHÔNG NGHÈO ĐI ═══════════════════════════════ */

describe("W4B-2B §7/§18 · Quan sát ẩn CAM KẾT, giữ QUAN HỆ", () => {
  it("không vùng cam kết nào ở chế độ Quan sát", () => {
    for (const id of GATED) {
      const html = observeHtml(id);
      // W4B-2D: thêm nhãn của họ tìm kiếm — thiếu nó thì bài mới gác cổng đi
      // qua test này mà không bị kiểm gì cả.
      for (const label of [
        "Thao tác với biến tích luỹ", "Thao tác sắp xếp", "Thao tác với bước tìm kiếm",
      ]) {
        expect(html, `${id}: còn "${label}" ở Quan sát`).not.toContain(`aria-label="${label}"`);
      }
      expect(html, `${id}: PredictionBar thế chỗ vùng cam kết`).not.toContain('class="predict-bar"');
    }
  });

  it("không nhãn cam kết nào lọt ra Quan sát", () => {
    const html = observeHtml("find_max" as AlgorithmId);
    for (const leak of ["Đặt ", "Giữ max"]) {
      expect(html, `còn nhãn cam kết "${leak}"`).not.toContain(leak);
    }
  });

  it("QUAN HỆ đang xét vẫn ở lại — cổng không được lấy mất dữ kiện quan sát", () => {
    for (const id of GATED) {
      expect(observeHtml(id), `${id}: mất dải quan hệ`).toContain("decision-strip");
    }
  });

  it("cổng nhìn thấy được và là NÚT thật (bàn phím tới được, có aria-expanded)", () => {
    for (const id of GATED) {
      const html = observeHtml(id);
      expect(html, `${id}: không có nút Thí nghiệm`).toContain("Thí nghiệm");
      expect(html, `${id}: cổng không khai trạng thái mở/đóng`).toContain('aria-expanded="false"');
      // <button> gốc ⇒ Tab tới được, Enter/Space kích hoạt được, không cần chuột
      expect(html, `${id}: cổng không phải <button>`).toMatch(/<button[^>]*>(?:(?!<\/button>)[\s\S])*Thí nghiệm/);
    }
  });
});

/* ══ 3. KHÔNG RÒ ĐÁP ÁN (§10) ═════════════════════════════════════════════ */

describe("W4B-2B §10 · Thí nghiệm bày LỰA CHỌN, không bày cái nào đúng", () => {
  it("mô hình tương tác không mang đáp án dưới bất kỳ tên nào", () => {
    for (const id of GATED) {
      const { state } = build(id);
      const cur = at(state, firstActionable(state));
      const model = stageModel(cur) as unknown as Record<string, unknown>;
      for (const forbidden of ["correctActionId", "expectedId", "expectedAction", "evidence", "result"]) {
        expect(Object.keys(model), `${id}: lộ ${forbidden}`).not.toContain(forbidden);
      }
    }
  });

  it("DOM ở Quan sát không mang trạng thái TƯƠNG LAI của cơ chế", () => {
    // find_max: max cuối cùng là 9; ở bước quyết định ĐẦU max mới là 7,5.
    const { state, config } = build("find_max" as AlgorithmId);
    const cur = at(state, firstActionable(state));
    const html = renderToString(
      <AlgorithmWorkspace config={config} state={cur} busy={false} dispatch={() => {}} />,
    );
    expect(html).not.toContain("đáp án");
    // kết quả cuối chỉ được công bố ở bước cuối
    const done = state.trace.steps.at(-1)!.events.find((e) => e.type === "done") as
      | { result: string }
      | undefined;
    expect(html, "công bố kết quả cuối ngay ở bước giữa").not.toContain(done!.result);
  });
});

/* ══ 4. CỔNG LÀ TRÌNH BÀY THUẦN (§3, §13) ═════════════════════════════════ */

describe("W4B-2B §13 · mở/đóng Thí nghiệm KHÔNG chạm engine state", () => {
  beforeEach(() => useAppStore.getState().reset());

  it("`labOpen` là state CỤC BỘ — không có đường nào từ nó vào store/dispatch", () => {
    const src = readFileSync(new URL("./domains/algorithm/ui.tsx", import.meta.url), "utf-8");
    expect(src).toMatch(/const \[labOpen, setLabOpen\] = useState\(false\)/);
    // setLabOpen chỉ được gọi với hằng true/false, không đi kèm dispatch/submit
    for (const m of src.matchAll(/setLabOpen\(([^)]*)\)/g)) {
      expect(["true", "false"], `setLabOpen(${m[1]}) không phải hằng`).toContain(m[1].trim());
    }
    expect(src).not.toMatch(/setLabOpen[\s\S]{0,120}dispatch\(/);
    expect(src).not.toMatch(/setLabOpen[\s\S]{0,120}submitPrediction\(/);
  });

  it("đổi trạng thái TRÌNH BÀY quanh mô phỏng không đổi state/cursor canonical", () => {
    for (const id of GATED) {
      const env: SimulationEnvelope = {
        status: "ok", simulation_id: `algorithm.${id}`, domain: "algorithm",
        visual_mode: "2d", title: "t", description: null, notes: null,
        config: {
          problem: { summary: "s", input: "i", output: "o" },
          algorithm_id: id,
          data: dataFor(id),
          data_generated: false, notes: null,
        },
      };
      useAppStore.getState().reset();
      useAppStore.getState().loadEnvelope(env);
      const st0 = useAppStore.getState().active!.state as AlgorithmSimState;
      useAppStore.getState().goToStep(firstActionable(st0));

      const before = JSON.stringify(useAppStore.getState().active!.state);
      const cursorBefore = (useAppStore.getState().active!.state as AlgorithmSimState).cursor;

      // Giải thích mở/đóng nhiều lần — bề mặt trình bày duy nhất sống ở store
      for (let i = 0; i < 4; i += 1) useAppStore.getState().toggleRight();

      expect(JSON.stringify(useAppStore.getState().active!.state), `${id}`).toBe(before);
      expect((useAppStore.getState().active!.state as AlgorithmSimState).cursor, `${id}`)
        .toBe(cursorBefore);
      expect(useAppStore.getState().prediction, `${id}: cổng trình bày làm bẩn prediction`)
        .toBeNull();
    }
  });
});

/* ══ 5. KHÔNG CÓ BÊN CHẤM THỨ HAI (§4, §24) ═══════════════════════════════ */

describe("W4B-2B §4 · `predict.check` vẫn là bên chấm DUY NHẤT", () => {
  it("cam kết đi qua submitPrediction → predict.check, phản hồi sống ở store", () => {
    for (const id of GATED) {
      const { mod, state } = build(id);
      const cur = at(state, firstActionable(state));
      const model = stageModel(cur);
      const ids = model.actions.map((a) => a.id);

      // đúng một đáp án được engine chấm là đúng — engine, không phải renderer
      const verdicts = ids.map((a) => mod.predict!.check(cur, a).verdict);
      /* W4B-2D: `binary_search` bày tới BA hành động (trái / giữa / phải), nên
         "đúng 1 sai 1" là con số của hai họ cũ, không phải bất biến. Bất biến
         thật: engine chấm ĐÚNG MỘT lựa chọn là đúng, mọi lựa chọn còn lại sai —
         và không lựa chọn nào rơi ra ngoài hai phán quyết đó. */
      expect(verdicts.filter((v) => v === "correct").length, `${id}: ${verdicts}`).toBe(1);
      expect(verdicts.filter((v) => v === "incorrect").length, `${id}: ${verdicts}`)
        .toBe(ids.length - 1);
    }
  });

  it("renderer/ActionZone không tự chấm: không có bên chấm nào ngoài predict.check", () => {
    for (const file of ["../components/ScanActionZone.tsx", "../components/SortActionZone.tsx",
                        "./domains/algorithm/ui.tsx"]) {
      const src = code(readFileSync(new URL(file, import.meta.url), "utf-8"));
      for (const forbidden of ["correctActionId", "isCorrect(", "checkAnswer(", "evaluate("]) {
        expect(src, `${file}: dựng bên chấm thứ hai (${forbidden})`).not.toContain(forbidden);
      }
    }
  });
});
