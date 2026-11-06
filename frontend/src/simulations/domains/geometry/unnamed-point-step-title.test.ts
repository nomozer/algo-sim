import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { docPhanHoiPhanTich } from "../../../llm/client";
import { buildPedagogicalConstructionPlan } from "./scene3d-semantic-policy";
import { withSubEntities } from "./scene3d-subentities";

/**
 * A step that drops a perpendicular onto a plane names the foot only when the foot HAS a short name. The real Hybrid /4
 * response below (sphere tangent to (AMBC), offline backend route) has an unnamed foot whose display label is a
 * description ("Hình chiếu của I lên (ABC)"); spliced into "Hạ hình chiếu vuông góc {foot} của I lên (ABC)" it read
 * "Hạ hình chiếu vuông góc Hình chiếu của I lên (ABC) của I lên (ABC)".
 */
const fx = JSON.parse(readFileSync(resolve(__dirname,
  "../../../../../docs/evaluation/geometry/runs/axo-hybrid4-capability-scene3d-reliability/fixtures/tangent-plane-sphere-response.json"),
"utf8")) as { response: unknown };

describe("projection step titles with unnamed feet", () => {
  it("never splice a description into the sentence; named feet keep their name", () => {
    const env = docPhanHoiPhanTich(fx.response) as unknown as { status: string; scene3d: Parameters<typeof withSubEntities>[0] };
    expect(env.status).toBe("ok");
    const titles = buildPedagogicalConstructionPlan(withSubEntities(env.scene3d)).steps.map((s) => s.title);
    const projections = titles.filter((t) => t.startsWith("Hạ hình chiếu vuông góc"));
    expect(projections.length).toBeGreaterThanOrEqual(2);
    for (const t of projections) {
      expect(t).not.toMatch(/vuông góc Hình chiếu/u);
      expect(t.match(/ của /gu)?.length ?? 0).toBe(1);
    }
    expect(projections).toContain("Hạ hình chiếu vuông góc H của I lên (AMC)");
    expect(projections).toContain("Hạ hình chiếu vuông góc của I lên (ABC)");
  });
});
