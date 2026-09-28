import assert from "node:assert/strict";
import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { PythonEnvError, repoRootOf, resolvePython, runGate } from "./full-gate.mjs";

const REPO = repoRootOf(new URL("./full-gate.mjs", import.meta.url));
const VENV = join(REPO, "backend", ".venv", "Scripts", "python.exe");
const spaced = () => mkdtempSync(join(tmpdir(), "gate env "));

test("repo root keeps a Windows path with spaces (no %20)", () => {
  const root = repoRootOf("file:///D:/tmp/w09%20repro/frontend/scripts/full-gate.mjs");
  assert.equal(root.replaceAll("\\", "/"), "D:/tmp/w09 repro");
});

test("explicit interpreter is verified and reported", { skip: !existsSync(VENV) }, () => {
  const py = resolvePython({ repo: spaced(), explicit: VENV, env: {} });
  assert.equal(py.source, "explicit");
  assert.equal(py.path, VENV);
  assert.equal(py.version, "3.12");
});

test("missing explicit interpreter fails closed, never falls back to PATH", () => {
  assert.throws(() => resolvePython({ repo: REPO, explicit: join(spaced(), "python.exe"), env: {} }),
    (e) => e instanceof PythonEnvError && e.code === "PYTHON_NOT_FOUND");
});

test("an executable that is not the backend Python is rejected", () => {
  assert.throws(() => resolvePython({ repo: REPO, explicit: process.execPath, env: {} }),
    (e) => e instanceof PythonEnvError && e.code === "PYTHON_INVALID");
});

test("interpreter version mismatch is rejected", { skip: !existsSync(VENV) }, () => {
  assert.throws(() => resolvePython({ repo: REPO, explicit: VENV, env: {}, required: "9.9" }),
    (e) => e instanceof PythonEnvError && e.code === "PYTHON_VERSION_MISMATCH");
});

test("detached tree without a venv reports every candidate it tried", () => {
  assert.throws(() => resolvePython({ repo: spaced(), env: {} }), (e) => {
    assert.equal(e.code, "PYTHON_ENV_UNRESOLVED");
    assert.ok(e.tried.length >= 1 && e.tried.every((t) => t.path && t.reason));
    return true;
  });
});

test("gate propagates the child exit code and spawn errors", () => {
  const cwd = spaced();
  assert.deepEqual(
    (({ ok, status }) => ({ ok, status }))(runGate({ cmd: [process.execPath, ["-e", "process.exit(3)"]], cwd })),
    { ok: false, status: 3 });
  assert.equal(runGate({ cmd: [process.execPath, ["-e", ""]], cwd }).ok, true);
  const missing = runGate({ cmd: [process.execPath, ["-e", ""]], cwd: join(cwd, "nope") });
  assert.equal(missing.ok, false);
  assert.equal(missing.error, "ENOENT");
});
