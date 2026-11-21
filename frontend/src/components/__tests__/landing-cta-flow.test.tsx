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

describe("AXO Landing — Canonical CTAs, Copy Accuracy & Intended Destination Flow", () => {
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

  it("renders Guest canonical CTAs, truthful 3-section copy, Closing Scene, and clean Footer bar", () => {
    useAuthStore.setState({ user: null, resolved: true });
    syncStoresForSSR();
    const html = renderToString(<LandingView />);

    expect(html).toContain("Bắt đầu dựng hình");
    expect(html).toContain("Tìm hiểu về Axo");
    expect(html).toContain("Mở Workspace");
    expect(html).toContain("Nhìn thấy bài toán trong không gian thật.");
    expect(html).toContain("Từ câu đề đến mô hình 3D.");
    expect(html).toContain("Khám phá từ bộ bài mẫu sẵn có.");
    expect(html).toContain("Sẵn sàng nhìn hình học theo cách khác?");

    const footerStart = html.indexOf('<footer id="landing-footer"');
    const footerBarStart = html.indexOf('class="axo-v14-footer-bar"', footerStart);
    const footerBarHtml = footerBarStart >= 0 ? html.slice(footerBarStart) : "";
    expect(footerBarHtml).toContain("Thư viện");
    expect(footerBarHtml).not.toContain("Vào ứng dụng");
    expect(footerBarHtml).not.toContain("Bắt đầu dựng hình");
    expect(footerBarHtml).not.toContain("Đăng nhập");
  });

  it("switches Header, Hero, and Closing Scene CTAs to 'Vào ứng dụng' when authenticated", () => {
    useAuthStore.setState({ user: SAMPLE_STUDENT, resolved: true });
    syncStoresForSSR();
    const html = renderToString(<LandingView />);

    const countMatches = (html.match(/>Vào ứng dụng<\/button>/g) ?? []).length;
    expect(countMatches).toBe(3); // Header + Hero + Closing Scene
    expect(html).not.toContain("Bắt đầu dựng hình");
  });

  it("routes unauthenticated Landing CTAs to /login with saved intended destination, restores Workspace once after login, and avoids redirect loops", () => {
    useAuthStore.setState({
      user: null,
      resolved: true,
      entitlement: { canRunSimulation: true, canPersistHistory: false, trialsLeft: null },
    });
    useAppStore.getState().setProblemText("Cho hình chóp S.ABC có SA vuông góc với đáy");
    useAppStore.getState().setView("landing");

    enterAxoWorkspace();
    expect(useAppStore.getState().view).toBe("login");
    expect(useAppStore.getState().guestEnteredApp).toBe(false);
    expect(peekIntendedDestination()?.kind).toBe("home");
    expect(window.sessionStorage.getItem(AXO_INTENDED_DESTINATION_KEY)).toBeTruthy();

    saveIntendedDestination({ kind: "sample", sampleId: "chop-thiet-dien-ba-diem" });
    const pendingSample = consumeIntendedDestination();
    expect(pendingSample?.kind).toBe("sample");
    expect(peekIntendedDestination()).toBeNull();

    const applied = applyIntendedDestination(pendingSample!, SAMPLE_STUDENT);
    expect(applied).toBe(true);
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().guestEnteredApp).toBe(true);
    expect(useAppStore.getState().activeSampleId).toBe("chop-thiet-dien-ba-diem");

    // Unauthenticated re-entry with active workspace preserves active sample destination
    useAuthStore.setState({ user: null, resolved: true });
    enterAxoWorkspaceWithOptions({ requireAuth: true });
    expect(useAppStore.getState().view).toBe("login");
    expect(peekIntendedDestination()?.kind).toBe("workspace");
    expect(peekIntendedDestination()?.sampleId).toBe("chop-thiet-dien-ba-diem");
  });

  it("allows Guests to view public Library and open verified Sample models without forcing login", () => {
    useAuthStore.setState({ user: null, resolved: true });
    useAppStore.getState().setView("landing");

    openLibraryFromLanding();
    expect(useAppStore.getState().view).toBe("library");

    openSampleInWorkspace("lap-phuong-thiet-dien-bat-ky");
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().activeSampleId).toBe("lap-phuong-thiet-dien-bat-ky");
  });
});
