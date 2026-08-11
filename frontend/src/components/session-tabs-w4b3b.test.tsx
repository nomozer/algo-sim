import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { beforeEach, describe, expect, it } from "vitest";
import { SessionTabs, sessionLabels } from "./SessionTabs";
import { useAppStore } from "../state/store";
import { registerAllSimulations } from "../simulations";
import { listSimulations } from "../simulations/registry";
import { offlineCatalog } from "../data/offline-catalog";

/**
 * W4B-3B — ĐIỀU HƯỚNG PHIÊN KHÔNG ĐƯỢC LẤN SÂN KHẤU.
 *
 * Thứ bậc của AlgoSim: **sân khấu > điều khiển > quản lí phiên**. Bản trước đặt
 * ngược: một CỘT 208px thường trực cho hạng mục thứ ba, và vì `grid-area: rail`
 * trải qua CẢ hàng `center` lẫn hàng `controls`, nó bóp luôn dải điều khiển.
 *
 * Đo được trong Chrome trước khi sửa (`w4b3b-workspace/before.json`):
 *
 *   bề rộng   1 phiên → 2 phiên      sân khấu           dải điều khiển
 *   1920      1672px  → 1448px       −224px, dời +224   1 dòng → 2 dòng
 *   1536      1460px  → 1236px       −224px, dời +224   1 dòng → 2 dòng
 *   1366      1290px  → 1066px       −224px, dời +224   (đã 2 dòng sẵn)
 *
 * Test này khoá phần kiểm được KHÔNG CẦN trình duyệt; phần hình học do
 * `scripts/accept-workspace-w4b3b.mjs` đo ở 4 bề rộng.
 */

const read = (rel: string) =>
  readFileSync(new URL(rel, import.meta.url), "utf-8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");

beforeEach(() => {
  if (listSimulations().length === 0) registerAllSimulations();
  useAppStore.getState().reset();
});

const s = () => useAppStore.getState();
const env = (id: string) => offlineCatalog().find((e) => e.simId === id)!.envelope;

/* ══ 1. KHÔNG CÒN CỘT THƯỜNG TRỰC ═══════════════════════════════════════ */

describe("W4B-3B §1 · không có cột điều hướng phiên thường trực", () => {
  it("không nguồn nào còn dựng vùng lưới `rail`", () => {
    /* Khoá theo NGUỒN chứ không theo ảnh: thu nhỏ cột rồi gọi là xong chính là
       thứ §0 cấm. Không còn `grid-area: rail` thì không còn cột. */
    expect(read("../App.tsx")).not.toContain("SessionRail");
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf-8");
    expect(css, "vùng lưới `rail` quay lại").not.toMatch(/grid-area:\s*rail/);
    expect(css, "lớp `.has-rail` quay lại").not.toContain("has-rail");
    expect(css, "thiếu hàng `tabs` cho điều hướng ngang").toMatch(/grid-area:\s*tabs/);
  });

  it("hàng tab KHÔNG dựng khi chỉ có một phiên", () => {
    s().loadEnvelope(env("algorithm.find_max"));
    expect(s().sessions).toHaveLength(1);
    expect(renderToString(<SessionTabs />)).toBe("");
  });

  it("`Mô phỏng mới` KHÔNG được chỉ sống trong hàng tab", () => {
    /* LỖI CHỨC NĂNG BẢN CŨ: lối vào duy nhất nằm trong đầu cột phiên, mà cột ẩn
       khi <2 phiên ⇒ đang mở một bài thì không có đường nào mở bài thứ hai.
       Tính năng nhiều phiên không với tới được từ chính trạng thái khởi đầu. */
    expect(read("./SessionTabs.tsx"), "lối vào lại chui vào hàng tab")
      .not.toContain("newSession");
    expect(read("../App.tsx"), "không còn chỗ nào mở được mô phỏng thứ hai")
      .toContain("newSession");
  });
});

/* ══ 2. TRÙNG TIÊU ĐỀ VẪN PHÂN BIỆT ĐƯỢC ════════════════════════════════ */

describe("W4B-3B §5 · nhãn phiên", () => {
  it("tiêu đề duy nhất thì KHÔNG gắn hậu tố", () => {
    expect(sessionLabels(["Tìm max", "Sắp xếp"])).toEqual(["Tìm max", "Sắp xếp"]);
  });

  it("tiêu đề trùng thì đánh số theo THỨ TỰ MỞ", () => {
    expect(sessionLabels(["Tìm max", "Tìm max"])).toEqual(["Tìm max · 1", "Tìm max · 2"]);
    expect(sessionLabels(["A", "B", "A", "A"])).toEqual(["A · 1", "B", "A · 2", "A · 3"]);
  });

  it("nhãn LUÔN phân biệt được — đó là mục đích tồn tại của hàm này", () => {
    const labels = sessionLabels(["X", "X", "X", "Y", "Y"]);
    expect(new Set(labels).size).toBe(labels.length);
  });

  it("là TRÌNH BÀY THUẦN — không suy nghĩa từ chuỗi, không đụng config", () => {
    const src = read("./SessionTabs.tsx");
    for (const bad of ["config", "envelope.config", "simulation_id", "moduleId ==="]) {
      expect(src, `nhãn phiên đọc vào ngữ nghĩa (${bad})`).not.toContain(bad);
    }
  });
});

/* ══ 3. KIẾN TRÚC PHIÊN KHÔNG ĐỔI ═══════════════════════════════════════ */

describe("W4B-3B §4 · dời TRÌNH BÀY, không dời kiến trúc", () => {
  it("hai phiên TRÙNG TIÊU ĐỀ vẫn là hai phiên độc lập, chuyển qua lại giữ nguyên", () => {
    /* Ca này chưa test nào phủ: hai phiên cùng bài dễ bị gộp nhầm theo tiêu đề
       hoặc theo `simulation_id` nếu ai đó "tối ưu" danh sách phiên. */
    const E = env("algorithm.find_max");
    s().loadEnvelope(E);
    const idA = s().activeSessionId!;
    s().nextStep();
    s().nextStep();
    const stateA = s().active!.state;

    s().newSession();
    s().loadEnvelope(E);
    const idB = s().activeSessionId!;
    expect(idB).not.toBe(idA);
    expect(s().sessions).toHaveLength(2);
    const stateB = s().active!.state;
    expect(stateB).not.toBe(stateA);

    s().switchSession(idA);
    expect(s().active!.state, "phiên trùng tiêu đề bị lẫn state").toBe(stateA);
    s().switchSession(idB);
    expect(s().active!.state).toBe(stateB);
  });

  it("hàng tab chỉ ĐỌC store + phát thao tác phiên — không tự dựng lại gì", () => {
    const src = read("./SessionTabs.tsx");
    for (const bad of ["loadEnvelope", "mod.init", "validateConfig", "fetch("]) {
      expect(src, `hàng tab tự dựng lại mô phỏng (${bad})`).not.toContain(bad);
    }
  });
});
