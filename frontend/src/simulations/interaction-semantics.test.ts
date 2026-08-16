import { describe, expect, it } from "vitest";
import { mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { publicCatalog } from "../data/offline-catalog";
import { provenance } from "../../scripts/evidence.mjs";
import type { SimulationModule } from "./types";

/**
 * W12-B0 — BỐN LOẠI HÀNH ĐỘNG, KHÔNG GỘP MỌI CÚ BẤM THÀNH "TƯƠNG TÁC".
 *
 * ─── VÌ SAO WAVE NÀY TỒN TẠI ──────────────────────────────────────────────
 *
 * Màn hình `algorithm.find_max` đọc ra: nhìn mô hình → đọc câu hỏi → bấm một
 * trong hai nút → engine chấm. Đó là ĐÁNH GIÁ BÁM CƠ CHẾ, và nó tốt — nhưng nó
 * KHÔNG phải thao tác mô hình. Con số "14 CERTIFIED" ở lượt trước không phân
 * biệt hai thứ ấy, nên nó chưa nói được điều người đọc tưởng nó nói.
 *
 * ─── CÂU HỎI CỔNG (§20) ───────────────────────────────────────────────────
 *
 *   "Khi ĐÓNG thử thách, học sinh thao tác lên cái gì?"
 *
 * "Một phương án trả lời" KHÔNG phải câu trả lời hợp lệ — nó thuộc THỬ THÁCH.
 *
 * ─── BỐN LOẠI ─────────────────────────────────────────────────────────────
 *
 *   MODEL_MANIPULATION  đổi state MIỀN có thẩm quyền
 *   MECHANISM_COMMITMENT quyết định của chính thuật toán
 *   TRACE_CONTROL       điều khiển quan sát tiến trình
 *   CHALLENGE           dự đoán / chấm — KHÔNG BAO GIỜ tính là thao tác mô hình
 */

const SIMS = new URL(".", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");

/**
 * AFFORDANCE TRÊN SÂN KHẤU — quét mã renderer của MIỀN để biết action nào
 * thật sự có đường bấm/kéo, không chỉ tồn tại trong `apply`.
 *
 * §14 gọi ca ngược lại là `AFFORDANCE_MISSING`: `apply` nhận một action mà học
 * sinh không có cách nào phát ra nó. Một chứng nhận đọc `apply` mà không đọc
 * renderer sẽ bỏ lọt đúng ca ấy.
 */
function stageActionsOf(domain: string): string[] {
  const dir = join(SIMS, "domains", domain);
  let files: string[] = [];
  try {
    files = readdirSync(dir).filter((f) => /\.tsx?$/.test(f) && !/\.test\./.test(f))
      .map((f) => join(dir, f));
  } catch { return []; }
  const found = new Set<string>();
  for (const f of files) {
    if (statSync(f).isDirectory()) continue;
    const body = readFileSync(f, "utf-8")
      .replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    for (const m of body.matchAll(/dispatch\(\s*\{\s*type:\s*"([a-z_]+)"/g)) found.add(m[1]);
    /* `ArrayView` nhận `onSwap` rồi renderer miền mới dispatch — bắt cả cầu nối
       ấy, nếu không một affordance thật sẽ đọc thành thiếu. */
    if (/onSwap=\{/.test(body)) found.add("whatif_swap");
  }
  return [...found].sort();
}

/**
 * BA CÂU HỎI TÁCH BẠCH — và câu (B) là câu bị bỏ qua ở lượt trước.
 *
 *   (A) Mô hình có thao tác được không?
 *   (B) Thao tác ấy có LIÊN QUAN tới cơ chế đang dạy không?
 *   (C) Nó có phải hành động CHÍNH và THẤY ĐƯỢC trên UI thật không?
 *
 * `find_max` trả lời (A) là CÓ — kéo cột phát `whatif_swap`, state đổi thật.
 * Nhưng (B) là KHÔNG: `whatif_swap` sắp xếp lại DỮ LIỆU VÀO, trong khi cơ chế
 * đang dạy là "ứng viên có lớn hơn max hiện tại không". Đổi thứ tự đầu vào
 * không cho học sinh tác động lên chính phép so sánh ấy.
 *
 * Nên một action đổi được state KHÔNG tự động là bằng chứng cho "mô phỏng
 * tương tác". Phải hỏi nó đụng tới ĐỐI TƯỢNG HỌC hay chỉ đụng ĐẦU VÀO của
 * đối tượng ấy.
 */
const ACTION_ROLE: Record<string, "INPUT" | "MECHANISM"> = {
  /* Sắp xếp lại dãy = đổi ĐỀ BÀI, không phải tham gia vào phép quét. */
  whatif_swap: "INPUT",
  /* Đổi điều kiện/tham số = cũng đổi đề bài. Với target mà THAM SỐ CHÍNH LÀ bài
     học (đổi cơ số, đổi chuỗi mã hoá, đổi bộ lọc) thì vai trò được nâng lên
     MECHANISM bằng bảng `MECHANISM_PARAM_TARGETS` bên dưới. */
  set_param: "INPUT",
  /* Bật/tắt công tắc logic, bật/tắt bit: quan hệ vào→ra CHÍNH LÀ bài học. */
  toggle: "MECHANISM",
  /* Dời khối trong trang: cấu trúc tài liệu chính là thứ đang dạy. */
  move: "MECHANISM",
  /* Nối/ngắt liên kết mạng: topology chính là thứ định tuyến phụ thuộc vào. */
  net_connect: "MECHANISM",
  net_disconnect: "MECHANISM",
  net_reset: "MECHANISM",
};

/**
 * Target mà THAM SỐ chính là đối tượng học — ở đó `set_param` được nâng vai trò.
 *
 * Mỗi dòng phải nói vì sao, nếu không bảng này thành cách lách để mọi target
 * đều "tương tác".
 */
const MECHANISM_PARAM_TARGETS: Record<string, string> = {
  "binary.base_conversion":
    "Cơ số nguồn/đích và giá trị LÀ bài học (quan hệ chữ số ↔ trọng số), không phải đầu vào của một cơ chế khác.",
  "binary.character_encoding":
    "Chuỗi ký tự và bảng mã LÀ bài học — đổi chúng là đổi chính thứ đang được mã hoá.",
  "database.relational_table_query":
    "Bộ lọc/chiếu/sắp LÀ truy vấn đang được dạy; đổi chúng là thực hiện chính thao tác của bài.",
  "web.style_model":
    "Thuộc tính trình bày LÀ quan hệ CSS đang dạy — đổi padding/màu là thực hiện bài học.",
  "color.rgb_model":
    "Ba kênh 0..255 LÀ cơ chế đang dạy — màu là kết quả của chính chúng, không phải đầu vào của một quá trình nào khác.",
  "network.graph_traversal":
    "Chọn BFS/DFS là chọn chính thuật toán đang so sánh, không phải đổi dữ liệu vào.",
  "tree.traversal":
    "Chọn kiểu duyệt là chọn chính định nghĩa đang dạy — bốn kiểu cho bốn dãy kết quả khác nhau.",
};

/** Action chỉ điều hướng nhánh — không đổi bài toán, nhưng vẫn là state miền. */
const BRANCH_ACTIONS = new Set(["exit_branch"]);

interface Row {
  id: string;
  domain: string;
  /** Câu trả lời cho câu hỏi cổng §20. */
  manipulatesWhenChallengeClosed: string;
  stageActions: string[];
  /** Action mà CHÍNH module này nhận (thử `apply`, so state). */
  acceptedByModule: string[];
  /** Đụng ĐỐI TƯỢNG HỌC. */
  mechanismActions: string[];
  /** Chỉ đổi ĐẦU VÀO của cơ chế. */
  inputActions: string[];
  hasChallenge: boolean;
  hasTimeline: boolean;
  primaryType: string;
}

/**
 * Action nào MODULE NÀY thật sự nhận — thử `apply` rồi so state.
 *
 * ⚠️ Bản đầu chỉ quét thư mục miền, nên mọi target trong một miền thừa hưởng
 * mọi action tìm thấy ở bất kỳ file nào của miền ấy. Kết quả: 23/23
 * INTERACTIVE_MODEL — một con số sai, vì `algorithm.scan` và
 * `algorithm.bounded_control_flow` có `apply: (state) => state` (không nhận
 * action nào) mà vẫn được ghi là thao tác được nhờ `whatif_swap` của file khác.
 *
 * Nên phép kiểm phải HAI VẾ: action đổi được state của CHÍNH module này, VÀ có
 * affordance phát ra nó trong renderer miền.
 */
function acceptedByModule(m: SimulationModule<unknown, unknown>, candidates: string[]): string[] {
  /* Config lấy từ CHÍNH danh mục mẫu đã validate — không viết fixture tay. Một
     fixture tay là một hợp đồng thứ hai sẽ trôi khỏi sản phẩm. */
  const entry = publicCatalog().find((e) => e.simId === m.id);
  if (!entry) return [];
  const parsed = m.validateConfig((entry.envelope as { config: unknown }).config);
  if (!parsed.ok) return [];
  const base = m.init(parsed.config);
  /* PROBE DẪN TỪ CONFIG THẬT, KHÔNG ĐOÁN TÊN.
     Năm target từng đọc ra `PROBE_LIMITED` chỉ vì tôi đoán id: logic dùng
     `N/G/K` chứ không phải `A`, mạng dùng `client/router/isp/server` chứ không
     phải `A/B`, tree dùng tham số `variant` chứ không phải `order`, generic
     dùng `a/b` chứ không phải `0`. Đọc thẳng từ config đã validate thì không
     còn chỗ cho phỏng đoán. */
  const cfg = parsed.config as Record<string, unknown>;
  const firstId = (arr: unknown, key = "id") =>
    Array.isArray(arr) && arr.length && typeof arr[0] === "object"
      ? String((arr[0] as Record<string, unknown>)[key]) : null;
  const derived: unknown[] = [];
  const inputId = firstId(cfg.inputs) ?? firstId(cfg.objects);
  if (inputId) derived.push({ type: "toggle", target: inputId });
  const links = cfg.links;
  if (Array.isArray(links) && Array.isArray(links[0])) {
    /* Trường là `a`/`b`, KHÔNG phải `from`/`to` — đọc từ hợp đồng miền
       (`network/index.ts`), không suy từ tên tiếng Anh nghe hợp lý. */
    derived.push({ type: "net_disconnect", a: String(links[0][0]), b: String(links[0][1]) });
  }
  if (typeof cfg.variant === "string") {
    const other = cfg.variant === "preorder" ? "inorder" : "preorder";
    derived.push({ type: "set_param", name: "variant", value: other });
  }
  if (Array.isArray(cfg.schema)) {
    const col = firstId(cfg.schema, "name");
    if (col) derived.push({ type: "set_param", name: "filter.column", value: col });
  }
  const objs = cfg.objects;
  if (Array.isArray(objs)) {
    const sw = objs.find((o) => (o as Record<string, unknown>).type === "switch");
    if (sw) derived.push({ type: "toggle", target: String((sw as Record<string, unknown>).id) });
  }

  /* Nhiều giá trị cho mỗi action: một probe đơn lẻ trúng đúng giá trị hiện tại
     sẽ là no-op hợp lệ và bị đọc nhầm thành "không nhận action". */
  const probes: Record<string, unknown[]> = {
    whatif_swap: [{ type: "whatif_swap", i: 0, j: 1 }, { type: "whatif_swap", i: 1, j: 2 }],
    set_param: [
      ...derived.filter((d) => (d as { type: string }).type === "set_param"),
      { type: "set_param", name: "targetBase", value: 8 },
      { type: "set_param", name: "targetBase", value: 2 },
      /* W5A — ba kênh màu. HAI giá trị cho mỗi kênh vì lý do ghi ngay dưới
         đây: một probe trúng đúng trị hiện tại là no-op hợp lệ và sẽ bị đọc
         nhầm thành "module không nhận action". */
      { type: "set_param", name: "red", value: 0 },
      { type: "set_param", name: "red", value: 255 },
      { type: "set_param", name: "green", value: 0 },
      { type: "set_param", name: "green", value: 255 },
      { type: "set_param", name: "blue", value: 0 },
      { type: "set_param", name: "blue", value: 255 },
      { type: "set_param", name: "text", value: "Zz" },
      { type: "set_param", name: "order", value: "postorder" },
      { type: "set_param", name: "order", value: "inorder" },
      { type: "set_param", name: "variant", value: "dfs" },
      { type: "set_param", name: "variant", value: "bfs" },
      { type: "set_param", name: "r", value: 7 },
      { type: "set_param", name: "threshold", value: 999 },
      { type: "set_param", name: "condition", value: ">= 999" },
      { type: "set_param", name: "selected", value: "heading" },
      { type: "set_param", name: "encoding", value: "unicode_codepoint" },
    ],
    toggle: [...derived.filter((d) => (d as { type: string }).type === "toggle"),
      { type: "toggle", target: "A" }, { type: "toggle", target: "0" },
      { type: "toggle", target: "1" }, { type: "toggle", target: "reset" }],
    move: [{ type: "move", target: "heading", x: 0, y: 1 },
      { type: "move", target: "paragraph", x: 0, y: 0 }],
    net_connect: [{ type: "net_connect", a: "A", b: "C" }],
    net_disconnect: [...derived.filter((d) => (d as { type: string }).type === "net_disconnect"),
      { type: "net_disconnect", a: "A", b: "B" }],
    net_reset: [{ type: "net_reset" }],
    exit_branch: [{ type: "exit_branch" }],
  };
  const ok: string[] = [];
  for (const name of candidates) {
    for (const a of probes[name] ?? []) {
      let next;
      try { next = m.apply(base, a as never); } catch { continue; }
      if (next !== base && JSON.stringify(next) !== JSON.stringify(base)) { ok.push(name); break; }
    }
  }
  return ok;
}

function classify(m: SimulationModule<unknown, unknown>, stage: string[]): Row {
  const accepted = acceptedByModule(m, stage);
  const roleOf = (a: string) =>
    a === "set_param" && MECHANISM_PARAM_TARGETS[m.id] ? "MECHANISM" : ACTION_ROLE[a];
  const mechanismActions = accepted.filter((a) => roleOf(a) === "MECHANISM");
  const inputActions = accepted.filter((a) => roleOf(a) === "INPUT");
  /* `apply: (state) => state` — module tự khai nó không nhận action nào. Đó là
     bằng chứng TRỰC TIẾP, khác hẳn việc probe của tôi không trúng. */
  const identityApply = /^\s*\(state[^)]*\)\s*=>\s*state\s*$/.test(
    m.apply.toString().replace(/\/\*[\s\S]*?\*\//g, "").trim());
  const branchOnly = accepted.filter((a) => BRANCH_ACTIONS.has(a));
  const hasChallenge = Boolean(m.predict);
  const hasTimeline = Boolean(m.timeline);

  let primaryType: string;
  let answer: string;
  if (mechanismActions.length) {
    /* Học sinh tác động lên CHÍNH đối tượng đang học. */
    primaryType = "INTERACTIVE_MODEL";
    answer = mechanismActions.join(" · ");
  } else if (inputActions.length) {
    /* Đổi được đề bài rồi xem engine chạy lại — hữu ích và thật, nhưng KHÔNG
       phải thao tác lên cơ chế. Gọi đúng tên nó (§12). */
    primaryType = "BOUNDED_PARAMETER_TOOL";
    answer = `${inputActions.join(" · ")} (đổi ĐẦU VÀO, không phải quyết định cơ chế)`;
  } else if (branchOnly.length) {
    primaryType = "COMMITMENT_TRACE";
    answer = "quyết định nhánh của cơ chế";
  } else if (hasTimeline) {
    /* PHÂN BIỆT HAI CA KHÁC HẲN NHAU — và đây là chỗ tôi đã suýt sai lần thứ ba.
       (a) `apply` là hàm đồng nhất ⇒ module THẬT SỰ không nhận action nào, nên
           TRACE_MODEL là phán quyết đúng và xác nhận được.
       (b) `apply` có nhận action, nhưng probe của tôi không trúng giá trị thật
           (id nút logic, id nút mạng, tên tham số bảng) ⇒ CHƯA kết luận được.
       Gộp (b) vào TRACE_MODEL là hạ cấp một target thao tác được chỉ vì phép đo
       hẹp — cùng lỗi đã phải sửa ở lượt "9 PROBE_UNVERIFIED". */
    primaryType = identityApply ? "TRACE_MODEL" : "PROBE_LIMITED";
    answer = identityApply
      ? "chỉ dòng thời gian (đã xác nhận: `apply` là hàm đồng nhất)"
      : "CHƯA KẾT LUẬN — `apply` có nhận action, probe chưa trúng giá trị thật";
  } else {
    primaryType = "AFFORDANCE_MISSING";
    answer = "KHÔNG CÓ — cần soát lại";
  }
  return {
    id: m.id, domain: m.domain,
    manipulatesWhenChallengeClosed: answer,
    stageActions: stage,
    mechanismActions, inputActions,
    acceptedByModule: accepted,
    hasChallenge, hasTimeline, primaryType,
  };
}

let rows: Row[] = [];

describe("W12-B0 — bốn loại hành động, phân loại trung thực", () => {
  it("dựng bảng 23 dòng và trả lời câu hỏi cổng cho từng target", () => {
    if (listSimulations().length === 0) registerAllSimulations();
    const domains = new Set(listSimulations().map((m) => m.domain));
    const byDomain = new Map([...domains].map((d) => [d, stageActionsOf(d)]));
    rows = listSimulations()
      .map((meta) => classify(getSimulation(meta.id)!, byDomain.get(meta.domain) ?? []))
      .sort((a, b) => a.id.localeCompare(b.id));
    expect(rows.length).toBeGreaterThanOrEqual(23);

    try {
      const dir = new URL("../../../docs/evaluation/m20/", import.meta.url)
        .pathname.replace(/^\/([A-Za-z]:)/, "$1");
      mkdirSync(dir, { recursive: true });
      /* XUẤT XỨ, KHÔNG CHỈ DẤU THỜI GIAN.
         Artifact này là ĐẦU VÀO của `certify-viewports-w12.mjs`, nhưng suốt W12
         nó chỉ có `generatedAt` ⇒ `UNKNOWN_PROVENANCE`. Một lượt chứng nhận
         không được nhận đầu vào mà chính nó không phán được trạng thái nguồn —
         nếu không, một mắt xích của bộ bằng chứng vĩnh viễn nằm ngoài cổng. */
      writeFileSync(join(dir, "w12-interaction-semantics.json"), JSON.stringify({
        ...provenance("interaction-semantics.test", { targets: rows.length }),
        kind: "DESCRIPTIVE_MANIFEST",
        note: "Dẫn từ hợp đồng module + affordance trong renderer miền. " +
              "KHÔNG phải chứng nhận trình duyệt — đó là việc của certify-w12.mjs.",
        gateQuestion: "Khi ĐÓNG thử thách, học sinh thao tác lên cái gì?",
        rows,
      }, null, 2), "utf-8");
    } catch { /* CI chỉ-đọc */ }
  });

  it("KHÔNG target nào rơi vào AFFORDANCE_MISSING", () => {
    /* §14: `apply` nhận một action mà học sinh không có đường phát ra nó. Một
       chứng nhận chỉ đọc `apply` sẽ bỏ lọt đúng ca ấy. */
    const missing = rows.filter((r) => r.primaryType === "AFFORDANCE_MISSING").map((r) => r.id);
    expect(missing, `target không có affordance nào trên sân khấu:\n${missing.join("\n")}`)
      .toEqual([]);
  });

  it("thử thách KHÔNG BAO GIỜ là câu trả lời cho câu hỏi cổng", () => {
    /* Đây là bất biến trung tâm của W12-B0. `find_max` có hai nút "Đặt 9 làm
       max mới"/"Giữ max = 7.5" — chúng nuôi `predict.check`, không đi qua
       `module.apply`, nên chúng thuộc THỬ THÁCH. Thao tác mô hình thật của nó
       là kéo cột trong `ArrayView` → `whatif_swap` → nhánh what-if. */
    for (const r of rows) {
      expect(r.manipulatesWhenChallengeClosed, `${r.id}`).not.toMatch(/dự đoán|phương án|trả lời/i);
    }
  });

  it("target khai INTERACTIVE_MODEL phải đụng ĐỐI TƯỢNG HỌC, không chỉ đầu vào", () => {
    /* Đây là bất biến trung tâm của W12-B0.5. Một action đổi được state KHÔNG
       tự động chứng minh "mô phỏng tương tác": phải hỏi nó đụng tới đối tượng
       đang dạy hay chỉ đụng đầu vào của đối tượng ấy. */
    for (const r of rows.filter((x) => x.primaryType === "INTERACTIVE_MODEL")) {
      expect(r.mechanismActions.length, `${r.id} khai interactive mà chỉ đổi đầu vào`)
        .toBeGreaterThan(0);
    }
  });

  it("`algorithm.find_max` — ca tham chiếu: mô hình và thử thách TÁCH BẠCH", () => {
    const fm = rows.find((r) => r.id === "algorithm.find_max")!;
    expect(fm.hasChallenge, "find_max phải CÓ thử thách").toBe(true);
    /* PHÂN LOẠI ĐÃ ĐỔI, và đó là điểm của W12-B0.5.
       `whatif_swap` đổi state thật, nhưng nó SẮP XẾP LẠI DỮ LIỆU VÀO — trong
       khi cơ chế đang dạy là "ứng viên có lớn hơn max hiện tại không". Đổi thứ
       tự đầu vào không cho học sinh tác động lên chính phép so sánh ấy.
       Quyết định promote/keep hiện CHỈ sống trong `predict` (thử thách), không
       có đường nào qua `module.apply` — nên `find_max` chưa phải mô phỏng
       tương tác theo nghĩa cơ chế. */
    expect(fm.inputActions, "kéo cột là thao tác ĐẦU VÀO").toContain("whatif_swap");
    expect(fm.mechanismActions, "chưa có action nào chạm tới quyết định của thuật toán")
      .toEqual([]);
    expect(fm.primaryType).toBe("BOUNDED_PARAMETER_TOOL");
    /* Đường thao tác: kéo cột trong ArrayView → onSwap → dispatch(whatif_swap)
       → apply → nhánh. Đóng thử thách lại, đường ấy vẫn còn. */
    const av = readFileSync(new URL("../components/ArrayView.tsx", import.meta.url)
      .pathname.replace(/^\/([A-Za-z]:)/, "$1"), "utf-8");
    expect(av, "ArrayView phải có đường kéo phát onSwap").toMatch(/onPointerDown/);
    expect(av).toMatch(/onSwap\(drag\.from, drag\.target\)/);
  });

  it("tính đúng sai của thử thách do ENGINE sở hữu, không do UI", () => {
    const idx = readFileSync(join(SIMS, "domains/algorithm/index.ts"), "utf-8");
    expect(idx, "`predict` phải dẫn từ điểm quyết định của trace")
      .toMatch(/decisionPointOf\(s\)/);
  });
});
