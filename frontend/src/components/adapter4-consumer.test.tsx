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

  // Review MAJOR-1: provenance claims must agree with the scene point in both directions.
  it.each([
    ["derived → source named", "DERIVED_FRESH", (v: any) => { v.provenance = "SOURCE_NAMED"; v.stated = true; }],
    ["derived → stated unnamed, unstated", "DERIVED_FRESH", (v: any) => { v.provenance = "STATED_UNNAMED"; }],
    ["stated unnamed → unstated", "STATED_UNNAMED", (v: any) => { v.stated = false; }],
    ["source named → unstated", "SOURCE_NAMED", (v: any) => { v.stated = false; }],
  ])("rejects provenance relabel %s", (_, from, mutate) => {
    const row = rows.find((r: any) => r.route_d.sections.some((s: any) => s.vertices.some((v: any) => v.provenance === from)));
    const raw = response(row);
    (mutate as (v: any) => void)(raw.route_d.sections.flatMap((s: any) => s.vertices).find((v: any) => v.provenance === from));
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
  });

  // Review MAJOR-2: dropping the closure certificate is not a way into the plane-only exception.
  const haCapChungChi = (r: any) => { r.route_d.sections[0].boundary = null; r.route_d.sections[0].closure_certificate = null; };
  const khoiDanXuat = (r: any) => {
    const sec = r.envelope.scene3d.objects.find((o: any) => o.type === "section");
    return r.envelope.scene3d.objects.find((o: any) => o.type === "solid" && !sec.depends.includes(o.id));
  };
  it.each([
    ["derived solid without vertex_ids", (r: any) => { delete khoiDanXuat(r).vertex_ids; }],
    ["derived solid with a renamed vertex", (r: any) => { khoiDanXuat(r).vertex_ids[1] = "Qx"; }],
    ["derived solid removed", (r: any) => {
      const id = khoiDanXuat(r).id;
      r.envelope.scene3d.objects = r.envelope.scene3d.objects.filter((o: any) => o.id !== id);
    }],
  ])("rejects a certificate-less section with %s", (_, mutate) => {
    const raw = response(rows.find((r: any) => "g_res" in r.route_d.answers));
    haCapChungChi(raw); (mutate as (r: any) => void)(raw);
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
  });

  it("accepts the real plane-only section, which has no derived solid", () => {
    const row = rows.find((r: any) => r.route_d.sections.some((s: any) => s.closure_certificate === null));
    expect(row).toBeDefined();
    expect(docPhanHoiHybrid(response(row)).ok).toBe(true);
  });

  it("rejects an empty closure rule", () => {
    const raw = response(); raw.route_d.sections[0].closure_certificate.rule = "";
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
  });

  // Review MINOR: malformed scene shapes never make the boundary throw.
  it.each([
    ["section without depends", false, (r: any) => { delete r.envelope.scene3d.objects.find((o: any) => o.type === "section").depends; }],
    ["non-array edge indices", false, (r: any) => {
      const src = r.envelope.scene3d.objects.find((o: any) => o.type === "section").vertex_sources
        .find((x: any) => x.solid_edge_vertex_indices);
      src.solid_edge_vertex_indices = 3;
    }],
    // Off the section path: notation typing belongs to the general scene gate (`hopLeScene3D`), not to /4.
    ["numeric notation", true, (r: any) => { r.envelope.scene3d.objects.find((o: any) => o.type === "point3").notation = 7; }],
  ])("does not throw on %s", (_, ok, mutate) => {
    const raw = response(); (mutate as (r: any) => void)(raw);
    expect(() => docPhanHoiHybrid(raw)).not.toThrow();
    expect(docPhanHoiHybrid(raw).ok).toBe(ok);
  });

  // The 25 real refusals of this run (`hybrid-offline-consumer/results/fixtures.json`).
  const refusals = JSON.parse(readFileSync(resolve(__dirname, "../../../docs/evaluation/geometry/runs/hybrid-offline-consumer/results/fixtures.json"), "utf8"))
    .fixtures.filter((r: any) => r.route_d.status === "REFUSED");
  it("covers every refusal fixture of the offline consumer run", () => expect(refusals).toHaveLength(25));
  it.each(refusals as any[])("keeps refusal $id without a scene", (row) => {
    const result = docPhanHoiHybrid(structuredClone(row));
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.envelope.scene3d).toBeUndefined();
    expect(result.envelope.reason_code).toBe(row.route_d.refusal.code);
  });

  it("refuses a success scene attached to a refusal", () => {
    const raw = response();
    raw.route_d.status = "REFUSED";
    raw.route_d.refusal = { code: "SOURCE_OBJECT_MISMATCH" };
    raw.envelope.status = "unsupported";
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
  });
});
