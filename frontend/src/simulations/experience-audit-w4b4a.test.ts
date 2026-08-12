import { beforeAll, describe, expect, it } from "vitest";
import { writeFileSync } from "node:fs";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { offlineCatalog } from "../data/offline-catalog";
import { exploreEntry } from "../components/SimulationWorkspace";
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
  /* W4B-4D: `count_if`/`sum_if` nay đổi được CHÍNH ĐIỀU KIỆN. Ngưỡng lấy từ
     dãy của bài — viết cứng một con số thì nó rơi ngoài miền ở bài khác và phép
     đo lại báo "không thao tác được" vì lý do sai. */
  algorithm: (s) => {
    const st = s as { config?: { data?: { array?: number[]; condition?: unknown } } };
    const arr = st.config?.data?.array ?? [];
    const acts: SimAction[] = [{ type: "whatif_swap", i: 0, j: 1 } as SimAction];
    if (st.config?.data?.condition && arr.length) {
      acts.push({ type: "set_param", name: "condition.op", value: "<" } as SimAction);
      acts.push({ type: "set_param", name: "condition.value", value: Math.max(...arr) } as SimAction);
      acts.push({ type: "set_param", name: "condition.value", value: Math.min(...arr) } as SimAction);
    }
    return acts;
  },
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
  /**
   * W4B-4D — CÁNH CỬA THẬT, khác hẳn `declaresExplore`.
   *
   * `declaresExplore` chỉ nói module có KHAI năng lực `explore` hay không, mà
   * mọi module thuật toán đều khai chung một khối — nên nó bằng `true` kể cả ở
   * bài mà `explore.entry()` trả `null` và học sinh KHÔNG hề thấy cửa nào. Đo
   * bằng cờ đó là đo lời khai, không đo trải nghiệm; nó đã che đúng một dương
   * tính giả: `count_if`/`sum_if` "thao tác được" bằng kéo-thả trong khi chính
   * sách của chúng tắt kéo, nên không lối nào phát nổi action ấy.
   */
  hasExploreEntry: boolean;
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
      hasExploreEntry: exploreEntry(mod, state, r.config) !== null,
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

  it("mọi target MỞ ĐƯỢC cửa Khám phá đều PHẢI đổi được state qua `apply`", () => {
    /* Đây là chỗ bắt "khai báo không kéo theo hành vi": một module mời vào chế
       độ Khám phá mà không action nào đổi được mô hình thì lời mời là hứa suông. */
    const liars = rows.filter((r) => r.hasExploreEntry && !r.manipulable);
    expect(liars.map((r) => r.target), "mời Khám phá nhưng không thao tác được").toEqual([]);
  });

  it("mọi target ĐỔI ĐƯỢC mô hình đều phải bày lối vào (không giấu năng lực)", () => {
    /* Chiều ngược lại: thao tác được mà không có CỬA thì học sinh không có đường
       nào biết. Ngoại lệ: bài `exploratory`/`hybrid` — cả sân khấu LÀ chỗ thao
       tác, luôn mở, không cần cổng.

       W4B-4D — VẾ NÀY TỪNG ĐO NHẦM. Nó đọc `declaresExplore`, mà mọi module
       thuật toán khai chung một khối `explore`, nên cờ ấy luôn `true` kể cả khi
       `entry()` trả `null`. `count_if`/`sum_if` vì thế đi lọt: engine nhận
       `whatif_swap` nên chúng tính là "thao tác được", trong khi chính sách của
       chúng tắt kéo và không cửa nào phát nổi action đó. Đọc CỬA thì hết lọt. */
    const hidden = rows.filter(
      (r) => r.manipulable && !r.hasExploreEntry
        && r.interactionMode !== "exploratory" && r.interactionMode !== "hybrid",
    );
    expect(hidden.map((r) => r.target), "thao tác được nhưng không có lối vào").toEqual([]);
  });

  it("KHÔNG target nào chỉ-có-timeline mà bị khai là thao tác trực tiếp", () => {
    /* `reveal_sequence` hay bất kỳ chuỗi bước nào KHÔNG phải thao tác. Bắt đúng
       ca đã ship một lần: bài HTML "từng bước" ở `generic.rule_scene`. */
    const fake = rows.filter((r) => !r.manipulable && r.hasExploreEntry);
    expect(fake.map((r) => r.target), "chuỗi bước bị tính là thao tác").toEqual([]);
  });

  it("cam kết KHÔNG được tính là thao tác trực tiếp", () => {
    /* `predict.check` phán đúng/sai; đó là CAM KẾT. Một target chỉ có cam kết mà
       không đổi được mô hình thì không phải mô hình tương tác. */
    for (const r of rows) {
      if (r.presentsCommitment && !r.manipulable) {
        expect(r.hasExploreEntry, `${r.target}: cam kết bị bày như Khám phá`).toBe(false);
      }
    }
  });
});

/* ══ QUYẾT ĐỊNH GIỮ-TRACE PHẢI KHAI TƯỜNG MINH ═══════════════════════════ */

/**
 * W4B-4C — BA target CỐ Ý giữ nguyên dạng trace, kèm lý do CƠ CHẾ.
 *
 * Đây không phải danh sách "chưa kịp làm". Mỗi dòng là một phán quyết: cơ chế
 * của bài LÀ tiến trình theo thời gian, nên thêm tham số cho học sinh chỉnh chỉ
 * làm tăng con số tương tác chứ không dạy thêm gì.
 *
 * Danh sách này ĐƯỢC PHÉP NGẮN ĐI (một target tìm ra tham số có nghĩa thì
 * chuyển sang tương tác và xoá khỏi đây), nhưng DÀI RA thì phải giải trình:
 * thêm một dòng nghĩa là vừa hạ cấp một trải nghiệm.
 */
const KEEP_TRACE: Record<string, string> = {
  "algorithm.bounded_control_flow":
    "Cơ chế LÀ luồng điều khiển chạy theo thời gian: gán, rẽ nhánh, lặp có biên. " +
    "Thứ đáng đổi là CHÍNH CHƯƠNG TRÌNH, mà cho sửa chương trình thì đây thành " +
    "một IDE — vượt ranh giới 'không thực thi mã tuỳ ý' của đề tài. Đổi giá trị " +
    "khởi tạo thì được, nhưng nó không dạy thêm gì so với việc xem biến biến đổi.",
  "algorithm.scan":
    "Quét một lượt là bài học VỀ TRÌNH TỰ: mỗi phần tử được xét đúng một lần, " +
    "theo thứ tự. Tham số duy nhất đáng đổi là dãy đầu vào, và dựng một trình " +
    "soạn dãy tổng quát chỉ để tăng số tương tác chính là thứ §25 cấm. Tám bài " +
    "quét chuyên biệt đã có thao tác riêng; `scan` là catch-all cho biến thể.",
  "network.protocol_encapsulation":
    "Đóng gói qua từng tầng là biến đổi TUẦN TỰ có hướng: mỗi tầng bọc thêm một " +
    "lớp lên PDU của tầng trước. Trình tự ấy CHÍNH LÀ khái niệm; cho kéo thả các " +
    "lớp sẽ dựng ra những trạng thái không tồn tại trong giao thức thật. Giữ 2D/3D " +
    "cùng một sự thật tất định.",
};

describe("W4B-4C · giữ-trace là QUYẾT ĐỊNH, không phải chỗ trống", () => {
  it("mọi target không thao tác được đều phải có lý do cơ chế khai sẵn", () => {
    const undecided = rows
      .filter((r) => !r.manipulable)
      .map((r) => r.target)
      .filter((id) => !KEEP_TRACE[id]);
    expect(undecided, "target chỉ-trace mà chưa ai quyết định").toEqual([]);
  });

  it("danh sách giữ-trace không được chứa target ĐÃ thao tác được", () => {
    /* Chiều ngược: nếu một bài đã có tương tác thật mà vẫn nằm trong danh sách
       này thì lý do đã lỗi thời, và một lý do lỗi thời là một lời giải thích
       sai cho người đọc sau. */
    const stale = Object.keys(KEEP_TRACE).filter(
      (id) => rows.find((r) => r.target === id)?.manipulable,
    );
    expect(stale, "lý do giữ-trace đã lỗi thời").toEqual([]);
  });

  it("mỗi lý do phải nói về CƠ CHẾ, không phải về tiến độ công việc", () => {
    for (const [id, why] of Object.entries(KEEP_TRACE)) {
      expect(why.length, `${id}: lý do quá cụt để kiểm chứng`).toBeGreaterThan(80);
      for (const excuse of ["chưa kịp", "sau này", "TODO", "tạm thời"]) {
        expect(why, `${id}: lý do là lời hứa, không phải phán quyết`).not.toContain(excuse);
      }
    }
  });
});
