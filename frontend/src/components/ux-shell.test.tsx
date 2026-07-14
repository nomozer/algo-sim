import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../App";
import { offlineCatalog, publicCatalog } from "../data/offline-catalog";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest } from "../state/history";
import { useAppStore } from "../state/store";
import { LibraryView } from "./LibraryView";

/**
 * M9-UX5 — vỏ ứng dụng: header, Trang chủ, Thư viện, và luật ICON.
 *
 * LƯU Ý VỀ SSR (anti-pattern #8, ARCHITECTURE_MAP): `renderToString(<App/>)` chỉ
 * thấy TRẠNG THÁI ĐẦU — zustand v5 dùng `useSyncExternalStore`, SSR lấy
 * getServerSnapshot = initial state. Nên các test dưới đây hoặc kiểm Home (đúng
 * là trạng thái đầu), hoặc render THẲNG component với prop.
 */

registerAllSimulations();

/**
 * BẤT BIẾN M9-UX5 — KHÔNG DÙNG KÝ TỰ UNICODE LÀM ICON.
 *
 * Đã cháy một lần: `◧`/`◨` (U+25E7/25E8) không có glyph trong font hệ thống
 * Windows → hiện Ô VUÔNG RỖNG (tofu) ngay trên header. Emoji (📎 🧪) thì mỗi hệ
 * điều hành vẽ một kiểu, không ăn theo màu chữ, không chỉnh được nét.
 * Icon phải là component SVG trong `components/icons.tsx`.
 */
const FORBIDDEN_ICON_CHARS = [
  "◧", "◨", "▸", "◀", "▶", "⏮", "⏭", "⏸", "⟳", "↺",
  "✕", "＋", "⌁",
  "📎", "🧪", "🔎", "💬", "🤖",
];

describe("(M9-UX5) luật icon — không ký tự Unicode/emoji trên UI", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
  });

  it("Trang chủ không chứa ký tự icon nào (đã thay bằng SVG)", () => {
    const html = renderToString(<App />);
    for (const ch of FORBIDDEN_ICON_CHARS) {
      expect(html, `ký tự icon "${ch}" vẫn còn trên UI — phải dùng icons.tsx`).not.toContain(ch);
    }
    // và icon SVG thì phải có thật (nút gửi + tải tệp trong composer)
    expect(html).toContain("<svg");
  });

  it("Thư viện không chứa ký tự icon nào", () => {
    const html = renderToString(<LibraryView />);
    for (const ch of FORBIDDEN_ICON_CHARS) {
      expect(html, `ký tự icon "${ch}" vẫn còn trên Thư viện`).not.toContain(ch);
    }
  });
});

describe("(M9-UX5) Trang chủ KHÔNG BAO GIỜ phình theo dữ liệu", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
  });

  it("không còn nút bung cả danh mục tại chỗ (đã dời sang Thư viện)", () => {
    const html = renderToString(<App />);
    expect(html).not.toContain("Xem tất cả mô phỏng mẫu");
    expect(html).toContain("Xem thư viện");
    // gợi ý vẫn đúng 6 mẫu nổi bật (đếm CHÍNH XÁC class, không đếm biến thể
    // starter-card-body / -title / -domain)
    expect((html.match(/class="starter-card"/g) ?? []).length).toBe(6);
  });

  /**
   * Đây là lời hứa cốt lõi của M9-UX5, nên phải chứng minh bằng render THẬT.
   *
   * Không dùng `useAppStore.setState()` rồi SSR được — anti-pattern #8: zustand v5
   * SSR đọc getInitialState, tức state lúc store được TẠO. Nên phải ghi lịch sử
   * TRƯỚC khi module store khởi tạo.
   *
   * THỨ TỰ IMPORT LÀ THỨ TỰ KHỞI TẠO, và có một cái bẫy: `simulations/index` kéo
   * theo `state/store` (UI của các domain đều dùng store). Nên phải ghi lịch sử
   * XONG rồi mới import `simulations` — import sims trước là store sinh ra với
   * lịch sử RỖNG và test lại xanh/đỏ vì lý do sai.
   */
  it("học dở NHIỀU bài → Trang chủ vẫn chỉ MỘT thẻ 'Tiếp tục học'", async () => {
    vi.resetModules();

    const history = await import("../state/history");
    const catalog = await import("../data/offline-catalog");

    history.__resetHistoryForTest();
    for (const e of catalog.publicCatalog().slice(0, 5)) {
      history.historyStore.record(e.envelope, null);
    }
    expect(history.historyStore.list()).toHaveLength(5);

    // CHỈ SAU KHI đã có lịch sử mới nạp sims (kéo theo store) → initial state thấy đủ 5
    const sims = await import("../simulations");
    sims.registerAllSimulations();
    const store = await import("../state/store");
    expect(store.useAppStore.getState().history).toHaveLength(5);

    const FreshApp = (await import("../App")).default;
    const html = renderToString(<FreshApp />);

    // trước M9-UX5, 5 mục lịch sử → 5 thẻ, gợi ý bị đẩy khuất. Nay: đúng 1.
    expect((html.match(/class="session-card"/g) ?? []).length).toBe(1);
    // (SSR chèn <!-- --> giữa chuỗi và biến nên "Xem tất cả (5)" KHÔNG liền mạch)
    expect(html).toContain("Xem tất cả (");
    // và gợi ý VẪN nguyên vẹn 6 mẫu — không bị lịch sử lấn
    expect((html.match(/class="starter-card"/g) ?? []).length).toBe(6);
  });

  it("hàng chip đề mẫu AI đã gỡ — Trang chủ có ĐÚNG MỘT đường dùng AI (gõ đề)", () => {
    const html = renderToString(<App />);
    expect(html).not.toContain("prompt-chip");
    expect(html).not.toContain("Chưa biết bắt đầu từ đâu");
    // đường dùng AI duy nhất: nút gửi của composer
    expect(html).toContain("Phân tích đề bằng AI");
  });
});

describe("(M9-UX5) Thư viện — nhà riêng của danh mục đầy đủ", () => {
  it("hiện TOÀN BỘ mẫu công khai, gom nhóm theo domain", () => {
    const html = renderToString(<LibraryView />);
    const pub = publicCatalog();
    expect((html.match(/class="starter-card"/g) ?? []).length).toBe(pub.length);
    expect(html).toContain("Thư viện mô phỏng");
    // (chữ hoa là do CSS text-transform; DOM giữ nguyên tiếng Việt có dấu)
    expect(html).toContain("Thuật toán");
    expect(html).toContain("Nhị phân");
  });

  it("KHÔNG rò fixture nội bộ hay chuỗi kĩ thuật (luật phạm vi M9-UX2/UX3)", () => {
    const html = renderToString(<LibraryView />);
    expect(offlineCatalog().length).toBeGreaterThan(publicCatalog().length);
    expect(html).not.toContain("tam giác");
    expect(html).not.toContain("(tổng quát)");
    expect(html).not.toContain("algorithm.");
    expect(html).not.toContain("generic.rule_scene");
  });
});

describe("(M9-UX5) AI thôi ngang hàng với mô phỏng (R0 phản chiếu lên UI)", () => {
  it("store: aiOpen mặc định ĐÓNG — không còn tab [Quan sát][Hỏi AI]", () => {
    useAppStore.getState().reset();
    expect(useAppStore.getState().aiOpen).toBe(false);
    // cặp tab cũ đã biến mất khỏi hợp đồng store
    expect("inspectorTab" in useAppStore.getState()).toBe(false);
  });

  it("header có mục Thư viện; điều hướng là link chữ, không phải nút pill", () => {
    const html = renderToString(<App />);
    expect(html).toContain("nav-link");
    expect(html).toContain("Thư viện");
    expect(html).toContain("Lịch sử");
  });
});
