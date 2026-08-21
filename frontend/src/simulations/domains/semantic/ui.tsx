/**
 * Renderer 2D cho route sinh ngữ nghĩa — CHỈ ĐỌC khung.
 *
 * Không tính lại bước, không đánh giá lại biểu thức, không suy diễn trạng thái
 * ngữ nghĩa (bất biến #31). Mọi giá trị vẽ ra đều lấy thẳng từ khung mà
 * `model.ts` đã chọn.
 *
 * 2D ONLY theo MVP §1.1 — không có 3D cho route này trong khoá luận.
 */
import type { WorkspaceProps } from "../../types";
import type { SemanticConfig, SemanticObject, SemanticState } from "./model";

const O = 12; // bước lưới cơ sở, px

function nhan(o: SemanticObject): string {
  return o.label ?? "";
}

function ChuoiO({ o, sang }: { o: SemanticObject; sang: boolean }) {
  const items = o.items ?? [];
  return (
    <div className="sem-block">
      <div className="sem-label">{nhan(o)}</div>
      <div className="sem-strip" data-hot={sang || undefined}>
        {items.length === 0 ? (
          <div className="sem-cell sem-cell-empty" aria-label="rỗng" />
        ) : (
          items.map((v, i) => (
            <div className="sem-cell" key={i}>
              {String(v)}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function NganXep({ o, sang }: { o: SemanticObject; sang: boolean }) {
  const items = o.items ?? [];
  return (
    <div className="sem-block">
      <div className="sem-label">{nhan(o)}</div>
      <div className="sem-stack" data-hot={sang || undefined}>
        {items.length === 0 ? (
          <div className="sem-stack-empty">trống</div>
        ) : (
          [...items].reverse().map((v, i) => (
            <div className="sem-cell" key={i}>
              {String(v)}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function HopGiaTri({ o, sang }: { o: SemanticObject; sang: boolean }) {
  const v = o.value;
  const rong = v === "" || v === null || v === undefined;
  return (
    <div className="sem-block sem-block-inline">
      <div className="sem-label">{nhan(o)}</div>
      <div className="sem-box" data-hot={sang || undefined}>
        {rong ? <span className="sem-chua-co">chưa có</span> : String(v)}
      </div>
    </div>
  );
}

function CotBieuDo({ o, sang }: { o: SemanticObject; sang: boolean }) {
  const items = (o.items ?? []).map((x) => Number(x) || 0);
  const cao = Math.max(1, ...items.map(Math.abs));
  return (
    <div className="sem-block">
      <div className="sem-label">{nhan(o)}</div>
      <div className="sem-bars" data-hot={sang || undefined}>
        {items.map((v, i) => (
          <div className="sem-bar-wrap" key={i}>
            <div className="sem-bar" style={{ height: `${(Math.abs(v) / cao) * 8 * O}px` }} />
            <div className="sem-bar-val">{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Bang({ o, sang }: { o: SemanticObject; sang: boolean }) {
  const rows = (o.items ?? []) as unknown[];
  return (
    <div className="sem-block">
      <div className="sem-label">{nhan(o)}</div>
      <div className="sem-grid" data-hot={sang || undefined}>
        {rows.map((row, r) => (
          <div className="sem-grid-row" key={r}>
            {(Array.isArray(row) ? row : [row]).map((v, c) => (
              <div className="sem-cell" key={c}>
                {String(v)}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Đồ thị — LAYOUT TẤT ĐỊNH, không physics, không camera, không editor.
 *
 * Đỉnh xếp đều trên một đường tròn theo THỨ TỰ ĐÃ SẮP của id. Chọn vòng tròn vì
 * nó tất định tuyệt đối: cùng một đồ thị luôn cho cùng một hình, nên ảnh chụp so
 * được giữa các lượt và test hình học không đỏ ngẫu nhiên. Force-directed đẹp
 * hơn nhưng phụ thuộc trạng thái khởi tạo — mỗi lần chạy một khác.
 *
 * `visited`/`current` đến TỪ BACKEND (đọc `memory_snapshot`). Component này
 * không biết BFS là gì và không được biết.
 */
function DoThi({ o, sang }: { o: SemanticObject; sang: boolean }) {
  const nodes = o.nodes ?? [];
  if (nodes.length === 0) return null;

  const R = 58;
  const PAD = 22;
  const size = (R + PAD) * 2;
  const tam = size / 2;
  const viTri = new Map<string, { x: number; y: number }>();
  nodes.forEach((n, i) => {
    // Bắt đầu từ 12 giờ (−π/2) để đồ thị nhỏ trông cân, và để thứ tự đọc khớp
    // thứ tự id — học sinh dò được đỉnh nào là đỉnh nào.
    const goc = (i / nodes.length) * Math.PI * 2 - Math.PI / 2;
    viTri.set(n, { x: tam + R * Math.cos(goc), y: tam + R * Math.sin(goc) });
  });

  const daTham = new Set(o.visited ?? []);
  const dangXet = o.current ?? null;

  return (
    <div className="sem-block">
      <div className="sem-label">{nhan(o)}</div>
      <svg
        className="sem-graph"
        data-hot={sang || undefined}
        viewBox={`0 0 ${size} ${size}`}
        width={size}
        height={size}
        role="img"
        aria-label={`Đồ thị ${nodes.length} đỉnh`}
      >
        {(o.edges ?? []).map(([u, v]) => {
          const a = viTri.get(u);
          const b = viTri.get(v);
          if (!a || !b) return null;
          return (
            <line
              key={`${u}-${v}`}
              className="sem-graph-edge"
              x1={a.x} y1={a.y} x2={b.x} y2={b.y}
            />
          );
        })}
        {nodes.map((n) => {
          const p = viTri.get(n)!;
          const trangThai = n === dangXet ? "current" : daTham.has(n) ? "visited" : "idle";
          return (
            <g key={n} className="sem-graph-node" data-state={trangThai}>
              <circle cx={p.x} cy={p.y} r={13} />
              <text x={p.x} y={p.y + 4} textAnchor="middle">{n}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

/** Con trỏ CHỈ vẽ khi neo phân giải được — không có ô thì không vẽ (#34). */
function ConTro({ o }: { o: SemanticObject }) {
  if (typeof o.target_index !== "number") return null;
  return (
    <div className="sem-pointer" style={{ marginInlineStart: `${o.target_index * 3.5}rem` }}>
      <span className="sem-pointer-cap">{nhan(o)}</span>
      <span className="sem-pointer-stem" aria-hidden="true" />
    </div>
  );
}

function VeMot({ o, sang }: { o: SemanticObject; sang: boolean }) {
  switch (o.type) {
    case "array_strip":
    case "queue_view":
      return <ChuoiO o={o} sang={sang} />;
    case "stack_view":
      return <NganXep o={o} sang={sang} />;
    case "bar_chart":
      return <CotBieuDo o={o} sang={sang} />;
    case "graph_view":
      return <DoThi o={o} sang={sang} />;
    case "table_grid":
      return <Bang o={o} sang={sang} />;
    case "value_box":
    case "bit_register":
    case "tree_element":
      return <HopGiaTri o={o} sang={sang} />;
    case "pointer":
      return <ConTro o={o} />;
    default:
      // Kiểu lạ: KHÔNG vẽ hộp rỗng giả vờ có gì đó. Backend đã fail-closed ở
      // #33/#34, nên tới đây mà còn kiểu lạ thì im lặng bỏ qua là đúng.
      return null;
  }
}

export function SemanticWorkspace({
  state,
}: WorkspaceProps<SemanticConfig, SemanticState>) {
  const buoc = state.timeline[state.cursor];
  if (!buoc) return null;
  const sang = new Set(buoc.highlighted);

  return (
    <div className="sem-stage" data-route="semantic">
      {state.groupingLevel === "iteration" && (
        <p className="sem-note">
          Đang xem gộp: mỗi bước hiển thị trọn một vòng lặp.
        </p>
      )}
      {state.executionTruncated && (
        <p className="sem-note sem-note-warn">
          Thuật toán dài hơn giới hạn mô phỏng nên chưa chạy hết.
        </p>
      )}

      <div className="sem-objects">
        {buoc.objects.map((o) => (
          <VeMot key={o.id} o={o} sang={sang.has(o.id)} />
        ))}
      </div>

      {/* (SHELL-N) THUYẾT MINH KHÔNG dựng ở đây — module cấp chữ qua `narrate()`
          ở `index.ts`, shell dựng bằng `NarrationSlot`. Bản đầu dựng cả hai nơi
          và L5a chụp được hậu quả: cùng một câu hiện HAI LẦN dưới sân khấu.
          Cùng quy ước với `generic/ui.tsx` và `algorithm/ui.tsx`. */}
    </div>
  );
}
