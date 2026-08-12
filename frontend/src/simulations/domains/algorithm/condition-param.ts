import { OP_TEXT } from "../../../core/algorithms";
import type { ConditionOp } from "../../../core/types";
import type { AlgorithmConfig } from "./model";

/**
 * W4B-4D — ĐIỀU KIỆN LÀ THAM SỐ CỦA BÀI, KHÔNG PHẢI HẰNG SỐ CỦA ĐỀ.
 *
 * ─── VÌ SAO PHẢI CÓ, VÀ VÌ SAO CHỈ CHO HAI BÀI NÀY ────────────────────────
 *
 * `count_if`/`sum_if` mang `mode: "hidden"` trong `interaction-policy.ts` với
 * lý do đã ghi từ lâu và VẪN ĐÚNG: đổi chỗ hai phần tử là một HOÁN VỊ, mà tổng
 * và số đếm bất biến theo hoán vị — kéo ở đó là trang trí, mời kéo là mời hão.
 *
 * Hệ quả là hai bài này không có lối vào Khám phá nào cả: học sinh chỉ còn
 * cam kết từng bước ("phần tử này có vào nhóm không?"). Cam kết đó hỏi MỘT
 * QUYẾT ĐỊNH BÊN TRONG một điều kiện đứng yên. Nó không hỏi được câu kia —
 * "chính điều kiện ấy chọn ra những ai?" — trong khi đó mới là thứ phân biệt
 * `count_if` với một phép duyệt suông.
 *
 * Nên tham số hoá đúng ĐIỀU KIỆN, và chỉ điều kiện:
 *   - phép so sánh: đúng sáu toán tử engine đã cài, không nhiều hơn;
 *   - ngưỡng: số nguyên TRONG khoảng giá trị của chính dãy — ra ngoài khoảng
 *     thì kết quả bão hoà (đếm hết hoặc đếm 0) và mọi lần kéo tiếp theo đều cho
 *     cùng một câu trả lời, tức là quay lại đúng cái vô nghĩa của kéo-thả.
 *
 * KHÔNG phải trình soạn biểu thức: không chuỗi điều kiện, không AND/OR, không
 * hàm. Miền đóng, tên lạ ⇒ `null` ⇒ người gọi giữ nguyên state.
 */

export const CONDITION_OPS: readonly ConditionOp[] = [">", ">=", "<", "<=", "==", "!="];

export const CONDITION_OP_LABEL: Record<ConditionOp, string> = OP_TEXT;

/** Khoảng ngưỡng hợp lệ = khoảng giá trị của chính dãy (bao gồm hai đầu). */
export function thresholdRange(array: readonly number[]): { min: number; max: number } | null {
  if (array.length === 0) return null;
  const min = Math.ceil(Math.min(...array));
  const max = Math.floor(Math.max(...array));
  return min <= max ? { min, max } : null;
}

/** Bài này có điều kiện để mà đổi không (chỉ `count_if`/`sum_if` có). */
export function hasCondition(config: AlgorithmConfig): boolean {
  return config.data.condition !== null;
}

/**
 * Áp một thay đổi CÓ RÀNG BUỘC lên điều kiện. `null` = không hợp lệ.
 *
 * Trả về config MỚI chứ không phải state: bên gọi (`apply`) mới là chỗ được
 * phép dựng lại trace, và dựng lại trace là việc của engine tất định.
 */
export function withConditionParam(
  config: AlgorithmConfig, name: string, value: number | string | boolean,
): AlgorithmConfig | null {
  const cond = config.data.condition;
  if (!cond) return null;                       // bài không có điều kiện ⇒ không có gì để đổi

  if (name === "condition.op") {
    if (typeof value !== "string" || !(CONDITION_OPS as readonly string[]).includes(value)) return null;
    if (value === cond.op) return null;         // không đổi ⇒ không state mới
    return { ...config, data: { ...config.data, condition: { ...cond, op: value as ConditionOp } } };
  }

  if (name === "condition.value") {
    const n = typeof value === "number" ? value : Number(value);
    if (!Number.isInteger(n)) return null;
    const r = thresholdRange(config.data.array);
    /* TỪ CHỐI chứ không kẹp về biên — cùng luật với mọi miền khác trong repo:
       kẹp im lặng làm học sinh thấy một con số mình không hề chọn. */
    if (!r || n < r.min || n > r.max) return null;
    if (n === cond.value) return null;
    return { ...config, data: { ...config.data, condition: { ...cond, value: n } } };
  }

  return null;                                   // ngoài tập đóng ⇒ fail-closed
}
