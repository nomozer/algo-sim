import { renderToString } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App, {
  AXO_AUTH_SYNC_STORAGE_KEY,
  reconcileAuthSession,
  resetAuthReconcileForTests,
} from "../../App";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { useAppStore } from "../../state/store";
import {
  clearIntendedDestination,
  enterAxoWorkspace,
  enterAxoWorkspaceWithOptions,
} from "../landing/landing-geometry-data";

const USERS_BY_ROLE: readonly AuthUser[] = [
  {
    id: 101,
    email: "student@axo.edu.vn",
    displayName: "Nguyễn Minh Anh",
    role: "student",
    mustChangePassword: false,
    status: "active",
  },
  {
    id: 202,
    email: "teacher@axo.edu.vn",
    displayName: "Trần Phương Lan",
    role: "teacher",
    mustChangePassword: false,
    status: "active",
  },
  {
    id: 1,
    email: "admin@axo.edu.vn",
    displayName: "Quản trị Axo",
    role: "admin",
    mustChangePassword: false,
    status: "active",
  },
];

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

describe("AXO Landing Page V1.2.1 — Auth & Navigation Sync", () => {
  const origWindow = (globalThis as { window?: unknown }).window;

  beforeEach(() => {
    resetAuthReconcileForTests();
    const sessionStorage = makeMemoryStorage();
    const localStorage = makeMemoryStorage();
    vi.stubGlobal("window", {
      location: { pathname: "/", hash: "", search: "" },
      sessionStorage,
      localStorage,
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

  it("synchronizes authenticated Student/Teacher/Admin state between Landing Header and Workspace LeftSidebar", () => {
    for (const user of USERS_BY_ROLE) {
      useAuthStore.setState({ user, resolved: true, error: null });
      useAppStore.getState().setView("landing");
      syncStoresForSSR();

      const landingHtml = renderToString(<App />);
      const headerHtml = landingHtml.slice(
        landingHtml.indexOf('<header id="landing-header"'),
        landingHtml.indexOf("</header>") + "</header>".length,
      );
      expect(landingHtml).toContain('id="view-landing"');
      expect(headerHtml).toContain('id="btn-landing-header-start"');
      expect(headerHtml).toContain('id="btn-landing-header-library"');
      expect(headerHtml).toContain("Vào ứng dụng");
      expect(headerHtml).not.toContain('id="header-user-actions"');
      expect(headerHtml).not.toContain(user.displayName);

      enterAxoWorkspace();
      syncStoresForSSR();
      const expectedView = user.role === "admin" ? "admin" : "home";
      expect(useAppStore.getState().view).toBe(expectedView);
      expect(useAppStore.getState().guestEnteredApp).toBe(true);

      const workspaceHtml = renderToString(<App />);
      if (user.role !== "admin") {
        expect(workspaceHtml).toContain('id="left-sidebar"');
        expect(workspaceHtml).toContain('id="sb-user-account-btn"');
        expect(workspaceHtml).toContain(user.displayName);
        expect(workspaceHtml).not.toContain('id="sb-guest-account-btn"');
      } else {
        expect(workspaceHtml).not.toContain('id="view-landing"');
      }
    }
  });

  it("supports clean Landing -> Login -> Auth Success -> Workspace and preserves draft problemText across Landing -> Workspace", () => {
    useAuthStore.setState({ user: null, resolved: true, error: null });
    useAppStore.getState().setView("landing");
    enterAxoWorkspaceWithOptions({ requireAuth: true });
    expect(useAppStore.getState().view).toBe("login");
    expect(useAppStore.getState().guestEnteredApp).toBe(false);

    useAuthStore.setState({ user: USERS_BY_ROLE[0], resolved: true, error: null });
    useAppStore.getState().goHome();
    useAppStore.getState().setProblemText("Cho hình chóp S.ABCD có đáy là hình vuông cạnh a.");
    useAppStore.getState().setView("landing");
    expect(useAppStore.getState().view).toBe("landing");

    enterAxoWorkspace();
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().guestEnteredApp).toBe(true);
    expect(useAppStore.getState().problemText).toBe(
      "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a.",
    );
  });

  it("clears stale user and session hint when /api/auth/me rejects with HTTP 401 (expired session)", async () => {
    window.sessionStorage.setItem("axo_auth_session_hint", "1");
    useAuthStore.setState({ user: USERS_BY_ROLE[1], resolved: false, error: null });

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await reconcileAuthSession(true);

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/auth/me",
      expect.objectContaining({ credentials: "include", method: "GET" }),
    );
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().resolved).toBe(true);
    expect(window.sessionStorage.getItem("axo_auth_session_hint")).toBeNull();
  });

  it("updates user immediately when /api/auth/me reports active session (e.g. after cross-tab login) without wipe on transient network errors", async () => {
    useAuthStore.setState({ user: null, resolved: false, error: null });

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ user: USERS_BY_ROLE[0] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await reconcileAuthSession(true);
    expect(useAuthStore.getState().user?.email).toBe(USERS_BY_ROLE[0].email);
    expect(useAuthStore.getState().resolved).toBe(true);

    // Transient network error preserves verified user session instead of spurious logout
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("offline"));
    await reconcileAuthSession(true);
    expect(useAuthStore.getState().user?.email).toBe(USERS_BY_ROLE[0].email);
    expect(AXO_AUTH_SYNC_STORAGE_KEY).toBe("axo_auth_sync_v1");
  });

  it("prevents initial LeftSidebar/TopNav flash on cold load to /gioi-thieu before useEffect runs", () => {
    useAuthStore.setState({ user: USERS_BY_ROLE[0], resolved: true, error: null });
    useAppStore.getState().reset();
    syncStoresForSSR();

    (window as unknown as { location: { pathname: string } }).location.pathname = "/gioi-thieu";
    const html = renderToString(<App />);
    expect(html).toContain('id="view-landing"');
    expect(html).not.toContain('id="left-sidebar"');
    expect(html).not.toContain('class="nav-bar"');
  });

  it("keeps logged-out Workspace users on /app Guest Workspace and wipes all private state (D3 & D5)", () => {
    useAuthStore.setState({ user: USERS_BY_ROLE[0], resolved: true, error: null });
    useAppStore.setState({
      view: "home",
      guestEnteredApp: true,
      problemText: "Đề bài riêng tư của học sinh A",
      activeHistoryId: "priv-hist-1",
    });

    useAuthStore.setState({ user: null, resolved: true, error: null });
    useAppStore.getState().enterGuestWorkspaceAfterLogout();

    const st = useAppStore.getState();
    expect(st.view).toBe("home");
    expect(st.guestEnteredApp).toBe(true);
    expect(st.problemText).toBe("");
    expect(st.active).toBeNull();
    expect(st.workspaceTabs).toEqual([]);
    expect(st.history).toEqual([]);
    expect(st.activeHistoryId).toBeNull();
  });
});
