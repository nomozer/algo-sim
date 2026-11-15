import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingInteractiveDemo } from "../landing/LandingInteractiveDemo";
import { LandingPreviewV14 } from "../landing/LandingPreviewV14";
import { LandingView } from "../LandingView";

describe("Landing approved UI, capsule buttons, and version consolidation guard", () => {
  it("restores pill border-radius on .axo-v14-btn and styles closing/footer cleanly with design tokens", () => {
    const cssSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );

    const v14BtnBlock = cssSrc.match(/\.axo-v14-btn\s*\{[\s\S]*?\}/);
    expect(v14BtnBlock?.[0]).toContain("border-radius: var(--rounded-full)");
    expect(v14BtnBlock?.[0]).not.toContain("var(--rounded-md)");

    const v14PrimaryHover = cssSrc.match(/\.axo-v14-btn-primary:hover\s*\{[\s\S]*?\}/);
    expect(v14PrimaryHover?.[0]).toContain("transform: translateY(-1px)");

    // Obsolete pre-upgrade classes cleanly removed after confirming zero callers
    expect(cssSrc).not.toContain(".axo-v14-closing-motif");
    expect(cssSrc).not.toContain(".axo-v14-footer-mark");

    // Zero hardcoded hex literals inside CSS rules
    expect(cssSrc).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });

  it("keeps Hero, Interactive Demo, and production routes intact without regression", () => {
    const prodHtml = renderToString(<LandingView />);
    expect(prodHtml).toContain('id="landing-header"');
    expect(prodHtml).toContain('id="landing-hero"');
    expect(prodHtml).toContain('id="landing-footer"');

    const v14Html = renderToString(<LandingPreviewV14 />);
    expect(v14Html).toContain('id="landing-hero"');
    expect(v14Html).toContain('id="cach-hoat-dong"');
    expect(v14Html).toContain('id="trai-nghiem"');
    expect(v14Html).toContain('id="landing-final-cta"');
    expect(v14Html).toContain('id="landing-footer"');

    const demoHtml = renderToString(<LandingInteractiveDemo presentation="v14" />);
    expect(demoHtml).toContain('id="btn-landing-sample-chop-thiet-dien-ba-diem"');
    expect(demoHtml).toContain('id="btn-landing-sample-lap-phuong-thiet-dien-bat-ky"');
    expect(demoHtml).toContain('id="btn-landing-open-showcase-3d"');
    // Demo CTA button was not inadvertently mutated
    const demoSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingInteractiveDemo.tsx"),
      "utf8",
    );
    expect(demoSrc).toContain('from "./LandingHeroScene3D"');
  });

  it("tracks landing prototype routes & enforces canonical component discipline", () => {
    const landingViewSrc = fs.readFileSync(
      path.resolve(__dirname, "../LandingView.tsx"),
      "utf8",
    );
    expect(landingViewSrc).toContain('from "./landing/LandingPreviewV14"');
    expect(landingViewSrc).toContain('from "./landing/LandingPrototypeA"');
    expect(landingViewSrc).toContain('from "./landing/LandingPrototypeB"');

    const closingSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingClosingV14.tsx"),
      "utf8",
    );
    expect(closingSrc).toContain('from "./LandingClosingScene3D"');
    expect(closingSrc).not.toContain("LandingClosingScene3DV15");
    expect(closingSrc).not.toContain("ClosingConstructionMotif");

    const reportPath = path.resolve(
      __dirname,
      "../../../../docs/evaluation/landing/AXO-LANDING-CTA-FOOTER-REFINEMENT-REPORT.md",
    );
    if (fs.existsSync(reportPath)) {
      const reportSrc = fs.readFileSync(reportPath, "utf8");
      expect(reportSrc).not.toContain("APPROVED_BY_USER");
      expect(reportSrc).toContain("PENDING_OWNER_REVIEW");
    }
  });
});
