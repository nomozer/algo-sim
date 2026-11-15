import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { AnnotatedPhrase } from "../landing/AnnotatedHeading";

describe("AXO Landing V1.4 — Expressive Geometry Typography", () => {
  it("renders all three annotation variants without duplicating readable text", () => {
    const circleHtml = renderToStaticMarkup(
      <h1>
        Hình học không gian, dễ{" "}
        <AnnotatedPhrase variant="circle">hình dung</AnnotatedPhrase> hơn.
      </h1>,
    );
    const strippedHeroText = circleHtml.replace(/<[^>]+>/g, "");
    expect(strippedHeroText).toBe("Hình học không gian, dễ hình dung hơn.");
    expect(circleHtml).toContain("axo-v14-anno-circle");
    expect(circleHtml).toContain("axo-v14-anno-path-circle");
    expect(circleHtml).toContain('aria-hidden="true"');
    expect(circleHtml).toContain('preserveAspectRatio="none"');
    expect(circleHtml).toContain('pathLength="1"');

    const underlineHtml = renderToStaticMarkup(
      <h2>
        Theo dõi bài toán qua{" "}
        <AnnotatedPhrase variant="underline">từng lớp không gian</AnnotatedPhrase>.
      </h2>,
    );
    expect(underlineHtml.replace(/<[^>]+>/g, "")).toBe(
      "Theo dõi bài toán qua từng lớp không gian.",
    );
    expect(underlineHtml).toContain("axo-v14-anno-underline");
    expect(underlineHtml).toContain("axo-v14-anno-node");

    const highlightHtml = renderToStaticMarkup(
      <AnnotatedPhrase variant="highlight">thiết diện thật</AnnotatedPhrase>,
    );
    expect(highlightHtml.replace(/<[^>]+>/g, "")).toBe("thiết diện thật");
    expect(highlightHtml).toContain("axo-v14-anno-highlight");
    expect(highlightHtml).toContain("axo-v14-anno-plane");
  });

  it("supports active and pending states without inline CSS custom properties", () => {
    const pendingHtml = renderToStaticMarkup(
      <AnnotatedPhrase variant="highlight" active={false}>
        S(MNPQ) = 3√7
      </AnnotatedPhrase>,
    );
    expect(pendingHtml).toContain("is-pending");

    const source = readFileSync(
      resolve(__dirname, "../landing/AnnotatedHeading.tsx"),
      "utf8",
    );
    expect(source).not.toContain("var(--");
    expect(source).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });

  it("defines non-scaling strokes and reduced-motion fallbacks in landing.css", () => {
    const css = readFileSync(
      resolve(__dirname, "../landing/landing.css"),
      "utf8",
    );
    expect(css).toContain(".axo-v14-anno-path");
    expect(css).toContain("vector-effect: non-scaling-stroke");
    expect(css).toContain(".axo-v14-anno.is-active .axo-v14-anno-path");
    expect(css).toContain("stroke-dashoffset: 0");
  });
});
