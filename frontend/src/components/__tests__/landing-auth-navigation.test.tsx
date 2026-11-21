import fs from "node:fs";
import path from "node:path";
import { renderToString } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App, {
  AXO_AUTH_SYNC_STORAGE_KEY,
  reconcileAuthSession,
  resetAuthReconcileForTests,
} from "../../App";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { historyStore } from "../../state/history";
import { useAppStore } from "../../state/store";
import { LandingHeader } from "../landing/LandingHeader";
import {
  AXO_INTENDED_DESTINATION_KEY,
  applyIntendedDestination,
  clearIntendedDestination,
  enterAxoWorkspace,
  peekIntendedDestination,
} from "../landing/landing-geometry-data";

const USERS: Record<"student" | "teacher" | "admin", AuthUser> = {
  student: {
    id: 101,
    email: "student@axo.edu.vn",
    displayName: "Nguyễn Minh Anh",
    role: "student",
    mustChangePassword: false,
    status: "active",
  },
  teacher: {
    id: 202,
    email: "teacher@axo.edu.vn",
    displayName: "Trần Phương Lan",
    role: "teacher",
    mustChangePassword: false,
    status: "active",
  },
  admin: {
    id: 1,
    email: "admin@axo.edu.vn",
    displayName: "Quản trị Axo",
    role: "admin",
    mustChangePassword: false,
    status: "active",
  },
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

describe("AXO Landing — Auth & Navigation Streamlining", () => {
  const origWindow = (globalThis as { window?: unknown }).window;

  beforeEach(() => {
    resetAuthReconcileForTests();
    clearIntendedDestination();
    vi.stubGlobal("window", {
      location: { pathname: "/gioi-thieu", hash: "", search: "" },
      sessionStorage: makeMemoryStorage(),
      localStorage: makeMemoryStorage(),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    if (origWindow !== undefined) {
      (globalThis as { window?: unknown }).window = origWindow;
    }
    resetAuthReconcileForTests();
    clearIntendedDestination();
    useAuthStore.setState({ user: null, resolved: false, error: null, authGate: null });
    useAppStore.getState().reset();
    syncStoresForSSR();
  });

  it("removes standalone Guest login actions from Header & Drawer and renders 3 post-Hero nav items + primary CTA", () => {
    useAuthStore.setState({ user: null, resolved: true, error: null });
    syncStoresForSSR();

    const html = renderToString(<LandingHeader />);
    expect(html).toContain('id="btn-landing-logo"');
    expect(html).toContain("Về Axo");
    expect(html).toContain("Cách hoạt động");
    expect(html).toContain("Bài mẫu");
    expect(html).not.toContain("Tổng quan");
    expect(html).toContain('id="btn-landing-header-library"');
    expect(html).toContain("Thư viện");
    expect(html).toContain('id="btn-landing-header-start"');
    expect(html).toContain("Bắt đầu");

    expect(html).not.toContain('id="btn-landing-header-login"');
    expect(html).not.toContain("Đăng nhập");
    expect(html).not.toContain('id="header-user-actions"');

    const headerSrc = fs.readFileSync(
      path.resolve(__dirname, "../landing/LandingHeader.tsx"),
      "utf8",
    );
    expect(headerSrc).not.toContain("btn-landing-header-login");
    expect(headerSrc).not.toContain("btn-landing-drawer-login");
    expect(headerSrc).not.toContain("Đăng nhập tài khoản");
  });

  it("routes authenticated Student/Teacher to Workspace and Admin to Admin Workspace without login screen", () => {
    for (const role of ["student", "teacher", "admin"] as const) {
      const user = USERS[role];
      useAuthStore.setState({ user, resolved: true, error: null });
      useAppStore.getState().setView("landing");
      syncStoresForSSR();

      const html = renderToString(<LandingHeader />);
      expect(html).not.toContain('id="header-user-actions"');
      expect(html).not.toContain(user.displayName);
      expect(html).toContain('id="btn-landing-header-library"');
      expect(html).toContain("Thư viện");
      expect(html).toContain("Vào ứng dụng");

      enterAxoWorkspace();
      expect(useAppStore.getState().view).toBe(role === "admin" ? "admin" : "home");
      expect(useAppStore.getState().view).not.toBe("login");
    }
  });

  it("reconciles expired sessions (HTTP 401) and cross-tab login/logout without redirect loops", async () => {
    window.sessionStorage.setItem("axo_auth_session_hint", "1");
    useAuthStore.setState({ user: USERS.student, resolved: false, error: null });

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await reconcileAuthSession(true);
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().resolved).toBe(true);
    syncStoresForSSR();

    const guestLanding = renderToString(<App />);
    expect(guestLanding).toContain('id="view-landing"');
    expect(guestLanding).toContain("Bắt đầu dựng hình");

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ user: USERS.teacher }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await reconcileAuthSession(true);
    syncStoresForSSR();
    expect(useAuthStore.getState().user?.email).toBe(USERS.teacher.email);

    const authedLanding = renderToString(<App />);
    const authedHeader = authedLanding.slice(
      authedLanding.indexOf('<header id="landing-header"'),
      authedLanding.indexOf("</header>") + "</header>".length,
    );
    expect(authedLanding).toContain('id="view-landing"');
    expect(authedHeader).toContain("Vào ứng dụng");
    expect(authedHeader).not.toContain('id="header-user-actions"');
    expect(authedHeader).not.toContain(USERS.teacher.displayName);
    expect(AXO_AUTH_SYNC_STORAGE_KEY).toBe("axo_auth_sync_v1");
  });

  it("rejects tampered or external-URL intendedDestination payloads to prevent open redirects", () => {
    window.sessionStorage.setItem(
      AXO_INTENDED_DESTINATION_KEY,
      JSON.stringify({ kind: "external", sampleId: "https://evil.example/phish", createdAt: Date.now() }),
    );
    expect(peekIntendedDestination()).toBeNull();

    window.sessionStorage.setItem(
      AXO_INTENDED_DESTINATION_KEY,
      JSON.stringify({ kind: "sample", sampleId: "https://evil.example/x", createdAt: Date.now() }),
    );
    expect(peekIntendedDestination()).toBeNull();
  });

  it("routes unauthenticated Landing entry to /login and restores saved draft from historyStore after auth across applyIntendedDestination and enterAxoWorkspace", () => {
    const draft = "Cho hinh chop S.ABCD day hinh thang";
    historyStore.writeDraftText(draft);
    useAppStore.setState({ problemText: "", view: "landing" });
    useAuthStore.setState({
      user: null,
      resolved: true,
      entitlement: {
        canRunSimulation: true,
        canPersistHistory: false,
        trialsLeft: 1,
      },
    });

    enterAxoWorkspace();
    expect(useAppStore.getState().view).toBe("login");
    expect(useAppStore.getState().guestEnteredApp).toBe(false);

    useAppStore.setState({ problemText: "", view: "login" });
    expect(
      applyIntendedDestination({ kind: "home", createdAt: Date.now() }, USERS.student),
    ).toBe(true);
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().guestEnteredApp).toBe(true);
    expect(useAppStore.getState().problemText).toBe(draft);

    useAuthStore.setState({ user: USERS.student, resolved: true });
    useAppStore.setState({ problemText: "", view: "landing" });
    enterAxoWorkspace();
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().problemText).toBe(draft);

    historyStore.clearDraftText();
  });
});
