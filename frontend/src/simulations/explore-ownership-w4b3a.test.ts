import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it } from "vitest";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { offlineCatalog } from "../data/offline-catalog";
import { challengeEntry, exploreEntry } from "../components/SimulationWorkspace";
import { useAppStore } from "../state/store";

/**
 * W4B-3A — HAI CHẾ ĐỘ, HAI TRÁCH NHIỆM, MỘT CHỦ SỞ HỮU TRÌNH BÀY.
 *
 * ─── VẤN ĐỀ ĐÃ ĐO ĐƯỢC ────────────────────────────────────────────────────
 *
 * Trước wave này, một nút tên "Thí nghiệm" do CHÍNH renderer miền dựng mở CÙNG
 * LÚC hai thứ khác loại:
 *
 *   - vùng cam kết (`ScanActionZone`/`SearchActionZone`/`SortActionZone`) — nộp
 *     qua `submitPrediction` → `predict.check` → engine PHÁN đúng/sai;
 *   - kéo-thả what-if — đi qua `module.apply`, KHÔNG ai phán gì.
 *
 * Hệ quả bố cục đo được ở cả bốn bề rộng (`docs/evaluation/m17/w4b2z-after/`):
 * 8 target thuật toán có `bands = legend, narration, experimentTrigger` và
 * `network.packet_routing` có `narration, experimentTrigger`. Mô hình tụt xuống
 * thành một mục trong bảng điều khiển.
 *
 * Hệ quả kiến trúc còn nặng hơn: cờ mở là `useState` cục bộ, nên chuyển phiên là
 * mất chế độ, và SSR luôn thấy `false` — không test nào chạm được trạng thái MỞ
 * (`ARCHITECTURE_MAP §8` #13).
 *
 * ─── PHÂN VAI SAU WAVE ────────────────────────────────────────────────────
 *
 *   store        : CÓ MỞ KHÔNG (`challengeOpen` / `exploreOpen`) — mù domain
 *   shell        : CHỖ ĐẶT lối vào (dải hành động phụ cạnh transport)
 *   module       : CÂU MỜI (`predict.entry` / `explore.entry`) + ngữ nghĩa
 *   renderer miền: bộ điều khiển cụ thể + phát `SimAction`
 *   engine       : state, timeline, và MỘT MÌNH phán đúng/sai
 */

const read = (rel: string) =>
  readFileSync(new URL(rel, import.meta.url), "utf-8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");

beforeEach(() => {
  if (listSimulations().length === 0) registerAllSimulations();
  useAppStore.getState().reset();
});

/* ══ 1. STORE VẪN MÙ DOMAIN ══════════════════════════════════════════════ */

describe("W4B-3A §1 · cờ chế độ sống ở store mà store KHÔNG biết nó nghĩa là gì", () => {
  it("store không import domain nào, không nhắc kéo/liên kết/vùng cam kết", () => {
    const src = read("../state/store.ts");
    expect(src, "store nhìn vào domain").not.toMatch(/from\s+["'].*simulations\/domains/);
    for (const leak of ["ScanActionZone", "algorithm_id", "net_cut", "whatif_swap"]) {
      expect(src, `store biết ngữ nghĩa miền (${leak})`).not.toContain(leak);
    }
  });

  it("`exploreOpen` là cờ trình bày — bật/tắt KHÔNG đụng state canonical", () => {
    const e = offlineCatalog().find((x) => x.simId === "network.packet_routing")!;
    const s = useAppStore.getState();
    s.loadEnvelope(e.envelope);
    const before = useAppStore.getState().active!.state;
    useAppStore.getState().setExploreOpen(true);
    useAppStore.getState().setExploreOpen(false);
    expect(useAppStore.getState().active!.state, "đổi chế độ đã dựng lại state").toBe(before);
  });
});

/* ══ 2. HAI CHẾ ĐỘ KHÔNG ĐƯỢC GỘP ════════════════════════════════════════ */

describe("W4B-3A §2 · Khám phá ≠ Thử thách", () => {
  it("hai cờ độc lập — mở cái này không kéo theo cái kia", () => {
    const e = offlineCatalog().find((x) => x.simId === "algorithm.find_max")!;
    useAppStore.getState().loadEnvelope(e.envelope);
    useAppStore.getState().setExploreOpen(true);
    expect(useAppStore.getState().challengeOpen, "Khám phá kéo theo Thử thách").toBe(false);
    useAppStore.getState().setExploreOpen(false);
    useAppStore.getState().setChallengeOpen(true);
    expect(useAppStore.getState().exploreOpen, "Thử thách kéo theo Khám phá").toBe(false);
  });

  it("`explore` KHÔNG được đi qua bên chấm — không module nào nối nó vào predict", () => {
    /* Đây là ranh giới trung tâm: Khám phá không có đúng/sai. Nếu một ngày
       `explore.entry` bắt đầu đọc `predict`/`check` thì hai chế độ đã nhập lại
       làm một, và học sinh học rằng kéo một cột cũng là "trả lời". */
    for (const f of ["./domains/algorithm/index.ts", "./domains/network/index.ts"]) {
      const src = read(f);
      const i = src.indexOf("explore:");
      if (i < 0) continue;
      const block = src.slice(i, i + 700);
      expect(block, `${f}: explore nối vào bên chấm`).not.toMatch(/\bcheck\s*\(/);
      expect(block, `${f}: explore tự phán đúng/sai`).not.toMatch(/verdict|correct/);
    }
  });

  it("bài mà kéo là TRANG TRÍ thì KHÔNG có lối vào Khám phá (không mời hão)", () => {
    /* `sum_if`/`count_if` khai `mode: "hidden"` — tổng/đếm bất biến theo thứ tự
       duyệt nên đổi chỗ không nhắm cơ chế nào (COVERAGE §2.6). */
    for (const id of ["algorithm.sum_if", "algorithm.count_if"]) {
      const e = offlineCatalog().find((x) => x.simId === id)!;
      const mod = getSimulation(id)!;
      const r = mod.validateConfig((e.envelope as { config: unknown }).config);
      expect(r.ok).toBe(true);
      if (!r.ok) continue;
      expect(exploreEntry(mod, mod.init(r.config), r.config), `${id}: mời một thao tác trang trí`)
        .toBeNull();
    }
  });
});

/* ══ 3. LỐI VÀO DẪN XUẤT TỪ NĂNG LỰC, KHÔNG TỪ TÊN BÀI ═══════════════════ */

describe("W4B-3A §3 · lối vào suy từ capability", () => {
  it("shell không rẽ nhánh theo tiêu đề/ngữ cảnh để quyết định bày Khám phá", () => {
    const src = read("../components/SimulationWorkspace.tsx");
    for (const bad of ["title.includes", "summary", "problem.", "description.includes"]) {
      expect(src, `rẽ nhánh theo ngữ cảnh (${bad})`).not.toContain(bad);
    }
    expect(src).toContain("mod.explore");
  });

  it("module KHÔNG khai `explore` ⇒ không lối vào Khám phá", () => {
    const none = offlineCatalog().find((e) => getSimulation(e.simId)?.explore === undefined);
    expect(none, "không còn bài nào thiếu explore — chọn lại đối chứng").toBeTruthy();
    if (!none) return;
    expect(exploreEntry(getSimulation(none.simId)!, {}, {})).toBeNull();
  });

  it("mọi lối vào đều có nhãn TỰ MÔ TẢ (không phải nút bí ẩn)", () => {
    for (const e of offlineCatalog()) {
      const mod = getSimulation(e.simId);
      if (!mod) continue;
      const r = mod.validateConfig((e.envelope as { config: unknown }).config);
      if (!r.ok) continue;
      let st: unknown;
      try { st = mod.init(r.config); } catch { continue; }
      for (const entry of [challengeEntry(mod, st, r.config), exploreEntry(mod, st, r.config)]) {
        if (!entry) continue;
        expect(entry.label.length, `${e.simId}: nhãn cụt "${entry.label}"`).toBeGreaterThan(14);
        expect(entry.label, `${e.simId}: nhãn lộ định danh kỹ thuật`).not.toMatch(/[a-z]+_[a-z]+|\./);
      }
    }
  });
});
