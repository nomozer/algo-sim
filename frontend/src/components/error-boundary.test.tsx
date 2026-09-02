/**
 * LƯỚI CHẶN NGOẠI LỆ — chứng minh nó ĐỎ được, không chỉ tồn tại.
 *
 * ─── VÌ SAO TIÊM LỖI, KHÔNG CHỜ LỖI THẬT ─────────────────────────────────
 *
 * Một lưới chưa bao giờ bắt gì là một lưới chưa được chứng minh. Kho này đã
 * học điều đó một lần với các bản soát thị giác: guard xanh suốt vì nó không
 * bao giờ chạm tới thứ nó tưởng đang canh.
 *
 * ⚠️ Component ném ở đây là **của test**, không có công tắc nào trong mã sản
 * phẩm. Một "chế độ gây lỗi" trong bản dựng thật là một bề mặt tấn công và một
 * cách để ai đó vô tình bật.
 *
 * ─── MỘT DỮ KIỆN VỀ SSR, ĐO ĐƯỢC KHI DỰNG CA NÀY ─────────────────────────
 *
 * `renderToString` **KHÔNG chạy error boundary**: SSR không có pha commit, nên
 * `getDerivedStateFromError` và `componentDidCatch` không bao giờ được gọi và
 * ngoại lệ lan thẳng ra ngoài `renderToString`. Bản đầu của tệp này viết ba ca
 * theo giả định ngược lại, và cả ba đỏ ngay lượt chạy đầu.
 *
 * Nên phép đo chia làm ba, mỗi phần đo đúng thứ nó đo được:
 *
 *   ① **logic của lớp** — gọi thẳng `getDerivedStateFromError` /
 *      `getDerivedStateFromProps` / `render`. Không cần renderer, và đây là
 *      nơi cơ chế đặt-lại sống.
 *   ② **fallback dựng ra chữ gì** — `renderToString` trên chính fallback, vì
 *      nó không ném nên SSR chạy được.
 *   ③ **hành vi thật khi một cây sống ném** — Chrome thật,
 *      `frontend/scripts/certify-error-boundary.mjs`.
 *
 * Kho không có `@testing-library/react` và không có jsdom, nên ③ là cách duy
 * nhất để câu *"lỗi có bị chặn không"* được trả lời bằng đo chứ không bằng suy.
 */
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ErrorBoundary, ErrorFallback } from "./ErrorBoundary";

interface State { hong: boolean; khoa?: string }

/** Component chỉ để test: ném trong lúc RENDER. */
function Ném({ khi = true }: { khi?: boolean }) {
  if (khi) throw new Error("lỗi dựng hình giả để kiểm lưới chặn");
  return <p>bình thường</p>;
}

const FALLBACK = (nhan: string) => (thuLai: () => void) => (
  <ErrorFallback loiNhan={nhan} hanhDong="Thử lại" onHanhDong={thuLai} />
);

/* React ghi lỗi ra console khi một boundary bắt được — đó là hành vi đúng, và
 * ta CÒN chủ động ghi thêm ở `componentDidCatch`. Nuốt tiếng ồn của test,
 * nhưng vẫn giữ được phép đếm để ca "lỗi vẫn quan sát được" có nghĩa. */
let daGhi: unknown[][] = [];
beforeEach(() => {
  daGhi = [];
  vi.spyOn(console, "error").mockImplementation((...a: unknown[]) => {
    daGhi.push(a);
  });
});
afterEach(() => vi.restoreAllMocks());

describe("T1–T2 · LOGIC của lớp: ném ⇒ đổi trạng thái ⇒ dựng fallback", () => {
  it("`getDerivedStateFromError` bật cờ hỏng", () => {
    expect(ErrorBoundary.getDerivedStateFromError()).toEqual({ hong: true });
  });

  it("hỏng ⇒ `render` trả FALLBACK, không trả cây con", () => {
    const b = new ErrorBoundary({
      mien: "test", children: <Ném />, fallback: FALLBACK("Có lỗi khi hiển thị."),
    });
    b.state = { hong: true };
    expect(renderToString(<>{b.render()}</>)).toContain("Có lỗi khi hiển thị.");
  });

  it("không hỏng ⇒ `render` TRONG SUỐT, trả đúng cây con", () => {
    const con = <p>bình thường</p>;
    const b = new ErrorBoundary({ mien: "test", children: con, fallback: FALLBACK("x") });
    b.state = { hong: false };
    expect(b.render()).toBe(con);
  });

  it("fallback nhận được một callback THẬT để phục hồi", () => {
    // Nút "Thử lại" phải nối vào một hàm có thật, không phải một nút giả.
    let nhan: (() => void) | null = null;
    const b = new ErrorBoundary({
      mien: "test", children: <Ném />,
      fallback: (thuLai) => { nhan = thuLai; return null; },
    });
    b.state = { hong: true };
    b.setState = ((f: unknown) => { (b as unknown as { state: State }).state =
      { ...b.state, ...(f as object) }; }) as typeof b.setState;
    b.render();
    expect(typeof nhan).toBe("function");
    nhan!();
    expect(b.state.hong).toBe(false);
  });
});

describe("T5 · lỗi MIỀN không đi qua lưới", () => {
  it("một lời từ chối là kết quả hợp lệ — nó KHÔNG ném, nên fallback không dựng", () => {
    /* Ranh giới trung tâm của wave: *"đề ngoài phạm vi"* và *"chương trình
     * không dựng được"* là câu trả lời của sản phẩm, có bề mặt riêng. Định
     * tuyến chúng qua `throw` để lưới lo là biến một câu trả lời thành sự cố,
     * và lúc ấy người học mất luôn lời giải thích. */
    const html = renderToString(
      <ErrorBoundary mien="test" fallback={FALLBACK("KHÔNG ĐƯỢC HIỆN")}>
        <p className="unsupported">Bài này thuộc môn học khác.</p>
      </ErrorBoundary>,
    );
    expect(html).toContain("Bài này thuộc môn học khác.");
    expect(html).not.toContain("KHÔNG ĐƯỢC HIỆN");
    expect(daGhi).toHaveLength(0);
  });
});

describe("T6 · fallback không phụ thuộc dữ liệu đã hỏng", () => {
  it("dựng được khi KHÔNG có cảnh, không có vật chọn, không có bước nào", () => {
    // Fallback chỉ nhận chữ tĩnh và một callback. Nếu nó đọc `scene.objects`
    // thì lỗi lặp vô hạn ngay trong lưới cuối.
    const html = renderToString(
      <ErrorFallback loiNhan="Có lỗi." hanhDong="Thử lại" onHanhDong={() => {}} />,
    );
    expect(html).toContain("Có lỗi.");
    expect(html).toContain('role="alert"');
  });

  it("KHÔNG lộ vết ngăn xếp hay tên kỹ thuật cho người học", () => {
    const b = new ErrorBoundary({
      mien: "scene3d", children: <Ném />, fallback: FALLBACK("Có lỗi khi hiển thị."),
    });
    b.state = { hong: true };
    const html = renderToString(<>{b.render()}</>);
    for (const cam of ["Error", "at Ném", "componentStack", "scene3d",
                       "lỗi dựng hình giả"]) {
      expect(html).not.toContain(cam);
    }
  });
});

describe("lỗi vẫn QUAN SÁT ĐƯỢC", () => {
  it("`componentDidCatch` ghi ra bảng điều khiển KÈM nhãn miền", () => {
    /* Nuốt im lặng thì lưới biến một trang trắng thành một lỗi không ai biết —
     * tệ hơn, vì trang trắng ít ra còn kêu. Gọi thẳng vì SSR không gọi hộ. */
    const b = new ErrorBoundary({ mien: "workspace", children: null, fallback: FALLBACK("x") });
    b.componentDidCatch(new Error("giả"), { componentStack: "  at X" } as never);
    expect(daGhi).toHaveLength(1);
    expect(String(daGhi[0][0])).toContain("workspace");
  });
});

describe("T3–T4 · ĐẶT LẠI theo khoá", () => {
  it("`resetKey` là thẩm quyền quên lỗi — đổi bài thì lưới phải quên", () => {
    /* Không đo bằng cây sống được (không có jsdom), nên khoá bằng NGUỒN: hai
     * mệnh đề dưới đây là toàn bộ cơ chế, và cả hai vỡ được một cách im lặng.
     *
     * Vì sao `getDerivedStateFromProps` chứ không `componentDidUpdate`: nó
     * chạy TRƯỚC khi dựng lại, nên cây con của bài mới không bị fallback của
     * bài cũ chặn mất một nhịp. */
    const src = readFileSync(
      new URL("./ErrorBoundary.tsx", import.meta.url), "utf8");
    expect(src).toMatch(/static getDerivedStateFromProps/);
    expect(src).toMatch(/p\.resetKey !== s\.khoa/);
    expect(src).toMatch(/hong: false/);
  });

  it("App truyền `resetKey` dẫn từ BÀI ĐANG MỞ, không phải một hằng", () => {
    const app = readFileSync(new URL("../App.tsx", import.meta.url), "utf8");
    expect(app).toMatch(/resetKey=\{`\$\{view\}\|/);
    expect(app).toContain("active?.envelope");
  });
});

describe("HAI MỨC, và mỗi mức có việc riêng", () => {
  const app = readFileSync(new URL("../App.tsx", import.meta.url), "utf8");

  it("lưới TRONG bọc `<main>` nên giữ được thanh điều hướng", () => {
    // Thứ tự quan trọng: `<ErrorBoundary mien="main">` phải mở TRƯỚC nhánh
    // `inWorkspace`, tức nó nằm trong `.app-main` cùng cấp với `<header>`.
    const i = app.indexOf('mien="main"');
    expect(i).toBeGreaterThan(app.indexOf("<header"));
    expect(i).toBeLessThan(app.indexOf("{inWorkspace ?"));
  });

  it("lưới NGOÀI bọc cả `App`, và điểm vào dựng nó", () => {
    expect(app).toMatch(/export function AppRoot/);
    expect(app).toMatch(/mien="root"/);
    const main = readFileSync(new URL("../main.tsx", import.meta.url), "utf8");
    expect(main).toContain("<AppRoot />");
    expect(main).not.toMatch(/<App \/>/);
  });

  it("lưới NGOÀI chỉ có MỘT lối phục hồi: tải lại", () => {
    // Nó không thể giữ điều hướng — điều hướng chính là thứ vừa vỡ.
    expect(app).toContain("window.location.reload()");
  });
});
