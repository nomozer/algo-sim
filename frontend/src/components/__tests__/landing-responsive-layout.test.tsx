import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingPreviewV14 } from "../landing/LandingPreviewV14";

describe("AXO Landing V1.4 — Responsive Layout, Unified Visual Polish & Clean Preview", () => {
  it("renders cohesive V1.4 sections cleanly without developer review chrome", () => {
    const html = renderToStaticMarkup(<LandingPreviewV14 />);

    expect(html).toContain('id="view-landing"');
    expect(html).toContain("axo-v14-root");
    expect(html).toContain('id="landing-header"');
    expect(html).toContain('id="landing-hero"');
    expect(html).toContain('id="cach-hoat-dong"');
    expect(html).toContain('id="trai-nghiem"');
    expect(html).toContain('data-ui="product-workbench"');
    expect(html).toContain("thiết diện thật");
    expect(html).toContain('id="btn-landing-sample-chop-thiet-dien-ba-diem"');
    expect(html).toContain('id="btn-landing-demo-reset"');
    expect(html).toContain('id="btn-landing-open-showcase-3d"');
    expect(html).toContain("Mở trong Xưởng 3D");
    expect(html).toContain("S(MENPF) = 6√6");
    expect(html).toContain('id="landing-final-cta"');
    expect(html).toContain("Đưa đề bài của bạn vào không gian 3D.");
    expect(html).toContain('id="btn-landing-final-start"');
    expect(html).toContain('id="btn-landing-hero-library"');
    expect(html).toContain('id="landing-footer"');
    expect(html).toContain('id="btn-landing-footer-library"');

    // Preview V1.4 must expose zero internal banners or prototype switchers
    expect(html).not.toContain('id="landing-v13-review-banner"');
    expect(html).not.toContain("PENDING_OWNER_REVIEW");
    expect(html).not.toContain("Pending Owner Review");
    expect(html).not.toContain("Prototype A");
    expect(html).not.toContain("Prototype B");
  });

  it("defines dedicated illustration-first mobile responsive layout rules without runway traps", () => {
    const css = readFileSync(
      resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );
    expect(css).toContain("@media (max-width: 920px)");
    expect(css).toContain('"visual"\n      "rail"\n      "readout"');
    expect(css).toContain("grid-template-columns: repeat(4, minmax(0, 1fr))");
    expect(css).toContain("@media (max-width: 680px)");
    expect(css).toContain("overflow-x: clip");

    const v14Start = css.indexOf("AXO LANDING V1.4");
    const v14Css = v14Start >= 0 ? css.slice(v14Start) : css;
    expect(v14Css).not.toContain("152vh");
    expect(v14Css).not.toContain("132svh");
  });

  it("maintains strict CSS custom-property & hex hygiene across V1.4 closing & preview TSX", () => {
    for (const rel of [
      "../landing/LandingClosingV14.tsx",
      "../landing/LandingPreviewV14.tsx",
    ]) {
      const src = readFileSync(resolve(__dirname, rel), "utf8");
      expect(src).not.toContain("var(--");
      expect(src).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    }
  });
});
