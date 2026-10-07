/**
 * Kiểu từ chối của `/api/analyze` mà vỏ ứng dụng hiển thị (`llm/client.ts`, `state/store.ts`).
 *
 * repo-cleanup: các kiểu của bộ thực thi thuật toán Tin học (`AlgorithmId`, `AnalysisOk`, `Trace`, `Step`, …) đã gỡ
 * cùng `core/algorithms.ts`, `core/scan.ts`, `core/program.ts`, `core/trace-builder.ts` — không còn người dùng.
 */

export interface AnalysisUnsupported {
  status: "unsupported";
  reason: string;
  /** (M17 W0) Thông điệp THÂN THIỆN cho học sinh — server gắn ở biên API;
   * FE ưu tiên hiển thị nó thay cho `reason` kỹ thuật khi có. */
  learner_reason?: string;
  /** (M17-VR1) Loại từ chối — CHỈ để chọn tiêu đề/gợi ý đúng bản chất:
   * "insufficient_specification" = chủ đề CÓ hỗ trợ nhưng đề thiếu dữ kiện
   * (nói "ngoài danh mục" là sai và làm học sinh hiểu nhầm). */
  failure_category?: string;
  /** (M17 W2B-PATCH) Mã lỗi chi tiết — chỉ để chọn tiêu đề/gợi ý khi một
   * `failure_category` gộp nhiều ca cần lời khuyên khác nhau (vd
   * "pipeline_stage_incomplete" vs "multiple_operations_not_supported" đều là
   * `semantic_incomplete`). KHÔNG BAO GIỜ hiển thị mã này cho học sinh. */
  error_code?: string;
  /** (W17 §15.3) Nguyên nhân từ chối do backend quyết từ mã có cấu trúc — chỉ để chọn gợi ý:
   * `SOURCE` mời sửa dữ kiện trong đề; `CONSTRUCTION`/`UNKNOWN` không bao giờ bảo sửa đề. */
  refusal_cause?: "SOURCE" | "CONSTRUCTION" | "UNKNOWN";
  /** (W20 §17, thẻ sửa ở cuboid-final-review) Mã lý do chi tiết của backend — CHỈ để chọn nhãn "loại vấn
   * đề" khi cùng một nguyên nhân gộp hai ca khác nhau (dựng lệch đã chứng minh vs chưa kiểm chứng được).
   * KHÔNG BAO GIỜ hiển thị mã này. */
  reason_code?: string;
}
