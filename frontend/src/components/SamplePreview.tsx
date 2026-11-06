import type { ReactNode } from "react";

/**
 * Thumbnail SVG chuẩn Axo V2.7 (P4.3) — chuyển nguyên vẹn 11 renderer bài toán
 * (`PROBLEM_THUMBNAIL_RENDERERS`) và 4 renderer phân loại (`getCategoryThumbnailSVG`)
 * từ `axo-unified-ui-v2-7-composer-validation-divider-review.html` (dòng 12404–13699).
 */

export type PreviewKind = "geometry";

export function previewKindOf(_simId: string): PreviewKind {
  return "geometry";
}

const GEO_THUMB_PALETTE = {
  ink: "#1E293B",
  dashed: "#64748B",
  shellFill: "rgba(148, 163, 184, 0.11)",
  shellFillStrong: "rgba(148, 163, 184, 0.17)",
  terracotta: "#C85A32",
  terracottaFill: "rgba(200, 90, 50, 0.25)",
  teal: "#0F766E",
  tealFill: "rgba(15, 118, 110, 0.16)",
  cobalt: "#2563EB",
  amber: "#D97706",
  amberFill: "rgba(217, 119, 6, 0.18)",
  planeFill: "rgba(109, 40, 217, 0.07)",
  planeStroke: "rgba(109, 40, 217, 0.36)",
  planeLabel: "#6D28D9",
} as const;

function GeoPt({
  x,
  y,
  label,
  dx,
  dy,
  color,
  r,
}: {
  x: number;
  y: number;
  label?: string;
  dx?: number;
  dy?: number;
  color?: string;
  r?: number;
}) {
  const c = color || GEO_THUMB_PALETTE.ink;
  const rad = r || 2.3;
  const tx = x + (dx !== undefined ? dx : 0);
  const ty = y + (dy !== undefined ? dy : -5);
  return (
    <>
      <circle cx={x} cy={y} r={rad} fill={c} />
      {label ? (
        <text
          x={tx}
          y={ty}
          fontFamily="Plus Jakarta Sans, sans-serif"
          fontSize="11"
          fontWeight="700"
          fill={c}
          paintOrder="stroke"
          stroke="#f8f6f1"
          strokeWidth="2.4"
          strokeLinejoin="round"
          textAnchor="middle"
        >
          {label}
        </text>
      ) : null}
    </>
  );
}

function GeoRightAngle({
  vx,
  vy,
  ux,
  uy,
  wx,
  wy,
  size,
  color,
}: {
  vx: number;
  vy: number;
  ux: number;
  uy: number;
  wx: number;
  wy: number;
  size?: number;
  color?: string;
}) {
  const s = size || 6.5;
  const c = color || GEO_THUMB_PALETTE.teal;
  const uLen = Math.hypot(ux, uy) || 1;
  const wLen = Math.hypot(wx, wy) || 1;
  const u1x = (ux / uLen) * s;
  const u1y = (uy / uLen) * s;
  const w1x = (wx / wLen) * s;
  const w1y = (wy / wLen) * s;
  const p1x = (vx + u1x).toFixed(1);
  const p1y = (vy + u1y).toFixed(1);
  const p2x = (vx + u1x + w1x).toFixed(1);
  const p2y = (vy + u1y + w1y).toFixed(1);
  const p3x = (vx + w1x).toFixed(1);
  const p3y = (vy + w1y).toFixed(1);
  return (
    <polyline
      points={`${p1x},${p1y} ${p2x},${p2y} ${p3x},${p3y}`}
      fill="none"
      stroke={c}
      strokeWidth="1.25"
      strokeLinejoin="round"
    />
  );
}

function GeoMidTick({
  x1,
  y1,
  x2,
  y2,
  color,
}: {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color?: string;
}) {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  const nx = (-dy / len) * 3.2;
  const ny = (dx / len) * 3.2;
  return (
    <line
      x1={(mx - nx).toFixed(1)}
      y1={(my - ny).toFixed(1)}
      x2={(mx + nx).toFixed(1)}
      y2={(my + ny).toFixed(1)}
      stroke={color || GEO_THUMB_PALETTE.terracotta}
      strokeWidth="1.35"
    />
  );
}

const PROBLEM_THUMBNAIL_RENDERERS: Record<string, () => ReactNode> = {
  // 1. Hình chóp tam giác S.ABC với mặt cắt qua 3 trung điểm M, N, P
  "thiet-dien-chop": () => (
    <>
      <polygon points="88,13 30,80 82,97 148,76" fill={GEO_THUMB_PALETTE.shellFill} />
      <line x1="30" y1="80" x2="148" y2="76" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.2" strokeDasharray="4,3" />
      <polygon points="44,50 92,62 136,44 92,35" fill={GEO_THUMB_PALETTE.planeFill} stroke={GEO_THUMB_PALETTE.planeStroke} strokeWidth="0.95" />
      <polygon points="59,46.5 85,55 118,44.5" fill={GEO_THUMB_PALETTE.terracottaFill} />
      <line x1="59" y1="46.5" x2="118" y2="44.5" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.4" strokeDasharray="3.5,2.5" />
      <polyline points="59,46.5 85,55 118,44.5" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.8" strokeLinejoin="round" />
      <polyline points="30,80 82,97 148,76" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" strokeLinejoin="round" />
      <line x1="88" y1="13" x2="30" y2="80" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="88" y1="13" x2="82" y2="97" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="88" y1="13" x2="148" y2="76" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <GeoMidTick x1={88} y1={13} x2={59} y2={46.5} />
      <GeoMidTick x1={59} y1={46.5} x2={30} y2={80} />
      <GeoMidTick x1={88} y1={13} x2={118} y2={44.5} />
      <GeoMidTick x1={118} y1={44.5} x2={148} y2={76} />
      <GeoPt x={88} y={13} label="S" dx={0} dy={-4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={30} y={80} label="A" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={82} y={97} label="B" dx={0} dy={10} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={148} y={76} label="C" dx={8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={59} y={46.5} label="M" dx={-9} dy={-2} color={GEO_THUMB_PALETTE.terracotta} r={2.5} />
      <GeoPt x={85} y={55} label="N" dx={7} dy={9} color={GEO_THUMB_PALETTE.terracotta} r={2.5} />
      <GeoPt x={118} y={44.5} label="P" dx={9} dy={-2} color={GEO_THUMB_PALETTE.terracotta} r={2.5} />
    </>
  ),

  // 2. Hình chóp tứ giác đều S.ABCD với thiết diện tứ giác MNPQ
  "mat-cheo-sac": () => (
    <>
      <polygon points="90,12 28,76 70,96 150,80" fill={GEO_THUMB_PALETTE.shellFill} />
      <line x1="28" y1="76" x2="110" y2="60" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="4,3" />
      <line x1="110" y1="60" x2="150" y2="80" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="4,3" />
      <line x1="90" y1="12" x2="110" y2="60" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="4,3" />
      <line x1="28" y1="76" x2="150" y2="80" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="0.95" strokeDasharray="3,3" />
      <line x1="70" y1="96" x2="110" y2="60" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="0.95" strokeDasharray="3,3" />
      <line x1="90" y1="12" x2="90" y2="78" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.35" strokeDasharray="3,2.5" />
      <GeoRightAngle vx={90} vy={78} ux={0} uy={-1} wx={1} wy={0} size={5.5} color={GEO_THUMB_PALETTE.teal} />
      <polygon points="18,78 72,92 158,52 104,34" fill={GEO_THUMB_PALETTE.planeFill} stroke={GEO_THUMB_PALETTE.planeStroke} strokeWidth="0.9" />
      <polygon points="52,51 78,66 126,53 102,40" fill={GEO_THUMB_PALETTE.terracottaFill} />
      <polyline points="52,51 102,40 126,53" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.35" strokeDasharray="3.5,2.5" />
      <polyline points="52,51 78,66 126,53" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.8" strokeLinejoin="round" />
      <polyline points="28,76 70,96 150,80" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" strokeLinejoin="round" />
      <line x1="90" y1="12" x2="28" y2="76" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="90" y1="12" x2="70" y2="96" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="90" y1="12" x2="150" y2="80" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <GeoPt x={90} y={12} label="S" dx={0} dy={-3.5} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={28} y={76} label="A" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={70} y={96} label="B" dx={-2} dy={10} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={150} y={80} label="C" dx={8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={110} y={60} label="D" dx={7} dy={-3} color={GEO_THUMB_PALETTE.dashed} r={2.0} />
      <GeoPt x={52} y={51} label="M" dx={-9} dy={-2} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={78} y={66} label="N" dx={-6} dy={10} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={126} y={53} label="P" dx={9} dy={2} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={102} y={40} label="Q" dx={7} dy={-4} color={GEO_THUMB_PALETTE.terracotta} r={2.2} />
    </>
  ),

  // 3. Hình chóp S.ABC có cạnh bên SA ⊥ (ABC)
  "vuong-goc-chop": () => (
    <>
      <polygon points="44,16 44,78 96,96 148,72" fill={GEO_THUMB_PALETTE.shellFill} />
      <polygon points="44,78 96,96 148,72" fill="rgba(15, 118, 110, 0.08)" />
      <line x1="44" y1="78" x2="148" y2="72" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.2" strokeDasharray="4,3" />
      <line x1="44" y1="78" x2="120" y2="85" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.35" strokeDasharray="3.5,2.5" />
      <line x1="44" y1="16" x2="120" y2="85" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.65" />
      <GeoRightAngle vx={120} vy={85} ux={-76} uy={-7} wx={28} wy={-13} size={6} color={GEO_THUMB_PALETTE.terracotta} />
      <GeoRightAngle vx={44} vy={78} ux={0} uy={-62} wx={52} wy={18} size={7.5} color={GEO_THUMB_PALETTE.teal} />
      <GeoRightAngle vx={44} vy={78} ux={0} uy={-62} wx={104} wy={-6} size={6.5} color={GEO_THUMB_PALETTE.teal} />
      <polyline points="44,78 96,96 148,72" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.6" strokeLinejoin="round" />
      <line x1="44" y1="16" x2="96" y2="96" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="44" y1="16" x2="148" y2="72" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="44" y1="16" x2="44" y2="78" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="2.4" />
      <GeoPt x={44} y={16} label="S" dx={-9} dy={2} color={GEO_THUMB_PALETTE.teal} r={2.7} />
      <GeoPt x={44} y={78} label="A" dx={-9} dy={4} color={GEO_THUMB_PALETTE.teal} r={2.7} />
      <GeoPt x={96} y={96} label="B" dx={0} dy={10} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={148} y={72} label="C" dx={8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={120} y={85} label="M" dx={9} dy={6} color={GEO_THUMB_PALETTE.terracotta} r={2.3} />
      <text x="19" y="51" fontFamily="JetBrains Mono, monospace" fontSize="11" fontWeight="700" fill={GEO_THUMB_PALETTE.teal}>
        SA⊥
      </text>
    </>
  ),

  // 4. Mặt phẳng (α) đi qua điểm M và vuông góc với đường thẳng SA cho trước
  "mp-vuong-goc-duong": () => (
    <>
      <polygon points="74,14 28,84 90,96 148,74" fill={GEO_THUMB_PALETTE.shellFill} />
      <line x1="28" y1="84" x2="148" y2="74" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="4,3" />
      <polygon points="24,38 78,24 128,64 74,80" fill="rgba(109, 40, 217, 0.11)" stroke="#6D28D9" strokeWidth="1.2" />
      <polygon points="51,49 84,65 108,42" fill={GEO_THUMB_PALETTE.terracottaFill} />
      <line x1="51" y1="49" x2="108" y2="42" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.35" strokeDasharray="3.5,2.5" />
      <polyline points="51,49 84,65 108,42" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.75" strokeLinejoin="round" />
      <GeoRightAngle vx={51} vy={49} ux={23} uy={-35} wx={33} wy={16} size={6.8} color={GEO_THUMB_PALETTE.teal} />
      <GeoRightAngle vx={51} vy={49} ux={-23} uy={35} wx={57} wy={-7} size={6.2} color={GEO_THUMB_PALETTE.teal} />
      <polyline points="28,84 90,96 148,74" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.5" />
      <line x1="74" y1="14" x2="90" y2="96" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.5" />
      <line x1="74" y1="14" x2="148" y2="74" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.5" />
      <line x1="74" y1="14" x2="28" y2="84" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="2.2" />
      <GeoPt x={74} y={14} label="S" dx={0} dy={-4} color={GEO_THUMB_PALETTE.teal} r={2.5} />
      <GeoPt x={28} y={84} label="A" dx={-8} dy={4} color={GEO_THUMB_PALETTE.teal} r={2.5} />
      <GeoPt x={90} y={96} label="B" dx={0} dy={10} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={148} y={74} label="C" dx={8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={51} y={49} label="M" dx={-10} dy={-2} color={GEO_THUMB_PALETTE.terracotta} r={2.8} />
      <text x="116" y="62" fontFamily="Plus Jakarta Sans, sans-serif" fontStyle="italic" fontSize="11" fontWeight="700" fill="#6D28D9">
        (α)
      </text>
    </>
  ),

  // 5. Thể tích khối chóp và khoảng cách SH từ đỉnh S đến mặt đáy (ABC)
  "the-tich-chop": () => (
    <>
      <polygon points="88,13 28,78 84,97 148,76" fill={GEO_THUMB_PALETTE.shellFill} />
      <polygon points="28,78 84,97 148,76" fill={GEO_THUMB_PALETTE.amberFill} />
      <line x1="28" y1="78" x2="148" y2="76" stroke={GEO_THUMB_PALETTE.amber} strokeWidth="1.4" strokeDasharray="4,3" />
      <line x1="28" y1="78" x2="88" y2="83" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.1" strokeDasharray="3,2.5" />
      <line x1="88" y1="13" x2="88" y2="83" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="2.3" strokeDasharray="4,2.5" />
      <GeoRightAngle vx={88} vy={83} ux={0} uy={-70} wx={-60} wy={-5} size={6.8} color={GEO_THUMB_PALETTE.teal} />
      <GeoRightAngle vx={88} vy={83} ux={0} uy={-70} wx={60} wy={-7} size={6.8} color={GEO_THUMB_PALETTE.teal} />
      <polyline points="28,78 84,97 148,76" fill="none" stroke={GEO_THUMB_PALETTE.amber} strokeWidth="1.8" strokeLinejoin="round" />
      <line x1="88" y1="13" x2="28" y2="78" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="88" y1="13" x2="84" y2="97" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="88" y1="13" x2="148" y2="76" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <rect x="93" y="40" width="17" height="15" rx="3" fill="rgba(240,253,250,0.92)" stroke="rgba(15,118,110,0.35)" strokeWidth="0.9" />
      <text x="101.5" y="51" fontFamily="JetBrains Mono, monospace" fontSize="11" fontWeight="700" fill={GEO_THUMB_PALETTE.teal} textAnchor="middle">
        h
      </text>
      <text x="114" y="89" fontFamily="Plus Jakarta Sans, sans-serif" fontStyle="italic" fontSize="11" fontWeight="700" fill="#B45309">
        Sđáy
      </text>
      <GeoPt x={88} y={13} label="S" dx={0} dy={-4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={28} y={78} label="A" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={84} y={97} label="B" dx={-2} dy={10} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={148} y={76} label="C" dx={8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={88} y={83} label="H" dx={-8} dy={-3} color={GEO_THUMB_PALETTE.teal} r={2.5} />
    </>
  ),

  // 6. Mặt cầu S(O, R) cắt bởi mặt phẳng (α) theo đường tròn giao tuyến C(H, r)
  "cau-cat-mat-phang": () => (
    <>
      <polygon points="22,80 140,88 158,56 40,48" fill={GEO_THUMB_PALETTE.planeFill} stroke={GEO_THUMB_PALETTE.planeStroke} strokeWidth="1" />
      <circle cx="88" cy="49" r="37" fill={GEO_THUMB_PALETTE.shellFill} stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.6" />
      <path d="M 51 49 A 37 9.5 0 0 1 125 49" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1" strokeDasharray="3.5,3" />
      <path d="M 51 49 A 37 9.5 0 0 0 125 49" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1" opacity="0.65" />
      <ellipse cx="88" cy="68" rx="30" ry="8.5" fill={GEO_THUMB_PALETTE.terracottaFill} />
      <path d="M 58 68 A 30 8.5 0 0 1 118 68" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.35" strokeDasharray="3.5,2.5" />
      <path d="M 58 68 A 30 8.5 0 0 0 118 68" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.8" />
      <line x1="88" y1="49" x2="88" y2="68" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.8" />
      <line x1="88" y1="68" x2="118" y2="68" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.6" />
      <line x1="88" y1="49" x2="118" y2="68" stroke={GEO_THUMB_PALETTE.cobalt} strokeWidth="1.4" strokeDasharray="3,2" />
      <GeoRightAngle vx={88} vy={68} ux={0} uy={-19} wx={30} wy={0} size={5.2} color={GEO_THUMB_PALETTE.teal} />
      <GeoPt x={88} y={49} label="O" dx={-8} dy={2} color={GEO_THUMB_PALETTE.ink} r={2.5} />
      <GeoPt x={88} y={68} label="H" dx={-8} dy={5} color={GEO_THUMB_PALETTE.teal} r={2.5} />
      <GeoPt x={118} y={68} label="M" dx={8} dy={4} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <text
        x="103"
        y="65.5"
        fontFamily="JetBrains Mono, monospace"
        fontSize="11"
        fontWeight="700"
        fill={GEO_THUMB_PALETTE.terracotta}
        paintOrder="stroke"
        stroke="#f8f6f1"
        strokeWidth="2.4"
        strokeLinejoin="round"
      >
        r
      </text>
      <text x="142" y="84" fontFamily="Plus Jakarta Sans, sans-serif" fontStyle="italic" fontSize="11" fontWeight="700" fill="#6D28D9">
        (α)
      </text>
    </>
  ),

  // 7. Bán kính và cấu trúc khối cầu S(O, R)
  "cau-the-tich": () => (
    <>
      <circle cx="90" cy="55" r="39" fill={GEO_THUMB_PALETTE.shellFillStrong} stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.65" />
      <ellipse cx="90" cy="55" rx="39" ry="11.5" fill={GEO_THUMB_PALETTE.amberFill} />
      <path d="M 51 55 A 39 11.5 0 0 1 129 55" fill="none" stroke={GEO_THUMB_PALETTE.amber} strokeWidth="1.3" strokeDasharray="4,3" />
      <path d="M 51 55 A 39 11.5 0 0 0 129 55" fill="none" stroke={GEO_THUMB_PALETTE.amber} strokeWidth="1.75" />
      <path d="M 90 16 A 13 39 0 0 0 90 94" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.1" strokeDasharray="3.5,3" />
      <path d="M 90 16 A 13 39 0 0 1 90 94" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.25" opacity="0.7" />
      <line x1="90" y1="16" x2="90" y2="94" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.2" strokeDasharray="3,2.5" />
      <line x1="90" y1="55" x2="126" y2="40" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="2.1" />
      <text x="108" y="42" fontFamily="JetBrains Mono, monospace" fontSize="11" fontWeight="700" fill={GEO_THUMB_PALETTE.terracotta} textAnchor="middle">
        R
      </text>
      <GeoPt x={90} y={55} label="O" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} r={2.7} />
      <GeoPt x={126} y={40} label="A" dx={8} dy={-2} color={GEO_THUMB_PALETTE.terracotta} r={2.6} />
    </>
  ),

  // 8. Thiết diện vuông góc trục OO′ của hình trụ
  "tru-thiet-dien-tron": () => (
    <>
      <rect x="54" y="22" width="72" height="66" fill={GEO_THUMB_PALETTE.shellFill} />
      <polygon points="28,65 138,71 154,45 44,39" fill={GEO_THUMB_PALETTE.planeFill} stroke={GEO_THUMB_PALETTE.planeStroke} strokeWidth="0.95" />
      <ellipse cx="90" cy="22" rx="36" ry="9.5" fill={GEO_THUMB_PALETTE.shellFillStrong} stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <ellipse cx="90" cy="55" rx="36" ry="9.5" fill={GEO_THUMB_PALETTE.terracottaFill} />
      <path d="M 54 55 A 36 9.5 0 0 1 126 55" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.35" strokeDasharray="3.5,2.5" />
      <path d="M 54 55 A 36 9.5 0 0 0 126 55" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.8" />
      <path d="M 54 88 A 36 9.5 0 0 1 126 88" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="4,3" />
      <path d="M 54 88 A 36 9.5 0 0 0 126 88" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="54" y1="22" x2="54" y2="88" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="126" y1="22" x2="126" y2="88" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="90" y1="22" x2="90" y2="88" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.5" strokeDasharray="3.5,2.5" />
      <line x1="90" y1="55" x2="126" y2="55" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.65" />
      <GeoRightAngle vx={90} vy={55} ux={0} uy={-20} wx={20} wy={0} size={5.2} color={GEO_THUMB_PALETTE.teal} />
      <GeoPt x={90} y={22} label="O′" dx={-9} dy={-1} color={GEO_THUMB_PALETTE.ink} r={2.2} />
      <GeoPt x={90} y={55} label="H" dx={-8} dy={4} color={GEO_THUMB_PALETTE.teal} r={2.5} />
      <GeoPt x={126} y={55} label="M" dx={9} dy={3} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={90} y={88} label="O" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} r={2.2} />
    </>
  ),

  // 9. Hình trụ và quan hệ giữa đường sinh với hai mặt đáy song song
  "tru-truc-xien": () => (
    <>
      <rect x="52" y="22" width="76" height="66" fill={GEO_THUMB_PALETTE.shellFill} />
      <rect x="90" y="22" width="38" height="66" fill={GEO_THUMB_PALETTE.tealFill} />
      <ellipse cx="90" cy="22" rx="38" ry="10" fill={GEO_THUMB_PALETTE.amberFill} stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <ellipse cx="90" cy="88" rx="38" ry="10" fill={GEO_THUMB_PALETTE.amberFill} />
      <path d="M 52 88 A 38 10 0 0 1 128 88" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.2" strokeDasharray="4,3" />
      <path d="M 52 88 A 38 10 0 0 0 128 88" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="52" y1="22" x2="52" y2="88" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="90" y1="22" x2="90" y2="88" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.75" strokeDasharray="4,2.5" />
      <line x1="128" y1="22" x2="128" y2="88" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="2.4" />
      <line x1="90" y1="22" x2="128" y2="22" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.6" />
      <line x1="90" y1="88" x2="128" y2="88" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.6" />
      <GeoRightAngle vx={90} vy={22} ux={0} uy={18} wx={18} wy={0} size={5.5} color={GEO_THUMB_PALETTE.teal} />
      <GeoRightAngle vx={90} vy={88} ux={0} uy={-18} wx={18} wy={0} size={5.5} color={GEO_THUMB_PALETTE.teal} />
      <GeoRightAngle vx={128} vy={88} ux={0} uy={-18} wx={-18} wy={0} size={5.5} color={GEO_THUMB_PALETTE.terracotta} />
      <text x="137" y="58" fontFamily="JetBrains Mono, monospace" fontSize="11" fontWeight="700" fill={GEO_THUMB_PALETTE.terracotta}>
        l
      </text>
      <text x="109" y="84" fontFamily="JetBrains Mono, monospace" fontSize="11" fontWeight="700" fill={GEO_THUMB_PALETTE.teal} textAnchor="middle">
        R
      </text>
      <GeoPt x={90} y={22} label="O′" dx={-9} dy={2} color={GEO_THUMB_PALETTE.ink} r={2.3} />
      <GeoPt x={128} y={22} label="A′" dx={9} dy={2} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={90} y={88} label="O" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} r={2.3} />
      <GeoPt x={128} y={88} label="A" dx={8} dy={4} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
    </>
  ),

  // 10. Thiết diện qua trục SO của hình nón (Tam giác cân SAB)
  "non-thiet-dien-truc": () => (
    <>
      <polygon points="36,92 144,92 128,10 52,10" fill={GEO_THUMB_PALETTE.planeFill} stroke={GEO_THUMB_PALETTE.planeStroke} strokeWidth="0.9" />
      <polygon points="90,15 46,85 134,85" fill={GEO_THUMB_PALETTE.terracottaFill} />
      <path d="M 46 85 A 44 11 0 0 1 134 85" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.2" strokeDasharray="4,3" />
      <path d="M 46 85 A 44 11 0 0 0 134 85" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.6" />
      <line x1="46" y1="85" x2="134" y2="85" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.65" strokeDasharray="4,2.5" />
      <line x1="90" y1="15" x2="46" y2="85" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.9" />
      <line x1="90" y1="15" x2="134" y2="85" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.9" />
      <line x1="90" y1="15" x2="90" y2="85" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.5" strokeDasharray="3.5,2.5" />
      <GeoRightAngle vx={90} vy={85} ux={0} uy={-20} wx={20} wy={0} size={5.5} color={GEO_THUMB_PALETTE.teal} />
      <GeoPt x={90} y={15} label="S" dx={0} dy={-4} color={GEO_THUMB_PALETTE.ink} r={2.6} />
      <GeoPt x={46} y={85} label="A" dx={-8} dy={4} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={134} y={85} label="B" dx={8} dy={4} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={90} y={85} label="O" dx={-7} dy={7} color={GEO_THUMB_PALETTE.teal} r={2.4} />
    </>
  ),

  // 11. Đường sinh SA = l, đường cao SO = h và bán kính đáy OA = R trong hình nón
  "non-duong-sinh": () => (
    <>
      <polygon points="86,15 42,85 130,85" fill={GEO_THUMB_PALETTE.shellFill} />
      <polygon points="86,15 86,85 130,85" fill={GEO_THUMB_PALETTE.tealFill} />
      <path d="M 42 85 A 44 11 0 0 1 130 85" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.2" strokeDasharray="4,3" />
      <path d="M 42 85 A 44 11 0 0 0 130 85" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.6" />
      <line x1="86" y1="15" x2="42" y2="85" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.45" />
      <line x1="86" y1="15" x2="86" y2="85" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="2.1" strokeDasharray="4,2.5" />
      <line x1="86" y1="85" x2="130" y2="85" stroke={GEO_THUMB_PALETTE.cobalt} strokeWidth="2.0" />
      <line x1="86" y1="15" x2="130" y2="85" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="2.35" />
      <GeoRightAngle vx={86} vy={85} ux={0} uy={-20} wx={20} wy={0} size={6.2} color={GEO_THUMB_PALETTE.teal} />
      <text x="75" y="55" fontFamily="JetBrains Mono, monospace" fontSize="11" fontWeight="700" fill={GEO_THUMB_PALETTE.teal}>
        h
      </text>
      <text x="108" y="81" fontFamily="JetBrains Mono, monospace" fontSize="11" fontWeight="700" fill={GEO_THUMB_PALETTE.cobalt} textAnchor="middle">
        R
      </text>
      <text x="116" y="48" fontFamily="JetBrains Mono, monospace" fontSize="11" fontWeight="700" fill={GEO_THUMB_PALETTE.terracotta}>
        l
      </text>
      <GeoPt x={86} y={15} label="S" dx={0} dy={-4} color={GEO_THUMB_PALETTE.ink} r={2.6} />
      <GeoPt x={86} y={85} label="O" dx={-7} dy={5} color={GEO_THUMB_PALETTE.teal} r={2.5} />
      <GeoPt x={130} y={85} label="A" dx={8} dy={4} color={GEO_THUMB_PALETTE.terracotta} r={2.6} />
    </>
  ),
};

function renderCategoryFallback(category?: string): ReactNode {
  if (category === "Mặt cầu") {
    return (
      <svg viewBox="0 0 180 110" data-thumb-fallback="true" aria-hidden="true">
        <polygon points="24,78 142,86 158,56 42,48" fill="#4F46E5" fillOpacity="0.08" stroke="rgba(79,70,229,0.28)" strokeWidth="1" />
        <circle cx="90" cy="54" r="38" fill="rgba(148,163,184,0.12)" stroke="#1E293B" strokeWidth="1.6" />
        <ellipse cx="90" cy="54" rx="38" ry="10" fill="none" stroke="#64748B" strokeWidth="1" strokeDasharray="4,3" />
        <ellipse cx="90" cy="69" rx="31" ry="9" fill="#C85A32" fillOpacity="0.28" stroke="#C85A32" strokeWidth="1.7" />
        <line x1="90" y1="54" x2="90" y2="69" stroke="#0F766E" strokeWidth="1.6" />
        <line x1="90" y1="69" x2="121" y2="69" stroke="#C85A32" strokeWidth="1.5" strokeDasharray="3,2" />
        <circle cx="90" cy="54" r="2.6" fill="#1E293B" />
        <circle cx="90" cy="69" r="2.6" fill="#C85A32" />
      </svg>
    );
  }
  if (category === "Hình trụ") {
    return (
      <svg viewBox="0 0 180 110" data-thumb-fallback="true" aria-hidden="true">
        <rect x="52" y="24" width="76" height="62" fill="rgba(148,163,184,0.12)" />
        <ellipse cx="90" cy="24" rx="38" ry="10" fill="rgba(148,163,184,0.16)" stroke="#1E293B" strokeWidth="1.55" />
        <ellipse cx="90" cy="56" rx="38" ry="10" fill="#C85A32" fillOpacity="0.26" stroke="#C85A32" strokeWidth="1.65" />
        <path d="M 52 86 A 38 10 0 0 1 128 86" fill="none" stroke="#64748B" strokeWidth="1.15" strokeDasharray="4,3" />
        <path d="M 52 86 A 38 10 0 0 0 128 86" fill="none" stroke="#1E293B" strokeWidth="1.55" />
        <line x1="52" y1="24" x2="52" y2="86" stroke="#1E293B" strokeWidth="1.55" />
        <line x1="128" y1="24" x2="128" y2="86" stroke="#1E293B" strokeWidth="1.55" />
        <line x1="90" y1="24" x2="90" y2="86" stroke="#0F766E" strokeWidth="1.4" strokeDasharray="3,3" />
      </svg>
    );
  }
  if (category === "Hình nón") {
    return (
      <svg viewBox="0 0 180 110" data-thumb-fallback="true" aria-hidden="true">
        <polygon points="90,16 46,84 134,84" fill="#C85A32" fillOpacity="0.24" />
        <path d="M 46 84 A 44 11 0 0 1 134 84" fill="none" stroke="#64748B" strokeWidth="1.2" strokeDasharray="4,3" />
        <path d="M 46 84 A 44 11 0 0 0 134 84" fill="none" stroke="#1E293B" strokeWidth="1.6" />
        <line x1="90" y1="16" x2="46" y2="84" stroke="#1E293B" strokeWidth="1.65" />
        <line x1="90" y1="16" x2="134" y2="84" stroke="#1E293B" strokeWidth="1.65" />
        <line x1="90" y1="16" x2="90" y2="84" stroke="#0F766E" strokeWidth="1.5" strokeDasharray="3,2" />
        <line x1="46" y1="84" x2="134" y2="84" stroke="#C85A32" strokeWidth="1.5" strokeDasharray="4,3" />
        <circle cx="90" cy="16" r="2.8" fill="#1E293B" />
        <circle cx="90" cy="84" r="2.6" fill="#0F766E" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 180 110" data-thumb-fallback="true" aria-hidden="true">
      <polygon points="90,14 34,76 76,96 146,80" fill="rgba(100,116,139,0.10)" />
      <line x1="34" y1="76" x2="112" y2="60" stroke="#64748B" strokeWidth="1.2" strokeDasharray="4,3" />
      <line x1="112" y1="60" x2="146" y2="80" stroke="#64748B" strokeWidth="1.2" strokeDasharray="4,3" />
      <line x1="90" y1="14" x2="112" y2="60" stroke="#64748B" strokeWidth="1.2" strokeDasharray="4,3" />
      <polygon points="54,54 82,66 125,57 104,42" fill="#C85A32" fillOpacity="0.28" stroke="#C85A32" strokeWidth="1.6" />
      <line x1="90" y1="14" x2="88" y2="75" stroke="#0F766E" strokeWidth="1.4" strokeDasharray="3,2" />
      <polyline points="34,76 76,96 146,80" fill="none" stroke="#1E293B" strokeWidth="1.6" />
      <line x1="90" y1="14" x2="34" y2="76" stroke="#1E293B" strokeWidth="1.6" />
      <line x1="90" y1="14" x2="76" y2="96" stroke="#1E293B" strokeWidth="1.6" />
      <line x1="90" y1="14" x2="146" y2="80" stroke="#1E293B" strokeWidth="1.6" />
      <circle cx="90" cy="14" r="2.8" fill="#1E293B" />
    </svg>
  );
}

export function SamplePreview({
  sampleId,
  category,
}: {
  kind?: PreviewKind;
  sampleId?: string | null;
  category?: string;
}) {
  if (sampleId && PROBLEM_THUMBNAIL_RENDERERS[sampleId]) {
    return (
      <svg
        viewBox="0 0 180 110"
        data-thumb-id={sampleId}
        data-thumb-fallback="false"
        aria-hidden="true"
      >
        {PROBLEM_THUMBNAIL_RENDERERS[sampleId]()}
      </svg>
    );
  }
  return renderCategoryFallback(category);
}
