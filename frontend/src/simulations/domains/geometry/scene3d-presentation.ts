/**
 * scene3d-presentation.ts — QUY TẮC TRÌNH BÀY THUẦN cho cảnh 3D.
 *
 * ─── VÌ SAO TÁCH RA MỘT FILE ──────────────────────────────────────────────
 *
 * Ba quyết định dưới đây là **trình bày**, không phải ngữ nghĩa: gọi một vật
 * bằng ký hiệu ngắn hay bằng câu mô tả, có vẽ nó lên khung mặc định hay không,
 * và ưu tiên nhãn nào khi hai nhãn chồng nhau. Chúng phải TÁCH khỏi
 * `scene3d-view` vì view là mã có `useEffect`, `THREE`, và một vòng vẽ — thứ
 * kiểm được bằng test thuần thì không nên nằm trong đó.
 *
 * ⚠️ **Không hàm nào ở đây tính toán hình học.** Chúng đọc siêu dữ liệu đã có
 * trong `SceneObject` (`id`, `label`, `type`, `producer`) và trả về quyết định
 * hiển thị. Không suy ra toạ độ, không dựng điểm, không đổi `Scene3D`.
 */
import type { SceneObject } from "./scene3d-model";

/**
 * Ký hiệu ngắn để in cạnh một vật trên khung mặc định.
 *
 * ─── VÌ SAO KHÔNG DÙNG THẲNG `label` ─────────────────────────────────────
 *
 * `label` là câu mô tả do tầng sinh cảnh viết: *"Hình chiếu vuông góc H của I
 * lên mặt phẳng (SBC)"*. Câu ấy đúng và đáng đọc — nhưng in nó cạnh một chấm
 * trên khung 3D thì bốn vật đã đủ phủ kín hình, và ảnh chụp thật cho thấy
 * chúng chồng lên nhau rồi chạy ra ngoài mép khung.
 *
 * Nên khung mặc định nói **ký hiệu hình học** — đúng thứ học sinh đọc trên
 * bảng — còn câu mô tả chuyển sang ô soi và cây thành phần. Không mất thông
 * tin, chỉ đổi chỗ trình bày.
 *
 * Quy tắc rút ký hiệu, theo thứ tự:
 *   1. `label` vốn đã ngắn (≤ 3 ký tự thấy được) ⇒ dùng nguyên.
 *   2. `id` dạng `X_prime` ⇒ `X′` (phẩy thật, không phải dấu nháy ASCII).
 *   3. `id` ngắn ⇒ dùng nguyên.
 *   4. còn lại ⇒ cắt phần đầu của `id` tới dấu gạch dưới đầu tiên.
 *
 * Bước 4 cố ý **không** rút gọn thành một câu: §8 của chỉ thị cấm biến một
 * định danh thành câu mô tả dài, và cũng cấm bịa tên hiển thị mới.
 */
export function kyHieuNgan(o: Pick<SceneObject, "id" | "label">): string {
  const nhan = (o.label ?? "").trim();
  if (nhan && nhan.length <= 3) return nhan;

  const id = (o.id ?? "").trim();
  if (!id) return nhan;

  const phay = id.replace(/_prime\b/g, "′");
  if (phay.length <= 4) return phay;

  // `vector_AA_prime` → `AA′`; `khoang_cach_A_B` → `khoang`.
  // Lấy phần MANG NGHĨA HÌNH HỌC nếu tiền tố là một từ khoá kỹ thuật đã biết.
  const bo = /^(vector|vec|point|line|plane|solid|section)_/.exec(phay);
  if (bo) {
    const con = phay.slice(bo[0].length);
    if (con) return con.length <= 6 ? con : con.split("_")[0];
  }
  return phay.length <= 6 ? phay : phay.split("_")[0];
}

/**
 * Vật này có phải một VECTƠ do tầng sinh cảnh phát ra dưới dạng điểm không?
 *
 * ─── VÌ SAO CẦN HỎI CÂU NÀY ──────────────────────────────────────────────
 *
 * Tầng sinh cảnh phát vectơ với `type: "point3"` và `render: "point_marker"`,
 * còn `xyz` là **thành phần của vectơ** chứ không phải toạ độ một điểm của
 * hình. Vẽ nó như một chấm là đặt lên khung một vật KHÔNG TỒN TẠI trong bài:
 * ảnh chụp thật cho thấy `vector_AA_prime` hiện thành một chấm đỏ ở (1,1,3),
 * nơi không có điểm nào của hình chóp.
 *
 * ─── VÌ SAO KHÔNG VẼ THÀNH MŨI TÊN ───────────────────────────────────────
 *
 * Vì `RENDER_KINDS` là hợp đồng khoá đồng bộ hai chiều với tầng sinh cảnh:
 * thêm một loại vẽ mới là đổi hợp đồng, tức đụng vào phần đang đóng băng. Và
 * dựng mũi tên từ `depends` sẽ là renderer TỰ SUY vị trí — đúng thứ ranh giới
 * R0 cấm, dù dữ liệu tình cờ có đủ.
 *
 * Nên lựa chọn ở đây là bảo thủ: **không vẽ lên khung mặc định**, giữ nguyên
 * trong cây thành phần và ô soi để vẫn tra được. Thà thiếu một mũi tên còn hơn
 * đặt lên hình một điểm không có thật.
 */
export function laVectoDangDiem(o: Pick<SceneObject, "type" | "producer">): boolean {
  if (o.type !== "point3") return false;
  const p = o.producer ?? "";
  return p === "vector_from_points" || p.endsWith(".vector_from_points");
}

/** Vật có được vẽ trên khung 3D mặc định không. */
export function veTrenKhung(o: Pick<SceneObject, "type" | "producer">): boolean {
  return !laVectoDangDiem(o);
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
