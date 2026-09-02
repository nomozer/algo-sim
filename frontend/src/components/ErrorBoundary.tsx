import { Component, type ErrorInfo, type ReactNode } from "react";

/**
 * CHẶN NGOẠI LỆ BẤT NGỜ — phòng thủ theo chiều sâu, không phải vá một lỗ đang chảy.
 *
 * ─── VÌ SAO CẦN, DÙ CHƯA CÓ LỖI NÀO ĐO ĐƯỢC ──────────────────────────────
 *
 * Trước bản này kho **không có một error boundary nào**, nên cả năm miền —
 * `HOME`, `WORKSPACE`, `SCENE3D`, `INSPECTOR`, `PLAYBACK` — chung **một số
 * phận**: một lần ném ở bất kỳ đâu là React gỡ trọn cây và người dùng nhìn một
 * trang trắng, không còn cả thanh điều hướng để đi tiếp.
 *
 * Bốn dạng envelope hỏng đã đo đều đi qua êm (`certify-refusal-surface` 21/21),
 * nên đây **không** phải bản vá cho một lỗi đang xảy ra. Nó là lưới cuối cho
 * lớp lỗi mà không phép kiểm dữ liệu nào bắt được: một bất biến bị phá trong
 * lúc dựng hình.
 *
 * ─── ĐIỀU NÓ KHÔNG BẮT — PHẢI NÓI RA ────────────────────────────────────
 *
 * React error boundary bắt ngoại lệ trong **render**, **lifecycle** và
 * **constructor** của cây con. Nó **KHÔNG** bắt:
 *
 *   · ngoại lệ trong trình xử lý sự kiện (`onClick`…);
 *   · promise bị từ chối mà không ai bắt;
 *   · `setTimeout` / `requestAnimationFrame` — kể cả vòng vẽ của Three.js;
 *   · lỗi ném từ chính fallback này.
 *
 * Nói *"đã chặn mọi lỗi frontend"* sau khi thêm boundary là một tuyên bố sai.
 * `docs/REACT_ERROR_BOUNDARY_HARDENING.md` phân loại từng lớp còn hở.
 *
 * ─── LỖI MIỀN KHÔNG ĐI QUA ĐÂY ──────────────────────────────────────────
 *
 * Đề ngoài phạm vi, xuất xứ không đủ, chương trình không dựng được — tất cả là
 * **kết quả hợp lệ của sản phẩm**, có bề mặt từ chối riêng và **không ném**.
 * Chúng phải tiếp tục không chạm tới component này; định tuyến một lời từ chối
 * qua `throw` để boundary lo là biến một câu trả lời thành một sự cố.
 */

interface Props {
  children: ReactNode;
  /**
   * Đổi giá trị này ⇒ **quên lỗi cũ và dựng lại**.
   *
   * Không có nó thì `hasError` dính vĩnh viễn: người dùng mở một bài khác,
   * cây con mới hoàn toàn, nhưng boundary vẫn nhớ lỗi của bài trước và tiếp
   * tục hiện fallback. Đây đúng lớp lỗi mà bản vá trạng thái-sót
   * (`Bước 10/6`) đã dạy một lần — trạng thái sống lâu hơn thứ sinh ra nó.
   */
  resetKey?: string;
  /** Nhãn miền, chỉ để ghi log — không hiện cho người học. */
  mien: string;
  /**
   * Giao diện thay thế. Nhận `thuLai` để dựng nút phục hồi.
   *
   * ⚠️ Fallback **không được đọc dữ liệu có thể đã gây ra lỗi** — không
   * `scene.objects`, không vật đang chọn, không khung hiện tại. Nó dựng từ chữ
   * tĩnh và một callback, nếu không thì lỗi lặp vô hạn ngay trong lưới cuối.
   */
  fallback: (thuLai: () => void) => ReactNode;
}

interface State {
  hong: boolean;
  /** Khoá đã thấy ở lần dựng trước — để phát hiện đổi bài. */
  khoa?: string;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hong: false };

  static getDerivedStateFromError(): Partial<State> {
    return { hong: true };
  }

  /**
   * ĐỔI KHOÁ ⇒ QUÊN LỖI, và làm ở đây chứ không ở `componentDidUpdate`:
   * `getDerivedStateFromProps` chạy **trước** khi dựng lại, nên cây con mới
   * không bao giờ bị fallback của bài cũ chặn mất một nhịp.
   */
  static getDerivedStateFromProps(p: Props, s: State): Partial<State> | null {
    if (p.resetKey !== s.khoa) return { hong: false, khoa: p.resetKey };
    return null;
  }

  componentDidCatch(loi: Error, tin: ErrorInfo): void {
    /* GIỮ QUAN SÁT ĐƯỢC. Nuốt im lặng thì boundary biến một trang trắng thành
     * một lỗi không ai biết — tệ hơn, vì trang trắng ít ra còn kêu.
     *
     * `console.error` chứ không phải một tầng telemetry: kho không có nơi thu
     * log, và dựng một cái chỉ cho chỗ này là thêm hạ tầng cho một dòng. Không
     * gửi gì ra ngoài. */
    // eslint-disable-next-line no-console
    console.error(`[ErrorBoundary:${this.props.mien}]`, loi, tin.componentStack);
  }

  render(): ReactNode {
    if (!this.state.hong) return this.props.children;
    return this.props.fallback(() => this.setState({ hong: false }));
  }
}

/**
 * Giao diện thay thế dùng chung — **chữ tĩnh và một nút**, không hơn.
 *
 * Không hiện vết ngăn xếp, không hiện tên component, không hiện định danh máy:
 * người học không đọc được chúng, và chúng là đúng loại chữ mà
 * `ui-hygiene` cấm lọt lên bề mặt. Người phát triển đọc chúng ở bảng điều
 * khiển, nơi `componentDidCatch` vừa ghi.
 */
export function ErrorFallback(
  { loiNhan, hanhDong, onHanhDong }: {
    loiNhan: string;
    hanhDong: string;
    onHanhDong: () => void;
  },
) {
  return (
    <div className="loi-chan" role="alert">
      <p className="loi-chan-nhan">{loiNhan}</p>
      <button type="button" className="btn-primary" onClick={onHanhDong}>
        {hanhDong}
      </button>
    </div>
  );
}
