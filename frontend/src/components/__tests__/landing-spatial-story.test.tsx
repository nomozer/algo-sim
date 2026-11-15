import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../../App";
import { registerAllSimulations } from "../../simulations";
import { useAuthStore } from "../../state/auth";
import { useAppStore } from "../../state/store";
import { LandingView } from "../LandingView";
import {
  enterAxoWorkspace,
  LANDING_CUBE_SAMPLE,
  LANDING_PYRAMID_SAMPLE,
  openLibraryFromLanding,
  openSampleInWorkspace,
} from "../landing/landing-geometry-data";

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
}

describe("Axo Spatial Story — Landing Page V1 Prototype", () => {
  beforeEach(() => {
    registerAllSimulations();
    useAuthStore.setState({
      user: null,
      resolved: true,
    });
    useAppStore.setState({
      guestEnteredApp: false,
      active: null,
      activeSampleId: null,
      activeHistoryId: null,
      workspaceTabs: [],
      activeTabId: null,
      routeFailure: null,
      view: "home",
    });
    syncStoreForSSR();
  });

  it("hiển thị đúng bản sắc Axo tiếng Việt, không chứa nội dung hay liên kết giả của Notion", () => {
    const html = renderToString(<LandingView />);

    expect(html).toContain('id="view-landing"');
    expect(html).toContain('id="landing-header"');
    expect(html).toContain('id="landing-nav"');
    expect(html).toContain('id="landing-hero"');
    expect(html).toContain('id="btn-landing-hero-start"');
    expect(html).toContain('id="btn-landing-hero-library"');
    expect(html).toContain('id="cach-hoat-dong"');
    expect(html).toContain('id="trai-nghiem"');
    expect(html).toContain('id="landing-product-showcase"');
    expect(html).toContain('id="btn-landing-open-showcase-3d"');
    expect(html).toContain('id="landing-final-cta"');
    expect(html).toContain('id="landing-footer"');

    expect(html).toContain("Hình học không gian, dễ hình dung hơn.");
    expect(html).toContain("Bắt đầu dựng hình");
    expect(html).toContain("Cách Axo hoạt động");
    expect(html).toContain("Giới thiệu");
    expect(html).toContain("Cách hoạt động");
    expect(html).toContain("Trải nghiệm");

    for (const forbidden of [
      "Notion",
      "Ramp HQ",
      "Where teams and",
      "OpenAI",
      "FedEx",
      "Pricing",
      "Enterprise",
      "Blog",
    ]) {
      expect(html).not.toContain(forbidden);
    }
  });

  it("dữ liệu 3D cho hai bài mẫu thỏa mãn đúng phương trình mặt cắt và kích thước đại số", () => {
    // 1. Chóp S.ABCD cắt bởi (MNP): x + y + 2z = 6
    const pyramidIds = ["M", "E", "N", "P", "F"] as const;
    for (const id of pyramidIds) {
      const [x, y, z] = LANDING_PYRAMID_SAMPLE.pointMap[id].domainXyz;
      expect(Math.abs(x + y + 2 * z - 6)).toBeLessThan(1e-9);
    }
    const [sx, sy, sz] = LANDING_PYRAMID_SAMPLE.pointMap.S.domainXyz;
    const [ax, ay, az] = LANDING_PYRAMID_SAMPLE.pointMap.A.domainXyz;
    expect(sx).toBe(ax);
    expect(sy).toBe(ay);
    expect(sz - az).toBe(6);

    // 2. Lập phương ABCD.A'B'C'D' cắt bởi (MNP): -x + y + z = 2 (lục giác đều cạnh 2√2)
    const cubeIds = LANDING_CUBE_SAMPLE.sectionLoop;
    for (let i = 0; i < cubeIds.length; i++) {
      const cur = LANDING_CUBE_SAMPLE.pointMap[cubeIds[i]].domainXyz;
      const nxt = LANDING_CUBE_SAMPLE.pointMap[cubeIds[(i + 1) % cubeIds.length]].domainXyz;
      expect(Math.abs(-cur[0] + cur[1] + cur[2] - 2)).toBeLessThan(1e-9);
      const edgeLen = Math.hypot(nxt[0] - cur[0], nxt[1] - cur[1], nxt[2] - cur[2]);
      expect(Math.abs(edgeLen - Math.sqrt(8))).toBeLessThan(1e-9);
    }
  });

  it("CTA chính, CTA thư viện và Showcase Interactive chuyển đúng sang App Workspace", () => {
    enterAxoWorkspace();
    expect(useAppStore.getState().guestEnteredApp).toBe(true);
    expect(useAppStore.getState().view).toBe("home");
    syncStoreForSSR();
    const homeHtml = renderToString(<App />);
    expect(homeHtml).toContain('id="left-sidebar"');
    expect(homeHtml).not.toContain('id="view-landing"');

    openLibraryFromLanding();
    expect(useAppStore.getState().guestEnteredApp).toBe(true);
    expect(useAppStore.getState().view).toBe("library");

    openSampleInWorkspace("chop-thiet-dien-ba-diem");
    expect(useAppStore.getState().guestEnteredApp).toBe(true);
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().activeSampleId).toBe("chop-thiet-dien-ba-diem");
  });

  it("điều hướng trực tiếp /gioi-thieu, khách ở /, người dùng đã đăng nhập ở / và /simulation/... hoạt động chuẩn", () => {
    useAppStore.getState().syncLocationRoute("/gioi-thieu");
    expect(useAppStore.getState().view).toBe("landing");

    // Khách tại "/" -> Landing
    useAppStore.getState().syncLocationRoute("/");
    syncStoreForSSR();
    expect(renderToString(<App />)).toContain('id="view-landing"');

    // Người dùng đã đăng nhập tại "/" -> thẳng Workspace Sidebar
    useAuthStore.setState({
      user: {
        id: 1,
        email: "demo@axo.edu.vn",
        displayName: "Demo",
        role: "student",
        mustChangePassword: false,
      },
      resolved: true,
    });
    syncStoreForSSR();
    expect(renderToString(<App />)).toContain('id="left-sidebar"');
    expect(renderToString(<App />)).not.toContain('id="view-landing"');

    // Deep-link trực tiếp vào mô phỏng
    useAppStore.getState().syncLocationRoute("/simulation/oxyz-line-plane-intersection");
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().activeSampleId).toBe("oxyz-giao-diem-duong-mat");
  });

  it("CSS của Landing chỉ giới hạn phạm vi trong #view-landing và không đụng global.css", () => {
    const cssText = readFileSync(new URL("../landing/landing.css", import.meta.url), "utf-8");
    expect(cssText).toContain("#view-landing.axo-sp-root");
    expect(cssText).not.toMatch(/^\s*(html|body|\*)\s*\{/m);
    expect(cssText).not.toContain(".app-root");
  });
});
