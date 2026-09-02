/**
 * scene3d-presentation.ts — QUY TẮC TRÌNH BÀY THUẦN cho cảnh 3D.
 *
 * ─── VÌ SAO TÁCH RA MỘT FILE ──────────────────────────────────────────────
 *
 * Các quyết định dưới đây là **trình bày và chỉ trình bày**: in ký hiệu hay
 * không, vẽ vật lên khung mặc định hay không, giữ nhãn nào khi hai nhãn chồng
 * nhau. Chúng tách khỏi `scene3d-view` vì view là mã có `useEffect`, `THREE`
 * và một vòng vẽ — thứ kiểm được bằng test thuần thì không nên nằm trong đó.
 *
 * ─── ĐIỀU FILE NÀY TỪNG LÀM VÀ NAY KHÔNG CÒN ──────────────────────────────
 *
 * Hai hàm đã bị GỠ, không phải đổi tên:
 *
 *   · `kyHieuNgan(o)` — đọc ngược `id` để rút ký hiệu: bóc `_prime` thành `′`,
 *     cắt tiền tố `vector_|point_|plane_|solid_|section_`, cắt tới gạch dưới
 *     đầu tiên. Nay ký hiệu do backend phát ở `SceneObject.notation`
 *     (`display_names.py`), và nếu vắng thì **không in gì**.
 *   · `laVectoDangDiem(o)` — đọc `producer === "vector_from_points"` để nhận
 *     ra một `point3` thật ra là vectơ. Nay backend giữ nguyên kiểu khai
 *     `vector3` và phát `render: "non_visual"`.
 *
 * Cả hai là **suy lại ngữ nghĩa ở tầng trình bày**, đúng thứ ranh giới R0 cấm,
 * và cả hai chỉ tồn tại vì tầng chiếu cảnh backend đang vứt đi siêu dữ liệu nó
 * đã cầm trên tay (`GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT §3, §19`). Sửa
 * đúng gốc thì chúng biến mất, không phải chuyển chỗ.
 *
 * ⚠️ **Luật còn hiệu lực:** không hàm nào ở đây được đọc `id` để suy ra nghĩa,
 * đọc `producer` để suy ra kiểu, hay dựng một cái tên. Chúng đọc những trường
 * backend đã QUYẾT (`render`, `notation`, `origin`) và trả về quyết định bố
 * cục. Không tính toạ độ, không dựng vật, không đổi `Scene3D`.
 */
import type { SceneObject } from "./scene3d-model";

/**
 * Ký hiệu in cạnh vật trên khung, hoặc `null` nếu không in gì.
 *
 * Mỏng có chủ đích: nó **chỉ** đọc quyết định của backend. Giữ hàm thay vì đọc
 * thẳng `o.notation` ở view để chỗ này còn là một điểm duy nhất kiểm được —
 * và để lần sau ai muốn "đoán tạm một ký hiệu khi thiếu" sẽ phải sửa một hàm
 * có test, thay vì thêm một `??` giữa JSX.
 *
 * Chuỗi rỗng cũng coi như không có: một nhãn rỗng vẫn dựng ra một ô trong bộ
 * lọc chồng nhãn và chiếm chỗ của một nhãn thật.
 */
export function kyHieu(o: Pick<SceneObject, "notation">): string | null {
  const n = (o.notation ?? "").trim();
  return n === "" ? null : n;
}

/**
 * Vật có được vẽ trên khung 3D mặc định không.
 *
 * Đọc `render`, là trường backend dùng để NÓI điều đó. `readout` (đại lượng
 * đo) và `non_visual` (vectơ) đều có mặt trong cảnh, đều chọn và soi được, và
 * đều không phải hình trên khung — `readout` hiện ở dải kết quả, `non_visual`
 * không hiện ở đâu trên khung cả.
 */
export function veTrenKhung(o: Pick<SceneObject, "render">): boolean {
  return o.render !== "non_visual" && o.render !== "readout";
}

/**
 * Ưu tiên nhãn khi hai nhãn chồng nhau — số càng lớn càng được giữ.
 *
 * Không dựng bộ bố trí nhãn tổng quát; chỉ cần một thứ tự để khi va nhau thì
 * biết ẩn cái nào. Vật đang chọn luôn thắng, vì đó là thứ người dùng vừa hỏi.
 */
export function uuTienNhan(
  o: Pick<SceneObject, "id" | "origin">,
  dangChon: string | null,
): number {
  if (dangChon && o.id === dangChon) return 3;
  return o.origin === "derived" ? 2 : 1;
}

/** Nửa chiều rộng/cao (điểm ảnh) coi là "chồng nhau" giữa hai nhãn. */
export const NGUONG_CHONG_NHAN = { x: 34, y: 11 } as const;

/**
 * Chọn nhãn nào được hiện khi một số nhãn chồng nhau.
 *
 * Thuật toán cố ý đơn giản và tất định: xếp theo ưu tiên giảm dần, giữ nhãn
 * nào không đè lên một nhãn đã giữ. Không tìm cách xê dịch nhãn — xê dịch làm
 * nhãn rời khỏi vật nó gọi tên, và lúc ấy hình sai theo một kiểu khác.
 */
export function locNhanChongNhau(
  nhan: { id: string; x: number; y: number; uuTien: number }[],
): Set<string> {
  const giu: { x: number; y: number }[] = [];
  const ket = new Set<string>();
  for (const n of [...nhan].sort((a, b) => b.uuTien - a.uuTien || a.id.localeCompare(b.id))) {
    const dung = giu.some(
      (g) => Math.abs(g.x - n.x) < NGUONG_CHONG_NHAN.x * 2
        && Math.abs(g.y - n.y) < NGUONG_CHONG_NHAN.y * 2,
    );
    if (dung) continue;
    giu.push({ x: n.x, y: n.y });
    ket.add(n.id);
  }
  return ket;
}
