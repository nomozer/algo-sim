import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore, type AuthUser } from "../../state/auth";
import {
  computeTrueShapeSection2D,
  LandingHeroV14,
} from "../landing/LandingHeroV14";

function syncAuthStoreForSSR() {
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
}

const TEST_STUDENT_USER: AuthUser = {
  id: 101,
  email: "student@axo.edu.vn",
  displayName: "Nguyễn Minh Anh",
  role: "student",
  mustChangePassword: false,
  status: "active",
};

describe("AXO Landing V1.4 — Hero Visual System & Lifecycle", () => {
  afterEach(() => {
    useAuthStore.setState({ user: null });
    syncAuthStoreForSSR();
  });

  it("computes an exact isometric 2D true-shape projection of MENPF", () => {
    const result = computeTrueShapeSection2D();
    expect(result.vertices.map((v) => v.label)).toEqual(["M", "E", "N", "P", "F"]);
    expect(result.edgeLengths3D.length).toBe(5);
    expect(result.edgeLengths2D.length).toBe(5);
    expect(result.maxDeviation).toBeLessThan(1e-4);
    for (const v of result.vertices) {
      expect(v.nx).toBeGreaterThanOrEqual(0);
      expect(v.nx).toBeLessThanOrEqual(1);
      expect(v.ny).toBeGreaterThanOrEqual(0);
      expect(v.ny).toBeLessThanOrEqual(1);
    }
  });

  it("renders guest and authenticated Hero CTAs cleanly without extra banners", () => {
    useAuthStore.setState({ user: null });
    syncAuthStoreForSSR();
    const guestHtml = renderToStaticMarkup(<LandingHeroV14 />);
    expect(guestHtml).toContain("axo-v14-anno-circle");
    expect(guestHtml).toContain('id="btn-landing-hero-start"');
    expect(guestHtml).toContain("Bắt đầu dựng hình");
    expect(guestHtml).toContain('id="btn-landing-hero-story"');
    expect(guestHtml).toContain("Xem cách hoạt động");
    expect(guestHtml).toContain('id="landing-hero-sculpture"');
    expect(guestHtml).toContain("Thiết diện thật (MNP)");
    expect(guestHtml).toContain("S(MENPF) = 6√6");
    expect(guestHtml).not.toContain("Pending Owner Review");

    useAuthStore.setState({ user: TEST_STUDENT_USER });
    syncAuthStoreForSSR();
    const authHtml = renderToStaticMarkup(<LandingHeroV14 />);
    expect(authHtml).toContain("Vào ứng dụng");
    expect(authHtml).not.toContain("Đăng nhập ngay");
  });

  it("enforces GPU cleanup, finite choreography, and token hygiene", () => {
    const source = readFileSync(
      resolve(__dirname, "../landing/LandingHeroV14.tsx"),
      "utf8",
    );
    expect(source).not.toContain("var(--");
    expect(source).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(source).toContain("webglcontextlost");
    expect(source).toContain("webglcontextrestored");
    expect(source).toContain("renderer.dispose()");
    expect(source).toContain("cancelAnimationFrame");
    expect(source).toContain("prefers-reduced-motion: reduce");
    expect(source).toContain("ANIMATION_DURATION_MS = 1420");
  });
});
