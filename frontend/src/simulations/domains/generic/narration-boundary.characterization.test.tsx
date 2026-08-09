import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { makeGenericModule } from "./index";
import { validateGenericConfig } from "./validate";
import { buildTimeline } from "./model";

/**
 * ĐẶC TẢ (CHARACTERIZATION), KHÔNG PHẢI KỲ VỌNG — `generic.rule_scene`,
 * ranh giới LLM ↔ bề mặt học sinh.
 *
 * ⚠️ ĐỌC KỸ TRƯỚC KHI SỬA: những assert dưới đây mô tả **hành vi HIỆN TẠI**,
 * kể cả hành vi đáng lo. Chúng KHÔNG phải hợp đồng mong muốn. Nếu một wave sau
 * quyết định siết `narration`, các test này sẽ đỏ — và đỏ là ĐÚNG: hãy sửa test
 * cho khớp hành vi mới, đừng nới lỏng bản vá cho khớp test.
 *
 * Câu hỏi được đo: chuỗi `narration` do LLM soạn có thể trở thành nội dung
 * runtime mà học sinh đọc, ở mức nào?
 *
 * Chuỗi sở hữu đã truy được (đo, không suy từ tên):
 *   LLM → `catalog.py` response schema `narration: STRING nullable`
 *       → `dsl/validator.py:485` — CHỈ `isinstance(str)`
 *       → mirror `generic/validate.ts:482` — CHỈ `typeof === "string"`
 *       → `model.ts:373` `step.narration ?? "Hé lộ: …"` (dùng NGUYÊN VĂN nếu có)
 *       → `index.ts:78` `narrate()` → khe thuyết minh của SHELL (bề mặt Quan sát)
 *       → `ui.tsx:818` thẻ TIẾN TRÌNH — nằm trong `GenericInspector`, tức panel
 *         GIẢI THÍCH (đóng mặc định), KHÔNG phải sân khấu
 *       → `getExplainContext` → ngữ cảnh của gia sư AI
 *
 * ĐÍNH CHÍNH DO ĐO ĐƯỢC: bản nháp của chính test này ghi "hiện hai lần trên một
 * màn hình" vì đọc `progressive = timeline.length > 1` rồi suy ra. Sai — dòng
 * 818 thuộc `GenericInspector`. Đo thật cho thấy `GenericWorkspace` KHÔNG in
 * narration; nó tới học sinh qua khe của shell, và lặp lại chỉ khi mở Giải
 * thích. Đây đúng là lý do §4 của đề bài cấm suy từ grep.
 *
 * KHÔNG gọi API ngoài. Mọi ca dựng bằng spec cục bộ, đi qua đúng validator thật.
 */

/** Spec tối thiểu HỢP LỆ có `reveal_sequence` — khuôn lấy từ `generic.test.ts`. */
function specWith(narration: string | undefined, valueOfA = 5) {
  return {
    dsl_version: "1.0",
    title: "canh do ranh gioi",
    objects: [
      { id: "A", type: "value_box", x: 20, y: 50, value: valueOfA },
      { id: "B", type: "node", x: 80, y: 50 },
    ],
    rules: [],
    interactions: [],
    processes: [
      {
        type: "reveal_sequence",
        steps: [
          { objects: ["A"], ...(narration === undefined ? {} : { narration }) },
          { objects: ["B"] },
        ],
      },
    ],
  };
}

const accept = (narration: string | undefined) => validateGenericConfig(specWith(narration));

/* ── 1. VALIDATOR CHẤP NHẬN GÌ ────────────────────────────────────────────── */

describe("đặc tả · validator hai tầng chỉ kiểm KIỂU của narration", () => {
  const CASES: Array<[string, string]> = [
    ["mâu thuẫn giá trị hiện trên cảnh", "Ô A đang mang giá trị 999."],
    ["tuyên bố một kết quả thuật toán", "Kết quả cuối cùng của bài này là 42."],
    ["tự phán học sinh đúng/sai", "Em đã chọn đúng rồi, giỏi lắm!"],
    ["lộ trước bước sau", "Bước sau sẽ hiện B, và đáp án là B."],
    ["tự xưng là hệ thống chấm điểm", "Hệ thống xác nhận: lời giải này chính xác."],
    ["chèn thẻ HTML", "<script>alert(1)</script><b>đậm</b>"],
    ["chuỗi rất dài", "x".repeat(20000)],
  ];

  for (const [name, text] of CASES) {
    it(`CHẤP NHẬN: ${name}`, () => {
      const r = accept(text);
      expect(r.ok, `validator từ chối: ${r.ok ? "" : r.error}`).toBe(true);
    });
  }

  it("không có TRẦN ĐỘ DÀI nào — chuỗi 20k ký tự đi thẳng vào spec", () => {
    const long = "x".repeat(20000);
    const r = accept(long);
    if (!r.ok) throw new Error(r.error);
    const frames = buildTimeline(r.config);
    expect(frames[0].narration).toHaveLength(20000);
  });

  it("narration KHÔNG phải chuỗi thì bị bỏ qua, KHÔNG làm hỏng spec", () => {
    const spec = specWith(undefined) as unknown as Record<string, unknown>;
    (spec.processes as Array<{ steps: Array<Record<string, unknown>> }>)[0].steps[0].narration = 123;
    const r = validateGenericConfig(spec);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    // rơi về chuỗi DẪN XUẤT của engine, không giữ giá trị lạ
    expect(buildTimeline(r.config)[0].narration).toContain("Hé lộ");
  });

  it("trường LẠ trong reveal step thì BỊ TỪ CHỐI — hàng rào có thật, chỉ hẹp", () => {
    const spec = specWith(undefined) as unknown as Record<string, unknown>;
    (spec.processes as Array<{ steps: Array<Record<string, unknown>> }>)[0].steps[0].html = "<b>x</b>";
    const r = validateGenericConfig(spec);
    expect(r.ok).toBe(false);
  });
});

/* ── 2. NÓ CÓ TỚI ĐƯỢC MẮT HỌC SINH KHÔNG ─────────────────────────────────── */

describe("đặc tả · narration của LLM hiển thị NGUYÊN VĂN", () => {
  const CLAIM = "Kết quả cuối cùng của bài này là 42.";

  it("engine giữ nguyên văn, không chuẩn hoá, không cắt", () => {
    const r = accept(CLAIM);
    if (!r.ok) throw new Error(r.error);
    expect(buildTimeline(r.config)[0].narration).toBe(CLAIM);
  });

  it("khe thuyết minh của shell (`narrate`) trả đúng chuỗi đó", () => {
    const mod = makeGenericModule();
    const r = mod.validateConfig(specWith(CLAIM));
    if (!r.ok) throw new Error(r.error);
    const state = mod.init(r.config);
    expect(mod.narrate!(state, r.config)?.text).toBe(CLAIM);
  });

  it("SÂN KHẤU không in narration; panel GIẢI THÍCH thì có", () => {
    const mod = makeGenericModule();
    const r = mod.validateConfig(specWith(CLAIM));
    if (!r.ok) throw new Error(r.error);
    const state = mod.init(r.config);
    const stage = renderToString(
      <mod.Workspace config={r.config} state={state} busy={false} dispatch={() => {}} />,
    );
    const Inspector = mod.Inspector!;
    const panel = renderToString(
      <Inspector config={r.config} state={state} busy={false} dispatch={() => {}} />,
    );
    expect(stage, "sân khấu tự in narration").not.toContain(CLAIM);
    expect(panel, "panel Giải thích mất thẻ TIẾN TRÌNH").toContain(CLAIM);
    /* ⇒ đường tới học sinh ở Quan sát là KHE CỦA SHELL (`narrate`), và câu này
       lặp lại lần hai chỉ khi học sinh mở Giải thích. */
    expect(mod.narrate!(state, r.config)?.text).toBe(CLAIM);
  });

  it("React ESCAPE thẻ HTML — không có đường chèn markup", () => {
    const mod = makeGenericModule();
    const r = mod.validateConfig(specWith("<script>alert(1)</script>"));
    if (!r.ok) throw new Error(r.error);
    const state = mod.init(r.config);
    const Inspector = mod.Inspector!;
    const panel = renderToString(
      <Inspector config={r.config} state={state} busy={false} dispatch={() => {}} />,
    );
    expect(panel).not.toContain("<script>");
    expect(panel).toContain("&lt;script&gt;");
  });
});

/* ── 3. NÓ CÓ SỞ HỮU SỰ THẬT KHÔNG — CÂU HỎI QUAN TRỌNG NHẤT ─────────────── */

describe("đặc tả · narration KHÔNG sở hữu state/kết quả/phán quyết", () => {
  const LIE = "Ô A đang mang giá trị 999 và thuật toán đã kết thúc.";

  it("đổi narration KHÔNG đổi một bit nào của state hay timeline", () => {
    const mod = makeGenericModule();
    const a = mod.validateConfig(specWith(undefined));
    const b = mod.validateConfig(specWith(LIE));
    if (!a.ok || !b.ok) throw new Error("spec không hợp lệ");

    const sa = mod.init(a.config) as unknown as Record<string, unknown>;
    const sb = mod.init(b.config) as unknown as Record<string, unknown>;

    const strip = (s: Record<string, unknown>) =>
      JSON.stringify(s, (k, v) => (k === "narration" ? undefined : v));
    expect(strip(sb), "narration đã rò vào state").toBe(strip(sa));
  });

  it("giá trị THẬT của object vẫn do engine sở hữu, dù narration nói khác", () => {
    const mod = makeGenericModule();
    const r = mod.validateConfig(specWith(LIE, 5));
    if (!r.ok) throw new Error(r.error);
    const state = mod.init(r.config);
    const stage = renderToString(
      <mod.Workspace config={r.config} state={state} busy={false} dispatch={() => {}} />,
    );
    // Sân khấu vẽ 5 — con số của engine. Nó KHÔNG bị narration làm sai lệch.
    expect(stage).toContain("5");
    expect(stage, "narration lọt vào sân khấu").not.toContain(LIE);
    // Nhưng khe thuyết minh của shell in nguyên câu nói 999, cùng lúc, cùng màn.
    expect(mod.narrate!(state, r.config)?.text).toBe(LIE);
    // ⇒ PHÁT HIỆN: engine giữ đúng sự thật; mâu thuẫn nằm giữa HAI BỀ MẶT,
    // và không tầng nào đối chiếu chúng.
  });

  it("generic.rule_scene KHÔNG khai `predict` ⇒ không có phán quyết để bẻ", () => {
    const mod = makeGenericModule();
    expect(mod.predict, "nếu có predict thì phải đo lại rủi ro").toBeUndefined();
  });

  it("narration là trường TRÌNH BÀY: không logic nào đọc nó để quyết định", () => {
    /* Khoá bằng mã nguồn: `model.ts` chỉ GÁN narration vào frame, không bao giờ
       so sánh/rẽ nhánh theo nó. Nếu một ngày có ai đọc nó để quyết định thì
       narration thành đầu vào của engine — đúng thứ bất biến #1 cấm. */
    const src = new URL("./model.ts", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
    const text = require("node:fs").readFileSync(src, "utf-8") as string;
    const reads = text.match(/narration\s*(===|!==|\.includes|\.match|\.length)/g) ?? [];
    expect(reads, `model.ts đang ĐỌC narration để quyết định: ${reads.join(", ")}`).toEqual([]);
  });
});
