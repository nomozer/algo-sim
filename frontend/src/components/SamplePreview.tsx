/**
 * SamplePreview (M9-UX2) — preview TRỰC QUAN cho starter card.
 *
 * Thuần trình bày: SVG tĩnh, DỮ LIỆU AN TOÀN CỐ ĐỊNH — không chạy engine,
 * không đụng state, không fetch, không nhân bản logic domain (đây là "tranh
 * minh hoạ", không phải mô phỏng thứ hai). Kind suy từ ĐỊNH DANH simulation_id
 * hoặc metadata `preview` tường minh của mẫu — không bao giờ từ chuỗi tiêu đề.
 * Id lạ → fallback "generic" (icon node-edge trung tính) — không bao giờ ném.
 */

export type PreviewKind =
  | "algorithm-bars"
  | "search-range"
  | "sort-swap"
  | "binary-bits"
  | "network-path"
  | "logic-gate"
  | "web-structure"
  | "generic";

const KIND_BY_SIM_ID: Record<string, PreviewKind> = {
  "algorithm.find_max": "algorithm-bars",
  "algorithm.find_min": "algorithm-bars",
  "algorithm.sum_if": "algorithm-bars",
  "algorithm.count_if": "algorithm-bars",
  "algorithm.linear_search": "search-range",
  "algorithm.binary_search": "search-range",
  "algorithm.bubble_sort": "sort-swap",
  "algorithm.insertion_sort": "sort-swap",
  "binary.decimal_to_binary": "binary-bits",
  "network.packet_routing": "network-path",
  "logic.and_gate": "logic-gate",
};

export function previewKindOf(simId: string, explicit?: string): PreviewKind {
  if (explicit && isPreviewKind(explicit)) return explicit;
  return KIND_BY_SIM_ID[simId] ?? "generic";
}

function isPreviewKind(s: string): s is PreviewKind {
  return (
    s in
    {
      "algorithm-bars": 1,
      "search-range": 1,
      "sort-swap": 1,
      "binary-bits": 1,
      "network-path": 1,
      "logic-gate": 1,
      "web-structure": 1,
      generic: 1,
    }
  );
}

/* Dữ liệu minh hoạ TĨNH — chỉ để tranh đẹp, không phải sự thật engine. */
const BARS = [34, 22, 46, 16, 28];
const SORT_BARS = [18, 40, 28, 34, 46];

function Bars() {
  // cột cao nhất được tô nổi (max) — gợi cơ chế "giá trị đang thắng"
  const maxIdx = BARS.indexOf(Math.max(...BARS));
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      {BARS.map((h, i) => (
        <rect
          key={i}
          x={8 + i * 17}
          y={50 - h}
          width={12}
          height={h}
          rx={2}
          fill={i === maxIdx ? "var(--accent-green)" : "#cfe3f7"}
        />
      ))}
    </svg>
  );
}

function SearchRange() {
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      {[0, 1, 2, 3, 4, 5, 6].map((i) => (
        <rect
          key={i}
          x={5 + i * 13}
          y={20}
          width={10}
          height={16}
          rx={2}
          fill={i < 2 ? "var(--hairline)" : i === 4 ? "var(--primary)" : "#cfe3f7"}
        />
      ))}
      <path d="M 62 14 l -5 5 h 10 z" fill="var(--primary)" />
      <text x={9} y={48} fontSize={8} fill="var(--ink-faint)">
        trái
      </text>
      <text x={57} y={48} fontSize={8} fill="var(--primary)">
        giữa
      </text>
      <text x={80} y={48} fontSize={8} fill="var(--ink-faint)">
        phải
      </text>
    </svg>
  );
}

function SortSwap() {
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      {SORT_BARS.map((h, i) => (
        <rect
          key={i}
          x={8 + i * 17}
          y={50 - h}
          width={12}
          height={h}
          rx={2}
          fill={i === 1 || i === 2 ? "var(--accent-orange)" : i === 4 ? "var(--accent-green)" : "#cfe3f7"}
        />
      ))}
      {/* mũi tên đổi chỗ giữa cặp đang so sánh */}
      <path
        d="M 31 6 q 8 -6 17 0"
        fill="none"
        stroke="var(--accent-orange-deep)"
        strokeWidth={1.6}
        markerEnd="url(#swap-arr)"
      />
      <defs>
        <marker id="swap-arr" markerWidth="6" markerHeight="6" refX="4" refY="3" orient="auto">
          <path d="M0,0 L5,3 L0,6 z" fill="var(--accent-orange-deep)" />
        </marker>
      </defs>
    </svg>
  );
}

function BinaryBits() {
  const bits = ["1", "1", "0", "1"];
  const weights = ["8", "4", "2", "1"];
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      {bits.map((b, i) => (
        <g key={i}>
          <rect
            x={10 + i * 20}
            y={12}
            width={16}
            height={20}
            rx={3}
            fill={b === "1" ? "var(--primary)" : "#eef4fb"}
            stroke="var(--hairline)"
          />
          <text
            x={18 + i * 20}
            y={26}
            textAnchor="middle"
            fontSize={11}
            fontWeight={700}
            fill={b === "1" ? "#fff" : "var(--ink-faint)"}
          >
            {b}
          </text>
          <text x={18 + i * 20} y={44} textAnchor="middle" fontSize={8} fill="var(--ink-faint)">
            {weights[i]}
          </text>
        </g>
      ))}
    </svg>
  );
}

function NetworkPath() {
  const nodes = [
    { x: 12, y: 40 },
    { x: 38, y: 16 },
    { x: 62, y: 40 },
    { x: 86, y: 16 },
  ];
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      {nodes.slice(0, -1).map((n, i) => (
        <line
          key={i}
          x1={n.x}
          y1={n.y}
          x2={nodes[i + 1].x}
          y2={nodes[i + 1].y}
          stroke="var(--primary)"
          strokeWidth={2}
        />
      ))}
      {nodes.map((n, i) => (
        <circle
          key={i}
          cx={n.x}
          cy={n.y}
          r={6}
          fill="var(--surface)"
          stroke={i === 0 ? "var(--accent-sky)" : i === nodes.length - 1 ? "var(--accent-green)" : "var(--accent-purple)"}
          strokeWidth={2}
        />
      ))}
      <circle cx={50} cy={28} r={4} fill="var(--accent-pink)" stroke="#fff" strokeWidth={1.5} />
    </svg>
  );
}

function LogicGate() {
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      <circle cx={12} cy={18} r={5} fill="var(--accent-green)" />
      <circle cx={12} cy={38} r={5} fill="var(--hairline)" />
      <line x1={17} y1={18} x2={34} y2={22} stroke="var(--ink-faint)" strokeWidth={1.5} />
      <line x1={17} y1={38} x2={34} y2={34} stroke="var(--ink-faint)" strokeWidth={1.5} />
      <rect x={34} y={16} width={26} height={24} rx={5} fill="#eef4fb" stroke="var(--hairline)" />
      <text x={47} y={31} textAnchor="middle" fontSize={9} fontWeight={700} fill="var(--ink-secondary)">
        AND
      </text>
      <line x1={60} y1={28} x2={76} y2={28} stroke="var(--ink-faint)" strokeWidth={1.5} />
      <circle cx={83} cy={28} r={6} fill="#f3f0e9" stroke="var(--accent-orange)" strokeWidth={2} />
    </svg>
  );
}

function WebStructure() {
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      <rect x={14} y={8} width={68} height={40} rx={4} fill="var(--surface)" stroke="var(--hairline)" />
      <rect x={20} y={14} width={40} height={7} rx={2} fill="var(--primary)" opacity={0.85} />
      <rect x={20} y={27} width={56} height={4} rx={2} fill="var(--hairline)" />
      <rect x={20} y={35} width={48} height={4} rx={2} fill="var(--hairline)" />
    </svg>
  );
}

function GenericIcon() {
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      <circle cx={30} cy={20} r={7} fill="var(--surface)" stroke="var(--accent-teal)" strokeWidth={2} />
      <circle cx={66} cy={36} r={7} fill="var(--surface)" stroke="var(--accent-purple)" strokeWidth={2} />
      <line x1={36} y1={24} x2={60} y2={33} stroke="var(--ink-faint)" strokeWidth={1.5} />
    </svg>
  );
}

const RENDERERS: Record<PreviewKind, () => JSX.Element> = {
  "algorithm-bars": Bars,
  "search-range": SearchRange,
  "sort-swap": SortSwap,
  "binary-bits": BinaryBits,
  "network-path": NetworkPath,
  "logic-gate": LogicGate,
  "web-structure": WebStructure,
  generic: GenericIcon,
};

export function SamplePreview({ kind }: { kind: PreviewKind }) {
  const Render = RENDERERS[kind] ?? GenericIcon;
  return (
    <span className="sample-preview">
      <Render />
    </span>
  );
}
