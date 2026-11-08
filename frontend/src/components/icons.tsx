/**
 * Bộ icon (M9-UX5 & Axo V2.7) — SVG, nét đậm bo tròn.
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

/* ── Thương hiệu Axo V2.7 ───────────────────────────────────────────────── */

const AxoMarkGeometry = () => (
  <g transform="translate(18.0 59.5)" fill="currentColor" fillRule="evenodd">
    <path
      fill="#FFFFFF"
      d="M 360,424.417 C 321.899,421.398 207.388,411.261 168.5,407.465 C 160.25,406.66 138.425,404.639 120,402.974 C 34.032,395.206 14.363,393.182 10.953,391.756 C 6.537,389.908 2.412,385.108 0.898,380.055 C -0.294,376.075 0.113,365.966 3.52,315 C 4.837,295.283 6.75,264.271 11.998,177.5 C 13.062,159.9 14.872,127.95 16.019,106.5 C 17.166,85.05 18.555,65.787 19.106,63.693 C 21.15,55.926 25.307,52.925 53.9,38.581 C 93.438,18.747 129.552,1.987 135.363,0.777 C 140.539,-0.3 179.318,2.781 327,16.004 C 350.925,18.146 394.575,21.945 424,24.446 C 453.425,26.947 479.478,29.461 481.895,30.032 C 492.374,32.507 495.48,37.638 496.403,54 C 497.635,75.837 501.972,155.59 503.5,184.5 C 504.343,200.45 505.914,228.575 506.993,247 C 508.071,265.425 509.44,289.632 510.035,300.793 C 511.466,327.633 511.365,327.991 498.16,343.198 C 488.187,354.683 447.888,402.13 436.12,416.242 C 427.58,426.483 424.36,428.034 411.934,427.893 C 406.745,427.833 383.375,426.269 360,424.417 Z"
    />
    <path d="M 360,424.417 C 321.899,421.398 207.388,411.261 168.5,407.465 C 160.25,406.66 138.425,404.639 120,402.974 C 34.032,395.206 14.363,393.182 10.953,391.756 C 6.537,389.908 2.412,385.108 0.898,380.055 C -0.294,376.075 0.113,365.966 3.52,315 C 4.837,295.283 6.75,264.271 11.998,177.5 C 13.062,159.9 14.872,127.95 16.019,106.5 C 17.166,85.05 18.555,65.787 19.106,63.693 C 21.15,55.926 25.307,52.925 53.9,38.581 C 93.438,18.747 129.552,1.987 135.363,0.777 C 140.539,-0.3 179.318,2.781 327,16.004 C 350.925,18.146 394.575,21.945 424,24.446 C 453.425,26.947 479.478,29.461 481.895,30.032 C 492.374,32.507 495.48,37.638 496.403,54 C 497.635,75.837 501.972,155.59 503.5,184.5 C 504.343,200.45 505.914,228.575 506.993,247 C 508.071,265.425 509.44,289.632 510.035,300.793 C 511.466,327.633 511.365,327.991 498.16,343.198 C 488.187,354.683 447.888,402.13 436.12,416.242 C 427.58,426.483 424.36,428.034 411.934,427.893 C 406.745,427.833 383.375,426.269 360,424.417 Z M 409,407 C 410.1,405.9 411,404.212 411,403.25 C 410.999,401.156 404.103,291.621 400.469,236 C 399.05,214.275 396.64,176.968 395.113,153.096 C 392.404,110.74 392.282,109.647 390.058,107.846 C 388.804,106.831 386.816,105.999 385.639,105.997 C 381.137,105.992 280.07,97.112 170,87.052 C 131.633,83.546 106.434,81.32 67.5,78 C 47.244,76.272 43.197,76.355 41.036,78.544 C 38.93,80.677 37.855,96.127 27.994,266 C 25.775,304.225 23.519,341.078 22.98,347.895 C 21.501,366.605 21.672,372.393 23.759,374.282 C 25.163,375.552 36.012,376.802 77.509,380.473 C 106.104,383.002 146.15,386.629 166.5,388.533 C 186.85,390.436 221.275,393.558 243,395.469 C 264.725,397.38 290.6,399.664 300.5,400.543 C 407.323,410.032 406.044,409.956 409,407 Z M 455.043,361.294 C 466.844,347.706 479.356,333.418 482.846,329.544 C 486.337,325.67 489.56,321.562 490.009,320.416 C 490.833,318.309 490.633,313.906 487.005,254.5 C 485.079,222.947 483.96,202.451 478.86,105.25 C 477.588,81.014 476.183,62 475.664,62 C 473.564,62 415.834,103.313 415.1,105.341 C 414.104,108.092 415.934,141.946 423.026,252 C 425.17,285.275 427.857,327.125 428.997,345 C 431.278,380.756 431.771,386 432.854,386 C 433.256,386 443.241,374.882 455.043,361.294 Z M 431.098,66.487 C 446.719,55.755 459.624,46.609 459.775,46.162 C 459.927,45.715 450.927,44.58 439.775,43.641 C 428.624,42.701 412.3,41.286 403.5,40.495 C 394.7,39.704 372.2,37.703 353.5,36.049 C 258.227,27.62 214.329,23.616 182.639,20.466 C 163.466,18.56 145.766,17 143.306,17 C 139.794,17 134.715,18.897 119.667,25.828 C 82.958,42.736 54.062,56.504 54.031,57.101 C 54.014,57.432 57.712,57.974 62.25,58.306 C 66.787,58.638 98.4,61.391 132.5,64.424 C 210.984,71.405 250.659,74.802 319.5,80.436 C 349.75,82.912 376.3,85.101 378.5,85.301 C 380.7,85.5 387.044,85.739 392.598,85.832 L 402.696,86 L 431.098,66.487 Z M 318.5,364.436 C 299.506,362.646 298.429,362.382 294.105,358.476 C 291.057,355.722 288.52,350.99 280.935,333.907 C 272.666,315.283 271.178,312.588 268.52,311.413 C 266.859,310.679 256.95,309.382 246.5,308.531 C 236.05,307.68 220.3,306.351 211.5,305.577 C 153.442,300.473 155.293,300.578 152.736,302.253 C 151.421,303.115 145.673,311.623 139.963,321.16 C 134.253,330.697 128.285,339.731 126.7,341.236 C 121.913,345.781 118.222,346.206 98.338,344.496 C 74.742,342.468 74.608,342.439 70.529,338.592 C 67.55,335.782 67,334.592 67,330.948 C 67,326.933 69.7,322.59 105.783,268.566 C 142.058,214.255 167.983,174.869 185.651,147.228 C 194.828,132.871 195.418,132.194 200.873,129.754 C 204.979,127.917 206.078,127.869 218.873,128.965 C 237.937,130.598 242.75,131.572 246.716,134.597 C 250.31,137.338 254.372,145.307 302.236,243.5 C 358.964,359.881 356.438,354.076 353.085,360.341 C 349.956,366.188 344.248,366.864 318.5,364.436 Z M 246.429,261.429 C 247.293,260.564 248,259.421 248,258.887 C 248,257.997 234.98,229.001 223.465,204.25 C 220.843,198.613 218.329,194 217.879,194 C 217.429,194 215.554,196.363 213.711,199.25 C 208.428,207.529 182.097,251.584 181.497,253.148 C 181.199,253.923 181.552,255.373 182.281,256.37 C 183.418,257.925 187.291,258.507 209.553,260.467 C 242.233,263.346 244.454,263.404 246.429,261.429 Z" />
  </g>
);

export const IconAxoLogo = ({ size = 22, className }: IconProps) => (
  <svg
    className={className ? `axo-logo-svg ${className}` : "axo-logo-svg"}
    width={size}
    height={size}
    viewBox="16 56 516 434"
    aria-hidden="true"
    focusable="false"
  >
    <AxoMarkGeometry />
  </svg>
);

export const IconAxoSidebarLogo = () => (
  <svg viewBox="0 0 547 547" role="img" aria-label="Axo logo">
    <AxoMarkGeometry />
  </svg>
);

export const IconHome = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 10l9-7 9 7v10a2 2 0 01-2 2H5a2 2 0 01-2-2V10z" />
    <path d="M9 21v-9h6v9" />
  </Svg>
);

export const IconLibrary = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3" y="4" width="7" height="7" rx="1.5" />
    <rect x="14" y="4" width="7" height="7" rx="1.5" />
    <rect x="3" y="15" width="7" height="7" rx="1.5" />
    <rect x="14" y="15" width="7" height="7" rx="1.5" />
  </Svg>
);

export const IconHistory = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3.5 2" />
  </Svg>
);

export const IconBell = (p: IconProps) => (
  <Svg {...p}>
    <path d="M18 8a6 6 0 00-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 01-3.46 0" />
  </Svg>
);

export const IconUser = (p: IconProps) => (
  <Svg {...p}>
    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </Svg>
);

export const IconUsers = (p: IconProps) => (
  <Svg {...p}>
    <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M22 21v-2a4 4 0 00-3-3.87" />
    <path d="M16 3.13a4 4 0 010 7.75" />
  </Svg>
);

export const IconLogout = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
    <path d="M16 17l5-5-5-5" />
    <path d="M21 12H9" />
  </Svg>
);

export const IconAlert = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v4.5M12 16h.01" />
  </Svg>
);

export const IconPlus = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 5v14M5 12h14" />
  </Svg>
);

export const IconEye = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
    <circle cx="12" cy="12" r="3" />
  </Svg>
);

export const IconEyeOff = (p: IconProps) => (
  <Svg {...p}>
    <path d="M17.94 17.94A10.07 10.07 0 0112 19c-6.5 0-10-7-10-7a18.45 18.45 0 015.06-5.94" />
    <path d="M9.9 4.24A9.12 9.12 0 0112 4c6.5 0 10 7 10 7a18.5 18.5 0 01-2.16 3.19" />
    <path d="M1 1l22 22" />
  </Svg>
);

export const IconSettings = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
  </Svg>
);

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

export const IconArrowRight = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Svg>
);

export const IconUpload = (p: IconProps) => (
  <Svg {...p}>
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
    <path d="M17 8l-5-5-5 5" />
    <path d="M12 3v12" />
  </Svg>
);

export const IconCamera = (p: IconProps) => (
  <Svg {...p}>
    <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
    <circle cx="12" cy="13" r="4" />
  </Svg>
);

export const IconSwitchCamera = (p: IconProps) => (
  <Svg {...p}>
    <path d="M20 11A8.1 8.1 0 004.5 9M4 5v4h4" />
    <path d="M4 13a8.1 8.1 0 0015.5 2m.5 4v-4h-4" />
  </Svg>
);

export const IconImage = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3" y="4" width="18" height="16" rx="2" />
    <circle cx="8.5" cy="9.5" r="1.5" />
    <path d="M21 15l-5-5L5 20" />
  </Svg>
);

export const IconFileDoc = (p: IconProps) => (
  <Svg {...p}>
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
    <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
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

/** Dự đoán bước tiếp theo — bóng đèn. Thay emoji 🔮. */
export const IconPredict = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 18h6M10 21h4" />
    <path d="M12 3a6 6 0 00-3.5 10.9V16h7v-2.1A6 6 0 0012 3z" />
  </Svg>
);

/** Đúng — dùng cho phán quyết dự đoán (thay ký tự ✓). */
export const IconCheck = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 12.5l5 5L20 6.5" />
  </Svg>
);

/** Sai — thay ký tự ✗. */
export const IconCross = (p: IconProps) => (
  <Svg {...p}>
    <path d="M18 6L6 18M6 6l12 12" />
  </Svg>
);

/** Không kết luận được (unsupported_to_verify) — thay ký tự •. */
export const IconInfo = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5M12 7.5v.01" />
  </Svg>
);

/** W17 · công tắc "Số đo" — thước kẻ chéo có vạch: số liệu đặt NGAY TRÊN hình. */
export const IconRuler = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3.5 15.5l12-12 5 5-12 12z" />
    <path d="M7.5 11.5l2 2M10.5 8.5l2 2M13.5 5.5l2 2" />
  </Svg>
);

/** W17 · công tắc "Kết quả" — lá cờ cắm đích: đáp số của đề. */
export const IconFlag = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 21V4" />
    <path d="M5 4h12l-2.5 4.5L17 13H5" />
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

export const IconTrash = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 6h18" />
    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
    <path d="M10 11v6M14 11v6" />
  </Svg>
);

export const IconZoomIn = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="M20 20l-3.5-3.5M11 8v6M8 11h6" />
  </Svg>
);

export const IconZoomOut = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="M20 20l-3.5-3.5M8 11h6" />
  </Svg>
);

export const IconFitContain = (p: IconProps) => (
  <Svg {...p}>
    <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3" />
    <rect x="7" y="7" width="10" height="10" rx="1.5" />
  </Svg>
);

export const IconFitCover = (p: IconProps) => (
  <Svg {...p}>
    <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
  </Svg>
);

export const IconCameraOff = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2 2l20 20" />
    <path d="M7 7H4a2 2 0 00-2 2v9a2 2 0 002 2h16" />
    <path d="M9.5 4h5L17 7h3a2 2 0 012 2v7.5" />
    <path d="M14.12 14.12a3.5 3.5 0 01-4.24-4.24" />
  </Svg>
);
