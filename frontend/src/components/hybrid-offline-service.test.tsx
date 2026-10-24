import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { registerAllSimulations } from "../simulations";
import { useAppStore } from "../state/store";
import { docPhanHoiHybrid, hybridViewCua } from "../simulations/domains/geometry/hybrid-preview-adapter";

const rows = JSON.parse(readFileSync(resolve(__dirname,
  "../../../docs/evaluation/geometry/runs/hybrid-primary-b1-b2-offline/results/offline/fixtures.json"), "utf8")).fixtures;

describe("text-first offline service product wrappers", () => {
  it.each(rows as any[])("consumes current backend output $id", (row) => {
    const response = structuredClone(row);
    const result = docPhanHoiHybrid(response);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    registerAllSimulations();
    if (row.route_d.status === "SERVED") {
      expect(result.envelope.scene3d).toEqual(row.envelope.scene3d);
      useAppStore.getState().loadEnvelope(result.envelope as any);
      expect(useAppStore.getState().active).not.toBeNull();
      expect(hybridViewCua(result.envelope)?.adapter_version).toBe("hybrid-simulation-adapter/4");
    } else {
      useAppStore.getState().loadUnsupported(result.envelope as any);
      expect(useAppStore.getState().active).toBeNull();
      expect(result.envelope.scene3d).toBeUndefined();
      expect(result.envelope.reason_code).toBe(row.route_d.refusal.code);
    }
  });

  it("clears a previously served scene when the next product result refuses", () => {
    registerAllSimulations();
    const serve = docPhanHoiHybrid(rows.find((r: any) => r.route_d.status === "SERVED"));
    const refuse = docPhanHoiHybrid(rows.find((r: any) => r.route_d.status === "REFUSED"));
    expect(serve.ok && refuse.ok).toBe(true);
    if (!serve.ok || !refuse.ok) return;
    useAppStore.getState().loadEnvelope(serve.envelope as any);
    expect(useAppStore.getState().active).not.toBeNull();
    useAppStore.getState().loadUnsupported(refuse.envelope as any);
    expect(useAppStore.getState().active).toBeNull();
  });
});
