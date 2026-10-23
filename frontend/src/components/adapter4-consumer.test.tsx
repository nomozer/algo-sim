import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { registerAllSimulations } from "../simulations";
import { useAppStore } from "../state/store";
import { docPhanHoiHybrid, hybridViewCua, kiemHybridView } from "../simulations/domains/geometry/hybrid-preview-adapter";

const rows = JSON.parse(readFileSync(resolve(__dirname, "../../../docs/evaluation/geometry/runs/hybrid-disabled-integration/results/adapter4-consumer-after-review/adapter4-frontend-fixtures.json"), "utf8")).fixtures;
const response = (row = rows[0]) => structuredClone({ ...row, schema_version: row.route_d.schema_version });

describe("Adapter /4 offline consumer", () => {
  it.each(rows as any[])("consumes real engine fixture $id without changing geometry", (row) => {
    const raw = response(row);
    const result = docPhanHoiHybrid(raw);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.envelope.scene3d).toEqual(raw.envelope.scene3d);
    const view = hybridViewCua(result.envelope)!;
    expect(view.adapter_version).toBe("hybrid-simulation-adapter/4");
    expect(view.answers).toHaveLength(Object.keys(raw.route_d.answers).length);
    expect(kiemHybridView(view, raw.envelope.scene3d)).toBeNull();
    registerAllSimulations();
    useAppStore.getState().loadEnvelope(result.envelope as any);
    expect(useAppStore.getState().active).not.toBeNull();
    expect(useAppStore.getState().analysisError).toBeNull();
  });

  it.each([
    ["source authority", (r: any) => { r.route_d.source_verification.authority = "legacy"; }],
    ["mixed wrapper", (r: any) => { r.schema_version = "hybrid-route-d-preview/1"; }],
    ["contract", (r: any) => { r.route_d.contract_version = "typed-fact-next/1"; }],
    ["adapter", (r: any) => { r.route_d.adapter_version = "hybrid-simulation-adapter/3"; }],
    ["unit", (r: any) => { r.route_d.length_unit = "b"; }],
    ["numeric binding", (r: any) => { r.route_d.answer_exact.g_ratio.coef = "7"; }],
    ["unpaired answer", (r: any) => { delete r.route_d.answers.g_ratio; }],
    ["closure", (r: any) => { r.route_d.sections[0].closure_certificate.verified = false; }],
    ["closure downgrade", (r: any) => { r.route_d.sections[0].boundary = null; r.route_d.sections[0].closure_certificate = null; }],
    ["empty vertices", (r: any) => { r.route_d.sections[0].boundary = null; r.route_d.sections[0].closure_certificate = null; r.route_d.sections[0].vertices = []; }],
    ["source edge", (r: any) => { r.route_d.sections[0].vertices[1].edge = ["A", "B"]; }],
    ["boundary", (r: any) => { r.route_d.sections[0].boundary.reverse(); r.route_d.sections[0].boundary.pop(); }],
    ["topology", (r: any) => { const p = r.envelope.scene3d.objects.find((o: any) => o.type === "section").polygon; [p[1], p[2]] = [p[2], p[1]]; }],
    ["provenance", (r: any) => { r.route_d.sections[0].vertices[0].provenance = "INVENTED"; }],
  ])("rejects mismatched %s", (_, mutate) => {
    const raw = response(); (mutate as (r: any) => void)(raw);
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
  });

  it("retains derived provenance without presenting it as a given", () => {
    const raw = response(rows.find((r: any) => r.id === "PARTIAL-1of2-construct"));
    const result = docPhanHoiHybrid(raw);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const view = hybridViewCua(result.envelope) as any;
    expect(view.sections[0].vertices.find((v: any) => v.label === "I")).toMatchObject({ provenance: "DERIVED_FRESH", stated: false });
    view.sections[0].vertices.find((v: any) => v.label === "I").stated = true;
    expect(kiemHybridView(view, raw.envelope.scene3d)).not.toBeNull();
  });

  it.each(["role", "notation", "display_group"])("rejects derived point promoted through %s", (field) => {
    const raw = response(rows.find((r: any) => r.id === "PARTIAL-1of2-construct"));
    const point = raw.envelope.scene3d.objects.find((o: any) => o.id === "I");
    point[field] = field === "display_group" ? ["given"] : field === "notation" ? "I" : "Điểm đề cho";
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
  });

  it("refuses a success scene attached to a refusal", () => {
    const raw = response();
    raw.route_d.status = "REFUSED";
    raw.route_d.refusal = { code: "SOURCE_OBJECT_MISMATCH" };
    raw.envelope.status = "unsupported";
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
  });
});
