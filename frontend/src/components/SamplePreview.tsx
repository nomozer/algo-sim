import type { ReactNode } from "react";

/**
 * Thumbnail SVG chuẩn hóa của Axo — đồng bộ trực tiếp với 11 mô hình Scene3D đã kiểm chứng
 * (đỉnh, nhãn điểm, nét liền/nét đứt, mặt cắt, dấu góc vuông và tư thế nhìn).
 * Dùng chung cho cả Trang chủ (`HomeView`), Thư viện (`LibraryView`) và Lịch sử (`SessionCard`).
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
  planeFill: "rgba(109, 40, 217, 0.08)",
  planeStroke: "rgba(109, 40, 217, 0.38)",
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
          fontSize="10.5"
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

const PROBLEM_THUMBNAIL_RENDERERS: Record<string, () => ReactNode> = {
  // 1. Hình chóp tứ giác S.ABCD (SA ⊥ đáy) với thiết diện tứ giác MNPQ song song đáy
  "thiet-dien-chop": () => (
    <>
      <polygon points="62,13 28,86 112,95 146,75" fill={GEO_THUMB_PALETTE.shellFill} />
      <line x1="62" y1="13" x2="62" y2="66" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <line x1="62" y1="66" x2="28" y2="86" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <line x1="62" y1="66" x2="146" y2="75" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <polygon points="34,47 84,59 124,45 74,35" fill={GEO_THUMB_PALETTE.planeFill} stroke={GEO_THUMB_PALETTE.planeStroke} strokeWidth="0.95" />
      <polygon points="62,39.5 45,49.5 87,54 104,44" fill={GEO_THUMB_PALETTE.terracottaFill} />
      <polyline points="45,49.5 62,39.5 104,44" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.35" strokeDasharray="3.5,2.5" />
      <polyline points="45,49.5 87,54 104,44" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.85" strokeLinejoin="round" />
      <polyline points="28,86 112,95 146,75" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" strokeLinejoin="round" />
      <line x1="62" y1="13" x2="28" y2="86" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="62" y1="13" x2="112" y2="95" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="62" y1="13" x2="146" y2="75" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <GeoPt x={62} y={13} label="S" dx={0} dy={-4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={62} y={66} label="A" dx={7} dy={-3} color={GEO_THUMB_PALETTE.dashed} r={2.0} />
      <GeoPt x={28} y={86} label="B" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={112} y={95} label="C" dx={4} dy={10} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={146} y={75} label="D" dx={8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={62} y={39.5} label="M" dx={8} dy={-3} color={GEO_THUMB_PALETTE.terracotta} r={2.3} />
      <GeoPt x={45} y={49.5} label="N" dx={-9} dy={2} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={87} y={54} label="P" dx={3} dy={10} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={104} y={44} label="Q" dx={9} dy={-2} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <text x="129" y="44" fontFamily="Plus Jakarta Sans, sans-serif" fontStyle="italic" fontSize="10" fontWeight="700" fill={GEO_THUMB_PALETTE.planeLabel}>
        (α)
      </text>
    </>
  ),

  // 2. Hình chóp tứ giác S.ABCD với mặt chéo (SAC) qua S, A, C
  "mat-cheo-sac": () => (
    <>
      <polygon points="52,14 26,84 112,94 142,72" fill={GEO_THUMB_PALETTE.shellFill} />
      <line x1="52" y1="62" x2="26" y2="84" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <line x1="52" y1="62" x2="142" y2="72" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <polygon points="44,10 44,68 122,98 122,38" fill={GEO_THUMB_PALETTE.planeFill} stroke={GEO_THUMB_PALETTE.planeStroke} strokeWidth="0.9" />
      <polygon points="52,14 52,62 112,94" fill={GEO_THUMB_PALETTE.terracottaFill} />
      <line x1="52" y1="14" x2="52" y2="62" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.5" strokeDasharray="3.5,2.5" />
      <line x1="52" y1="62" x2="112" y2="94" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.55" strokeDasharray="3.5,2.5" />
      <line x1="52" y1="14" x2="112" y2="94" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="2.0" />
      <polyline points="26,84 112,94 142,72" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" strokeLinejoin="round" />
      <line x1="52" y1="14" x2="26" y2="84" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="52" y1="14" x2="142" y2="72" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <GeoPt x={52} y={14} label="S" dx={-8} dy={0} color={GEO_THUMB_PALETTE.terracotta} r={2.5} />
      <GeoPt x={52} y={62} label="A" dx={-8} dy={1} color={GEO_THUMB_PALETTE.terracotta} r={2.3} />
      <GeoPt x={26} y={84} label="B" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={112} y={94} label="C" dx={5} dy={9} color={GEO_THUMB_PALETTE.terracotta} r={2.5} />
      <GeoPt x={142} y={72} label="D" dx={8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <text x="115" y="34" fontFamily="Plus Jakarta Sans, sans-serif" fontStyle="italic" fontSize="9.5" fontWeight="700" fill={GEO_THUMB_PALETTE.planeLabel}>
        (SAC)
      </text>
    </>
  ),

  // 3. Hình chóp tứ giác S.ABCD có cạnh bên SA ⊥ (ABCD)
  "vuong-goc-chop": () => (
    <>
      <polygon points="54,14 26,86 114,95 142,73" fill={GEO_THUMB_PALETTE.shellFill} />
      <polygon points="54,64 26,86 114,95 142,73" fill="rgba(15, 118, 110, 0.09)" />
      <line x1="54" y1="64" x2="26" y2="86" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.2" strokeDasharray="3.5,2.5" />
      <line x1="54" y1="64" x2="142" y2="73" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.2" strokeDasharray="3.5,2.5" />
      <GeoRightAngle vx={54} vy={64} ux={0} uy={-50} wx={-28} wy={22} size={6.5} color={GEO_THUMB_PALETTE.teal} />
      <GeoRightAngle vx={54} vy={64} ux={0} uy={-50} wx={88} wy={9} size={6.5} color={GEO_THUMB_PALETTE.teal} />
      <line x1="54" y1="14" x2="54" y2="64" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="2.3" strokeDasharray="4,2.5" />
      <polyline points="26,86 114,95 142,73" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" strokeLinejoin="round" />
      <line x1="54" y1="14" x2="26" y2="86" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="54" y1="14" x2="114" y2="95" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="54" y1="14" x2="142" y2="73" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <GeoPt x={54} y={14} label="S" dx={-8} dy={0} color={GEO_THUMB_PALETTE.terracotta} r={2.6} />
      <GeoPt x={54} y={64} label="A" dx={-8} dy={-2} color={GEO_THUMB_PALETTE.teal} r={2.6} />
      <GeoPt x={26} y={86} label="B" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={114} y={95} label="C" dx={4} dy={9} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={142} y={73} label="D" dx={8} dy={4} color={GEO_THUMB_PALETTE.ink} />
    </>
  ),

  // 4. Hình chóp S.ABCD (SA ⊥ đáy) với mặt phẳng (α) qua B vuông góc với SC tại H (BH ⊥ SC)
  "mp-vuong-goc-duong": () => (
    <>
      <polygon points="74,13 56,77 108,89 126,65" fill={GEO_THUMB_PALETTE.shellFill} />
      <polygon points="40,81 96,91 142,61 86,53" fill="rgba(109, 40, 217, 0.10)" stroke="#6D28D9" strokeWidth="1.1" />
      <line x1="74" y1="13" x2="76" y2="54" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.35" strokeDasharray="3.5,2.5" />
      <line x1="76" y1="54" x2="56" y2="77" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <line x1="76" y1="54" x2="126" y2="65" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <line x1="56" y1="77" x2="126" y2="65" stroke="#6D28D9" strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <line x1="56" y1="77" x2="101" y2="75" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.95" strokeDasharray="3.5,2.5" />
      <GeoRightAngle vx={101} vy={75} ux={-27} uy={-62} wx={-45} wy={2} size={6.5} color={GEO_THUMB_PALETTE.teal} />
      <polyline points="56,77 108,89 126,65" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" strokeLinejoin="round" />
      <line x1="74" y1="13" x2="56" y2="77" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="74" y1="13" x2="126" y2="65" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="74" y1="13" x2="108" y2="89" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="2.1" />
      <GeoPt x={74} y={13} label="S" dx={-6} dy={-4} color={GEO_THUMB_PALETTE.ink} r={2.5} />
      <GeoPt x={76} y={54} label="A" dx={7} dy={-3} color={GEO_THUMB_PALETTE.dashed} r={2.1} />
      <GeoPt x={56} y={77} label="B" dx={-8} dy={6} color={GEO_THUMB_PALETTE.ink} r={2.4} />
      <GeoPt x={108} y={89} label="C" dx={5} dy={9} color={GEO_THUMB_PALETTE.ink} r={2.4} />
      <GeoPt x={126} y={65} label="D" dx={8} dy={3} color={GEO_THUMB_PALETTE.ink} r={2.3} />
      <GeoPt x={101} y={75} label="H" dx={9} dy={1} color={GEO_THUMB_PALETTE.teal} r={2.6} />
      <text x="136" y="75" fontFamily="Plus Jakarta Sans, sans-serif" fontStyle="italic" fontSize="10" fontWeight="700" fill="#6D28D9">
        (α)
      </text>
    </>
  ),

  // 5. Thể tích khối chóp tứ giác đều S.ABCD và đường cao SH ⊥ (ABCD) tại tâm H
  "the-tich-chop": () => (
    <>
      <polygon points="90,13 30,74 70,95 150,81" fill={GEO_THUMB_PALETTE.shellFill} />
      <polygon points="30,74 70,95 150,81 110,60" fill={GEO_THUMB_PALETTE.amberFill} />
      <line x1="30" y1="74" x2="110" y2="60" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <line x1="110" y1="60" x2="150" y2="81" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <line x1="90" y1="13" x2="110" y2="60" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.15" strokeDasharray="3.5,2.5" />
      <line x1="30" y1="74" x2="150" y2="81" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="0.95" strokeDasharray="3,2.5" />
      <line x1="70" y1="95" x2="110" y2="60" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="0.95" strokeDasharray="3,2.5" />
      <line x1="90" y1="13" x2="90" y2="77.5" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="2.2" strokeDasharray="4,2.5" />
      <GeoRightAngle vx={90} vy={77.5} ux={0} uy={-64} wx={60} wy={3.5} size={6.5} color={GEO_THUMB_PALETTE.teal} />
      <polyline points="30,74 70,95 150,81" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" strokeLinejoin="round" />
      <line x1="90" y1="13" x2="30" y2="74" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="90" y1="13" x2="70" y2="95" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="90" y1="13" x2="150" y2="81" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <GeoPt x={90} y={13} label="S" dx={0} dy={-4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={30} y={74} label="A" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={70} y={95} label="B" dx={-2} dy={10} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={150} y={81} label="C" dx={8} dy={4} color={GEO_THUMB_PALETTE.ink} />
      <GeoPt x={110} y={60} label="D" dx={7} dy={-3} color={GEO_THUMB_PALETTE.dashed} r={2.0} />
      <GeoPt x={90} y={77.5} label="H" dx={-8} dy={-2} color={GEO_THUMB_PALETTE.terracotta} r={2.5} />
    </>
  ),

  // 6. Mặt cầu S(I, R) cắt bởi mặt phẳng (α) theo đường tròn giao tuyến C(H, r) với điểm M trên vành
  "cau-cat-mat-phang": () => (
    <>
      <polygon points="22,80 140,88 158,56 40,48" fill={GEO_THUMB_PALETTE.planeFill} stroke={GEO_THUMB_PALETTE.planeStroke} strokeWidth="1" />
      <circle cx="88" cy="49" r="37" fill={GEO_THUMB_PALETTE.shellFill} stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.6" />
      <path d="M 51 49 A 37 9.5 0 0 1 125 49" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1" strokeDasharray="3.5,3" />
      <path d="M 51 49 A 37 9.5 0 0 0 125 49" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1" opacity="0.65" />
      <ellipse cx="88" cy="68" rx="30" ry="8.5" fill={GEO_THUMB_PALETTE.terracottaFill} />
      <path d="M 58 68 A 30 8.5 0 0 1 118 68" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.35" strokeDasharray="3.5,2.5" />
      <path d="M 58 68 A 30 8.5 0 0 0 118 68" fill="none" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.8" />
      <line x1="88" y1="49" x2="88" y2="68" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.8" strokeDasharray="3,2" />
      <line x1="88" y1="68" x2="118" y2="68" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.65" strokeDasharray="3,2" />
      <line x1="88" y1="49" x2="118" y2="68" stroke={GEO_THUMB_PALETTE.cobalt} strokeWidth="1.45" strokeDasharray="3,2" />
      <GeoRightAngle vx={88} vy={68} ux={0} uy={-19} wx={30} wy={0} size={5.2} color={GEO_THUMB_PALETTE.teal} />
      <GeoPt x={88} y={49} label="I" dx={-8} dy={2} color={GEO_THUMB_PALETTE.ink} r={2.5} />
      <GeoPt x={88} y={68} label="H" dx={-8} dy={5} color={GEO_THUMB_PALETTE.teal} r={2.5} />
      <GeoPt x={118} y={68} label="M" dx={8} dy={4} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <text x="142" y="84" fontFamily="Plus Jakarta Sans, sans-serif" fontStyle="italic" fontSize="10.5" fontWeight="700" fill="#6D28D9">
        (α)
      </text>
    </>
  ),

  // 7. Bán kính IA = R và cấu trúc khối cầu S(I, R)
  "cau-the-tich": () => (
    <>
      <circle cx="90" cy="55" r="39" fill={GEO_THUMB_PALETTE.shellFillStrong} stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.65" />
      <ellipse cx="90" cy="55" rx="39" ry="11.5" fill={GEO_THUMB_PALETTE.amberFill} />
      <path d="M 51 55 A 39 11.5 0 0 1 129 55" fill="none" stroke={GEO_THUMB_PALETTE.amber} strokeWidth="1.3" strokeDasharray="4,3" />
      <path d="M 51 55 A 39 11.5 0 0 0 129 55" fill="none" stroke={GEO_THUMB_PALETTE.amber} strokeWidth="1.75" />
      <path d="M 90 16 A 13 39 0 0 0 90 94" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.1" strokeDasharray="3.5,3" />
      <path d="M 90 16 A 13 39 0 0 1 90 94" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.25" opacity="0.7" />
      <line x1="90" y1="55" x2="126" y2="40" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="2.1" strokeDasharray="4,2.5" />
      <text x="108" y="42" fontFamily="JetBrains Mono, monospace" fontSize="10.5" fontWeight="700" fill={GEO_THUMB_PALETTE.terracotta} textAnchor="middle">
        R
      </text>
      <GeoPt x={90} y={55} label="I" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} r={2.7} />
      <GeoPt x={126} y={40} label="A" dx={8} dy={-2} color={GEO_THUMB_PALETTE.terracotta} r={2.6} />
    </>
  ),

  // 8. Thiết diện tròn qua trung điểm M vuông góc trục OO′ của hình trụ
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
      <GeoRightAngle vx={90} vy={55} ux={0} uy={-20} wx={20} wy={0} size={5.2} color={GEO_THUMB_PALETTE.teal} />
      <GeoPt x={90} y={22} label="O′" dx={-9} dy={-1} color={GEO_THUMB_PALETTE.ink} r={2.2} />
      <GeoPt x={90} y={55} label="M" dx={-9} dy={4} color={GEO_THUMB_PALETTE.terracotta} r={2.5} />
      <GeoPt x={90} y={88} label="O" dx={-8} dy={4} color={GEO_THUMB_PALETTE.ink} r={2.2} />
      <text x="142" y="66" fontFamily="Plus Jakarta Sans, sans-serif" fontStyle="italic" fontSize="10" fontWeight="700" fill={GEO_THUMB_PALETTE.planeLabel}>
        (α)
      </text>
    </>
  ),

  // 9. Hình trụ có trục OO′ và bán kính đáy OA (OO′ ⊥ OA tại O)
  "tru-truc-xien": () => (
    <>
      <polygon points="38,86 66,24 138,24 110,86" fill={GEO_THUMB_PALETTE.shellFill} />
      <ellipse cx="102" cy="24" rx="36" ry="9.5" fill={GEO_THUMB_PALETTE.shellFillStrong} stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <ellipse cx="74" cy="86" rx="36" ry="9.5" fill={GEO_THUMB_PALETTE.amberFill} />
      <path d="M 38 86 A 36 9.5 0 0 1 110 86" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.2" strokeDasharray="4,3" />
      <path d="M 38 86 A 36 9.5 0 0 0 110 86" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="38" y1="86" x2="66" y2="24" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="110" y1="86" x2="138" y2="24" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.55" />
      <line x1="74" y1="86" x2="102" y2="24" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.75" strokeDasharray="4,2.5" />
      <line x1="74" y1="86" x2="110" y2="86" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="2.1" strokeDasharray="4,2.5" />
      <GeoRightAngle vx={74} vy={86} ux={14} uy={-31} wx={20} wy={0} size={5.8} color={GEO_THUMB_PALETTE.teal} />
      <GeoPt x={102} y={24} label="O′" dx={9} dy={1} color={GEO_THUMB_PALETTE.ink} r={2.3} />
      <GeoPt x={74} y={86} label="O" dx={-9} dy={4} color={GEO_THUMB_PALETTE.ink} r={2.4} />
      <GeoPt x={110} y={86} label="A" dx={9} dy={4} color={GEO_THUMB_PALETTE.terracotta} r={2.5} />
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
      <line x1="90" y1="15" x2="46" y2="85" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.95" />
      <line x1="90" y1="15" x2="134" y2="85" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="1.95" />
      <line x1="90" y1="15" x2="90" y2="85" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="1.5" strokeDasharray="3.5,2.5" />
      <GeoRightAngle vx={90} vy={85} ux={0} uy={-20} wx={20} wy={0} size={5.5} color={GEO_THUMB_PALETTE.teal} />
      <GeoPt x={90} y={15} label="S" dx={0} dy={-4} color={GEO_THUMB_PALETTE.ink} r={2.6} />
      <GeoPt x={46} y={85} label="A" dx={-8} dy={4} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={134} y={85} label="B" dx={8} dy={4} color={GEO_THUMB_PALETTE.terracotta} r={2.4} />
      <GeoPt x={90} y={85} label="O" dx={-7} dy={7} color={GEO_THUMB_PALETTE.teal} r={2.4} />
      <text x="132" y="24" fontFamily="Plus Jakarta Sans, sans-serif" fontStyle="italic" fontSize="10" fontWeight="700" fill={GEO_THUMB_PALETTE.planeLabel}>
        (α)
      </text>
    </>
  ),

  // 11. Đường sinh SA, đường cao SO và bán kính đáy OA trong hình nón
  "non-duong-sinh": () => (
    <>
      <polygon points="86,15 42,85 130,85" fill={GEO_THUMB_PALETTE.shellFill} />
      <polygon points="86,15 86,85 130,85" fill={GEO_THUMB_PALETTE.tealFill} />
      <path d="M 42 85 A 44 11 0 0 1 130 85" fill="none" stroke={GEO_THUMB_PALETTE.dashed} strokeWidth="1.2" strokeDasharray="4,3" />
      <path d="M 42 85 A 44 11 0 0 0 130 85" fill="none" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.6" />
      <line x1="86" y1="15" x2="42" y2="85" stroke={GEO_THUMB_PALETTE.ink} strokeWidth="1.45" />
      <line x1="86" y1="15" x2="86" y2="85" stroke={GEO_THUMB_PALETTE.teal} strokeWidth="2.1" strokeDasharray="4,2.5" />
      <line x1="86" y1="85" x2="130" y2="85" stroke={GEO_THUMB_PALETTE.cobalt} strokeWidth="1.9" strokeDasharray="4,2.5" />
      <line x1="86" y1="15" x2="130" y2="85" stroke={GEO_THUMB_PALETTE.terracotta} strokeWidth="2.35" />
      <GeoRightAngle vx={86} vy={85} ux={0} uy={-20} wx={20} wy={0} size={6.2} color={GEO_THUMB_PALETTE.teal} />
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
