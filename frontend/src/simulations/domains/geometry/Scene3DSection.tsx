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

export function Scene3DSection({ scene, de }: { scene: unknown; de?: string | null }) {
  if (!hopLeScene3D(scene)) return null;
  return (
    <section className="geo3d-section" aria-label="Xưởng hình 3D">
      {/* KHÔNG còn tiêu đề + đoạn dẫn ở đây.
          Bản trước mở đầu bằng một `<h3>` và một đoạn văn ba dòng giải thích
          hình từ đâu ra — rồi mới tới khung 3D, lúc ấy đã bị đẩy xuống dưới
          nếp gấp. Câu ấy đúng và vẫn cần, nhưng nó là chú thích cho một công
          cụ, không phải lời mở của một bài đọc: nay nó nằm sau nút «Chi tiết»
          trong chính xưởng. Học sinh mở trang ra và thấy HÌNH. */}
      <Scene3DExplorer scene={scene} de={de ?? null} />
    </section>
  );
}
