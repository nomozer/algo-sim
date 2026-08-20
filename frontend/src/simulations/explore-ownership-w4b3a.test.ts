import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { beforeEach, describe, expect, it } from "vitest";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { offlineCatalog } from "../data/offline-catalog";
import { exploreEntry } from "../components/SimulationWorkspace";
import { thresholdRange } from "./domains/algorithm/condition-param";
import { whatIfPolicyOf } from "./domains/algorithm/interaction-policy";
import { activeTrace, type AlgorithmConfig, type AlgorithmSimState } from "./domains/algorithm/model";
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

/** Câu KẾT QUẢ do engine phát ở bước cuối — thứ học sinh đọc được là "đáp số". */
function finalResult(s: AlgorithmSimState): string {
  const trace = activeTrace(s);
  for (let i = trace.steps.length - 1; i >= 0; i--) {
    for (const ev of trace.steps[i].events) {
      if (ev.type === "done") return ev.result;
    }
  }
  throw new Error("trace không có bước done");
}

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
  /* ĐÃ XOÁ 2026-08-21 (Task 10b) — it("hai cờ độc lập — mở cái này không kéo theo cái kia", () => {
     Chi con MOT co che do sau W13 — 'hai co doc lap' khong con doi tuong. */

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

  /**
   * W4B-4D — CÙNG BẤT BIẾN, KHOÁ THEO TÍNH CHẤT THAY VÌ THEO KẾT LUẬN CŨ.
   *
   * Bản trước khoá thẳng "`sum_if`/`count_if` phải KHÔNG có lối vào Khám phá".
   * Kết luận ấy đúng ở thời điểm viết vì lối vào duy nhất là kéo-thả, mà kéo là
   * một HOÁN VỊ còn tổng/đếm bất biến theo hoán vị. Nhưng "kéo vô nghĩa" không
   * kéo theo "không có gì để khám phá": hai bài này bị bỏ lại với đúng một việc
   * là cam kết từng bước, tức chỉ hỏi được câu BÊN TRONG một điều kiện đứng yên.
   *
   * Bất biến thật là: MỘT LỐI VÀO KHÁM PHÁ PHẢI DẪN TỚI THAO TÁC CÓ HỆ QUẢ.
   * Nay khoá đúng câu đó, và khoá cả tiền đề của kết luận cũ (kéo vẫn tắt, và
   * hoán vị vẫn không đổi kết quả) — nếu ngày nào tiền đề sai thì test đỏ chứ
   * không im lặng.
   */
  it("lối vào Khám phá phải dẫn tới thao tác CÓ HỆ QUẢ, không phải cánh cửa trống", () => {
    for (const id of ["algorithm.sum_if", "algorithm.count_if"]) {
      const e = offlineCatalog().find((x) => x.simId === id)!;
      const mod = getSimulation(id)!;
      const r = mod.validateConfig((e.envelope as { config: unknown }).config);
      expect(r.ok).toBe(true);
      if (!r.ok) continue;
      const cfg = r.config as AlgorithmConfig;
      const s0 = mod.init(cfg) as AlgorithmSimState;

      expect(exploreEntry(mod, s0, cfg), `${id}: không còn lối vào Khám phá`).not.toBeNull();

      /* TIỀN ĐỀ 1 — kéo vẫn là trang trí ở hai bài này, nên `mode` phải giữ
         `hidden`; `ui.tsx` đọc đúng cờ này để KHÔNG bật kéo khi mở Khám phá. */
      expect(whatIfPolicyOf(cfg.algorithm_id).mode, `${id}: kéo được bật lại`).toBe("hidden");

      /* TIỀN ĐỀ 2 — và đây là chỗ đo, không phải chỗ tin: đổi chỗ hai phần tử
         KHÔNG đổi kết quả cuối. Nếu một ngày nó đổi thì lý do "kéo là trang
         trí" đã hết đúng và phải xét lại chính sách. */
      const swapped = mod.apply!(s0, { type: "whatif_swap", i: 0, j: 2 }) as AlgorithmSimState;
      expect(finalResult(swapped), `${id}: hoán vị lại đổi kết quả`).toBe(finalResult(s0));

      /* KẾT LUẬN — cửa dẫn tới đổi ĐIỀU KIỆN, và điều kiện thì đổi kết quả. */
      const range = thresholdRange(cfg.data.array)!;
      const other = cfg.data.condition!.value === range.max ? range.min : range.max;
      const s1 = mod.apply!(s0, { type: "set_param", name: "condition.value", value: other }) as AlgorithmSimState;
      expect(s1, `${id}: đổi ngưỡng mà state không đổi`).not.toBe(s0);
      expect(finalResult(s1), `${id}: đổi ngưỡng mà kết quả y nguyên`).not.toBe(finalResult(s0));
    }
  });

  it("bài KHÔNG có điều kiện thì `set_param` không mở được cửa hậu nào", () => {
    /* Đối chứng: nếu `set_param` nhận bừa thì mọi bài đều "thao tác được" và
       phép đo trải nghiệm mất khả năng phân biệt. */
    const e = offlineCatalog().find((x) => x.simId === "algorithm.bubble_sort")!;
    const mod = getSimulation("algorithm.bubble_sort")!;
    const r = mod.validateConfig((e.envelope as { config: unknown }).config);
    if (!r.ok) throw new Error(r.error);
    const s0 = mod.init(r.config);
    for (const name of ["condition.value", "condition.op", "array", "__proto__"]) {
      expect(mod.apply!(s0, { type: "set_param", name, value: 5 }), name).toBe(s0);
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
      /* Chỉ còn MỘT lối vào sau W13 — `challengeEntry` đã bị gỡ cùng chế độ. */
      for (const entry of [exploreEntry(mod, st, r.config)]) {
        if (!entry) continue;
        expect(entry.label.length, `${e.simId}: nhãn cụt "${entry.label}"`).toBeGreaterThan(14);
        expect(entry.label, `${e.simId}: nhãn lộ định danh kỹ thuật`).not.toMatch(/[a-z]+_[a-z]+|\./);
      }
    }
  });
});

/* ══ 4. RENDERER KHÔNG ĐƯỢC GHI VÀO STATE ════════════════════════════════ */

describe("W4B-3F §4 · mọi biến đổi đi qua `module.apply`, không có đường tắt", () => {
  it("KHÔNG renderer miền nào GHI THẲNG vào state", () => {
    /* LỖ HỔNG DO TIÊM LỖI BẮT ĐƯỢC, không phải phòng xa.
     *
     * Đổi `dispatch({ type: "set_param" })` trong renderer web thành
     *     (state.style as Record<string, unknown>)[name] = value;
     * đi lọt TOÀN BỘ suite. Lý do nó im: state bị sửa TẠI CHỖ nên mọi khẳng
     * định đọc lại state vẫn thấy "đúng" — trong khi store không hề biết gì,
     * nên không re-render, không vào phiên, không vào lịch sử. Đây chính là bất
     * biến #6 (renderer không sở hữu sự thật ngữ nghĩa) và trước wave này không
     * có guard nào canh nó.
     *
     * Quét theo TỪNG DÒNG: đơn giản hơn và không có bẫy khớp qua nhiều dòng.
     */
    const files: string[] = [];
    const walk = (d: string) => {
      for (const n of readdirSync(d)) {
        const full = join(d, n);
        if (statSync(full).isDirectory()) walk(full);
        else if (/\.tsx?$/.test(n) && !/\.test\.tsx?$/.test(n)) files.push(full);
      }
    };
    walk(new URL("./domains", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
    expect(files.length, "không quét được file nào — phép dò hỏng?").toBeGreaterThan(5);

    /** Một DÒNG có ghi vào `state` KHÔNG — xét VẾ TRÁI của phép gán.
     *
     * Bản đầu quét cả dòng và kêu oan ba chỗ: `base[id] = state.base[id]` (ghi
     * vào `base`, ĐỌC state — hợp lệ) và hai dòng `state[n] = 1` trong
     * `validate.ts`, nơi `state` là một BIẾN CỤC BỘ dò chu trình, không liên
     * quan gì tới state của engine. Guard kêu oan là guard sẽ bị tắt.
     */
    const writesToState = (line: string): boolean => {
      const eq = line.search(/[^=!<>]=(?![=>])/);
      if (eq < 0) return false;
      const lhs = line.slice(0, eq + 1).trim();
      return /^\(?\s*state\b/.test(lhs);
    };

    /** NGOẠI LỆ KHAI TƯỜNG MINH: file tự khai một biến cục bộ tên `state`. */
    const hasLocalState = (src: string) => /\b(?:const|let|var)\s+state\b/.test(src);

    const offenders: string[] = [];
    for (const f of files) {
      const src = readFileSync(f, "utf-8")
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/^\s*\/\/.*$/gm, "");
      /* NGOẠI LỆ KHAI TƯỜNG MINH: file tự khai một biến CỤC BỘ tên `state`
         (vd bản đồ dò chu trình trong `validate.ts`) — nó không liên quan gì
         tới state của engine, và một guard kêu oan là một guard sẽ bị tắt. */
      if (hasLocalState(src)) continue;
      for (const line of src.split("\n")) {
        if (writesToState(line)) {
          offenders.push(`${f.split(/[\/]/).slice(-2).join("/")}: ${line.trim()}`);
        }
      }
    }
    expect(
      offenders,
      `renderer ghi thẳng vào state — bỏ qua module.apply:\n${offenders.join("\n")}`,
    ).toEqual([]);
  });
});
