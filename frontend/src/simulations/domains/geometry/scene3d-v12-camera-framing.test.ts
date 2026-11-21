import { describe, expect, it } from "vitest";
import * as THREE from "three";

import { khungNhinQuanhTam, tinhTamXoayTuKhoi } from "./scene3d-camera";
import { tinhViTriNhanDiem, tinhVungAnToanKhungNhin } from "./scene3d-view";

describe("scene3d V11-VIS-1 initial camera framing and label clamping", () => {
  const viewports: Array<[number, number, number, number]> = [
    [1920, 1080, 0.25, -0.15],
    [1366, 768, 0.28, -0.22],
    [768, 1024, 0.30, 0.0],
    [390, 844, 0.32, 0.0],
  ];

  it("compensates camera safe NDC bounds for setViewOffset lens shift across desktop, tablet, and mobile", () => {
    // S07-like unit pyramid O.ABC + elongated height S09-like pyramid
    const solids = [
      [
        [0, 0, 0],
        [2, 0, 0],
        [0, 2, 0],
        [0, 0, 2],
      ] as [number, number, number][],
      [
        [0, 0, 0],
        [3, 0, 0],
        [0, 4, 0],
        [0, 0, 6],
      ] as [number, number, number][],
    ];

    for (const pts of solids) {
      const info = tinhTamXoayTuKhoi(
        [{ loai: "solid", vertices: pts, faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]] }],
        pts,
      );
      expect(info).not.toBeNull();
      const huong: [number, number, number] = [8, -5, 6];

      for (const [w, h, dichTamDoc, dichTamNgang] of viewports) {
        const tc = {
          tiLeDoc: 0.65,
          tiLeNgang: 0.72,
          dichTamDoc,
          dichTamNgang,
        };
        const safe = tinhVungAnToanKhungNhin(tc, w, h);
        const kn = khungNhinQuanhTam(pts, info!.tamXoay, 38, w / h, huong, safe);
        expect(kn).not.toBeNull();

        const cam = new THREE.PerspectiveCamera(38, w / h, 0.1, 200);
        cam.position.set(...kn!.viTri);
        cam.up.set(0, 0, 1);
        cam.lookAt(...kn!.nhinVao);
        cam.setViewOffset(w, h, -dichTamNgang * (w * 0.5), dichTamDoc * (h * 0.5), w, h);
        cam.updateProjectionMatrix();
        cam.updateMatrixWorld(true);

        for (const v of pts) {
          const ndc = new THREE.Vector3(...v).project(cam);
          const sx = ((ndc.x + 1) / 2) * w;
          const sy = ((1 - ndc.y) / 2) * h;
          expect(sx).toBeGreaterThanOrEqual(16);
          expect(sx).toBeLessThanOrEqual(w - 16);
          expect(sy).toBeGreaterThanOrEqual(16);
          expect(sy).toBeLessThanOrEqual(h - 16);
        }
      }
    }
  });

  it("clamps and reorients vertex labels near top/right/bottom/left viewport borders", () => {
    const res = tinhViTriNhanDiem(
      [
        { id: "S", x: 195, y: 8, w: 20, h: 20 },
        { id: "A", x: 6, y: 400, w: 20, h: 20 },
        { id: "B", x: 382, y: 836, w: 20, h: 20 },
      ],
      [],
      [],
      new Map(),
      { w: 390, h: 844, pad: 8 },
    );
    for (const [, pos] of res) {
      expect(pos.x).toBeGreaterThanOrEqual(8);
      expect(pos.x + 20).toBeLessThanOrEqual(390 - 8);
      expect(pos.y).toBeGreaterThanOrEqual(8);
      expect(pos.y + 20).toBeLessThanOrEqual(844 - 8);
    }
  });
});
