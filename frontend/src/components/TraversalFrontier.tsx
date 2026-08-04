/**
 * TraversalFrontier — PRIMITIVE DÙNG CHUNG cho frontier của duyệt đồ thị/cây.
 *
 * VÌ SAO CÓ: audit cơ chế chấm `network.graph_traversal` 9/18 và `tree.traversal`
 * 11/18, cùng một lý do — frontier chỉ là MỘT DÒNG CHỮ ("Hàng đợi: C, D"). Mà
 * frontier chính là thứ phân biệt BFS với DFS: bỏ nó đi thì hai thuật toán trông
 * y hệt nhau, chỉ khác mã giả.
 *
 * RANH GIỚI CỨNG — primitive này KHÔNG:
 * - sở hữu state (mọi thứ nhận qua props, dựng lại từ cursor hiện tại);
 * - chạy lại BFS/DFS/traversal để tự tính frontier;
 * - đọc/parse narration;
 * - giữ animation state làm nguồn sự thật.
 * Nó chỉ VẼ mảng `items` mà engine đã ghi trong `step.frontierAfter`.
 *
 * QUEUE VÀ STACK KHÔNG PHẢI MỘT THỨ ĐỔI NHÃN:
 * - queue (FIFO): engine `shift()` → phần tử SẮP RA nằm ở **đầu mảng**. Vẽ nằm
 *   ngang, trái → phải; mũi tên RA ở bên trái, mũi tên VÀO ở bên phải.
 * - stack (LIFO): engine `pop()` → phần tử SẮP RA nằm ở **cuối mảng**. Vẽ dựng
 *   đứng và ĐẢO lại để đỉnh nằm trên; đẩy/lấy đều ở đỉnh.
 * Vẽ sai đầu là dạy sai thuật toán, nên hai mode có bố cục khác nhau hẳn.
 */

export interface FrontierItem {
  /** Định danh node theo engine. KHÔNG duy nhất: DFS cho phép một node nằm
   *  nhiều lần trong ngăn xếp — nên key vẽ phải kèm vị trí. */
  id: string;
  label: string;
}

export type FrontierMode = "queue" | "stack";

export interface FrontierDelta {
  /** id vừa được thêm vào frontier ở bước này. */
  entering: string[];
  /** id vừa rời frontier ở bước này. */
  leaving: string[];
}

/**
 * So sánh frontier hai bước liền kề — TẤT ĐỊNH, theo BỘI SỐ (multiset), không
 * theo tập hợp: DFS có thể chứa cùng một node nhiều lần, dùng Set sẽ tính sai.
 * Thuần hàm: cùng đầu vào luôn cho cùng kết quả, nên back/scrub/nhảy cuối đều
 * dựng lại đúng mà không cần nhớ gì giữa các lần render.
 */
export function frontierDelta(prev: string[] | null, curr: string[]): FrontierDelta {
  if (!prev) return { entering: [], leaving: [] };
  const count = (xs: string[]) => {
    const m = new Map<string, number>();
    for (const x of xs) m.set(x, (m.get(x) ?? 0) + 1);
    return m;
  };
  const a = count(prev);
  const b = count(curr);
  const entering: string[] = [];
  const leaving: string[] = [];
  for (const [id, n] of b) {
    const d = n - (a.get(id) ?? 0);
    for (let i = 0; i < d; i += 1) entering.push(id);
  }
  for (const [id, n] of a) {
    const d = n - (b.get(id) ?? 0);
    for (let i = 0; i < d; i += 1) leaving.push(id);
  }
  return { entering, leaving };
}

interface Props {
  mode: FrontierMode;
  /** Theo ĐÚNG thứ tự engine ghi trong `frontierAfter`. */
  items: FrontierItem[];
  /** id vừa vào / vừa ra (từ `frontierDelta`). */
  delta?: FrontierDelta;
  /** Node đang được xử lý ở bước này (engine `step.current`). */
  activeId?: string | null;
  /** Nhãn hiển thị, vd "Hàng đợi (FIFO)". */
  label: string;
}

const EMPTY_TEXT = "(rỗng)";

export function TraversalFrontier({ mode, items, delta, activeId = null, label }: Props) {
  const entering = new Set(delta?.entering ?? []);
  const leaving = delta?.leaving ?? [];

  /* Vị trí phần tử SẮP RA: queue = đầu mảng, stack = cuối mảng. */
  const outIndex = items.length === 0 ? -1 : mode === "queue" ? 0 : items.length - 1;
  /* Stack vẽ đảo để ĐỈNH nằm trên — thứ tự dữ liệu không đổi, chỉ đổi cách bày. */
  const order = mode === "stack" ? [...items].reverse() : items;
  const realIndex = (i: number) => (mode === "stack" ? items.length - 1 - i : i);

  return (
    <section className={`frontier frontier-${mode}`} aria-label={label}>
      <header className="frontier-head">
        <span className="frontier-label">{label}</span>
        <span className="frontier-count">{items.length} phần tử</span>
      </header>

      {/* Phần tử vừa RỜI frontier — hiện tách ra để thấy "vừa lấy ra cái gì". */}
      {leaving.length > 0 && (
        <p className="frontier-left-out">
          <span className="frontier-tag is-out">vừa lấy ra</span>
          {leaving.join(", ")}
        </p>
      )}

      {items.length === 0 ? (
        <p className="frontier-empty">{EMPTY_TEXT}</p>
      ) : (
        <ol className="frontier-items">
          {order.map((it, i) => {
            const ri = realIndex(i);
            const isOut = ri === outIndex;
            const isNew = entering.has(it.id);
            const isActive = activeId !== null && it.id === activeId;
            const cls = ["frontier-item"];
            if (isOut) cls.push("is-out-next");
            if (isNew) cls.push("is-new");
            if (isActive) cls.push("is-active");
            return (
              <li key={`${it.id}#${ri}`} className={cls.join(" ")}>
                {/* Nhãn CHỮ cho vị trí — không để màu làm tín hiệu duy nhất. */}
                {isOut && (
                  <span className="frontier-pos">{mode === "queue" ? "đầu" : "đỉnh"}</span>
                )}
                <span className="frontier-value">{it.label}</span>
                {isNew && <span className="frontier-tag is-in">mới</span>}
              </li>
            );
          })}
        </ol>
      )}

      <p className="frontier-rule">
        {mode === "queue"
          ? "FIFO — vào ở cuối, ra ở đầu (trái → phải)"
          : "LIFO — đẩy vào và lấy ra đều ở đỉnh (trên cùng)"}
      </p>
    </section>
  );
}
