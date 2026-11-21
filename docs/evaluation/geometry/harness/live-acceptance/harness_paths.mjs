// Shared path/argument contract of the live-acceptance harness (axo-live-acceptance-harness/1).
//
// Every run used to copy its own browser scripts, whose DEFAULT output was the run directory the copy sat in — so
// re-running an old copy overwrote that run's frozen evidence. Here nothing has a default output: `--out-dir` is
// required and must be missing or empty, and inputs (`--manifest`, `--browser-checks`) are read-only paths.
import { existsSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { createRequire } from "node:module";

export const HARNESS_VERSION = "axo-live-acceptance-harness/1";

const HERE = resolve(dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Z]:)/, "$1")));
export const ROOT = resolve(HERE, "../../../../..");
export const FE = join(ROOT, "frontend");

export function loadPlaywright() {
  return createRequire(join(FE, "package.json"))("playwright");
}

/** `{flags, values}` for `--name value` / bare `--flag` arguments. */
export function parseArgs(argv, valueNames) {
  const values = {};
  const flags = new Set();
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) throw new Error(`unexpected argument ${a}`);
    const name = a.slice(2);
    if (valueNames.includes(name)) {
      if (i + 1 >= argv.length) throw new Error(`--${name} needs a value`);
      values[name] = argv[++i];
    } else flags.add(name);
  }
  return { flags, values };
}

/** A fresh output directory: refused when it already holds anything (an earlier run's evidence). */
export function freshOutDir(path) {
  if (!path) throw new Error("--out-dir is required (no default output — see harness_paths.mjs)");
  const out = resolve(path);
  if (existsSync(out) && readdirSync(out).length > 0) {
    throw new Error(`refusing to write into non-empty ${out}: evidence is never overwritten`);
  }
  mkdirSync(join(out, "screenshots"), { recursive: true });
  return out;
}

export function required(values, name) {
  if (!values[name]) throw new Error(`--${name} is required`);
  return resolve(values[name]);
}
