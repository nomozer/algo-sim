import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  cauMucTieuSoChuaTraLoi,
  docPhanHoiHybrid,
  hybridViewCua,
  kiemHybridView,
} from "../simulations/domains/geometry/hybrid-preview-adapter";

/**
 * Run `compositional-semantics-simulation-goals`: a source asking a trigonometric VALUE of an angle ("Tính côsin của góc
 * …") is served as the constructed, verified angle with `route_d.source_goal_completion` stating the number NOT answered.
 * The client keeps that record on the view, tells the learner the value is not computed for them, and rejects a record
 * that claims the goal answered or a number shown.
 */
const rows = JSON.parse(readFileSync(resolve(__dirname, "../../../docs/evaluation/geometry/runs/hybrid-disabled-integration/results/adapter4-consumer-after-review/adapter4-frontend-fixtures.json"), "utf8")).fixtures;
const base = () => structuredClone({ ...rows[0], schema_version: rows[0].route_d.schema_version });
const SGC = {
  schema_version: "source-goal-completion/1", source_goal_fully_satisfied: false, numeric_answer_shown: false,
  goals: [{ goal_id: "q1", source_request: "TRIGONOMETRIC_VALUE_OF_ANGLE", function: "cos",
    simulation_objective: "ANGLE_CONSTRUCTED_AND_VERIFIED", state: "GOAL_VISUALIZATION_READY", numeric_source_goal: "NOT_ANSWERED",
    value_defined: true }],
};

describe("numeric source goal not answered (cos / tan of an angle)", () => {
  it("results without the record carry no note", () => {
    const r = docPhanHoiHybrid(base());
    if (!r.ok) throw new Error(r.reason);
    expect(cauMucTieuSoChuaTraLoi(hybridViewCua(r.envelope))).toBeNull();
  });

  it("keeps the record and tells the learner the value is not computed, without any number", () => {
    const raw = base();
    raw.route_d.source_goal_completion = structuredClone(SGC);
    const r = docPhanHoiHybrid(raw);
    if (!r.ok) throw new Error(r.reason);
    const view = hybridViewCua(r.envelope)!;
    expect(kiemHybridView(view, raw.envelope.scene3d)).toBeNull();
    const note = cauMucTieuSoChuaTraLoi(view)!;
    expect(note).toMatch(/côsin/);
    expect(note).toMatch(/không tính hộ/);
    expect(note).not.toMatch(/\d/);
  });

  it.each([
    ["claims the goal satisfied", (c: any) => { c.source_goal_fully_satisfied = true; }],
    ["claims a number shown", (c: any) => { c.numeric_answer_shown = true; }],
    ["claims the number answered", (c: any) => { c.goals[0].numeric_source_goal = "ANSWERED"; }],
    ["unknown function", (c: any) => { c.goals[0].function = "arccos"; }],
    ["no goals", (c: any) => { c.goals = []; }],
  ])("rejects a malformed or self-promoted record: %s", (_, mutate) => {
    const raw = base();
    raw.route_d.source_goal_completion = structuredClone(SGC);
    (mutate as (c: any) => void)(raw.route_d.source_goal_completion);
    expect(docPhanHoiHybrid(raw).ok).toBe(false);
  });

  it("re-validates a stored view: a record promoted to answered afterwards is rejected", () => {
    const raw = base();
    raw.route_d.source_goal_completion = structuredClone(SGC);
    const r = docPhanHoiHybrid(raw);
    if (!r.ok) throw new Error(r.reason);
    const view = structuredClone(hybridViewCua(r.envelope)) as any;
    view.source_goal_completion.numeric_source_goal = "ANSWERED";
    view.source_goal_completion.goals[0].numeric_source_goal = "ANSWERED";
    expect(kiemHybridView(view, raw.envelope.scene3d)).not.toBeNull();
  });
});
