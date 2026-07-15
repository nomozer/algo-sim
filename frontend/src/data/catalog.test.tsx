import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../App";
import { SamplePreview, previewKindOf } from "../components/SamplePreview";
import { makeAlgorithmModule } from "../simulations/domains/algorithm";
import { makeAndGateModule } from "../simulations/domains/logic";
import { makeBinaryModule } from "../simulations/domains/binary";
import { makeNetworkModule } from "../simulations/domains/network";
import { progressOf, SessionCard } from "../components/SessionCard";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest, historyStore, type HistoryItem } from "../state/history";
import { useAppStore } from "../state/store";
import { offlineCatalog, publicCatalog, starterEntries } from "./offline-catalog";
import { OFFLINE_SAMPLES } from "./sim-samples";

/**
 * M9-UX2 — DANH MỤC CÔNG KHAI ↔ FIXTURE NỘI BỘ + preview + gỡ thẻ Ứng dụng.
 *
 * Luật phạm vi luận văn: KIẾN TRÚC được phép tổng quát, nhưng TRẢI NGHIỆM HỌC
 * công khai khoanh trong Tin học THPT. Ví dụ liên miền (tam giác) ở lại làm
 * fixture nội bộ — không xoá năng lực, không quảng bá cho học sinh.
 * Phân loại bằng METADATA TƯỜNG MINH (visibility) — CẤM lọc theo chuỗi tiêu đề.
 */

registerAllSimulations();

describe("(1)(2)(5)(6) visibility — metadata tường minh, không lọc tiêu đề", () => {
  it("mẫu liên miền/fixture khai visibility='internal_fixture' NGAY TẠI ĐỊNH NGHĨA", () => {
    const byId = Object.fromEntries(OFFLINE_SAMPLES.map((s) => [s.id, s]));
    for (const id of ["gen-reveal", "gen-and", "gen-binary", "gen-packet"]) {
      expect(byId[id]?.visibility).toBe("internal_fixture");
    }
    // không khai → mặc định public (không suy từ tiêu đề)
    expect(byId["logic-and"]?.visibility).toBeUndefined();
  });

  it("publicCatalog: chỉ mẫu Tin học THPT; KHÔNG chứa fixture nội bộ", () => {
    const pub = publicCatalog();
    expect(pub.every((e) => e.visibility === "public")).toBe(true);
    const ids = pub.map((e) => e.id);
    expect(ids).not.toContain("gen-reveal");
    expect(ids).not.toContain("gen-and");
    expect(ids).not.toContain("gen-binary");
    expect(ids).not.toContain("gen-packet");
    // 8 algorithm + logic + binary + network(x2) + web = 13 mẫu công khai
    expect(pub).toHaveLength(13);
    expect(ids).toContain("gen-web"); // HTML/CSS là chương trình Tin học (T12 CĐ4)
    expect(ids).toContain("network-encapsulation"); // M10 flagship (Thư viện)
  });

  it("(3) fixture nội bộ VẪN trong offlineCatalog đầy đủ (test/dev dùng được)", () => {
    const all = offlineCatalog();
    expect(all.map((e) => e.id)).toContain("gen-reveal");
    expect(all).toHaveLength(17);
    const reveal = all.find((e) => e.id === "gen-reveal")!;
    expect(reveal.visibility).toBe("internal_fixture");
    expect(reveal.envelope.simulation_id).toBe("generic.rule_scene");
  });

  it("starterEntries ⊆ public, 6 mẫu nổi bật đúng thứ tự ưu tiên", () => {
    const starters = starterEntries();
    expect(starters.every((e) => e.visibility === "public")).toBe(true);
    expect(starters.map((e) => e.simId)).toEqual([
      "algorithm.find_max",
      "algorithm.binary_search",
      "algorithm.bubble_sort",
      "binary.decimal_to_binary",
      "network.packet_routing",
      "logic.and_gate",
    ]);
  });
});

describe("(7) lịch sử KHÔNG hỏng khi mẫu rời danh mục công khai", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
  });

  it("envelope đã validate của fixture nội bộ vẫn mở lại được (zero-AI)", () => {
    const reveal = offlineCatalog().find((e) => e.id === "gen-reveal")!;
    const store = () => useAppStore.getState();
    // như một phiên học cũ đã lưu
    store().loadEnvelope(reveal.envelope, reveal.id);
    expect(store().active).not.toBeNull();
    store().goHome();
    expect(store().history).toHaveLength(1);
    // mẫu không còn public — nhưng lịch sử mở lại bằng envelope, không qua catalog
    expect(publicCatalog().some((e) => e.id === "gen-reveal")).toBe(false);
    store().reopenFromHistory(store().history[0].id);
    expect(store().active!.moduleId).toBe("generic.rule_scene");
    expect(store().view).toBe("workspace");
  });
});

describe("(8)(9) thẻ 'Ứng dụng của cơ chế này' đã gỡ + metadata chết đã dọn", () => {
  it("module không còn khai applications (metadata chỉ nuôi thẻ đó — đã dọn sạch)", () => {
    // field đã bị gỡ khỏi HỢP ĐỒNG (types.ts) nên phải truy cập kiểu unknown
    const modules: Record<string, unknown>[] = [
      makeAlgorithmModule("find_max") as unknown as Record<string, unknown>,
      makeAndGateModule() as unknown as Record<string, unknown>,
      makeBinaryModule() as unknown as Record<string, unknown>,
      makeNetworkModule() as unknown as Record<string, unknown>,
    ];
    for (const mod of modules) expect(mod.applications).toBeUndefined();
  });
});

describe("(12)(13)(14) preview — kiến trúc nhẹ, theo định danh, fallback an toàn", () => {
  it("previewKindOf suy từ simulation id/metadata — đủ các mẫu nổi bật", () => {
    expect(previewKindOf("algorithm.find_max")).toBe("algorithm-bars");
    expect(previewKindOf("algorithm.find_min")).toBe("bars-min");
    expect(previewKindOf("algorithm.sum_if")).toBe("sum-threshold");
    expect(previewKindOf("algorithm.count_if")).toBe("count-threshold");
    expect(previewKindOf("algorithm.linear_search")).toBe("linear-scan");
    expect(previewKindOf("algorithm.binary_search")).toBe("search-range");
    expect(previewKindOf("algorithm.bubble_sort")).toBe("sort-swap");
    expect(previewKindOf("algorithm.insertion_sort")).toBe("insertion-lift");
    expect(previewKindOf("binary.decimal_to_binary")).toBe("binary-bits");
    expect(previewKindOf("network.packet_routing")).toBe("network-path");
    expect(previewKindOf("network.protocol_encapsulation")).toBe("network-encapsulation");
    expect(previewKindOf("logic.and_gate")).toBe("logic-gate");
  });

  /**
   * M9-UX3 — BẤT BIẾN CHỐNG TÁI PHÁT.
   *
   * Trước M9-UX3, 8 bài thuật toán chen vào 3 tranh. Hệ quả KHÔNG phải "xấu" mà
   * là DẠY SAI: linear_search mượn tranh trái/giữa/phải của binary_search (tìm
   * tuần tự không có mid); insertion_sort mượn mũi tên ĐỔI CHỖ của bubble_sort
   * (chèn là DỜI, không đổi chỗ) — trong khi decision.ts (M9-S1) hỏi học sinh
   * hai câu khác hẳn nhau. Vi phạm nguyên tắc sư phạm #6 (COVERAGE §2.6): mọi
   * thứ trực quan phải chạm ĐÚNG cơ chế ẩn của chính bài đó.
   *
   * Test này khoá lại: một tranh = một cơ chế = một bài.
   */
  it("KHÔNG hai bài thuật toán nào dùng chung một tranh (mỗi cơ chế một tranh)", () => {
    const algoIds = [
      "algorithm.find_max",
      "algorithm.find_min",
      "algorithm.sum_if",
      "algorithm.count_if",
      "algorithm.linear_search",
      "algorithm.binary_search",
      "algorithm.bubble_sort",
      "algorithm.insertion_sort",
    ];
    const kinds = algoIds.map((id) => previewKindOf(id));
    expect(new Set(kinds).size).toBe(algoIds.length);
    // và không bài nào rơi vào fallback (fallback = "chưa có tranh của mình")
    expect(kinds).not.toContain("generic");
  });

  it("id lạ → fallback 'generic' và VẪN render được (không ném)", () => {
    expect(previewKindOf("future.unknown_module")).toBe("generic");
    const html = renderToString(<SamplePreview kind="generic" />);
    expect(html).toContain("<svg");
  });

  it("mọi kind đều là SVG tĩnh thuần trình bày (không fetch, không engine)", () => {
    for (const kind of [
      "algorithm-bars",
      "bars-min",
      "sum-threshold",
      "count-threshold",
      "linear-scan",
      "search-range",
      "sort-swap",
      "insertion-lift",
      "binary-bits",
      "network-path",
      "network-encapsulation",
      "logic-gate",
      "web-structure",
      "generic",
    ] as const) {
      const html = renderToString(<SamplePreview kind={kind} />);
      expect(html).toContain("<svg");
    }
  });
});

/**
 * M9-UX7 — `InputPanel` (panel trái workspace) ĐÃ GỠ HẲN: sau khi có trang Thư
 * viện, danh mục tồn tại ở ba nơi và panel trái là bản sao thứ ba.
 *
 * Hai test của nó (chỉ mẫu công khai · không lộ simulation_id) KHÔNG mất độ phủ:
 * - "chỉ mẫu công khai" nay do `ux-shell.test.tsx` kiểm trên `LibraryView`;
 * - "không lộ chuỗi kĩ thuật" nay do `ui-hygiene.test.ts` QUÉT MÃ NGUỒN — mạnh hơn
 *   hẳn, vì nó soi mọi component chứ không chỉ component có test đi qua.
 */

/**
 * M9-UX4 — CHUỖI KĨ THUẬT KHÔNG BAO GIỜ LÊN UI HỌC SINH.
 * `HistoryView` từng render thẳng `{item.simulationId}` → học sinh thấy
 * `algorithm.bubble_sort` trên trang Lịch sử. Cùng loại rò rỉ đã vá ở InputPanel
 * (M9-UX3) nhưng còn sót ở đây — vá nốt và khoá lại.
 */
/**
 * CẢNH BÁO CHO NGƯỜI VIẾT TEST SAU: `renderToString(<App/>)` KHÔNG thấy state đã
 * mutate. Zustand v5 dùng `useSyncExternalStore`, và khi SSR React lấy
 * getServerSnapshot = **initial state**. Vì vậy mọi test SSR trong repo này chỉ
 * hợp lệ ở trạng thái ĐẦU (Home). Muốn kiểm một view có dữ liệu thì render thẳng
 * COMPONENT với prop (SessionCard là hàm thuần theo `item`) — đừng đi qua App,
 * nếu không test sẽ xanh vì lý do sai (vd "Thuật toán" khớp nhầm nhãn ở starter
 * card của Home chứ không phải thẻ lịch sử).
 */
function historyItemFor(simId: string): HistoryItem {
  const entry = offlineCatalog().find((e) => e.simId === simId)!;
  __resetHistoryForTest();
  return historyStore.record(entry.envelope, null);
}

describe("(M9-UX4) SessionCard — thẻ chung Home + Lịch sử, có tiến độ, không rò id", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
  });

  it("KHÔNG in simulation_id ra UI; hiện nhãn tiếng Việt + tiến độ từ engine", () => {
    const item = historyItemFor("algorithm.bubble_sort");
    const html = renderToString(<SessionCard item={item} onOpen={() => {}} />);

    // rò rỉ cũ: HistoryView render thẳng {item.simulationId}
    expect(html).not.toContain("algorithm.bubble_sort");
    expect(html).not.toContain("algorithm.");
    expect(html).toContain("Thuật toán");
    // tiến độ SUY TỪ ENGINE TẤT ĐỊNH — không persist trong localStorage.
    // (Assert bằng ARIA, không bằng chuỗi hiển thị: SSR chèn <!-- --> giữa các
    // text node nên "bước 1 / 40" không bao giờ liền mạch trong HTML.)
    expect(html).toContain("progressbar");
    expect(html).toContain('aria-valuenow="1"');
    expect(html).toContain('aria-valuemax="40"');
  });

  it("progressOf: module khai timeline → có tiến độ; đúng tổng bước của engine", () => {
    const item = historyItemFor("algorithm.bubble_sort");
    expect(progressOf(item)).toEqual({ cursor: 0, total: 40 });
  });

  it("module KHÔNG khai timeline (exploratory) → KHÔNG có tiến độ, không bịa '1 bước'", () => {
    const item = historyItemFor("logic.and_gate");
    expect(progressOf(item)).toBeNull();

    const html = renderToString(<SessionCard item={item} onOpen={() => {}} />);
    expect(html).toContain("Cổng logic AND");
    expect(html).toContain("Lôgic");
    expect(html).not.toContain("progressbar");
  });

  it("nút xóa chỉ hiện khi có onRemove (Home không xóa, Lịch sử có)", () => {
    const item = historyItemFor("algorithm.bubble_sort");
    expect(renderToString(<SessionCard item={item} onOpen={() => {}} />)).not.toContain(
      "session-remove",
    );
    expect(
      renderToString(<SessionCard item={item} onOpen={() => {}} onRemove={() => {}} />),
    ).toContain("session-remove");
  });
});

describe("(11)(15)(17) Home SSR — preview hiện, fixture nội bộ vắng, 0 network", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
  });

  it("starter cards mang preview trực quan; KHÔNG có mẫu tam giác trên Home", () => {
    const html = renderToString(<App />);
    expect(html).toContain("Em muốn khám phá bài toán nào?");
    expect(html).toContain("sample-preview");
    expect((html.match(/sample-preview/g) ?? []).length).toBeGreaterThanOrEqual(6);
    // đầu ra công khai không quảng bá fixture liên miền
    expect(html).not.toContain("tam giác");
    expect(html).not.toContain("(tổng quát)");
    // (17) chưa có lịch sử → Home vẫn hữu ích, không mục rỗng
    expect(html).not.toContain("Tiếp tục học");
  });
});
