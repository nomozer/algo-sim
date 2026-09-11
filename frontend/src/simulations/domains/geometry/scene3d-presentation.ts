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
 * Định danh CHÍNH NÓ đã là một ký hiệu toán học chưa.
 *
 * Một chữ hoa, có thể thêm tối đa hai ký tự chữ/số/phẩy. `T`, `C`, `E`, `O'`,
 * `A1` lọt; `plane_MNP`, `V_AMNP`, `ABCD_base`, `the_volume_sabcd`, `S.ABCD`
 * đều **không** lọt.
 */
const KY_HIEU_THUAN = /^[A-Z][A-Za-z0-9'′]{0,2}$/;

/**
 * Ký hiệu cho HÌNH (thiết diện, đường tròn, elip) — không dùng cho điểm.
 *
 * ⚠️ **Đây là một nới lỏng có chủ đích của luật ở đầu tệp, và nó phải ở lại
 * hẹp.** Luật ấy cấm đọc `id` để suy ra nghĩa, vì đã có lúc phía frontend tự
 * rút ký hiệu từ `id` và cho ra `plane_MNP` → `MNP`, `V_AMNP` → nguyên si.
 *
 * Nhưng backend **không phát `notation`** cho thiết diện `T`, đường tròn `C`
 * và elip `E` (kiểm trên cả bốn fixture p1/p3/p6/p7: `notation = null`), trong
 * khi ngôn ngữ thị giác đã duyệt đòi đúng ba nhãn ấy. Thêm `notation` cho
 * chúng là đổi backend — nằm ngoài phạm vi cho phép.
 *
 * Nên phía này chỉ nhận `id` khi **bản thân `id` ĐÃ LÀ một ký hiệu**, theo
 * `KY_HIEU_THUAN`. Nó không dựng tên, không cắt chuỗi, không suy diễn: hoặc
 * `id` đúng là `T` và được dùng nguyên vẹn, hoặc không có nhãn nào. Chính các
 * `id` từng gây lỗi cũ đều bị mẫu này loại — xem nền đỏ trong
 * `scene3d-presentation.test.ts`.
 *
 * `notation` khi có vẫn THẮNG, để hôm nào backend phát nó thì đường này tự
 * ngừng được dùng.
 */
export function kyHieuHinh(o: Pick<SceneObject, "notation" | "id">): string | null {
  const n = kyHieu(o);
  if (n !== null) return n;
  const id = (o.id ?? "").trim();
  return KY_HIEU_THUAN.test(id) ? id : null;
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
