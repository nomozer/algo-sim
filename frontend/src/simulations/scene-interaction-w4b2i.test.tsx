import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { ALGORITHM_IDS, type AlgorithmId } from "../core/types";
import { makeAlgorithmModule } from "./domains/algorithm/index";
import { AlgorithmWorkspace } from "./domains/algorithm/ui";
import type { AlgorithmSimState } from "./domains/algorithm/model";
import {
  searchInteractionOf,
  searchSceneRegions,
  stageInteractionsOf,
} from "./domains/algorithm/decision";
import { ArrayView } from "../components/ArrayView";

import { commitmentSurfaceKind } from "./domains/algorithm/interaction-policy";

/**
 * W4B-2I — HÀNH ĐỘNG GẮN VÀO SÂN KHẤU (họ tìm kiếm).
 *
 * Điều wave này phải chứng minh KHÔNG phải là "nút nhỏ đi" mà là: học sinh tác
 * động lên CHÍNH vùng mà hành động ảnh hưởng, engine vẫn là bên chấm duy nhất,
 * và không sinh ra bề mặt cam kết thứ hai.
 */

const DATA: Partial<Record<AlgorithmId, Record<string, unknown>>> = {
  binary_search: { array: [2, 4, 5, 7, 8, 9, 11], target: 9 },
  linear_search: { array: [4, 9, 2, 7, 5, 8], target: 7 },
};

function build(id: AlgorithmId) {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: {}, algorithm_id: id, data: DATA[id]!, data_generated: false, notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) as AlgorithmSimState };
}

const at = (s: AlgorithmSimState, cursor: number): AlgorithmSimState => ({ ...s, cursor });

function firstActionable(s: AlgorithmSimState): number {
  for (let i = 0; i < s.trace.steps.length; i += 1) {
    if (stageInteractionsOf(at(s, i)).length > 0) return i;
  }
  throw new Error("không có bước nào cam kết được");
}

/** Bóc chú thích — repo CỐ Ý nhắc tên thứ đã bỏ để ghi lại vì sao bỏ. */
const code = (src: string) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");

const SEARCH_IDS = ALGORITHM_IDS.filter((id) => DATA[id] !== undefined);

/* ══ 1. ÁNH XẠ NGỮ NGHĨA → VÙNG CỘT ═══════════════════════════════════════ */

describe("W4B-2I · searchSceneRegions — ngữ nghĩa sở hữu ánh xạ, không phải renderer", () => {
  it("cả hai bài tìm kiếm đều có fixture — thiếu thì bất biến phủ hụt", () => {
    expect(SEARCH_IDS.sort()).toEqual(["binary_search", "linear_search"]);
  });

  it("binary_search: nửa trái / phần tử giữa / nửa phải ra ĐÚNG cột của vùng xét", () => {
    const { state } = build("binary_search");
    const cur = at(state, firstActionable(state));
    const model = searchInteractionOf(cur)!;
    const { left, right, middle } = model.activeRange!;
    const regions = searchSceneRegions(model, 7)!;
    expect(regions).not.toBeNull();

    const byId = new Map(regions.map((r) => [r.id, r.indices]));
    /* ĐẢO NGHĨA (xem chú thích đầu khối binary ở decision.ts): option `right`
       nghĩa là nửa PHẢI bị loại ⇒ tìm tiếp ở nửa TRÁI. Nếu ánh xạ bị viết thẳng
       tên-sang-tên thì test này đỏ — đó chính là chỗ dễ ship bug nhất. */
    for (const [id, expected] of [
      ["right", Array.from({ length: middle - left }, (_, k) => left + k)],
      ["left", Array.from({ length: right - middle }, (_, k) => middle + 1 + k)],
    ] as const) {
      if (byId.has(id)) expect(byId.get(id), `option ${id}`).toEqual(expected);
    }
    if (byId.has("found")) expect(byId.get("found")).toEqual([middle]);
  });

  it("linear_search: phần tử đang xét = 1 cột, phần còn lại = đuôi dãy", () => {
    const { state } = build("linear_search");
    const cur = at(state, firstActionable(state));
    const model = searchInteractionOf(cur)!;
    const regions = searchSceneRegions(model, 6)!;
    const byRole = new Map(
      model.actions.map((a) => [a.visualRole, regions.find((r) => r.id === a.id)!.indices]),
    );
    expect(byRole.get("current-item")).toEqual([model.currentIndex]);
    expect(byRole.get("continue-region")).toEqual(
      Array.from({ length: 6 - model.currentIndex - 1 }, (_, k) => model.currentIndex + 1 + k),
    );
  });

  it("mọi vùng đều KHÔNG RỖNG và KHÔNG chồng cột — nếu không thì trả null", () => {
    for (const id of SEARCH_IDS) {
      const { state } = build(id);
      for (let k = 0; k < state.trace.steps.length; k += 1) {
        const model = searchInteractionOf(at(state, k));
        if (!model) continue;
        const regions = searchSceneRegions(model, (DATA[id]!.array as number[]).length);
        if (regions === null) continue;
        const all = regions.flatMap((r) => r.indices);
        expect(all.length, `${id}@${k}: vùng rỗng`).toBeGreaterThan(0);
        expect(new Set(all).size, `${id}@${k}: hai hành động trùng cột`).toBe(all.length);
      }
    }
  });

  it("TẤT CẢ-HOẶC-KHÔNG: nửa rỗng ⇒ null, không sinh trạng thái lai nửa-vùng-nửa-nút", () => {
    const { state } = build("binary_search");
    const cur = at(state, firstActionable(state));
    const model = searchInteractionOf(cur)!;
    // Vùng xét thu về đúng một phần tử ⇒ cả hai nửa đều rỗng.
    const degenerate = { ...model, activeRange: { left: 3, right: 3, middle: 3 } };
    expect(searchSceneRegions(degenerate, 7)).toBeNull();
  });

  it("KHÔNG RÒ ĐÁP ÁN: vùng chỉ mang id/nhãn/chỉ số", () => {
    for (const id of SEARCH_IDS) {
      const { state } = build(id);
      const model = searchInteractionOf(at(state, firstActionable(state)))!;
      const regions = searchSceneRegions(model, (DATA[id]!.array as number[]).length);
      for (const r of regions ?? []) {
        expect(Object.keys(r).sort()).toEqual(["id", "indices", "label"]);
      }
    }
  });
});

/* ══ 2. SÂN KHẤU LÀ NÚT THẬT, KỂ CẢ VỚI BÀN PHÍM ══════════════════════════ */

describe("W4B-2I · KEYBOARD_INTERACTION — thao tác trực tiếp KHÔNG chỉ dành cho chuột", () => {
  const stageHtml = (disabled = false) => {
    const { state } = build("binary_search");
    const cur = at(state, firstActionable(state));
    const model = searchInteractionOf(cur)!;
    return renderToString(
      <ArrayView
        step={cur.trace.steps[cur.cursor]}
        labels={null}
        regions={searchSceneRegions(model, 7)}
        onRegionAct={() => {}}
        regionsDisabled={disabled}
      />,
    );
  };

  it("mỗi vùng có role=button, vào được bằng Tab, và có TÊN đọc lên được", () => {
    const html = stageHtml();
    const roles = html.match(/role="button"/g) ?? [];
    expect(roles.length, "không có vùng bấm nào trên sân khấu").toBeGreaterThanOrEqual(2);
    expect((html.match(/tabindex="0"/g) ?? []).length).toBe(roles.length);
    expect((html.match(/aria-label="[^"]+"/g) ?? []).length).toBeGreaterThanOrEqual(roles.length);
  });

  it("svg KHÔNG còn là role=img khi có vùng bấm — nếu không, vùng tàng hình với AT", () => {
    expect(stageHtml()).toContain('role="group"');
    // Không có vùng ⇒ giữ nguyên hành vi cũ, không đổi một pixel.
    const { state } = build("binary_search");
    const plain = renderToString(
      <ArrayView step={state.trace.steps[0]} labels={null} />,
    );
    expect(plain).toContain('role="img"');
    expect(plain).not.toContain('role="button"');
  });

  it("đã cam kết ⇒ vùng còn THẤY được nhưng rời khỏi thứ tự Tab", () => {
    const html = stageHtml(true);
    expect(html).toContain('aria-disabled="true"');
    expect(html).toContain('tabindex="-1"');
    expect(html).not.toContain('tabindex="0"');
  });

  it("Enter/Space được nối tay và CHẶN nổi bọt — Space không được cướp làm Tự chạy", () => {
    const src = readFileSync(new URL("../components/ArrayView.tsx", import.meta.url), "utf-8");
    expect(src).toMatch(/e\.key === "Enter" \|\| e\.key === " "/);
    expect(src).toContain("stopPropagation");
    expect(src).toContain("preventDefault");
  });
});

/* ══ 3. ĐÚNG MỘT BỀ MẶT CAM KẾT ═══════════════════════════════════════════ */

describe("W4B-2I · NO_DUPLICATE_DETACHED_QUIZ_SURFACE", () => {
  /* Bốn tổ hợp, và điều phải giữ là KHÔNG tổ hợp nào cho ra hai bề mặt. Luật
     này từng nằm trong JSX của `AlgorithmWorkspace` và một lần tiêm lỗi
     (`actionsHidden={false}`) đã đi lọt toàn bộ suite — `labOpen` là state cục
     bộ nên SSR chỉ thấy trạng thái ĐÓNG, nơi cả hai đều vắng. */
  it("commitmentSurfaceKind: mọi tổ hợp cho ĐÚNG MỘT hình thức, không bao giờ hai", () => {
    expect(commitmentSurfaceKind(false, false)).toBe("none");
    expect(commitmentSurfaceKind(false, true)).toBe("none");
    expect(commitmentSurfaceKind(true, false)).toBe("buttons");
    expect(commitmentSurfaceKind(true, true)).toBe("scene");
  });

  /* it("`actionsHidden…") ĐÃ XOÁ 2026-08-21 (Task 10b).
     Kiem hang nut hanh dong cua vung cam ket — W13 go ca hang nut lan vung cam ket. */

  /* it("zone ở hình thức …") ĐÃ XOÁ 2026-08-21 (Task 10b).
     Kiem hang nut hanh dong cua vung cam ket — W13 go ca hang nut lan vung cam ket. */

  it("sân khấu sở hữu hành động ⇒ hàng nút rời BIẾN MẤT", () => {
    const { config, state } = build("binary_search");
    const cur = at(state, firstActionable(state));
    const model = searchInteractionOf(cur)!;
    expect(searchSceneRegions(model, 7), "fixture này phải gắn được sân khấu").not.toBeNull();

    // Quan sát: cổng đóng ⇒ không vùng bấm, không hàng nút.
    const observe = renderToString(
      <AlgorithmWorkspace config={config} state={cur} busy={false} dispatch={() => {}} />,
    );
    expect(observe, "Quan sát bày vùng bấm cam kết").not.toContain('role="button"');
    expect(observe).not.toContain("search-actions");
  });

  it("nhãn hành động của vùng bấm khớp NGUYÊN VĂN nhãn engine cấp", () => {
    for (const id of SEARCH_IDS) {
      const { state } = build(id);
      const model = searchInteractionOf(at(state, firstActionable(state)))!;
      const regions = searchSceneRegions(model, (DATA[id]!.array as number[]).length) ?? [];
      for (const r of regions) {
        const action = model.actions.find((a) => a.id === r.id)!;
        expect(r.label, `${id}: renderer tự chế nhãn`).toBe(action.label);
      }
    }
  });
});

/* ══ 4. ENGINE VẪN LÀ BÊN CHẤM DUY NHẤT ═══════════════════════════════════ */

describe("W4B-2I · ENGINE_OWNS_ACTION_VERDICT trên đường sân khấu", () => {
  /* ĐÃ XOÁ 2026-08-21 (Task 10b) — it("id vùng bấm LÀ option id của engine ⇒ nộp thẳng qua predict.check"
     Kiem duong predict.check — W13 go co chu dich. */

  /* ĐÃ XOÁ 2026-08-21 (Task 10b) — it("WRONG_DIRECT_ACTION_PRESERVES_CANONICAL_STATE — sai không đụng can
     Kiem duong predict.check — W13 go co chu dich. */

  it("ArrayView KHÔNG tự chấm và KHÔNG tự suy ra vùng nào ứng hành động nào", () => {
    const src = code(readFileSync(new URL("../components/ArrayView.tsx", import.meta.url), "utf-8"));
    for (const forbidden of [
      "correctActionId", "isCorrect(", "checkAnswer(", "evaluate(",
      // Renderer biết "nửa trái" nghĩa là gì = renderer sở hữu ngữ nghĩa thuật toán.
      "left-region", "right-region", "middle-item", "activeRange", "algorithm_id",
    ]) {
      expect(src, `ArrayView sở hữu ngữ nghĩa (${forbidden})`).not.toContain(forbidden);
    }
  });

  it("ArrayView nộp ĐÚNG id engine cấp — không viết lại ở khoảnh khắc phát", () => {
    /* W4B-3A — LỖ HỔNG DO TIÊM LỖI BẮT ĐƯỢC, không phải phòng xa.
     *
     * Hai guard trên kiểm MÔ HÌNH vùng (id khớp option engine) và một DANH SÁCH
     * TỪ CẤM trong nguồn. Tiêm lỗi
     *     onRegionAct?.(r.id === "left" ? "correct" : r.id)
     * đi lọt cả hai: mô hình không đổi, và không dùng từ nào trong danh sách —
     * nhưng renderer vừa tự quyết định một cam kết là ĐÚNG. Đó chính là bất biến
     * #11 (chỉ engine tất định mới được phán) bị thủng ngay tại chỗ phát.
     *
     * Nên khoá vào chính ĐỐI SỐ: id đi ra phải là id của vùng, nguyên vẹn. */
    const src = code(readFileSync(new URL("../components/ArrayView.tsx", import.meta.url), "utf-8"));
    const calls = [...src.matchAll(/onRegionAct\?\.\(([^)]*)\)/g)].map((m) => m[1].trim());
    // Phép dò phải thật sự dò: 0 lượt khớp trông y hệt một regex hỏng.
    expect(calls.length, "không tìm thấy chỗ phát nào — regex hỏng?").toBeGreaterThan(0);
    for (const arg of calls) {
      expect(arg, `renderer viết lại id trước khi nộp: onRegionAct(${arg})`).toBe("r.id");
    }
  });
});
