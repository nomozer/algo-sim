import { GEOMETRY_SAMPLES, geometrySampleById } from "../../data/geometry-samples";
import { useAuthStore, type AuthUser } from "../../state/auth";
import { historyStore } from "../../state/history";
import { useAppStore } from "../../state/store";

export const AXO_INTENDED_DESTINATION_KEY = "axo_intended_destination_v1";
const INTENDED_DEST_TTL_MS = 30 * 60 * 1000;

export type IntendedDestinationKind = "home" | "workspace" | "library" | "sample" | "admin";

export interface IntendedDestination {
  readonly kind: IntendedDestinationKind;
  readonly sampleId?: string;
  readonly preferActive?: boolean;
  readonly createdAt: number;
}

let inMemoryIntendedDestination: IntendedDestination | null = null;

function readSessionStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage ?? null;
  } catch {
    return null;
  }
}

const VALID_INTENDED_DEST_KINDS: ReadonlySet<string> = new Set([
  "home",
  "workspace",
  "library",
  "sample",
  "admin",
]);

function isSafeSampleId(value: unknown): value is string {
  return typeof value === "string" && /^[a-z0-9][a-z0-9-_]{0,79}$/i.test(value);
}

function isIntendedDestinationFresh(dest: IntendedDestination | null): dest is IntendedDestination {
  if (!dest || typeof dest !== "object") return false;
  if (!VALID_INTENDED_DEST_KINDS.has(dest.kind)) return false;
  if (dest.sampleId !== undefined && !isSafeSampleId(dest.sampleId)) return false;
  if (typeof dest.createdAt !== "number" || !Number.isFinite(dest.createdAt)) return false;
  return Date.now() - dest.createdAt <= INTENDED_DEST_TTL_MS;
}

export function saveIntendedDestination(
  dest: Omit<IntendedDestination, "createdAt"> & { createdAt?: number },
): void {
  const normalized: IntendedDestination = {
    kind: dest.kind,
    sampleId: dest.sampleId,
    preferActive: dest.preferActive,
    createdAt: dest.createdAt ?? Date.now(),
  };
  inMemoryIntendedDestination = normalized;
  const ss = readSessionStorage();
  if (!ss) return;
  try {
    ss.setItem(AXO_INTENDED_DESTINATION_KEY, JSON.stringify(normalized));
  } catch {
    /* bỏ qua nếu trình duyệt chặn sessionStorage */
  }
}

export function peekIntendedDestination(): IntendedDestination | null {
  if (isIntendedDestinationFresh(inMemoryIntendedDestination)) {
    return inMemoryIntendedDestination;
  }
  const ss = readSessionStorage();
  if (!ss) return null;
  try {
    const raw = ss.getItem(AXO_INTENDED_DESTINATION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as IntendedDestination;
    if (!isIntendedDestinationFresh(parsed)) {
      clearIntendedDestination();
      return null;
    }
    inMemoryIntendedDestination = parsed;
    return parsed;
  } catch {
    return null;
  }
}

export function clearIntendedDestination(): void {
  inMemoryIntendedDestination = null;
  const ss = readSessionStorage();
  if (!ss) return;
  try {
    ss.removeItem(AXO_INTENDED_DESTINATION_KEY);
  } catch {
    /* bỏ qua nếu trình duyệt chặn sessionStorage */
  }
}

export function consumeIntendedDestination(): IntendedDestination | null {
  const pending = peekIntendedDestination();
  clearIntendedDestination();
  return pending;
}

export function resetIntendedDestinationForTests(): void {
  clearIntendedDestination();
}

/**
 * Restore unsent draft text persisted in historyStore so cold reloads or
 * Landing -> Login -> Workspace round-trips never drop user problem text.
 */
export function restoreSavedDraftIfEmpty(): void {
  const store = useAppStore.getState();
  if (store.problemText.trim().length > 0) return;
  const saved = historyStore.readDraftText();
  if (saved && saved.trim().length > 0) {
    store.setProblemText(saved);
  }
}

/**
 * Restore the exact task destination after successful login/register without creating
 * a redirect loop or losing draft problemText.
 */
export function applyIntendedDestination(dest: IntendedDestination, user: AuthUser | null): boolean {
  if (!user) return false;
  const store = useAppStore.getState();
  store.setGuestEnteredApp(true);

  if (user.role === "admin" || dest.kind === "admin") {
    if (user.role === "admin") {
      store.setView("admin");
      return true;
    }
  }

  if (dest.kind === "sample" && dest.sampleId) {
    const sample = geometrySampleById(dest.sampleId);
    if (sample) {
      store.loadEnvelope(sample.envelope, sample.id, sample.problemText);
      return true;
    }
    store.openLibrary();
    return true;
  }

  if (dest.kind === "library") {
    store.openLibrary();
    return true;
  }

  if (dest.kind === "workspace" && dest.preferActive && store.active !== null) {
    store.setView("workspace");
    return true;
  }

  store.goHome();
  restoreSavedDraftIfEmpty();
  return true;
}

export interface EnterWorkspaceOptions {
  /**
   * Defaults to true: unauthenticated Landing CTAs route through /login with a
   * saved intendedDestination and land directly in Workspace (/app) after auth.
   * Pass false only when explicitly entering a guest-accessible workspace path.
   */
  readonly requireAuth?: boolean;
}

export function enterAxoWorkspaceWithOptions(options?: EnterWorkspaceOptions): void {
  const auth = useAuthStore.getState();
  const store = useAppStore.getState();

  if (auth.user !== null) {
    store.setGuestEnteredApp(true);
    clearIntendedDestination();
    if (auth.user.role === "admin") {
      store.setView("admin");
      return;
    }
    if (store.active !== null) {
      store.setView("workspace");
    } else {
      store.goHome();
      restoreSavedDraftIfEmpty();
    }
    return;
  }

  const target: IntendedDestination =
    store.active !== null
      ? {
          kind: "workspace",
          preferActive: true,
          sampleId: store.activeSampleId ?? undefined,
          createdAt: Date.now(),
        }
      : { kind: "home", createdAt: Date.now() };

  const requiresAuth =
    options?.requireAuth !== undefined
      ? options.requireAuth
      : true;

  if (requiresAuth) {
    saveIntendedDestination(target);
    store.setGuestEnteredApp(false);
    store.setView("login");
    return;
  }

  store.setGuestEnteredApp(true);
  if (store.active !== null) {
    store.setView("workspace");
  } else {
    store.goHome();
    restoreSavedDraftIfEmpty();
  }
}

export function enterAxoWorkspace(): void {
  enterAxoWorkspaceWithOptions();
}

export function openLibraryFromLanding(): void {
  const store = useAppStore.getState();
  store.setGuestEnteredApp(true);
  store.openLibrary();
}

export function openSampleInWorkspace(sampleId: string): void {
  const store = useAppStore.getState();
  store.setGuestEnteredApp(true);
  const sample = geometrySampleById(sampleId) ?? GEOMETRY_SAMPLES[0];
  if (sample) {
    store.loadEnvelope(sample.envelope, sample.id, sample.problemText);
  } else {
    store.openLibrary();
  }
}
