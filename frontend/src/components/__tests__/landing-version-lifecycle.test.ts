import fs from "node:fs";
import path from "node:path";
import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingView, readLandingPrototypeMode } from "../LandingView";
import { LandingPreviewV14 } from "../landing/LandingPreviewV14";

describe("AXO Landing — Version Lifecycle Consolidation & Production Preservation", () => {
  it("removes rejected V1.3 prototypes while keeping ?preview=v1.4 isolated and production intact", () => {
    const landingDir = path.resolve(__dirname, "../landing");
    const files = fs.readdirSync(landingDir);

    expect(files).not.toContain("LandingPrototypeA.tsx");
    expect(files).not.toContain("LandingPrototypeB.tsx");

    // Reject arbitrary V15/V16 proliferation
    for (const file of files) {
      expect(file).not.toMatch(/V1[5-9]|V2[0-9]/);
    }

    // Rejected ?prototype=a|b queries fall back safely to canonical production
    expect(readLandingPrototypeMode("")).toBe("prod");
    expect(readLandingPrototypeMode("?prototype=a")).toBe("prod");
    expect(readLandingPrototypeMode("?prototype=b")).toBe("prod");
    expect(readLandingPrototypeMode("?prototype=unknown")).toBe("prod");
    expect(readLandingPrototypeMode("?preview=v1.4")).toBe("v14");
    expect(readLandingPrototypeMode("?preview=v14")).toBe("v14");

    const prodHtml = renderToString(createElement(LandingView));
    expect(prodHtml).toContain('id="landing-hero"');
    expect(prodHtml).toContain("axo-sp-closing-sculpture");
    expect(prodHtml).not.toContain("axo-v14-root");
    expect(prodHtml).not.toContain("axo-v13-");

    const previewHtml = renderToString(createElement(LandingPreviewV14));
    expect(previewHtml).toContain("axo-v14-root");
    expect(previewHtml).not.toContain("PENDING_OWNER_REVIEW");
  });

  it("removes dead .axo-v13-* CSS and source references across frontend/src", () => {
    const cssSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );
    expect(cssSrc).not.toContain(".axo-v13-");

    const landingViewSrc = fs.readFileSync(
      path.resolve(__dirname, "../LandingView.tsx"),
      "utf8",
    );
    expect(landingViewSrc).not.toContain("LandingPrototypeA");
    expect(landingViewSrc).not.toContain("LandingPrototypeB");
    expect(landingViewSrc).toContain("LandingPreviewV14");

    const appSrc = fs.readFileSync(path.resolve(__dirname, "../../App.tsx"), "utf8");
    expect(appSrc).toContain('effectiveView === "landing"');
    expect(appSrc).toContain('currentPath === "/gioi-thieu"');
  });
});
