import { describe, expect, it } from "vitest";
import * as THREE from "three";
import samplesData from "../../../data/geometry-samples.json";
import circumFixture from "./scene3d-circumsphere-fixture.json";
import {
  cauTrucGocNhin,
  diemNeoNhanMatPhang,
  moRongDaGiacMatPhang,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";
import { chonHuongNhin } from "./scene3d-camera";
import { dongBoNetDayManHinh } from "./scene3d-edge-visibility";
import {
  buildObject3D,
  datCoGocVuong,
  doanNhuongCanh,
  updateCanonicalEdgeVisibility,
} from "./scene3d-view";

type SampleItem = {
  id: string;
  envelope: {
    scene3d: Scene3D;
  };
};

const SAMPLES = ((samplesData as unknown as { samples?: SampleItem[]; items?: SampleItem[] }).samples
  ?? (samplesData as unknown as { items?: SampleItem[] }).items
  ?? []) as SampleItem[];
const sampleScene = (id: string): Scene3D => {
  const found = SAMPLES.find((s) => s.id === id);
  if (!found) throw new Error(`Missing sample: ${id}`);
  return found.envelope.scene3d;
};

const makeCamera = (pos: [number, number, number], target: [number, number, number] = [0, 0, 2]) => {
  const cam = new THREE.PerspectiveCamera(42, 1440 / 900, 0.1, 200);
  cam.position.set(...pos);
  cam.lookAt(...target);
  cam.updateMatrixWorld(true);
  cam.updateProjectionMatrix();
  return cam;
};

describe("Scene3D final-frame shared visual quality upgrades", () => {
  it("renders curved rims (circle3, ellipse3, cylinder caps, sphere reference) via uniform screen-space fat segments without buffer churn", () => {
    const cylinder: SceneObject = {
      id: "cyl",
      label: "Hình trụ",
      type: "curved_solid",
      render: "curved_solid",
      origin: "derived",
      producer: "construct_curved_solid",
      depends: [],
      curved_kind: "cylinder",
      anchor: ["0", "0", "0"],
      apex_or_top: ["0", "0", "6"],
      radius_sq: "4",
      height_sq: "36",
    };
    const ellipse: SceneObject = {
      id: "sec_el",
      label: "Thiết diện elip",
      type: "ellipse3",
      render: "ellipse",
      origin: "derived",
      producer: "intersect_plane_curved_ellipse",
      depends: ["cyl"],
      surface_role: "SECTION_REGION",
      center: ["0", "0", "3"],
      normal: ["-1", "0", "2"],
      major_dir: ["2", "0", "1"],
      minor_dir: ["0", "1", "0"],
      semi_major_sq: "5",
      semi_minor_sq: "4",
    };
    const sphere: SceneObject = {
      id: "ball",
      label: "Mặt cầu",
      type: "curved_solid",
      render: "curved_solid",
      origin: "derived",
      producer: "construct_curved_solid",
      depends: [],
      curved_kind: "ball",
      anchor: ["8", "0", "3"],
      radius_sq: "4",
      height_sq: "0",
    };

    const root = new THREE.Group();
    root.add(
      buildObject3D(cylinder, false)!,
      buildObject3D(ellipse, false)!,
      buildObject3D(sphere, false)!,
    );

    const camA = makeCamera([12, 4, 7], [2, 0, 3]);
    updateCanonicalEdgeVisibility(root, camA, "1440x900@1");

    const fatGroup = new THREE.Group();
    const summaryA = dongBoNetDayManHinh([root], fatGroup, 1440, 900);

    // Raw world-space flat ribbons & 1px rim segments must be listed in sourceRimObjects
    // so WebGL render hides foreshortened flat ribbons while keeping metadata intact.
    expect(summaryA.sourceRimObjects.length).toBeGreaterThanOrEqual(8);

    const activeFatRims = fatGroup.children.filter(
      (c) => c.visible && c.name.startsWith("fat_rim:"),
    ) as unknown as {
      name: string;
      geometry: THREE.BufferGeometry;
      material: { linewidth: number };
    }[];
    expect(activeFatRims.length).toBeGreaterThanOrEqual(4);
    for (const rimSeg of activeFatRims) {
      expect(rimSeg.material.linewidth).toBeGreaterThan(1.4);
    }

    // Section ellipse visible rim must match section stroke hierarchy (> base cylinder rim > sphere reference rim), with NO artificial sphere_silhouette
    const ellipseVis = activeFatRims.find((c) => c.name.includes("sec_el") && c.name.endsWith(":thay"));
    const cylBaseVis = activeFatRims.find((c) => c.name.includes("cyl") && c.name.endsWith(":thay"));
    const sphereRefVis = activeFatRims.find((c) => c.name.includes("ball") && c.name.endsWith(":thay"));
    const sphereSil = fatGroup.getObjectByName("fat:sphere_silhouette:ball");
    expect(ellipseVis).toBeDefined();
    expect(cylBaseVis).toBeDefined();
    expect(sphereRefVis).toBeDefined();
    expect(sphereSil).toBeUndefined();
    expect(ellipseVis!.material.linewidth).toBeGreaterThan(cylBaseVis!.material.linewidth);
    expect(cylBaseVis!.material.linewidth).toBeGreaterThan(sphereRefVis!.material.linewidth);

    // Orbiting camera must update pooled LineSegments2 buffers in-place without replacing geometries
    const geomBefore = new Map(activeFatRims.map((c) => [c.name, c.geometry]));
    const camB = makeCamera([-10, 7, 6], [2, 0, 3]);
    updateCanonicalEdgeVisibility(root, camB, "1440x900@1");
    dongBoNetDayManHinh([root], fatGroup, 1440, 900);
    for (const [name, g0] of geomBefore) {
      const after = fatGroup.children.find((c) => c.name === name) as THREE.Mesh | undefined;
      if (after?.visible) {
        expect(after.geometry).toBe(g0);
      }
    }
  });

  it("extracts curved-solid axis and base topology in cauTrucGocNhin so oblique cylinders avoid axial barrel camera views", () => {
    const obliqueScene = sampleScene("tru-truc-xien");
    const ct = cauTrucGocNhin(obliqueScene.objects);
    expect(ct.canh.length).toBeGreaterThan(0);

    const cyl = obliqueScene.objects.find((o) => o.type === "curved_solid")!;
    expect(cyl.anchor).toBeDefined();
    expect(cyl.apex_or_top).toBeDefined();
    const axis = new THREE.Vector3(
      Number(cyl.apex_or_top![0]) - Number(cyl.anchor![0]),
      Number(cyl.apex_or_top![1]) - Number(cyl.anchor![1]),
      Number(cyl.apex_or_top![2]) - Number(cyl.anchor![2]),
    ).normalize();

    const dir = new THREE.Vector3(...chonHuongNhin(ct.diem, ct.canh, ct.mat)).normalize();
    const sinAxisView = axis.clone().cross(dir).length();
    // Previously fallback [8, 5, 6] looked nearly down the slanted axis (sin < 0.25);
    // general topology-aware camera selection must give a clear side-elevated view (sin >= 0.45).
    expect(sinAxisView).toBeGreaterThanOrEqual(0.45);
  });

  it("gives apex cutting planes a clear margin and places plane notation badges outside the cross-section interior", () => {
    const chopScene = sampleScene("thiet-dien-chop");
    const plane = chopScene.objects.find((o) => o.type === "plane3")!;
    const sec = chopScene.objects.find((o) => o.type === "section")!;
    const pts = chopScene.objects
      .filter((o) => o.xyz)
      .map((o) => o.xyz!.map((v) => {
        const [a, b] = v.split("/");
        return b ? Number(a) / Number(b) : Number(a);
      }) as [number, number, number]);

    const p0 = plane.point!.map((v) => {
      const [a, b] = v.split("/");
      return b ? Number(a) / Number(b) : Number(a);
    }) as [number, number, number];
    const n = plane.normal!.map((v) => {
      const [a, b] = v.split("/");
      return b ? Number(a) / Number(b) : Number(a);
    }) as [number, number, number];

    const sheet = moRongDaGiacMatPhang(p0, n, pts);
    expect(sheet).not.toBeNull();
    const neo = diemNeoNhanMatPhang(p0, n, pts);
    expect(neo).not.toBeNull();

    const secPts = (sec.polygon ?? sec.vertices ?? []).map((p) =>
      p.map((v) => {
        const [a, b] = v.split("/");
        return b ? Number(a) / Number(b) : Number(a);
      }) as [number, number, number],
    );
    const sheetDiag = Math.max(
      ...sheet!.flatMap((a) => sheet!.map((b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]))),
    );
    const secDiag = Math.max(
      ...secPts.flatMap((a) => secPts.map((b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]))),
    );
    // Extended plane patch must clearly frame the apex section rather than hugging it within 3%
    expect(sheetDiag).toBeGreaterThan(secDiag * 1.42);

    // Projected 2D anchor for (MNP) must lie strictly outside the projected 2D triangle MNP
    const cam = makeCamera([8, 3, 6], [1.5, 1.5, 1.5]);
    const proj2 = (p: [number, number, number]): [number, number] => {
      const v = new THREE.Vector3(...p).project(cam);
      return [((v.x + 1) / 2) * 1440, ((1 - v.y) / 2) * 900];
    };
    const tri2 = secPts.slice(0, 3).map(proj2);
    const neo2 = proj2(neo!);
    const cross2 = (o: [number, number], a: [number, number], b: [number, number]) =>
      (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const c0 = cross2(tri2[0], tri2[1], neo2);
    const c1 = cross2(tri2[1], tri2[2], neo2);
    const c2 = cross2(tri2[2], tri2[0], neo2);
    const insideTri = (c0 >= 0 && c1 >= 0 && c2 >= 0) || (c0 <= 0 && c1 <= 0 && c2 <= 0);
    expect(insideTri).toBe(false);
  });

  it("yields solid-face polygon3 objects to their constructed parent solid so combined solids are not painted as cross-sections", () => {
    const scene = circumFixture as unknown as Scene3D;
    const facePolys = scene.objects.filter(
      (o) => o.type === "polygon3" && (o.display_group ?? []).includes("face") && o.parent === "OABC",
    );
    expect(facePolys).toHaveLength(4);
    const nhuong = doanNhuongCanh(scene.objects, () => "0,0,0");
    for (const f of facePolys) {
      expect(nhuong.has(f.id)).toBe(true);
      const built = buildObject3D({ ...f, display_role: "hit_proxy" }, false)!;
      expect(built.getObjectByName(`polygon_fill:${f.id}`)).toBeUndefined();
      expect(built.getObjectByName(`polygon_border:${f.id}:thay`)).toBeUndefined();
    }
  });

  it("supports toggling right-angle markers and hidden dashed strokes off/on without mutating geometry data", () => {
    const mpScene = sampleScene("mp-vuong-goc-duong");
    const segWithPerp = mpScene.objects.find((o) => o.perpendicular_witness?.marker)
      ?? ({
        id: "sa",
        label: "SA",
        type: "segment3",
        render: "segment",
        origin: "derived",
        producer: "construct_segment",
        depends: [],
        point_a: ["0", "0", "0"],
        point_b: ["0", "0", "4"],
        perpendicular_witness: {
          from: "S",
          foot_id: "A",
          on: "day",
          relation: "line_perp_plane",
          foot: ["0", "0", "0"],
          marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
        },
      } as SceneObject);
    const solid = mpScene.objects.find((o) => o.type === "solid")!;

    const root = new THREE.Group();
    root.add(buildObject3D(solid, false)!, buildObject3D(segWithPerp, false)!);
    const cam = makeCamera([8, 4, 6], [1, 1, 1.5]);
    updateCanonicalEdgeVisibility(root, cam, "1440x900@1");

    expect(datCoGocVuong([root], cam, 900, undefined, true)).toBeGreaterThan(0);
    expect(datCoGocVuong([root], cam, 900, undefined, false)).toBe(0);

    const fatGroup = new THREE.Group();
    dongBoNetDayManHinh([root], fatGroup, 1440, 900, true);
    const dashedWhenOn = fatGroup.children.filter(
      (c) => c.visible && (c as unknown as { material?: { dashed?: boolean } }).material?.dashed === true,
    );
    expect(dashedWhenOn.length).toBeGreaterThan(0);

    dongBoNetDayManHinh([root], fatGroup, 1440, 900, false);
    const dashedWhenOff = fatGroup.children.filter(
      (c) => c.visible && (c as unknown as { material?: { dashed?: boolean } }).material?.dashed === true,
    );
    expect(dashedWhenOff).toHaveLength(0);
  });
});
