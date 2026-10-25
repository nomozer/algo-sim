import { afterEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import * as THREE from "three";
import { Scene3DExplorer } from "./Scene3DExplorer";
import { buildObject3D } from "./scene3d-view";
import { PHONG_CACH_SCENE3D } from "./scene3d-roles";
import type { Scene3D, SceneObject } from "./scene3d-model";
import { tapKetQuaCuoi } from "./scene3d-model";
import fixture from "./scene3d-section-fixture.json";

// Seed the learner's actual open panels/selection; render the real component without WebGL.
const learner = vi.hoisted(() => ({ analysis: false, selected: null as string | null }));
vi.mock("react", async (importOriginal) => {
  const react = await importOriginal<typeof import("react")>();
  return { ...react, useLayoutEffect: react.useEffect, useState: (initial: unknown) => react.useState(() => {
    const value = typeof initial === "function" ? initial() : initial;
    if (value && typeof value === "object" && "selected_id" in value)
      return { ...value, selected_id: learner.selected, current_step: 999 };
    if (value instanceof Set) return new Set(learner.analysis ? ["phan-tich"] : []);
    return value;
  }) };
});
afterEach(() => { learner.analysis = false; learner.selected = null; });

const scene = fixture as unknown as Scene3D;
const section = scene.objects.find(o => o.type === "section")!;
const families = ["triangular_pyramid", "triangular_prism", "rectangular_pyramid", "cuboid", "cube", "regular_square_pyramid", "regular_triangular_pyramid"];
const officialScene = (family: string): Scene3D => JSON.parse(readFileSync(new URL(
  `../../../../../docs/evaluation/geometry/runs/visual-hybrid-final-corrections/visual/inputs/fixtures/${family}_positive.json`, import.meta.url), "utf8")).envelope.scene3d;

describe("Owner F1: one formula region per selected quantity", () => {
  it("a final distance without a formula appears only in analysis after selection", () => {
    const data = JSON.parse(readFileSync(new URL(
      "../../../../../docs/evaluation/geometry/runs/b3-distance-browser-e2e/fixtures.json", import.meta.url), "utf8"));
    const scene = data.fixtures.find((f: { expected: string }) => f.expected === "SERVE").envelope.scene3d as Scene3D;
    const result = scene.objects.find(o => tapKetQuaCuoi(scene).has(o.id) && o.value != null)!;
    expect(result).toBeDefined();
    expect(result.formula?.references).toEqual([]);
    learner.analysis = true;
    learner.selected = result.id;
    const html = renderToString(<Scene3DExplorer scene={scene} />);
    expect(html).toContain(`data-analysis-item="${result.id}"`);
    expect(html).not.toContain(`data-value-entity="${result.id}"`);
    expect(html).not.toContain(`data-formula-entity="${result.id}"`);
    // Mode B reveals the selected result's annotation on the canvas: the locked suite's `selection_per_quantity`
    // fails with ANNOTATION_MISSING otherwise (measured at 3c6d1e65, where this line asserted the opposite).
    expect(html).toContain(`data-ann-id="${result.id}"`);
    expect(html).toContain('href="#geo3d-bang-phan-tich"');
  });
  it.each(families)("%s keeps the explanation in analysis and links the inspector to it", family => {
    const scene = officialScene(family);
    learner.analysis = true;
    // Use a real backend measurement with a coherent formula.
    const quantity = scene.objects.find(o => o.formula && o.value != null && tapKetQuaCuoi(scene).has(o.id))!;
    expect(quantity).toBeDefined();
    learner.selected = quantity.id;
    const html = renderToString(<Scene3DExplorer scene={scene} />);
    expect(html).toContain("data-analysis-formula=");
    expect(html.includes(`data-formula-entity="${quantity.id}"`)).toBe(false);
    expect(html.includes('class="geo3d-soi-cong-thuc"')).toBe(false);
    expect(html).toContain('href="#geo3d-bang-phan-tich"');
    expect(html).toContain('data-panel="soi"');
  });

  it("preserves the inspector formula in Mode A for a non-final measurement", () => {
    const scene = officialScene("triangular_pyramid");
    const quantity = scene.objects.find(o => o.formula && o.value != null && !tapKetQuaCuoi(scene).has(o.id))!;
    learner.selected = quantity.id;
    const html = renderToString(<Scene3DExplorer scene={scene} />);
    expect(html).toContain(`data-formula-entity="${quantity.id}"`);
    expect(html).not.toContain("data-math-analysis-panel");
  });
});

function borderColors(object: THREE.Object3D): number[] {
  const colors: number[] = [];
  object.traverse(child => {
    if (!child.name.startsWith("polygon_border:")) return;
    const material = (child as THREE.Line).material as THREE.LineBasicMaterial;
    if (material?.color) colors.push(material.color.getHex());
  });
  return colors;
}

describe("Owner F2: selected section preserves semantic fill and geometry", () => {
  it.each(["section", "polygon3"] as const)("highlights only the selected %s boundary in cobalt", type => {
    const input: SceneObject = { ...section, type, surface_role: "SECTION_REGION" };
    const before = JSON.stringify(input);
    const neutral = buildObject3D(input, false)!;
    const selected = buildObject3D(input, "dich")!;
    expect(borderColors(neutral)).toContain(0xc85a32);
    expect(borderColors(selected)).toContain(0x2563eb);
    const fills: THREE.Mesh[] = [];
    selected.traverse(child => { if (child.name.startsWith("section_fill:") || child.name.startsWith("polygon_fill:")) fills.push(child as THREE.Mesh); });
    expect(fills.length).toBeGreaterThan(0);
    expect((fills[0].material as THREE.MeshBasicMaterial).color.getHex()).toBe(PHONG_CACH_SCENE3D.colors.polygon);
    expect(JSON.stringify(input)).toBe(before);
    expect(borderColors(buildObject3D(input, false)!)).toEqual(borderColors(neutral));
  });
});

it("Owner P3.3: a standalone sphere has one presentation reference and no extra meridians", () => {
  const sphere: SceneObject = { id: "sphere", label: "Mặt cầu", type: "curved_solid", render: "curved_solid",
    origin: "derived", producer: "construct_curved", depends: [], curved_kind: "ball",
    anchor: ["0", "0", "0"], radius_sq: "25", height_sq: "0" };
  const object = buildObject3D(sphere, false)!;
  let lines = 0;
  object.traverse(child => { if ((child as THREE.Line).isLine) lines++; });
  expect(lines).toBe(2); // solid and dashed rendering passes of one circle, never two scene entities
  const reference = object.getObjectByName("sphere_reference:sphere")!;
  expect(reference.userData.presentationReference.authoritative).toBe(false);
  const referenceLines: THREE.Line[] = [];
  reference.traverse(child => { if ((child as THREE.Line).isLine) referenceLines.push(child as THREE.Line); });
  expect(referenceLines).toHaveLength(lines);
});
