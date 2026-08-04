import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { TraversalFrontier, frontierDelta } from "./TraversalFrontier";

/**
 * PRIMITIVE FRONTIER — khoá ba thứ dễ làm sai nhất:
 * 1. Queue và Stack KHÔNG được vẽ giống nhau rồi đổi nhãn (đầu ở hai phía khác
 *    nhau — vẽ sai đầu là dạy sai thuật toán).
 * 2. `frontierDelta` phải theo BỘI SỐ, không theo tập hợp: DFS cho phép một node
 *    nằm nhiều lần trong ngăn xếp.
 * 3. Primitive thuần trình bày — không giữ state, không đổi dữ liệu đầu vào.
 */

const items = (...ids: string[]) => ids.map((id) => ({ id, label: id }));
const html = (el: React.ReactElement) => renderToString(el).replace(/<!--.*?-->/g, "");

describe("frontierDelta — so sánh theo bội số, tất định", () => {
  it("bước đầu (không có bước trước) → không có gì vào/ra", () => {
    expect(frontierDelta(null, ["A"])).toEqual({ entering: [], leaving: [] });
  });

  it("thêm một phần tử", () => {
    expect(frontierDelta(["A"], ["A", "B"])).toEqual({ entering: ["B"], leaving: [] });
  });

  it("lấy ra một phần tử", () => {
    expect(frontierDelta(["A", "B"], ["B"])).toEqual({ entering: [], leaving: ["A"] });
  });

  it("vừa ra vừa vào trong cùng một bước", () => {
    const d = frontierDelta(["A", "B"], ["B", "C", "D"]);
    expect(d.leaving).toEqual(["A"]);
    expect(d.entering.sort()).toEqual(["C", "D"]);
  });

  it("frontier rỗng ở cả hai phía không lỗi", () => {
    expect(frontierDelta([], [])).toEqual({ entering: [], leaving: [] });
  });

  it("TRÙNG id (DFS đẩy một node nhiều lần) đếm theo BỘI SỐ, không gộp", () => {
    // ngăn xếp có hai bản B; bước sau chỉ còn một → đúng 1 phần tử rời đi
    expect(frontierDelta(["B", "B"], ["B"])).toEqual({ entering: [], leaving: ["B"] });
    // ngược lại: đẩy thêm một bản B nữa
    expect(frontierDelta(["B"], ["B", "B"])).toEqual({ entering: ["B"], leaving: [] });
  });

  it("hàm THUẦN — không sửa mảng đầu vào", () => {
    const prev = ["A", "B"];
    const curr = ["B", "C"];
    frontierDelta(prev, curr);
    expect(prev).toEqual(["A", "B"]);
    expect(curr).toEqual(["B", "C"]);
  });
});

describe("TraversalFrontier — queue và stack KHÔNG chung bố cục", () => {
  it("queue: phần tử sắp ra là ĐẦU MẢNG, gắn nhãn chữ 'đầu'", () => {
    const h = html(
      <TraversalFrontier mode="queue" items={items("C", "D", "E")} label="Hàng đợi (FIFO)" />,
    );
    expect(h).toContain("frontier-queue");
    expect(h).toContain("đầu");
    expect(h).not.toContain("đỉnh");
    // C (đầu mảng) phải mang lớp is-out-next
    const first = h.indexOf("is-out-next");
    const posC = h.indexOf(">C<");
    const posD = h.indexOf(">D<");
    expect(first).toBeGreaterThan(-1);
    expect(posC).toBeLessThan(posD); // giữ thứ tự engine: trái → phải
    expect(h.slice(first, first + 200)).toContain(">C<");
  });

  it("stack: phần tử sắp ra là CUỐI MẢNG, đảo để đỉnh nằm TRÊN, nhãn 'đỉnh'", () => {
    const h = html(
      <TraversalFrontier mode="stack" items={items("A", "B", "E")} label="Ngăn xếp (LIFO)" />,
    );
    expect(h).toContain("frontier-stack");
    expect(h).toContain("đỉnh");
    expect(h).not.toContain(">đầu<");
    // đỉnh = E (cuối mảng) và phải được vẽ TRƯỚC trong DOM (nằm trên)
    const posE = h.indexOf(">E<");
    const posA = h.indexOf(">A<");
    expect(posE).toBeLessThan(posA);
    const out = h.indexOf("is-out-next");
    expect(h.slice(out, out + 200)).toContain(">E<");
  });

  it("cùng một mảng, queue và stack đánh dấu HAI phần tử khác nhau", () => {
    const same = items("P", "Q", "R");
    const q = html(<TraversalFrontier mode="queue" items={same} label="q" />);
    const s = html(<TraversalFrontier mode="stack" items={same} label="s" />);
    const outOf = (h: string) => {
      const i = h.indexOf("is-out-next");
      return h.slice(i, i + 200).match(/>([PQR])</)?.[1];
    };
    expect(outOf(q)).toBe("P"); // FIFO → ra ở đầu
    expect(outOf(s)).toBe("R"); // LIFO → ra ở đỉnh (cuối mảng)
  });

  it("rỗng: hiện '(rỗng)', không lỗi", () => {
    const h = html(<TraversalFrontier mode="queue" items={[]} label="Hàng đợi (FIFO)" />);
    expect(h).toContain("(rỗng)");
    expect(h).toContain("0 phần tử");
  });

  it("một phần tử: vừa là đầu vừa là cuối, không lỗi", () => {
    const h = html(<TraversalFrontier mode="stack" items={items("X")} label="Ngăn xếp (LIFO)" />);
    expect(h).toContain(">X<");
    expect((h.match(/is-out-next/g) ?? []).length).toBe(1);
  });

  it("nhãn TRÙNG nhưng khác vị trí không bị gộp (DFS đẩy trùng node)", () => {
    const h = html(
      <TraversalFrontier mode="stack" items={items("B", "B")} label="Ngăn xếp (LIFO)" />,
    );
    expect((h.match(/frontier-item[ "]/g) ?? []).length).toBe(2);
    expect(h).toContain("2 phần tử");
  });

  it("phần tử vừa vào / vừa ra được đánh dấu bằng CHỮ, không chỉ màu", () => {
    const h = html(
      <TraversalFrontier
        mode="queue"
        items={items("D", "E")}
        delta={{ entering: ["E"], leaving: ["C"] }}
        label="Hàng đợi (FIFO)"
      />,
    );
    expect(h).toContain("vừa lấy ra");
    expect(h).toContain(">C<"); // phần tử rời đi vẫn nhìn thấy được
    expect(h).toContain("mới");
  });

  it("luật FIFO/LIFO được nói bằng chữ trên chính khối", () => {
    expect(html(<TraversalFrontier mode="queue" items={items("A")} label="q" />))
      .toContain("FIFO");
    expect(html(<TraversalFrontier mode="stack" items={items("A")} label="s" />))
      .toContain("LIFO");
  });
});
