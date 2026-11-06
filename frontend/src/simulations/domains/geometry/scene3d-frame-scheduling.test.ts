import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

// Exercise the actual closure bodies: controls.update dispatches change while vong is running.
const source = readFileSync(new URL("./scene3d-view.tsx", import.meta.url), "utf8");
const loop = source.slice(source.indexOf("    const vong = () => {"), source.indexOf("    veRef.current = () => {"));

describe("camera frame scheduling", () => {
  it("does not latch controlsInteracting after OrbitControls has ended a wheel gesture", () => {
    const handlers = source.slice(source.indexOf("    const danhDauNguoiDungChinhCam = () => {"), source.indexOf("    const xuLyMatNguCanhWebgl ="));
    const rawWheelHandler = source.match(/renderer\.domElement\.addEventListener\("wheel", (\w+),/)?.[1];
    expect(rawWheelHandler).toBeDefined();
    const run = new Function(`
      let controlsInteracting = false, lastInteractionWakeMs = 0, userAdjustedCamera = false;
      const dangDatKhungTuDong = false, baoCaoCameraPose = () => {}, wakeRenderLoop = () => {};
      ${handlers}
      danhDauNguoiDungChinhCam(); xuLyKetThucDieuKhien();
      ${rawWheelHandler}();
      return controlsInteracting;
    `);
    expect(run()).toBe(false);
  });

  it("keeps one pending frame when damping emits a change during the current render", () => {
    const run = new Function(`
      let rafId = 0, song = true, userAdjustedCamera = true;
      let wakeRenderLoop = () => {};
      let renders = 0, reports = 0, nextId = 0;
      const pending = new Map();
      const requestAnimationFrame = fn => { pending.set(++nextId, fn); return nextId; };
      const renderSingleFrame = () => { renders++; wakeRenderLoop(); return true; };
      const isAnimationActive = () => true;
      const baoCaoCameraPose = () => { reports++; };
      ${loop}
      wakeRenderLoop();
      const sizes = [];
      for (let i = 0; i < 12; i++) {
        const callbacks = [...pending.values()]; pending.clear();
        for (const fn of callbacks) fn();
        sizes.push(pending.size);
      }
      return { sizes, renders, reports };
    `);
    expect(run()).toEqual({ sizes: Array(12).fill(1), renders: 12, reports: 0 });
  });
});
