/**
 * Migration Stage 2 (run `scene3d-to-hybrid-v2-replacement`): `/api/analyze` may answer with an Adapter /4 response when
 * the server enables the local Hybrid V2 route. `analyzeViaServer` reads it through the /4 reader the product already
 * locks (`docPhanHoiHybrid`); the default route's envelopes pass through untouched.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { analyzeViaServer, docPhanHoiPhanTich } from "../llm/client";
import { registerAllSimulations } from "../simulations";
import { hybridViewCua } from "../simulations/domains/geometry/hybrid-preview-adapter";
import { useAppStore } from "../state/store";

const rows = JSON.parse(readFileSync(resolve(__dirname,
  "../../../docs/evaluation/geometry/runs/hybrid-primary-b1-b2-offline/results/offline/fixtures.json"), "utf8")).fixtures;
const served = () => structuredClone(rows.find((r: any) => r.route_d.status === "SERVED"));
const refused = () => structuredClone(rows.find((r: any) => r.route_d.status === "REFUSED"));

afterEach(() => vi.restoreAllMocks());

describe("analyzeViaServer reads a Hybrid V2 /4 response", () => {
  it("served ⇒ envelope with the checked hybrid view, loadable by the store", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(served())));
    const env = await analyzeViaServer({ type: "text", content: "probe" });
    expect(env.status).toBe("ok");
    expect(hybridViewCua(env)?.adapter_version).toBe("hybrid-simulation-adapter/4");
    registerAllSimulations();
    useAppStore.getState().loadEnvelope(env as any);
    expect(useAppStore.getState().active).not.toBeNull();
  });

  it("refused ⇒ the refusal envelope as is, with no scene", () => {
    const r = refused();
    const env = docPhanHoiPhanTich(r) as any;
    expect(env.status).toBe("unsupported");
    expect(env.reason_code).toBe(r.route_d.refusal.code);
    expect(env.scene3d).toBeUndefined();
  });

  it.each([
    ["identity", (x: any) => { x.route_d.adapter_version = "hybrid-simulation-adapter/3"; }],
    ["backend-injected view", (x: any) => { x.envelope.hybrid_preview = { adapter_version: "forged" }; }],
    ["missing scene", (x: any) => { delete x.envelope.scene3d; }],
  ])("a /4 response that fails the reader (%s) is a SYSTEM refusal, never a scene", (_n, tamper) => {
    const x = served();
    tamper(x);
    const env = docPhanHoiPhanTich(x) as any;
    expect(env.status).toBe("unsupported");
    expect(env.failure_category).toBe("verification_gap");
    expect(env.scene3d).toBeUndefined();
  });

  it("a default-route envelope passes through byte-for-byte", () => {
    const def = { status: "ok", simulation_id: "x", scene3d: { objects: [], events: [] } };
    expect(docPhanHoiPhanTich(def)).toBe(def);
  });
});
