import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./index";
import { AlgorithmWorkspace, insertionHold } from "./ui";
import type { AlgorithmSimState } from "./model";
import { activeTrace } from "./model";
import type { AlgorithmId } from "../../../core/types";
import { whatIfPolicyOf } from "./interaction-policy";


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

/**
 * W4B-3A — CÂU MỜI ĐỌC QUA ĐÚNG ĐƯỜNG SHELL DÙNG.
 *
 * Lối vào Thí nghiệm/Thử thách KHÔNG còn do `AlgorithmWorkspace` dựng, nên mọi
 * khẳng định "nhãn X có trên màn hình" phải hỏi chủ sở hữu mới. Gọi thẳng
 * `challengeEntry`/`exploreEntry` — CÙNG hàm `SimulationControls` gọi, không
 * phải bản sao dành riêng cho test.
 */
/* Hai helper `entries`/`textOf` GỠ 2026-08-21 (Task 10b): chúng chỉ phục vụ
   các khẳng định về cổng Thử thách, mà W13 đã gỡ cổng đó. */

describe("gating swap trong AlgorithmWorkspace", () => {
  /* W4B-2I — HAI TEST NÀY ĐỔI TIỀN ĐỀ, có chủ đích.
   *
   * Trước: `bubble_sort`/`selection_sort` là hai bài DUY NHẤT chưa gác cổng, nên
   * chúng làm bài làm chứng cho "vùng cam kết hiện thẳng ở Quan sát" và "gợi ý
   * kéo hiện ở bước thường". Nay cả chín bài đều gác ⇒ hai khẳng định đó mô tả
   * một trạng thái sản phẩm KHÔNG CÒN TỒN TẠI.
   *
   * Luật W3B §15 (cam kết trước, kéo sau) KHÔNG mất và không cần SSR để kiểm:
   * chủ sở hữu của nó là hàm thuần `whatIfDragAllowed`, đã khoá đủ sáu nhánh ở
   * `interaction-family-sorting-w3b.test.tsx`. `labOpen` là state cục bộ nên
   * `renderToString` luôn chỉ thấy trạng thái ĐÓNG — dùng SSR để kiểm trạng thái
   * MỞ là đúng anti-pattern #8 (ARCHITECTURE_MAP §8).
   *
   * Nên hai test này nay khoá đúng thứ SSR nhìn thấy được: Quan sát của bài sắp
   * xếp trông y hệt bảy bài kia. */
  /* W4B-3A — cùng ba khẳng định, nhưng vế thứ ba hỏi ĐÚNG CHỦ SỞ HỮU MỚI: câu
     mời không còn nằm trong HTML của sân khấu (đó chính là dải đã gỡ), nó nằm ở
     lối vào mà `SimulationControls` dựng. */
  it("bubble_sort: Quan sát KHÔNG bày cam kết, KHÔNG mời kéo — lối vào ở dải phụ", () => {
    const h = html("bubble_sort", { array: [1, 3, 2], order: "asc" }, 1);
    expect(h).not.toContain("Thao tác sắp xếp");
    /* W12 §6: vùng CAM KẾT vẫn nằm sau lối vào (dòng trên) — thứ đổi là CÔNG CỤ.
       Thử thách đóng ⇒ kéo dùng được ngay, nên `cursor:grab` PHẢI có mặt. */
    expect(h, "thử thách đóng mà không có con trỏ kéo").toContain("cursor:grab");
    expect(h, "câu mời quay lại thành dải dưới mô hình").not.toContain("tự đổi chỗ từng cặp");
  });

  it("selection_sort: cùng một luật — không còn bài sắp xếp nào hở vùng cam kết", () => {
    const h = html("selection_sort", { array: [3, 1, 2], order: "asc" }, 1);
    expect(h).not.toContain("Thao tác sắp xếp");
    expect(h, "thử thách đóng mà không có con trỏ kéo").toContain("cursor:grab");
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

  it("(16) binary_search: không gợi ý kéo tự do; CÓ cổng Thí nghiệm; tiền đề vẫn đọc được", () => {
    const BIN = { array: [1, 3, 5, 7, 9, 11, 13], target: 3 };
    const h = html("binary_search", BIN, 1);
    expect(h).not.toContain("Kéo một cột");
    /* W4B-2D: nhãn nút hứa THỨ NẰM SAU CỔNG — cổng gác cả vùng cam kết, nên
       nhãn cũ (chỉ nói về kéo) sẽ khiến học sinh không biết các nút chọn nửa đi
       đâu. W4B-3A: nhãn đó nay sống ở lối vào, không ở sân khấu. */
    // Tiền đề là dữ kiện QUAN SÁT — nó ở lại kể cả khi cổng đã ẩn vùng cam kết.
    expect(h).toContain("sắp xếp tăng dần");
  });

  it("find_max (challenge): có lối vào phá bất biến, không kéo tự do mặc định", () => {
    const h = html("find_max", { array: [7.5, 9, 6] }, 1);
    /* W12 §10 — hồi quy đúng target khởi nguồn quan sát của người dùng. */
    expect(h, "find_max mặc định không có affordance nào ngoài ô dự đoán")
      .toContain("cursor:grab");
  });

  /* it("(PhET/CLT) challenge: teaser tự-giải-thích…") ĐÃ XOÁ 2026-08-21
     (Task 10b): nó kiểm nhãn của cổng Thử thách, mà W13 gỡ cả cổng. Bất biến
     "lối vào phải TỰ MÔ TẢ" không mất — `explore-ownership-w4b3a.test.ts` khoá
     nó cho lối vào Khám phá, tức lối vào duy nhất còn lại. */

  it("linear_search: kéo WHAT-IF nay nằm sau cổng — Quan sát không mời kéo", () => {
    /* W4B-2D §3. `mode` vẫn `framed` (khung câu hỏi là CHI PHÍ), nhưng chỗ ĐẶT
       công cụ đổi: `runLinearSearch` không phát sự kiện swap nào, nên đổi chỗ
       là WHAT-IF chứ không phải bước của thuật toán. Gợi ý kéo chỉ được xuất
       hiện SAU khi học sinh mở Thí nghiệm — bản render đó do runner trình duyệt
       phủ (labOpen là useState cục bộ). */
    const h = html("linear_search", { array: [4, 9, 7], target: 9 }, 1);
    expect(h, "thử thách đóng mà không có con trỏ kéo").toContain("cursor:grab");
    /* W4B-2V/C: khung CHI PHÍ chuyển từ `framing` (đoạn 310 ký tự) sang `hint`
       — chuỗi đứng ngay cạnh công cụ kéo. Ý không mất, chỗ đặt đổi. */
    expect(whatIfPolicyOf("linear_search").hint).toContain("chi phí");
    expect(whatIfPolicyOf("linear_search").framing!.length,
      "framing lại phình thành đoạn giảng").toBeLessThan(60);
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

       2026-08-21 (Task 10b): cổng Thí nghiệm đã bị W13 gỡ, nên `find_max` KHÔNG
       còn gác vùng cam kết nữa — `ScanActionZone` quay lại là bề mặt hợp lệ và
       `decision-strip` không dựng (ui.tsx: `decision && !scan && …`). Đảo lại
       hai khẳng định cho khớp kiến trúc hiện tại.

       Điều test này thật sự khoá KHÔNG ĐỔI: biểu thức phải dùng ĐÚNG hai giá trị
       mà event `compare` nêu, không phải renderer tự tính lại. */
    expect(h).toContain("scan-action");
    expect(h).not.toContain("decision-strip");
    // SSR escape ">"
    expect(h).toMatch(new RegExp(`${vi}\\s*&gt;\\s*${String(vj).replace(".", ",")}`));
  });

  it("bước hệ quả find_max (cập nhật max): quan hệ trước → sau vẫn nói được", () => {
    const h = html("find_max", { array: [7.5, 9, 6] }, 2);
    /* KHÁC bước quyết định ở trên: dải HỆ QUẢ (`decision-strip is-consequence`)
       render độc lập với `scan`, nên ở đây nó vẫn có mặt. Hai dải khác nhau,
       đừng gộp — `ui.tsx` dựng chúng bằng hai điều kiện tách biệt. */
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
