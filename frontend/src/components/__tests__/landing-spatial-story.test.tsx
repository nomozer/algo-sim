import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingView } from "../LandingView";
import {
  LANDING_CUBE_SAMPLE,
  LANDING_PRISM_STORY_SPEC,
  LANDING_PYRAMID_SAMPLE,
  enterAxoWorkspace,
  landingSampleById,
  openLibraryFromLanding,
  openSampleInWorkspace,
} from "../landing/landing-geometry-data";
import { registerAllSimulations } from "../../simulations";
import { useAppStore } from "../../state/store";

describe("AXO Landing Page V1.1 — Spatial Story & Architecture", () => {
  it("renders Hero with frameless spatial sculpture, 2 focused CTAs, and clean editorial hierarchy", () => {
    const html = renderToString(<LandingView />);

    expect(html).toContain('id="view-landing"');
    expect(html).toContain("Hình học không gian, dễ hình dung hơn.");
    expect(html).toContain('id="landing-hero-sculpture"');
    expect(html).toContain('id="btn-landing-hero-start"');
    expect(html).toContain('id="btn-landing-hero-story"');

    // Hero must NOT show a third button, stats strip, or proof vertex tags inside the Hero section
    const heroStart = html.indexOf('id="landing-hero"');
    const heroEnd = html.indexOf('id="cach-hoat-dong"');
    const heroSlice = html.slice(heroStart, heroEnd);
    expect(heroSlice).not.toContain('id="btn-landing-hero-library"');
    expect(heroSlice).not.toContain("axo-sp-hero-meta");
    expect(heroSlice).not.toContain("axo-sp-point-tag");

    // Library CTA remains accessible in the Final CTA closing band (preserving workspace entry contract)
    expect(html).toContain('id="btn-landing-hero-library"');
    expect(html).toContain('id="btn-landing-final-start"');
    expect(html).toContain("axo-sp-closing-sculpture");
  });

  it("renders continuous 4-stage Storytelling with collapsed math disclosure and interactive Demo showcase", () => {
    const html = renderToString(<LandingView />);

    expect(html).toContain('id="cach-hoat-dong"');
    expect(html).toContain("Một bài toán, mở ra từng lớp không gian.");
    expect(html).toContain('id="btn-landing-story-step-0"');
    expect(html).toContain('id="btn-landing-story-step-3"');
    expect(html).toContain("Chi tiết tọa độ &amp; kiểm chứng hình học");
    expect(html).toContain('id="landing-storytelling-scene"');

    expect(html).toContain('id="trai-nghiem"');
    expect(html).toContain('id="landing-product-showcase"');
    expect(html).toContain('id="landing-demo-scene"');
    expect(html).toContain('id="btn-landing-sample-chop-thiet-dien-ba-diem"');
    expect(html).toContain('id="btn-landing-sample-lap-phuong-thiet-dien-bat-ky"');
    expect(html).toContain("Xem đề bài gốc");
    expect(html).toContain('id="btn-landing-open-showcase-3d"');
  });

  it("keeps verified geometric invariants across Landing normalized samples", () => {
    expect(LANDING_PYRAMID_SAMPLE.milestones).toHaveLength(4);
    expect(LANDING_CUBE_SAMPLE.milestones).toHaveLength(4);

    // Pyramid S.ABCD midpoints M=(S+A)/2, N=(B+C)/2, P=(C+D)/2 and plane x+y+2z=6 on section MENPF
    const S = LANDING_PYRAMID_SAMPLE.pointMap["S"].domainXyz;
    const A = LANDING_PYRAMID_SAMPLE.pointMap["A"].domainXyz;
    const B = LANDING_PYRAMID_SAMPLE.pointMap["B"].domainXyz;
    const C = LANDING_PYRAMID_SAMPLE.pointMap["C"].domainXyz;
    const D = LANDING_PYRAMID_SAMPLE.pointMap["D"].domainXyz;
    const M = LANDING_PYRAMID_SAMPLE.pointMap["M"].domainXyz;
    const N = LANDING_PYRAMID_SAMPLE.pointMap["N"].domainXyz;
    const P = LANDING_PYRAMID_SAMPLE.pointMap["P"].domainXyz;
    for (let k = 0; k < 3; k++) {
      expect(M[k]).toBeCloseTo((S[k] + A[k]) / 2, 4);
      expect(N[k]).toBeCloseTo((B[k] + C[k]) / 2, 4);
      expect(P[k]).toBeCloseTo((C[k] + D[k]) / 2, 4);
    }
    for (const id of LANDING_PYRAMID_SAMPLE.sectionLoop) {
      const [x, y, z] = LANDING_PYRAMID_SAMPLE.pointMap[id].domainXyz;
      expect(x + y + 2 * z).toBeCloseTo(6, 4);
    }

    // Cube section MNEPFQ must form an equilateral planar hexagon
    const loop = LANDING_CUBE_SAMPLE.sectionLoop.map(
      (id) => LANDING_CUBE_SAMPLE.pointMap[id].pos,
    );
    expect(loop).toHaveLength(6);
    const edgeLengths = loop.map((p, idx) => {
      const q = loop[(idx + 1) % loop.length];
      return Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]);
    });
    for (const len of edgeLengths) {
      expect(len).toBeCloseTo(edgeLengths[0], 4);
    }

    // Prism ABC.A'B'C' story spec: M=(A+B)/2, N=(A+C)/2, P=(C+C')/2, Q=(B+B')/2 -> isosceles trapezoid MNPQ
    expect(LANDING_PRISM_STORY_SPEC.milestones).toHaveLength(4);
    const pMap = LANDING_PRISM_STORY_SPEC.pointMap;
    const dist3 = (u: readonly number[], v: readonly number[]) =>
      Math.hypot(u[0] - v[0], u[1] - v[1], u[2] - v[2]);
    expect(dist3(pMap["M"].domainXyz, pMap["N"].domainXyz)).toBeCloseTo(2, 4);
    expect(dist3(pMap["P"].domainXyz, pMap["Q"].domainXyz)).toBeCloseTo(4, 4);
    expect(dist3(pMap["M"].domainXyz, pMap["Q"].domainXyz)).toBeCloseTo(2 * Math.SQRT2, 4);
    expect(dist3(pMap["N"].domainXyz, pMap["P"].domainXyz)).toBeCloseTo(2 * Math.SQRT2, 4);

    // Coplanarity of M, N, P, Q in normalized 3D coordinates
    const pm = pMap["M"].pos;
    const pn = pMap["N"].pos;
    const pp = pMap["P"].pos;
    const pq = pMap["Q"].pos;
    const u1 = [pn[0] - pm[0], pn[1] - pm[1], pn[2] - pm[2]];
    const u2 = [pp[0] - pm[0], pp[1] - pm[1], pp[2] - pm[2]];
    const nVec = [
      u1[1] * u2[2] - u1[2] * u2[1],
      u1[2] * u2[0] - u1[0] * u2[2],
      u1[0] * u2[1] - u1[1] * u2[0],
    ];
    expect(
      (pq[0] - pm[0]) * nVec[0] + (pq[1] - pm[1]) * nVec[1] + (pq[2] - pm[2]) * nVec[2],
    ).toBeCloseTo(0, 4);

    expect(landingSampleById("unknown-id").id).toBe(LANDING_PYRAMID_SAMPLE.id);
  });

  it("navigates cleanly from Landing CTA into Workspace, Library, and Sample Studio", () => {
    registerAllSimulations();

    useAppStore.getState().setView("landing");
    enterAxoWorkspace();
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().guestEnteredApp).toBe(true);

    useAppStore.getState().setView("landing");
    openLibraryFromLanding();
    expect(useAppStore.getState().view).toBe("library");

    useAppStore.getState().setView("landing");
    openSampleInWorkspace("lap-phuong-thiet-dien-bat-ky");
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().activeSampleId).toBe("lap-phuong-thiet-dien-bat-ky");
  });

  it("keeps Landing styles isolated in landing.css without CSS variable leakage into TSX", () => {
    const landingDir = path.resolve(__dirname, "../landing");
    const files = fs.readdirSync(landingDir).filter((f) => f.endsWith(".tsx"));
    for (const file of files) {
      const src = fs.readFileSync(path.join(landingDir, file), "utf8");
      expect(src).not.toContain("var(--");
      expect(src).not.toMatch(/import\s+["']\.\/.*\.css["']/);
    }
  });
});
