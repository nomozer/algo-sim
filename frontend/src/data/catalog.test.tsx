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
import {
  discoverableCatalog, offlineCatalog, publicCatalog, starterEntries,
  FOCUS_SIM_IDS, PRODUCT_DOMAINS,
} from "./offline-catalog";
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

  it("publicCatalog: CHỈ hình học; không fixture nội bộ, không di sản Tin học", () => {
    /* HỢP ĐỒNG MỚI (2026-08-31, dọn phạm vi sản phẩm). Bản cũ khẳng định
       "danh mục công khai ⊆ 13 target tiêu điểm Tin học" — đúng với đề cũ, và
       nay chính là thứ phải KHÔNG còn đúng. Không nới khẳng định: đổi hẳn
       đối tượng nó nói về, rồi khoá chặt hơn ở chiều ngược lại. */
    const pub = publicCatalog();
    expect(pub.length, "bề mặt công khai trống ⇒ mọi khẳng định dưới đây vô nghĩa")
      .toBeGreaterThan(0);
    expect(pub.every((e) => e.visibility === "public")).toBe(true);

    for (const e of pub) {
      expect(PRODUCT_DOMAINS, `${e.id}: miền ngoài sản phẩm lọt lên bề mặt`)
        .toContain(e.domain);
    }

    const ids = pub.map((e) => e.id);
    for (const cam of ["gen-reveal", "gen-and", "gen-binary", "gen-packet",
                       "web-intro-page", "gen-web", "gen-rule-library",
                       "network-encapsulation"]) {
      expect(ids, `${cam}: fixture/di sản lọt vào bề mặt công khai`).not.toContain(cam);
    }

    /* Chiều NGƯỢC lại mới là chiều dễ trôi: một mẫu Tin học bất kỳ quay lại
       bề mặt. Khẳng định theo MIỀN nên nó bắt cả mẫu chưa tồn tại. */
    const miềnLạ = pub.filter((e) => e.domain !== "geometry");
    expect(miềnLạ.map((e) => e.id), "mẫu ngoài hình học quay lại bề mặt")
      .toEqual([]);
  });

  it("mẫu Tin học VẪN sống — de-expose, không delete", () => {
    /* Ranh giới của wave dọn phạm vi: bề mặt hẹp lại, RUNTIME không đổi. Mất
       khẳng định này thì lần dọn sau sẽ xoá thật mà không ai thấy — cùng lúc
       làm hỏng Lịch sử và bài giáo viên đã giao (chúng giữ envelope của các
       miền ấy). */
    const all = offlineCatalog();
    for (const id of ["web-intro-page", "network-encapsulation"]) {
      expect(all.map((e) => e.id), `${id} biến mất khỏi runtime`).toContain(id);
    }
    const disc = discoverableCatalog().map((e) => e.simId);
    expect(disc.length).toBeGreaterThan(publicCatalog().length);
    for (const simId of FOCUS_SIM_IDS.slice(0, 3)) {
      expect(disc, `${simId}: target tiêu điểm cũ mất mẫu công khai`).toContain(simId);
    }
  });

  it("(3) fixture nội bộ VẪN trong offlineCatalog đầy đủ (test/dev dùng được)", () => {
    const all = offlineCatalog();
    expect(all.map((e) => e.id)).toContain("gen-reveal");
    expect(all).toHaveLength(offlineCatalog().length);
    const reveal = all.find((e) => e.id === "gen-reveal")!;
    expect(reveal.visibility).toBe("internal_fixture");
    expect(reveal.envelope.simulation_id).toBe("generic.rule_scene");
  });

  it("starterEntries ⊆ public — ba bài hình học, đúng thứ tự ưu tiên", () => {
    const starters = starterEntries();
    expect(starters.every((e) => e.visibility === "public")).toBe(true);
    /* Chọn theo ID MẪU chứ không theo `simId`: mọi bài hình học dùng chung
       `generic.semantic_program`, nên lọc theo `simId` hoặc lấy hết hoặc không
       lấy gì. Khoá luôn thứ tự — nó là thứ tự sư phạm, không phải ngẫu nhiên. */
    expect(starters.map((e) => e.id)).toEqual([
      "thiet-dien-chop",   // thiết diện — hoạt động trung tâm
      "vuong-goc-chop",    // quan hệ vuông góc
      "the-tich-chop",     // thể tích
    ]);
    const pubIds = new Set(publicCatalog().map((e) => e.id));
    for (const e of starters) {
      expect(pubIds, `${e.id}: bài gợi ý không có trong danh mục công khai`)
        .toContain(e.id);
    }
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
    expect(html).toContain("Em muốn dựng hình nào?");
    expect(html).toContain("sample-preview");
    /* Đếm theo THẺ, không theo lớp `sample-preview` (lớp ấy xuất hiện hai lần
       mỗi thẻ, nên bản cũ `>= 6` thật ra đang nói "ít nhất ba thẻ" mà đọc như
       "ít nhất sáu"). Ba thẻ là con số THẬT của bề mặt hình học — bám số thật
       chứ không để một ngưỡng lỏng rồi nới dần. */
    expect((html.match(/class="starter-card"/g) ?? []).length).toBe(3);
    // đầu ra công khai không quảng bá fixture liên miền
    expect(html).not.toContain("tam giác");
    expect(html).not.toContain("(tổng quát)");
    /* Không một nhãn miền Tin học nào lọt lên Trang chủ. */
    for (const cam of ["Thuật toán", "Nhị phân", "Mạng", "CSDL", "Lôgic"]) {
      expect(html, `${cam}: nhãn miền cũ còn trên Trang chủ`).not.toContain(cam);
    }
    // (17) chưa có lịch sử → Home vẫn hữu ích, không mục rỗng
    expect(html).not.toContain("Tiếp tục học");
  });
});
