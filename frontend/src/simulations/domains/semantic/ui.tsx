/**
 * Sân khấu dự phòng của route `generic.semantic_program` — CHỈ ĐỌC khung.
 *
 * (/13) Renderer 2D container (dải ô, ngăn xếp, hàng đợi, đồ thị, bảng ánh xạ, con trỏ, hộp giá trị) là đường lên
 * màn hình của miền Tin học và đã gỡ cùng `visual_bindings` ở backend: khung giờ không mang đối tượng 2D nào. Mọi bài
 * hình học đi bằng `scene3d` (Scene3DExplorer), không tới đây. Sân khấu này chỉ còn khai TRUNG THỰC mức gộp và việc
 * chạm trần thực thi (cấm cắt câm, luật cứng #12) cho một envelope không có cảnh 3D.
 */
import type { WorkspaceProps } from "../../types";
import type { SemanticConfig, SemanticState } from "./model";

export function SemanticWorkspace({
  state,
}: WorkspaceProps<SemanticConfig, SemanticState>) {
  const buoc = state.timeline[state.cursor];
  if (!buoc) return null;

  return (
    <div className="sem-stage" data-route="semantic">
      {state.groupingLevel === "iteration" && (
        <p className="sem-note">
          Đang xem gộp: mỗi bước hiển thị trọn một vòng lặp.
        </p>
      )}
      {state.executionTruncated && (
        <p className="sem-note sem-note-warn">
          Mô phỏng dài hơn giới hạn nên chưa chạy hết.
        </p>
      )}
      {/* (SHELL-N) THUYẾT MINH KHÔNG dựng ở đây — module cấp chữ qua `narrate()` ở `index.ts`, shell dựng bằng
          `NarrationSlot`. Dựng cả hai nơi thì cùng một câu hiện HAI LẦN dưới sân khấu. */}
    </div>
  );
}
