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
  if (n === "") return null;
  return n;
}

/**
 * Ký hiệu hiển thị của các điểm đang hiện — nếu nhiều điểm có ký hiệu cùng nằm
 * tại đúng một vị trí (`xyz` trùng nhau), ghép ký hiệu bằng `" ≡ "` (điểm đề
 * cho đứng trước điểm dựng) để chân đường vuông góc `H` trùng đỉnh `B` hiện
 * thành `"B ≡ H"` thay vì làm biến mất tên đỉnh `B`.
 */
export function kyHieuDiem<T extends Pick<SceneObject, "id" | "notation" | "origin" | "xyz">>(
  diem: T[],
  khoa: (o: T) => string = (o) => o.xyz?.join("|") ?? o.id,
): Map<string, string> {
  const nhom = new Map<string, T[]>();
  for (const o of diem) {
    if (!kyHieu(o)) continue;
    const k = khoa(o);
    const ds = nhom.get(k) ?? [];
    ds.push(o);
    nhom.set(k, ds);
  }
  const ra = new Map<string, string>();
  for (const ds of nhom.values()) {
    const sap = [...ds].sort((a, b) => (a.origin === "free" ? 0 : 1) - (b.origin === "free" ? 0 : 1));
    const chu = [...new Set(sap.map((o) => kyHieu(o)!))].join(" ≡ ");
    for (const o of ds) ra.set(o.id, chu);
  }
  return ra;
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

/** Khe tối thiểu (điểm ảnh) giữa hai hộp nhãn điểm đang hiện. */
export const KHE_NHAN_PX = 2;

/**
 * Chọn nhãn nào được hiện khi một số nhãn chồng nhau.
 *
 * Thuật toán cố ý đơn giản và tất định: xếp theo ưu tiên giảm dần, giữ nhãn
 * nào không đè lên một nhãn đã giữ. Không tìm cách xê dịch nhãn — xê dịch làm
 * nhãn rời khỏi vật nó gọi tên, và lúc ấy hình sai theo một kiểu khác.
 *
 * "Đè" là hộp THẬT `w × h` của nhãn chạm nhau (cộng khe `KHE_NHAN_PX`); hộp đặt như `scene3d-view` đặt nhãn:
 * `translate(-50%,-140%)` từ neo (x, y). Bản trước dùng một cửa sổ cố định 68×22 px, cỡ cho câu mô tả dài thời
 * trước; với ký hiệu ngắn nó giấu oan đỉnh S cạnh H1 và A′, B′ cạnh H1 (run `scene3d-construction-audit`).
 */
export function locNhanChongNhau(
  nhan: { id: string; x: number; y: number; lx?: number; ly?: number; duoi?: boolean; uuTien: number; w: number; h: number }[],
): Set<string> {
  const hop = (n: { x: number; y: number; lx?: number; ly?: number; duoi?: boolean; w: number; h: number }) =>
    n.lx !== undefined && n.ly !== undefined
      ? [n.lx, n.ly, n.lx + n.w, n.ly + n.h]
      : n.duoi
        ? [n.x - n.w / 2, n.y + 0.4 * n.h, n.x + n.w / 2, n.y + 1.4 * n.h]
        : [n.x - n.w / 2, n.y - 1.4 * n.h, n.x + n.w / 2, n.y - 0.4 * n.h];
  const giu: number[][] = [];
  const ket = new Set<string>();
  for (const n of [...nhan].sort((a, b) => b.uuTien - a.uuTien || a.id.localeCompare(b.id))) {
    const [l, t, r, b] = hop(n);
    const dung = giu.some(([gl, gt, gr, gb]) =>
      l < gr + KHE_NHAN_PX && gl < r + KHE_NHAN_PX && t < gb + KHE_NHAN_PX && gt < b + KHE_NHAN_PX);
    if (dung) continue;
    giu.push([l, t, r, b]);
    ket.add(n.id);
  }
  return ket;
}
