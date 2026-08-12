import { beforeAll, describe, expect, it } from "vitest";
import { writeFileSync } from "node:fs";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { offlineCatalog } from "../data/offline-catalog";
import type { SimAction, SimulationModule } from "./types";

/**
 * W4B-4A — KIỂM TRẢI NGHIỆM CHO TOÀN DANH MỤC, ĐO BẰNG HÀNH VI.
 *
 * ─── VÌ SAO KHÔNG TIN BẢNG PHÂN LOẠI CŨ ───────────────────────────────────
 *
 * Ma trận AFTER của wave trước suy loại trải nghiệm từ NĂNG LỰC KHAI BÁO
 * (`explore` có không, `interactionMode` là gì). Hai sự cố đã chứng minh cách
 * suy đó không đủ:
 *
 *   - `web.style_model` khai `exploratory` và được đếm là thao tác-trực-tiếp,
 *     trong khi bài HTML công khai lúc ấy vẫn là `reveal_sequence` giả ở
 *     `generic.rule_scene`;
 *   - `logic.boolean_dag` có bằng chứng trình duyệt đầy đủ mà câu hướng dẫn vẫn
 *     bảo học sinh bấm một đầu vào KHÔNG TỒN TẠI.
 *
 * Khai báo đúng không kéo theo trải nghiệm đúng. Nên bài kiểm này hỏi thẳng
 * CÂU HỎI NGHIỆM THU, bằng cách thực sự phát action lên module:
 *
 *   "Bỏ hết Play/Next/chấm điểm đi, học sinh còn đổi được mô hình và thấy hệ
 *    quả tất định không?"
 *
 * ─── PHÉP ĐO ──────────────────────────────────────────────────────────────
 *
 * Với mỗi target có mẫu offline: dựng state, phát MỌI action mà miền đó khai,
 * và xem `module.apply` có trả về state KHÁC không — KHÔNG đụng tới timeline.
 * `apply` là chủ sở hữu tất định duy nhất, nên "state đổi qua apply" chính là
 * định nghĩa máy-đọc-được của "thao tác được mô hình".
 *
 * Bảng kết quả ghi ra `docs/evaluation/m17/w4b4a-experience/probe.json` để báo
 * cáo đọc lại — KHÔNG chép tay con số nào.
 */

/**
 * Action mà mỗi miền THẬT SỰ nhận — đọc từ chính `apply` của miền.
 *
 * ⚠️ Bản đầu ĐOÁN tên action (`bit0`, `st.config.inputs` cho mọi module logic,
 * lọc `o.type === "switch"` cho generic) và cho ra BA dương tính giả ngược:
 * `binary.decimal_to_binary`, `logic.and_gate`, `generic.rule_scene` đều báo
 * "không thao tác được" trong khi chúng thao tác được thật. Một phép đo sai kiểu
 * đó nguy hiểm hơn không đo, vì nó đọc như bằng chứng.
 *
 * Shape đúng, đọc từ nguồn:
 *   binary.decimal_to_binary : toggle target = CHỈ SỐ dạng chuỗi ("0".."n-1")
 *   logic.and_gate           : toggle target = "A" | "B" (state.inputA/inputB)
 *   logic.boolean_dag        : toggle target = id trong config.inputs
 *   generic.rule_scene       : toggle target = khoá trong state.base (giá trị số)
 */
const DOMAIN_ACTIONS: Record<string, (state: unknown) => SimAction[]> = {
  logic: (s) => {
    const st = s as {
      config?: { inputs?: { id: string }[] };
      inputA?: number; inputB?: number;
    };
    if (st.config?.inputs) {
      return st.config.inputs.map((i) => ({ type: "toggle", target: i.id }) as SimAction);
    }
    // and_gate: hai đầu vào nằm thẳng trên state, không qua config.
    return st.inputA === undefined
      ? []
      : ([{ type: "toggle", target: "A" }, { type: "toggle", target: "B" }] as SimAction[]);
  },
  binary: (s) => {
    const st = s as { bits?: unknown[] };
    const n = Array.isArray(st.bits) ? st.bits.length : 0;
    const toggles = Array.from(
      { length: n },
      (_, i) => ({ type: "toggle", target: String(i) }) as SimAction,
    );
    return [
      ...toggles,
      { type: "set_param", name: "decimal", value: 7 } as SimAction,
      // W4B-4C: base_conversion + character_encoding nay nhận tham số có ràng buộc.
      { type: "set_param", name: "targetBase", value: 8 } as SimAction,
      { type: "set_param", name: "inputValue", value: "1010" } as SimAction,
      { type: "set_param", name: "encoding", value: "unicode_codepoint" } as SimAction,
      { type: "set_param", name: "text", value: "Bê" } as SimAction,
    ];
  },
  network: () => [
    { type: "net_disconnect", a: "A", b: "R1" } as SimAction,
    { type: "net_reset" } as SimAction,
    // W4B-4C: graph_traversal nay chọn được thuật toán và điểm xuất phát.
    { type: "set_param", name: "variant", value: "dfs" } as SimAction,
    { type: "set_param", name: "variant", value: "bfs" } as SimAction,
  ],
  web: () => [
    { type: "set_param", name: "fontSize", value: 32 } as SimAction,
    { type: "set_param", name: "backgroundColor", value: "#fde68a" } as SimAction,
  ],
  algorithm: () => [{ type: "whatif_swap", i: 0, j: 1 } as SimAction],
  generic: (s) => {
    const st = s as { base?: Record<string, unknown> };
    return Object.entries(st.base ?? {})
      .filter(([, v]) => typeof v === "number")
      .map(([id]) => ({ type: "toggle", target: id }) as SimAction);
  },
  /* W4B-4B — database nay nhận `set_param` cho truy vấn có ràng buộc. */
  database: () => [
    { type: "set_param", name: "filter.value", value: "0" } as SimAction,
    { type: "set_param", name: "sort.direction", value: "asc" } as SimAction,
  ],
  /* W4B-4C: tree nay đổi được thứ tự duyệt trên cùng một cây. */
  tree: () => [
    { type: "set_param", name: "variant", value: "inorder" } as SimAction,
    { type: "set_param", name: "variant", value: "postorder" } as SimAction,
  ],
};

interface Row {
  target: string;
  domain: string;
  interactionMode: string;
  steps: number;
  /** Có action nào đổi được state qua `apply` không (KHÔNG dùng timeline). */
  manipulable: boolean;
  actionsTried: number;
  actionsThatChanged: number;
  declaresExplore: boolean;
  declaresPredict: boolean;
  presentsCommitment: boolean;
}

const rows: Row[] = [];

beforeAll(() => {
  if (listSimulations().length === 0) registerAllSimulations();

  const seen = new Set<string>();
  for (const entry of offlineCatalog()) {
    if (seen.has(entry.simId)) continue;
    const mod = getSimulation(entry.simId) as SimulationModule | undefined;
    if (!mod) continue;
    const r = mod.validateConfig((entry.envelope as { config: unknown }).config);
    if (!r.ok) continue;
    let state: unknown;
    try { state = mod.init(r.config); } catch { continue; }
    seen.add(entry.simId);

    const actions = (DOMAIN_ACTIONS[mod.domain] ?? (() => []))(state);
    let changed = 0;
    for (const a of actions) {
      try { if (mod.apply(state, a) !== state) changed += 1; } catch { /* fail-closed = không đổi */ }
    }

    const steps = mod.timeline ? mod.timeline.stepCount(state) : 1;
    let commitment = 0;
    if (mod.timeline && mod.predict?.presentedInStage) {
      for (let i = 0; i < steps; i += 1) {
        if (mod.predict.presentedInStage(mod.timeline.goToStep(state, i))) commitment += 1;
      }
    }

    rows.push({
      target: entry.simId,
      domain: mod.domain,
      interactionMode: mod.interactionMode,
      steps,
      manipulable: changed > 0,
      actionsTried: actions.length,
      actionsThatChanged: changed,
      declaresExplore: !!mod.explore,
      declaresPredict: !!mod.predict,
      presentsCommitment: commitment > 0,
    });
  }
  rows.sort((a, b) => a.target.localeCompare(b.target));

  try {
    writeFileSync(
      new URL("../../../docs/evaluation/m17/w4b4a-experience/probe.json", import.meta.url),
      JSON.stringify({ when: new Date().toISOString(), rows }, null, 2),
      "utf-8",
    );
  } catch { /* thư mục chưa có ở lượt chạy đầu — bảng vẫn kiểm được */ }
});

describe("W4B-4A · câu hỏi nghiệm thu chạy trên toàn danh mục", () => {
  it("phép đo phải thật sự chạm được danh mục", () => {
    expect(rows.length, "không dựng được target nào — phép dò hỏng?").toBeGreaterThan(10);
  });

  it("phép đo phải PHÂN BIỆT ĐƯỢC thao-tác-được và identity", () => {
    /* MỒI HAI CHIỀU. Bản đầu của phép đo này đoán sai tên action và báo ba
       target "không thao tác được" trong khi chúng thao tác được — một phép đo
       im lặng sai đọc y hệt một phép đo sạch. Nên chứng minh nó phân biệt được
       trước khi tin bất kỳ con số nào. */
    const changing = { apply: (s: unknown) => ({ ...(s as object) }) } as unknown as SimulationModule;
    const identity = { apply: (s: unknown) => s } as unknown as SimulationModule;
    const probe = { a: 1 };
    expect(changing.apply(probe, { type: "toggle", target: "x" }) !== probe,
      "mồi DƯƠNG không được nhận diện").toBe(true);
    expect(identity.apply(probe, { type: "toggle", target: "x" }) !== probe,
      "mồi ÂM bị nhận nhầm thành thao tác được").toBe(false);

    // Và trên danh mục thật, phép đo phải thấy CẢ HAI loại — toàn 0 hoặc toàn 1
    // đều là dấu hiệu phép đo hỏng chứ không phải sự thật.
    expect(rows.some((r) => r.manipulable), "không target nào thao tác được?").toBe(true);
    expect(rows.some((r) => !r.manipulable), "mọi target đều thao tác được?").toBe(true);
  });

  it("mọi target khai `explore` đều PHẢI đổi được state qua `apply`", () => {
    /* Đây là chỗ bắt "khai báo không kéo theo hành vi": một module nói nó có
       chế độ Khám phá mà không action nào đổi được mô hình thì lối vào ấy là
       lời hứa suông. */
    const liars = rows.filter((r) => r.declaresExplore && !r.manipulable);
    expect(liars.map((r) => r.target), "khai Khám phá nhưng không thao tác được").toEqual([]);
  });

  it("mọi target ĐỔI ĐƯỢC mô hình đều phải bày lối vào (không giấu năng lực)", () => {
    /* Chiều ngược lại: thao tác được mà không khai `explore` thì học sinh không
       có đường nào biết. Ngoại lệ: bài `exploratory`/`hybrid` — cả sân khấu LÀ
       chỗ thao tác, luôn mở, không cần cổng. */
    const hidden = rows.filter(
      (r) => r.manipulable && !r.declaresExplore
        && r.interactionMode !== "exploratory" && r.interactionMode !== "hybrid",
    );
    expect(hidden.map((r) => r.target), "thao tác được nhưng không có lối vào").toEqual([]);
  });

  it("KHÔNG target nào chỉ-có-timeline mà bị khai là thao tác trực tiếp", () => {
    /* `reveal_sequence` hay bất kỳ chuỗi bước nào KHÔNG phải thao tác. Bắt đúng
       ca đã ship một lần: bài HTML "từng bước" ở `generic.rule_scene`. */
    const fake = rows.filter((r) => !r.manipulable && r.declaresExplore);
    expect(fake.map((r) => r.target), "chuỗi bước bị tính là thao tác").toEqual([]);
  });

  it("cam kết KHÔNG được tính là thao tác trực tiếp", () => {
    /* `predict.check` phán đúng/sai; đó là CAM KẾT. Một target chỉ có cam kết mà
       không đổi được mô hình thì không phải mô hình tương tác. */
    for (const r of rows) {
      if (r.presentsCommitment && !r.manipulable) {
        expect(r.declaresExplore, `${r.target}: cam kết bị bày như Khám phá`).toBe(false);
      }
    }
  });
});
