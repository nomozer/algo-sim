import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../App";
import { itemsForRole } from "./TopNav";
import { offlineCatalog, publicCatalog } from "../data/offline-catalog";

/** Số thẻ gợi ý trên Trang chủ = 4 mẫu hình học chuẩn Axo V2.7 (`STARTER_SAMPLE_IDS`). */
const SO_GOI_Y = 4;
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest } from "../state/history";
import { useAppStore } from "../state/store";
import { LibraryView } from "./LibraryView";
import { SimulationInspector } from "./SimulationInspector";

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

describe("luật icon — không ký tự Unicode/emoji trên UI", () => {
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

describe("Trang chủ KHÔNG BAO GIỜ phình theo dữ liệu", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
  });

  it("không còn nút bung cả danh mục tại chỗ (đã dời sang Thư viện)", () => {
    const html = renderToString(<App />);
    expect(html).not.toContain("Xem tất cả mô phỏng mẫu");
    expect(html).toContain("Xem tất cả thư viện");
    // gợi ý vẫn đúng 4 mẫu chuẩn Axo V2.7 (đếm CHÍNH XÁC class)
    expect((html.match(/class="starter-card"/g) ?? []).length).toBe(SO_GOI_Y);
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
    const muc = catalog.discoverableCatalog();
    expect(muc.length).toBeGreaterThan(1);
    for (const e of muc) history.historyStore.record(e.envelope, null);
    expect(history.historyStore.list()).toHaveLength(muc.length);

    // CHỈ SAU KHI đã có lịch sử mới nạp sims (kéo theo store) → initial state thấy đủ
    const sims = await import("../simulations");
    sims.registerAllSimulations();
    const store = await import("../state/store");
    expect(store.useAppStore.getState().history).toHaveLength(muc.length);

    const FreshApp = (await import("../App")).default;
    const html = renderToString(<FreshApp />);

    // Đúng 1 thẻ Tiếp tục học (.resume-home-card) theo chuẩn Axo V2.7
    expect((html.match(/class="resume-home-card"/g) ?? []).length).toBe(1);
    expect(html).toContain("Tiếp tục học");
    expect(html).toContain("Xem lịch sử →");
    // và gợi ý VẪN nguyên vẹn 4 mẫu chuẩn Axo V2.7 — không bị lịch sử lấn
    expect((html.match(/class="starter-card"/g) ?? []).length).toBe(SO_GOI_Y);
  });

  it("hàng chip đề mẫu AI đã gỡ — Trang chủ có ĐÚNG MỘT đường dùng AI (gõ đề)", () => {
    const html = renderToString(<App />);
    expect(html).not.toContain("prompt-chip");
    expect(html).not.toContain("Chưa biết bắt đầu từ đâu");
    // đường dùng AI duy nhất: nút gửi của composer
    expect(html).toContain("Phân tích đề bằng AI");
  });
});

describe("Thư viện — nhà riêng của danh mục đầy đủ", () => {
  it("hiện TOÀN BỘ mẫu công khai, gom nhóm theo domain", () => {
    const html = renderToString(<LibraryView />);
    const pub = publicCatalog();
    expect((html.match(/class="lib-card"/g) ?? []).length).toBe(pub.length);
    expect(html).toContain("Thư viện mô phỏng");
    expect(html).toContain("Hình chóp");
    expect(html).toContain("Mặt cầu");
    expect(html).toContain("Hình trụ");
    expect(html).toContain("Hình nón");
    /* Dọn phạm vi sản phẩm — Thư viện chỉ còn nhóm Hình học. Khẳng định cả
       chiều VẮNG MẶT: một nhãn miền cũ hiện lại là dấu bề mặt trôi ngược. */
    for (const cam of ["Thuật toán", "Nhị phân", "Mạng", "CSDL", "Lôgic", "Web"]) {
      expect(html, `${cam}: nhóm miền cũ quay lại Thư viện`).not.toContain(cam);
    }
  });

  it("KHÔNG rò fixture nội bộ hay chuỗi kĩ thuật (luật phạm vi M9-UX2/UX3)", () => {
    const html = renderToString(<LibraryView />);
    expect(offlineCatalog().length).toBe(publicCatalog().length);
    expect(html).not.toContain("Tam giác (tổng quát)");
    expect(html).not.toContain("(tổng quát)");
    expect(html).not.toContain("algorithm.");
    expect(html).not.toContain("generic.rule_scene");
  });
});

/**
 * AI RA HẲN KHỎI WORKSPACE — render THẬT, không chỉ quét mã nguồn.
 */
describe("Panel Giải thích không còn control AI nào", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
  });

  it('không còn "Hỏi AI về bước này" trong panel Giải thích', () => {
    const html = renderToString(<SimulationInspector />);
    expect(html).not.toContain("Hỏi AI");
    expect(html).not.toContain("ai-toggle");
    expect(html).not.toContain("ai-section");
    expect(html).not.toContain("aria-expanded");
  });

  it("panel Giải thích vẫn render bình thường (tiêu đề + chỗ cho Inspector)", () => {
    const html = renderToString(<SimulationInspector />);
    expect(html).toContain("GIẢI THÍCH");
    expect(html).toContain("Chưa có mô phỏng nào đang chạy.");
  });

  it("Trang chủ VẪN giữ đường phân tích đề bằng AI", () => {
    const html = renderToString(<App />);
    expect(html).toContain("Phân tích đề bằng AI");
  });
});

describe("AI thôi ngang hàng với mô phỏng (R0 phản chiếu lên UI)", () => {
  it("store: aiOpen mặc định ĐÓNG — không còn tab [Quan sát][Hỏi AI]", () => {
    useAppStore.getState().reset();
    expect(useAppStore.getState().aiOpen).toBe(false);
    // cặp tab cũ đã biến mất khỏi hợp đồng store
    expect("inspectorTab" in useAppStore.getState()).toBe(false);
  });

  it("store: rightOpen mặc định ĐÓNG, và không đọc bề rộng cửa sổ nữa", () => {
    expect(useAppStore.getInitialState().rightOpen).toBe(false);

    const src = readFileSync(new URL("../state/store.ts", import.meta.url), "utf-8")
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/^\s*\/\/.*$/gm, "");
    expect(src).not.toMatch(/window\.innerWidth/);
    expect(src).toMatch(/rightOpen:\s*false/);
  });

  it("panel vẫn MỞ ĐƯỢC — đóng mặc định là điểm khởi đầu, không phải gỡ bỏ", () => {
    useAppStore.setState({ rightOpen: useAppStore.getInitialState().rightOpen });
    useAppStore.getState().toggleRight();
    expect(useAppStore.getState().rightOpen).toBe(true);
    useAppStore.getState().toggleRight();
    expect(useAppStore.getState().rightOpen).toBe(false);
  });

  it("CHƯA đăng nhập: header chuẩn Axo V2.7 với capsule 3 mục (Trang chủ, Thư viện, Lịch sử) và nút Đăng nhập / Đăng ký", () => {
    const html = renderToString(<App />);
    expect(html).toContain("nav-link");
    expect(html).toContain("nav-n1-capsule");
    expect(html).toContain("Trang chủ");
    expect(html).toContain("Thư viện");
    expect(html).toContain("Lịch sử");
    expect(html).toContain("Đăng nhập");
    expect(html).toContain("Đăng ký");
  });

  it("ĐÃ đăng nhập: capsule điều hướng nhất quán đúng 3 mục (Trang chủ, Thư viện, Lịch sử) theo chuẩn Axo V2.7 (P3)", () => {
    for (const role of ["student", "teacher"] as const) {
      const labels = itemsForRole(role).map((i) => i.label);
      expect(labels).toEqual(["Trang chủ", "Thư viện", "Lịch sử"]);
    }
  });

  it("Header Navigation không chứa các mục điều hướng cũ (Mô phỏng mới, Bài thực hành, Lớp của em, Quan sát lớp)", () => {
    for (const role of ["student", "teacher"] as const) {
      const labels = itemsForRole(role).map((i) => i.label);
      for (const legacyLabel of ["Mô phỏng mới", "Bài thực hành", "Lớp của em", "Quan sát lớp"]) {
        expect(labels).not.toContain(legacyLabel);
      }
    }
  });
});

describe("W-UI · xưởng 3D dùng bề rộng desktop và không tự che hình", () => {
  it("cột nội dung nới ra khi cảnh là 3D — không kẹt ở sàn của khay 2D", () => {
    const app = readFileSync(new URL("../App.tsx", import.meta.url), "utf8");
    expect(app).toMatch(/canvasFirst\s*=\s*\n?\s*inWorkspace && hopLeScene3D/);
    expect(app).toContain('canvasFirst ? " la-canh-3d" : ""');

    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toContain(".app-layout.la-canh-3d");
    expect(css).toMatch(/\.app-layout\.la-canh-3d[^}]*grid-template-columns:\s*minmax\(0, 1fr\)/s);
  });

  it("ô soi KHÔNG dành cột cạnh hình ở desktop: không lưới hai cột, ô soi là bảng nổi", () => {
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).not.toMatch(/\.geo3d-san:has\(\.geo3d-soi\)/);
    expect(css).not.toMatch(/\.geo3d-san > \.geo3d-soi/);
    const ex = readFileSync(new URL("../simulations/domains/geometry/Scene3DExplorer.tsx", import.meta.url), "utf8");
    expect(ex).toMatch(/<BangNoi\s+panel="soi"/);
  });

  it("ô soi ở khổ hẹp nằm dưới sân khấu, không phủ lên số đo và nút điều khiển", () => {
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    const i = css.indexOf("@media (max-width: 48rem)");
    const khoi = css.slice(i, css.indexOf("@media", i + 1));
    expect(khoi).toMatch(/\n\s*\.geo3d-bang-noi\.geo3d-soi,\s*\n\s*\.geo3d-bang-noi\.geo3d-ngan \{[^}]*position:\s*static/s);
  });

  it("nút nổi ở khổ hẹp nằm trên khung, không đè lên hình", () => {
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    const i = css.indexOf("@media (max-width: 48rem)");
    const khoi = css.slice(i, css.indexOf("@media", i + 1));
    expect(khoi).toMatch(/\n\s*\.geo3d-noi \{[^}]*position:\s*static[^}]*order:\s*-1/s);
    expect(khoi).toMatch(/\n\s*\.geo3d-san \{[^}]*flex-direction:\s*column/s);
  });

  it("một khay điều khiển trên một màn hình — khay 2D ẩn khi cảnh là 3D", () => {
    const app = readFileSync(new URL("../App.tsx", import.meta.url), "utf8");
    expect(app).toMatch(/\{!canvasFirst && \(\s*<footer className="panel-controls">/s);
  });
});

describe("W-UI · nhãn từ chối phải nói đúng loại thất bại", () => {
  it("sinh chương trình hình học không thành KHÔNG còn mang nhãn ngoài danh mục", () => {
    const src = readFileSync(
      new URL("./SimulationWorkspace.tsx", import.meta.url), "utf8");
    expect(src).toContain('geometry_generation_failed');
    expect(src).toContain('"CHƯA DỰNG ĐƯỢC MÔ PHỎNG"');
    expect(src).toContain('"NGOÀI DANH MỤC MÔ PHỎNG"');
    expect(src.indexOf('"CHƯA DỰNG ĐƯỢC MÔ PHỎNG"'))
      .toBeLessThan(src.indexOf('"NGOÀI DANH MỤC MÔ PHỎNG"'));
  });
});
