/**
 * DẢI LỚP HỌC TRỰC TIẾP — hai bề mặt, một dòng, trong thanh xưởng.
 *
 * ─── VÌ SAO NẰM TRONG THANH XƯỞNG, KHÔNG NỔI ĐÈ LÊN CANVAS ──────────────
 *
 * Bản mẫu tôi được xem có một thanh điều khiển NỔI, và tác giả đã phải viết
 * hẳn một `ResizeObserver` đo chiều cao rồi cộng padding bù — mà ảnh chụp vẫn
 * cho thấy nó che mất hàng nút học sinh đang cần bấm. Thanh nổi trên một mặt
 * làm việc cuộn được là một cái bẫy bố cục, không phải một lựa chọn thẩm mỹ.
 *
 * Ở đây dải chiếm chỗ THẬT trong thanh trên (một hàng flex đã có sẵn), nên
 * không có gì để che và không cần đo gì.
 *
 * ─── KHÔNG NÚT GIẢ ──────────────────────────────────────────────────────
 *
 * Mỗi nút hoặc GỌI THẬT một endpoint, hoặc `disabled` kèm `title` nói vì sao.
 * Chưa có tiết nào chạy thì «Đồng bộ» tắt — không phải mờ đi cho đẹp mà vì
 * không có gì để đồng bộ về.
 */
import { useState } from "react";
import type { ClassroomSession } from "../state/classroom-sync";

export interface LiveDockProps {
  session: ClassroomSession | null;
  className: string;
  studentCount: number;
  helpCount: number;
  /** `null` = chưa chọn bài; nút bắt đầu tiết vẫn dùng được (chiếu bài trống). */
  assignmentId: number | null;
  busy?: boolean;
  onStart: () => void;
  onEnd: () => void;
  onSetMode: (mode: "follow" | "free") => void;
  onSync: () => void;
  onMonitor: () => void;
}

export function LiveClassDock(p: LiveDockProps) {
  const [thu, setThu] = useState(false);
  const dangDay = p.session !== null;
  const mode = p.session?.mode ?? "follow";

  if (thu) {
    return (
      <button type="button" className="live-dock-thu"
        onClick={() => setThu(false)}
        title="Mở bảng điều khiển lớp">
        <span className={`live-cham${dangDay ? " dang-day" : ""}`} aria-hidden="true" />
        {p.className}
        {p.helpCount > 0 && <span className="live-canh-bao">{p.helpCount}</span>}
      </button>
    );
  }

  return (
    <div className="live-dock" role="group" aria-label="Điều khiển lớp học">
      <button type="button" className="live-dock-gap" onClick={() => setThu(true)}
        title="Thu gọn bảng điều khiển">
        <span className={`live-cham${dangDay ? " dang-day" : ""}`} aria-hidden="true" />
        <span className="live-lop">{p.className}</span>
        <span className="live-si-so">{p.studentCount} HS</span>
      </button>

      {!dangDay ? (
        <button type="button" className="live-nut live-nut-chinh"
          onClick={p.onStart} disabled={p.busy}>
          Bắt đầu tiết
        </button>
      ) : (
        <>
          {/* Hai chế độ là MỘT lựa chọn, nên dựng như một cặp — không phải hai
              công tắc độc lập có thể cùng bật. */}
          <div className="live-cap" role="radiogroup" aria-label="Chế độ lớp">
            <button type="button" role="radio" aria-checked={mode === "follow"}
              className={`live-nut${mode === "follow" ? " la-chon" : ""}`}
              onClick={() => p.onSetMode("follow")} disabled={p.busy}>
              Theo cô/thầy
            </button>
            <button type="button" role="radio" aria-checked={mode === "free"}
              className={`live-nut${mode === "free" ? " la-chon" : ""}`}
              onClick={() => p.onSetMode("free")} disabled={p.busy}>
              Cho tự khám phá
            </button>
          </div>

          <button type="button" className="live-nut" onClick={p.onSync}
            disabled={p.busy}
            title="Đưa cả lớp về đúng màn hình cô/thầy đang xem — một lần, không đổi chế độ">
            Gọi cả lớp về đây
          </button>

          <button type="button" className="live-nut" onClick={p.onMonitor}>
            Theo dõi
            {p.helpCount > 0 && <span className="live-canh-bao">{p.helpCount}</span>}
          </button>

          <button type="button" className="live-nut live-nut-ket"
            onClick={p.onEnd} disabled={p.busy}>
            Kết thúc
          </button>
        </>
      )}
    </div>
  );
}

/**
 * CHỈ BÁO của học sinh — nhỏ, một dòng, không bao giờ chặn màn hình.
 *
 * Nói bằng tiếng học sinh: không có `follow`, `free`, `cmd_id` hay
 * `selected_id` nào lọt ra đây (`ui-hygiene`). Và khi phiên đã cũ thì nói
 * thật là đang kết nối lại, thay vì giả vờ vẫn đang đồng bộ.
 */
export function StudentLiveIndicator({
  session, stale,
}: {
  session: ClassroomSession | null;
  /** Lần hỏi cuối đã quá lâu — máy chủ có thể đang không trả lời. */
  stale?: boolean;
}) {
  if (session === null) return null;
  if (stale) {
    return (
      <span className="live-chi-bao la-cu" role="status">
        <span className="live-cham" aria-hidden="true" /> Đang kết nối lại…
      </span>
    );
  }
  return (
    <span className="live-chi-bao" role="status">
      <span className="live-cham dang-day" aria-hidden="true" />
      {session.mode === "follow" ? "Đang theo cô/thầy" : "Em tự khám phá"}
    </span>
  );
}

/**
 * NÚT GIƠ TAY. Dễ thấy, nhưng không lấn canvas — nó sống trong thanh trên
 * cùng hàng với chỉ báo, không nổi lên trên hình.
 *
 * Sau khi báo thì nút ĐỔI VAI: không cho bấm lại lần nữa (spam làm bảng của
 * giáo viên đầy cùng một tên), chỉ còn đường huỷ.
 */
export function HelpRequestButton({
  requested, busy, onRequest, onCancel,
}: {
  requested: boolean;
  busy?: boolean;
  onRequest: () => void;
  onCancel: () => void;
}) {
  if (requested) {
    return (
      <span className="live-tro-giup la-gui">
        <span role="status">Đã báo cô/thầy</span>
        <button type="button" className="live-nut" onClick={onCancel} disabled={busy}>
          Huỷ
        </button>
      </span>
    );
  }
  return (
    <button type="button" className="live-nut live-nut-giup"
      onClick={onRequest} disabled={busy}>
      Em cần hỗ trợ
    </button>
  );
}
