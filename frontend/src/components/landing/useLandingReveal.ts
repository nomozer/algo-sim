import { useEffect, useRef, useState } from "react";

export type LandingRevealState = "static" | "pending" | "revealed";

/**
 * Progressive-enhancement scroll reveal for Landing sections.
 * - SSR and no-JS environments render at `"static"` (fully visible).
 * - Respects `prefers-reduced-motion: reduce` (stays `"revealed"` immediately).
 * - Uses IntersectionObserver with a scroll fallback so content can never stay hidden.
 */
export function useLandingReveal<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);
  const [revealState, setRevealState] = useState<LandingRevealState>("static");

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof window === "undefined") return;

    const reduced = Boolean(
      window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches,
    );
    if (reduced || typeof IntersectionObserver === "undefined") {
      setRevealState("revealed");
      return;
    }

    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight * 0.94) {
      setRevealState("revealed");
      return;
    }

    setRevealState("pending");

    let revealed = false;
    const markRevealed = () => {
      if (revealed) return;
      revealed = true;
      setRevealState("revealed");
    };

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting || entry.boundingClientRect.top < window.innerHeight * 0.94) {
            markRevealed();
            observer.disconnect();
            break;
          }
        }
      },
      { threshold: 0.08, rootMargin: "0px 0px -24px 0px" },
    );
    observer.observe(el);

    const onScrollFallback = () => {
      if (revealed) return;
      const box = el.getBoundingClientRect();
      if (box.top < window.innerHeight * 0.96) {
        markRevealed();
        observer.disconnect();
      }
    };

    window.addEventListener("scroll", onScrollFallback, { passive: true });
    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", onScrollFallback);
    };
  }, []);

  return { ref, revealState } as const;
}
