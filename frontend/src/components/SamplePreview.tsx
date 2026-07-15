/**
 * SamplePreview (M9-UX2 · mở rộng M9-UX3) — preview TRỰC QUAN cho starter card.
 *
 * Thuần trình bày: SVG tĩnh, DỮ LIỆU AN TOÀN CỐ ĐỊNH — không chạy engine,
 * không đụng state, không fetch, không nhân bản logic domain (đây là "tranh
 * minh hoạ", không phải mô phỏng thứ hai). Kind suy từ ĐỊNH DANH simulation_id
 * hoặc metadata `preview` tường minh của mẫu — không bao giờ từ chuỗi tiêu đề.
 * Id lạ → fallback "generic" (icon node-edge trung tính) — không bao giờ ném.
 *
 * M9-UX3 — LUẬT: MỘT TRANH = MỘT CƠ CHẾ = MỘT BÀI.
 * Tranh phải vẽ đúng cơ chế ẩn của CHÍNH bài đó (nguyên tắc sư phạm #6,
 * COVERAGE §2.6) — cùng cơ chế mà `decision.ts` (M9-S1) đem ra hỏi học sinh.
 * Trước M9-UX3, 8 bài thuật toán chen vào 3 tranh, và hai trong số đó DẠY SAI:
 * linear_search mượn tranh trái/giữa/phải của binary_search (tìm tuần tự không
 * có mid), insertion_sort mượn mũi tên ĐỔI CHỖ của bubble_sort (chèn là DỜI).
 * Khoá bằng test "không hai bài thuật toán nào dùng chung một tranh".
 */

export type PreviewKind =
  | "algorithm-bars"
  | "bars-min"
  | "sum-threshold"
  | "count-threshold"
  | "linear-scan"
  | "search-range"
  | "sort-swap"
  | "insertion-lift"
  | "binary-bits"
  | "network-path"
  | "network-encapsulation"
  | "logic-gate"
  | "web-structure"
  | "generic";

const KIND_BY_SIM_ID: Record<string, PreviewKind> = {
  "algorithm.find_max": "algorithm-bars",
  "algorithm.find_min": "bars-min",
  "algorithm.sum_if": "sum-threshold",
  "algorithm.count_if": "count-threshold",
  "algorithm.linear_search": "linear-scan",
  "algorithm.binary_search": "search-range",
  "algorithm.bubble_sort": "sort-swap",
  "algorithm.insertion_sort": "insertion-lift",
  "binary.decimal_to_binary": "binary-bits",
  "network.packet_routing": "network-path",
  "network.protocol_encapsulation": "network-encapsulation",
  "logic.and_gate": "logic-gate",
};

export function previewKindOf(simId: string, explicit?: string): PreviewKind {
  if (explicit && isPreviewKind(explicit)) return explicit;
  return KIND_BY_SIM_ID[simId] ?? "generic";
}

function isPreviewKind(s: string): s is PreviewKind {
  return s in RENDERERS;
}

/* Dữ liệu minh hoạ TĨNH — chỉ để tranh đẹp, không phải sự thật engine. */
const BARS = [34, 22, 46, 16, 28];
const SORT_BARS = [18, 40, 28, 34, 46];
/** Cột cho cảnh "có ngưỡng": 3 cột vượt ngưỡng, 2 cột dưới. */
const THRESHOLD_BARS = [30, 16, 38, 12, 28];
const THRESHOLD_Y = 24; // y của đường ngưỡng trong viewBox 0 0 96 56

function Bars() {
  // cột CAO NHẤT tô xanh — cơ chế find_max: "giá trị đang thắng"
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

function BarsMin() {
  // cột THẤP NHẤT tô tím — cùng bố cục Bars, khác ĐÍCH. Phân biệt tức thì.
  const minIdx = BARS.indexOf(Math.min(...BARS));
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
          fill={i === minIdx ? "var(--accent-purple)" : "#cfe3f7"}
        />
      ))}
      <path d="M 55 30 l -4 5 h 8 z" fill="var(--accent-purple)" />
    </svg>
  );
}

/** Cột + đường ngưỡng nét đứt — nền chung của sum_if và count_if. */
function ThresholdBars({ fill }: { fill: string }) {
  return (
    <>
      <line
        x1={4}
        y1={THRESHOLD_Y}
        x2={92}
        y2={THRESHOLD_Y}
        stroke="var(--accent-orange)"
        strokeWidth={1.2}
        strokeDasharray="3 2"
      />
      {THRESHOLD_BARS.map((h, i) => (
        <rect
          key={i}
          x={8 + i * 17}
          y={46 - h}
          width={12}
          height={h}
          rx={2}
          fill={46 - h < THRESHOLD_Y ? fill : "var(--hairline)"}
        />
      ))}
    </>
  );
}

function SumThreshold() {
  // cơ chế sum_if: chỉ cột VƯỢT NGƯỠNG mới được CỘNG DỒN vào tổng.
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      <ThresholdBars fill="var(--accent-green)" />
      <rect x={58} y={0} width={36} height={13} rx={3} fill="var(--accent-green)" />
      <text x={76} y={9.5} textAnchor="middle" fontSize={9} fontWeight={700} fill="#fff">
        Σ 96
      </text>
    </svg>
  );
}

function CountThreshold() {
  // cơ chế count_if: cùng ngưỡng, nhưng ĐẾM chứ không cộng — đây đúng là chỗ
  // học sinh hay lẫn sum với count, nên hai tranh phải khác nhau thấy được.
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      <ThresholdBars fill="var(--primary)" />
      <circle cx={80} cy={7} r={7} fill="var(--primary)" />
      <text x={80} y={10.5} textAnchor="middle" fontSize={9} fontWeight={700} fill="#fff">
        3
      </text>
    </svg>
  );
}

function LinearScan() {
  // cơ chế linear_search: QUÉT TRÁI → PHẢI. Ô đã xem xám đi, kính lúp dừng ở ô
  // đang xét. TUYỆT ĐỐI không trái/giữa/phải — tìm tuần tự không có mid.
  const scanned = 3; // 3 ô đã xem, ô thứ 4 (idx 3) đang xét
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      {[0, 1, 2, 3, 4].map((i) => (
        <rect
          key={i}
          x={6 + i * 17}
          y={i === scanned ? 18 : 20}
          width={13}
          height={i === scanned ? 21 : 17}
          rx={2}
          fill={i < scanned ? "#eef1f4" : i === scanned ? "var(--primary)" : "#cfe3f7"}
          stroke={i < scanned ? "var(--hairline)" : "none"}
        />
      ))}
      {/* mũi tên tiến trình quét, từ trái tới ô đang xét */}
      <path d="M 12 46 h 46" stroke="var(--ink-faint)" strokeWidth={1.2} strokeDasharray="2 2" />
      <path d="M 62 46 l -5 -3 v 6 z" fill="var(--ink-faint)" />
      {/* kính lúp trên ô đang xét */}
      <circle cx={62} cy={9} r={4.5} fill="none" stroke="var(--primary)" strokeWidth={1.8} />
      <line x1={65} y1={12} x2={67.5} y2={14.5} stroke="var(--primary)" strokeWidth={1.8} />
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
  // cơ chế bubble_sort: ĐỔI CHỖ cặp kề nhau — hai mũi tên vòng NGƯỢC nhau,
  // hai cột cùng được tô cam (cả hai cùng di chuyển).
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
          fill={
            i === 1 || i === 2
              ? "var(--accent-orange)"
              : i === 4
                ? "var(--accent-green)"
                : "#cfe3f7"
          }
        />
      ))}
      {/* hai cung ngược chiều = hoán vị tại chỗ của cặp đang so sánh */}
      <path
        d="M 31 6 q 8 -7 17 0"
        fill="none"
        stroke="var(--accent-orange-deep)"
        strokeWidth={1.5}
        markerEnd="url(#swap-arr)"
      />
      <path
        d="M 48 7 q -8 7 -17 0"
        fill="none"
        stroke="var(--accent-orange-deep)"
        strokeWidth={1.5}
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

function InsertionLift() {
  // cơ chế insertion_sort: NHẤC phần tử ra khỏi hàng rồi DỜI vào đúng chỗ.
  // KHÔNG phải đổi chỗ — decision.ts hỏi "dời?", không hỏi "đổi chỗ?".
  const rest = [
    { x: 8, h: 16 },
    { x: 25, h: 24 },
    { x: 59, h: 32 },
    { x: 76, h: 42 },
  ];
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      {rest.map((b, i) => (
        <rect key={i} x={b.x} y={50 - b.h} width={12} height={b.h} rx={2} fill="#cfe3f7" />
      ))}
      {/* chỗ trống nó vừa rời khỏi */}
      <rect
        x={42}
        y={30}
        width={12}
        height={20}
        rx={2}
        fill="none"
        stroke="var(--hairline)"
        strokeDasharray="2 2"
      />
      {/* phần tử đang được cầm trên tay */}
      <rect x={42} y={2} width={12} height={20} rx={2} fill="var(--accent-orange)" />
      {/* dời xuống chỗ chèn */}
      <path
        d="M 48 24 v 4"
        stroke="var(--accent-orange-deep)"
        strokeWidth={1.6}
        markerEnd="url(#lift-arr)"
      />
      <defs>
        <marker id="lift-arr" markerWidth="6" markerHeight="6" refX="4" refY="3" orient="auto">
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

/**
 * network.protocol_encapsulation — cơ chế: PDU LỚN DẦN khi đóng gói qua các tầng.
 * Các đoạn rộng dần (payload → +TCP → +IP → +LINK/FCS): payload xanh lá, header
 * xanh da trời, trailer cam. Đúng cơ chế bài dạy (một tranh = một cơ chế, #6).
 */
function NetworkEncap() {
  return (
    <svg viewBox="0 0 96 56" className="sample-preview-svg" aria-hidden="true">
      <rect x={8} y={8} width={34} height={8} rx={2} fill="var(--accent-green)" />
      <rect x={8} y={20} width={48} height={8} rx={2} fill="var(--accent-sky)" />
      <rect x={8} y={32} width={62} height={8} rx={2} fill="var(--accent-sky)" opacity={0.6} />
      <rect x={8} y={44} width={80} height={8} rx={2} fill="var(--accent-orange)" opacity={0.7} />
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
  "bars-min": BarsMin,
  "sum-threshold": SumThreshold,
  "count-threshold": CountThreshold,
  "linear-scan": LinearScan,
  "search-range": SearchRange,
  "sort-swap": SortSwap,
  "insertion-lift": InsertionLift,
  "binary-bits": BinaryBits,
  "network-path": NetworkPath,
  "network-encapsulation": NetworkEncap,
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
