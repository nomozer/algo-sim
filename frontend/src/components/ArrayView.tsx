import { useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import type { Step } from "../core/types";
import { fmt } from "../core/trace-builder";
import type { LegendItem } from "./StageLegend";

/**
 * Renderer 2D (SVG) cho dữ liệu dạng dãy — vẽ thuần túy theo
 * snapshot + events của bước hiện tại (R3.2: cấm suy diễn logic thuật toán).
 * - Cột được key theo snapshot.ids → đổi chỗ/dời là cột TRƯỢT sang vị trí mới
 *   (CSS transition trên transform), không nhảy tức thì.
 * - Con trỏ tam giác chỉ vào các cột đang tham gia sự kiện của bước.
 * - Kéo thả what-if (R3.3): kéo một cột thả lên cột khác → onSwap(i, j).
 */

const COL_W = 56;
const COL_GAP = 14;
const CHART_H = 190;
const TOP_PAD = 26;
const BOTTOM_PAD = 52;

/* ── W4B-2A — BỐ CỤC THÍCH ỨNG THEO BỀ RỘNG KHẢ DỤNG ───────────────────────
 *
 * Trước đây `COL_W`/`COL_GAP` là hằng số, nên bề rộng hình vẽ chỉ phụ thuộc SỐ
 * phần tử: 7 cột luôn ra 504px, kể cả trong sân khấu 1306px. Đo được trên toàn
 * danh mục (W4B-2A baseline): đóng panel Quan sát cấp thêm 316px bề rộng, hình
 * vẽ lớn thêm **0px** — chỗ dư thành khoảng trắng.
 *
 * Cách chữa KHÔNG phải kéo giãn SVG. `viewBox` vẫn bằng đúng bề rộng hiển thị
 * nên `scale ≈ 1` giữ nguyên — chữ và nét không phình. Thay vào đó **tính lại
 * bố cục nội tại**: cột và khe rộng ra cho tới một TRẦN NGỮ NGHĨA, rồi dừng.
 *
 * Vì sao có trần: bảy cột trải kín 1300px không dạy thêm điều gì, chỉ làm mắt
 * phải quét xa hơn giữa hai cột đang so sánh — mà "so sánh hai cột kề nhau"
 * chính là cơ chế của bài. Chạm trần thì phần dư thành lề căn giữa CÓ CHỦ ĐÍCH,
 * không phải lỗi.
 *
 * Tỉ lệ khe/cột giữ đúng 14/56 = 0,25 của bản gốc.
 *
 * ── HIỆU CHỈNH MẬT ĐỘ (W4B-2A, sau soát trình duyệt) ───────────────────────
 * Trần đầu tiên đặt ở 96px là VƯỢT MỨC: bảy cột ra 864px, tám cột ra 984px —
 * kỹ thuật thì thích ứng đúng, nhưng cột to tới mức bố cục mất cân đối. Bài học
 * ghi lại để không lặp: **"simulation-first" KHÔNG có nghĩa là phóng đối tượng
 * cho chiếm nhiều sân khấu hơn.** Sân khấu ưu tiên chỗ cho *quan hệ* giữa các
 * đối tượng — con trỏ, cặp đang so sánh, ranh giới vùng đã sắp, quỹ đạo dời
 * chỗ, và sau này là công cụ thao tác của học sinh. Cột chỉ cần lớn tới mức
 * ĐỌC ĐƯỢC; chỗ dư dành cho cơ chế, không dành cho kích thước cột.
 *
 * Bốn ứng viên đo được (sân khấu 1306px):
 *
 *   trần   colW  khe   7 cột   8 cột
 *    96     96    24    864     984   ← vượt mức, bố cục mất cân đối
 *    76     76    19    684     779   ← CHỌN
 *    68     68    17    612     697
 *    60     60    15    540     615   ← gần như quay lại bản cũ (504)
 *
 * Chọn 76 vì nó giữ được khoảng cách so sánh giữa hai cột kề nhau đủ ngắn để
 * mắt bắt được cả cặp trong một lần nhìn, mà vẫn hơn hẳn bản hằng số cũ.
 */
const MIN_COL_W = 28;
const MAX_COL_W = 76;
const MIN_GAP = 8;
const MAX_GAP = 24;
const GAP_RATIO = COL_GAP / COL_W;
/** Chừa hai bên để hình không dính mép thẻ. */
const SAFE_PAD = 24;

export interface ArrayChartLayout {
  colW: number;
  gap: number;
  width: number;
  /** Đã chạm trần ngữ nghĩa — bề rộng dư thêm là lề căn giữa, không phải lỗi. */
  capped: boolean;
}

/**
 * Bố cục nội tại của biểu đồ dãy. HÀM THUẦN — kiểm được không cần trình duyệt.
 *
 * `available <= 0` nghĩa là chưa đo được khung (lần render đầu, SSR, jsdom):
 * trả đúng bố cục hằng số cũ để không có bước nhảy thị giác và để mọi test
 * SSR sẵn có giữ nguyên kết quả.
 */
export function arrayChartLayout(n: number, available: number): ArrayChartLayout {
  const count = Math.max(1, n);
  if (!Number.isFinite(available) || available <= 0) {
    return { colW: COL_W, gap: COL_GAP, width: count * COL_W + (count + 1) * COL_GAP, capped: false };
  }
  const usable = Math.max(0, available - SAFE_PAD);
  // width(colW) = n*colW + (n+1)*colW*GAP_RATIO  ⇒ giải ra colW
  const raw = usable / (count + (count + 1) * GAP_RATIO);
  const colW = Math.max(MIN_COL_W, Math.min(MAX_COL_W, Math.floor(raw)));
  const gap = Math.max(MIN_GAP, Math.min(MAX_GAP, Math.round(colW * GAP_RATIO)));
  return {
    colW,
    gap,
    width: count * colW + (count + 1) * gap,
    capped: colW >= MAX_COL_W,
  };
}

interface ColumnState {
  fill: string;
  stroke: string;
  strokeWidth: number;
  /** Cột đang tham gia sự kiện của bước hiện tại → vẽ con trỏ. */
  active: boolean;
}

function columnState(step: Step, index: number): ColumnState {
  // Sự kiện của bước hiện tại có ưu tiên cao nhất
  for (const ev of step.events) {
    if (ev.type === "swap" && (ev.i === index || ev.j === index)) {
      return step.userAction
        ? { fill: "var(--accent-purple)", stroke: "var(--accent-purple-deep)", strokeWidth: 2, active: true }
        : { fill: "var(--accent-orange)", stroke: "var(--accent-orange-deep)", strokeWidth: 2, active: true };
    }
    if (ev.type === "compare" && (ev.i === index || ev.j === index)) {
      return { fill: "var(--accent-sky)", stroke: "var(--primary)", strokeWidth: 2, active: true };
    }
    if (ev.type === "compare_value" && ev.i === index) {
      return { fill: "var(--accent-sky)", stroke: "var(--primary)", strokeWidth: 2, active: true };
    }
    if ((ev.type === "insert" || ev.type === "shift") && ("index" in ev ? ev.index === index : ev.to === index)) {
      return { fill: "var(--accent-purple)", stroke: "var(--accent-purple-deep)", strokeWidth: 2, active: true };
    }
  }
  // Sau đó đến marks trong snapshot
  const mark = step.snapshot.marks[index];
  if (mark === "found" || mark === "sorted") {
    return { fill: "var(--accent-green)", stroke: "var(--accent-green)", strokeWidth: 1, active: false };
  }
  if (mark === "eliminated") {
    return { fill: "var(--hairline)", stroke: "var(--hairline)", strokeWidth: 1, active: false };
  }
  if (mark === "considering") {
    return { fill: "var(--accent-teal)", stroke: "var(--accent-teal)", strokeWidth: 1, active: false };
  }
  return { fill: "#dcebfa", stroke: "var(--hairline)", strokeWidth: 1, active: false };
}

/* ── NGHĨA CỦA MARK THEO BÀI (W3B-1) ─────────────────────────────────────────
 *
 * Engine chỉ có bốn mark (`Mark` ở core/types.ts) nhưng chúng phục vụ chín
 * thuật toán, nên MỘT mark mang nhiều nghĩa — y hệt chuyện `eliminated` ở cuối
 * hàm dưới. Với `found`, đo trong Chrome (W3A-001/002) thấy cả bốn bài quét dãy
 * đều đọc thành "đã tìm thấy": `count_if` nói "đã tìm thấy" cho phần tử nó vừa
 * ĐẾM, `sum_if` cho phần tử vừa CỘNG vào tổng. Không bài nào trong bốn bài này
 * đi tìm một giá trị cho trước, nên nhãn đó dạy sai cơ chế.
 *
 * Sửa ở TẦNG TRÌNH BÀY: mark canonical giữ nguyên từng ký tự (engine, trace,
 * timeline không đụng tới) — chỉ chỗ ĐẶT TÊN cho màu là đổi. Bài không có trong
 * bảng rơi về nhãn cũ, nên `linear_search`/`binary_search` (hai bài THẬT SỰ đi
 * tìm) và mọi target khác không đổi một chữ.
 */
const FOUND_LABEL: Record<string, string> = {
  // Ở đây `found` là phần tử THẮNG cuối cùng: engine `clearMarks()` rồi mark
  // đúng một ô ở bước kết. Nó ĐƯỢC CHỌN làm max/min chứ không phải "tìm thấy".
  find_max: "đã chọn làm max",
  find_min: "đã chọn làm min",
  // Ở đây `found` gắn cho TỪNG phần tử thoả điều kiện, ngay bước nó được gộp
  // vào biến tích luỹ — nghĩa là "đã vào kết quả", khác hẳn "tìm thấy".
  count_if: "đã được đếm",
  sum_if: "đã được cộng vào tổng",
};

/* `considering` chỉ do find_max/find_min phát ra, và engine giữ ĐÚNG MỘT ô mang
 * mark này: ô đang giữ vai max/min hiện hành (khi cập nhật, ô cũ chuyển sang
 * `eliminated`). Gọi nó là "vùng đang xét" biến một phần tử cụ thể thành một
 * vùng mơ hồ, và trùng nghĩa với nhãn "đang xét / so sánh" ngay bên trên. */
const CONSIDERING_LABEL: Record<string, string> = {
  find_max: "max hiện tại",
  find_min: "min hiện tại",
};

/**
 * CHÚ GIẢI SUY TỪ TRACE THẬT (UI-CLARITY W1).
 *
 * Đặt cạnh `columnState` có chủ đích: đây là NƠI DUY NHẤT biết màu nào mang
 * nghĩa gì trên sân khấu dãy. Chú giải viết tay ở chỗ khác sẽ trôi khỏi bảng
 * màu này mà không có gì báo — mà một chú giải sai còn tệ hơn không có.
 *
 * Chỉ liệt kê trạng thái mà target THẬT SỰ dùng: quét toàn trace (không phải
 * riêng bước hiện tại) nên chú giải **đứng yên suốt timeline** thay vì hiện ra
 * rồi biến mất theo bước — bản trước chỉ hiện chú giải lúc đang giữ quân bài.
 *
 * KHÔNG liệt kê màu nền mặc định (phần tử chưa được đụng tới): đó là *vắng mặt
 * trạng thái*, không phải một tín hiệu được phát ra.
 */
export function arrayLegendItems(
  steps: Step[],
  opts: { algorithmId: string; hasGap: boolean },
): LegendItem[] {
  const items: LegendItem[] = [];
  const marks = new Set<string>();
  const events = new Set<string>();
  for (const s of steps) {
    // `marks` là Record<number, Mark> (thưa theo chỉ số), không phải mảng.
    for (const m of Object.values(s.snapshot.marks)) if (m) marks.add(m);
    for (const e of s.events) events.add(e.type);
  }

  if (events.has("compare") || events.has("compare_value")) {
    items.push({ tone: "scan", label: "đang xét / so sánh" });
  }
  if (marks.has("considering")) {
    items.push({
      tone: "considering",
      label: CONSIDERING_LABEL[opts.algorithmId] ?? "vùng đang xét",
    });
  }
  if (events.has("swap")) items.push({ tone: "bound", label: "đang đổi chỗ" });
  if (opts.hasGap) items.push({ tone: "gap", label: "ô trống" });
  if (marks.has("sorted")) items.push({ tone: "done", label: "phần đã sắp xong" });
  else if (marks.has("found")) {
    items.push({ tone: "done", label: FOUND_LABEL[opts.algorithmId] ?? "đã tìm thấy" });
  }

  /* CÙNG MỘT MÀU XÁM, HAI NGHĨA — nhãn phải theo cơ chế của bài.
     `binary_search` tô xám nửa BỊ LOẠI khỏi vùng tìm kiếm (không bao giờ xét
     lại). `find_max`/`count_if`/`linear_search`… tô xám phần ĐÃ DUYỆT QUA — đã
     xét rồi, không phải bị loại trừ. Dùng một nhãn cho cả hai là dạy sai đúng
     kiểu mà audit ngôn ngữ màu đã chỉ ra. */
  if (marks.has("eliminated")) {
    items.push({
      tone: "eliminated",
      label: opts.algorithmId === "binary_search" ? "nửa đã bị loại" : "đã duyệt qua",
    });
  }

  return items;
}

interface DragState {
  from: number;
  startX: number;
  startY: number;
  dx: number;
  dy: number;
  target: number | null;
}

interface ArrayViewProps {
  step: Step;
  labels: string[] | null;
  /** Cho phép kéo thả what-if (R3.3a: chỉ khi đang dừng, nguồn engine, chưa ở nhánh). */
  interactive?: boolean;
  onSwap?: (i: number, j: number) => void;
  /**
   * Vị trí Ô TRỐNG — chỗ một phần tử vừa bị rút ra khỏi dãy (sắp xếp chèn).
   * `snapshot.array` tại vị trí này vẫn còn BẢN SAO của phần tử vừa dời sang
   * phải; vẽ nguyên nó ra thì học sinh thấy một số xuất hiện hai lần và tưởng
   * thuật toán nhân bản phần tử. Ô trống vẽ bằng KHUNG NÉT ĐỨT + chữ, không chỉ
   * bằng màu. `null` = không có ô trống (mọi target khác không đổi gì).
   */
  gapIndex?: number | null;
}

export function ArrayView({
  step, labels, interactive = false, onSwap, gapIndex = null,
}: ArrayViewProps) {
  const arr = step.snapshot.array;
  const ids = step.snapshot.ids;
  const n = arr.length;
  const height = TOP_PAD + CHART_H + BOTTOM_PAD;
  const maxV = Math.max(...arr, 1);

  const svgRef = useRef<SVGSVGElement>(null);
  const [drag, setDrag] = useState<DragState | null>(null);

  /* Bề rộng khả dụng đo từ CHÍNH khung chứa, không từ `window.innerWidth`:
     sân khấu co giãn theo panel Quan sát mở/đóng chứ không theo cửa sổ. Đo tại
     chỗ (ArrayView là chủ sở hữu sizing) thay vì dựng một hook dùng chung khi
     mới có một consumer. */
  const boxRef = useRef<HTMLDivElement>(null);
  const [available, setAvailable] = useState(0);
  useEffect(() => {
    const el = boxRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(([entry]) => {
      setAvailable(Math.round(entry.contentRect.width));
    });
    ro.observe(el);
    setAvailable(Math.round(el.getBoundingClientRect().width));
    return () => ro.disconnect();
  }, []);

  const layout = arrayChartLayout(n, available);
  const colW = layout.colW;
  const colGap = layout.gap;
  const width = layout.width;

  const colX = (i: number) => colGap + i * (colW + colGap);

  /** Quy đổi khoảng cách chuột (px màn hình) sang đơn vị viewBox. */
  function screenToSvg(px: number): number {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect || rect.width === 0) return px;
    return px * (width / rect.width);
  }

  function targetFromCenter(cx: number, from: number): number | null {
    const idx = Math.round((cx - colGap - colW / 2) / (colW + colGap));
    if (idx < 0 || idx >= n || idx === from) return null;
    return idx;
  }

  function onPointerDown(e: ReactPointerEvent<SVGRectElement>, i: number) {
    if (!interactive || !onSwap) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    setDrag({ from: i, startX: e.clientX, startY: e.clientY, dx: 0, dy: 0, target: null });
  }

  function onPointerMove(e: ReactPointerEvent<SVGRectElement>) {
    if (!drag) return;
    const dx = screenToSvg(e.clientX - drag.startX);
    const dy = screenToSvg(e.clientY - drag.startY);
    const center = colX(drag.from) + colW / 2 + dx;
    setDrag({ ...drag, dx, dy, target: targetFromCenter(center, drag.from) });
  }

  function onPointerUp() {
    if (!drag) return;
    if (drag.target !== null && onSwap) onSwap(drag.from, drag.target);
    setDrag(null);
  }

  // Vẽ cột đang kéo sau cùng để nổi lên trên (SVG vẽ theo thứ tự)
  const order = arr.map((_, i) => i);
  if (drag) {
    order.splice(order.indexOf(drag.from), 1);
    order.push(drag.from);
  }

  return (
    <div ref={boxRef} style={{ width: "100%" }}>
    <svg
      ref={svgRef}
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      /* `maxWidth: width` GIỮ NGUYÊN — đây KHÔNG phải chỗ kéo giãn. `width` nay
         là bề rộng bố cục vừa tính lại từ khung chứa, nên viewBox vẫn khớp đúng
         pixel hiển thị và `scale ≈ 1` được bảo toàn (test khoá ở dag.test.tsx
         cùng luật). Hình lớn hơn vì BỐ CỤC lớn hơn, không vì SVG bị phóng. */
      style={{ maxWidth: width, display: "block", margin: "0 auto", touchAction: "none" }}
      role="img"
      aria-label="Mô phỏng dãy số"
    >
      {order.map((i) => {
        const v = arr[i];
        const h = Math.max((v / maxV) * CHART_H, 6);
        const y = TOP_PAD + CHART_H - h;
        const st = columnState(step, i);
        const dimmed = step.snapshot.marks[i] === "eliminated";
        const isDragged = drag?.from === i;
        const isTarget = drag?.target === i;
        const isGap = gapIndex === i;
        const tx = colX(i) + (isDragged ? drag.dx : 0);
        const ty = isDragged ? drag.dy : 0;

        // Ô TRỐNG: không vẽ cột giá trị (giá trị ở đây là bản sao còn sót),
        // chỉ vẽ khung nét đứt + chữ "trống" — khác HÌNH DẠNG, không chỉ khác màu.
        if (isGap) {
          return (
            <g key={ids[i]} style={{ transform: `translate(${colX(i)}px, 0px)`,
                                     transition: "transform 0.35s ease" }}>
              <rect x={0} y={TOP_PAD} width={colW} height={CHART_H} rx={5}
                    fill="none" stroke="var(--ink-muted)" strokeWidth={2} strokeDasharray="6 5" />
              <text x={colW / 2} y={TOP_PAD + CHART_H / 2} textAnchor="middle"
                    fontSize={12} fill="var(--ink-muted)">trống</text>
              <text x={colW / 2} y={TOP_PAD + CHART_H + (labels ? 42 : 26)} textAnchor="middle"
                    fontSize={11} fill="var(--ink-faint)">{i}</text>
            </g>
          );
        }

        return (
          <g
            key={ids[i]}
            style={{
              transform: `translate(${tx}px, ${ty}px)`,
              // Trượt mượt khi đổi chỗ/dời; khi đang kéo thì bám theo chuột ngay
              transition: isDragged ? "none" : "transform 0.35s ease",
            }}
            opacity={isDragged ? 0.85 : 1}
          >
            {isTarget && (
              <rect
                x={-4}
                y={TOP_PAD - 4}
                width={colW + 8}
                height={CHART_H + 8}
                rx={8}
                fill="none"
                stroke="var(--accent-purple-deep)"
                strokeWidth={2}
                strokeDasharray="6 4"
              />
            )}
            <rect
              x={0}
              y={y}
              width={colW}
              height={h}
              rx={5}
              fill={st.fill}
              stroke={isDragged ? "var(--accent-purple-deep)" : st.stroke}
              strokeWidth={isDragged ? 2 : st.strokeWidth}
              style={{
                transition: isDragged ? undefined : "y 0.25s ease, height 0.25s ease, fill 0.25s ease",
                cursor: interactive ? (isDragged ? "grabbing" : "grab") : "default",
              }}
              onPointerDown={(e) => onPointerDown(e, i)}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onPointerCancel={() => setDrag(null)}
            />
            <text
              x={colW / 2}
              y={y - 8}
              textAnchor="middle"
              fontSize={14}
              fontWeight={600}
              fill={dimmed ? "var(--ink-faint)" : "var(--ink)"}
              pointerEvents="none"
            >
              {fmt(v)}
            </text>
            {/* Con trỏ chỉ phần tử đang tham gia sự kiện của bước */}
            {st.active && (
              <path
                d={`M ${colW / 2} ${TOP_PAD + CHART_H + 4} l -6 9 h 12 z`}
                fill={st.stroke}
              />
            )}
            {labels && labels[i] && (
              <text
                x={colW / 2}
                y={TOP_PAD + CHART_H + 26}
                textAnchor="middle"
                fontSize={12}
                fill={dimmed ? "var(--ink-faint)" : "var(--ink-secondary)"}
              >
                {labels[i]}
              </text>
            )}
            <text
              x={colW / 2}
              y={TOP_PAD + CHART_H + (labels ? 42 : 26)}
              textAnchor="middle"
              fontSize={11}
              fill="var(--ink-faint)"
            >
              {i}
            </text>
          </g>
        );
      })}
    </svg>
    </div>
  );
}
