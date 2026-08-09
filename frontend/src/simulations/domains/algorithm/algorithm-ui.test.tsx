import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./index";
import { AlgorithmWorkspace, insertionHold } from "./ui";
import type { AlgorithmSimState } from "./model";
import { activeTrace } from "./model";
import type { AlgorithmId } from "../../../core/types";

/**
 * M9-S1 — UI theo chính sách tương tác + dải nhân quả dùng chung.
 *
 * (19) Ở một điểm quyết định, các biểu diễn liên kết phải cùng kể MỘT sự kiện:
 * dải nhân quả (expression) dùng đúng giá trị mà sự kiện compare của trace nêu.
 */

function stateAt(algorithmId: AlgorithmId, data: Record<string, unknown>, cursor: number): AlgorithmSimState {
  const mod = makeAlgorithmModule(algorithmId);
  const r = mod.validateConfig({ problem: {}, algorithm_id: algorithmId, data, data_generated: false, notes: null });
  if (!r.ok) throw new Error(r.error);
  return mod.timeline!.goToStep(mod.init(r.config), cursor) as AlgorithmSimState;
}

function html(algorithmId: AlgorithmId, data: Record<string, unknown>, cursor: number): string {
  const mod = makeAlgorithmModule(algorithmId);
  const r = mod.validateConfig({ problem: {}, algorithm_id: algorithmId, data, data_generated: false, notes: null });
  if (!r.ok) throw new Error(r.error);
  const s = stateAt(algorithmId, data, cursor);
  return renderToString(
    <AlgorithmWorkspace config={r.config} state={s} busy={false} dispatch={() => {}} />,
  );
}

describe("gating swap trong AlgorithmWorkspace", () => {
  /* W3B §15 — mode "free" GIỮ NGUYÊN, nhưng gợi ý kéo không được mời học sinh
     làm việc đang bị khoá. Ở bước quyết định, cam kết đi trước bằng nút; kéo
     (thí nghiệm what-if) mở lại sau khi đã chốt. */
  it("bubble_sort (free): hiện gợi ý kéo-thả ở bước KHÔNG phải điểm quyết định", () => {
    const h = html("bubble_sort", { array: [1, 3, 2], order: "asc" }, 0);
    expect(h).toContain("Kéo một cột");
  });

  it("bubble_sort: ở điểm quyết định CHƯA cam kết thì không mời kéo", () => {
    const h = html("bubble_sort", { array: [1, 3, 2], order: "asc" }, 1);
    expect(h).toContain("Thao tác sắp xếp"); // vùng cam kết có mặt
    expect(h).not.toContain("Kéo một cột"); // …và kéo không được mời song song
  });

  it("(17) sum_if (hidden): KHÔNG gợi ý kéo-thả — kể cả sau khi có cổng Thí nghiệm", () => {
    /* W4B-2C ĐỔI TIỀN ĐỀ CỦA TEST NÀY, có chủ đích.
       Trước: `hidden` ⇒ không kéo VÀ không nút thí nghiệm — đúng khi cổng chỉ
       mang MỘT nghĩa là "mở kéo-thả".
       Nay: cổng mang nghĩa rộng hơn — "công cụ của học sinh". Với `sum_if` bộ
       công cụ đó chỉ có CAM KẾT, không có kéo. Nên nút thí nghiệm được phép có
       mặt, còn điều phải giữ bằng mọi giá vẫn là: KHÔNG kéo.
       Đó mới là thứ `mode: "hidden"` bảo vệ (kéo ở bài này là trang trí). */
    const h = html("sum_if", { array: [5, 8, 3], condition: { op: ">", value: 4 } }, 1);
    expect(h).not.toContain("Kéo một cột");
    expect(h).not.toContain("cursor:grab");
  });

  it("(16) binary_search (challenge): không gợi ý kéo tự do; CÓ nút thí nghiệm phá tiền điều kiện", () => {
    const h = html("binary_search", { array: [1, 3, 5, 7, 9, 11, 13], target: 3 }, 1);
    expect(h).not.toContain("Kéo một cột");
    expect(h).toContain("Thí nghiệm");
    expect(h).toContain("sắp thứ tự");
  });

  it("find_max (challenge): có nút thí nghiệm phá bất biến, không kéo tự do mặc định", () => {
    const h = html("find_max", { array: [7.5, 9, 6] }, 1);
    expect(h).not.toContain("Kéo một cột");
    expect(h).toContain("Thí nghiệm");
  });

  it("(PhET/CLT) challenge: teaser tự-giải-thích hiện TRƯỚC khi mở thí nghiệm — nút không còn bí ẩn", () => {
    // find_max: teaser nêu bất biến vùng-đã-duyệt, mời thử mà chưa lộ hệ quả.
    const hMax = html("find_max", { array: [7.5, 9, 6] }, 1);
    expect(hMax).toContain("vùng đã duyệt");
    // binary_search: teaser nêu tiền điều kiện dãy-đã-sắp, ngay khi CHƯA mở lab.
    const hBin = html("binary_search", { array: [1, 3, 5, 7, 9, 11, 13], target: 3 }, 1);
    expect(hBin).toContain("phá thứ tự");
  });

  it("linear_search (framed): kéo được nhưng khung câu hỏi là CHI PHÍ tìm kiếm", () => {
    const h = html("linear_search", { array: [4, 9, 7], target: 9 }, 1);
    expect(h).toContain("sớm hơn"); // khung: đưa target sớm/muộn → số lần so sánh đổi
  });
});

describe("(19) dải nhân quả — khớp sự kiện trace hiện tại", () => {
  it("bước quyết định find_max: expression chứa đúng hai giá trị mà event compare nêu", () => {
    const s = stateAt("find_max", { array: [7.5, 9, 6] }, 1);
    const step = activeTrace(s).steps[1];
    const cmp = step.events.find((e) => e.type === "compare") as { i: number; j: number };
    const vi = step.snapshot.array[cmp.i];
    const vj = step.snapshot.array[cmp.j];

    const h = html("find_max", { array: [7.5, 9, 6] }, 1);
    /* INTERACTION-FAMILY W1: ở cụm quét dãy, bước quyết định từng được trình bày
       bằng VÙNG HÀNH ĐỘNG (`ScanActionZone`) thay cho dải nhân quả — vùng đó
       mang sẵn state line + phép so sánh, nên dựng cả hai là lặp.

       W4B-2B §7: `find_max` nay GÁC vùng cam kết sau cổng Thí nghiệm, mà SSR
       luôn thấy `labOpen = false` (state cục bộ của component — ARCHITECTURE_MAP
       §8 #13), nên ở đây bề mặt hợp lệ là DẢI NHÂN QUẢ. Đúng luật "một bề mặt
       một lúc", chỉ là bề mặt đổi theo chế độ. Quan hệ KHÔNG được biến mất khỏi
       Quan sát chỉ vì nút cam kết đã đi chỗ khác.

       Điều test này thật sự khoá KHÔNG ĐỔI: biểu thức phải dùng ĐÚNG hai giá trị
       mà event `compare` nêu, không phải renderer tự tính lại. */
    expect(h).toContain("decision-strip");
    expect(h).not.toContain("scan-action");
    // SSR escape ">"
    expect(h).toMatch(new RegExp(`${vi}\\s*&gt;\\s*${String(vj).replace(".", ",")}`));
  });

  it("bước hệ quả find_max (cập nhật max): dải nói rõ nhân quả trước → sau", () => {
    const h = html("find_max", { array: [7.5, 9, 6] }, 2);
    expect(h).toContain("decision-strip");
    expect(h).toContain("→");
    expect(h).toContain("max");
  });
});

/**
 * (INSERT-HOLD) SẮP XẾP CHÈN — quân bài đang cầm, ô trống, và dịch phải.
 *
 * Lỗi audit bắt được: sân khấu hiện dãy `[3, 7, 7, 9, 8, 2]` — số `7` hai lần và
 * giá trị đang chèn (`4`) biến mất. Engine KHÔNG sai: `vars.gia_tri_chen` giữ
 * quân bài, và `snapshot.ids` giữ định danh của nó ĐÚNG tại ô trống. Renderer
 * trước đây chỉ đọc `array` nên vẽ ra bản sao còn sót.
 *
 * Các test dưới đây khoá: số phần tử LOGIC luôn đúng, không có số nào bị nhân
 * bản trên màn hình, quân bài luôn nhìn thấy được, và ô trống lùi dần sang trái.
 */
describe("(INSERT-HOLD) sắp xếp chèn: đang giữ · ô trống · dịch phải", () => {
  const DATA = { array: [7, 3, 9, 4, 8, 2], order: "asc" };
  const mod = makeAlgorithmModule("insertion_sort");
  const cfg = (() => {
    const r = mod.validateConfig({
      problem: {}, algorithm_id: "insertion_sort", data: DATA,
      data_generated: false, notes: null,
    });
    if (!r.ok) throw new Error(r.error);
    return r.config;
  })();
  const base = mod.init(cfg) as AlgorithmSimState;
  const steps = activeTrace(base).steps;
  const stateFor = (c: number) => mod.timeline!.goToStep(base, c) as AlgorithmSimState;
  const at = (c: number) =>
    renderToString(
      <AlgorithmWorkspace
        config={cfg}
        state={mod.timeline!.goToStep(base, c) as AlgorithmSimState}
        busy={false}
        dispatch={() => {}}
      />,
    ).replace(/<!--.*?-->/g, "");

  /** Bước đang trong một lượt chèn (đã rút quân bài, chưa chèn xong). */
  const holdingSteps = steps
    .map((s, i) => ({ s, i }))
    .filter(({ s }) =>
      typeof s.snapshot.vars["gia_tri_chen"] === "number" &&
      !s.events.some((e) => e.type === "insert"));

  it("có ít nhất một bước đang giữ quân bài (fixture đủ để kiểm)", () => {
    expect(holdingSteps.length).toBeGreaterThan(3);
  });

  it("mọi bước đang giữ: quân bài hiện ở khu 'Đang giữ' và nói rõ đã rút khỏi dãy", () => {
    for (const { i } of holdingSteps) {
      const h = at(i);
      expect(h, `bước ${i} thiếu khay đang giữ`).toContain("hold-tray");
      expect(h, `bước ${i} thiếu chữ "Đang giữ"`).toContain("Đang giữ");
      expect(h, `bước ${i} không nói ô trống`).toContain("ô trống ở vị trí");
    }
  });

  it("mọi bước đang giữ: dãy có ĐÚNG MỘT ô trống, vẽ bằng nét đứt + chữ", () => {
    for (const { i } of holdingSteps) {
      const h = at(i);
      expect((h.match(/>trống</g) ?? []).length, `bước ${i}`).toBe(1);
      expect(h).toContain("stroke-dasharray");
    }
  });

  it("KHÔNG bước nào hiện một giá trị bị nhân bản trên sân khấu", () => {
    for (const { s, i } of holdingSteps) {
      const gapId = s.snapshot.ids;
      // giá trị THẬT đang nằm trong dãy = mọi ô trừ ô trống
      const gap = insertionHold(stateFor(i), i)!.gapIndex;
      const shown = s.snapshot.array.filter((_, idx) => idx !== gap);
      const key = s.snapshot.vars["gia_tri_chen"] as number;
      // tổng số phần tử logic = ô có giá trị + quân bài đang cầm
      expect(shown.length + 1, `bước ${i} sai số phần tử`).toBe(s.snapshot.array.length);
      // multiset [dãy hiện + quân bài] luôn bằng multiset ban đầu
      const got = [...shown, key].sort((a, b) => a - b);
      expect(got, `bước ${i} multiset lệch`).toEqual([...DATA.array].sort((a, b) => a - b));
      expect(gapId.length).toBe(DATA.array.length);
    }
  });

  it("ô trống LÙI DẦN sang trái trong một lượt (đúng chiều dịch phải)", () => {
    // lấy lượt chèn đầu tiên có ít nhất hai bước dịch
    const rounds: number[][] = [];
    let cur: number[] = [];
    steps.forEach((s, i) => {
      if (s.events.some((e) => e.type === "assign_var" && e.name === "gia_tri_chen")) {
        if (cur.length) rounds.push(cur);
        cur = [];
      }
      const h = insertionHold(stateFor(i), i);
      if (h) cur.push(h.gapIndex);
    });
    if (cur.length) rounds.push(cur);
    const multi = rounds.find((r) => new Set(r).size >= 2);
    expect(multi, "fixture không có lượt nào dịch ≥2 lần").toBeDefined();
    const uniq = [...new Set(multi!)];
    for (let k = 1; k < uniq.length; k += 1) {
      expect(uniq[k], "ô trống phải lùi sang TRÁI").toBeLessThan(uniq[k - 1]);
    }
  });

  it("bước CHÈN: không còn khay giữ, không còn ô trống", () => {
    const insertStep = steps.findIndex((s) => s.events.some((e) => e.type === "insert"));
    const h = at(insertStep);
    expect(h).not.toContain("hold-tray");
    expect(h).not.toContain(">trống<");
  });

  it("kết quả cuối đúng và dãy đủ phần tử", () => {
    const lastStep = steps[steps.length - 1];
    expect(lastStep.snapshot.array).toEqual([...DATA.array].sort((a, b) => a - b));
    expect(lastStep.snapshot.array.length).toBe(DATA.array.length);
  });
});


/**
 * (SEL-CONSISTENCY) SẮP XẾP CHỌN — mọi vùng giao diện phải cùng nói MỘT thuật toán.
 *
 * Bối cảnh: ảnh trong audit cơ chế cho thấy `selection_sort` mang tiêu đề "phương
 * pháp nổi bọt". Nguyên nhân là FIXTURE của harness audit (catalog công khai
 * không có mẫu riêng cho selection_sort nên envelope được nhân bản từ
 * bubble_sort), KHÔNG phải sản phẩm. Test này khoá điều đó lại: với một config
 * selection_sort đúng, tên thuật toán · mã giả · thuyết minh · engine phải khớp,
 * và KHÔNG vùng nào được nhắc "nổi bọt".
 */
describe("(SEL-CONSISTENCY) sắp xếp chọn nói cùng một thuật toán ở mọi chỗ", () => {
  const DATA = { array: [7, 3, 9, 4, 8, 2], order: "asc" };
  const mod = makeAlgorithmModule("selection_sort");
  const r = mod.validateConfig({
    problem: { summary: "Sắp xếp dãy tăng dần bằng phương pháp chọn" },
    algorithm_id: "selection_sort", data: DATA, data_generated: false, notes: null,
  });
  if (!r.ok) throw new Error(r.error);
  const cfg = r.config;
  const base = mod.init(cfg) as AlgorithmSimState;
  const steps = activeTrace(base).steps;
  const render = (c: number) =>
    renderToString(
      <AlgorithmWorkspace
        config={cfg}
        state={mod.timeline!.goToStep(base, c) as AlgorithmSimState}
        busy={false}
        dispatch={() => {}}
      />,
    ).replace(/<!--.*?-->/g, "");

  it("module tự khai đúng tên thuật toán", () => {
    expect(mod.id).toBe("algorithm.selection_sort");
    expect(mod.title).toContain("chọn");
    expect(mod.title).not.toContain("nổi bọt");
  });

  it("KHÔNG vùng nào trên sân khấu nhắc 'nổi bọt' ở bất kỳ bước nào", () => {
    for (let c = 0; c < steps.length; c += 1) {
      expect(render(c), `bước ${c} rò tên thuật toán khác`).not.toContain("nổi bọt");
    }
  });

  it("thuyết minh của engine nói đúng cơ chế CHỌN (cực trị + đổi chỗ)", () => {
    const all = steps.map((s) => s.narration).join(" ");
    expect(all).not.toContain("nổi bọt");
    expect(all).toMatch(/nhỏ nhất|cực trị|chọn/);
  });

  it("mã giả là mã giả của sắp xếp chọn, không phải nổi bọt", () => {
    const insp = renderToString(
      <AlgorithmWorkspace config={cfg} state={base} busy={false} dispatch={() => {}} />,
    );
    expect(insp).not.toContain("cặp kề");
  });

  it("engine cho kết quả đúng và giữ đủ phần tử", () => {
    const lastStep = steps[steps.length - 1];
    expect(lastStep.snapshot.array).toEqual([...DATA.array].sort((a, b) => a - b));
    expect(lastStep.snapshot.array.length).toBe(DATA.array.length);
  });

  it("sân khấu phân biệt vùng đã sắp với vùng chưa sắp", () => {
    // ở bước giữa phải có ít nhất một phần tử đã chốt (mark "sorted")
    const mid = Math.floor(steps.length * 0.6);
    const marks = Object.values(steps[mid].snapshot.marks);
    expect(marks).toContain("sorted");
  });
});
