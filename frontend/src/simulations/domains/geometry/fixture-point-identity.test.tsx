import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import type { Scene3D, SceneObject } from "./scene3d-model";

/**
 * Lời đề của fixture TỔNG HỢP "Khối chóp và khối thành phần" (family07) dùng trong `measure-axo-performance.mjs`.
 * Lời đề gốc trong audit_scenes.json (bằng chứng đóng băng, không sửa) dùng CÙNG chữ D cho hai điểm khác nhau:
 * trung điểm của SA và đỉnh của khối chóp thứ hai. Cảnh đã tách thành `D` (trung điểm) và `D1` (đỉnh), nên lời đề
 * hiển thị phải gọi đúng như cảnh. Harness đọc hằng này bằng `fixture("DENSE_MULTI_SOLID_STATEMENT", …)`.
 */
const DENSE_MULTI_SOLID_STATEMENT =
  "Cho hai hình chóp S.ABC và D1.ABC có chung mặt đáy ABC là tam giác vuông cân tại A với AB = AC = 2. Biết SA vuông góc với mặt phẳng (ABC) và SA = 6; đỉnh D1 của hình chóp thứ hai nằm cùng phía với S, D1A vuông góc với (ABC) và D1A = 2. Gọi D là trung điểm của SA. Dựng hai khối chóp.";

type Row = { id: string; problem_text?: string; scene?: Scene3D };
const rows: Row[] = JSON.parse(readFileSync(new URL("../../../../../docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json", import.meta.url), "utf8"));
const family07 = rows.find(r => r.id.startsWith("family07"))!.scene!;
const pt = (s: Scene3D, id: string) => s.objects.find(o => o.id === id && o.type === "point3") as SceneObject & { xyz: string[] };
const q = (v: string) => { const [n, d = "1"] = v.split("/"); return Number(n) / Number(d); };
const vec = (s: Scene3D, a: string, b: string) => pt(s, b).xyz.map((v, i) => q(v) - q(pt(s, a).xyz[i]!));
const gramSq = (s: Scene3D, v: number[]) => {
  const g = (s.chart_metric ?? [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]]).map(r => r.map(q));
  return v.reduce((acc, vi, i) => acc + v.reduce((a2, vj, j) => a2 + vi * g[i]![j]! * vj, 0), 0);
};
const symbol = (o: SceneObject) => o.notation || o.id;

describe("fixture point identity and relations", () => {
  const scenes = [
    ...rows.filter(r => r.scene?.objects).map(r => ({ id: r.id, scene: r.scene! })),
    ...GEOMETRY_SAMPLES.map(s => ({ id: `sample:${s.id}`, scene: (s.envelope as unknown as { scene3d: Scene3D }).scene3d })),
  ];

  it.each(scenes.map(s => [s.id, s.scene] as const))("%s: no two points share a symbol or a position", (_id, scene) => {
    const pts = scene.objects.filter(o => o.type === "point3");
    const syms = pts.map(symbol);
    expect(new Set(syms).size, `duplicate symbols ${syms}`).toBe(syms.length);
    const pos = pts.map(p => (p.xyz ?? []).join(","));
    expect(new Set(pos).size, `duplicate positions ${pos}`).toBe(pos.length);
  });

  it("family07: D is the midpoint of SA, D1 is a distinct apex with D1A ⊥ (ABC) and D1A = 2, SA = 6 (exact, scene metric)", () => {
    const s = family07;
    expect(pt(s, "D").xyz.map(q)).toEqual(pt(s, "A").xyz.map((a, i) => (q(a) + q(pt(s, "S").xyz[i]!)) / 2));
    expect(pt(s, "D").producer).toBe("construct_point.midpoint");
    expect(pt(s, "D1").xyz).not.toEqual(pt(s, "D").xyz);
    expect(gramSq(s, vec(s, "A", "S"))).toBe(36);
    expect(gramSq(s, vec(s, "A", "D1"))).toBe(4);
    expect(gramSq(s, vec(s, "A", "B"))).toBe(4);
    expect(gramSq(s, vec(s, "A", "C"))).toBe(4);
    // D1A ⊥ AB và D1A ⊥ AC theo metric của cảnh ⇒ D1A ⊥ (ABC)
    const g = (u: number[], v: number[]) => (gramSq(s, u.map((x, i) => x + v[i]!)) - gramSq(s, u) - gramSq(s, v)) / 2;
    expect(g(vec(s, "A", "D1"), vec(s, "A", "B"))).toBe(0);
    expect(g(vec(s, "A", "D1"), vec(s, "A", "C"))).toBe(0);
  });

  it("family07: the presented statement names points exactly as the scene does (no letter used twice)", () => {
    const syms = new Set(family07.objects.filter(o => o.type === "point3").map(symbol));
    const mentioned = new Set(DENSE_MULTI_SOLID_STATEMENT.match(/\b[A-Z]\d?(?=[^a-zà-ỹ]|$)/gu) ?? []);
    for (const m of mentioned) expect(syms.has(m), `statement mentions ${m}`).toBe(true);
    expect(DENSE_MULTI_SOLID_STATEMENT).toMatch(/D là trung điểm của SA/u);
    expect(DENSE_MULTI_SOLID_STATEMENT).not.toMatch(/\bD\.ABC|\bDA\b/u);
    expect(pt(family07, "D1").label).toContain("D1");
  });

  it("family07: no step or annotation shows the computed volumes", () => {
    const anchors = [0, 9999];
    for (const a of anchors) {
      const html = renderToString(<AxoWorkspaceV62 scene={family07} initialStep={a} de={DENSE_MULTI_SOLID_STATEMENT} />);
      expect(html).not.toMatch(/4\/3|bằng 4\b|Thể tích [^<]* bằng/u);
      expect(html).not.toMatch(/KẾT LUẬN|Xem kết quả|dock-goal-conclusion/u);
    }
  });
});
