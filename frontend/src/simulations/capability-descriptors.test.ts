import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { beforeAll, describe, expect, it } from "vitest";
import descriptorsJson from "./capability-descriptors.json";
import { getSimulation, listSimulations, registerAllSimulations } from "./index";
import { publicCatalog } from "../data/offline-catalog";

/**
 * M14 §C4 — CROSS-LOCK descriptor backend ↔ registry frontend (TEST-ONLY).
 *
 * capability-descriptors.json là bản SINH từ CATALOG+FAMILY_SELECTORS phía
 * backend. Test này khóa nó vào THỰC TẾ frontend: mọi runtime target là module
 * đã đăng ký, mọi variant resolve về module thật, selector token KHÔNG phải
 * module. Đồng thời cấm mọi module PRODUCTION import file này (điểm 6) —
 * renderer availability đã dẫn xuất từ hợp đồng module, FE không cần descriptor.
 */

interface Membership {
  family_id: string;
  result_authority: string;
  variant_id: string | null;
  family_spec_version: string | null;
  mechanism_id: string | null;
}
interface Target {
  domain: string;
  executor_id: string;
  reachability: string[];
  curriculum_anchor: string;
  known_gaps: string[];
  family_memberships: Membership[];
}
interface Selector {
  selector_token: string;
  family_spec_version: string;
  owned_mechanisms: string[];
  variants: { variant_id: string; concrete_simulation_id: string; mechanism_id: string }[];
}
const descriptors = descriptorsJson as unknown as {
  runtime_targets: Record<string, Target>;
  family_selectors: Record<string, Selector>;
  llm_choices: string[];
};

beforeAll(() => registerAllSimulations());

describe("M14 §C4 — descriptor ↔ registry cross-lock", () => {
  it("mọi runtime target là module FE đã đăng ký (song ánh 1:1, vẫn 14)", () => {
    const ids = Object.keys(descriptors.runtime_targets);
    expect(ids.length).toBe(14);
    for (const id of ids) expect(getSimulation(id), `thiếu module ${id}`).toBeDefined();
    // song ánh: số module đăng ký == số runtime target
    expect(listSimulations().length).toBe(ids.length);
  });

  it("executor_id trỏ đúng module thật", () => {
    for (const [id, t] of Object.entries(descriptors.runtime_targets)) {
      expect(t.executor_id).toBe(id);
      expect(getSimulation(t.executor_id)).toBeDefined();
    }
  });

  it("mọi variant của selector resolve về một module concrete có thật", () => {
    for (const sel of Object.values(descriptors.family_selectors)) {
      for (const v of sel.variants) {
        expect(getSimulation(v.concrete_simulation_id), v.concrete_simulation_id).toBeDefined();
        expect(sel.owned_mechanisms).toContain(v.mechanism_id);
      }
    }
  });

  it("selector_token KHÔNG phải module FE (token ảo, không bao giờ là envelope id)", () => {
    for (const sel of Object.values(descriptors.family_selectors)) {
      expect(getSimulation(sel.selector_token)).toBeUndefined();
    }
  });

  it("reachability library_discoverable ⟹ có mẫu trong publicCatalog", () => {
    const publicIds = new Set(publicCatalog().map((e) => e.simId));
    for (const [id, t] of Object.entries(descriptors.runtime_targets)) {
      if (t.reachability.includes("library_discoverable")) {
        expect(publicIds.has(id), `${id} khai library_discoverable nhưng không có mẫu công khai`).toBe(true);
      }
    }
    // algorithm.scan KHÔNG library_discoverable (discovery A) — chốt đúng thực tế
    expect(descriptors.runtime_targets["algorithm.scan"].reachability).not.toContain(
      "library_discoverable",
    );
  });
});

describe("M14 điểm 6 — descriptor JSON là artifact test-only, KHÔNG dependency production", () => {
  const SRC = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
  function walk(dir: string, out: string[] = []): string[] {
    for (const name of readdirSync(dir)) {
      const full = join(dir, name);
      if (statSync(full).isDirectory()) walk(full, out);
      else if (/\.tsx?$/.test(name) && !/\.test\.tsx?$/.test(name)) out.push(full);
    }
    return out;
  }

  it("không module runtime FE nào import capability-descriptors.json", () => {
    const offenders = walk(SRC)
      .filter((f) => /capability-descriptors\.json/.test(readFileSync(f, "utf-8")))
      .map((f) => f.replace(SRC, ""));
    expect(offenders, `import bị cấm ở: ${offenders.join(", ")}`).toEqual([]);
  });
});
