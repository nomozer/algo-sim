/**
 * Bộ icon (M9-UX5) — SVG, nét đậm bo tròn.
 *
 * VÌ SAO CÓ FILE NÀY: trước đây UI trộn emoji (📎 🧪), ký tự hình khối
 * (⏮ ◀ ▶ ⏭ ↺ ▸ ✕) và ký tự hiếm (`◧` U+25E7 — font Windows KHÔNG có glyph nên
 * hiện ra ô vuông rỗng ngay trên header). Mỗi thứ một nét, một cỡ, một màu, và
 * cái nào hiển thị được là tuỳ máy.
 *
 * LUẬT: icon trong UI phải là component ở file này. KHÔNG dùng emoji/ký tự
 * Unicode làm icon nữa. Tất cả cùng khung 24×24, cùng `stroke-width` 2.4, đầu và
 * góc bo tròn; màu lấy `currentColor` nên tự ăn theo màu chữ của nút chứa nó.
 */

type IconProps = { size?: number; className?: string };

function Svg({ size = 16, className, children }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      className={className ? `icon ${className}` : "icon"}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

/* ── Ô nhập ─────────────────────────────────────────────────────────────── */

/**
 * Tải tệp — KẸP GIẤY, không phải dấu `+`.
 * `+` là icon của "thêm gì đó / mở menu" (Manus dùng nó cho một menu nhiều mục).
 * Nút này chỉ làm ĐÚNG MỘT việc: gửi tệp đề. Kẹp giấy nói đúng việc đó.
 */
export const IconAttach = (p: IconProps) => (
  <Svg {...p}>
    <path d="M21 11l-8.5 8.5a5 5 0 01-7-7L14 4a3.5 3.5 0 015 5l-8.5 8.5a1.5 1.5 0 01-2-2L16 8" />
  </Svg>
);

export const IconSend = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 19V5M6 11l6-6 6 6" />
  </Svg>
);

/* ── Điều khiển timeline ────────────────────────────────────────────────── */

export const IconToStart = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 6v12M18 6L9 12l9 6V6z" />
  </Svg>
);

export const IconPrev = (p: IconProps) => (
  <Svg {...p}>
    <path d="M15 6l-6 6 6 6" />
  </Svg>
);

export const IconNext = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 6l6 6-6 6" />
  </Svg>
);

export const IconToEnd = (p: IconProps) => (
  <Svg {...p}>
    <path d="M18 6v12M6 6l9 6-9 6V6z" />
  </Svg>
);

export const IconPlay = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7 5l11 7-11 7V5z" />
  </Svg>
);

export const IconPause = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 5v14M15 5v14" />
  </Svg>
);

export const IconReset = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 12a9 9 0 109-9 9 9 0 00-6.36 2.64L3 8" />
    <path d="M3 3v5h5" />
  </Svg>
);

/* ── Điều hướng & thao tác ──────────────────────────────────────────────── */

export const IconBack = (p: IconProps) => (
  <Svg {...p}>
    <path d="M19 12H5M11 18l-6-6 6-6" />
  </Svg>
);

export const IconChevronRight = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 6l6 6-6 6" />
  </Svg>
);

export const IconChevronDown = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 9l6 6 6-6" />
  </Svg>
);

export const IconClose = (p: IconProps) => (
  <Svg {...p}>
    <path d="M18 6L6 18M6 6l12 12" />
  </Svg>
);

export const IconSearch = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="M20 20l-3.5-3.5" />
  </Svg>
);

/* ── Ngữ nghĩa của sản phẩm ─────────────────────────────────────────────── */

/** Hỏi AI — bong bóng hội thoại. AI là TRỢ THỦ, không phải xương sống (R0). */
export const IconAsk = (p: IconProps) => (
  <Svg {...p}>
    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
  </Svg>
);

/** Nhánh thử nghiệm what-if — ống nghiệm. */
export const IconExperiment = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 3h6M10 3v6L5 19a2 2 0 002 2h10a2 2 0 002-2l-5-10V3" />
  </Svg>
);

/**
 * Bật/tắt panel. Thay `◧`/`◨` (U+25E7/25E8) — hai ký tự này không có glyph trong
 * font hệ thống Windows nên hiện ra Ô VUÔNG RỖNG (tofu) ngay trên header.
 */
export const IconPanel = ({ side, ...p }: IconProps & { side: "left" | "right" }) => (
  <Svg {...p}>
    <rect x="3" y="4" width="18" height="16" rx="2" />
    <path d={side === "left" ? "M9 4v16" : "M15 4v16"} />
  </Svg>
);
