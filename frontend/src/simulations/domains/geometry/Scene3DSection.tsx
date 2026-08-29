import { Scene3DExplorer } from "./Scene3DExplorer";
import type { Scene3D } from "./scene3d-model";

/**
 * Vùng "Quá trình dựng hình 3D" trong thẻ mô phỏng — Phase 5F.
 *
 * ─── VÌ SAO LÀ MỘT VÙNG RIÊNG, KHÔNG THAY RENDERER 2D ────────────────────
 *
 * Đường 2D cũ nguyên vẹn: 24 target Tin học không đổi một dòng, và bài hình
 * học vẫn có `envelope` như mọi bài khác. Cảnh 3D là **thứ THÊM VÀO** khi
 * chương trình đã qua mọi cổng — nên nó là một khối nằm dưới, không phải một
 * chế độ tranh chỗ với `VisualModeToggle`.
 *
 * ─── VÌ SAO NHẬN `scene: unknown` ────────────────────────────────────────
 *
 * `envelope.scene3d` đến từ backend, và `SimulationEnvelope.config` cũng khai
 * `unknown` với cùng lý do: dữ liệu qua mạng thì không có gì bảo đảm hình dạng
 * ngoài việc **kiểm tại chỗ nhận**. `hopLeScene3D` là chỗ kiểm ấy, và nó
 * fail-closed: hình dạng lạ ⇒ không dựng vùng nào, không dựng một khung trống.
 *
 * Bày một khung 3D rỗng là mời người học đi tìm thứ không có.
 */

/** Kiểm hình dạng tại BIÊN NHẬN. Không tin dữ liệu qua mạng. */
export function hopLeScene3D(x: unknown): x is Scene3D {
  if (!x || typeof x !== "object") return false;
  const s = x as Partial<Scene3D>;
  return (
    Array.isArray(s.objects) &&
    s.objects.length > 0 &&
    Array.isArray(s.events) &&
    s.events.length > 0 &&
    Array.isArray(s.free_objects)
  );
}

export function Scene3DSection({ scene }: { scene: unknown }) {
  if (!hopLeScene3D(scene)) return null;
  return (
    <section className="geo3d-section" aria-labelledby="geo3d-heading">
      <h3 id="geo3d-heading" className="geo3d-heading">
        Quá trình dựng hình 3D
      </h3>
      {/* Câu này nói cho học sinh biết HÌNH NÀY TỪ ĐÂU RA — và đó là điều phân
          biệt hệ này với một phần mềm vẽ hình. Không có nó, khung 3D đọc như
          một hình vẽ ai đó đã ngồi dựng sẵn. */}
      <p className="geo3d-lead">
        Hình dưới đây do máy dựng lại từng bước theo đúng chương trình đã được
        kiểm chứng. Bạn xem được từng bước, xoay góc nhìn, và bấm vào từng
        điểm, cạnh hay mặt để xem nó từ đâu ra; hình thì không sửa được.
      </p>
      <Scene3DExplorer scene={scene} />
    </section>
  );
}
