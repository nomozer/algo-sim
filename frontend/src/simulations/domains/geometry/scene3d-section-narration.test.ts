import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { Scene3D, SceneObject } from "./scene3d-model";
import { buildPedagogicalStepNarration, pedagogicalStepList } from "./scene3d-semantic-policy";
import { sectionDetails } from "./scene3d-subentities";

const fixtures: { id: string; scene: Scene3D }[] = JSON.parse(readFileSync(new URL(
  "../../../../../docs/evaluation/geometry/runs/axo-final-educational-viewer-readiness/section-fixtures.json", import.meta.url), "utf8"));
const symbol = (o: SceneObject | undefined) => o?.notation ?? o?.label ?? "";
const narration = (scene: Scene3D, sec: SceneObject) => {
  const steps = pedagogicalStepList(scene).filter(s => s.targetIds.includes(sec.id));
  expect(steps.length).toBeGreaterThan(0);
  return buildPedagogicalStepNarration(scene, steps.at(-1)!);
};

describe("closed section narration consumes certified topology", () => {
  for (const fixture of fixtures) it(`covers every face trace and anonymous vertex: ${fixture.id}`, () => {
    const scene = structuredClone(fixture.scene);
    const before = JSON.stringify(scene);
    for (const sec of scene.objects.filter(o => o.type === "section")) {
      const nar = narration(scene, sec);
      const traceLines = nar.detailedEvidence.filter(s => s.startsWith("Trên mặt "));
      expect(traceLines).toHaveLength(sec.steps!.length);
      const solid = scene.objects.find(o => o.type === "solid" && sec.depends.includes(o.id))!;
      const names = sectionDetails(scene, sec.id)!.vertexNames;
      sec.vertex_sources!.forEach((source, i) => {
        if (/^[A-Z][A-Za-z0-9′']*$/u.test(names[i]!)) return;
        if (source.kind !== "SOLID_EDGE_INTERSECTION") return;
        const edge = source.solid_edge_vertex_indices!.map(j => symbol(scene.objects.find(o => o.id === solid.vertex_ids![j]))).join("");
        expect(nar.conciseRationale).toContain(edge);
        expect(traceLines.join(" ")).toContain(`giao điểm của ${edge} với mặt phẳng cắt`);
      });
      // The external line–plane point is not among certified polygon vertices or the new topology explanation.
      if (fixture.id.includes("exterior")) expect([nar.conciseRationale, ...traceLines].join(" ")).not.toMatch(/\bQ\b/u);
    }
    expect(JSON.stringify(scene)).toBe(before);
  });

  it("is independent of point notation and object order", () => {
    const scene = structuredClone(fixtures.find(f => f.id.includes("exterior"))!.scene);
    const letters = "SABCDMNP", replacements = "TKLQRUVW";
    const rename = (s: string) => s.replace(/[SABCDMNP]/gu, c => replacements[letters.indexOf(c)]!);
    for (const o of scene.objects) {
      if (o.notation) o.notation = rename(o.notation);
      if (o.type === "point3" && /^[A-Z]$/u.test(o.label)) o.label = rename(o.label);
    }
    scene.objects.reverse();
    const sec = scene.objects.find(o => o.type === "section")!;
    const nar = narration(scene, sec);
    expect(nar.conciseRationale).toContain(rename("CD"));
    expect(nar.conciseRationale).toContain(rename("AD"));
    expect(nar.detailedEvidence.filter(s => s.startsWith("Trên mặt "))).toHaveLength(5);
  });

  it("does not invent topology when provenance is absent", () => {
    const scene = structuredClone(fixtures.find(f => f.id.includes("exterior"))!.scene);
    const sec = scene.objects.find(o => o.type === "section")!;
    delete sec.vertex_sources;
    expect(narration(scene, sec).detailedEvidence.filter(s => s.startsWith("Trên mặt "))).toHaveLength(0);
  });

  it("still explains an edge cut when a constructed point has no short name", () => {
    const scene = structuredClone(fixtures.find(f => f.id.includes("exterior"))!.scene);
    const point = scene.objects.find(o => o.type === "point3" && o.notation === "N")!;
    point.notation = null; point.label = "Giao điểm được dựng";
    const sec = scene.objects.find(o => o.type === "section")!;
    const nar = narration(scene, sec);
    expect(nar.conciseRationale).toContain("SB");
    expect(nar.detailedEvidence.filter(s => s.startsWith("Trên mặt "))).toHaveLength(5);
    expect(nar.conciseRationale).not.toMatch(/\bN\b/u);
  });
});
