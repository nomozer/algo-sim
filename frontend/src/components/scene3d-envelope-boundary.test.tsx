import { readFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { analyzeViaServer } from "../llm/client";
import { registerAllSimulations } from "../simulations";
import { getSimulation } from "../simulations/registry";
import { useAppStore } from "../state/store";
import { __resetHistoryForTest, historyStore } from "../state/history";
import { hopLeScene3D } from "../simulations/domains/geometry/scene3d-model";
import { ChartMetricError, veKhongGian } from "../simulations/domains/geometry/scene3d-chart";
import type { SimulationEnvelope } from "../simulations/types";

const fixture = () => JSON.parse(readFileSync(join(__dirname,
  "../../../docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2/served-H01_CUBE.json"), "utf8")).response.envelope;
const store = () => useAppStore.getState();
const diagonal = (x: string) => [[x, "0", "0"], ["0", "1", "0"], ["0", "0", "1"]];
const BAD: [string, unknown][] = [
  ["malformed shape", [["1"]]],
  ["malformed rational", diagonal("1/0")],
  ["non-SPD", diagonal("-1")],
  ["singular", diagonal("0")],
  ["asymmetric", [["1", "1", "0"], ["0", "1", "0"], ["0", "0", "1"]]],
  ["overflow", diagonal("9".repeat(400))],
  ["finite SPD but display overflow", diagonal("1" + "0".repeat(40))],
  ["non-finite rational", diagonal(`${"9".repeat(400)}/${"9".repeat(400)}`)],
];

beforeEach(() => {
  registerAllSimulations();
  __resetHistoryForTest();
  store().reset();
});
afterEach(() => vi.restoreAllMocks());

describe("F2 acceptance boundary, not renderer fallback", () => {
  it("direct chart conversion fails closed on finite SPD display overflow", () => {
    const scene = fixture().scene3d;
    scene.chart_metric = diagonal("1" + "0".repeat(40));
    expect(() => veKhongGian(scene)).toThrow(ChartMetricError);
  });
  it.each(BAD)("direct load rejects %s before active or history", (_name, metric) => {
    const env = fixture();
    env.scene3d.chart_metric = metric;
    expect(() => store().loadEnvelope(env)).not.toThrow();
    expect(store().active).toBeNull();
    expect(store().analysisError).toBeTruthy();
    expect(historyStore.list()).toEqual([]);
  });

  it("API status ok is diagnostic input, not acceptance; malformed scene cannot bypass via 2D", async () => {
    const env = fixture();
    env.scene3d = { chart_metric: diagonal("-1") };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(env)));
    const response = await analyzeViaServer({ type: "text", content: "offline boundary probe" });
    expect(response.status).toBe("ok");
    store().loadEnvelope(response as SimulationEnvelope);
    expect(store().active).toBeNull();
    expect(store().analysisError).toBeTruthy();
    expect(historyStore.list()).toEqual([]);
  });

  it("rejecting a new scene clears stale active, without deleting the previous history", () => {
    store().loadEnvelope(fixture());
    const before = historyStore.list();
    store().setPlaying(true);
    const bad = fixture();
    bad.scene3d.chart_metric = diagonal("-1");
    store().loadEnvelope(bad);
    expect(store().active).toBeNull();
    expect(store().activeHistoryId).toBeNull();
    expect(store().playing).toBe(false);
    expect(historyStore.list()).toEqual(before);
  });

  it("revalidates raw old history with invalid metric; does not restore cursor into previous active", () => {
    store().loadEnvelope(fixture());
    const before = historyStore.list();
    const env = fixture();
    env.scene3d.chart_metric = diagonal("-1");
    const old = { ...before[0], id: "old-invalid", envelope: env, lastCursor: 999, visualMode: "3d" as const };
    vi.spyOn(historyStore, "list").mockReturnValue([old, ...before]);
    const touch = vi.spyOn(historyStore, "touch");
    const record = vi.spyOn(historyStore, "record");
    store().reopenFromHistory(old.id);
    expect(store().active).toBeNull();
    expect(store().analysisError).toBeTruthy();
    expect(store().view).toBe("home");
    expect(touch).not.toHaveBeenCalled();
    expect(record).not.toHaveBeenCalled();
    expect(historyStore.list()).toEqual([old, ...before]);
  });

  it("legacy 2D is independently config-validated, retained, and makes no Scene3D claim", () => {
    const env = fixture();
    delete env.scene3d;
    store().loadEnvelope(env);
    expect(store().active).not.toBeNull();
    const id = store().activeHistoryId!;
    store().reset();
    store().reopenFromHistory(id);
    expect(store().active).not.toBeNull();
    expect(hopLeScene3D((store().active!.envelope as any).scene3d)).toBe(false);
    const active = store().active!;
    const Stage = getSimulation(active.moduleId)!.Workspace;
    const html = renderToString(<Stage config={active.config} state={active.state} busy={false} dispatch={store().dispatch} />);
    expect(html).toContain("semantic");
    expect(html).not.toContain("geo3d-canvas");
    expect(html).not.toContain("Trên hình đã dựng");
    expect(historyStore.list()).toHaveLength(1);
    const invalid = { ...env, config: { frames: [] } };
    store().loadEnvelope(invalid);
    expect(store().active).toBeNull();
    expect(store().analysisError).toBeTruthy();
    expect(historyStore.list()).toHaveLength(1);
  });

  it("null scene keeps legacy 2D, but cannot bypass config validation", () => {
    const env = { ...fixture(), scene3d: null };
    store().loadEnvelope(env);
    expect(store().active).not.toBeNull();
    store().loadEnvelope({ ...env, config: {} });
    expect(store().active).toBeNull();
    expect(store().analysisError).toBeTruthy();
    expect(historyStore.list()).toHaveLength(1);
  });
});
