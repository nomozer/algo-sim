import { beforeAll, describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { getSimulation, listSimulations } from "./registry";
import { registerAllSimulations } from "./index";
import {
  availableVisualModes,
  rendererFor,
  representationPolicyOf,
  representationPolicyProblems,
  type RepresentationPolicy,
} from "./renderer";

/**
 * W4B-2R — CHÍNH SÁCH BIỂU DIỄN TRÊN TOÀN DANH MỤC.
 *
 * §44: danh sách target phải DẪN XUẤT TỪ REGISTRY, không chép tay. Một guard
 * chép tay 22 cái tên sẽ vẫn xanh khi target thứ 23 ra đời mà không ai phân loại
 * nó — tức là im lặng đúng lúc cần nói nhất.
 */

beforeAll(() => {
  if (listSimulations().length === 0) registerAllSimulations();
});

/* `listSimulations()` trả META (id/title/modes), không phải module — meta không
   mang `Workspace`/`renderers`/`threeD` nên chính sách không đọc được từ đó.
   Lấy id từ registry (vẫn là nguồn dẫn xuất, §44) rồi tra ngược ra module thật. */
const mods = () => listSimulations().map((meta) => getSimulation(meta.id)!);

describe("W4B-2R · CATALOG_HAS_EXACTLY_ONE_REPRESENTATION_POLICY_PER_TARGET", () => {
  it("registry có target, và mỗi id xuất hiện ĐÚNG một lần", () => {
    const ids = mods().map((m) => m.id);
    expect(ids.length).toBeGreaterThan(0);
    expect(new Set(ids).size, `id trùng: ${ids.join(", ")}`).toBe(ids.length);
  });

  it("mỗi target phân loại được vào ĐÚNG MỘT chính sách", () => {
    const legal: RepresentationPolicy[] = ["2d_only", "3d_only", "2d_and_3d_justified"];
    for (const m of mods()) {
      const p = representationPolicyOf(m);
      expect(legal, `${m.id}: chính sách lạ "${p}"`).toContain(p);
    }
  });

  it("NO_2D_3D_BY_DEFAULT — không target nào vi phạm chính sách", () => {
    const problems = mods().flatMap(representationPolicyProblems);
    expect(problems, problems.join("\n")).toEqual([]);
  });

  it("phân bố hiện tại: đúng MỘT target 2D+3D, và đó là 3D SƯ PHẠM", () => {
    /* Con số này CỐ Ý được khoá. Nếu một wave sau thêm 3D cho target khác, test
       này đỏ và buộc phải viết ra lý do sư phạm — chứ không lặng lẽ trôi về
       "sản phẩm có 3D ở nhiều chỗ". */
    const both = mods().filter((m) => representationPolicyOf(m) === "2d_and_3d_justified");
    expect(both.map((m) => m.id)).toEqual(["network.protocol_encapsulation"]);
    expect(both[0].threeD?.role).toBe("pedagogical");
    expect(both[0].threeD?.meaningOfZ).toContain("tầng");
  });

  it("không target nào là 3D_ONLY — và đó là kết quả HỢP LỆ, không phải thiếu sót", () => {
    expect(mods().filter((m) => representationPolicyOf(m) === "3d_only")).toEqual([]);
  });
});

describe("W4B-2R · 2D_ONLY_HAS_NO_3D_RUNTIME_TOGGLE", () => {
  it("target 2D_ONLY: không mode 3D khả dụng, không renderer 3D, không khai threeD", () => {
    for (const m of mods()) {
      if (representationPolicyOf(m) !== "2d_only") continue;
      expect(availableVisualModes(m), `${m.id}`).toEqual(["2d"]);
      expect(rendererFor(m, "3d"), `${m.id}: còn renderer 3D treo`).toBeUndefined();
      expect(m.threeD, `${m.id}: còn khai threeD`).toBeUndefined();
    }
  });

  it("`packet_routing` ĐÃ chuyển sang 2D_ONLY (hồi quy có tên)", () => {
    /* Không phải test thừa: đây là target DUY NHẤT đổi chính sách ở wave này, và
       lý do là chính nó tự khai `architectural_poc` = chiều sâu chỉ là bố cục. */
    const m = mods().find((x) => x.id === "network.packet_routing")!;
    expect(representationPolicyOf(m)).toBe("2d_only");
    expect(availableVisualModes(m)).toEqual(["2d"]);
  });

  it("toggle chỉ dựng khi có ≥2 mode ⇒ 2D_ONLY không bao giờ thấy toggle", () => {
    for (const m of mods()) {
      if (representationPolicyOf(m) === "2d_only") {
        expect(availableVisualModes(m).length, `${m.id}`).toBeLessThan(2);
      }
    }
  });
});

describe("W4B-2R · BOTH_REQUIRES_SHARED_ENGINE_TRUTH", () => {
  it("2D và 3D của cùng target là CÙNG module — không fork engine, không id riêng", () => {
    for (const m of mods()) {
      if (representationPolicyOf(m) !== "2d_and_3d_justified") continue;
      // Cùng một `SimulationModule` ⇒ cùng init/apply/timeline/predict theo định nghĩa.
      expect(rendererFor(m, "2d")).toBeDefined();
      expect(rendererFor(m, "3d")).toBeDefined();
      expect(rendererFor(m, "2d")).not.toBe(rendererFor(m, "3d"));
      expect(m.id, "3D không được có simulation_id riêng").not.toMatch(/_?3d$/i);
    }
  });
});

describe("W4B-2R · REPRESENTATION_POLICY_NOT_CONTEXT_STRING_DRIVEN", () => {
  it("chủ sở hữu chính sách không đọc tiêu đề/đề bài/ngữ cảnh", () => {
    const src = readFileSync(new URL("./renderer.ts", import.meta.url), "utf-8")
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/^\s*\/\/.*$/gm, "");
    /* Kiểm TRƯỜNG NGỮ CẢNH, không kiểm chữ "includes(" — `effectiveVisualMode`
       dùng `Array.includes` hoàn toàn hợp lệ, cấm nó là cấm nhầm chính cơ chế
       dẫn xuất mà wave này dựng lên. */
    for (const forbidden of ["title", "summary", "problem", "description", "notes"]) {
      expect(src, `renderer.ts rẽ nhánh theo ngữ cảnh (${forbidden})`).not.toContain(forbidden);
    }
    // …và không switch-case theo simulation_id.
    expect(src).not.toMatch(/id\s*===\s*["']/);

    /* `modes.includes("3d")` là HỢP LỆ — "3d" là một giá trị của enum năng lực
       `VisualMode`, không phải chuỗi ngữ cảnh. Điều thật sự phải cấm là chủ sở
       hữu chính sách chạm vào tầng dữ liệu/đề bài, nên khẳng định trên IMPORT:
       nó chỉ được biết `./types`, không biết config, envelope hay store. */
    const imports = [...src.matchAll(/from\s+["']([^"']+)["']/g)].map((m) => m[1]);
    expect(imports.sort()).toEqual(["./types", "react"]);
  });
});
