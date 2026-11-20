import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { veKhongGian } from "./scene3d-chart";
import { objectsAt, stepCount, type Scene3D } from "./scene3d-model";
import {
  buildPedagogicalConstructionPlan,
  buildVerifiedObjectTooltip,
  registerExactSceneOrigin,
  resolveCanonicalSectionDesignation,
  resolveStepVisualRoles,
  shortSym,
} from "./scene3d-semantic-policy";
import { withSubEntities } from "./scene3d-subentities";
import { createCanvasPointerTapTracker } from "./scene3d-view";

function extractCatalogSample(id: string) {
  const found = GEOMETRY_SAMPLES.find((s) => s.id === id);
  if (!found) throw new Error(`Missing catalog sample: ${id}`);
  return found;
}

function sampleRawScene(sample: ReturnType<typeof extractCatalogSample>): Scene3D {
  return (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;
}

function prepareScene(raw: Scene3D) {
  const sub = withSubEntities(raw);
  registerExactSceneOrigin(sub, raw);
  const plan = buildPedagogicalConstructionPlan(sub);
  const disp = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
  return { raw, plan, disp };
}

describe("Object Selection, Pointer Tap Tracking & Verified Hover Tooltip", () => {
  it("omits Isolate/Hide controls and restore banner while rendering V9.4.17 Xem quan hệ and Định vị actions", () => {
    const sample = extractCatalogSample("chop-thiet-dien-ba-diem");
    const raw = sampleRawScene(sample);
    const { disp } = prepareScene(raw);
    const pointS = disp.objects.find((o) => o.type === "point3" && (o.id === "S" || shortSym(o) === "S"));
    const planeMnp = disp.objects.find((o) => o.type === "plane3" && (o.label?.includes("MNP") || o.id.includes("MNP")));
    const segSa = disp.objects.find((o) => o.id === "chieu_cao_SA")
      ?? disp.objects.find((o) => o.type === "segment3" && (o.label === "SA" || o.id.includes("SA")));
    expect(pointS).toBeDefined();
    expect(planeMnp).toBeDefined();
    expect(segSa).toBeDefined();

    for (const selId of [segSa!.id, pointS!.id, planeMnp!.id]) {
      const html = renderToString(
        <AxoWorkspaceV62
          scene={raw}
          de={sample.envelope.description}
          tieuDe={sample.envelope.title}
          initialSelectedId={selId}
        />,
      );
      expect(html).toContain('class="context-object-card"');
      expect(html).toContain('id="btn-clear-pick"');
      expect(html).not.toContain('id="btn-card-isolate"');
      expect(html).not.toContain('id="btn-card-hide"');
      expect(html).not.toContain('id="dock-visibility-restore-bar"');
      expect(html).not.toContain('id="btn-restore-hidden-objects"');
      expect(html).not.toContain("Chỉ xem phần này");
      expect(html).not.toContain("Ẩn đối tượng");
      expect(html).not.toContain("Hiện lại toàn hình");
      expect(html).not.toContain("Hiện lại tất cả");
      expect(html).not.toContain("Tập trung");
      expect(html).toContain("Xem quan hệ");
      expect(html).toContain("Định vị");
    }
  });

  it("selecting SA in chop-thiet-dien-ba-diem keeps full surrounding pyramid structure visible", () => {
    const sample = extractCatalogSample("chop-thiet-dien-ba-diem");
    const raw = sampleRawScene(sample);
    const { disp } = prepareScene(raw);
    const lastStep = Math.max(0, stepCount(disp) - 1);
    const vis = objectsAt(disp, lastStep);
    const segSa = vis.find((o) => o.id === "chieu_cao_SA")
      ?? vis.find((o) => o.type === "segment3" && o.label === "SA");
    expect(segSa).toBeDefined();

    const roles = resolveStepVisualRoles(disp, lastStep, {
      selectedId: segSa!.id,
      auxiliaryShown: false,
    });
    const visiblePointSyms = vis
      .filter((o) => o.type === "point3" && (roles.get(o.id)?.visible ?? true))
      .map((o) => shortSym(o) || o.id);
    for (const reqLabel of ["S", "A", "B", "C", "D"]) {
      expect(visiblePointSyms).toContain(reqLabel);
    }
    const solidObj = vis.find((o) => o.type === "solid");
    expect(solidObj).toBeDefined();
    expect(roles.get(solidObj!.id)?.visible).toBe(true);
    expect(roles.get(segSa!.id)?.visible).toBe(true);
    expect(roles.get(segSa!.id)?.opacityScale ?? 1).toBeGreaterThanOrEqual(1);
  });

  it("pointer tap tracker rejects orbit drags, return-to-origin drags, multi-touch pinch, right-clicks, and pointercancel", () => {
    const tracker = createCanvasPointerTapTracker(4);

    // 1. Clean single-finger / left-click tap selects
    expect(tracker.handleDown({ pointerId: 1, pointerType: "mouse", button: 0, clientX: 100, clientY: 100 }).activeCount).toBe(1);
    expect(tracker.handleMove({ pointerId: 1, pointerType: "mouse", buttons: 1, clientX: 102, clientY: 101 })).toEqual({
      exceededDrag: false,
      isHoverEligible: false,
    });
    expect(tracker.handleUp({ pointerId: 1, pointerType: "mouse", button: 0, clientX: 102, clientY: 101 }).shouldSelect).toBe(true);

    // 2. Orbit drag exceeding 4px then returning within 4px still does NOT select
    tracker.handleDown({ pointerId: 2, pointerType: "mouse", button: 0, clientX: 100, clientY: 100 });
    expect(tracker.handleMove({ pointerId: 2, pointerType: "mouse", buttons: 1, clientX: 118, clientY: 100 }).exceededDrag).toBe(true);
    tracker.handleMove({ pointerId: 2, pointerType: "mouse", buttons: 1, clientX: 101, clientY: 100 });
    const dragUp = tracker.handleUp({ pointerId: 2, pointerType: "mouse", button: 0, clientX: 101, clientY: 100 });
    expect(dragUp.shouldSelect).toBe(false);
    expect(dragUp.dragged).toBe(true);

    // 3. Recovery click after drag works cleanly
    tracker.handleDown({ pointerId: 3, pointerType: "mouse", button: 0, clientX: 200, clientY: 200 });
    expect(tracker.handleUp({ pointerId: 3, pointerType: "mouse", button: 0, clientX: 200, clientY: 200 }).shouldSelect).toBe(true);

    // 4. Right-click does not trigger selection or hover lock
    tracker.handleDown({ pointerId: 4, pointerType: "mouse", button: 2, clientX: 120, clientY: 120 });
    expect(tracker.handleMove({ pointerId: 4, pointerType: "mouse", buttons: 0, clientX: 120, clientY: 120 }).isHoverEligible).toBe(true);
    expect(tracker.handleUp({ pointerId: 4, pointerType: "mouse", button: 2, clientX: 120, clientY: 120 }).shouldSelect).toBe(false);

    // 5. Two-finger pinch blocks selection on both staggered lifts, then allows next single tap
    tracker.handleDown({ pointerId: 10, pointerType: "touch", clientX: 50, clientY: 50 });
    expect(tracker.handleDown({ pointerId: 11, pointerType: "touch", clientX: 140, clientY: 140 }).startedMultiTouch).toBe(true);
    const firstLift = tracker.handleUp({ pointerId: 10, pointerType: "touch", clientX: 52, clientY: 50 });
    expect(firstLift.shouldSelect).toBe(false);
    expect(firstLift.multiTouch).toBe(true);
    const secondLift = tracker.handleUp({ pointerId: 11, pointerType: "touch", clientX: 140, clientY: 140 });
    expect(secondLift.shouldSelect).toBe(false);
    expect(secondLift.activeCount).toBe(0);

    // Subsequent single touch tap works cleanly
    tracker.handleDown({ pointerId: 12, pointerType: "touch", clientX: 80, clientY: 80 });
    expect(tracker.handleUp({ pointerId: 12, pointerType: "touch", clientX: 81, clientY: 80 }).shouldSelect).toBe(true);

    // 6. pointercancel + pointerleave reset state cleanly
    tracker.handleDown({ pointerId: 13, pointerType: "touch", clientX: 80, clientY: 80 });
    expect(tracker.handleCancel({ pointerId: 13, pointerType: "touch", clientX: 80, clientY: 80 }).activeCount).toBe(0);
    tracker.handleLeave();
    expect(tracker.handleMove({ pointerId: 1, pointerType: "mouse", buttons: 0, clientX: 90, clientY: 90 }).isHoverEligible).toBe(true);
  });

  it("verified hover tooltip and section designation use canonical MENPF and MNEPFQ instead of rotated cycles", () => {
    for (const [sampleId, expectedName, forbiddenName] of [
      ["chop-thiet-dien-ba-diem", "MENPF", "NPFME"],
      ["lap-phuong-thiet-dien-bat-ky", "MNEPFQ", "EPFQMN"],
    ] as const) {
      const { disp } = prepareScene(sampleRawScene(extractCatalogSample(sampleId)));
      const lastStep = Math.max(0, stepCount(disp) - 1);
      const sec = disp.objects.find((o) => o.type === "section");
      expect(sec, sampleId).toBeDefined();
      const canon = resolveCanonicalSectionDesignation(disp, sec!);
      expect(canon?.compactLabel).toBe(expectedName);
      const tooltip = buildVerifiedObjectTooltip(disp, sec!.id, lastStep);
      expect(tooltip).not.toBeNull();
      expect(tooltip!.header).toContain(expectedName);
      expect(tooltip!.header).not.toContain(forbiddenName);
      expect(tooltip!.body).not.toContain(forbiddenName);
    }
  });
});
