import type { ConditionOp } from "./types";

/**
 * predicate.ts — CHỦ SỞ HỮU DUY NHẤT của "sáu phép so sánh nghĩa là gì".
 *
 * ─── VÌ SAO FILE NÀY RA ĐỜI (W5C / Phase C) ────────────────────────────────
 *
 * Cùng sáu toán tử `> >= < <= == !=` được cài BA LẦN, ở ba engine khác nhau:
 *
 *   core/algorithms.ts::testCondition   sum_if · count_if
 *   core/scan.ts::opHolds               algorithm.scan
 *   core/program.ts (nhánh "compare")   bounded_control_flow
 *
 * Ba bản ấy hôm nay đồng ý với nhau — nhưng KHÔNG có gì bắt chúng phải thế.
 * Một lần sửa `>=` thành `>` ở một bản là một lớp học sinh bị chấm sai ở đúng
 * giá trị BIÊN, và hai bản kia vẫn xanh nên không test nào đỏ. Ranh giới `=`
 * chính là chỗ bài học nằm ("từ 8,0 TRỞ LÊN" khác "trên 8,0"), nên nó cũng là
 * chỗ một lỗi lệch-một gây hại nhất và khó thấy nhất.
 *
 * ─── PHẠM VI ───────────────────────────────────────────────────────────────
 *
 * File này sở hữu NGỮ NGHĨA TOÁN TỬ trên hai SỐ, không hơn. Nó không biết
 * ngưỡng ở đâu ra, không biết phần tử nào đang được xét, không dựng chữ.
 * `program.ts` giữ riêng `==`/`!=` của nó vì ở đó hai vế có thể là bool hoặc
 * chuỗi — so sánh THỨ TỰ thì mới uỷ quyền xuống đây.
 */

/**
 * `x <op> y` — hàm THUẦN, tổng (mọi `ConditionOp` đều có nhánh).
 *
 * Không có `default:` cố ý: `switch` vét cạn để TypeScript đỏ ngay khi ai đó
 * thêm toán tử thứ bảy mà quên cài nó. Một `default` ở đây sẽ nuốt toán tử mới
 * thành một phép so sánh tuỳ tiện — đúng cái bẫy `program.ts` đã mắc, nơi mọi
 * op không khớp lặng lẽ trở thành `>=`.
 */
export function compareNumbers(x: number, op: ConditionOp, y: number): boolean {
  switch (op) {
    case ">":
      return x > y;
    case ">=":
      return x >= y;
    case "<":
      return x < y;
    case "<=":
      return x <= y;
    case "==":
      return x === y;
    case "!=":
      return x !== y;
  }
}

/**
 * Toán tử có BAO GỒM ranh giới không (`>=`, `<=`, `==`).
 *
 * Dùng để nói/kiểm về chính ranh giới ấy mà không phải viết lại danh sách ở nơi
 * thứ tư. `!=` KHÔNG bao gồm: tại `x == y` nó cho Sai.
 */
export function includesBoundary(op: ConditionOp): boolean {
  return op === ">=" || op === "<=" || op === "==";
}
