/**
 * regular-square-pyramid-w05 — CHẾ ĐỘ TẬP TRUNG của xưởng 3D. **0 mạng, 0 LLM, 0 WebGL.**
 *
 * Mở một mô phỏng 3D ⇒ không gian lấp trang: thanh trên toàn cục (đăng nhập/đăng ký, điều hướng) không dựng; xưởng
 * tự mang đường ra (nút quay lại về đúng trang trước), tên bài, và công cụ đã NHÓM: «Đề bài» · «Khám phá» · «Hiển
 * thị» · «Thêm». Thẻ lời giải dưới thanh phát đã gỡ — mọi đại lượng chọn được ở «Đại lượng», công thức và nguồn ở ô
 * soi, chú giải màu ở «Hiển thị». Không có jsdom: hành vi bàn phím của menu là hàm thuần, cấu trúc qua SSR, thao
 * tác thật ở đầu dò trình duyệt `frontend/scripts/w05-focus-probe.mjs`.
 */
import { describe, expect, it, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { renderToString } from "react-dom/server";
import type { Scene3D } from "./scene3d-model";
import { coherentFormula, geometryAnchor, objectsAt, quantityChoices } from "./scene3d-model";
import { Scene3DExplorer } from "./Scene3DExplorer";
import { Scene3DPlayer } from "./scene3d-playback";
import { buocMenu, hoTroToanManHinh } from "./scene3d-tool-menu";
import { withSubEntities } from "./scene3d-subentities";
import { useAppStore } from "../../../state/store";
import { registerAllSimulations } from "../../index";
import geometrySamples from "../../../data/geometry-samples.json";

const FIXTURES = fileURLToPath(new URL(
  "../../../../../docs/evaluation/geometry/runs/w11-pedagogical-polish/inputs/fixtures/", import.meta.url));
const FAMILIES = ["triangular_pyramid", "triangular_prism", "rectangular_pyramid",
  "cuboid", "cube", "cross_section"] as const;
const canh = (f: string): Scene3D =>
  JSON.parse(readFileSync(`${FIXTURES}${f}_positive.json`, "utf8")).envelope.scene3d;
const sach = (h: string) => h.replace(/<!--.*?-->/g, "");
const SRC = (p: string) => readFileSync(fileURLToPath(new URL(p, import.meta.url)), "utf8")
  .replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");

const xuong = (s: Scene3D, extra: Record<string, unknown> = {}) => sach(renderToString(
  <Scene3DExplorer scene={s} de="Cho hình chóp S.ABC." tieuDe="Thể tích khối chóp S.ABC"
                   quayLai={{ nhan: "Thư viện", onClick: () => {} }} {...extra} />));

describe("C · vỏ: không thanh trên toàn cục khi cảnh 3D", () => {
  it("App không dựng `nav-bar` khi `canvasFirst`; gốc mang lớp chế độ tập trung", () => {
    const app = SRC("../../../App.tsx");
    expect(app).toMatch(/\{!canvasFirst && \(\s*<header className="nav-bar">/);
    expect(app).toMatch(/canvasFirst \? " la-tap-trung" : ""/);
  });

  it("CSS chế độ tập trung: xưởng không còn trần 1320 px, không cuộn ngang", () => {
    const css = readFileSync(fileURLToPath(new URL("../../../styles/global.css", import.meta.url)), "utf8");
    expect(css).toMatch(/\.app-root\.la-tap-trung[^{]*\.geo3d-xuong\s*\{[^}]*max-width:\s*none/);
    // Không hàng lưới rỗng của khay 2D (đo W05: trang dư 16 px ⇒ cuộn được, canvas dời khi bấm).
    expect(css).toMatch(/\.app-root\.la-tap-trung \.app-layout\.la-canh-3d\s*\{[^}]*grid-template-areas:\s*"center";[^}]*row-gap:\s*0/);
  });
});

describe("C2 · đường ra về đúng trang trước", () => {
  const env = (geometrySamples as { samples: { envelope: unknown }[] }).samples[0].envelope;
  beforeEach(() => {
    registerAllSimulations();
    useAppStore.getState().reset();
  });

  it("vào từ Thư viện ⇒ quay lại về Thư viện, rời bài (active/bài giao dọn)", () => {
    useAppStore.getState().setView("library");
    useAppStore.getState().loadEnvelope(env as never);
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().returnView).toBe("library");
    useAppStore.getState().roiXuong();
    const s = useAppStore.getState();
    expect(s.view).toBe("library");
    expect(s.active).toBeNull();
    expect(s.activeAssignment).toBeNull();
  });

  it("đổi bài TRONG xưởng không ghi đè trang trước; mặc định là trang chủ", () => {
    useAppStore.getState().setView("history");
    useAppStore.getState().loadEnvelope(env as never);
    useAppStore.getState().loadEnvelope(env as never);
    expect(useAppStore.getState().returnView).toBe("history");
    useAppStore.getState().reset();
    useAppStore.getState().loadEnvelope(env as never);
    expect(useAppStore.getState().returnView).toBe("home");
  });

  it("SimulationWorkspace truyền nút quay lại + tên bài vào xưởng (tên trang tiếng Việt, không định danh)", () => {
    const ws = SRC("../../../components/SimulationWorkspace.tsx");
    expect(ws).toMatch(/quayLai=\{\{ nhan: TEN_TRANG\[returnView\]/);
    expect(ws).toMatch(/onClick: roiXuong/);
    expect(ws).toMatch(/tieuDe=\{active\.envelope\.title/);
  });
});

describe("C5/D · hàng trên: quay lại · tên bài · công cụ đã nhóm", () => {
  const s = canh("triangular_pyramid");

  it("nút quay lại có chữ trang đích và tên bài là tiêu đề", () => {
    const h = xuong(s);
    expect(h).toMatch(/class="geo3d-quay-lai"[^>]*>.*Thư viện/);
    expect(h).toMatch(/<h1 class="geo3d-ten-bai"[^>]*>Thể tích khối chóp S\.ABC<\/h1>/);
    expect(h).not.toContain("Hình dựng theo từng bước");
  });

  it("«Đề bài» là nút chính mở bảng đề; ba nhóm là nút menu có chữ", () => {
    const h = xuong(s);
    expect(h).toMatch(/data-mo-bang="de"[^>]*>Đề bài</);
    for (const ten of ["Khám phá", "Hiển thị", "Thêm"]) {
      expect(h).toMatch(new RegExp(`aria-haspopup="menu"[^>]*>(<[^>]+>)*${ten}`));
    }
  });

  it("chip phẳng cũ không còn trên thanh: Chi tiết, Lưới, Hình phụ, Hiện tất cả, Thành phần, Đại lượng nằm trong menu", () => {
    const thanh = xuong(s).split('class="geo3d-san"')[0];
    for (const cu of ["Chi tiết", "Lưới", "Hình phụ", "Hiện tất cả", "Thành phần", "Đại lượng"]) {
      expect(thanh, cu).not.toContain(`>${cu}<`);
    }
    expect(thanh).not.toContain("geo3d-chip");
  });

  it("«Tách khối» chỉ dựng khi cảnh có mặt; «Xem lại toàn hình» luôn có", () => {
    expect(xuong(s)).toContain("Tách khối");
    const khongMat = { ...s, objects: s.objects.filter((o) => o.type === "point3") } as Scene3D;
    const h = xuong(khongMat);
    expect(h).not.toContain("Tách khối");
    expect(h).toContain("Xem lại toàn hình");
  });

  it("menu mở/đóng bằng bàn phím: mũi tên vòng, Home/End, phím khác không đổi", () => {
    expect(buocMenu(0, 3, "ArrowDown")).toBe(1);
    expect(buocMenu(2, 3, "ArrowDown")).toBe(0);
    expect(buocMenu(0, 3, "ArrowUp")).toBe(2);
    expect(buocMenu(1, 3, "Home")).toBe(0);
    expect(buocMenu(1, 3, "End")).toBe(2);
    expect(buocMenu(1, 3, "a")).toBeNull();
  });

  it("toàn màn hình chỉ khi trình duyệt hỗ trợ (SSR: không có mục)", () => {
    expect(hoTroToanManHinh(undefined)).toBe(false);
    expect(hoTroToanManHinh({ fullscreenEnabled: false } as Document)).toBe(false);
    expect(hoTroToanManHinh({ fullscreenEnabled: true } as Document)).toBe(true);
  });
});

describe("E · không còn thẻ lời giải lặp dưới mô phỏng", () => {
  it.each(FAMILIES)("%s: trình phát không dựng thẻ lời giải ở bước cuối", (f) => {
    const s = canh(f);
    const h = sach(renderToString(<Scene3DPlayer scene={s} initialStep={s.events.length - 1} />));
    expect(h).not.toContain("geo3d-loi-giai");
    expect(h).not.toContain("Xem lời giải đầy đủ");
  });

  it.each(FAMILIES)("%s: mọi đại lượng có công thức vẫn chọn được ở «Đại lượng» (ô soi mang công thức)", (f) => {
    const s = withSubEntities(canh(f));
    const cuoi = geometryAnchor(s, s.events.length - 1);
    const q = quantityChoices(s, cuoi);
    const chon = new Set([...q.results, ...q.steps, ...q.givens]);
    const coMat = new Set(objectsAt(s, cuoi).map((o) => o.id));
    const coCongThuc = s.objects.filter((o) => coMat.has(o.id) && coherentFormula(s, o)?.references.length);
    // Thiết diện không có đại lượng tính: phép kiểm rỗng ở họ ấy, các họ đo đều có công thức.
    if (f !== "cross_section") expect(coCongThuc.length).toBeGreaterThan(0);
    for (const o of coCongThuc) {
      const goc = o.annotation?.same_as && chon.has(o.annotation.same_as) ? o.annotation.same_as : o.id;
      expect(chon, o.id).toContain(goc);
    }
  });

  it("ô soi luôn mang công thức (không còn nhánh 'lời giải đang mở')", () => {
    const ma = SRC("./Scene3DExplorer.tsx");
    expect(ma).not.toContain("moLoiGiai");
    expect(ma).toMatch(/\{formula && \(\s*<p className="geo3d-soi-cong-thuc"/);
  });

  it("chú giải màu sống trong menu «Hiển thị» (cùng bốn vai, cùng lớp màu)", () => {
    const ma = SRC("./Scene3DExplorer.tsx");
    for (const chu of ["Đang xét", "Dữ kiện số", "Đại lượng trung gian", "Hình liên quan", "Vừa dựng ở bước này"]) {
      expect(ma).toContain(chu);
    }
    expect(ma).toMatch(/chanMenu=\{[\s\S]*geo3d-chu-giai/);
  });
});
