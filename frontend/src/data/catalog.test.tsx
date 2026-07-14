import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../App";
import { SamplePreview, previewKindOf } from "../components/SamplePreview";
import { makeAlgorithmModule } from "../simulations/domains/algorithm";
import { makeAndGateModule } from "../simulations/domains/logic";
import { makeBinaryModule } from "../simulations/domains/binary";
import { makeNetworkModule } from "../simulations/domains/network";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest } from "../state/history";
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
    // 8 algorithm + logic + binary + network + web = 12 mẫu công khai
    expect(pub).toHaveLength(12);
    expect(ids).toContain("gen-web"); // HTML/CSS là chương trình Tin học (T12 CĐ4)
  });

  it("(3) fixture nội bộ VẪN trong offlineCatalog đầy đủ (test/dev dùng được)", () => {
    const all = offlineCatalog();
    expect(all.map((e) => e.id)).toContain("gen-reveal");
    expect(all).toHaveLength(16);
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
    expect(previewKindOf("algorithm.find_min")).toBe("algorithm-bars");
    expect(previewKindOf("algorithm.binary_search")).toBe("search-range");
    expect(previewKindOf("algorithm.linear_search")).toBe("search-range");
    expect(previewKindOf("algorithm.bubble_sort")).toBe("sort-swap");
    expect(previewKindOf("algorithm.insertion_sort")).toBe("sort-swap");
    expect(previewKindOf("algorithm.sum_if")).toBe("algorithm-bars");
    expect(previewKindOf("binary.decimal_to_binary")).toBe("binary-bits");
    expect(previewKindOf("network.packet_routing")).toBe("network-path");
    expect(previewKindOf("logic.and_gate")).toBe("logic-gate");
  });

  it("id lạ → fallback 'generic' và VẪN render được (không ném)", () => {
    expect(previewKindOf("future.unknown_module")).toBe("generic");
    const html = renderToString(<SamplePreview kind="generic" />);
    expect(html).toContain("<svg");
  });

  it("mọi kind đều là SVG tĩnh thuần trình bày (không fetch, không engine)", () => {
    for (const kind of [
      "algorithm-bars",
      "search-range",
      "sort-swap",
      "binary-bits",
      "network-path",
      "logic-gate",
      "web-structure",
      "generic",
    ] as const) {
      const html = renderToString(<SamplePreview kind={kind} />);
      expect(html).toContain("<svg");
    }
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
