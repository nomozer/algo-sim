import type { ComponentType } from "react";
import { getSimulation } from "../simulations/registry";
import type { WorkspaceProps } from "../simulations/types";
import { useAppStore } from "../state/store";

/**
 * Panel phải — nội dung QUAN SÁT theo domain qua module.Inspector (M2 #5):
 * algorithm → biến + mã giả; binary → bit; network → tuyến... Core không
 * hard-code bất kỳ nội dung domain nào.
 *
 * LỊCH SỬ CỦA CỘT NÀY — hai lần thu hẹp vai trò của AI, cùng một lý do:
 *
 * - M9-UX5: bỏ cặp tab [Quan sát][Hỏi AI] (AI chiếm một nửa cột phải) → AI
 *   xuống thành một mục THU GỌN ở đáy.
 * - Bản này: bỏ luôn mục thu gọn đó. Workspace là nơi học sinh làm việc với
 *   MÔ PHỎNG; narration + Observer phải tự đủ để giải thích bước hiện tại.
 *   Còn một nút gọi model ngay cạnh timeline nghĩa là vẫn còn một đường tiêu
 *   token trong lúc chạy, và vẫn còn một góc màn hình thường trực cho AI.
 *
 * AI nay chỉ xuất hiện ở BỐN chỗ, tất cả đều ở giai đoạn HIỂU ĐỀ, không có chỗ
 * nào trong workspace: ô nhập đề · trạng thái đang phân tích · tóm tắt "hệ
 * thống đã hiểu" · phản hồi thiếu dữ kiện / ngoài phạm vi.
 * Danh sách ĐÓNG — xem `docs/evaluation/ui-baseline/UI_INTERACTION_BASELINE.md §5`.
 */
export function SimulationInspector() {
  const active = useAppStore((s) => s.active);
  const playing = useAppStore((s) => s.playing);
  const dispatch = useAppStore((s) => s.dispatch);

  const mod = active ? getSimulation(active.moduleId) : undefined;
  const Inspector = mod?.Inspector as ComponentType<WorkspaceProps> | undefined;

  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <span className="eyebrow">QUAN SÁT</span>

      {active && Inspector ? (
        <Inspector config={active.config} state={active.state} busy={playing} dispatch={dispatch} />
      ) : (
        <p className="hint">
          {active
            ? "Mô phỏng này không có panel quan sát riêng."
            : "Chưa có mô phỏng nào đang chạy."}
        </p>
      )}
    </div>
  );
}
