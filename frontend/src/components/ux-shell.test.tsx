import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../App";
import { itemsForRole } from "./AppSidebar";
import { offlineCatalog, publicCatalog } from "../data/offline-catalog";

/** Số thẻ gợi ý trên Trang chủ = số bài mẫu hình học (`STARTER_SAMPLE_IDS`). */
const SO_GOI_Y = 3;
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
    /* `discoverableCatalog()` chứ không `publicCatalog()`: thứ đang canh là
       "lịch sử dài KHÔNG làm Trang chủ phình". Bề mặt công khai nay chỉ có ba
       bài hình học, không đủ để dựng ca năm mục — mà số mẫu được QUẢNG BÁ vốn
       không phải biến của tính chất này. */
    /* Ghi TOÀN BỘ danh mục, không cắt ở 5. Con số 5 là tàn dư của thời danh
       mục có 25 mẫu; tính chất đang canh là *"lịch sử DÀI không làm Trang chủ
       phình"*, và nó chỉ cần lịch sử **nhiều hơn một**. Ghim một con số lớn hơn
       số mẫu hiện có là để test đỏ vì một lý do không liên quan. */
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

    // trước M9-UX5, 5 mục lịch sử → 5 thẻ, gợi ý bị đẩy khuất. Nay: đúng 1.
    expect((html.match(/class="session-card"/g) ?? []).length).toBe(1);
    // (SSR chèn <!-- --> giữa chuỗi và biến nên "Xem tất cả (5)" KHÔNG liền mạch)
    expect(html).toContain("Xem tất cả (");
    // và gợi ý VẪN nguyên vẹn 6 mẫu — không bị lịch sử lấn
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

describe("(M9-UX5) Thư viện — nhà riêng của danh mục đầy đủ", () => {
  it("hiện TOÀN BỘ mẫu công khai, gom nhóm theo domain", () => {
    const html = renderToString(<LibraryView />);
    const pub = publicCatalog();
    expect((html.match(/class="starter-card"/g) ?? []).length).toBe(pub.length);
    expect(html).toContain("Thư viện mô phỏng");
    // (chữ hoa là do CSS text-transform; DOM giữ nguyên tiếng Việt có dấu)
    expect(html).toContain("Hình học");
    /* Dọn phạm vi sản phẩm — Thư viện chỉ còn nhóm Hình học. Khẳng định cả
       chiều VẮNG MẶT: một nhãn miền cũ hiện lại là dấu bề mặt trôi ngược. */
    for (const cam of ["Thuật toán", "Nhị phân", "Mạng", "CSDL", "Lôgic", "Web"]) {
      expect(html, `${cam}: nhóm miền cũ quay lại Thư viện`).not.toContain(cam);
    }
  });

  it("KHÔNG rò fixture nội bộ hay chuỗi kĩ thuật (luật phạm vi M9-UX2/UX3)", () => {
    const html = renderToString(<LibraryView />);
    /* ĐÃ BỎ: `offlineCatalog().length > publicCatalog().length`.
     *
     * Nó khẳng định CÓ TỒN TẠI fixture nội bộ không được quảng bá — một tính
     * chất của `OFFLINE_SAMPLES`, ngân hàng mẫu viết tay của miền Tin học, nay
     * đã gỡ. Ba bài hình học đều là `public`, nên hai tập bằng nhau và phép so
     * ấy không còn nội dung để kiểm (`LEGACY_SUBJECT_ASSERTION`).
     *
     * Luật THẬT của test — không rò chuỗi kỹ thuật lên Thư viện — nằm ở các
     * phép kiểm dưới đây và giữ nguyên. */
    expect(offlineCatalog().length).toBe(publicCatalog().length);
    expect(html).not.toContain("tam giác");
    expect(html).not.toContain("(tổng quát)");
    expect(html).not.toContain("algorithm.");
    expect(html).not.toContain("generic.rule_scene");
  });
});

/**
 * AI RA HẲN KHỎI WORKSPACE — render THẬT, không chỉ quét mã nguồn.
 *
 * M9-UX5 đã hạ AI từ "một nửa cột phải" xuống "mục thu gọn ở đáy". Bản này bỏ
 * nốt mục thu gọn: workspace là nơi làm việc với mô phỏng, và narration +
 * Observer phải tự đủ. Đường dùng AI ở Trang chủ (phân tích đề) KHÔNG đổi —
 * đó mới là chỗ AI có việc thật.
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

describe("(M9-UX5) AI thôi ngang hàng với mô phỏng (R0 phản chiếu lên UI)", () => {
  it("store: aiOpen mặc định ĐÓNG — không còn tab [Quan sát][Hỏi AI]", () => {
    useAppStore.getState().reset();
    expect(useAppStore.getState().aiOpen).toBe(false);
    // cặp tab cũ đã biến mất khỏi hợp đồng store
    expect("inspectorTab" in useAppStore.getState()).toBe(false);
  });

  /**
   * W4B-2B §8 — panel Giải thích ĐÓNG mặc định ở MỌI bề rộng.
   *
   * Dùng `getInitialState()` chứ không `getState()`: `reset()` cố ý KHÔNG đụng
   * trạng thái panel (nó dọn runtime, không dọn tuỳ chọn trình bày), nên
   * `getState()` sẽ mang theo mọi lượt `toggleRight` của test chạy trước và test
   * này sẽ xanh/đỏ vì lý do sai.
   *
   * Assert thứ hai là phần QUAN TRỌNG hơn: mặc định không được phụ thuộc
   * `window.innerWidth` nữa. Trước đây `rightOpen: WIDE_SCREEN` đọc bề rộng lúc
   * nạp module ⇒ SSR (không có `window`) mở panel còn trình duyệt hẹp thì đóng,
   * hai nhánh khởi tạo khác nhau cho cùng một học sinh.
   */
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

  it("CHƯA đăng nhập: header mỏng, điều hướng là link chữ, KHÔNG có thanh bên", () => {
    /* M18 — bài kiểm này đổi vì THÔNG TIN KIẾN TRÚC đổi, không phải vì nó
       phiền. Trước wave này Thư viện/Lịch sử nằm trên header cho mọi người;
       nay chúng là mục ỨNG DỤNG, chỉ có nghĩa khi đã có tài khoản, nên chúng
       chuyển vào thanh bên sau đăng nhập (§3, §11, §12).

       Cái phải giữ nguyên là hình thức: điều hướng vẫn là LINK CHỮ chứ không
       phải hàng nút pill (M9-UX5), và trang chưa đăng nhập KHÔNG có thanh điều
       hướng thường trực nào cả. */
    const html = renderToString(<App />);
    expect(html).toContain("nav-link");
    expect(html).toContain("Đăng nhập");
    expect(html).toContain("Đăng ký");
    expect(html, "trang chưa đăng nhập vẫn dựng thanh điều hướng ứng dụng")
      .not.toContain("app-nav-list");
  });

  it("ĐÃ đăng nhập: Thư viện/Lịch sử vẫn tới được, qua thanh bên theo vai trò", () => {
    /* Kiểm HÀM THUẦN chứ không SSR: zustand trả trạng thái ĐẦU cho server
       snapshot, nên `renderToString` sau khi set store vẫn dựng ra trang khách
       và assert sẽ xanh/đỏ vì lý do sai (ARCHITECTURE_MAP §8 #13). */
    for (const role of ["student", "teacher"] as const) {
      const labels = itemsForRole(role).map((i) => i.label);
      expect(labels, `${role}: mất lối vào Thư viện`).toContain("Thư viện");
      expect(labels, `${role}: mất lối vào Lịch sử`).toContain("Lịch sử");
      expect(labels[0], `${role}: mô phỏng không còn là mục đầu`).toBe("Mô phỏng mới");
    }
  });

  it("hai vai KHÔNG dùng chung một thanh điều hướng", () => {
    /* Đối chứng cho bài trên: nếu hai danh sách bằng nhau thì "theo vai trò"
       chỉ là lời nói. */
    const student = itemsForRole("student").map((i) => i.view);
    const teacher = itemsForRole("teacher").map((i) => i.view);
    expect(student).not.toEqual(teacher);
    expect(teacher, "giáo viên không có lối vào Quan sát lớp").toContain("observe");
    expect(student, "học sinh lại quan sát được lớp").not.toContain("observe");
  });
});
