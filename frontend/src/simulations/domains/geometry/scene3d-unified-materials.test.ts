import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  boVanhDayTrung, buildObject3D, canonicalEdgeMaterial, datKhoiCongKhongChe, disposeScene3DObject, updateCanonicalEdgeVisibility,
} from "./scene3d-view";
import * as roles from "./scene3d-roles";
import type { Scene3D, SceneObject } from "./scene3d-model";
import { diemVanhCongBiChe, classifyWorldSegmentVisibility, type CurvedSolidVolumeMeta } from "./scene3d-edge-visibility";

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

describe("curved visibility follows the ray and finite solid", () => {
  const v = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);
  const volume = (kind: CurvedSolidVolumeMeta["kind"]): CurvedSolidVolumeMeta => ({
    id: "volume", kind, anchor: v(0, 0, 0), top: kind === "ball" ? null : v(0, 0, 2), radius: 1, height: 2,
  });

  it("hides a sphere point just beyond the perspective silhouette", () => {
    expect(diemVanhCongBiChe(v(1, 0, 0), v(0.9, 10, 0), [volume("ball")])).toBe(true);
    expect(diemVanhCongBiChe(v(1, 0, 0), v(1.1, 10, 0), [volume("ball")])).toBe(false);
    expect(diemVanhCongBiChe(v(1, 0, 0), v(1, 10, 0), [volume("ball")])).toBe(false);
  });

  it("detects a small sphere far along the eye ray without clipping off its end", () => {
    expect(diemVanhCongBiChe(v(-1, 0, 0), v(10000, 0, 0), [volume("ball")])).toBe(true);
    expect(diemVanhCongBiChe(v(-2, 0, 0), v(10000, 0, 0), [volume("ball")])).toBe(true);
    expect(diemVanhCongBiChe(v(1, 0, 0), v(10000, 0, 0), [volume("ball")])).toBe(false);
  });

  it.each(["cylinder", "cone"] as const)("%s side classification matches the independent outward normal across camera rotations", kind => {
    const solid = volume(kind);
    const p = v(kind === "cone" ? 0.5 : 1, 0, 1);
    const normal = v(1, 0, kind === "cone" ? 0.5 : 0);
    for (const z of [-4, 1, 6]) for (let i = 0; i < 48; i += 1) {
      const eye = v(8 * Math.cos(i * Math.PI / 24), 8 * Math.sin(i * Math.PI / 24), z);
      const facing = normal.dot(eye.clone().sub(p));
      if (Math.abs(facing) < 1e-8) continue;
      expect(diemVanhCongBiChe(p, eye, [solid]), `${kind}, camera=${eye.toArray()}`).toBe(facing < 0);
    }
  });

  it("respects cylinder caps, including axial rays and bottom views", () => {
    const solid = volume("cylinder");
    expect(diemVanhCongBiChe(v(0, 0, 0), v(0, 0, 5), [solid])).toBe(true);
    expect(diemVanhCongBiChe(v(0, 0, 2), v(0, 0, 5), [solid])).toBe(false);
    expect(diemVanhCongBiChe(v(0, 0, 0), v(0, 0, -5), [solid])).toBe(false);
    expect(diemVanhCongBiChe(v(1, 0, 2), v(-5, 0, 5), [solid])).toBe(false);
    expect(diemVanhCongBiChe(v(1, 0, 0), v(-5, 0, -5), [solid])).toBe(false);
  });

  it("splits a line partly covered by a curved solid and changes visibility with camera", () => {
    const ball = { ...volume("ball"), anchor: v(0, 0, 3) };
    const spans = classifyWorldSegmentVisibility(v(-3, 0, 0), v(3, 0, 0), v(0, 0, 10), [], { curved_occluders: [ball] }).spans;
    expect(spans.map(s => s.visibility)).toEqual(["VISIBLE", "HIDDEN", "VISIBLE"]);
    const reverse = classifyWorldSegmentVisibility(v(-3, 0, 0), v(3, 0, 0), v(0, 0, -10), [], { curved_occluders: [ball] }).spans;
    expect(reverse.map(s => s.visibility)).toEqual(["VISIBLE"]);
  });

  it("uses the same curved occluder for a degenerate sampled rim segment", () => {
    const ball = { ...volume("ball"), anchor: v(0, 0, 3) };
    expect(classifyWorldSegmentVisibility(v(0, 0, 0), v(0, 0, 0), v(0, 0, 10), [], { curved_occluders: [ball] }).spans[0].visibility).toBe("HIDDEN");
  });
});

describe("shared semantic material behavior", () => {
  it("sphere outline is the camera tangent circle rather than an equator", () => {
    const input: SceneObject = { ...common, depends: [], id: "sphere", type: "curved_solid", render: "curved_solid",
      curved_kind: "ball", anchor: ["1", "2", "3"], radius_sq: "4", height_sq: "0" };
    const root = new THREE.Group(), built = buildObject3D(input, false)!;
    root.add(built);
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    for (const eye of [[9, 4, 5], [-7, -4, 5], [7, 4, -5]]) {
      camera.position.set(...eye as [number, number, number]); camera.lookAt(1, 2, 3); camera.updateMatrixWorld();
      updateCanonicalEdgeVisibility(root, camera);
      const outline = built.getObjectByName("sphere_silhouette:sphere") as THREE.Mesh;
      expect(outline).toBeDefined();
      built.updateMatrixWorld(true);
      const point = new THREE.Vector3(1, 0, 0).applyMatrix4(outline.matrixWorld);
      const radial = point.clone().sub(new THREE.Vector3(1, 2, 3));
      expect(radial.length()).toBeCloseTo(2, 5);
      expect(radial.dot(camera.position.clone().sub(point))).toBeCloseTo(0, 5);
    }
  });
  it.each(["cylinder", "cone"] as const)("%s renders its physical rims and camera-tangent generators without inventing scene entities", kind => {
    const input: SceneObject = { ...common, depends: [], id: kind, type: "curved_solid", render: "curved_solid",
      curved_kind: kind, anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "3"], radius_sq: "4", height_sq: "9" };
    const before = JSON.stringify(input), root = new THREE.Group();
    const built = buildObject3D(input, false)!;
    root.add(built);
    const rims: THREE.Object3D[] = [];
    built.traverse(n => { if (n.userData.curvedRimLoop) rims.push(n); });
    expect(rims).toHaveLength(kind === "cylinder" ? 2 : 1);
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    for (const eye of [[7, 4, 5], [-7, -4, 5], [7, 4, -5]]) {
      camera.position.set(...eye as [number, number, number]); camera.lookAt(0, 0, 1); camera.updateMatrixWorld();
      updateCanonicalEdgeVisibility(root, camera);
      const silhouette = built.getObjectByName(`curved_silhouette:${kind}`)!;
      expect(silhouette).toBeDefined();
      expect(silhouette.visible).toBe(true);
      for (const line of silhouette.children as THREE.Line[]) {
        const p = new THREE.Vector3().fromBufferAttribute(line.geometry.getAttribute("position"), 0);
        expect(Math.hypot(p.x, p.y)).toBeCloseTo(2, 5);
        const normal = new THREE.Vector3(p.x / 2, p.y / 2, kind === "cone" ? 2 / 3 : 0);
        expect(normal.dot(camera.position.clone().sub(p))).toBeCloseTo(0, 5);
      }
    }
    expect(JSON.stringify(input)).toBe(before);
  });
  it("hover is distinct from selection and preserves the neutral section fill", () => {
    for (const o of [polygon, circle, ellipse]) {
      const hovered = buildObject3D(o, "hover")!;
      const material = (hovered.getObjectByName(`section_fill:${o.id}`) as THREE.Mesh).material as THREE.MeshBasicMaterial;
      expect(material.color.getHex()).toBe(0xc85a32);
      expect(material.opacity).toBe(fill(o).material.opacity);
      const colors: number[] = [];
      hovered.traverse(n => {
        const m = (n as THREE.Mesh).material as THREE.MeshBasicMaterial | undefined;
        if (m?.color && m.colorWrite !== false && !n.name.startsWith("section_fill:")) colors.push(m.color.getHex());
      });
      expect(colors).toContain(0x0f766e);
      expect(colors).not.toContain(0x2563eb);
    }
  });
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
      // Same section depth semantics too: drawn after shells, revealed only by explicit X-ray.
      const xray = buildObject3D(o, false, undefined, undefined, undefined, undefined, undefined, true)!;
      const xrayMesh = (xray.getObjectByName(`section_fill:${o.id}`) ?? xray.getObjectByName(`polygon_fill:${o.id}`)) as THREE.Mesh;
      expect([o.id, mesh.renderOrder, (mesh.material as THREE.Material).depthTest, (xrayMesh.material as THREE.Material).depthTest])
        .toEqual([o.id, fill(polygon).renderOrder, true, false]);
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

  it("queues the front curve rim with the solid outlines so it is drawn over them", () => {
    // three.js draws the opaque queue first; renderOrder only orders within a queue. An opaque rim was therefore
    // overdrawn by the (transparent-queue) cylinder generator where both meet near tangency.
    const cylinder: SceneObject = { ...common, depends: [], id: "cyl", type: "curved_solid", render: "curved_solid",
      curved_kind: "cylinder", anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "3"], radius_sq: "4", height_sq: "9" };
    const generator = buildObject3D(cylinder, false)!.getObjectByName("curved_generator:cyl:0") as THREE.Line;
    expect((generator.material as THREE.Material).transparent).toBe(true);
    for (const o of [circle, ellipse]) for (const selected of [false, "dich"] as const) {
      let front: THREE.Mesh | undefined;
      buildObject3D(o, selected)!.traverse(n => { front ??= n.userData.curvedRimLoop?.thayMesh; });
      expect([o.id, (front!.material as THREE.Material).transparent]).toEqual([o.id, true]);
      expect(front!.renderOrder).toBeGreaterThan(generator.renderOrder);
    }
  });

  it("strokes every drawn rim chord with a 1px line that cannot collapse when the region is seen edge-on", () => {
    const cylinder: SceneObject = { ...common, depends: [], id: "cyl", type: "curved_solid", render: "curved_solid",
      curved_kind: "cylinder", anchor: ["0", "0", "-2"], apex_or_top: ["0", "0", "3"], radius_sq: "4", height_sq: "25" };
    for (const o of [circle, ellipse]) {
      const root = new THREE.Group(), built = buildObject3D(o, "dich")!;
      root.add(buildObject3D(cylinder, false)!, built);
      let rim: { thayMesh: THREE.Mesh; khuatMesh: THREE.Mesh; thayNet: THREE.LineSegments; khuatNet: THREE.LineSegments } | undefined;
      built.traverse(n => { rim ??= n.userData.curvedRimLoop; });
      expect(rim!.thayNet.material).toBe(rim!.thayMesh.material);
      expect(rim!.khuatNet.material).toBe(rim!.khuatMesh.material);
      const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
      for (const eye of [null, [9, 4, 5], [0.5, 9, 1.2]] as const) {
        if (eye) {
          camera.position.set(eye[0], eye[1], eye[2]); camera.lookAt(0, 0, 1); camera.updateMatrixWorld();
          updateCanonicalEdgeVisibility(root, camera);
        }
        // a ribbon chord is 6 vertices, a stroke chord 2: both must carry exactly the same chords
        expect(rim!.thayNet.geometry.drawRange.count * 3).toBe(rim!.thayMesh.geometry.drawRange.count);
        expect(rim!.khuatNet.geometry.drawRange.count * 3).toBe(rim!.khuatMesh.geometry.drawRange.count);
      }
      expect(rim!.khuatNet.geometry.drawRange.count).toBeGreaterThan(0); // the side view hides part of the rim
    }
  });

  /* Internal review 2026-10-25 (C1, I1, I2). */
  const ball: SceneObject = { ...common, depends: [], id: "ball", type: "curved_solid", render: "curved_solid",
    curved_kind: "ball", anchor: ["1", "1", "3/2"], radius_sq: "5" };
  const lookFrom = (eye: [number, number, number]) => {
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.set(...eye); camera.lookAt(1, 1, 1.5); camera.updateMatrixWorld();
    return camera;
  };

  it("never shows a silhouette that no camera update has placed", () => {
    const cylinder: SceneObject = { ...ball, id: "cyl", curved_kind: "cylinder", apex_or_top: ["1", "1", "3"], height_sq: "9/4" };
    for (const o of [ball, cylinder]) {
      const built = buildObject3D(o, false)!;
      const outline = built.getObjectByName(`sphere_silhouette:${o.id}`) ?? built.getObjectByName(`curved_silhouette:${o.id}`);
      expect([o.id, outline!.visible]).toEqual([o.id, false]);
    }
  });

  it("places the silhouette of a curved solid that does not occlude (secondary solid sharing the primary's frame)", () => {
    const root = new THREE.Group(), built = buildObject3D(ball, false)!;
    root.add(built);
    datKhoiCongKhongChe(built);
    updateCanonicalEdgeVisibility(root, lookFrom([12, 9, 10]));
    const outline = built.getObjectByName("sphere_silhouette:ball")!;
    expect(outline.visible).toBe(true);
    expect(outline.position.distanceTo(new THREE.Vector3(1, 1, 1.5))).toBeGreaterThan(0); // moved off the anchor, toward the eye
    expect(Math.hypot(outline.scale.x - 1)).toBeGreaterThan(1e-6);                       // not the unplaced unit ring
  });

  it("classifies a polyhedron's edges by solid faces only, also when a curved solid encloses it", () => {
    const hiddenWith = (withBall: boolean) => {
      const root = new THREE.Group();
      if (withBall) root.add(buildObject3D(ball, false)!);
      root.add(buildObject3D(solid, false)!);
      return updateCanonicalEdgeVisibility(root, lookFrom([12, 9, 10])).hidden_edge_ids;
    };
    expect(hiddenWith(false).length).toBeLessThan(6);
    expect(hiddenWith(true)).toEqual(hiddenWith(false));
  });

  it("lets a backend circle own a cap rim: the solid drops its own rim at the same centre, radius and axis", () => {
    const cylinder: SceneObject = { ...common, depends: [], id: "cyl", type: "curved_solid", render: "curved_solid",
      curved_kind: "cylinder", anchor: ["0", "0", "0"], apex_or_top: ["0", "0", "3"], radius_sq: "4", height_sq: "9" };
    const cap = (center: [string, string, string], extra: Partial<SceneObject> = {}): SceneObject =>
      ({ ...circle, id: `c${center[2]}`, center, normal: ["0", "0", "1"], radius_sq: "4", ...extra });
    const rims = (others: SceneObject[]) => {
      const built = buildObject3D(cylinder, false)!;
      boVanhDayTrung(built, cylinder, others);
      const out: THREE.Object3D[] = [];
      built.traverse(n => { if (n.userData.curvedRimLoop) out.push(n); });
      return out.length;
    };
    expect(rims([])).toBe(2);
    expect(rims([cap(["0", "0", "0"])])).toBe(1);
    expect(rims([cap(["0", "0", "0"]), cap(["0", "0", "3"], { normal: ["0", "0", "-2"] })])).toBe(0); // opposite normal: same circle
    expect(rims([cap(["0", "0", "0"], { radius_sq: "1" }), cap(["0", "0", "3"], { normal: ["1", "0", "0"] })])).toBe(2);
    expect(rims([{ ...cap(["0", "0", "0"]), type: "ellipse3" }])).toBe(2);
  });

  it("keeps both cap rims of a cylinder given by height, and matches caps on a tilted fractional axis (review round 2)", () => {
    const count = (o: SceneObject, others: SceneObject[]) => {
      const built = buildObject3D(o, false)!;
      boVanhDayTrung(built, o, others);
      let n = 0;
      built.traverse(x => { if (x.userData.curvedRimLoop) n += 1; });
      return n;
    };
    const byHeight: SceneObject = { ...common, depends: [], id: "h", type: "curved_solid", render: "curved_solid",
      curved_kind: "cylinder", anchor: ["0", "0", "0"], apex_or_top: null, radius_sq: "1", height_sq: "9/4" } as SceneObject;
    expect(count(byHeight, [])).toBe(2);
    expect(count(byHeight, [{ ...circle, id: "top", center: ["0", "0", "3/2"], radius_sq: "1" }])).toBe(1);
    const tilted: SceneObject = { ...byHeight, id: "t", apex_or_top: ["1/3", "2/3", "2/3"], radius_sq: "1/4", height_sq: "1" };
    const capOn = (center: [string, string, string]): SceneObject => ({ ...circle, id: `c${center[0]}`, center, normal: ["1", "2", "2"], radius_sq: "1/4" });
    expect(count(tilted, [capOn(["0", "0", "0"]), capOn(["1/3", "2/3", "2/3"])])).toBe(0);
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

/* f2-role-aware-oracle — the ellipse rim band must lie INSIDE the curve whatever the handedness of the envelope's
 * (major_dir, minor_dir, normal). With a left-handed frame (as served for the p6 oblique cylinder cut) the band went
 * outside and the selected cobalt boundary lost its front arc in the browser. */
describe("ellipse rim band orientation", () => {
  const inward = (o: SceneObject) => {
    const g = buildObject3D(o, "dich")!;
    let meta: { trong: THREE.Vector3[]; ngoai: THREE.Vector3[] } | undefined;
    g.traverse((x) => { meta ??= x.userData.curvedRimLoop; });
    return meta!.ngoai.every((p, i) => meta!.trong[i].length() < p.length());
  };
  it("right-handed frame", () => expect(inward(ellipse)).toBe(true));
  it("left-handed frame", () => expect(inward({ ...ellipse, normal: ["0", "0", "-1"] })).toBe(true));
});
