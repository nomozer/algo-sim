import { beforeEach, describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { offlineCatalog } from "../data/offline-catalog";
import { specDrift } from "../components/SimulationWorkspace";
import { useAppStore } from "../state/store";
import type { SimAction, SimulationModule } from "./types";

/**
 * W4B-4D — TIÊU ĐỀ LÀ ĐỀ BÀI; MÔ HÌNH CÓ THỂ ĐÃ ĐI CHỖ KHÁC.
 *
 * ─── LỖI DO CHÍNH WAVE NÀY SINH RA ────────────────────────────────────────
 *
 * Khi các bài còn chạy đúng một cấu hình, tiêu đề và mô hình luôn nói cùng một
 * điều. Từ khi đổi được tham số có ràng buộc thì không còn thế nữa: đề viết
 * "Đếm số học sinh đạt điểm trung bình môn từ 8,0 trở lên", học sinh kéo ngưỡng
 * về 6, và con số cuối cùng trên màn hình đọc như đáp số của bài gốc. Màn hình
 * đang khẳng định một điều SAI, và không bề mặt nào nói ra.
 *
 * Nhãn "Đã đổi so với đề bài" là chỗ DUY NHẤT nói ra chênh lệch đó, cho mọi
 * target, nên không miền nào phải tự nhớ. Bài kiểm này khoá cả hai chiều: nó
 * phải hiện khi lệch, và tuyệt đối KHÔNG được hiện khi chưa lệch — một nhãn kêu
 * suốt sẽ bị học sinh học cách phớt lờ, đúng lúc nó cần được đọc.
 */

const CASES: [string, SimAction][] = [
  ["algorithm.count_if", { type: "set_param", name: "condition.op", value: "<" }],
  ["algorithm.sum_if", { type: "set_param", name: "condition.op", value: "<" }],
  ["binary.base_conversion", { type: "set_param", name: "targetBase", value: 8 }],
  ["binary.character_encoding", { type: "set_param", name: "text", value: "B" }],
  ["network.graph_traversal", { type: "set_param", name: "variant", value: "dfs" }],
  ["tree.traversal", { type: "set_param", name: "variant", value: "postorder" }],
  ["database.relational_table_query", { type: "set_param", name: "sort.direction", value: "asc" }],
  ["web.style_model", { type: "set_param", name: "fontSize", value: 32 }],
];

beforeEach(() => {
  if (listSimulations().length === 0) registerAllSimulations();
  useAppStore.getState().reset();
});

const load = (simId: string) => {
  const e = offlineCatalog().find((x) => x.simId === simId);
  if (!e) throw new Error(`không có mẫu cho ${simId}`);
  useAppStore.getState().loadEnvelope(e.envelope);
  const active = useAppStore.getState().active!;
  return { active, mod: getSimulation(simId)! as SimulationModule };
};

describe("W4B-4D · nhãn lệch-đề nói đúng lúc", () => {
  it("vừa mở bài ra thì KHÔNG target nào bị báo là đã đổi", () => {
    /* Vế chống-kêu-oan, và nó bắt được một lỗi thật lúc dựng: `web` giữ kiểu
       trong state nên phải tự dựng lại hình dạng config, mà nó không giữ `notes`
       của đề — so cả khối thì mọi đề có `notes` đều "đã đổi" ngay khi vừa mở. */
    const seen = new Set<string>();
    for (const entry of offlineCatalog()) {
      if (seen.has(entry.simId)) continue;
      seen.add(entry.simId);
      const mod = getSimulation(entry.simId) as SimulationModule | undefined;
      if (!mod) continue;
      const r = mod.validateConfig((entry.envelope as { config: unknown }).config);
      if (!r.ok) continue;
      expect(specDrift(mod, mod.init(r.config), r.config), `${entry.simId}: kêu oan lúc vừa mở`)
        .toBe(false);
    }
  });

  it("đổi một tham số thì nhãn bật, ở MỌI bài đổi được tham số", () => {
    for (const [simId, action] of CASES) {
      const { active, mod } = load(simId);
      const after = mod.apply(active.state, action);
      expect(after, `${simId}: action mẫu không đổi được state`).not.toBe(active.state);
      expect(specDrift(mod, after, active.config), `${simId}: đã đổi mà nhãn im`).toBe(true);
      useAppStore.getState().reset();
    }
  });

  it("đặt lại đúng giá trị cũ thì nhãn TẮT — so giá trị, không so tham chiếu", () => {
    /* `apply` luôn dựng config mới, nên một phép so tham chiếu sẽ báo "đã đổi"
       vĩnh viễn kể từ thao tác đầu tiên, kể cả khi học sinh vừa quay về đúng
       chỗ cũ. Đó là cách hỏng dễ xảy ra nhất và khó thấy nhất. */
    const { active, mod } = load("tree.traversal");
    const away = mod.apply(active.state, { type: "set_param", name: "variant", value: "postorder" });
    expect(specDrift(mod, away, active.config)).toBe(true);
    const back = mod.apply(away, { type: "set_param", name: "variant", value: "preorder" });
    expect(specDrift(mod, back, active.config), "về đúng đề rồi mà nhãn vẫn sáng").toBe(false);
  });

  it("module KHÔNG khai `currentConfig` thì không bao giờ có nhãn", () => {
    expect(specDrift({}, { anything: 1 }, { other: 2 })).toBe(false);
  });

  it("chỉ so ĐÚNG các khoá module khai — khoá không khai không tính là lệch", () => {
    const mod = { currentConfig: (s: { a: number }) => ({ a: s.a }) };
    expect(specDrift(mod, { a: 1 }, { a: 1, notes: "của đề" })).toBe(false);
    expect(specDrift(mod, { a: 2 }, { a: 1, notes: "của đề" })).toBe(true);
  });

  it("JSX của shell THẬT SỰ gọi hàm này và in đúng chuỗi ấy", () => {
    /* Hàm thuần đúng mà JSX quên gọi thì học sinh vẫn không thấy gì.
     *
     * ⚠️ KHÔNG kiểm được bằng `renderToString`: zustand trả TRẠNG THÁI ĐẦU cho
     * server snapshot, nên workspace luôn dựng ra màn hình rỗng dù store đã nạp
     * bài (`ARCHITECTURE_MAP §8` #13). Bản đầu của bài kiểm này SSR thật và vế
     * "chưa đổi thì chưa có nhãn" XANH — xanh vì trang rỗng, không vì nhãn tắt.
     * Một khẳng định đúng vì lý do sai còn tệ hơn không có.
     *
     * Nên ở tầng này chỉ khoá SỢI DÂY nối hàm ↔ JSX; còn nhãn hiện thật trên
     * màn hình thì chứng minh trong Chrome (`accept-experience-w4b4c.mjs`). */
    const src = readFileSync(new URL("../components/SimulationWorkspace.tsx", import.meta.url), "utf-8");
    expect(src, "shell không gọi specDrift").toMatch(/specDrift\(mod,\s*active\.state,\s*active\.config\)/);
    expect(src, "shell không in nhãn nào").toContain("Đã đổi so với đề bài");
  });
});
