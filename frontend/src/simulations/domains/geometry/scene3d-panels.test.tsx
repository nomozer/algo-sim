/**
 * regular-square-pyramid-w04 · H-W2-3 — MỘT cơ chế bảng nổi cho MỌI bảng thông tin của xưởng mô phỏng.
 *
 * Kiểm kê (run w04, `diagnostics/PANEL_INVENTORY.md`): ô soi (Chi tiết đối tượng), Xem đề, Thành phần, Đại lượng,
 * Các bước dựng. Trước W4 chỉ «Các bước dựng» nổi; ô soi thành CỘT lưới ở ≥ 1100 px (canvas co lại, camera đổi tỉ lệ),
 * ba ngăn dùng chung MỘT ngăn phủ mép phải (mở cái này đóng cái kia), trên mobile phủ lên hình.
 *
 * Hàm thuần ở đây giữ luật; component kiểm qua `renderToString` và cấu trúc mã nguồn; kéo, mở nhiều bảng, đổi cỡ, chọn
 * đại lượng và mobile kiểm bằng thao tác trình duyệt thật (`frontend/scripts/check-panels.mjs`).
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { Scene3D } from "./scene3d-model";
import { Scene3DExplorer } from "./Scene3DExplorer";
import { batTatBang, DAI_TIEU_DE, datViTriTuDong, lenTren, LE_BANG } from "./scene3d-floating-panel";
import { CAO_KHUNG_MIN, caoKhungKhaDung, caoKhungVuaHinh, Scene3DPlayer } from "./scene3d-playback";
import { tiLeKhungHinh } from "./scene3d-view";
import { anchorOfGeometryStep, geometryNarrationAt, geometryStepCount, objectsAt } from "./scene3d-model";
import { groupKeysOf, selectableIds, semanticTree, treeAt, type TreeNode } from "./interaction-state";
import { entitiesPresentAt, withSubEntities } from "./scene3d-subentities";

const nguon = (f: string) => readFileSync(new URL(f, import.meta.url), "utf8").replace(/\r\n/g, "\n");
const KHUNG = { x: 0, y: 0, w: 1000, h: 560 };
const CO = { w: 272, h: 200 };

describe("chỗ mặc định tự tránh vật cản", () => {
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

  it("hai cột mép đầy ⇒ sát cạnh trái của vật cản phải, chưa vội chồng (probe W4: bảng thứ tư chồng lên bảng đầu)", () => {
    const khung = { x: 0, y: 0, w: 1320, h: 628 };
    const vatCan = [{ x: 1000, y: 16, w: 312, h: 416 }, { x: 1000, y: 440, w: 312, h: 100 },
      { x: 16, y: 90, w: 320, h: 418 }, { x: 12, y: 12, w: 160, h: 70 }];
    expect(datViTriTuDong({ w: 320, h: 293 }, khung, vatCan)).toEqual({ x: 1000 - 320 - LE_BANG, y: 2 * LE_BANG });
  });

  it("hết chỗ ⇒ bậc thang KHÔNG che dải tiêu đề (nút đóng) của bảng khác", () => {
    const khung = { x: 0, y: 0, w: 600, h: 400 };
    const vatCan = [{ x: 280, y: 16, w: 312, h: 380 }, { x: 16, y: 16, w: 250, h: 380 }];
    const p = datViTriTuDong({ w: 272, h: 200 }, khung, vatCan, 0);
    const dai = vatCan.map((v) => ({ ...v, h: DAI_TIEU_DE }));
    const o = { ...p, w: 272, h: 200 };
    expect(dai.some((v) => o.x < v.x + v.w && v.x < o.x + o.w && o.y < v.y + v.h && v.y < o.y + o.h)).toBe(false);
    expect(o.y + o.h).toBeLessThanOrEqual(400 - LE_BANG);
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

describe("nhiều bảng cùng mở", () => {
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

describe("mọi bảng thông tin đi qua MỘT cơ chế", () => {
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

/* Yêu cầu 5 — «Thành phần» là lối phụ: nhóm thu gọn mặc định, giữ trong bài, nhóm chứa vật đang chọn tự mở; nội
   dung theo bước dựng, KHÔNG lộ vật tương lai (bản trước hiện tên vật chưa dựng ở dạng mờ — vẫn là lộ trước). */
describe("cây thành phần theo bước", () => {
  const day = withSubEntities(RSP); // đúng cảnh xưởng dựng cây (mặt, cạnh sinh thêm)
  const cay = semanticTree(day);
  const ids = (ns: readonly TreeNode[]): string[] => ns.flatMap((n) => [n.isCategory ? `#${n.label}` : n.id, ...ids(n.children)]);

  it("chỉ vật đã có ở bước; nhóm rỗng biến mất", () => {
    const co = entitiesPresentAt(day, anchorOfGeometryStep(day, 1), objectsAt);
    const loc = treeAt(cay, co);
    const thay = ids(loc).filter((x) => !x.startsWith("#"));
    expect(thay.length).toBeGreaterThan(0);
    expect(thay.every((x) => co.has(x))).toBe(true);
    const tatCa = selectableIds(cay);
    expect(tatCa.filter((x) => !co.has(x)).some((x) => thay.includes(x))).toBe(false);
    // …và mọi vật đã có đều hiện — kể cả khi vật cha (khối chưa khép) chưa có: điểm S…D thuộc khối S.ABCD
    // nhưng có trước nó (probe W4 trình duyệt bắt: cây bước 2 thiếu S, A, B, C, D, đáy).
    expect(tatCa.filter((x) => co.has(x)).sort()).toEqual([...thay].sort());
    expect(co.has("khoi_chop")).toBe(false);
    expect(thay).toContain("S");
    const nhomRong = (ns: readonly TreeNode[]): boolean =>
      ns.some((n) => (n.isCategory && n.children.length === 0) || nhomRong(n.children));
    expect(nhomRong(loc)).toBe(false);
    // ở bước cuối mọi vật chọn được đều có mặt
    const cuoi = entitiesPresentAt(day, day.events.length - 1, objectsAt);
    expect(selectableIds(treeAt(cay, cuoi))).toEqual(tatCa.filter((x) => cuoi.has(x)));
  });

  it("khoá nhóm duy nhất theo đường đi; vật đang chọn ⇒ đúng các nhóm trên đường tới nó", () => {
    const keys = (ns: readonly TreeNode[], p = ""): string[] =>
      ns.flatMap((n) => [...(n.isCategory ? [`${p}/${n.id}`] : []), ...keys(n.children, `${p}/${n.id}`)]);
    const k = keys(cay);
    expect(new Set(k).size).toBe(k.length);
    const mot = selectableIds(cay)[selectableIds(cay).length - 1];
    const nhom = groupKeysOf(cay, mot);
    expect(nhom.length).toBeGreaterThan(0);
    expect(nhom.every((x) => k.includes(x))).toBe(true);
    expect(groupKeysOf(cay, "khong-co")).toEqual([]);
  });

  it("nhóm là <details> thu gọn mặc định; trạng thái mở gắn với bài, nhóm của vật chọn tự mở", () => {
    const ex = nguon("./Scene3DExplorer.tsx");
    expect(ex).toMatch(/<details[^>]*className="geo3d-tree-cat"/);
    expect(ex).not.toMatch(/disabled=\{chuaCo\}/);
    expect(ex).toMatch(/setMoNhom\(new Set\(\)\)/);
    // khoá tính trên cây ĐÃ LỌC — đúng đường đi của nút đang dựng (nhóm của khối chưa có được đưa lên một tầng)
    expect(ex).toMatch(/groupKeysOf\(cayBuoc, tt\.selected_id\)/);
  });
});

/* Yêu cầu 4 — canvas lấy phần chiều cao còn lại, thanh phát sát đáy vùng mô phỏng; «Bước n/N» trong thanh; mô tả
   đầy đủ của bước ở bảng «Các bước dựng», không thành dòng dài dưới thanh. */
const RSP: Scene3D = JSON.parse(readFileSync(fileURLToPath(new URL(
  "../../../../../docs/evaluation/geometry/runs/regular-square-pyramid-w03/inputs/fixtures/regular_square_pyramid_positive.json",
  import.meta.url)), "utf8")).envelope.scene3d;

describe("canvas theo chiều cao khả dụng", () => {
  it("canvas = cửa sổ − phần trên canvas − thanh điều khiển − khe và lề đáy; không dưới mức sàn", () => {
    // 1440×900: canvas bắt đầu ở 115 px (trang), thanh điều khiển cao 40, khe 8 ⇒ thanh kết thúc sát đáy (lề 12)
    expect(caoKhungKhaDung(900, 115, 40, 8)).toBe(900 - 115 - 8 - 40 - 12);
    // màn thấp: không co canvas xuống vô nghĩa — trang cuộn thay vì hình bé như con tem
    expect(caoKhungKhaDung(500, 200, 40, 8)).toBe(CAO_KHUNG_MIN);
  });
});

/* mobile-canvas-fit (D5): khổ hẹp — canvas cao vừa hình. Đo trước sửa (390×844): canvas 519 px, hình lấp 53 % chiều
   cao, dải trắng 107 + 137 px; mở «Các bước dựng» cuộn trang 338 px và hình rời khỏi khung nhìn. */
describe("D5 · khổ hẹp: canvas cao vừa hình", () => {
  it("hình ràng theo bề ngang: canvas = rộng × tỉ lệ hình — phần dư chỉ là dải trắng, cắt đi; hình giữ nguyên cỡ", () => {
    expect(caoKhungVuaHinh(519, 358, 1.06)).toBe(Math.round(358 * 1.06));
  });

  it("hình ràng theo chiều cao: giữ TRỌN phần khả dụng — không trần, không thu nhỏ hình (brief W5, đề D5 (a) bị loại)", () => {
    expect(caoKhungVuaHinh(519, 358, 1.77)).toBe(519);
  });

  it("không dưới sàn `CAO_KHUNG_MIN` — còn chỗ để xoay hình", () => {
    expect(caoKhungVuaHinh(519, 358, 0.4)).toBe(CAO_KHUNG_MIN);
  });

  it("tỉ lệ hình chỉ theo CẢNH (cùng hướng nhìn + phép xoay hiển thị với khung nhìn): bước, lựa chọn, bảng không đổi nó", () => {
    const r = tiLeKhungHinh(RSP.objects);
    expect(r).not.toBeNull();
    expect(r!).toBeGreaterThan(0);
    expect(tiLeKhungHinh(RSP.objects)).toBe(r);
    // Cảnh không cạnh (khung cũ ôm mặt cầu bao) ⇒ không tỉ lệ ⇒ trình phát giữ chiều cao khả dụng.
    expect(tiLeKhungHinh(RSP.objects.filter((o) => o.type === "point3"))).toBeNull();
  });

  it("chỉ áp ở khổ hẹp — cùng điểm gãy với bảng trong dòng chảy; desktop giữ canvas lấp phần còn lại (W5 R1)", () => {
    const src = nguon("./scene3d-playback.tsx");
    expect(src).toContain('const KHO_HEP = "(max-width: 48rem)"');
    expect(src).toMatch(/hep \? caoKhungVuaHinh\(khaDung, r\.width, tiLeHinh!\) : khaDung/);
    expect(nguon("../../../styles/global.css")).toMatch(/@media \(max-width: 48rem\) \{\n {2}\.geo3d-bang-noi \{\n {4}position: static;/);
  });

  it("điện thoại ngang (phone-landscape-layout): JS và CSS cùng MỘT điều kiện; ở đó thanh là cột cạnh canvas, không vừa hình D5", () => {
    const src = nguon("./scene3d-playback.tsx");
    const css = nguon("../../../styles/global.css");
    const dk = src.match(/const NGANG_THAP = "([^"]+)"/)?.[1];
    expect(dk).toBe("(orientation: landscape) and (max-height: 30rem)");
    const khoi = css.slice(css.indexOf(`@media ${dk} {`));
    expect(khoi.length).toBeLessThan(css.length);
    // thanh điều khiển thành cột bên phải canvas; bảng nổi như desktop (khổ hẹp xếp chúng dưới nếp gấp)
    expect(khoi).toMatch(/\.geo3d-player \{\n {4}display: grid;\n {4}grid-template-columns: minmax\(0, 1fr\) 10rem;/);
    expect(khoi).toMatch(/\.geo3d-bang-noi \{\n {4}position: absolute;/);
    // D5 (vừa hình) chỉ ở khổ hẹp KHÔNG ngang thấp; thanh nằm cạnh canvas thì không trừ khỏi chiều cao khả dụng
    expect(src).toMatch(/const hep = tiLeHinh !== null && mq\(KHO_HEP\) && !mq\(NGANG_THAP\);/);
    expect(src).toMatch(/const duoiKhung = tr\.top >= r\.bottom - 1;/);
    expect(src).toMatch(/duoiKhung \? tr\.height : 0,\n\s+duoiKhung \? khe : 0\)/);
  });

  it("khổ hẹp: khe ngang của nút phát hẹp lại SAU luật gốc `.geo3d-btn` (thứ tự CSS quyết thắng thua)", () => {
    const css = nguon("../../../styles/global.css");
    const goc = css.indexOf("\n.geo3d-btn {");
    const hep = css.indexOf("@media (max-width: 48rem) {\n  .geo3d-btn {\n    padding-inline: var(--sp-sm);");
    expect(goc).toBeGreaterThan(0);
    expect(hep).toBeGreaterThan(goc);
  });

  it("bảng bước dài: giữ bước đang xem trong thân bảng bằng cuộn THÂN BẢNG, không `scrollIntoView` (cuộn cả trang)", () => {
    const src = nguon("./scene3d-playback.tsx");
    expect(src).toMatch(/than\.scrollTop \+= r\.top - c\.top/);
    expect(src).toMatch(/\}, \[buocHinh, moBuoc\]\);/);
    expect(src).not.toMatch(/\.scrollIntoView\(/);
  });
});

describe("bước dựng trong thanh điều khiển", () => {
  it("«Bước n/N» nằm trong thanh điều khiển; xưởng không còn dòng lời kể dài dưới thanh", () => {
    const h = renderToString(<Scene3DPlayer scene={RSP} />);
    const thanh = h.slice(h.indexOf("geo3d-controls"));
    expect(thanh).toContain(`Bước 1/${geometryStepCount(RSP)}`);
    const xuong = renderToString(<Scene3DExplorer scene={RSP} />);
    expect(xuong).not.toContain("geo3d-buoc-loi");
  });

  it("mô tả đầy đủ của bước đang xem ở bảng «Các bước dựng», ngay dưới mục của nó", () => {
    const k = anchorOfGeometryStep(RSP, 2);
    const h = renderToString(<Scene3DPlayer scene={RSP} initialStep={k} stepsOpen />);
    const moTa = geometryNarrationAt(RSP, k);
    const muc = h.slice(h.indexOf('aria-current="step"'));
    expect(muc.slice(0, muc.indexOf("</li>"))).toContain(moTa);
  });
});
