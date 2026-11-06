import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToString } from "react-dom/server";
import { beforeEach, describe, expect, it } from "vitest";
import { docPhanHoiPhanTich } from "../llm/client";
import { registerAllSimulations } from "../simulations";
import { Scene3DExplorer } from "../simulations/domains/geometry/Scene3DExplorer";
import {
  docPhanHoiHybrid,
  hybridViewCua,
  kiemHybridView,
} from "../simulations/domains/geometry/hybrid-preview-adapter";
import { veKhongGian } from "../simulations/domains/geometry/scene3d-chart";
import { hopLeScene3D, phanTichToanHocCuaCanh } from "../simulations/domains/geometry/scene3d-model";
import { withSubEntities } from "../simulations/domains/geometry/scene3d-subentities";
import { __resetHistoryForTest } from "../state/history";
import { useAppStore } from "../state/store";
import { buildFailureMessage } from "./photo-problem-flow";
import { SimulationWorkspace, UnsupportedNotice } from "./SimulationWorkspace";

type FixtureRow = {
  id: string;
  category: string;
  source_corpus: string;
  problem_text: string;
  response: Record<string, any>;
};

const bundle = JSON.parse(
  readFileSync(
    resolve(
      __dirname,
      "../../../docs/evaluation/geometry/runs/hybrid-master-backend-replacement/product-integration-frontend-fixtures.json",
    ),
    "utf8",
  ),
) as { fixtures: FixtureRow[] };

function fixtureOf(id: string): Record<string, any> {
  const found = bundle.fixtures.find((f) => f.id === id);
  if (!found) throw new Error(`Missing fixture ${id}`);
  return structuredClone(found.response);
}

beforeEach(() => {
  __resetHistoryForTest();
  registerAllSimulations();
  useAppStore.getState().reset();
});

describe("Hybrid /4 product integration — Category B plane-section-certificate/1", () => {
  it.each(["K-A01", "R1-B01"])(
    "accepts real Category B section fixture %s through client reader, store, and Scene3DExplorer without leaking machine IDs",
    (id) => {
      const raw = fixtureOf(id);
      const parsed = docPhanHoiHybrid(raw);
      expect(parsed.ok, parsed.ok ? "" : parsed.reason).toBe(true);
      if (!parsed.ok) return;

      const env = docPhanHoiPhanTich(raw);
      expect(env.status).toBe("ok");
      if (env.status !== "ok") return;

      const view = hybridViewCua(env);
      expect(view?.adapter_version).toBe("hybrid-simulation-adapter/4");
      expect(view?.sections).toHaveLength(1);
      expect(kiemHybridView(view, (env as any).scene3d)).toBeNull();
      expect(hopLeScene3D((env as any).scene3d)).toBe(true);

      useAppStore.getState().loadEnvelope(env, undefined, id);
      const state = useAppStore.getState();
      expect(state.active).not.toBeNull();
      expect(state.analysisError).toBeNull();
      expect(state.unsupported).toBeNull();
      expect(state.view).toBe("workspace");

      const html = renderToString(
        <Scene3DExplorer
          scene={(state.active!.envelope as any).scene3d}
          de={state.active!.envelope.description ?? null}
          tieuDe={state.active!.envelope.title ?? null}
          hybrid={hybridViewCua(state.active!.envelope)}
        />,
      ).replace(/<!--.*?-->/g, "");
      expect(html).toContain("Phân tích toán học");
      expect(html).not.toMatch(/\b(kq_|td_|mp_td_)[A-Za-z0-9_]+/);
      expect(html).not.toContain("section:td_");
    },
  );

  it.each<[string, (raw: any) => void]>([
    ["certificate_version", (r) => { r.route_d.sections[0].certificate_version = "plane-section-certificate/0"; }],
    ["certificate_category", (r) => { r.route_d.sections[0].certificate_category = "DECLARED"; }],
    ["section_object_id", (r) => { r.route_d.sections[0].section_object_id = "td_other"; }],
    ["declared_boundary", (r) => { r.route_d.sections[0].declared_boundary = ["A", "B", "C"]; }],
    ["open section", (r) => { r.envelope.scene3d.objects.find((o: any) => o.type === "section").closed = false; }],
    ["identity diagnostics", (r) => { r.envelope.scene3d.objects.find((o: any) => o.type === "section").identity_diagnostics = ["dup"]; }],
    ["solid_object_id", (r) => { r.route_d.sections[0].solid_object_id = "missing_solid"; }],
    ["plane_object_id", (r) => { r.route_d.sections[0].plane_object_id = "mp_other"; }],
    ["plane_points", (r) => { r.route_d.sections[0].plane_points = ["A", "B", "C"]; }],
    ["through_point", (r) => { r.route_d.sections[0].through_point = "B"; }],
    ["ordinal", (r) => { r.route_d.sections[0].vertices[0].ordinal = 1; }],
    ["vertex xyz", (r) => { r.route_d.sections[0].vertices[0].xyz = ["9", "9", "9"]; }],
    ["stated promoted to true", (r) => { r.route_d.sections[0].vertices[0].stated = true; }],
    ["entity_id mismatch", (r) => { r.route_d.sections[0].vertices[1].entity_id = "forged_entity"; }],
    ["anonymous_coordinate_fallback", (r) => {
      r.envelope.scene3d.objects.find((o: any) => o.type === "section").endpoint_entities[1].anonymous_coordinate_fallback = true;
    }],
    ["supporting edge labels", (r) => { r.route_d.sections[0].vertices[1].edge = ["A", "B"]; }],
    ["supporting edge indices", (r) => { r.route_d.sections[0].vertices[1].solid_edge_vertex_indices = [0, 1]; }],
    ["source_kind mismatch", (r) => { r.route_d.sections[0].vertices[2].source_kind = "SOLID_VERTEX"; }],
    ["unnamed cut forged label", (r) => {
      const cut = r.route_d.sections[0].vertices.find((v: any) => v.provenance === "ENGINE_DERIVED_EDGE_CUT");
      cut.label = "A";
    }],
    ["provenance mismatch", (r) => {
      const cut = r.route_d.sections[0].vertices.find((v: any) => v.provenance === "ENGINE_DERIVED_EDGE_CUT");
      cut.provenance = "THROUGH_POINT_REUSE";
    }],
    ["closure verified=false", (r) => { r.route_d.sections[0].closure_certificate.verified = false; }],
    ["closure version mismatch", (r) => { r.route_d.sections[0].closure_certificate.version = "other/1"; }],
    ["closure producer mismatch", (r) => { r.route_d.sections[0].closure_certificate.producer = "forged.producer"; }],
    ["closure area_squared missing", (r) => { r.route_d.sections[0].closure_certificate.area_squared = "invalid"; }],
    ["plane_equation missing", (r) => { r.route_d.sections[0].plane_equation = null; }],
    ["plane_equation zero normal", (r) => { r.route_d.sections[0].plane_equation = { normal: ["0", "0", "0"], offset: "1" }; }],
    ["boundary mismatch", (r) => { r.route_d.sections[0].boundary = [...r.route_d.sections[0].boundary].reverse(); }],
  ])("rejects tampered Category B field: %s", (_name, mutate) => {
    const raw = fixtureOf("K-A01");
    mutate(raw);
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
    const clientEnv = docPhanHoiPhanTich(raw);
    expect(clientEnv.status).toBe("unsupported");
  });

  it("rejects Category B through-point reuse on edge cut when label or through_point is forged (R1-B01)", () => {
    const raw = fixtureOf("R1-B01");
    const tpVertex = raw.route_d.sections[0].vertices.find((v: any) => v.provenance === "THROUGH_POINT_REUSE");
    expect(tpVertex.source_kind).toBe("SOLID_EDGE_INTERSECTION");
    expect(tpVertex.label).toBe("H");

    const badLabel = structuredClone(raw);
    badLabel.route_d.sections[0].vertices.find((v: any) => v.provenance === "THROUGH_POINT_REUSE").label = null;
    expect(docPhanHoiHybrid(badLabel).ok).toBe(false);
  });
});

describe("Hybrid /4 product integration — route-d-clarification/1 learner notice", () => {
  it.each(["S2-C-A01_goc_chieu", "S2-C-D06_unnamed_prism"])(
    "surfaces concrete Vietnamese clarification question for %s without leaking machine codes",
    (id) => {
      const raw = fixtureOf(id);
      const expectedQuestion = raw.route_d.refusal.clarification.question as string;
      expect(expectedQuestion).toBeTruthy();

      const env = docPhanHoiPhanTich(raw);
      expect(env.status).toBe("unsupported");
      if (env.status !== "unsupported") return;
      expect(env.clarification?.question).toBe(expectedQuestion);
      expect("unresolved_id" in (env.clarification as unknown as Record<string, unknown>)).toBe(false);
      expect("schema_version" in (env.clarification as unknown as Record<string, unknown>)).toBe(false);

      useAppStore.getState().loadUnsupported(env);
      const u = useAppStore.getState().unsupported!;
      const html = renderToString(<UnsupportedNotice unsupported={u} />).replace(/<!--.*?-->/g, "");
      expect(html).toContain(expectedQuestion);
      expect(html).toContain("data-clarification-question");
      expect(html).not.toContain("AMBIGUOUS_FACT");
      expect(html).not.toContain("route-d-clarification/1");
      expect(html).not.toContain("u1");
    },
  );

  it("handles unsupported clarification (question: null) cleanly without rendering an empty question", () => {
    const raw = fixtureOf("S2-E-E02_truncated_pyramid");
    expect(raw.route_d.refusal.clarification.kind).toBe("unsupported");
    expect(raw.route_d.refusal.clarification.question).toBeNull();

    const env = docPhanHoiPhanTich(raw);
    expect(env.status).toBe("unsupported");
    if (env.status !== "unsupported") return;
    expect(env.clarification?.question).toBeNull();

    useAppStore.getState().loadUnsupported(env);
    const html = renderToString(<UnsupportedNotice unsupported={useAppStore.getState().unsupported!} />).replace(
      /<!--.*?-->/g,
      "",
    );
    expect(html).not.toContain("data-clarification-question");
    expect(html).not.toContain("OUT_OF_SCOPE");
    expect(html).not.toContain("VALID_BUT_UNSUPPORTED");
  });

  it.each<[string, (raw: any) => void]>([
    ["backend-smuggled envelope.clarification", (r) => { r.envelope.clarification = r.route_d.refusal.clarification; }],
    ["wrong clarification schema_version", (r) => { r.route_d.refusal.clarification.schema_version = "other/1"; }],
    ["kind/nlu_class mismatch", (r) => { r.route_d.refusal.clarification.nlu_class = "VALID_BUT_UNSUPPORTED"; }],
    ["missing question on ambiguous", (r) => { r.route_d.refusal.clarification.question = null; }],
    ["empty quote", (r) => { r.route_d.refusal.clarification.quote = "   "; }],
    ["empty spans array", (r) => { r.route_d.refusal.clarification.spans = []; }],
    ["invalid spans", (r) => { r.route_d.refusal.clarification.spans = [[5, 2]]; }],
    ["internal token in question", (r) => { r.route_d.refusal.clarification.question = "Làm rõ @m_1 hoặc kq_g1::edge?"; }],
  ])("rejects malformed clarification record: %s", (_name, mutate) => {
    const raw = fixtureOf("S2-C-A01_goc_chieu");
    mutate(raw);
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
    const fallback = docPhanHoiPhanTich(raw);
    expect(fallback.status).toBe("unsupported");
    if (fallback.status === "unsupported") {
      expect(fallback.failure_category).toBe("verification_gap");
      expect(fallback.clarification).toBeUndefined();
    }
  });
});

describe("Hybrid /4 product integration — recoverable infrastructure errors clear stale UI state", () => {
  it("clears stale unsupported notice and active scene on recoverable infrastructure error", () => {
    const servedEnv = docPhanHoiPhanTich(fixtureOf("K-A01"));
    expect(servedEnv.status).toBe("ok");
    if (servedEnv.status === "ok") {
      useAppStore.getState().loadEnvelope(servedEnv, undefined, "K-A01");
      expect(useAppStore.getState().active).not.toBeNull();
      expect(useAppStore.getState().view).toBe("workspace");
    }

    const refusalEnv = docPhanHoiPhanTich(fixtureOf("S2-C-A01_goc_chieu"));
    expect(refusalEnv.status).toBe("unsupported");
    if (refusalEnv.status === "unsupported") {
      useAppStore.getState().loadUnsupported(refusalEnv);
      expect(useAppStore.getState().unsupported).not.toBeNull();
      expect(useAppStore.getState().active).toBeNull();
      expect(useAppStore.getState().view).toBe("home");
    }

    // Starting a new analysis clears stale unsupported notice immediately.
    useAppStore.getState().setAnalyzing(true);
    expect(useAppStore.getState().unsupported).toBeNull();

    // Infrastructure HTTP 503/502/504 failure sets analysisError without leaving stale refusal or active scene.
    useAppStore.getState().loadUnsupported(refusalEnv as any);
    useAppStore
      .getState()
      .setAnalysisError("Tuyến Hybrid ở chế độ mô phỏng tích hợp chưa nạp được bộ dữ liệu phát lại.");
    const st = useAppStore.getState();
    expect(st.analysisError).toContain("chưa nạp được bộ dữ liệu");
    expect(st.unsupported).toBeNull();
    expect(st.active).toBeNull();
    expect(st.view).toBe("home");
  });

  it("clears activeAssignment and semanticFocus on refusal, infrastructure error, and invalid envelope (M18)", () => {
    const fakeAssignment = { id: "asg-1", title: "Bài cô giao", classroomId: "cls-1" } as any;
    const servedEnv = docPhanHoiPhanTich(fixtureOf("K-A01"));
    const refusalEnv = docPhanHoiPhanTich(fixtureOf("S2-C-A01_goc_chieu"));
    expect(servedEnv.status).toBe("ok");
    expect(refusalEnv.status).toBe("unsupported");
    if (servedEnv.status !== "ok" || refusalEnv.status !== "unsupported") return;

    // 1. Refusal clears activeAssignment & semanticFocus
    useAppStore.getState().setActiveAssignment(fakeAssignment);
    useAppStore.getState().setSemanticFocus("step-1" as any);
    useAppStore.getState().loadEnvelope(servedEnv, undefined, "K-A01");
    useAppStore.getState().setView("home");
    expect(useAppStore.getState().activeAssignment).not.toBeNull();
    useAppStore.getState().loadUnsupported(refusalEnv);
    expect(useAppStore.getState().activeAssignment).toBeNull();
    expect(useAppStore.getState().semanticFocus).toBeNull();

    // 2. Infrastructure error clears activeAssignment & semanticFocus
    useAppStore.getState().setActiveAssignment(fakeAssignment);
    useAppStore.getState().setSemanticFocus("step-2" as any);
    useAppStore.getState().loadEnvelope(servedEnv, undefined, "K-A01");
    useAppStore.getState().setView("home");
    useAppStore.getState().setAnalysisError("Dịch vụ trích xuất gặp sự cố kết nối.");
    expect(useAppStore.getState().activeAssignment).toBeNull();
    expect(useAppStore.getState().semanticFocus).toBeNull();

    // 3. Invalid envelope rejection clears activeAssignment & semanticFocus
    useAppStore.getState().setActiveAssignment(fakeAssignment);
    useAppStore.getState().setSemanticFocus("step-3" as any);
    useAppStore.getState().loadEnvelope({ ...servedEnv, simulation_id: "unknown.sim" } as any);
    expect(useAppStore.getState().activeAssignment).toBeNull();
    expect(useAppStore.getState().semanticFocus).toBeNull();
  });

  it("includes route-d-clarification/1 question in Photo Review -> Build failure message without duplicating", () => {
    const refusalEnv = docPhanHoiPhanTich(fixtureOf("S2-C-A01_goc_chieu"));
    expect(refusalEnv.status).toBe("unsupported");
    if (refusalEnv.status !== "unsupported") return;
    const msg = buildFailureMessage(refusalEnv);
    expect(msg).toContain(refusalEnv.clarification!.question!);
  });
});

describe("Hybrid /4 product integration — all 16 scope & refusal classes (§VI)", () => {
  it("covers all 16 scope and refusal classes in the product fixture bundle", () => {
    const categories = new Set(bundle.fixtures.map((f) => f.category));
    expect(categories.size).toBe(16);
  });

  it.each(bundle.fixtures)(
    "consumes real /api/analyze /4 response $id ($category) cleanly through store and UI",
    (row) => {
      const raw = structuredClone(row.response);
      const parsed = docPhanHoiHybrid(raw);
      expect(parsed.ok, parsed.ok ? "" : parsed.reason).toBe(true);
      const env = docPhanHoiPhanTich(raw);

      if (raw.route_d.status === "SERVED") {
        expect(env.status).toBe("ok");
        if (env.status !== "ok") return;
        const scene = (env as any).scene3d;
        expect(hopLeScene3D(scene)).toBe(true);
        const view = hybridViewCua(env);
        expect(view).not.toBeNull();
        expect(kiemHybridView(view, scene)).toBeNull();

        useAppStore.getState().loadEnvelope(env, undefined, row.id);
        const st = useAppStore.getState();
        expect(st.active).not.toBeNull();
        expect(st.unsupported).toBeNull();
        expect(st.analysisError).toBeNull();

        const day = withSubEntities(scene);
        const chart = veKhongGian(day);
        expect(chart.objects.length).toBeGreaterThan(0);

        const analysis = phanTichToanHocCuaCanh(day, view);
        const answerValues = Object.values(raw.route_d.answers as Record<string, string>);
        expect(view!.answers.map((a) => a.symbolic)).toEqual(answerValues);
        for (const ans of answerValues) {
          expect(analysis.requestedResults.some((r) => r.valueDisplay === ans)).toBe(true);
        }

        const html = renderToString(
          <Scene3DExplorer
            scene={(st.active!.envelope as any).scene3d}
            de={st.active!.envelope.description ?? null}
            tieuDe={st.active!.envelope.title ?? null}
            hybrid={hybridViewCua(st.active!.envelope)}
          />,
        ).replace(/<!--.*?-->/g, "");
        expect(html).not.toMatch(/\b(kq_|td_|mp_td_)[A-Za-z0-9_]+/);
        expect(html).not.toContain("section:td_");
        if (answerValues.length > 0) {
          expect(html).toContain("Phân tích toán học");
        }
      } else {
        expect(env.status).toBe("unsupported");
        if (env.status !== "unsupported") return;
        expect((env as any).scene3d).toBeUndefined();
        useAppStore.getState().loadUnsupported(env);
        const st = useAppStore.getState();
        expect(st.active).toBeNull();
        expect(st.unsupported).not.toBeNull();
        const html = renderToString(<UnsupportedNotice unsupported={st.unsupported!} />).replace(
          /<!--.*?-->/g,
          "",
        );
        if (raw.route_d.refusal?.clarification?.question) {
          expect(html).toContain("data-clarification-question");
          expect(html).toContain(raw.route_d.refusal.clarification.question);
        }
        expect(html).not.toContain("route-d-clarification/1");
      }
    },
  );
});

describe("Hybrid /4 product integration — «Đề bài» là đề người học đã gửi (SOURCE_GIVEN)", () => {
  const served = bundle.fixtures.filter((f) => f.response.route_d?.status === "SERVED");

  it.each(served)("$id: envelope mang đề nguyên văn (problem_statement), envelope.description KHÔNG phải đề", (row) => {
    const env = docPhanHoiPhanTich(structuredClone(row.response));
    if (env.status !== "ok") throw new Error(row.id);
    // Nền đỏ của lỗi: tuyến Hybrid đặt câu miễn trừ vào description ⇒ nút «Đề bài» mất mọi giả thiết.
    expect(env.description).not.toBe(row.problem_text);
    useAppStore.getState().loadEnvelope(env, undefined, row.problem_text);
    expect(useAppStore.getState().active!.envelope.problem_statement).toBe(row.problem_text);
    // Mở lại từ Lịch sử (0 AI) vẫn mang đúng đề.
    const hid = useAppStore.getState().activeHistoryId!;
    useAppStore.getState().reset();
    useAppStore.getState().reopenFromHistory(hid);
    expect(useAppStore.getState().active!.envelope.problem_statement).toBe(row.problem_text);
  });

  it("bài giao cho lớp (envelope gửi đi, mở lại KHÔNG kèm đề) vẫn mang đề — review F1", () => {
    const row = served[0];
    const env = docPhanHoiPhanTich(structuredClone(row.response));
    if (env.status !== "ok") throw new Error(row.id);
    useAppStore.getState().loadEnvelope(env, undefined, row.problem_text);
    // AssignDialog gửi `active.envelope`; máy chủ lưu nguyên dict (`_validated_envelope`); AssignmentsView mở lại bằng
    // `loadEnvelope(a.envelope)` — không đối số đề, trên máy học sinh không có Lịch sử của bài này.
    const giao = JSON.parse(JSON.stringify(useAppStore.getState().active!.envelope));
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAppStore.getState().loadEnvelope(giao);
    expect(useAppStore.getState().active!.envelope.problem_statement).toBe(row.problem_text);
  });

  it("SimulationWorkspace đưa đề nguyên văn vào «Đề bài» trước description/title", () => {
    // Tích hợp Axo (axo-hybrid4-integration-reliability): thay quét chuỗi nguồn bằng hành vi. Envelope đã đóng dấu
    // `problem_statement` (như bài giao cho lớp) mở KHÔNG kèm đề vẫn hiện đề nguyên văn, không hiện lời miễn trừ.
    const row = served[0];
    const env = docPhanHoiPhanTich(structuredClone(row.response));
    if (env.status !== "ok") throw new Error(row.id);
    const stamped = { ...env, problem_statement: row.problem_text };
    useAppStore.getState().loadEnvelope(stamped);
    Object.assign(useAppStore.getInitialState(), useAppStore.getState());
    const html = renderToString(<SimulationWorkspace />);
    const statement = html.match(/id="dock-prob-statement"[^>]*data-statement-source="([a-z]+)"[^>]*>([\s\S]*?)<\/div>/u);
    expect(statement?.[1]).toBe("learner");
    expect(statement?.[2]?.replace(/<[^>]+>/gu, "")).toContain(row.problem_text.slice(0, 20));
    if (env.description) expect(statement?.[2] ?? "").not.toContain(env.description);
  });

  it("đề có ký hiệu ⊥ / ∥ / ′ đi qua store không bị chuẩn hoá", () => {
    const row = served[0];
    const env = docPhanHoiPhanTich(structuredClone(row.response));
    if (env.status !== "ok") throw new Error(row.id);
    const de = "Cho hình chóp S.ABCD, SA ⊥ (ABCD), AB ∥ CD, A′ là điểm đối xứng; góc ∠SBA = 60°.";
    useAppStore.getState().loadEnvelope(env, undefined, de);
    expect(useAppStore.getState().active!.envelope.problem_statement).toBe(de);
  });
});
