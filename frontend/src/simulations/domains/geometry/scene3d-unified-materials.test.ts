import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { buildObject3D, canonicalEdgeMaterial, disposeScene3DObject, updateCanonicalEdgeVisibility } from "./scene3d-view";
import * as roles from "./scene3d-roles";
import type { Scene3D, SceneObject } from "./scene3d-model";

const common = { label: "Miền", origin: "derived", producer: null, depends: [] } as const;
const polygon: SceneObject = { ...common, depends: [], id: "polygon", type: "section", render: "polygon", closed: true,
  surface_role: "SECTION_REGION", polygon: [["0", "0", "1"], ["2", "0", "1"], ["0", "2", "1"]] };
const circle: SceneObject = { ...common, depends: [], id: "circle", type: "circle3", render: "circle",
  surface_role: "SECTION_REGION", center: ["0", "0", "1"], normal: ["0", "0", "1"], radius_sq: "4" };
const ellipse: SceneObject = { ...circle, id: "ellipse", type: "ellipse3", render: "ellipse", major_dir: ["1", "0", "0"],
  minor_dir: ["0", "1", "0"], semi_major_sq: "4", semi_minor_sq: "1" };
const solid: SceneObject = { ...common, depends: [], id: "solid", type: "solid", render: "mesh",
  vertex_ids: ["A", "B", "C", "S"],
  vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"], ["0", "0", "3"]],
  faces: [[0, 2, 1], [0, 1, 3], [1, 2, 3], [2, 0, 3]] };
const fill = (o: SceneObject, selected = false, xray = false) => {
  const built = buildObject3D(o, selected, undefined, undefined, undefined, undefined, undefined, xray)!;
  return built.getObjectByName(`section_fill:${o.id}`) as THREE.Mesh<THREE.BufferGeometry, THREE.MeshBasicMaterial>;
};
const shell = (o: SceneObject, selected = false) => {
  const built = buildObject3D(o, selected)!;
  return built.children.find(n => n instanceof THREE.Mesh && (n.material as THREE.Material).colorWrite !== false) as THREE.Mesh<THREE.BufferGeometry, THREE.MeshStandardMaterial>;
};

describe("shared semantic material behavior", () => {
  it("uses one section language for polygon, circle and ellipse, including selection and explicit X-ray", () => {
    for (const selected of [false, true]) {
      const materials = [polygon, circle, ellipse].map(o => fill(o, selected).material);
      expect(new Set(materials.map(m => m.color.getHex())).size).toBe(1);
      expect(new Set(materials.map(m => m.opacity)).size).toBe(1);
      for (const m of materials) {
        expect(m.isMeshBasicMaterial).toBe(true); // lighting cannot change semantic section fill
        expect(m.forceSinglePass).toBe(true); // a flat region needs only one draw submission
        expect(m.depthTest).toBe(true);
        expect(m.depthWrite).toBe(false);
      }
    }
    for (const o of [polygon, circle, ellipse]) {
      expect(fill(o, false, true).material.depthTest).toBe(false);
      expect(fill(o).renderOrder).toBe(7);
    }
  });

  it("keeps base regions structural rather than recoloring them as sections", () => {
    const base = { ...polygon, id: "base", type: "polygon3", surface_role: "BASE_REGION" as const };
    const built = buildObject3D(base, false)!;
    const material = (built.getObjectByName("polygon_fill:base") as THREE.Mesh).material as THREE.MeshBasicMaterial;
    expect(material.color.getHex()).not.toBe(fill(polygon).material.color.getHex());
    expect(material.isMeshBasicMaterial).toBe(true);
  });

  it("gives a metadata-free constructed polygon the same section fallback as circle/ellipse", () => {
    // Pre-metadata envelopes (e.g. saved public samples) carry neither surface_role nor formation_roles; the
    // backend now tags such a construct_polygon AUXILIARY_SURFACE. Fallback must not differ by mesh technique.
    const legacy: SceneObject = { ...polygon, id: "legacy", type: "polygon3", surface_role: undefined };
    const auxiliary: SceneObject = { ...polygon, id: "aux", type: "polygon3", surface_role: "AUXILIARY_SURFACE" };
    const untypedCircle: SceneObject = { ...circle, id: "untyped_circle", surface_role: undefined };
    const reference = fill(polygon).material;
    for (const o of [legacy, auxiliary, untypedCircle]) {
      const built = buildObject3D(o, false)!;
      const mesh = (built.getObjectByName(`section_fill:${o.id}`) ?? built.getObjectByName(`polygon_fill:${o.id}`)) as THREE.Mesh;
      const material = mesh.material as THREE.MeshBasicMaterial;
      expect([o.id, material.color.getHex(), material.opacity]).toEqual([o.id, reference.color.getHex(), reference.opacity]);
    }
    expect(roles.vaiTroMien({ ...polygon, type: "polygon3", surface_role: undefined, formation_roles: ["CONSTRUCT_BASE"] })).toBe("base");
  });

  it("does not submit transparent flat rim ribbons twice", () => {
    for (const o of [circle, ellipse]) {
      const built = buildObject3D(o, false)!;
      built.traverse(n => {
        const m = (n as THREE.Mesh).material as THREE.Material | undefined;
        if (m?.transparent && m.side === THREE.DoubleSide && m.colorWrite !== false) expect(m.forceSinglePass).toBe(true);
      });
    }
  });

  it("shares selected shell emphasis across polyhedra and every curved solid", () => {
    const expected = shell(solid, true).material;
    expect(expected.opacity).toBeGreaterThan(shell(solid).material.opacity);
    for (const kind of ["cylinder", "cone", "ball"] as const) {
      const curved: SceneObject = { ...common, depends: [], id: kind, type: "curved_solid", render: "curved_solid",
        curved_kind: kind, anchor: ["0", "0", "0"], radius_sq: "4", height_sq: "9" };
      const material = shell(curved, true).material;
      expect(material.color.getHex()).toBe(expected.color.getHex());
      expect(material.opacity).toBe(expected.opacity);
      expect(material.depthWrite).toBe(false);
    }
  });

  it("subordinates hidden ink without losing its dash or overriding CPU visibility during selection", () => {
    for (const selected of [false, true]) {
      const visible = canonicalEdgeMaterial(false, selected);
      const hidden = canonicalEdgeMaterial(true, selected);
      expect(hidden).toBeInstanceOf(THREE.LineDashedMaterial);
      expect(hidden.opacity).toBeLessThan(visible.opacity * 0.8);
      expect(hidden.depthTest).toBe(false);
      expect(hidden.depthWrite).toBe(false);
      expect((hidden as THREE.LineDashedMaterial).gapSize).toBeGreaterThan(0);
    }
  });

  it("assigns solid roles by complete construction history, independent of object array order", () => {
    const scene: Scene3D = { free_objects: [], objects: [{ ...solid, id: "later" }, { ...solid, id: "earlier" }],
      events: [{ step_index: 1, action: "CREATE", object: "earlier", depends: [], explanation: "" },
        { step_index: 2, action: "CREATE", object: "later", depends: [], explanation: "" }] };
    const serialized = JSON.stringify(scene);
    const assign = roles.vaiTroKhoi;
    expect(typeof assign).toBe("function");
    const assigned = assign(scene);
    expect(assigned.get("earlier")).toBe("primary");
    expect(assigned.get("later")).toBe("secondary");
    expect([...assign({ ...scene, objects: [...scene.objects].reverse() })]).toEqual([...assigned]);
    // Hide/isolate/step consume this full-scene map, never reassign a visible subset.
    expect(["later"].map(id => assigned.get(id))).toEqual(["secondary"]);
    expect(JSON.stringify(scene)).toBe(serialized);
  });

  it("leaves scene geometry and authoritative data unchanged while building and selecting every region", () => {
    const objects = [solid, polygon, circle, ellipse];
    const before = JSON.stringify(objects);
    for (const o of objects) for (const selected of [false, true]) buildObject3D(o, selected);
    expect(JSON.stringify(objects)).toBe(before);
  });

  it("reuses encountered edge materials over repeated camera sweeps instead of recreating them with spans", () => {
    const root = new THREE.Group();
    root.add(buildObject3D(solid, false)!);
    const camera = new THREE.PerspectiveCamera(50, 1.6, 0.1, 200);
    const seen = new Set<string>();
    const materials = new Map<string, THREE.Material>();
    const sweep = () => {
      for (const position of [[8, 3, 6], [-8, -3, 6], [8, -3, 6], [-8, 3, 6]]) {
        camera.position.set(position[0], position[1], position[2]);
        camera.lookAt(0, 0, 1);
        camera.updateMatrixWorld();
        updateCanonicalEdgeVisibility(root, camera, "1440x900@1");
        root.traverse(n => {
          if (n.parent?.userData.visualOwnerId) {
            const material = (n as THREE.Line).material as THREE.Material;
            seen.add(material.uuid);
            materials.set(material.uuid, material);
          }
        });
      }
    };
    sweep();
    const afterWarmup = seen.size;
    expect(afterWarmup).toBeGreaterThan(0);
    sweep(); sweep();
    expect(seen.size).toBe(afterWarmup);
    const disposed: string[] = [];
    for (const material of materials.values()) material.addEventListener("dispose", () => disposed.push(material.uuid));
    disposeScene3DObject(root);
    expect(disposed.sort()).toEqual([...materials.keys()].sort()); // includes inactive encountered styles, exactly once
  });
});
