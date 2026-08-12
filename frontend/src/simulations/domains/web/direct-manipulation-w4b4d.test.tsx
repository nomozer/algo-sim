import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeWebStyleModule } from "./index";
import { cssTextOf, htmlTextOf, isModified, moveBlock, selectNode } from "./apply";
import type { SimAction } from "../../types";
import type { WebConfig, WebState } from "./model";

/**
 * W4B-4D — HỌC SINH THAO TÁC LÊN TRANG, KHÔNG PHẢI LÊN MỘT BẢNG ĐIỀU KHIỂN.
 *
 * ─── LỖI ĐÃ ĐO ĐƯỢC ───────────────────────────────────────────────────────
 *
 * Bản W4B-3F đã có một trang thật (khung + `h1` + `p`), nhưng đường DUY NHẤT
 * chạm tới nó là cột thanh trượt bên trái. Muốn đổi tiêu đề, học sinh phải đọc
 * tên thuộc tính rồi ĐOÁN nó ứng với phần nào của trang — tức là quan hệ
 * "thẻ ↔ bộ chọn ↔ hiển thị", đúng thứ bài này dạy, bị bỏ lại cho người học tự
 * suy ra. Và trang chỉ có MỘT hình dạng: mọi thứ thuộc HTML (thứ tự tài liệu)
 * đều đứng yên, chỉ CSS đổi được.
 *
 * Wave này thêm hai lối tác động THẲNG lên đối tượng, và bài kiểm khoá cả hai:
 *
 *   1. CHỌN — bấm vào phần nào là cầm phần ấy; sân khấu, cột control và
 *      Inspector cùng đọc một `state.selected`.
 *   2. DỜI  — đổi thứ tự khối trong thân trang, miền là một HOÁN VỊ của tập
 *      khối đã có (không thêm/xoá thẻ ⇒ không phải trình soạn thảo HTML).
 *
 * Bài học nằm ở chỗ hai bản chiếu LỆCH nhau: dời khối thì HTML đổi mà CSS
 * KHÔNG đổi. Nếu một ngày bảng kiểu cũng đổi theo thứ tự thì mô hình đã sai,
 * nên chỗ lệch đó được khoá bằng test chứ không để trong lời văn.
 */

const mod = makeWebStyleModule();

const stateOf = (over: Record<string, unknown> = {}): WebState => {
  const r = mod.validateConfig({
    heading: "Chào các bạn",
    paragraph: "Đoạn văn giới thiệu ngắn.",
    style: { backgroundColor: "#fde68a", fontSize: 24 },
    ...over,
  });
  if (!r.ok) throw new Error(r.error);
  return mod.init(r.config as WebConfig);
};

const act = (s: WebState, a: SimAction): WebState => mod.apply!(s, a) as WebState;
const render = (s: WebState) =>
  renderToString(<mod.Workspace state={s} dispatch={() => {}} config={{} as never} busy={false} />);
/** Phần HTML từ khung trang trở đi — nơi SÂN KHẤU vẽ, tách khỏi cột control. */
const stage = (s: WebState) => {
  const html = render(s);
  return html.slice(html.search(/class="web-page[" ]/));
};

// ── 1. CHỌN — bấm vào phần nào là cầm phần ấy ─────────────────
describe("W4B-4D · chọn một phần của trang", () => {
  it("mở bài ra là đang cầm khung trang, chưa cầm khối nào", () => {
    expect(stateOf().selected).toBe("page");
  });

  it("chọn khối ⇒ state đổi ngay, KHÔNG cần phát timeline", () => {
    const s0 = stateOf();
    const s1 = act(s0, { type: "set_param", name: "selected", value: "heading" });
    expect(s1).not.toBe(s0);
    expect(s1.selected).toBe("heading");
    expect(act(s1, { type: "set_param", name: "selected", value: "paragraph" }).selected)
      .toBe("paragraph");
  });

  it("chọn lại đúng thứ đang cầm ⇒ KHÔNG sinh state mới", () => {
    /* Không phải tiết kiệm bộ nhớ: một state mới mỗi lần bấm sẽ khiến mọi phép
       đo "thao tác này có đổi gì không" xanh với cả những cú bấm vô nghĩa. */
    const s = act(stateOf(), { type: "set_param", name: "selected", value: "heading" });
    expect(act(s, { type: "set_param", name: "selected", value: "heading" })).toBe(s);
  });

  it("tên nút lạ ⇒ fail-closed, state giữ nguyên", () => {
    const s = stateOf();
    for (const bad of ["body", "h2", "", "__proto__", "trang", "style"]) {
      expect(selectNode(bad), bad).toBeNull();
      expect(act(s, { type: "set_param", name: "selected", value: bad }), bad).toBe(s);
    }
  });

  it("`selected` KHÔNG chiếm mất tên của một thuộc tính kiểu", () => {
    /* Hai nhánh dùng chung `set_param`, nên phải chắc chúng không giẫm nhau:
       đổi màu vẫn đổi màu, và không cú chọn nào lọt vào `style`. */
    const s = act(stateOf(), { type: "set_param", name: "backgroundColor", value: "#a7f3d0" });
    expect(s.style.backgroundColor).toBe("#a7f3d0");
    expect(s.selected).toBe("page");
    expect(Object.keys(s.style)).not.toContain("selected");
  });
});

// ── 2. DỜI — hoán vị, không phải soạn thảo ────────────────────
describe("W4B-4D · dời khối trong thân trang", () => {
  it("dời tiêu đề xuống ô 1 ⇒ thứ tự tài liệu đảo lại", () => {
    const s0 = stateOf();
    expect(s0.order).toEqual(["heading", "paragraph"]);
    const s1 = act(s0, { type: "move", target: "heading", x: 0, y: 1 });
    expect(s1).not.toBe(s0);
    expect(s1.order).toEqual(["paragraph", "heading"]);
    // và khối vừa dời vẫn là khối đang cầm ⇒ mũi tên thứ hai dời đúng nó
    expect(s1.selected).toBe("heading");
  });

  it("miền là HOÁN VỊ: không thêm, không xoá, không đổi tập khối", () => {
    let s = stateOf();
    for (const [t, y] of [["paragraph", 0], ["heading", 0], ["paragraph", 1]] as const) {
      s = act(s, { type: "move", target: t, x: 0, y });
      expect([...s.order].sort()).toEqual(["heading", "paragraph"]);
    }
  });

  it("ô đích ngoài miền / khối lạ / đứng yên ⇒ state giữ nguyên", () => {
    const s = stateOf();
    const bad: SimAction[] = [
      { type: "move", target: "heading", x: 0, y: 2 },    // quá cuối
      { type: "move", target: "heading", x: 0, y: -1 },   // quá đầu
      { type: "move", target: "heading", x: 0, y: 0.5 },  // không phải chỉ số ô
      { type: "move", target: "footer", x: 0, y: 0 },     // khối không có trong trang
      { type: "move", target: "heading", x: 0, y: 0 },    // đã ở đó rồi
    ];
    for (const a of bad) expect(act(s, a), JSON.stringify(a)).toBe(s);
    expect(moveBlock(["heading"], "heading", 0)).toBeNull();
  });

  it("đề không có đoạn văn ⇒ thân trang một khối, không có gì để dời", () => {
    /* Một ô trống vẫn đảo lên đảo xuống được sẽ vừa vô nghĩa vừa in ra một thẻ
       `<p>` không tồn tại trong trang. */
    const s = stateOf({ paragraph: "" });
    expect(s.order).toEqual(["heading"]);
    expect(htmlTextOf(s)).not.toContain("<p>");
    expect(act(s, { type: "move", target: "paragraph", x: 0, y: 0 })).toBe(s);
  });
});

// ── 3. HAI BẢN CHIẾU LỆCH NHAU — đó là bài học ────────────────
describe("W4B-4D · thứ tự thuộc HTML, hình thức thuộc CSS", () => {
  it("dời khối ⇒ cấu trúc thẻ đổi, bảng kiểu KHÔNG đổi", () => {
    const s0 = stateOf();
    const s1 = act(s0, { type: "move", target: "heading", x: 0, y: 1 });
    expect(htmlTextOf(s1)).not.toBe(htmlTextOf(s0));
    expect(htmlTextOf(s1).indexOf("<p>")).toBeLessThan(htmlTextOf(s1).indexOf("<h1>"));
    expect(cssTextOf(s1.style), "bảng kiểu đổi theo thứ tự — CSS không sở hữu thứ tự")
      .toBe(cssTextOf(s0.style));
  });

  it("đổi kiểu ⇒ bảng kiểu đổi, cấu trúc thẻ KHÔNG đổi", () => {
    const s0 = stateOf();
    const s1 = act(s0, { type: "set_param", name: "headingSize", value: 40 });
    expect(cssTextOf(s1.style)).not.toBe(cssTextOf(s0.style));
    expect(htmlTextOf(s1)).toBe(htmlTextOf(s0));
  });

  it("SÂN KHẤU vẽ theo `state.order`, không theo thứ tự viết trong JSX", () => {
    /* Đây là chỗ dễ trượt nhất: JSX có sẵn `<h1>` rồi `<p>` viết cứng, nên một
       bản cài đặt vẫn "chạy được" trong khi sân khấu đứng yên còn mã bên dưới
       thì đảo — hai bản chiếu của một state nói hai điều khác nhau. */
    const s0 = stateOf();
    const before = stage(s0);
    expect(before.indexOf("<h1")).toBeLessThan(before.indexOf("<p"));

    const s1 = act(s0, { type: "move", target: "heading", x: 0, y: 1 });
    const after = stage(s1);
    expect(after.indexOf("<p"), "sân khấu không đảo theo state").toBeLessThan(after.indexOf("<h1"));
  });

  it("khối bàn phím tới được, và mũi tên dời có TÊN đọc lên được", () => {
    const s = act(stateOf(), { type: "set_param", name: "selected", value: "heading" });
    const html = render(s);
    expect(html).toContain('role="button"');
    expect(html).toContain("Chọn Tiêu đề (.trang h1)");
    expect(html).toContain("Đưa Tiêu đề lên trên");
    expect(html).toContain("Đưa Tiêu đề xuống dưới");
  });

  it("mũi tên dời CHỈ hiện ở khối đang chọn, và chỉ khi có từ hai khối", () => {
    expect(render(stateOf()), "chưa chọn khối nào mà đã có mũi tên")
      .not.toContain("lên trên");
    const one = act(stateOf({ paragraph: "" }),
      { type: "set_param", name: "selected", value: "heading" });
    expect(render(one), "trang một khối vẫn mời dời chỗ").not.toContain("lên trên");
  });
});

// ── 4. RANH GIỚI CŨ KHÔNG ĐƯỢC NỚI ────────────────────────────
describe("W4B-4D · vẫn không phải trình soạn thảo", () => {
  it("renderer KHÔNG tự ghép chuỗi cấu trúc — chỉ đọc `htmlTextOf`", () => {
    /* Nếu JSX tự nối `<div class="trang">…` thì cấu trúc có hai nguồn sự thật,
       và một cú dời có thể hiện ở sân khấu mà không hiện ở mã. */
    const src = readFileSync(new URL("./ui.tsx", import.meta.url), "utf-8");
    expect(src, "renderer tự dựng chuỗi HTML").not.toMatch(/<div class=\\?"trang/);
    expect(src).toContain("htmlTextOf(state)");
  });

  it("state vẫn không mang mã: `order` chỉ chứa tên khối đã khai", () => {
    const s = act(stateOf(), { type: "move", target: "heading", x: 0, y: 1 });
    for (const b of s.order) expect(["heading", "paragraph"]).toContain(b);
    expect(JSON.stringify(s)).not.toContain("<");
  });

  it("Về ban đầu trả lại CẢ cấu trúc lẫn hình thức", () => {
    let s = stateOf();
    s = act(s, { type: "move", target: "heading", x: 0, y: 1 });
    s = act(s, { type: "set_param", name: "headingSize", value: 40 });
    expect(isModified(s)).toBe(true);

    const back = act(s, { type: "toggle", target: "reset" });
    expect(back.order, "đặt lại mà cấu trúc vẫn đảo").toEqual(["heading", "paragraph"]);
    expect(back.style).toEqual(stateOf().style);
    expect(isModified(back)).toBe(false);
  });

  it("chỉ dời khối thôi cũng đã là ĐÃ SỬA — phải có đường lùi", () => {
    const s = act(stateOf(), { type: "move", target: "heading", x: 0, y: 1 });
    expect(isModified(s), "đổi cấu trúc mà không hiện nút Về ban đầu").toBe(true);
  });

  it("chọn một nút KHÔNG phải là sửa trang", () => {
    /* Đối chứng cho phép đo trên: nếu `isModified` xanh với cả cú chọn thì nút
       Về ban đầu hiện ra ngay khi học sinh mới chỉ nhìn quanh. */
    const s = act(stateOf(), { type: "set_param", name: "selected", value: "paragraph" });
    expect(isModified(s)).toBe(false);
  });
});
