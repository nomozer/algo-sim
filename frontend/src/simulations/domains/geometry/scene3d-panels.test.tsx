/**
 * regular-square-pyramid-w04 · H-W2-3 — MỘT cơ chế bảng nổi cho MỌI bảng thông tin của xưởng mô phỏng.
 *
 * Kiểm kê (run w04, `diagnostics/PANEL_INVENTORY.md`): ô soi (Chi tiết đối tượng), Xem đề, Thành phần, Đại lượng,
 * Các bước dựng. Trước W4 chỉ «Các bước dựng» nổi; ô soi thành CỘT lưới ở ≥ 1100 px (canvas co lại, camera đổi tỉ lệ),
 * ba ngăn dùng chung MỘT ngăn phủ mép phải (mở cái này đóng cái kia), trên mobile phủ lên hình.
 *
 * Hàm thuần ở đây giữ luật; component kiểm qua `renderToString` và cấu trúc mã nguồn; kéo, mở nhiều bảng, đổi cỡ, chọn
 * đại lượng và mobile kiểm bằng thao tác trình duyệt thật (`frontend/scripts/w04-panels-probe.mjs`).
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { Scene3D } from "./scene3d-model";
import { Scene3DExplorer } from "./Scene3DExplorer";
import { batTatBang, datViTriTuDong, lenTren, LE_BANG } from "./scene3d-floating-panel";

const nguon = (f: string) => readFileSync(new URL(f, import.meta.url), "utf8").replace(/\r\n/g, "\n");
const KHUNG = { x: 0, y: 0, w: 1000, h: 560 };
const CO = { w: 272, h: 200 };

describe("W4 · chỗ mặc định tự tránh vật cản", () => {
  it("không vật cản ⇒ góc trên-phải", () => {
    expect(datViTriTuDong(CO, KHUNG, [])).toEqual({ x: 1000 - 272 - 2 * LE_BANG, y: 2 * LE_BANG });
  });

  it("góc trên-phải đã có bảng ⇒ ngay dưới nó, cùng cột phải", () => {
    const bang = { x: 1000 - 300 - 2 * LE_BANG, y: 2 * LE_BANG, w: 300, h: 180 };
    expect(datViTriTuDong(CO, KHUNG, [bang])).toEqual({ x: 1000 - 272 - 2 * LE_BANG, y: 2 * LE_BANG + 180 + LE_BANG });
  });

  it("cột phải hết chỗ ⇒ cột trái, dưới nút nổi", () => {
    const cotPhai = { x: 1000 - 300, y: 0, w: 300, h: 560 };
    const nutNoi = { x: 12, y: 12, w: 160, h: 80 };
    expect(datViTriTuDong(CO, KHUNG, [cotPhai, nutNoi])).toEqual({ x: 2 * LE_BANG, y: 12 + 80 + LE_BANG });
  });

  it("không chỗ trống nào ⇒ vẫn nằm trọn trong khung (lệch bậc thang), không bao giờ ra ngoài", () => {
    const kinChoan = [{ x: 0, y: 0, w: 1000, h: 560 }];
    const p = datViTriTuDong(CO, KHUNG, kinChoan, 2);
    expect(p.x).toBeGreaterThanOrEqual(LE_BANG);
    expect(p.y).toBeGreaterThanOrEqual(LE_BANG);
    expect(p.x + CO.w).toBeLessThanOrEqual(1000 - LE_BANG);
    expect(p.y + CO.h).toBeLessThanOrEqual(560 - LE_BANG);
    expect(datViTriTuDong(CO, KHUNG, kinChoan, 3)).not.toEqual(p);
  });
});

describe("W4 · nhiều bảng cùng mở", () => {
  it("bật/tắt một bảng không đụng bảng khác", () => {
    const a = batTatBang(new Set(), "thanh-phan");
    const b = batTatBang(a, "dai-luong");
    expect([...b].sort()).toEqual(["dai-luong", "thanh-phan"]);
    expect([...batTatBang(b, "thanh-phan")]).toEqual(["dai-luong"]);
  });

  it("bảng vừa dùng lên trên cùng; thứ tự các bảng còn lại giữ nguyên", () => {
    expect(lenTren(["soi", "cac-buoc", "de"], "soi")).toEqual(["cac-buoc", "de", "soi"]);
    expect(lenTren(["soi"], "dai-luong")).toEqual(["soi", "dai-luong"]);
  });
});

describe("W4 · mọi bảng thông tin đi qua MỘT cơ chế", () => {
  const ex = nguon("./Scene3DExplorer.tsx");
  const pb = nguon("./scene3d-playback.tsx");
  const css = nguon("../../../styles/global.css");

  it("ô soi, Xem đề, Thành phần, Đại lượng (xưởng) và Các bước dựng (trình phát) đều là `BangNoi`", () => {
    for (const p of ["soi", "de", "thanh-phan", "dai-luong"]) expect(ex).toContain(`panel="${p}"`);
    expect(pb).toContain('panel="cac-buoc"');
    // không còn khung riêng nào cho bảng thông tin
    expect(ex).not.toMatch(/<aside[^>]*className="geo3d-(soi|ngan)"/);
  });

  it("chọn vật không dành cột: hết lưới hai cột của ô soi ở ≥ 1100 px", () => {
    expect(css).not.toMatch(/\.geo3d-san:has\(\.geo3d-soi\)/);
    expect(css).not.toMatch(/\.geo3d-san > \.geo3d-soi/);
  });

  it("chọn đại lượng giữ bảng «Đại lượng» mở (nội dung và lựa chọn giữ nguyên)", () => {
    const i = ex.indexOf("data-quantity-id");
    expect(ex.slice(i, i + 400)).not.toMatch(/setNgan\(null\)|dongBang\(/);
  });

  it("mặc định không bảng nào mở", () => {
    const s: Scene3D = JSON.parse(readFileSync(fileURLToPath(new URL(
      "../../../../../docs/evaluation/geometry/runs/regular-square-pyramid-w03/inputs/fixtures/regular_square_pyramid_positive.json",
      import.meta.url)), "utf8")).envelope.scene3d;
    const h = renderToString(<Scene3DExplorer scene={s} de="Đề" />);
    expect(h).not.toContain("geo3d-bang-noi");
  });
});
