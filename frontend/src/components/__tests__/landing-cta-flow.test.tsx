import { renderToString } from "react-dom/server";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { registerAllSimulations } from "../../simulations";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { useAppStore } from "../../state/store";
import { LandingView } from "../LandingView";
import {
  AXO_INTENDED_DESTINATION_KEY,
  applyIntendedDestination,
  clearIntendedDestination,
  consumeIntendedDestination,
  enterAxoWorkspace,
  enterAxoWorkspaceWithOptions,
  openLibraryFromLanding,
  openSampleInWorkspace,
  peekIntendedDestination,
  saveIntendedDestination,
} from "../landing/landing-geometry-data";

const SAMPLE_STUDENT: AuthUser = {
  id: 77,
  email: "hocsinh@axo.edu.vn",
  displayName: "Phạm Minh Tuấn",
  role: "student",
  mustChangePassword: false,
  status: "active",
};

function syncStoresForSSR() {
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

function makeMemoryStorage(): Storage {
  const map = new Map<string, string>();
  return {
    get length() {
      return map.size;
    },
    clear() {
      map.clear();
    },
    getItem(key: string) {
      return map.has(key) ? map.get(key)! : null;
    },
    key(index: number) {
      return Array.from(map.keys())[index] ?? null;
    },
    removeItem(key: string) {
      map.delete(key);
    },
    setItem(key: string, value: string) {
      map.set(key, String(value));
    },
  };
}

describe("AXO Landing V1.2.2 — Canonical CTAs, Copy Accuracy & Intended Destination Flow", () => {
  const origWindow = (globalThis as { window?: unknown }).window;

  beforeAll(() => {
    registerAllSimulations();
  });

  beforeEach(() => {
    clearIntendedDestination();
    vi.stubGlobal("window", {
      location: { pathname: "/gioi-thieu", hash: "", search: "" },
      sessionStorage: makeMemoryStorage(),
      localStorage: makeMemoryStorage(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    if (origWindow !== undefined) {
      (globalThis as { window?: unknown }).window = origWindow;
    }
    clearIntendedDestination();
    useAuthStore.setState({
      user: null,
      resolved: false,
      error: null,
      entitlement: { canRunSimulation: true, canPersistHistory: false, trialsLeft: null },
    });
    useAppStore.getState().reset();
    syncStoresForSSR();
  });

  it("renders Guest canonical CTAs, truthful closing copy, and clean Footer without duplicate CTA", () => {
    useAuthStore.setState({ user: null, resolved: true });
    syncStoresForSSR();
    const html = renderToString(<LandingView />);

    expect(html).toContain("Bắt đầu dựng hình");
    expect(html).toContain("Khám phá cách hoạt động");
    expect(html).toContain("Khám phá thư viện bài mẫu");
    expect(html).toContain("Mở trong Xưởng 3D");
    expect(html).toContain("Từ đề toán đến mô hình hình học không gian.");
    expect(html).not.toContain("Tự tay dựng hình không gian từ đề bài của bạn.");

    const footerStart = html.indexOf('<footer id="landing-footer"');
    const footerHtml = footerStart >= 0 ? html.slice(footerStart) : "";
    expect(footerHtml).toContain("Thư viện bài mẫu");
    expect(footerHtml).not.toContain("Vào ứng dụng");
    expect(footerHtml).not.toContain("Bắt đầu dựng hình");
    expect(footerHtml).not.toContain("Đăng nhập");
  });

  it("switches Hero, Header, and Final CTA to 'Vào ứng dụng' when authenticated", () => {
    useAuthStore.setState({ user: SAMPLE_STUDENT, resolved: true });
    syncStoresForSSR();
    const html = renderToString(<LandingView />);

    const countMatches = (html.match(/>Vào ứng dụng<\/button>/g) ?? []).length;
    expect(countMatches).toBe(3); // Header + Hero + Final CTA
    expect(html).not.toContain("Bắt đầu dựng hình");
  });

  it("preserves exact intended destination when auth is required and restores it once after login (zero loop)", () => {
    useAuthStore.setState({
      user: null,
      resolved: true,
      entitlement: { canRunSimulation: false, canPersistHistory: false, trialsLeft: 0 },
    });
    useAppStore.getState().setProblemText("Cho hình chóp S.ABC có SA vuông góc với đáy");
    useAppStore.getState().setView("landing");

    // Clicking Start when Guest quota exhausted routes directly to existing Axo login view & records destination
    enterAxoWorkspace();
    expect(useAppStore.getState().view).toBe("login");
    expect(peekIntendedDestination()?.kind).toBe("home");
    expect(window.sessionStorage.getItem(AXO_INTENDED_DESTINATION_KEY)).toBeTruthy();

    // Sample-specific intended destination resumes that exact sample after login & consumes key (single-use)
    saveIntendedDestination({ kind: "sample", sampleId: "chop-thiet-dien-ba-diem" });
    const pendingSample = consumeIntendedDestination();
    expect(pendingSample?.kind).toBe("sample");
    expect(peekIntendedDestination()).toBeNull();

    const applied = applyIntendedDestination(pendingSample!, SAMPLE_STUDENT);
    expect(applied).toBe(true);
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().activeSampleId).toBe("chop-thiet-dien-ba-diem");

    // Explicitly requiring auth while an active simulation exists preserves workspace resumption
    enterAxoWorkspaceWithOptions({ requireAuth: true });
    expect(peekIntendedDestination()?.kind).toBe("workspace");
    expect(peekIntendedDestination()?.sampleId).toBe("chop-thiet-dien-ba-diem");
  });

  it("allows Guests to view public Library and Sample models without forcing login", () => {
    useAuthStore.setState({ user: null, resolved: true });
    useAppStore.getState().setView("landing");

    openLibraryFromLanding();
    expect(useAppStore.getState().view).toBe("library");

    openSampleInWorkspace("lap-phuong-thiet-dien-bat-ky");
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().activeSampleId).toBe("lap-phuong-thiet-dien-bat-ky");
  });
});
