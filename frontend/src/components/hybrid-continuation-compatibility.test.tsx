import { describe, expect, it } from "vitest";
import {
  docPhanHoiHybrid,
  hybridViewCua,
  kiemHybridView,
  HYBRID_SIMULATION_ADAPTER,
  HYBRID_SIMULATION_SCHEMA,
} from "../simulations/domains/geometry/hybrid-preview-adapter";
import {
  attachHybridViewToScene,
  hybridViewOfScene,
  registerExactSceneOrigin,
  type Scene3D,
} from "../simulations/domains/geometry/scene3d-model";
import { veKhongGian } from "../simulations/domains/geometry/scene3d-chart";
import {
  classifyPolygonShapeWithProvenance,
  classifyScenePolygonShape,
} from "../simulations/domains/geometry/scene3d-semantic-policy";

function buildMinimalServedHybrid4Payload(opts?: {
  answers?: Record<string, string>;
  answerExact?: Record<string, { coef: string; dim: number; unit: string | null }>;
  sourceProvenance?: unknown[];
  relationCertificates?: unknown[];
  baseLabel?: string;
  baseVertices?: [string, string, string][];
}) {
  const baseVertices: [string, string, string][] = opts?.baseVertices ?? [
    ["0", "0", "0"],
    ["2", "0", "0"],
    ["2", "2", "0"],
    ["0", "2", "0"],
  ];
  const scene3d: Scene3D = {
    free_objects: ["A", "B", "C", "D", "S"],
    length_unit: { symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false },
    chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
    objects: [
      { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: null, render: "point_marker", depends: [], xyz: baseVertices[0] },
      { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: null, render: "point_marker", depends: [], xyz: baseVertices[1] },
      { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: null, render: "point_marker", depends: [], xyz: baseVertices[2] },
      { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: null, render: "point_marker", depends: [], xyz: baseVertices[3] },
      { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
      {
        id: "day_ABCD",
        type: "polygon3",
        label: opts?.baseLabel ?? "Đáy ABCD",
        notation: "ABCD",
        origin: "derived",
        producer: "construct_polygon",
        render: "polygon",
        surface_role: "BASE_REGION",
        depends: ["A", "B", "C", "D"],
        vertex_ids: ["A", "B", "C", "D"],
        vertices: baseVertices,
      },
      {
        id: "khoi_S_ABCD",
        type: "solid",
        label: "Hình chóp S.ABCD",
        notation: "S.ABCD",
        origin: "derived",
        producer: "construct_solid",
        render: "mesh",
        depends: ["S", "A", "B", "C", "D"],
        vertex_ids: ["S", "A", "B", "C", "D"],
        vertices: [["0", "0", "4"], ...baseVertices],
        faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
      },
      ...(opts?.answers && Object.keys(opts.answers).length > 0
        ? [
            {
              id: "kq_g1",
              type: "quantity",
              label: "Thể tích",
              notation: "V",
              origin: "derived" as const,
              producer: "measure.volume",
              render: "readout" as const,
              depends: ["khoi_S_ABCD"],
              value: "16/3",
            },
          ]
        : []),
    ],
    events: [
      { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Init" },
      { step_index: 1, action: "CREATE", object: "day_ABCD", depends: ["A", "B", "C", "D"], explanation: "Base" },
      { step_index: 2, action: "CREATE", object: "khoi_S_ABCD", depends: ["S", "A", "B", "C", "D"], explanation: "Solid" },
      ...(opts?.answers && Object.keys(opts.answers).length > 0
        ? [{ step_index: 3, action: "MEASURE" as const, object: "kq_g1", depends: ["khoi_S_ABCD"], semantic_kind: "FINAL_RESULT" as const, explanation: "V" }]
        : []),
    ],
  };

  return {
    schema_version: HYBRID_SIMULATION_SCHEMA,
    envelope: {
      status: "ok",
      simulation_id: "generic.semantic_program",
      domain: "geometry",
      visual_mode: "2d",
      title: "Hình chóp S.ABCD",
      description: "Cho hình chóp S.ABCD.",
      config: { spec_version: "1.0", title: "Hình chóp S.ABCD", frames: [], view_steps: [] },
      notes: null,
      scene3d,
    },
    route_d: {
      schema_version: HYBRID_SIMULATION_SCHEMA,
      adapter_version: HYBRID_SIMULATION_ADAPTER,
      contract_version: "typed-fact-next/2",
      status: "SERVED",
      refusal: null,
      source_verification: { authority: "registry.kiem_nguon", verified: true },
      length_unit: "a",
      sections: [],
      answers: opts?.answers ?? {},
      answer_exact: opts?.answerExact ?? {},
      planner: { trace: [], goal_checks: {}, negated_checks: {} },
      ...(opts?.sourceProvenance !== undefined ? { source_provenance: opts.sourceProvenance } : {}),
      ...(opts?.relationCertificates !== undefined ? { relation_certificates: opts.relationCertificates } : {}),
    },
  };
}

describe("AXO Master Continuation — Priority F: Hybrid /4 Contract Compatibility", () => {
  it("F1. Accepts SL-1 geometric construction payloads (answers: {}) without mutating envelope.scene3d", () => {
    const raw = buildMinimalServedHybrid4Payload({ answers: {}, answerExact: {} });
    const snapshotBefore = structuredClone(raw.envelope.scene3d);
    const res = docPhanHoiHybrid(raw);
    expect(res.ok).toBe(true);
    if (!res.ok) return;
    expect(res.envelope.scene3d).toEqual(snapshotBefore);
    const view = hybridViewCua(res.envelope);
    expect(view?.adapter_version).toBe(HYBRID_SIMULATION_ADAPTER);
    expect(view?.answers).toEqual([]);
    expect(kiemHybridView(view, res.envelope.scene3d as Scene3D)).toBeNull();
  });

  // F2 (Axo-only `hybrid_clarification` shape: version/clause_id/message_vi/{start,end}) đã gỡ khi tích hợp Hybrid /4:
  // backend `route-d-clarification/1` thật (typed_fact_next.py) dùng schema_version/unresolved_id/kind/nlu_class/[a,b];
  // hợp đồng thật được khoá ở hybrid-product-integration.test.tsx.

  it("F3. Validates source_provenance & relation_certificates and honors them via attachHybridViewToScene without mutating scene3d", () => {
    const rawSquare = buildMinimalServedHybrid4Payload({
      baseLabel: "Đáy ABCD", // Generic label! Certified ONLY via Hybrid /4 source_provenance
      sourceProvenance: [
        { fact_id: "f1", kind: "regular_polygon", polygon: ["A", "B", "C", "D"], verified: true },
      ],
      relationCertificates: [
        { relation_id: "r1", kind: "perpendicular_line_plane", verified: true },
      ],
    });
    const resSq = docPhanHoiHybrid(rawSquare);
    expect(resSq.ok).toBe(true);
    if (!resSq.ok) return;
    expect(resSq.envelope.scene3d).toEqual(rawSquare.envelope.scene3d);

    const viewSq = hybridViewCua(resSq.envelope)!;
    expect(viewSq.source_provenance?.length).toBe(1);
    expect(kiemHybridView(viewSq, resSq.envelope.scene3d as Scene3D)).toBeNull();

    const rawScene = resSq.envelope.scene3d as Scene3D;
    // Before attaching Hybrid view: generic "Đáy ABCD" is NOT assumed square
    expect(classifyPolygonShapeWithProvenance(rawScene, rawScene.objects[5]).certifiedShape).toBeNull();

    // After attaching Hybrid view (and propagating through veKhongGian): certified as "hình vuông" [GIVEN]!
    attachHybridViewToScene(rawScene, viewSq);
    const dispScene = registerExactSceneOrigin(veKhongGian(rawScene), rawScene);
    expect(hybridViewOfScene(dispScene)).toBe(viewSq);
    const certSq = classifyPolygonShapeWithProvenance(dispScene, dispScene.objects[5]);
    expect(certSq.provenance).toBe("GIVEN");
    expect(certSq.certifiedShape).toBe("hình vuông");

    // Rectangle source_provenance on equal-side coordinates -> stays "hình chữ nhật", NEVER upgraded to "hình vuông"
    const rawRect = buildMinimalServedHybrid4Payload({
      baseLabel: "Đáy ABCD",
      sourceProvenance: [
        { fact_id: "f_rect", kind: "rectangle", polygon: ["A", "B", "C", "D"], verified: true },
      ],
    });
    const resRect = docPhanHoiHybrid(rawRect);
    expect(resRect.ok).toBe(true);
    if (resRect.ok) {
      const scRect = resRect.envelope.scene3d as Scene3D;
      attachHybridViewToScene(scRect, hybridViewCua(resRect.envelope));
      const certRect = classifyPolygonShapeWithProvenance(scRect, scRect.objects[5]);
      expect(certRect.provenance).toBe("GIVEN");
      expect(certRect.certifiedShape).toBe("hình chữ nhật");
    }

    // Real Adapter /4 call-based source_provenance (`{ id, fn, args, quotes }`) + 4-layer `geometric-relation-certificate/1`
    const realAdapter4Payload = buildMinimalServedHybrid4Payload({
      baseLabel: "Đáy ABCD",
      sourceProvenance: [
        { id: "p1", fn: "regular_polygon", args: { vertices: ["A", "B", "C", "D"], side: "2a" }, quotes: ["Đáy ABCD là hình vuông cạnh 2a"] },
      ],
      relationCertificates: [
        {
          schema_version: "geometric-relation-certificate/1",
          relation_id: "relcert:t1",
          relation_kind: "tangent_to",
          subject_id: "(I)",
          target_id: "(ABCD)",
          SOURCE_GROUNDING_PROOF: { verified: true, call_id: "t1", fn: "sphere_tangent_plane", quotes: ["tiếp xúc với (ABCD)"] },
          GEOMETRIC_RELATION_PROOF: { verified: true, invariant: "distance_sq_center_to_plane_equals_radius_sq" },
          KERNEL_EXECUTION_PROOF: { verified: true },
          RESULT_CERTIFICATE: { verified: true },
        },
      ],
    });
    const resReal4 = docPhanHoiHybrid(realAdapter4Payload);
    expect(resReal4.ok).toBe(true);
    if (resReal4.ok) {
      const scReal4 = resReal4.envelope.scene3d as Scene3D;
      attachHybridViewToScene(scReal4, hybridViewCua(resReal4.envelope));
      const certReal4 = classifyPolygonShapeWithProvenance(scReal4, scReal4.objects[5]);
      expect(certReal4.provenance).toBe("GIVEN");
      expect(certReal4.certifiedShape).toBe("hình vuông");
    }

    // Tampered 4-layer relation certificate (KERNEL_EXECUTION_PROOF.verified = false) -> fail-closed
    const tamperedRelCert = structuredClone(realAdapter4Payload);
    (tamperedRelCert.route_d.relation_certificates![0] as Record<string, unknown>).KERNEL_EXECUTION_PROOF = { verified: false };
    expect(docPhanHoiHybrid(tamperedRelCert).ok).toBe(false);

    // Malformed source_provenance entry -> fail-closed
    const badProv = buildMinimalServedHybrid4Payload({
      sourceProvenance: ["not-an-object"],
    });
    expect(docPhanHoiHybrid(badProv).ok).toBe(false);
  });

  it("F4. Distinguishes the three BCR-01 regimes (Refused MISSING_DIMENSION vs Served Illustrative vs Contradictory)", () => {
    // Regime 1: Backend REFUSED MISSING_DIMENSION -> respected as refusal, never fabricated
    const refusedMissingDim = {
      schema_version: HYBRID_SIMULATION_SCHEMA,
      envelope: {
        status: "unsupported",
        reason_code: "MISSING_DIMENSION",
        message: "Đề bài thiếu kích thước bắt buộc để tính đại lượng mục tiêu.",
        scene3d: null,
        simulation_id: null,
      },
      route_d: {
        schema_version: HYBRID_SIMULATION_SCHEMA,
        adapter_version: HYBRID_SIMULATION_ADAPTER,
        contract_version: "typed-fact-next/2",
        status: "REFUSED",
        refusal: { code: "MISSING_DIMENSION", message: "Thiếu kích thước." },
      },
    };
    const r1 = docPhanHoiHybrid(refusedMissingDim);
    expect(r1.ok).toBe(true);
    if (r1.ok) {
      expect(r1.envelope.status).toBe("unsupported");
      expect(r1.envelope.scene3d).toBeNull();
    }

    // Regime 2: Backend SERVED illustrative configuration (partial facts) -> rendered truthfully without special-shape upgrade
    const servedIllustrative = buildMinimalServedHybrid4Payload({ baseLabel: "Đáy ABCD" });
    const r2 = docPhanHoiHybrid(servedIllustrative);
    expect(r2.ok).toBe(true);
    if (r2.ok) {
      const sc = r2.envelope.scene3d as Scene3D;
      expect(classifyScenePolygonShape(sc, sc.objects[5])).toBe("tứ giác");
    }

    // Regime 3: Contradictory contract (source_provenance says regular_polygon on non-square rectangle coordinates) -> CONTRADICTORY_OR_UNSUPPORTED
    const contradictory = buildMinimalServedHybrid4Payload({
      baseLabel: "Đáy ABCD",
      baseVertices: [["0", "0", "0"], ["4", "0", "0"], ["4", "2", "0"], ["0", "2", "0"]],
      sourceProvenance: [{ fact_id: "f_sq", kind: "regular_polygon", polygon: ["A", "B", "C", "D"], verified: true }],
    });
    const r3 = docPhanHoiHybrid(contradictory);
    expect(r3.ok).toBe(true);
    if (r3.ok) {
      const sc3 = r3.envelope.scene3d as Scene3D;
      attachHybridViewToScene(sc3, hybridViewCua(r3.envelope));
      expect(classifyPolygonShapeWithProvenance(sc3, sc3.objects[5]).provenance).toBe("CONTRADICTORY_OR_UNSUPPORTED");
    }
  });

  it("F5 (BLOCKER-2): Rejects compact `relation_certificates` with `verified: false` and `source_provenance` stubs lacking both `verified: true` and `quotes`", () => {
    const unverifiedCompactCert = buildMinimalServedHybrid4Payload({
      relationCertificates: [{ kind: "line_perp_plane", verified: false }],
    });
    expect(docPhanHoiHybrid(unverifiedCompactCert).ok).toBe(false);

    const unverifiedProvenanceStub = buildMinimalServedHybrid4Payload({
      sourceProvenance: [{ kind: "square", polygon: ["A", "B", "C", "D"] }],
    });
    expect(docPhanHoiHybrid(unverifiedProvenanceStub).ok).toBe(false);

    const explicitlyFalseProvenance = buildMinimalServedHybrid4Payload({
      sourceProvenance: [{ kind: "square", polygon: ["A", "B", "C", "D"], verified: false }],
    });
    expect(docPhanHoiHybrid(explicitlyFalseProvenance).ok).toBe(false);
  });
});
