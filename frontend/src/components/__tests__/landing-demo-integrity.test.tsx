import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingHeader } from "../landing/LandingHeader";
import { LandingInteractiveDemo } from "../landing/LandingInteractiveDemo";
import { LandingStorytelling } from "../landing/LandingStorytelling";
import {
  LANDING_CUBE_SAMPLE,
  LANDING_PYRAMID_SAMPLE,
} from "../landing/landing-geometry-data";

describe("AXO Landing Page V1.1 — Mathematical Demo & Navigation Integrity", () => {
  it("exposes steady-weight header pill navigation and accessible mobile toggle controls", () => {
    const html = renderToString(<LandingHeader />);
    expect(html).toContain('id="landing-header"');
    expect(html).toContain('id="landing-nav"');
    expect(html).toContain('id="nav-landing-landing-hero"');
    expect(html).toContain('id="nav-landing-cach-hoat-dong"');
    expect(html).toContain('id="nav-landing-trai-nghiem"');
    expect(html).toContain('id="btn-landing-mobile-menu"');
    expect(html).toContain('aria-expanded="false"');
    // Mobile backdrop/drawer are conditionally mounted when open so hero content is unobstructed on SSR
    expect(html).not.toContain('id="landing-mobile-drawer"');
  });

  it("keeps Storytelling distinct from Hero artwork and uses exact S.ABCD geometry", () => {
    const html = renderToString(<LandingStorytelling />);
    expect(html).toContain("axo-sp-story-runway");
    expect(html).toContain("axo-sp-story-sticky");
    expect(html).toContain("axo-sp-story-math-disclosure");
    expect(html).toContain("S.ABCD");
    for (const m of LANDING_PYRAMID_SAMPLE.milestones) {
      expect(html).toContain(m.tag.replace(/&/g, "&amp;"));
    }

    // Plane (MNP) must remain coplanar inside the normalized coordinates across MENPF
    const M = LANDING_PYRAMID_SAMPLE.pointMap["M"].pos;
    const N = LANDING_PYRAMID_SAMPLE.pointMap["N"].pos;
    const P = LANDING_PYRAMID_SAMPLE.pointMap["P"].pos;
    const ux = N[0] - M[0];
    const uy = N[1] - M[1];
    const uz = N[2] - M[2];
    const vx = P[0] - M[0];
    const vy = P[1] - M[1];
    const vz = P[2] - M[2];
    const nx = uy * vz - uz * vy;
    const ny = uz * vx - ux * vz;
    const nz = ux * vy - uy * vx;
    for (const id of LANDING_PYRAMID_SAMPLE.sectionLoop) {
      const Q = LANDING_PYRAMID_SAMPLE.pointMap[id].pos;
      const coplanarity = (Q[0] - M[0]) * nx + (Q[1] - M[1]) * ny + (Q[2] - M[2]) * nz;
      expect(coplanarity).toBeCloseTo(0, 4);
    }
  });

  it("keeps Interactive Demo focused with workbench controls and both sample slugs", () => {
    const html = renderToString(<LandingInteractiveDemo />);
    expect(html).toContain('id="landing-product-showcase"');
    expect(html).toContain('id="btn-landing-sample-chop-thiet-dien-ba-diem"');
    expect(html).toContain('id="btn-landing-sample-lap-phuong-thiet-dien-bat-ky"');
    expect(html).toContain('id="btn-landing-demo-reset"');
    expect(html).toContain('id="btn-landing-demo-prev"');
    expect(html).toContain('id="btn-landing-demo-next"');
    expect(html).toContain('id="btn-landing-open-showcase-3d"');
    expect(html).toContain("axo-sp-demo-problem-disclosure");

    // Regular hexagon points in cube sample lie strictly on domain plane -x + y + z = 2
    for (const id of LANDING_CUBE_SAMPLE.sectionLoop) {
      const [x, y, z] = LANDING_CUBE_SAMPLE.pointMap[id].domainXyz;
      expect(-x + y + z).toBeCloseTo(2, 4);
    }
  });
});
