import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { compareNumbers, includesBoundary } from "./predicate";
import { runAlgorithm } from "./algorithms";
import { runScan, SCAN_VERSION } from "./scan";
import type { AnalysisOk, ConditionOp } from "./types";

/**
 * W5C (Phase C) — HỌ VỊ TỪ: SÁU TOÁN TỬ, MỘT NGHĨA, KIỂM Ở RANH GIỚI.
 *
 * ─── ĐIỀU PHẢI CHỨNG MINH ──────────────────────────────────────────────────
 *
 * Không phải "hàm so sánh chạy đúng" — mà là: MỌI engine có vị từ đều đồng ý
 * với nhau ở CẢ BA quan hệ (nhỏ hơn · BẰNG · lớn hơn), cho CẢ SÁU toán tử.
 *
 * Vì sao ranh giới `=` là chỗ đáng kiểm nhất: bài học nằm đúng ở đó ("từ 8,0
 * TRỞ LÊN" khác "trên 8,0"), và một lỗi lệch-một ở đó không làm gì hỏng trông
 * thấy — nó chỉ lặng lẽ chấm sai đúng những học sinh ở ngưỡng. Ba bản cài trước
 * W5C đồng ý với nhau vì may, không vì có gì bắt chúng phải thế.
 */

const OPS: ConditionOp[] = [">", ">=", "<", "<=", "==", "!="];

/** Ba quan hệ, dựng quanh MỘT ngưỡng — 80 là ngưỡng thật trong đề mẫu. */
const T = 80;
const BELOW = 79;
const EQUAL = 80;
const ABOVE = 81;

/* ══ 1. CHỦ SỞ HỮU: bảng chân trị đầy đủ, viết tay ═══════════════════════ */

describe("W5C §1 · sáu toán tử × ba quan hệ — bảng viết tay, không sinh lại từ code", () => {
  /* Bảng này CỐ Ý viết tay. Sinh nó bằng chính `compareNumbers` sẽ là test tự
     xác nhận: nó xanh với mọi bản cài, kể cả bản sai. */
  const TRUTH: Record<ConditionOp, [boolean, boolean, boolean]> = {
    //            79<80   80=80   81>80
    ">":         [false,  false,  true],
    ">=":        [false,  true,   true],
    "<":         [true,   false,  false],
    "<=":        [true,   true,   false],
    "==":        [false,  true,   false],
    "!=":        [true,   false,  true],
  };

  it.each(OPS)("%s: đúng ở cả ba quan hệ", (op) => {
    const [lo, eq, hi] = TRUTH[op];
    expect(compareNumbers(BELOW, op, T), `${BELOW} ${op} ${T}`).toBe(lo);
    expect(compareNumbers(EQUAL, op, T), `${EQUAL} ${op} ${T} — RANH GIỚI`).toBe(eq);
    expect(compareNumbers(ABOVE, op, T), `${ABOVE} ${op} ${T}`).toBe(hi);
  });

  it("`includesBoundary` khớp đúng cột giữa của bảng — không phải danh sách thứ hai", () => {
    for (const op of OPS) {
      expect(includesBoundary(op), `${op}: khai bao-gồm-ranh-giới lệch bảng chân trị`)
        .toBe(TRUTH[op][1]);
    }
  });
});

/* ══ 2. MỌI ENGINE ĐỀU ĐI QUA CHỦ SỞ HỮU ĐÓ ═════════════════════════════ */

function sumIfAnalysis(array: number[], op: ConditionOp, value: number): AnalysisOk {
  return {
    problem: {},
    algorithm_id: "sum_if",
    data: { array, condition: { op, value }, labels: null, target: null, order: null },
    data_generated: false,
    notes: null,
  } as unknown as AnalysisOk;
}

/** Đáp số cuối mà engine công bố — thứ học sinh đọc là "kết quả". */
function finalResultText(steps: { events: { type: string; result?: string }[] }[]): string {
  for (let i = steps.length - 1; i >= 0; i -= 1) {
    for (const ev of steps[i].events) {
      if (ev.type === "done") return ev.result as string;
    }
  }
  throw new Error("trace không có bước done");
}

describe("W5C §2 · `sum_if`: đáp số của engine khớp phép so sánh, KỂ CẢ ở ranh giới", () => {
  const ARRAY = [BELOW, EQUAL, ABOVE];

  it.each(OPS)("%s: tổng bằng đúng tổng các phần tử thoả", (op) => {
    const trace = runAlgorithm(sumIfAnalysis(ARRAY, op, T));
    const expected = ARRAY.filter((v) => compareNumbers(v, op, T)).reduce((a, b) => a + b, 0);
    expect(finalResultText(trace.steps), `${op}: đáp số không khớp phép so sánh`)
      .toContain(String(expected));
  });

  it("RANH GIỚI, ca cụ thể: `>=` ngưỡng 80 PHẢI nhận phần tử 80", () => {
    /* Đây là ca đã được nêu đích danh trong đặc tả Phase C. Giữ nó riêng, viết
       thẳng con số, để nếu ngày nào nó hỏng thì thông báo lỗi nói đúng câu
       chuyện thay vì "tham số thứ hai của bảng". */
    const withBoundary = finalResultText(runAlgorithm(sumIfAnalysis(ARRAY, ">=", T)).steps);
    const withoutBoundary = finalResultText(runAlgorithm(sumIfAnalysis(ARRAY, ">", T)).steps);
    expect(withBoundary).toContain(String(EQUAL + ABOVE));
    expect(withoutBoundary).toContain(String(ABOVE));
    expect(withBoundary, "`>=` và `>` cho cùng đáp số ⇒ ranh giới đang bị bỏ qua")
      .not.toBe(withoutBoundary);
  });
});

describe("W5C §3 · `algorithm.scan` đồng ý với `sum_if` ở TỪNG phần tử", () => {
  /* Hai engine khác nhau, cùng một câu hỏi "phần tử này có thoả không". Trước
     W5C chúng có hai bản cài riêng; test này là chỗ phát hiện nếu chúng lại
     tách ra. */
  const ARRAY = [BELOW, EQUAL, ABOVE, 100, 0];

  it.each(OPS)("%s: cùng tập phần tử thoả điều kiện", (op) => {
    const scanTrace = runScan({
      scan_version: SCAN_VERSION,
      array: ARRAY,
      seed: { from: "constant", value: 0, varName: "tong" },
      compare: { kind: "to_constant", op, value: T },
      update: { kind: "add_current" },
      marking: "match_highlight",
      stop: "end_of_array",
    });

    const expected = ARRAY.filter((v) => compareNumbers(v, op, T));
    const total = expected.reduce((a, b) => a + b, 0);
    expect(finalResultText(scanTrace.steps), `${op}: scan lệch khỏi phép so sánh chung`)
      .toContain(String(total));
  });
});

/* ══ 3. KHÔNG CÒN BẢN CÀI THỨ TƯ NÀO MỌC LÊN ════════════════════════════ */

describe("W5C §4 · một chủ sở hữu, và nó phải ở lại là một", () => {
  const read = (rel: string) =>
    readFileSync(new URL(rel, import.meta.url), "utf-8")
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/^\s*\/\/.*$/gm, "");

  it("không engine nào tự cài lại `switch` sáu toán tử", () => {
    /* Quét MÃ ĐÃ BỎ COMMENT nên một ví dụ trong chú thích không làm đỏ oan. */
    for (const f of ["./algorithms.ts", "./scan.ts", "./program.ts"]) {
      const src = read(f);
      /* Dấu hiệu của một bản cài LẠI là một nhãn `case` trả thẳng một phép so
         sánh. Nhãn `case` gộp lại rồi UỶ QUYỀN (như `program.ts` sau W5C) thì
         không sao — nên guard nhìn vào `case … : return`, không nhìn nhãn. */
      expect(src, `${f}: đang cài lại ngữ nghĩa toán tử thay vì gọi predicate.ts`)
        .not.toMatch(/case\s+"<="\s*:\s*return/);
      expect(src, `${f}: không còn gọi chủ sở hữu chung`).toContain("compareNumbers");
    }
  });

  it("`program.ts` không còn `default` nuốt toán tử lạ thành `>=`", () => {
    /* Đây là lỗi THẬT đã có trong mã: nhánh `default` của khối `compare` trả
       `l >= r`, nên một toán tử thứ bảy thêm vào enum sẽ chạy sai trong im lặng
       thay vì đỏ. Nay op lạ thì ném. */
    const src = read("./program.ts");
    expect(src).not.toMatch(/default:\s*\n\s*return \(l as number\) >= \(r as number\);/);
    expect(src).toMatch(/Toán tử so sánh chưa được cài/);
  });
});
