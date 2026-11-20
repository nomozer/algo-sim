import fs from "node:fs";
import path from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { LandingView, readLandingPrototypeMode } from "../LandingView";
import { canonicalPathForView, resolveLocationRoute } from "../AxoErrorExperience";
import { LandingHeroV14 } from "../landing/LandingHeroV14";
import { LandingPreviewV14 } from "../landing/LandingPreviewV14";

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

describe("AXO Landing V1.4 — Minimal Product-First Hero, Cleanup & Lifecycle", () => {
  afterEach(() => {
    useAuthStore.setState({ user: null });
    syncAuthStoreForSSR();
  });

  it("activates ?preview=landing-v14 (with ?preview=v1.4 alias) and rejects deprecated axo-hero/portal-reference previews", () => {
    expect(canonicalPathForView("landing")).toBe("/about");
    expect(resolveLocationRoute("/about")).toEqual({ kind: "view", view: "landing" });
    expect(resolveLocationRoute("/gioi-thieu")).toEqual({ kind: "view", view: "landing" });
    expect(resolveLocationRoute("/app")).toEqual({ kind: "view", view: "home" });

    expect(readLandingPrototypeMode("?preview=landing-v14")).toBe("v14");
    expect(readLandingPrototypeMode("?preview=v1.4")).toBe("v14");
    expect(readLandingPrototypeMode("?preview=v14")).toBe("v14");

    expect(readLandingPrototypeMode("?preview=axo-hero")).toBe("prod");
    expect(readLandingPrototypeMode("?preview=portal-reference")).toBe("prod");
    expect(readLandingPrototypeMode("")).toBe("prod");

    const prodHtml = renderToStaticMarkup(<LandingView />);
    expect(prodHtml).not.toContain("axo-v14-root");
  });

  it("renders Notion-minimal left copy (without circle stroke) + Bundaumayo-composed Atelier studio diorama visual on right", () => {
    useAuthStore.setState({ user: null });
    syncAuthStoreForSSR();
    const v14Html = renderToStaticMarkup(<LandingPreviewV14 />);
    const heroStart = v14Html.indexOf('id="landing-hero"');
    const storyStart = v14Html.indexOf('id="cach-hoat-dong"');
    expect(heroStart).toBeGreaterThan(-1);
    expect(storyStart).toBeGreaterThan(heroStart);

    const heroSlice = v14Html.slice(heroStart, storyStart);
    expect(heroSlice).toContain('id="axo-v14-hero-heading"');
    expect(heroSlice).toContain("axo-v14-hero-atelier");
    expect(heroSlice).toContain("Hình học không gian,");
    expect(heroSlice).toContain("dễ hình dung hơn.");
    expect(heroSlice).not.toContain("axo-v14-anno-circle");
    expect(heroSlice).toContain('id="btn-landing-hero-start"');
    expect(heroSlice).toContain("Bắt đầu dựng hình");
    expect(heroSlice).toContain('id="btn-landing-hero-story"');
    expect(heroSlice).toContain("Xem cách hoạt động");
    expect(heroSlice).toContain('id="landing-hero-sculpture"');
    expect(heroSlice).toContain('data-hero-mode="atelier-studio-diorama"');
    expect(heroSlice).toContain("/assets/landing/hero-studio/hero-studio-diorama.png");
    expect(heroSlice).toContain("/assets/landing/hero-studio/hero-float-plane.png");
    expect(heroSlice).toContain("/assets/landing/hero-studio/hero-float-orbit.png");
    expect(heroSlice).not.toContain("12√3");
    expect(heroSlice).not.toContain("axo-v14-hero-minimal");

    expect(heroSlice).not.toContain("<canvas");
    expect(heroSlice).not.toContain("axo-v14-portal-");
    expect(heroSlice).not.toContain("axo-v14-hero-horizon");

    // Non-Hero Landing V1.4 sections stay intact
    expect(v14Html).toContain("axo-v14-root");
    expect(v14Html).toContain('id="cach-hoat-dong"');
    expect(v14Html).toContain('id="trai-nghiem"');
    expect(v14Html).toContain('id="landing-final-cta"');
    expect(v14Html).toContain('id="landing-footer"');
    expect(v14Html).not.toContain("PENDING_OWNER_REVIEW");
    expect(v14Html).not.toContain("APPROVED_BY_USER");

    useAuthStore.setState({ user: TEST_STUDENT_USER });
    syncAuthStoreForSSR();
    const authHtml = renderToStaticMarkup(<LandingHeroV14 />);
    expect(authHtml).toContain("Vào ứng dụng");
    expect(authHtml).not.toContain("Đăng nhập ngay");
  });

  it("enforces full cleanup of retired portals, glass sculpture PNGs, and unused r3f dependencies, while verifying studio plates exist", () => {
    const feRoot = path.resolve(__dirname, "../../..");
    expect(fs.existsSync(path.join(feRoot, "src/prototypes/enter-portals-ref"))).toBe(false);
    expect(fs.existsSync(path.join(feRoot, "public/draco"))).toBe(false);
    expect(fs.existsSync(path.join(feRoot, "public/assets/landing/hero-concept"))).toBe(false);
    expect(fs.existsSync(path.join(feRoot, "src/components/landing/portals"))).toBe(false);
    expect(fs.existsSync(path.join(feRoot, "public/assets/landing/hero-studio/hero-studio-diorama.png"))).toBe(true);
    expect(fs.existsSync(path.join(feRoot, "public/assets/landing/hero-studio/hero-float-plane.png"))).toBe(true);
    expect(fs.existsSync(path.join(feRoot, "public/assets/landing/hero-studio/hero-float-orbit.png"))).toBe(true);

    const pkg = JSON.parse(fs.readFileSync(path.join(feRoot, "package.json"), "utf8")) as {
      dependencies?: Record<string, string>;
    };
    expect(pkg.dependencies?.["@react-three/fiber"]).toBeUndefined();
    expect(pkg.dependencies?.["@react-three/drei"]).toBeUndefined();
    expect(pkg.dependencies?.["maath"]).toBeUndefined();

    const heroSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingHeroV14.tsx"),
      "utf8",
    );
    expect(heroSrc).toContain("prefers-reduced-motion: reduce");
    expect(heroSrc).not.toContain("var(--");
    expect(heroSrc).not.toContain("APPROVED_BY_USER");
  });
});
