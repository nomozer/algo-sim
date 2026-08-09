import type { AlgorithmId } from "./types";

/**
 * Mã giả từng thuật toán (giọng liệt kê bước kiểu SGK, chỉ số 1-based).
 * Engine gắn Step.line trỏ vào dòng đang thực hiện — renderer highlight.
 * R1.2: khi đối chiếu SGK, chỉnh câu chữ tại đây cho khớp sách.
 */
/**
 * W4B-2D §4 — BIẾN NÀO LÀ **VỊ TRÍ 0-BASED CỦA ENGINE**.
 *
 * Bảng này sống CẠNH `PSEUDOCODE` vì chính `PSEUDOCODE` sinh ra nghĩa vụ: mã giả
 * ở trên khai "chỉ số 1-based", nên mọi biến chỉ-số hiện cho học sinh phải đếm
 * từ 1 theo. Đo trong Chrome (`docs/evaluation/m17/w4b2d-search-family/`) thấy
 * điều ngược lại — cùng MỘT màn hình binary_search: mã giả `trái ← 1`, chip BIẾN
 * `trái 0`, vùng xét `1–10`, nhãn cột `0–9`. Học sinh tính `giữa ← (trái+phải)
 * div 2` theo mã giả ra 5, app hiện 4: mã giả KHÔNG lần theo được bằng chính
 * bảng biến đứng cạnh nó.
 *
 * `algorithms.ts` đã chốt luật này từ trước cho THUYẾT MINH (`pos()` — "Vị trí
 * nói với học sinh: luôn đếm từ 1"), nhưng chưa bao giờ áp cho `VarsView` và
 * `ArrayView`. Đúng anti-pattern #10: vá một bề mặt, quên bề mặt kia.
 *
 * ─── VÌ SAO LÀ BẢNG THEO BÀI, KHÔNG PHẢI BẢNG THEO TÊN BIẾN ────────────────
 * Cám dỗ là để `VarsView` tự nhận ra "biến tên `i` thì cộng 1". Không được —
 * tra thật cho thấy tên biến KHÔNG suy ra được tính-vị-trí:
 *  - `core/program.ts` cho ĐỀ BÀI tự đặt tên biến; một chương trình khai biến
 *    tên `i` mà bị cộng 1 là sai câm;
 *  - `core/scan.ts` có `trackIndexVar` LÀ vị trí 0-based thật, nhưng tên do spec
 *    đặt nên bảng theo tên sẽ bỏ sót.
 * Tính-vị-trí phải do bên SINH TRACE khai, không do bề mặt hiển thị đoán. Ở đây
 * bên sinh trace là 9 bài chuyên biệt, và chúng khai tĩnh — đúng một chỗ.
 *
 * ─── HAI BIẾN CỐ Ý VẮNG MẶT ────────────────────────────────────────────────
 * `luot` (nổi bọt) và `vi_tri_cuc_tri` (chọn) ĐÃ được engine ghi 1-based sẵn
 * (`setVar("luot", i + 1)`, `setVar("vi_tri_cuc_tri", j + 1)`). Cho chúng vào
 * đây là cộng 1 lần thứ hai. Đây chính là lý do bảng phải liệt kê theo bài chứ
 * không quét theo tên: hai biến này *nghe như* chỉ số nhưng không phải.
 */
export const POSITION_VARS: Record<AlgorithmId, readonly string[]> = {
  find_max: ["vt"],
  find_min: ["vt"],
  sum_if: [],
  count_if: [],
  linear_search: ["i"],
  binary_search: ["trai", "phai", "giua"],
  bubble_sort: [],
  insertion_sort: [],
  selection_sort: [],
};

export const PSEUDOCODE: Record<AlgorithmId, string[]> = {
  find_max: [
    "max ← a[1]; vt ← 1",
    "với mỗi i từ 2 đến n:",
    "   nếu a[i] > max thì",
    "      max ← a[i]; vt ← i",
    "trả về max và vị trí vt",
  ],
  find_min: [
    "min ← a[1]; vt ← 1",
    "với mỗi i từ 2 đến n:",
    "   nếu a[i] < min thì",
    "      min ← a[i]; vt ← i",
    "trả về min và vị trí vt",
  ],
  sum_if: [
    "tong ← 0",
    "với mỗi i từ 1 đến n:",
    "   nếu a[i] thỏa điều kiện thì",
    "      tong ← tong + a[i]",
    "trả về tong",
  ],
  count_if: [
    "dem ← 0",
    "với mỗi i từ 1 đến n:",
    "   nếu a[i] thỏa điều kiện thì",
    "      dem ← dem + 1",
    "trả về dem",
  ],
  linear_search: [
    "với mỗi i từ 1 đến n:",
    "   nếu a[i] = x thì",
    "      trả về vị trí i",
    "trả về “không tìm thấy”",
  ],
  binary_search: [
    "trái ← 1; phải ← n",
    "lặp khi trái ≤ phải:",
    "   giữa ← (trái + phải) div 2",
    "   nếu a[giữa] = x: trả về giữa",
    "   nếu a[giữa] < x: trái ← giữa + 1",
    "   ngược lại: phải ← giữa − 1",
    "trả về “không tìm thấy”",
  ],
  bubble_sort: [
    "với mỗi lượt từ 1 đến n − 1:",
    "   với mỗi cặp kề (j, j+1) trong vùng chưa sắp:",
    "      nếu a[j] và a[j+1] sai thứ tự thì",
    "         đổi chỗ a[j] và a[j+1]",
    "   phần tử cuối vùng chưa sắp đã đúng chỗ",
    "trả về dãy đã sắp xếp",
  ],
  insertion_sort: [
    "coi a[1] là phần đã sắp",
    "với mỗi i từ 2 đến n:",
    "   k ← a[i]; j ← i − 1",
    "   lặp khi j ≥ 1 và a[j] > k:",
    "      dời a[j] sang phải; j ← j − 1",
    "   chèn k vào vị trí j + 1",
    "trả về dãy đã sắp xếp",
  ],
  selection_sort: [
    "với mỗi i từ 1 đến n − 1:",
    "   vt ← i (vị trí cực trị tạm của phần chưa sắp)",
    "   với mỗi j từ i + 1 đến n:",
    "      nếu a[j] tốt hơn a[vt] theo thứ tự sắp thì vt ← j",
    "   đổi chỗ a[i] và a[vt] (nếu vt ≠ i)",
    "trả về dãy đã sắp xếp",
  ],
};
