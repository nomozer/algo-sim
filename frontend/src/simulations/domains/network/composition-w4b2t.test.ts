import { describe, expect, it } from "vitest";
import { layout2d } from "./ui";
import type { NetNode } from "./model";

/**
 * W4B-2T — BỐ CỤC TOPOLOGY PHẢI SUY TỪ CHỖ THẬT SỰ CÓ.
 *
 * Đo được trước wave này: topology dựng đúng 610px bất kể sân khấu rộng bao
 * nhiêu (mức dùng bề ngang 37.6% ở 1920). Họ mảng đã giải bài này từ W4B-2A;
 * network là renderer cuối còn tự khai một hằng số pixel.
 *
 * Test này tồn tại vì TIÊM LỖI phát hiện thiếu nó: khôi phục hằng số cứng mà
 * không có file test nào đỏ — chỉ phép đo trình duyệt bắt được, mà phép đo thì
 * không chạy trong CI. Hàm thuần ⇒ kiểm được không cần Chrome.
 */

const NODES: NetNode[] = [
  { id: "a", type: "client" }, { id: "b", type: "router" },
  { id: "c", type: "isp" }, { id: "d", type: "server" },
];
const ROUTE = ["a", "b", "c", "d"];

const widthAt = (available: number) => layout2d(NODES, ROUTE, available).width;

describe("W4B-2T · layout2d THÍCH ỨNG theo bề rộng khả dụng", () => {
  it("sân khấu rộng hơn ⇒ topology dùng nhiều hơn (không đứng yên ở hằng số)", () => {
    const narrow = widthAt(700);
    const wide = widthAt(1600);
    expect(wide, "bề rộng không đổi theo sân khấu ⇒ vẫn là hằng số cứng")
      .toBeGreaterThan(narrow);
  });

  it("KẸP TRÊN: thiết bị không phình to lố khi màn cực rộng (§7)", () => {
    /* Không kẹp thì 4 nút trải trên 3000px thành bốn hòn đảo xa nhau — "dùng
       hết sân khấu" mà quan hệ nối kết thì loãng ra. */
    const huge = widthAt(4000);
    const wide = widthAt(1600);
    expect(huge).toBe(widthAt(3000)); // đã chạm trần
    expect(huge).toBeGreaterThanOrEqual(wide);
    expect(huge).toBeLessThan(4000);
  });

  it("KẸP DƯỚI: màn hẹp vẫn giữ khoảng cách tối thiểu đọc được", () => {
    // Hẹp hơn mức tối thiểu thì KHÔNG được bóp nút chồng lên nhau; SVG co bằng
    // viewBox thay vì bằng cách dí các nút vào nhau.
    expect(widthAt(200)).toBe(widthAt(0));
  });

  it("bề rộng 0 (SSR/chưa đo) ⇒ rơi về bố cục mặc định, không NaN", () => {
    const l = layout2d(NODES, ROUTE, 0);
    expect(Number.isFinite(l.width)).toBe(true);
    expect(l.width).toBeGreaterThan(0);
    for (const id of ROUTE) expect(Number.isFinite(l.positions[id].x)).toBe(true);
  });

  it("mọi nút vẫn được định vị ở mọi bề rộng — không nút nào mồ côi", () => {
    for (const w of [0, 400, 900, 1600, 3000]) {
      const l = layout2d(NODES, ROUTE, w);
      for (const n of NODES) {
        expect(l.positions[n.id], `w=${w}: mất nút ${n.id}`).toBeDefined();
      }
    }
  });
});
