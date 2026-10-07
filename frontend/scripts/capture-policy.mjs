/**
 * CHÍNH SÁCH CHỤP ẢNH — một luật cho mọi bộ đo trình duyệt (exact-dimensions).
 *
 * Phép kiểm điểm ảnh của bộ đo đọc KHUNG TRONG BỘ NHỚ (`canvasFrame`), không đọc tệp PNG; tệp chỉ là bằng chứng. Nên
 * quyết định "có lưu ảnh không" đặt ở ĐÚNG MỘT CHỖ — `compiler-scene-suite.capture`, mọi bộ đo gọi chung — và đặt
 * TRƯỚC khi chụp, không phải chụp rồi xoá:
 *
 *   `toi-thieu` (mặc định) — chỉ ảnh mà oracle bắt buộc đọc (`ORACLE`: crop cạnh khuất của bộ dựng bằng chứng), ảnh
 *                            khớp tập duyệt chọn TRƯỚC lượt đo (`--review-set`, glob tương đối thư mục run), và ảnh
 *                            chẩn đoán tại trạng thái lỗi (`loi: true`).
 *   `day-du`               — mọi trạng thái (tìm lỗi một tiến trình dựng, hay dựng sheet duyệt cũ).
 *
 * Phép kiểm vẫn chạy y nguyên ở cả hai chế độ; chỉ việc GHI tệp đổi. Bộ đếm (`demAnh`) phân biệt lượt gọi, ảnh tạo và
 * lượt bỏ qua — số ảnh không chụp không bao giờ được trình bày như số ảnh đã xoá.
 */
import { readFileSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";

/** Ảnh oracle bắt buộc: `build_scene3d_visual_evidence.STATES` cắt crop cạnh khuất từ hai trạng thái này. */
export const ORACLE = ["neutral_final.png", "rotated_neutral.png"];

let cheDo = "toi-thieu";
let goc = null;            // thư mục run (cha của `inputs/REVIEW_SET.json`)
let mau = [];              // glob tập duyệt → RegExp trên đường dẫn tương đối run
export const demAnh = { goi: 0, tao: 0, bo_qua: 0, loi: 0 };

const globRe = (g) => new RegExp(`^${g.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, "[^/]*")}$`);

/** Đặt chính sách từ cờ dòng lệnh: `--anh-che-do toi-thieu|day-du` · `--review-set <inputs/REVIEW_SET.json>`. */
export function datChinhSach({ mode, reviewSet } = {}) {
  if (mode) {
    if (!["toi-thieu", "day-du"].includes(mode)) throw new Error(`CAPTURE_MODE_UNKNOWN:${mode}`);
    cheDo = mode;
  }
  if (reviewSet) {
    const p = resolve(String(reviewSet));
    goc = dirname(dirname(p));
    mau = JSON.parse(readFileSync(p, "utf8")).items.map((i) => globRe(i.path));
  }
}

/** Có lưu ảnh này không — quyết TRƯỚC khi chụp. */
export function canChup(path, { loi = false } = {}) {
  if (loi || cheDo === "day-du") return true;
  const ten = path.replaceAll("\\", "/").split("/").pop();
  if (ORACLE.includes(ten)) return true;
  if (!goc) return false;
  const tuongDoi = relative(goc, resolve(path)).replaceAll("\\", "/");
  return mau.some((re) => re.test(tuongDoi));
}

/** Tóm tắt ghi vào JSON bằng chứng của bộ đo. */
export function tomTatAnh() {
  return { mode: cheDo, review_set_patterns: mau.length, oracle_states: ORACLE, ...demAnh };
}

/** Lỗi môi trường / bộ đo / phép kiểm sản phẩm — ba lớp không được gộp (exact-dimensions, brief E). */
export function phanLoaiLoi(runError, assertionsPass) {
  if (runError) {
    return /POLL_TIMEOUT|CDP_TIMEOUT|WS_OPEN_TIMEOUT|TEXTAREA_NOT_READY|SUBMIT_NOT|Không tìm thấy Chrome|net::ERR/
      .test(String(runError)) ? "ENVIRONMENT" : "HARNESS";
  }
  return assertionsPass ? null : "PRODUCT_ASSERTION";
}
