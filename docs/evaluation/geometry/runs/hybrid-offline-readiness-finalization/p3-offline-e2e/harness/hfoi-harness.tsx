// HFOI P3 offline E2E harness — the PRODUCT shell (same as frontend/src/main.tsx: registerAllSimulations + AppRoot),
// plus ONE injected segment: transport of a Hybrid preview response. No product caller exists (the preview endpoint is
// operator-only and refuses browsers), so the harness fetches the response JSON from its own server (fresh output of the
// real endpoint) and passes it through the REAL adapter (docPhanHoiHybrid) and the REAL store. Nothing else is mocked here.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AppRoot } from "@fe/App";
import { registerAllSimulations } from "@fe/simulations";
import { useAppStore } from "@fe/state/store";
import { docPhanHoiHybrid, hybridViewCua } from "@fe/simulations/domains/geometry/hybrid-preview-adapter";
import { geometryTimeline, type Scene3D } from "@fe/simulations/domains/geometry/scene3d-model";
import "@fe/styles/global.css";

registerAllSimulations();

(window as unknown as { __HFOI__: unknown }).__HFOI__ = {
  dapAn() { return hybridViewCua(useAppStore.getState().active?.envelope)?.answers ?? []; },
  /** Injected transport: response JSON → adapter → store. Returns what the store accepted. */
  async nap(url: string) {
    const raw = await (await fetch(url)).json();
    const r = docPhanHoiHybrid(raw);
    if (!r.ok) return { adapter: "REJECTED", reason: r.reason, ...trangThai() };
    const env = r.envelope as { status?: string };
    if (env.status === "ok") useAppStore.getState().loadEnvelope(env as never);
    else useAppStore.getState().loadUnsupported(env as never);
    return { adapter: "ACCEPTED", ...trangThai() };
  },
  /** The product's own definition of a UI step (group of events, anchor = last event) — the reference for which
   *  event index each "Bước k/N" represents; chip visibility (hybridTaiBuoc) is checked against it, not derived from it. */
  buoc(scene: Scene3D) { return geometryTimeline(scene).map((g) => ({ start: g.start, end: g.end, anchor: g.anchor })); },
  /** Product LLM_ONLY path stand-in for legacy envelopes: straight to the store (no adapter, as /api/analyze). */
  napEnvelope(env: unknown) {
    useAppStore.getState().loadEnvelope(env as never);
    return trangThai();
  },
};

function trangThai() {
  const s = useAppStore.getState();
  return { view: s.view, active: !!s.active, unsupported: !!s.unsupported, analysisError: s.analysisError ?? null };
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppRoot />
  </StrictMode>,
);
