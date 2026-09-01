import { registerSemanticDomain } from "./domains/semantic";

export * from "./types";
export { getSimulation, listSimulations, registerSimulation } from "./registry";

let registered = false;

/**
 * Đăng ký domain mô phỏng vào registry (gọi một lần khi app khởi động).
 *
 * ─── VÌ SAO CHỈ CÒN MỘT DÒNG (FRONTEND_LEGACY_FIXTURE_CUTOVER, 2026-09-02) ─
 *
 * Đề tài là **mô phỏng 3D hình học không gian**. Chín domain Tin học
 * (`algorithm`, `binary`, `color`, `database`, `generic`, `logic`, `network`,
 * `tree`, `web`) đã gỡ khỏi mã ĐANG CHẠY, đồng bộ với việc gỡ danh mục 24
 * target ở backend. Git history là bản lưu — không dựng `domains/legacy/`.
 *
 * ⚠️ `geometry` KHÔNG có mặt ở đây, và đó là ĐÚNG: mặt 3D không đi qua
 * registry. `SimulationWorkspace` gắn `Scene3DExplorer` thẳng khi envelope
 * mang một `scene3d` hợp lệ. `semantic` mới là thứ đăng ký
 * `generic.semantic_program` — `simulation_id` DUY NHẤT sản phẩm phát ra.
 *
 * `fromLegacyAnalysis`/`toSimulationId` cũng đi cùng `legacy.ts`: chúng ánh xạ
 * `algorithm_id` của bài mẫu Tin học sang `simulation_id`, và không bài mẫu
 * nào còn tồn tại để ánh xạ.
 */
export function registerAllSimulations(): void {
  if (registered) return;
  registered = true;
  registerSemanticDomain();
}
