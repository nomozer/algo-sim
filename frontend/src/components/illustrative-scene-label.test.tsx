import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  cauCauHinhMinhHoa,
  docPhanHoiHybrid,
  hybridViewCua,
  kiemHybridView,
} from "../simulations/domains/geometry/hybrid-preview-adapter";

/**
 * Run `real-world-end-to-end-reliability`: an Adapter /4 result whose figure is NOT fixed by the source (a proven
 * height-invariant answer) carries `route_d.scene_configuration.unique = false`. The client must keep that label with
 * the view (never present the scene as the unique configuration) and reject a malformed or self-promoted label.
 */
const rows = JSON.parse(readFileSync(resolve(__dirname, "../../../docs/evaluation/geometry/runs/hybrid-disabled-integration/results/adapter4-consumer-after-review/adapter4-frontend-fixtures.json"), "utf8")).fixtures;
const base = () => structuredClone({ ...rows[0], schema_version: rows[0].route_d.schema_version });
const CFG = {
  unique: false, kind: "HEIGHT_INVARIANT_ILLUSTRATIVE", free_parameter: "height", free_for: ["S"],
  illustrative_h2: "1", invariance_certificate: { method: "rational_function_identity_in_h2", max_degree: 3 },
};

describe("Adapter /4 illustrative (non-unique) scene label", () => {
  it("unique scenes carry no illustrative note", () => {
    const r = docPhanHoiHybrid(base());
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(cauCauHinhMinhHoa(hybridViewCua(r.envelope))).toBeNull();
  });

  it("keeps the non-unique label on the view and produces a learner note", () => {
    const raw = base();
    raw.route_d.scene_configuration = structuredClone(CFG);
    const r = docPhanHoiHybrid(raw);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const view = hybridViewCua(r.envelope)!;
    expect(view.scene_configuration).toMatchObject({ unique: false, kind: "HEIGHT_INVARIANT_ILLUSTRATIVE" });
    expect(kiemHybridView(view, raw.envelope.scene3d)).toBeNull();
    const note = cauCauHinhMinhHoa(view);
    expect(note).toMatch(/minh họa/);
    expect(note).toMatch(/không phụ thuộc/);
  });

  it("keeps a similarity-scale label and says the drawn lengths are not source data", () => {
    const raw = base();
    raw.route_d.scene_configuration = { unique: false, kind: "SIMILARITY_SCALE_ILLUSTRATIVE", free_parameter: "scale",
      free_for: ["AB"], source_length_supplied: false, scale_origin: "INTERNAL_CONSTRUCTION_CONVENTION" };
    const r = docPhanHoiHybrid(raw);
    if (!r.ok) throw new Error(r.reason);
    const note = cauCauHinhMinhHoa(hybridViewCua(r.envelope))!;
    expect(note).toMatch(/không cho độ dài nào/);
    expect(note).toMatch(/không phải dữ kiện/);
    expect(note).not.toMatch(/\d/);
  });

  it("keeps a target-invariant label and says the drawn figure is one of many", () => {
    const raw = base();
    raw.route_d.scene_configuration = { unique: false, kind: "TARGET_INVARIANT_ILLUSTRATIVE", free_parameter: "shape",
      free_for: ["AB", "BC"], source_length_supplied: false };
    const r = docPhanHoiHybrid(raw);
    if (!r.ok) throw new Error(r.reason);
    const note = cauCauHinhMinhHoa(hybridViewCua(r.envelope))!;
    expect(note).toMatch(/không xác định duy nhất/);
    expect(note).toMatch(/không phải dữ kiện/);
    expect(note).not.toMatch(/[0-9]/);
  });

  it.each([
    ["claims unique", (c: any) => { c.unique = true; }],
    ["unknown kind", (c: any) => { c.kind = "GUESSED_HEIGHT"; }],
    ["free_for not strings", (c: any) => { c.free_for = [1]; }],
    ["missing free_parameter", (c: any) => { delete c.free_parameter; }],
  ])("rejects a malformed label: %s", (_, mutate) => {
    const raw = base();
    raw.route_d.scene_configuration = structuredClone(CFG);
    (mutate as (c: any) => void)(raw.route_d.scene_configuration);
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
  });

  it("re-validates a stored view: a label promoted to unique after the fact is rejected", () => {
    const raw = base();
    raw.route_d.scene_configuration = structuredClone(CFG);
    const r = docPhanHoiHybrid(raw);
    if (!r.ok) throw new Error(r.reason);
    const view = structuredClone(hybridViewCua(r.envelope)) as any;
    view.scene_configuration.unique = true;
    expect(kiemHybridView(view, raw.envelope.scene3d)).not.toBeNull();
  });
});
