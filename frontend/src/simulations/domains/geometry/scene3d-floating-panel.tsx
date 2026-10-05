/**
 * BẢNG NỔI trên vùng mô phỏng — regular-square-pyramid-w02 · B (thay cột «Các bước dựng» của W1).
 *
 * W1 dành cho danh sách bước một CỘT lưới cạnh khung: mở bảng thì khung 3D co lại và camera đổi tỉ lệ. Bảng nổi
 * nằm TRÊN khung, không chiếm chỗ trong bố cục; mở/đóng không đổi kích thước canvas.
 *
 *   desktop (> 48rem)  nổi ở phía phải vùng mô phỏng; kéo bằng TIÊU ĐỀ (thao tác con trỏ không tới canvas nên không
 *                      xoay hình); phím mũi tên trên tiêu đề dời bảng; luôn kẹp trong vùng mô phỏng, kể cả khi đổi cỡ
 *                      cửa sổ, nên nút đóng luôn thấy được; có nút về vị trí mặc định
 *   khổ hẹp            bảng trong dòng chảy dưới điều khiển (CSS), thu gọn được; không kéo — không tranh thao tác với orbit
 *
 * Vị trí do NGƯỜI GỌI giữ (`viTri`/`onViTri`): đóng rồi mở lại không mất chỗ người học đã kéo tới. `null` = mặc định.
 * Hàm thuần `kepBang`/`dichBangPhim` giữ luật; component chỉ nối sự kiện.
 */
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { IconChevronDown, IconClose, IconReset } from "../../../components/icons";

export interface ViTriBang { x: number; y: number }
export interface Khung { x: number; y: number; w: number; h: number }

/** Lề tối thiểu (px) giữa bảng và mép vùng mô phỏng. */
export const LE_BANG = 8;
/** Bước dời bằng phím mũi tên (px); giữ Shift ⇒ gấp bốn. */
export const BUOC_PHIM = 16;

/** Kẹp góc trên-trái của bảng cỡ `co` vào `khung` (toạ độ cùng hệ); bảng to hơn khung ⇒ dính lề trên-trái. */
export function kepBang(p: ViTriBang, co: { w: number; h: number }, khung: Khung): ViTriBang {
  const kep = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), Math.max(lo, hi));
  return {
    x: kep(p.x, khung.x + LE_BANG, khung.x + khung.w - co.w - LE_BANG),
    y: kep(p.y, khung.y + LE_BANG, khung.y + khung.h - co.h - LE_BANG),
  };
}

/** Vị trí mặc định: phía phải, sát trên vùng mô phỏng. */
export function viTriMacDinh(co: { w: number; h: number }, khung: Khung): ViTriBang {
  return kepBang({ x: khung.x + khung.w - co.w - 2 * LE_BANG, y: khung.y + 2 * LE_BANG }, co, khung);
}

/** Phím mũi tên ⇒ vị trí mới (chưa kẹp); phím khác ⇒ `null`. */
export function dichBangPhim(p: ViTriBang, key: string, shift: boolean): ViTriBang | null {
  const d = BUOC_PHIM * (shift ? 4 : 1);
  const v: Record<string, [number, number]> = {
    ArrowLeft: [-d, 0], ArrowRight: [d, 0], ArrowUp: [0, -d], ArrowDown: [0, d],
  };
  return v[key] ? { x: p.x + v[key][0], y: p.y + v[key][1] } : null;
}

/** Bảng có đang NỔI không — do CSS quyết theo khổ màn hình (khổ hẹp thì trong dòng chảy). */
const dangNoi = (el: HTMLElement | null) => !!el && getComputedStyle(el).position === "absolute";

export function BangNoi({
  id, tieuDe, viTri, onViTri, onDong, khungRef, children,
}: {
  id: string;
  tieuDe: string;
  viTri: ViTriBang | null;
  onViTri: (p: ViTriBang | null) => void;
  onDong: () => void;
  /** Phần tử là VÙNG MÔ PHỎNG; bảng kẹp trong hộp của nó (toạ độ theo khối chứa của bảng). */
  khungRef: { current: HTMLElement | null };
  children: ReactNode;
}) {
  const ref = useRef<HTMLElement>(null);
  const keo = useRef<{ id: number; cx: number; cy: number; x: number; y: number } | null>(null);
  const [thuGon, setThuGon] = useState(false);
  const [, setNhip] = useState(0);

  /** Hộp vùng mô phỏng theo hệ toạ độ của khối chứa bảng (`offsetParent`). */
  const khung = (): Khung | null => {
    const el = ref.current;
    const k = khungRef.current;
    const cha = el?.offsetParent as HTMLElement | null;
    if (!el || !k || !cha) return null;
    const a = k.getBoundingClientRect();
    const b = cha.getBoundingClientRect();
    return { x: a.left - b.left, y: a.top - b.top, w: a.width, h: a.height };
  };
  const co = () => ({ w: ref.current?.offsetWidth ?? 0, h: ref.current?.offsetHeight ?? 0 });
  const hienTai = (): ViTriBang | null => {
    const k = khung();
    return k ? (viTri ? kepBang(viTri, co(), k) : viTriMacDinh(co(), k)) : null;
  };

  // Đổi cỡ cửa sổ / vùng mô phỏng ⇒ vẽ lại để kẹp lại (vị trí đã kéo vẫn giữ, chỉ hiển thị bị kẹp).
  useEffect(() => {
    const nhip = () => setNhip((n) => n + 1);
    window.addEventListener("resize", nhip);
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(nhip) : null;
    if (ro && khungRef.current) ro.observe(khungRef.current);
    return () => { window.removeEventListener("resize", nhip); ro?.disconnect(); };
  }, [khungRef]);
  // Lần vẽ đầu chưa đo được hộp ⇒ vẽ lại một lần sau khi gắn vào DOM.
  useLayoutEffect(() => { setNhip((n) => n + 1); }, []);

  const p = dangNoi(ref.current) ? hienTai() : null;
  return (
    <section
      ref={ref}
      id={id}
      className={`geo3d-bang-noi${thuGon ? " la-thu-gon" : ""}`}
      aria-label={tieuDe}
      data-che-khung=""
      data-panel-x={p ? Math.round(p.x) : undefined}
      data-panel-y={p ? Math.round(p.y) : undefined}
      style={p ? { left: `${p.x}px`, top: `${p.y}px`, right: "auto" } : undefined}
      onKeyDown={(e) => {
        if (e.key === "Escape") { e.stopPropagation(); onDong(); }
      }}
    >
      <div
        className="geo3d-bang-noi-dau"
        tabIndex={0}
        role="group"
        aria-label={`${tieuDe} — kéo hoặc dùng phím mũi tên để dời bảng`}
        onPointerDown={(e) => {
          if (!dangNoi(ref.current) || (e.target as HTMLElement).closest("button")) return;
          const v = hienTai();
          if (!v) return;
          e.preventDefault();
          e.currentTarget.setPointerCapture(e.pointerId);
          keo.current = { id: e.pointerId, cx: e.clientX, cy: e.clientY, x: v.x, y: v.y };
        }}
        onPointerMove={(e) => {
          const k = keo.current;
          const kh = khung();
          if (!k || k.id !== e.pointerId || !kh) return;
          onViTri(kepBang({ x: k.x + e.clientX - k.cx, y: k.y + e.clientY - k.cy }, co(), kh));
        }}
        onPointerUp={(e) => {
          if (keo.current?.id === e.pointerId) keo.current = null;
        }}
        onPointerCancel={() => { keo.current = null; }}
        onKeyDown={(e) => {
          const v = hienTai();
          const kh = khung();
          const moi = v && kh && dangNoi(ref.current) ? dichBangPhim(v, e.key, e.shiftKey) : null;
          if (!moi || !kh) return;
          e.preventDefault();
          onViTri(kepBang(moi, co(), kh));
        }}
      >
        <h4 className="geo3d-bang-noi-tieu">{tieuDe}</h4>
        <button type="button" className="geo3d-soi-dong geo3d-bang-noi-gon" aria-expanded={!thuGon}
                aria-label={thuGon ? "Mở rộng bảng" : "Thu gọn bảng"} onClick={() => setThuGon((x) => !x)}>
          <IconChevronDown />
        </button>
        <button type="button" className="geo3d-soi-dong geo3d-bang-noi-ve" aria-label="Về vị trí mặc định"
                onClick={() => onViTri(null)} disabled={viTri === null}>
          <IconReset />
        </button>
        <button type="button" className="geo3d-soi-dong" aria-label="Đóng" onClick={onDong}>
          <IconClose />
        </button>
      </div>
      {!thuGon && <div className="geo3d-bang-noi-than">{children}</div>}
    </section>
  );
}
