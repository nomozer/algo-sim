/**
 * Khai báo kiểu cho `certify-sweep-w12.mjs`.
 *
 * Cùng lí do với `evidence.d.mts`: script chạy thẳng bằng `node`, nên nguồn ở
 * lại JS thuần và đây là bản chiếu kiểu cho phía test. `GATES` được xuất ra chỉ
 * để `certification-sweep.test.ts` kiểm được rằng không cổng con nào rụng trong
 * im lặng — chạy thẳng file mới thi hành lượt chứng nhận.
 */

export interface SweepGate {
  name: string;
  /** `DERIVED` = dẫn từ hợp đồng module · `BROWSER` = bấm thật qua CDP. */
  kind: "DERIVED" | "BROWSER";
  cmd: [string, string[]];
  /** Đường dẫn tuyệt đối tới artifact — luôn nằm trong `docs/evaluation/`. */
  out: string;
}

export declare const GATES: SweepGate[];
