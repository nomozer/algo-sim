import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { IconCheck, IconChevronDown } from "../../../components/icons";

/**
 * MENU NHÓM CÔNG CỤ của hàng trên xưởng 3D (regular-square-pyramid-w05).
 *
 * Hàng trên chỉ giữ thao tác chính có chữ; công cụ cùng loại gom vào một nút menu có chữ («Khám phá», «Hiển thị»,
 * «Thêm»), và tính năng sau này vào một nhóm chứ không thành một chip nữa trên thanh. Không phải hệ bảng thứ hai:
 * menu chỉ là LỐI VÀO — bảng thông tin vẫn là `BangNoi` (W4), công tắc trình bày vẫn là state của xưởng.
 *
 * Mẫu ARIA menu-button: nút có `aria-haspopup="menu"` + `aria-expanded`; mở ⇒ tiêu điểm vào mục đầu; mũi tên/Home/
 * End đi giữa các mục (`buocMenu`, hàm thuần); Escape đóng và trả tiêu điểm về nút; bấm ra ngoài hay Tab đóng. Mục
 * công tắc là `menuitemcheckbox` (`aria-checked`); mục `giuMo` (công tắc trình bày) giữ menu mở, mục khác đóng nó.
 */

export interface MucMenu {
  nhan: string;
  onChon: () => void;
  /** Có ⇒ mục công tắc (`menuitemcheckbox`, `aria-checked`). */
  chon?: boolean;
  /** Giữ menu mở sau khi chọn (bật nhiều công tắc liền); mặc định đóng và trả tiêu điểm về nút menu. */
  giuMo?: boolean;
  title?: string;
}

/** Mục kế tiếp theo phím trong menu `n` mục; `null` ⇒ phím không thuộc điều hướng menu. */
export function buocMenu(i: number, n: number, phim: string): number | null {
  if (n <= 0) return null;
  if (phim === "ArrowDown") return (i + 1) % n;
  if (phim === "ArrowUp") return (i - 1 + n) % n;
  if (phim === "Home") return 0;
  if (phim === "End") return n - 1;
  return null;
}

/** Trình duyệt cho phép toàn màn hình (`document.fullscreenEnabled`); SSR/không hỗ trợ ⇒ `false`. */
export function hoTroToanManHinh(doc: Pick<Document, "fullscreenEnabled"> | undefined): boolean {
  return !!doc?.fullscreenEnabled;
}

export function MenuCongCu({ nhan, khoa, muc, chanMenu }: {
  nhan: string;
  /** Khoá ổn định của nhóm — `data-mo-nhom`, nơi bảng mở từ menu trả tiêu điểm về khi đóng. */
  khoa: string;
  muc: MucMenu[];
  /** Nội dung không bấm được dưới các mục (vd chú giải màu). */
  chanMenu?: ReactNode;
}) {
  const [mo, setMo] = useState(false);
  const goc = useRef<HTMLDivElement>(null);
  const nut = useRef<HTMLButtonElement>(null);
  const id = useId();
  const cacMuc = () => [...(goc.current?.querySelectorAll<HTMLElement>("[role^=menuitem]") ?? [])];

  useEffect(() => {
    if (!mo) return undefined;
    cacMuc()[0]?.focus();
    const ngoai = (e: PointerEvent) => {
      if (!goc.current?.contains(e.target as Node)) setMo(false);
    };
    document.addEventListener("pointerdown", ngoai);
    return () => document.removeEventListener("pointerdown", ngoai);
  }, [mo]);

  const phim = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      setMo(false);
      nut.current?.focus();
      return;
    }
    if (e.key === "Tab") { setMo(false); return; }
    const ds = cacMuc();
    const k = buocMenu(ds.indexOf(document.activeElement as HTMLElement), ds.length, e.key);
    if (k !== null) {
      e.preventDefault();
      ds[k]?.focus();
    }
  };

  return (
    <div className="geo3d-menu" ref={goc} onKeyDown={mo ? phim : undefined}>
      <button
        ref={nut}
        type="button"
        className={`geo3d-menu-nut${mo ? " la-mo" : ""}`}
        aria-haspopup="menu"
        aria-expanded={mo}
        aria-controls={mo ? id : undefined}
        data-mo-nhom={khoa}
        onClick={() => setMo((x) => !x)}
      >
        {nhan}
        <IconChevronDown size={14} />
      </button>
      {mo && (
        <div className="geo3d-menu-hop" id={id} role="menu" aria-label={nhan}>
          {muc.map((m) => (
            <button
              key={m.nhan}
              type="button"
              role={m.chon === undefined ? "menuitem" : "menuitemcheckbox"}
              aria-checked={m.chon}
              className="geo3d-menu-muc"
              title={m.title}
              tabIndex={-1}
              onClick={() => {
                m.onChon();
                if (!m.giuMo) { setMo(false); nut.current?.focus(); }
              }}
            >
              <span className="geo3d-menu-dau">{m.chon && <IconCheck size={14} />}</span>
              {m.nhan}
            </button>
          ))}
          {chanMenu}
        </div>
      )}
    </div>
  );
}

/**
 * DẢI LỚP GỌN (classroom-band-fit, `ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW`).
 *
 * Màn rộng: vỏ `display: contents` ⇒ dải lớp vẫn là các mục của hàng trên, y như trước; nút chip ẩn. Màn chật (CSS,
 * cùng điều kiện với khối ngang thấp + điện thoại dọc thấp): dải gom vào MỘT chip trên hàng đầu — chip mang `tomTat`
 * (trạng thái lớp, chỉ đọc) — và chạm chip thì dải ĐẦY ĐỦ hiện trong hộp thả. Chiều cao không còn chỗ cho dải một dòng
 * riêng (sàn canvas 320 px, vùng chạm 44 px). Không phải menu ARIA: trong hộp là nút, nhóm chọn, hộp thoại — mẫu
 * disclosure (`aria-expanded` + vùng). Bấm ra ngoài / Escape đóng như `MenuCongCu`; hộp thoại con tự lo phím của nó.
 */
export function NhomLop({ tomTat, children }: { tomTat: ReactNode; children: ReactNode }) {
  const [mo, setMo] = useState(false);
  const goc = useRef<HTMLDivElement>(null);
  const nut = useRef<HTMLButtonElement>(null);
  const id = useId();

  useEffect(() => {
    if (!mo) return undefined;
    const ngoai = (e: PointerEvent) => {
      if (!goc.current?.contains(e.target as Node)) setMo(false);
    };
    document.addEventListener("pointerdown", ngoai);
    return () => document.removeEventListener("pointerdown", ngoai);
  }, [mo]);

  const phim = (e: React.KeyboardEvent) => {
    if (e.key !== "Escape" || (e.target as Element).closest?.("[role=dialog]")) return;
    e.preventDefault();
    setMo(false);
    nut.current?.focus();
  };

  return (
    <div className={`geo3d-lop${mo ? " la-mo" : ""}`} ref={goc} onKeyDown={mo ? phim : undefined}>
      <button
        ref={nut}
        type="button"
        className="geo3d-menu-nut geo3d-lop-nut"
        aria-expanded={mo}
        aria-controls={id}
        title="Lớp học — trạng thái và điều khiển"
        onClick={() => setMo((x) => !x)}
      >
        <span className="geo3d-lop-tom">{tomTat}</span>
        <IconChevronDown size={14} />
      </button>
      <div className="geo3d-lop-than" id={id} role="group" aria-label="Lớp học">{children}</div>
    </div>
  );
}
