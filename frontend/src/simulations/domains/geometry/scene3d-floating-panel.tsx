/**
 * BẢNG NỔI trên vùng mô phỏng — MỘT cơ chế cho MỌI bảng thông tin của xưởng.
 *
 * regular-square-pyramid-w02 · B tạo nó cho «Các bước dựng» (thay cột W1). regular-square-pyramid-w04 (H-W2-3) đưa
 * mọi bảng thông tin lên cùng cơ chế: ô soi (Chi tiết đối tượng), Xem đề, Thành phần, Đại lượng, Các bước dựng —
 * kiểm kê ở `docs/evaluation/geometry/runs/regular-square-pyramid-w04/diagnostics/PANEL_INVENTORY.md`.
 *
 *   desktop (> 48rem)  nổi TRÊN vùng mô phỏng, không chiếm chỗ trong bố cục: mở/đóng/chọn không đổi cỡ canvas, không
 *                      đổi camera, không đổi bước. Kéo bằng TIÊU ĐỀ (con trỏ không tới canvas nên không xoay hình),
 *                      phím mũi tên trên tiêu đề dời bảng, Escape đóng; luôn kẹp trong vùng mô phỏng kể cả khi đổi cỡ
 *                      cửa sổ; nút về vị trí mặc định; thu gọn. Nhiều bảng cùng mở: chỗ mặc định tự tránh nút nổi và
 *                      bảng đang mở (`datViTriTuDong`), bảng vừa dùng nổi lên trên (`lenTren`).
 *   khổ hẹp            bảng trong DÒNG CHẢY dưới hình và điều khiển (CSS), thu gọn được, nút đầu bảng đủ lớn cho thao
 *                      tác chạm; không kéo — không tranh thao tác với orbit; không phủ lên hình hay nút phát.
 *
 * Vị trí và thứ tự lớp do HOST giữ (`BangNoiHost`, xưởng cấp): đóng rồi mở lại không mất chỗ người học đã kéo tới.
 * Không có host (trình phát đứng riêng) ⇒ bảng tự giữ trong lúc nó còn gắn. Hàm thuần giữ luật; component chỉ nối sự kiện.
 */
import {
  createContext, useCallback, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode,
} from "react";
import { IconChevronDown, IconClose, IconReset } from "../../../components/icons";

export interface ViTriBang { x: number; y: number }
export interface Khung { x: number; y: number; w: number; h: number }

/** Lề tối thiểu (px) giữa bảng và mép vùng mô phỏng. */
export const LE_BANG = 8;
/** Bước dời bằng phím mũi tên (px); giữ Shift ⇒ gấp bốn. */
export const BUOC_PHIM = 16;
/** Bước lệch bậc thang khi mọi chỗ mặc định đều bị chiếm. */
const BAC_THANG = 28;

/** Kẹp góc trên-trái của bảng cỡ `co` vào `khung` (toạ độ cùng hệ); bảng to hơn khung ⇒ dính lề trên-trái. */
export function kepBang(p: ViTriBang, co: { w: number; h: number }, khung: Khung): ViTriBang {
  const kep = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), Math.max(lo, hi));
  return {
    x: kep(p.x, khung.x + LE_BANG, khung.x + khung.w - co.w - LE_BANG),
    y: kep(p.y, khung.y + LE_BANG, khung.y + khung.h - co.h - LE_BANG),
  };
}

/** Vị trí mặc định khi không có vật cản: phía phải, sát trên vùng mô phỏng. */
export function viTriMacDinh(co: { w: number; h: number }, khung: Khung): ViTriBang {
  return kepBang({ x: khung.x + khung.w - co.w - 2 * LE_BANG, y: khung.y + 2 * LE_BANG }, co, khung);
}

const giao = (a: Khung, b: Khung) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

/**
 * Chỗ mặc định của một bảng vừa mở, tránh `vatCan` (nút nổi, bảng đang mở): thử cột PHẢI từ trên xuống (đỉnh khung,
 * rồi ngay dưới từng vật cản), rồi cột TRÁI như thế; chỗ đầu tiên bảng nằm trọn trong khung mà không giao vật cản nào
 * thắng. Hết chỗ ⇒ lệch bậc thang theo `thuTu` từ góc trên-phải, vẫn kẹp trong khung.
 */
export function datViTriTuDong(co: { w: number; h: number }, khung: Khung, vatCan: Khung[], thuTu = 0): ViTriBang {
  const ys = [khung.y + 2 * LE_BANG, ...vatCan.map((v) => v.y + v.h + LE_BANG)].sort((a, b) => a - b);
  for (const x of [khung.x + khung.w - co.w - 2 * LE_BANG, khung.x + 2 * LE_BANG]) {
    for (const y of ys) {
      const o = { x, y, w: co.w, h: co.h };
      if (x >= khung.x + LE_BANG && y + co.h <= khung.y + khung.h - LE_BANG && !vatCan.some((v) => giao(o, v))) {
        return { x, y };
      }
    }
  }
  const p = viTriMacDinh(co, khung);
  return kepBang({ x: p.x - thuTu * BAC_THANG, y: p.y + thuTu * BAC_THANG }, co, khung);
}

/** Phím mũi tên ⇒ vị trí mới (chưa kẹp); phím khác ⇒ `null`. */
export function dichBangPhim(p: ViTriBang, key: string, shift: boolean): ViTriBang | null {
  const d = BUOC_PHIM * (shift ? 4 : 1);
  const v: Record<string, [number, number]> = {
    ArrowLeft: [-d, 0], ArrowRight: [d, 0], ArrowUp: [0, -d], ArrowDown: [0, d],
  };
  return v[key] ? { x: p.x + v[key][0], y: p.y + v[key][1] } : null;
}

/** Bật/tắt bảng `id` trong tập bảng đang mở — không đụng bảng khác. */
export function batTatBang<T>(mo: ReadonlySet<T>, id: T): Set<T> {
  const ra = new Set(mo);
  if (!ra.delete(id)) ra.add(id);
  return ra;
}

/** Đưa bảng `id` lên trên cùng; thứ tự các bảng khác giữ nguyên. */
export function lenTren(thuTu: readonly string[], id: string): string[] {
  return [...thuTu.filter((x) => x !== id), id];
}

/** Vị trí đã đặt của một bảng: `nguoiDung` = người học kéo/dời tới (nút về mặc định có việc để làm). */
export interface ViTriLuu { p: ViTriBang; nguoiDung: boolean }

interface Host {
  viTri: Readonly<Record<string, ViTriLuu>>;
  dat: (panel: string, v: ViTriLuu | null) => void;
  thuTu: readonly string[];
  len: (panel: string) => void;
}

const HostCtx = createContext<Host | null>(null);

/** Host của mọi bảng nổi trong xưởng: nhớ vị trí qua đóng/mở và thứ tự lớp. Trạng thái TRÌNH BÀY thuần. */
export function BangNoiHost({ children }: { children: ReactNode }) {
  const [viTri, setViTri] = useState<Record<string, ViTriLuu>>({});
  const [thuTu, setThuTu] = useState<string[]>([]);
  const dat = useCallback((panel: string, v: ViTriLuu | null) => setViTri((s) => {
    const ra = { ...s };
    if (v) ra[panel] = v; else delete ra[panel];
    return ra;
  }), []);
  const len = useCallback((panel: string) => setThuTu((t) => (t.at(-1) === panel ? t : lenTren(t, panel))), []);
  const host = useMemo(() => ({ viTri, dat, thuTu, len }), [viTri, dat, thuTu, len]);
  return <HostCtx.Provider value={host}>{children}</HostCtx.Provider>;
}

/** Bảng có đang NỔI không — do CSS quyết theo khổ màn hình (khổ hẹp thì trong dòng chảy). */
const dangNoi = (el: HTMLElement | null) => !!el && getComputedStyle(el).position === "absolute";

/** Vùng mô phỏng (canvas) mà bảng kẹp vào: canvas của xưởng / trình phát chứa bảng. */
const timKhung = (el: HTMLElement | null) =>
  el?.closest(".geo3d-xuong, .geo3d-player")?.querySelector<HTMLElement>(".geo3d-canvas") ?? null;

export function BangNoi({
  panel, tieuDe, onDong, children, id, nhanDong, tieuDeLop = "", className = "", traTieuDiem,
}: {
  /** Khoá bảng (`data-panel`): giữ vị trí qua đóng/mở, thứ tự lớp, chọn bảng trong bộ đo. */
  panel: string;
  tieuDe: string;
  onDong: () => void;
  children: ReactNode;
  id?: string;
  /** Tên nút đóng; mặc định "Đóng ‹tiêu đề›" (ô soi: "Bỏ chọn" — đóng ô soi là bỏ chọn vật). */
  nhanDong?: string;
  tieuDeLop?: string;
  className?: string;
  /** Nơi trả tiêu điểm khi đóng bằng bàn phím (nút đã mở bảng). */
  traTieuDiem?: () => HTMLElement | null;
}) {
  const host = useContext(HostCtx);
  const [viTriRieng, setViTriRieng] = useState<ViTriLuu | null>(null);
  const luu = host ? host.viTri[panel] ?? null : viTriRieng;
  const datLuu = (v: ViTriLuu | null) => (host ? host.dat(panel, v) : setViTriRieng(v));
  const ref = useRef<HTMLElement>(null);
  const keo = useRef<{ id: number; cx: number; cy: number; x: number; y: number } | null>(null);
  const [thuGon, setThuGon] = useState(false);
  const [, setNhip] = useState(0);

  /** Hộp vùng mô phỏng theo hệ toạ độ của khối chứa bảng (`offsetParent`). */
  const heToaDo = () => (ref.current?.offsetParent as HTMLElement | null)?.getBoundingClientRect() ?? null;
  const khung = (): Khung | null => {
    const k = timKhung(ref.current)?.getBoundingClientRect();
    const b = heToaDo();
    return k && b ? { x: k.left - b.left, y: k.top - b.top, w: k.width, h: k.height } : null;
  };
  const co = () => ({ w: ref.current?.offsetWidth ?? 0, h: ref.current?.offsetHeight ?? 0 });
  /** Nút nổi và các bảng nổi KHÁC — cùng hệ toạ độ với bảng này. */
  const vatCan = (): Khung[] => {
    const b = heToaDo();
    const xuong = ref.current?.closest(".geo3d-xuong, .geo3d-player");
    if (!b || !xuong) return [];
    return [...xuong.querySelectorAll<HTMLElement>(".geo3d-noi, .geo3d-bang-noi")]
      .filter((e) => e !== ref.current && (e.classList.contains("geo3d-noi") || dangNoi(e)))
      .map((e) => e.getBoundingClientRect())
      .filter((r) => r.width > 0 && r.height > 0)
      .map((r) => ({ x: r.left - b.left, y: r.top - b.top, w: r.width, h: r.height }));
  };
  const hienTai = (): ViTriBang | null => {
    const k = khung();
    return k && luu ? kepBang(luu.p, co(), k) : null;
  };

  // Đổi cỡ cửa sổ / vùng mô phỏng ⇒ vẽ lại để kẹp lại (vị trí đã kéo vẫn giữ, chỉ hiển thị bị kẹp).
  useEffect(() => {
    const nhip = () => setNhip((n) => n + 1);
    window.addEventListener("resize", nhip);
    const k = timKhung(ref.current);
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(nhip) : null;
    if (ro && k) ro.observe(k);
    return () => { window.removeEventListener("resize", nhip); ro?.disconnect(); };
  }, []);
  // Mở ⇒ lên trên cùng; chưa có chỗ (lần đầu, hay vừa về mặc định) ⇒ đặt chỗ tự động MỘT lần, rồi giữ nguyên —
  // bảng không nhảy khi bảng khác mở/đóng. Khổ hẹp (trong dòng chảy) ⇒ cuộn tới bảng vừa mở.
  useLayoutEffect(() => {
    host?.len(panel);
    if (!dangNoi(ref.current)) ref.current?.scrollIntoView?.({ block: "nearest" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useLayoutEffect(() => {
    if (luu || !dangNoi(ref.current)) return;
    const k = khung();
    if (k) datLuu({ p: datViTriTuDong(co(), k, vatCan(), host ? host.thuTu.indexOf(panel) : 0), nguoiDung: false });
  });

  const noi = dangNoi(ref.current);
  const p = noi ? hienTai() : null;
  const lop = host ? 3 + Math.max(0, host.thuTu.indexOf(panel)) : undefined;
  return (
    <section
      ref={ref}
      id={id ?? `geo3d-bang-${panel}`}
      className={`geo3d-bang-noi ${className}${thuGon ? " la-thu-gon" : ""}`}
      aria-label={tieuDe}
      data-panel={panel}
      data-che-khung=""
      data-panel-x={p ? Math.round(p.x) : undefined}
      data-panel-y={p ? Math.round(p.y) : undefined}
      style={p ? { left: `${p.x}px`, top: `${p.y}px`, right: "auto", zIndex: lop }
        : noi ? { visibility: "hidden", zIndex: lop } : undefined}
      onPointerDownCapture={() => host?.len(panel)}
      onFocusCapture={() => host?.len(panel)}
      onKeyDown={(e) => {
        if (e.key === "Escape") { e.stopPropagation(); onDong(); traTieuDiem?.()?.focus(); }
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
          datLuu({ p: kepBang({ x: k.x + e.clientX - k.cx, y: k.y + e.clientY - k.cy }, co(), kh), nguoiDung: true });
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
          datLuu({ p: kepBang(moi, co(), kh), nguoiDung: true });
        }}
      >
        <h4 className={`geo3d-bang-noi-tieu ${tieuDeLop}`}>{tieuDe}</h4>
        <button type="button" className="geo3d-soi-dong geo3d-bang-noi-gon" aria-expanded={!thuGon}
                aria-label={thuGon ? "Mở rộng bảng" : "Thu gọn bảng"} onClick={() => setThuGon((x) => !x)}>
          <IconChevronDown />
        </button>
        <button type="button" className="geo3d-soi-dong geo3d-bang-noi-ve" aria-label="Về vị trí mặc định"
                onClick={() => datLuu(null)} disabled={!luu?.nguoiDung}>
          <IconReset />
        </button>
        {/* Tên riêng, không "Đóng" trơn: nhiều bảng cùng mở thì hai nút cùng tên là mơ hồ với trình đọc màn hình. */}
        <button type="button" className="geo3d-soi-dong geo3d-bang-noi-dong"
                aria-label={nhanDong ?? `Đóng ${tieuDe.toLowerCase()}`} onClick={onDong}>
          <IconClose />
        </button>
      </div>
      {!thuGon && <div className="geo3d-bang-noi-than">{children}</div>}
    </section>
  );
}
