import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LandingView, readLandingPrototypeMode } from "../LandingView";
import { LandingPrototypeA } from "../landing/LandingPrototypeA";
import { LandingPrototypeB } from "../landing/LandingPrototypeB";

describe("AXO Landing Page V1.3 — Prototype Isolation, Motion Accessibility & Fallback Safety", () => {
  it("parses query-gated prototype modes deterministically and preserves V1.2.2 by default", () => {
    expect(readLandingPrototypeMode("")).toBe("prod");
    expect(readLandingPrototypeMode("?foo=1")).toBe("prod");
    expect(readLandingPrototypeMode("?prototype=unknown")).toBe("prod");
    expect(readLandingPrototypeMode("?prototype=a")).toBe("a");
    expect(readLandingPrototypeMode("?prototype=A")).toBe("a");
    expect(readLandingPrototypeMode("?prototype=b")).toBe("b");
    expect(readLandingPrototypeMode("?prototype=%20b%20")).toBe("b");

    const defaultHtml = renderToString(<LandingView />);
    expect(defaultHtml).toContain('id="landing-hero"');
    expect(defaultHtml).toContain('id="landing-storytelling-scene"');
    expect(defaultHtml).toContain('id="landing-final-cta"');
    expect(defaultHtml).not.toContain('id="landing-v13-review-banner"');
    expect(defaultHtml).not.toContain("PENDING_OWNER_REVIEW");
  });

  it("renders Prototype A (Vector Motion) cleanly with review banner and pure SVG Hero/Story", () => {
    const html = renderToString(<LandingPrototypeA onSwitchMode={() => undefined} />);

    expect(html).toContain('id="landing-v13-review-banner"');
    expect(html).toContain("PENDING_OWNER_REVIEW");
    expect(html).toContain("axo-v13-proto-a");
    expect(html).toContain('id="landing-hero-sculpture"');
    expect(html).toContain('id="landing-storytelling-scene"');
    expect(html).toContain('id="btn-landing-story-play-toggle"');
    expect(html).toContain("Tạm dừng");

    for (let i = 0; i < 4; i++) {
      expect(html).toContain(`id="btn-landing-story-step-${i}"`);
    }

    // Hero & Story in Prototype A remain 100% vector SVG without WebGL <canvas>
    const heroStart = html.indexOf('id="landing-hero"');
    const demoStart = html.indexOf('id="trai-nghiem"');
    const heroAndStory = demoStart > heroStart ? html.slice(heroStart, demoStart) : html;
    expect(heroAndStory).not.toContain("<canvas");
    expect(heroAndStory).toContain("<svg");
  });

  it("renders Prototype B (3D Spatial) with WebGL context lease slot and deterministic SVG fallbacks", () => {
    const html = renderToString(<LandingPrototypeB onSwitchMode={() => undefined} />);

    expect(html).toContain('id="landing-v13-review-banner"');
    expect(html).toContain("PENDING_OWNER_REVIEW");
    expect(html).toContain("axo-v13-proto-b");
    expect(html).toContain('id="landing-hero-sculpture"');
    expect(html).toContain('id="landing-storytelling-scene"');
    expect(html).toContain('id="btn-landing-story-play-toggle"');
    expect(html).toContain('id="v13-demo-slot"');

    // SSR / no-WebGL initial render renders accessible SVG fallbacks inside both hero and story stages
    expect(html).toContain("Không gian dựng hình 3D với các mặt phẳng cắt và thiết diện");
    expect(html).toContain("Khối lăng trụ ABC.A′B′C′ chặng Bước 1");
  });

  it("enforces prefers-reduced-motion styles, zero inline CSS tokens, and never auto-approves deliverables", () => {
    const landingCss = fs.readFileSync(
      path.resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );
    const protoASrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingPrototypeA.tsx"),
      "utf8",
    );
    const protoBSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingPrototypeB.tsx"),
      "utf8",
    );

    expect(landingCss).toContain("@media (prefers-reduced-motion: reduce)");
    expect(landingCss).toContain(".axo-v13-step-item");
    expect(landingCss).toContain(".axo-v13-play-btn");
    expect(landingCss).toContain(".axo-v13-switch-btn");
    expect(landingCss).toContain(".axo-v13-canvas-host");

    for (const src of [protoASrc, protoBSrc]) {
      expect(src).not.toContain("var(--");
      expect(src).not.toMatch(/import\s+["'][^"']*\.css["']/);
      expect(src).not.toContain("APPROVED_BY_USER");
      expect(src).toContain("prefers-reduced-motion: reduce");
    }
  });
});
