import { createElement, lazy, type ComponentType, type LazyExoticComponent } from "react";

export type RetryableLazyComponent<T extends ComponentType<any>> = T & {
  preload: () => Promise<{ default: T }>;
};

const RETRY_DELAY_MS = 250;
const resetHandlers = new Set<() => void>();

export function resetFailedLazyChunks(): void {
  for (const fn of resetHandlers) {
    fn();
  }
}

/**
 * Chỉ prefetch theo ý định (hover/focus) khi người dùng không bật Data Saver
 * hoặc không đang ở mạng quá chậm (2G / slow-2g).
 */
export function shouldPrefetchOnIntent(): boolean {
  if (typeof navigator === "undefined") return false;
  const nav = navigator as Navigator & {
    connection?: { saveData?: boolean; effectiveType?: string };
  };
  const conn = nav.connection;
  if (!conn) return true;
  if (conn.saveData) return false;
  const eff = conn.effectiveType?.toLowerCase();
  return eff !== "2g" && eff !== "slow-2g";
}

export function isChunkLoadError(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  const msg = err.message.toLowerCase();
  const name = err.name.toLowerCase();
  return (
    name.includes("chunkloaderror") ||
    msg.includes("failed to fetch dynamically imported module") ||
    msg.includes("importing a module script failed") ||
    msg.includes("error loading dynamically imported module") ||
    msg.includes("loading chunk") ||
    msg.includes("loading css chunk") ||
    msg.includes("unable to preload css") ||
    msg.includes("load failed") ||
    msg.includes("networkerror")
  );
}

/**
 * Wrapper `React.lazy` có thử lại 1 lần khi mạng chập chờn và cho phép gọi `.preload()`.
 * Giữ nguyên instance `React.lazy` trong suốt chu kỳ Suspense -> ErrorBoundary để React bắt lỗi sạch,
 * và chỉ đặt lại khi gọi `resetFailedLazyChunks()` lúc người dùng bấm khôi phục.
 */
export function lazyWithRetry<T extends ComponentType<any>>(
  loader: () => Promise<{ default: T }>,
): RetryableLazyComponent<T> {
  let preloaded: Promise<{ default: T }> | null = null;
  let activeLazy: LazyExoticComponent<T> | null = null;
  let hasResolved = false;

  const loadWithRetry = async (): Promise<{ default: T }> => {
    try {
      const mod = await loader();
      hasResolved = true;
      return mod;
    } catch (firstErr) {
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
      try {
        const mod = await loader();
        hasResolved = true;
        return mod;
      } catch {
        preloaded = null;
        throw firstErr;
      }
    }
  };

  resetHandlers.add(() => {
    if (!hasResolved) {
      activeLazy = null;
      preloaded = null;
    }
  });

  function LazyRetryWrapper(props: Record<string, unknown>) {
    if (!activeLazy) {
      activeLazy = lazy(() => {
        if (preloaded) {
          const p = preloaded;
          return p.catch(() => loadWithRetry());
        }
        return loadWithRetry();
      });
    }
    const Inner = activeLazy as unknown as ComponentType<Record<string, unknown>>;
    return createElement(Inner, props);
  }

  LazyRetryWrapper.preload = () => {
    if (!preloaded) {
      preloaded = loadWithRetry().catch((err) => {
        preloaded = null;
        throw err;
      });
    }
    return preloaded;
  };

  return LazyRetryWrapper as unknown as RetryableLazyComponent<T>;
}
