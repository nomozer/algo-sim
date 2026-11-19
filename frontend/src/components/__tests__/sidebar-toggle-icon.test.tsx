import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { IconAxoLogo, IconAxoSidebarLogo, IconSidebarPanel } from "../icons";
import { IconSidebarCollapsedTrigger, IconSidebarToggle } from "../LeftSidebar";

describe("Sidebar Toggle Icon Refinement (V1.1)", () => {
  it("keeps outer box and detached interior bar geometry while reducing corner radius rx cleanly", () => {
    const html = renderToString(<IconSidebarPanel />);
    const rectMatch = html.match(
      /<rect[^>]*x="([\d.]+)"[^>]*y="([\d.]+)"[^>]*width="([\d.]+)"[^>]*height="([\d.]+)"[^>]*rx="([\d.]+)"/,
    );
    expect(rectMatch).not.toBeNull();

    const [, xStr, yStr, wStr, hStr, rxStr] = rectMatch!;
    expect(Number(xStr)).toBeCloseTo(2.25, 2);
    expect(Number(yStr)).toBeCloseTo(3.25, 2);
    expect(Number(wStr)).toBeCloseTo(15.5, 2);
    expect(Number(hStr)).toBeCloseTo(13.5, 2);

    const rx = Number(rxStr);
    // ~38.3% reduction from previous rx=3 -> rx=1.85 (crisper rounded corners matching editorial frames)
    expect(rx).toBeGreaterThanOrEqual(1.6);
    expect(rx).toBeLessThanOrEqual(2.1);

    const pathMatch = html.match(/<path[^>]*d="M([\d.]+)\s+([\d.]+)v([\d.]+)"/);
    expect(pathMatch).not.toBeNull();
    const [, barXStr, barY1Str, barLenStr] = pathMatch!;
    expect(Number(barXStr)).toBeCloseTo(6.25, 2);
    expect(Number(barY1Str)).toBeCloseTo(6.75, 2);
    expect(Number(barLenStr)).toBeCloseTo(6.5, 2);
  });

  it("shares the exact IconSidebarPanel glyph across LeftSidebar open and collapsed triggers", () => {
    const base = renderToString(<IconSidebarPanel />);
    expect(renderToString(<IconSidebarToggle />)).toBe(base);
    expect(renderToString(<IconSidebarCollapsedTrigger />)).toBe(base);
  });

  it("does not alter the Axo brand logos", () => {
    const mainLogo = renderToString(<IconAxoLogo />);
    const sidebarLogo = renderToString(<IconAxoSidebarLogo />);
    expect(mainLogo).toContain("<svg");
    expect(sidebarLogo).toContain("<svg");
    expect(mainLogo).not.toContain("sb-toggle-layout-icon");
    expect(sidebarLogo).not.toContain("sb-toggle-layout-icon");
  });
});
