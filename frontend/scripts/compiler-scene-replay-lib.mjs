import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export const sortedUnique = (values) => [...new Set(values ?? [])].sort();

export function setDiff(expected, actual) {
  const left = sortedUnique(expected);
  const right = sortedUnique(actual);
  return {
    missing: left.filter((id) => !right.includes(id)),
    unexpected: right.filter((id) => !left.includes(id)),
  };
}

function comparePair(leftName, left, rightName, right) {
  const diff = setDiff(left, right);
  return {
    left: leftName,
    right: rightName,
    missing: diff.missing,
    unexpected: diff.unexpected,
    pass: diff.missing.length === 0 && diff.unexpected.length === 0,
  };
}

export function compareClosures(oracle, declared, observed) {
  const sets = {
    oracle_expected_closure: sortedUnique(oracle),
    event_declared_closure: sortedUnique(declared),
    browser_observed_closure: sortedUnique(observed),
  };
  const pairs = {
    oracle_vs_event: comparePair(
      "oracle_expected_closure", sets.oracle_expected_closure,
      "event_declared_closure", sets.event_declared_closure,
    ),
    oracle_vs_browser: comparePair(
      "oracle_expected_closure", sets.oracle_expected_closure,
      "browser_observed_closure", sets.browser_observed_closure,
    ),
    event_vs_browser: comparePair(
      "event_declared_closure", sets.event_declared_closure,
      "browser_observed_closure", sets.browser_observed_closure,
    ),
  };
  return { ...sets, pairs, pass: Object.values(pairs).every((p) => p.pass) };
}

export function eventDeclaredClosure(events, targetId) {
  const dependencies = new Map();
  for (const event of events ?? []) {
    const objectIds = Array.isArray(event.objects)
      ? event.objects
      : event.object ? [event.object] : [];
    for (const objectId of objectIds) {
      const next = sortedUnique(event.depends);
      if (dependencies.has(objectId)) {
        const before = dependencies.get(objectId);
        if (JSON.stringify(before) !== JSON.stringify(next)) {
          throw new Error(`EVENT_DEPENDENCY_CONFLICT:${objectId}`);
        }
      } else {
        dependencies.set(objectId, next);
      }
    }
  }
  const seen = new Set();
  const queue = [targetId];
  while (queue.length > 0) {
    const id = queue.shift();
    if (!id || seen.has(id)) continue;
    seen.add(id);
    queue.push(...(dependencies.get(id) ?? []));
  }
  return sortedUnique(seen);
}

export function solidTopology(scene) {
  const solid = (scene?.objects ?? []).find((object) => object.type === "solid");
  if (!solid) return { vertices: 0, edges: 0, faces: 0, euler: null };
  const edges = new Set();
  for (const face of solid.faces ?? []) {
    for (let index = 0; index < face.length; index += 1) {
      const a = face[index];
      const b = face[(index + 1) % face.length];
      edges.add(a < b ? `${a}:${b}` : `${b}:${a}`);
    }
  }
  const vertices = (solid.vertex_ids ?? solid.vertices ?? []).length;
  const faces = (solid.faces ?? []).length;
  return { vertices, edges: edges.size, faces, euler: vertices - edges.size + faces };
}

export function assessCssReadiness(actual, baseline, scrollWidth, viewportWidth) {
  const checks = {
    scene_layout: Boolean(actual.scene)
      && actual.scene.display === "flex" && actual.scene.width > 100,
    canvas_layout: Boolean(actual.box)
      && ["relative", "absolute"].includes(actual.box.position),
    canvas_size: Boolean(actual.canvas)
      && actual.canvas.width > 100 && actual.canvas.height > 100
      && actual.canvas.width <= actual.box.width + 2
      && actual.canvas.height <= actual.box.height + 2,
    controls_styled: Boolean(actual.controls && actual.controlButton && actual.controlText)
      && actual.controls.display !== baseline.div.display
      && actual.controls.fontFamily !== baseline.div.fontFamily
      && actual.controlText.color !== baseline.span.color,
    readout_styled: Boolean(actual.readout && actual.readoutText)
      && actual.readout.position !== baseline.ul.position
      && actual.readout.fontFamily !== baseline.ul.fontFamily
      && actual.readoutText.color !== baseline.span.color,
    no_document_overflow: scrollWidth <= viewportWidth + 1,
  };
  return { checks, pass: Object.values(checks).every(Boolean) };
}

export function expectedVisibleIds(scene, step) {
  const visible = new Set(scene?.free_objects ?? []);
  for (const event of scene?.events ?? []) {
    if ((event.step_index ?? 0) > step) continue;
    if (Array.isArray(event.objects)) event.objects.forEach((id) => visible.add(id));
    else if (event.object) visible.add(event.object);
  }
  return sortedUnique([...visible].filter((id) =>
    (scene?.objects ?? []).some((object) => object.id === id)));
}

export function sha256File(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function validateSuiteManifest(manifest, repoRoot) {
  const errors = [];
  if (manifest?.schema_version !== "generic-tier-a-suite/1") {
    errors.push("schema_version");
  }
  if (!Array.isArray(manifest?.viewports) || manifest.viewports.length !== 2) {
    errors.push("viewports");
  }
  if (!Array.isArray(manifest?.scenarios) || manifest.scenarios.length !== 4) {
    errors.push("scenarios");
  }
  const names = new Set();
  for (const scenario of manifest?.scenarios ?? []) {
    if (!scenario.id || names.has(scenario.id)) errors.push(`scenario_id:${scenario.id}`);
    names.add(scenario.id);
    if (!scenario.positive_fixture || !scenario.negative_fixture) {
      errors.push(`fixtures:${scenario.id}`);
    }
    if (!scenario.causal_target_id
        || !scenario.oracle_expected_closure?.includes(scenario.causal_target_id)) {
      errors.push(`oracle_target:${scenario.id}`);
    }
    if (!scenario.oracle_source?.path || !scenario.oracle_source?.sha256) {
      errors.push(`oracle_source:${scenario.id}`);
    } else if (repoRoot) {
      const path = resolve(repoRoot, scenario.oracle_source.path);
      if (sha256File(path) !== scenario.oracle_source.sha256) {
        errors.push(`oracle_source_hash:${scenario.id}`);
      }
    }
    for (const key of ["vertices", "edges", "faces", "euler"]) {
      if (typeof scenario.topology?.[key] !== "number") errors.push(`topology:${scenario.id}:${key}`);
    }
  }
  if (errors.length > 0) throw new Error(`INVALID_SUITE_MANIFEST:${errors.join(",")}`);
  return true;
}

export async function pollUntil(read, predicate, {
  timeoutMs = 25_000,
  intervalMs = 100,
  now = () => Date.now(),
  pause = (ms) => new Promise((resolvePause) => setTimeout(resolvePause, ms)),
} = {}) {
  const deadline = now() + timeoutMs;
  let last;
  do {
    last = await read();
    if (predicate(last)) return last;
    await pause(intervalMs);
  } while (now() <= deadline);
  throw new Error(`POLL_TIMEOUT:${JSON.stringify(last)}`);
}
