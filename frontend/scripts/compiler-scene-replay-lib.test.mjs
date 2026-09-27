import assert from "node:assert/strict";
import test from "node:test";

import {
  assessCssReadiness,
  compareClosures,
  eventDeclaredClosure,
  pollUntil,
  solidTopology,
  validateSuiteManifest,
} from "./compiler-scene-replay-lib.mjs";

test("causal closure reports every pair independently", () => {
  const result = compareClosures(["A", "B"], ["A", "C"], ["A", "B", "D"]);
  assert.equal(result.pass, false);
  assert.deepEqual(result.pairs.oracle_vs_event.missing, ["B"]);
  assert.deepEqual(result.pairs.oracle_vs_event.unexpected, ["C"]);
  assert.deepEqual(result.pairs.oracle_vs_browser.unexpected, ["D"]);
  assert.deepEqual(result.pairs.event_vs_browser.missing, ["C"]);
  assert.deepEqual(result.pairs.event_vs_browser.unexpected, ["B", "D"]);
});

test("event closure uses events only and rejects conflicting transport declarations", () => {
  const events = [
    { object: "solid", depends: ["A", "B"] },
    { object: "volume", depends: ["solid"] },
  ];
  assert.deepEqual(eventDeclaredClosure(events, "volume"), ["A", "B", "solid", "volume"]);
  assert.throws(() => eventDeclaredClosure([
    { object: "T", depends: ["solid", "plane"] },
    { object: "T", depends: ["other", "plane"] },
  ], "T"), /EVENT_DEPENDENCY_CONFLICT:T/);
});

test("topology counts unique undirected edges", () => {
  const result = solidTopology({ objects: [{
    type: "solid", vertex_ids: ["A", "B", "C", "S"],
    faces: [[0, 1, 2], [0, 3, 1], [1, 3, 2], [2, 3, 0]],
  }] });
  assert.deepEqual(result, { vertices: 4, edges: 6, faces: 4, euler: 2 });
});

test("CSS readiness is driven by computed sentinel styles, not stylesheet rules", () => {
  const baseline = {
    div: { display: "inline", fontFamily: "Times", color: "rgb(0, 0, 0)" },
    ul: { position: "static", fontFamily: "Times" },
    span: { color: "rgb(0, 0, 0)" },
  };
  const actual = {
    scene: { display: "flex", width: 900 },
    box: { position: "relative", width: 900, height: 500 },
    canvas: { width: 898, height: 498 },
    controls: { display: "flex", fontFamily: "Inter" },
    controlButton: { color: "rgb(0, 0, 0)" },
    controlText: { color: "rgb(97, 93, 89)" },
    readout: { position: "relative", fontFamily: "Inter" },
    readoutText: { color: "rgb(97, 93, 89)" },
  };
  assert.equal(assessCssReadiness(actual, baseline, 900, 900).pass, true);
  assert.equal(assessCssReadiness(actual, baseline, 901.5, 900).checks.no_document_overflow, false);
});

test("manifest requires frozen independent oracle source", () => {
  assert.throws(() => validateSuiteManifest({
    schema_version: "generic-tier-a-suite/1",
    viewports: [{ width: 1 }, { width: 2 }],
    scenarios: [{ id: "x", positive_fixture: "p", negative_fixture: "n",
      causal_target_id: "v", oracle_expected_closure: ["v"],
      topology: { vertices: 1, edges: 0, faces: 1, euler: 2 } }],
  }), /INVALID_SUITE_MANIFEST/);
});

test("semantic polling returns on state change without a fixed readiness sleep", async () => {
  let tick = 0;
  let clock = 0;
  const result = await pollUntil(
    async () => ++tick,
    (value) => value === 3,
    { now: () => clock, pause: async (ms) => { clock += ms; } },
  );
  assert.equal(result, 3);
});
