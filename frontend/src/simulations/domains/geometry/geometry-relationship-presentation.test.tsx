import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { PUBLIC_GEOMETRY_SAMPLES, type GeometrySample } from "../../../data/geometry-samples";
import { veKhongGian } from "./scene3d-chart";
import { objectsAt, stepCount, type Scene3D, type SceneObject } from "./scene3d-model";
import {
  DEFAULT_VISIBLE_RELATION_LIMIT,
  attachProblemContextToScene,
  buildPedagogicalConstructionPlan,
  buildPedagogicalStepNarration,
  buildVerifiedObjectTooltip,
  formatPlaneDisplayNotation,
  pedagogicalStepList,
  registerExactSceneOrigin,
  replaceRawSceneIdTokens,
  resolveCanonicalSectionDesignation,
  resolveCertifiedPlaneSymbolFromContext,
  resolveStudentObjectPresentation,
  resolveVerifiedObjectRelations,
  shortSym,
} from "./scene3d-semantic-policy";
import { withSubEntities } from "./scene3d-subentities";

type NineObjectCategory =
  | "Point"
  | "Segment"
  | "Line"
  | "Plane"
  | "Section"
  | "Circle"
  | "Sphere"
  | "Solid"
  | "Construction auxiliary";

const preparedSceneCache = new Map<string, { raw: Scene3D; disp: Scene3D }>();

function prepareCatalogScene(sample: GeometrySample): { raw: Scene3D; disp: Scene3D } {
  const cached = preparedSceneCache.get(sample.id);
  if (cached) return cached;
  const raw = structuredClone((sample.envelope as unknown as { scene3d: Scene3D }).scene3d);
  attachProblemContextToScene(raw, {
    title: sample.envelope.title,
    statement: sample.problemText || sample.envelope.description,
  });
  const sub = withSubEntities(raw);
  registerExactSceneOrigin(sub, raw);
  const plan = buildPedagogicalConstructionPlan(sub);
  const disp = registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
  const entry = { raw, disp };
  preparedSceneCache.set(sample.id, entry);
  return entry;
}

function makeSceneObj(
  partial: Omit<SceneObject, "origin" | "producer"> & Partial<Pick<SceneObject, "origin" | "producer">>,
): SceneObject {
  return {
    origin: "derived",
    producer: "test",
    ...partial,
  };
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
}

function rawMachineIdTokensOfScene(disp: Scene3D): string[] {
  const tokens = new Set<string>();
  for (const o of disp.objects) {
    if (!o.id || o.id.includes("::")) continue;
    // Any multi-character underscore-bearing machine id (e.g. mp_tiep_dien, doan_IA, M_AB, truc_day)
    if (/^[a-zA-Z0-9]+_[a-zA-Z0-9_]+$/u.test(o.id)) {
      tokens.add(o.id);
    }
    // Lowercase multi-word machine ids (e.g. thiet_dien already filtered above; check single lowercase words > 3 chars like chop, cau, duong if snake/lower)
    if (["chop", "lang_tru", "mp_tiep_dien", "cau_ngoai_tiep", "chieu_cao_SA", "tam_giac_ABC"].includes(o.id)) {
      tokens.add(o.id);
    }
  }
  return [...tokens];
}

function assertNoRawSceneIds(text: string | null | undefined, machineTokens: readonly string[], ctxLabel: string): void {
  if (!text) return;
  for (const tok of machineTokens) {
    const re = new RegExp(`(?<![\\p{L}0-9_])${escapeRegExp(tok)}(?![\\p{L}0-9_])`, "u");
    expect(text, `${ctxLabel} leaked raw scene ID "${tok}" in "${text}"`).not.toMatch(re);
  }
  expect(text, `${ctxLabel} contains underscore raw identifier pattern`).not.toMatch(
    /\b(?:mp|pt|doan|canh|chieu|duong|tam_giac|cau|thiet|goc|kc|truc)_[a-zA-Z0-9_]+\b/u,
  );
}

function categoryOfObject(o: SceneObject): NineObjectCategory | null {
  if (o.display_role === "non_visual" || o.display_role === "hit_proxy" || o.display_role === "measurement") {
    return null;
  }
  if (o.type === "point3") return "Point";
  if (o.type === "segment3") return "Segment";
  if (o.type === "line3") return "Line";
  if (o.type === "plane3") return "Plane";
  if (o.type === "section") return "Section";
  if (o.type === "circle3") return "Circle";
  if (o.type === "curved_solid" && o.curved_kind === "ball") return "Sphere";
  if (o.type === "solid") return "Solid";
  return null;
}

describe("Geometry Relationship Presentation & Certified Plane Context Audit", () => {
  it("1. Certified plane symbol resolution upgrades mp_tiep_dien to (P) cleanly with concise non-repeating Title, Description, Relations, and Steps", () => {
    const sample = PUBLIC_GEOMETRY_SAMPLES.find((s) => s.id === "mat-phang-tiep-xuc-mat-cau")!;
    expect(sample).toBeDefined();
    const { raw, disp } = prepareCatalogScene(sample);
    const steps = pedagogicalStepList(disp);
    const finalAnchor = steps[steps.length - 1]!.anchor;

    const mpRaw = raw.objects.find((o) => o.id === "mp_tiep_dien")!;
    const mpDisp = disp.objects.find((o) => o.id === "mp_tiep_dien")!;
    expect(mpRaw.notation).toBeNull();
    expect(resolveCertifiedPlaneSymbolFromContext(mpDisp, disp, sample.problemText)).toBe("(P)");
    expect(formatPlaneDisplayNotation(mpDisp, disp)).toBe("(P)");
    expect(shortSym(mpDisp, disp)).toBe("(P)");

    const pres = resolveStudentObjectPresentation(disp, "mp_tiep_dien", finalAnchor)!;
    expect(pres).not.toBeNull();
    expect(pres.title).toBe("Mặt phẳng (P)");
    expect(pres.description).toBe("Đi qua A và vuông góc với IA");
    expect(pres.title).not.toBe(pres.description);

    const relSummary = resolveVerifiedObjectRelations(disp, "mp_tiep_dien", finalAnchor);
    expect(relSummary.objectLabel).toBe("(P)");
    const stmts = relSummary.relations.map((r) => r.statement);
    expect(stmts).toContain("IA ⊥ (P)");
    expect(stmts).toContain("A ∈ (P)");
    expect(stmts).toContain("Mặt phẳng (P) tiếp xúc (S) tại A");
    for (const stmt of stmts) {
      expect(stmt.toLowerCase()).not.toContain("mặt phẳng qua a và vuông góc với ia");
    }

    // Radius / height segment presentation & step narration replace long uncertified plane wording with (P)
    const iaPres = resolveStudentObjectPresentation(disp, "doan_IA", finalAnchor)!;
    expect(iaPres).not.toBeNull();
    expect(`${iaPres.title} ${iaPres.description ?? ""}`.toLowerCase()).not.toContain(
      "mặt phẳng qua a và vuông góc với ia",
    );

    const narrations = steps.map((st) => buildPedagogicalStepNarration(disp, st));
    const joinedStepText = narrations
      .map((n) => `${n.actionTitle} ${n.conciseRationale} ${n.detailedEvidence.join(" ")}`)
      .join(" | ");
    expect(joinedStepText).toContain("(P)");
    expect(joinedStepText.toLowerCase()).not.toContain("mặt phẳng qua a và vuông góc với ia");
    const joinedTitles = steps.map((st) => `${st.title} ${st.subtitle ?? ""}`).join(" | ");
    expect(joinedTitles).toContain("(P)");
    expect(joinedTitles.toLowerCase()).not.toContain("mặt phẳng qua a và vuông góc với ia");

    // Token replacement API cleans raw mp_tiep_dien and uncertified prose references
    expect(replaceRawSceneIdTokens("Khoảng cách từ I tới mp_tiep_dien bằng R", disp)).toBe(
      "Khoảng cách từ I tới (P) bằng R",
    );
    expect(replaceRawSceneIdTokens("Khoảng cách tới mặt phẳng qua A và vuông góc với IA", disp)).toBe(
      "Khoảng cách tới mặt phẳng (P)",
    );
  });

  it("2. Certified plane symbol resolution generalizes across other catalog problems (hinh-non mp_P) without hardcoding and stays fail-closed when uncertified", () => {
    // Generic certified case in hinh-non-cat-song-song-day where mp_P also arrived with notation: null
    const coneSample = PUBLIC_GEOMETRY_SAMPLES.find((s) => s.id === "hinh-non-cat-song-song-day")!;
    expect(coneSample).toBeDefined();
    const { disp: coneDisp } = prepareCatalogScene(coneSample);
    const coneLast = pedagogicalStepList(coneDisp).slice(-1)[0]!.anchor;
    const mpP = coneDisp.objects.find((o) => o.id === "mp_P")!;
    expect(resolveCertifiedPlaneSymbolFromContext(mpP, coneDisp)).toBe("(P)");
    expect(formatPlaneDisplayNotation(mpP, coneDisp)).toBe("(P)");
    const mpPPres = resolveStudentObjectPresentation(coneDisp, "mp_P", coneLast)!;
    expect(mpPPres.title).toBe("Mặt phẳng (P)");

    // Fail-closed synthetic test: NO plane symbol like (P)/(Q)/(α) in problemText, events, metadata, or labels
    const uncertifiedRaw: Scene3D = {
      free_objects: [],
      events: [
        { step_index: 0, action: "CREATE", object: "I", depends: [], explanation: "Dựng tâm mặt cầu." },
        { step_index: 1, action: "CREATE", object: "K", depends: ["I"], explanation: "Lấy điểm K trên mặt cầu." },
        {
          step_index: 2,
          action: "CREATE",
          object: "mp_x",
          depends: ["K", "doan_IK"],
          explanation: "Dựng mặt phẳng tiếp diện tại K vuông góc với IK.",
        },
      ],
      objects: [
        makeSceneObj({ id: "I", type: "point3", render: "point_marker", label: "Điểm I", notation: "I", reference: "I", xyz: ["0", "0", "0"], depends: [] }),
        makeSceneObj({ id: "K", type: "point3", render: "point_marker", label: "Điểm K", notation: "K", reference: "K", xyz: ["0", "0", "5"], depends: ["I"] }),
        makeSceneObj({
          id: "cau",
          type: "curved_solid",
          render: "curved_solid",
          curved_kind: "ball",
          label: "Mặt cầu tâm I, bán kính R = 5",
          notation: "(S)",
          reference: "(S)",
          anchor: ["0", "0", "0"],
          radius_sq: "25",
          depends: ["I"],
        }),
        makeSceneObj({
          id: "doan_IK",
          type: "segment3",
          render: "segment",
          label: "Đoạn thẳng IK",
          notation: "IK",
          reference: "IK",
          endpoints: [["0", "0", "0"], ["0", "0", "5"]],
          endpoint_ids: ["I", "K"],
          depends: ["I", "K"],
          perpendicular_witness: {
            from: "I",
            foot: ["0", "0", "5"],
            foot_id: "K",
            on: "mp_x",
            marker: { u: ["1", "0", "0"], v: ["0", "1", "0"] },
          },
        }),
        makeSceneObj({
          id: "mp_x",
          type: "plane3",
          render: "surface",
          label: "Mặt phẳng qua K và vuông góc với IK",
          notation: null,
          reference: "Mặt phẳng qua K và vuông góc với IK",
          point: ["0", "0", "5"],
          normal: ["0", "0", "5"],
          depends: ["K", "doan_IK"],
          surface_role: "CUTTING_PLANE",
        }),
      ],
    };
    attachProblemContextToScene(uncertifiedRaw, {
      title: "Tiếp diện chưa đặt ký hiệu",
      statement: "Cho mặt cầu (S) tâm I bán kính 5 và điểm K thuộc mặt cầu. Xét mặt phẳng tiếp diện qua K vuông góc IK.",
    });
    const uncertDisp = prepareCatalogScene({
      id: "synthetic-uncertified-plane",
      group: "synthetic",
      problemText: "Cho mặt cầu (S) tâm I bán kính 5 và điểm K thuộc mặt cầu. Xét mặt phẳng tiếp diện qua K vuông góc IK.",
      envelope: { simId: "geometry", title: "Synthetic", description: "", scene3d: uncertifiedRaw } as never,
    }).disp;
    const mpX = uncertDisp.objects.find((o) => o.id === "mp_x")!;
    expect(resolveCertifiedPlaneSymbolFromContext(mpX, uncertDisp)).toBeNull();
    const uncertPres = resolveStudentObjectPresentation(uncertDisp, "mp_x", 2)!;
    expect(uncertPres.title).toBe("Mặt phẳng tiếp diện tại K");
    expect(uncertPres.description).toBe("Đi qua K và vuông góc với IK");
    expect(uncertPres.title).not.toBe(uncertPres.description);
  });

  it("3. Audits ALL 9 object types across ALL 11 public catalog samples: zero raw IDs, zero self-references, zero duplicates, and zero future-step leaks", { timeout: 15000 }, () => {
    expect(PUBLIC_GEOMETRY_SAMPLES).toHaveLength(11);

    const coveredCategories = new Set<NineObjectCategory>();
    const selfRelRe = /^(.+?)\s+(?:⊥|∥|tiếp xúc|∈|⊂|=)\s+\1$/iu;
    const selfInterRe = /^(.+?)\s+là giao của\s+\1\b/iu;

    for (const sample of PUBLIC_GEOMETRY_SAMPLES) {
      const { disp } = prepareCatalogScene(sample);
      const machineTokens = rawMachineIdTokensOfScene(disp);
      const steps = pedagogicalStepList(disp);
      expect(steps.length, `${sample.id} must have >= 1 step`).toBeGreaterThanOrEqual(1);
      const lastAnchor = steps[steps.length - 1]!.anchor;

      // Track first step index (0..steps.length-1) in which each object ID becomes present
      const firstVisibleStepById = new Map<string, number>();
      for (let k = 0; k < steps.length; k += 1) {
        const present = objectsAt(disp, steps[k]!.anchor);
        for (const po of present) {
          if (!firstVisibleStepById.has(po.id)) {
            firstVisibleStepById.set(po.id, k);
          }
        }
        // Step narration audit for step k
        const narr = buildPedagogicalStepNarration(disp, steps[k]!);
        assertNoRawSceneIds(steps[k]!.title, machineTokens, `${sample.id}:step${k}:step.title`);
        assertNoRawSceneIds(steps[k]!.subtitle, machineTokens, `${sample.id}:step${k}:step.subtitle`);
        assertNoRawSceneIds(narr.actionTitle, machineTokens, `${sample.id}:step${k}:actionTitle`);
        assertNoRawSceneIds(narr.conciseRationale, machineTokens, `${sample.id}:step${k}:conciseRationale`);
        for (const evLine of narr.detailedEvidence) {
          assertNoRawSceneIds(evLine, machineTokens, `${sample.id}:step${k}:detailedEvidence`);
        }
      }

      for (const obj of disp.objects) {
        const baseCat = categoryOfObject(obj);
        if (baseCat) coveredCategories.add(baseCat);
        if (obj.formation_roles?.includes("CONSTRUCT_AUXILIARY_GEOMETRY") && baseCat !== null) {
          coveredCategories.add("Construction auxiliary");
        }
        if (obj.display_role === "non_visual" || obj.display_role === "hit_proxy") continue;

        const pres = resolveStudentObjectPresentation(disp, obj.id, lastAnchor);
        if (pres) {
          assertNoRawSceneIds(pres.title, machineTokens, `${sample.id}:${obj.id}:pres.title`);
          assertNoRawSceneIds(pres.description, machineTokens, `${sample.id}:${obj.id}:pres.description`);
        }

        const tip = buildVerifiedObjectTooltip(disp, obj.id, lastAnchor);
        if (tip) {
          assertNoRawSceneIds(tip.header, machineTokens, `${sample.id}:${obj.id}:tip.header`);
          assertNoRawSceneIds(tip.body, machineTokens, `${sample.id}:${obj.id}:tip.body`);
        }

        const finalRel = resolveVerifiedObjectRelations(disp, obj.id, lastAnchor);
        assertNoRawSceneIds(finalRel.objectLabel, machineTokens, `${sample.id}:${obj.id}:rel.label`);

        const seenStmtSet = new Set<string>();
        const seenKindStmtSet = new Set<string>();
        for (const r of finalRel.relations) {
          assertNoRawSceneIds(r.statement, machineTokens, `${sample.id}:${obj.id}:rel.stmt`);
          expect(r.statement, `${sample.id}:${obj.id} self-ref`).not.toMatch(selfRelRe);
          expect(r.statement, `${sample.id}:${obj.id} self-inter`).not.toMatch(selfInterRe);
          const normStmt = r.statement.trim().toLowerCase();
          const kindStmtKey = `${r.kind}::${normStmt}`;
          expect(seenKindStmtSet.has(kindStmtKey), `${sample.id}:${obj.id} duplicate kind+statement: ${r.statement}`).toBe(
            false,
          );
          expect(seenStmtSet.has(normStmt), `${sample.id}:${obj.id} duplicate statement: ${r.statement}`).toBe(false);
          seenStmtSet.add(normStmt);
          seenKindStmtSet.add(kindStmtKey);
        }

        // Strict zero-future-step-leak check at every step k
        const objFirstStep = firstVisibleStepById.get(obj.id);
        if (objFirstStep !== undefined) {
          for (let k = objFirstStep; k < steps.length; k += 1) {
            const visibleAtK = new Set(objectsAt(disp, steps[k]!.anchor).map((o) => o.id));
            const relAtK = resolveVerifiedObjectRelations(disp, obj.id, steps[k]!.anchor);
            for (const r of relAtK.relations) {
              for (const tid of r.targetIds) {
                const targetObj = disp.objects.find((o) => o.id === tid);
                if (!targetObj || targetObj.display_role === "non_visual" || targetObj.display_role === "measurement") {
                  continue;
                }
                const targetFirstStep = firstVisibleStepById.get(tid);
                if (targetFirstStep !== undefined) {
                  expect(
                    targetFirstStep,
                    `${sample.id}:${obj.id} at step ${k} leaked future object ${tid} (introduced at step ${targetFirstStep}) in "${r.statement}"`,
                  ).toBeLessThanOrEqual(k);
                }
                expect(
                  visibleAtK.has(tid) || tid.includes("::"),
                  `${sample.id}:${obj.id} at step ${k} referenced invisible target ${tid} in "${r.statement}"`,
                ).toBe(true);
              }
            }
          }
        }
      }
    }

    // All 9 required object categories must actually be covered across the 11 catalog samples
    for (const reqCat of [
      "Point",
      "Segment",
      "Line",
      "Plane",
      "Section",
      "Circle",
      "Sphere",
      "Solid",
      "Construction auxiliary",
    ] satisfies NineObjectCategory[]) {
      expect(coveredCategories.has(reqCat), `Missing coverage of object type: ${reqCat}`).toBe(true);
    }
  });

  it("4. Verifies 4-tier deterministic relation priority, DEFAULT_VISIBLE_RELATION_LIMIT === 4, and inline truncation toggle", () => {
    expect(DEFAULT_VISIBLE_RELATION_LIMIT).toBe(4);

    // Deterministic 4-tier ranking across object kinds (definition/intersection <= containment <= parallel/perp/tangency <= metric)
    const sample = PUBLIC_GEOMETRY_SAMPLES.find((s) => s.id === "chop-thiet-dien-ba-diem")!;
    const { raw, disp } = prepareCatalogScene(sample);
    const steps = pedagogicalStepList(disp);
    const lastAnchor = steps[steps.length - 1]!.anchor;

    const isCoreKind = (kind: string): boolean =>
      kind === "tangency"
      || kind === "perpendicular"
      || kind === "parallel"
      || kind === "intersection_point"
      || kind === "intersection_line"
      || kind === "intersection";

    const classifyTierForStep = (
      subjectType: string,
      subjectId: string,
      stepTargetIds: ReadonlySet<string>,
      stepDepends: ReadonlySet<string>,
      rel: { kind: string; statement: string; targetIds: string[] },
    ): number => {
      const isSecSummary =
        rel.kind === "section_membership"
        && !rel.statement.startsWith("Đỉnh ")
        && (subjectType === "section" || subjectType === "polygon3" || subjectType === "point3");
      const isCurrentStepDirect =
        rel.kind !== "dependency"
        && (
          rel.targetIds.some((id) => stepTargetIds.has(id))
          || (
            stepTargetIds.has(subjectId)
            && (isCoreKind(rel.kind) || isSecSummary || rel.targetIds.some((id) => stepDepends.has(id)))
          )
        );
      if (isCurrentStepDirect) return 1;
      if (isCoreKind(rel.kind) || isSecSummary) return 2;
      if (rel.kind !== "dependency") return 3;
      return 4;
    };

    for (const catSample of PUBLIC_GEOMETRY_SAMPLES) {
      const { disp: catDisp } = prepareCatalogScene(catSample);
      const catSteps = pedagogicalStepList(catDisp);
      const totalSteps = Math.max(1, stepCount(catDisp));
      const catLast = Math.max(0, Math.min(catSteps[catSteps.length - 1]!.anchor, totalSteps - 1));
      const stepFocusIds = new Set<string>();
      const snapFocus = catDisp.formation?.steps[catLast]?.focus_ids ?? [];
      for (const fid of snapFocus) stepFocusIds.add(fid);
      if (catLast > 0) {
        const prevIds = new Set(objectsAt(catDisp, catLast - 1).map((o) => o.id));
        for (const o of objectsAt(catDisp, catLast)) {
          if (!prevIds.has(o.id)) stepFocusIds.add(o.id);
        }
      }
      const stepEv = catDisp.events.find((e) => e.step_index === catLast);
      if (stepEv) {
        if (stepEv.object) stepFocusIds.add(stepEv.object);
        for (const oid of stepEv.objects ?? []) stepFocusIds.add(oid);
      }
      const stepEventDepends = new Set<string>(stepEv?.depends ?? []);
      for (const obj of catDisp.objects) {
        const res = resolveVerifiedObjectRelations(catDisp, obj.id, catLast);
        for (let i = 1; i < res.relations.length; i += 1) {
          const prevTier = classifyTierForStep(obj.type, obj.id, stepFocusIds, stepEventDepends, res.relations[i - 1]!);
          const curTier = classifyTierForStep(obj.type, obj.id, stepFocusIds, stepEventDepends, res.relations[i]!);
          expect(
            curTier,
            `${catSample.id}:${obj.id} tier order violated between "${res.relations[i - 1]!.kind}:${res.relations[i - 1]!.statement}" (T${prevTier}) and "${res.relations[i]!.kind}:${res.relations[i]!.statement}" (T${curTier})`,
          ).toBeGreaterThanOrEqual(prevTier);
        }
        // Deterministic ordering across repeated invocations
        expect(resolveVerifiedObjectRelations(catDisp, obj.id, catLast).relations).toEqual(res.relations);
      }
    }

    // Inline card in AxoWorkspaceV62 exposes [Xem quan hệ] action and enforces 4-item initial truncation
    const sec = disp.objects.find((o) => o.type === "section")!;
    const secRel = resolveVerifiedObjectRelations(disp, sec.id, lastAnchor);
    expect(secRel.relations.length).toBeGreaterThan(DEFAULT_VISIBLE_RELATION_LIMIT);
    expect(secRel.relations.slice(0, DEFAULT_VISIBLE_RELATION_LIMIT)).toHaveLength(4);
    const html = renderToString(
      <AxoWorkspaceV62
        scene={raw}
        de={sample.problemText || sample.envelope.description}
        tieuDe={sample.envelope.title ?? sample.id}
        initialSelectedId={sec.id}
      />,
    );
    expect(html).toContain("Thiết diện MENPF");
    expect(html).toContain('data-context-action="relations"');
    const wsSrc = readFileSync(
      fileURLToPath(new URL("../../../components/SimulationWorkspace.tsx", import.meta.url)),
      "utf8",
    );
    expect(wsSrc).toContain("const INITIAL_VISIBLE_RELATIONS = 4;");
    expect(wsSrc).toContain('id="btn-context-toggle-more-relations"');
    expect(wsSrc).toContain("`Xem thêm ${hiddenCount} quan hệ`");
  });

  it("5. Preserves key mathematical invariants across F = SD ∩ (MNP), MENPF / MNEPFQ cyclic order, Oxyz, and Sphere tangent / secant circle", () => {
    const pyrSample = PUBLIC_GEOMETRY_SAMPLES.find((s) => s.id === "chop-thiet-dien-ba-diem")!;
    const { disp: pyrDisp } = prepareCatalogScene(pyrSample);
    const pyrLast = pedagogicalStepList(pyrDisp).slice(-1)[0]!.anchor;
    const pyrSec = pyrDisp.objects.find((o) => o.type === "section")!;
    expect(resolveCanonicalSectionDesignation(pyrDisp, pyrSec)?.compactLabel).toBe("MENPF");
    const pyrFRel = resolveVerifiedObjectRelations(pyrDisp, "F", pyrLast);
    expect(pyrFRel.relations.some((r) => r.kind === "intersection_point" && r.statement === "F = SD ∩ (MNP)")).toBe(true);

    const cubeSample = PUBLIC_GEOMETRY_SAMPLES.find((s) => s.id === "lap-phuong-thiet-dien-bat-ky")!;
    const { disp: cubeDisp } = prepareCatalogScene(cubeSample);
    const cubeSec = cubeDisp.objects.find((o) => o.type === "section")!;
    expect(resolveCanonicalSectionDesignation(cubeDisp, cubeSec)?.compactLabel).toBe("MNEPFQ");

    const oxyzSample = PUBLIC_GEOMETRY_SAMPLES.find((s) => s.id === "oxyz-giao-diem-duong-mat")!;
    const { disp: oxyzDisp } = prepareCatalogScene(oxyzSample);
    const oxyzLast = pedagogicalStepList(oxyzDisp).slice(-1)[0]!.anchor;
    const oxyzMRel = resolveVerifiedObjectRelations(oxyzDisp, "M", oxyzLast);
    expect(oxyzMRel.relations.some((r) => r.kind === "intersection_point" && r.statement.includes("M = DE ∩ (P)"))).toBe(true);

    const secSphereSample = PUBLIC_GEOMETRY_SAMPLES.find((s) => s.id === "mat-cau-cat-mat-phang")!;
    const { disp: secDisp } = prepareCatalogScene(secSphereSample);
    const secLast = pedagogicalStepList(secDisp).slice(-1)[0]!.anchor;
    const cauRel = resolveVerifiedObjectRelations(secDisp, "cau", secLast);
    expect(cauRel.relations.some((r) => r.statement === "Đường tròn (H; HM) là giao của (S) và (P)")).toBe(true);
  });
});
