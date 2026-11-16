import { useEffect, useRef, useState, type ReactNode } from "react";

export type AnnotationVariant = "circle" | "underline" | "highlight";

export interface AnnotatedPhraseProps {
  readonly variant: AnnotationVariant;
  readonly children: ReactNode;
  readonly active?: boolean;
  readonly className?: string;
}

const VARIANT_GEOMETRY: Record<
  AnnotationVariant,
  {
    readonly viewBox: string;
    readonly pathD: string;
    readonly secondaryD?: string;
    readonly planePoints?: string;
  }
> = {
  circle: {
    viewBox: "0 0 368 184",
    pathD:
      "M 330 38 C 278 10, 98 6, 32 38 C 4 54, 4 134, 56 156 C 138 178, 304 166, 348 112 C 364 84, 346 26, 258 14",
  },
  underline: {
    viewBox: "0 0 280 22",
    pathD: "M 5 12 Q 140 7 275 12",
    secondaryD: "M 5 8 L 5 16 M 275 8 L 275 16",
  },
  highlight: {
    viewBox: "0 0 320 120",
    planePoints: "10,16 312,10 306,106 4,112",
    pathD: "M 10 16 L 312 10 L 306 106 L 4 112 Z",
    secondaryD:
      "M 6 16 L 14 16 M 10 12 L 10 20 M 308 10 L 316 10 M 312 6 L 312 14 M 302 106 L 310 106 M 306 102 L 306 110 M 0 112 L 8 112 M 4 108 L 4 116",
  },
};

export function AnnotatedPhrase({
  variant,
  children,
  active = true,
  className,
}: AnnotatedPhraseProps) {
  const rootRef = useRef<HTMLSpanElement | null>(null);
  const [enteredViewport, setEnteredViewport] = useState(true);

  useEffect(() => {
    if (!active || typeof window === "undefined") return;
    const reduced = Boolean(
      window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches,
    );
    if (reduced) {
      setEnteredViewport(true);
      return;
    }

    const el = rootRef.current;
    if (!el || typeof IntersectionObserver === "undefined") {
      setEnteredViewport(true);
      return;
    }

    const rect = el.getBoundingClientRect();
    if (rect.top <= window.innerHeight * 0.94 && rect.bottom >= 0) {
      setEnteredViewport(true);
      return;
    }

    setEnteredViewport(false);
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setEnteredViewport(true);
          io.disconnect();
        }
      },
      { threshold: 0.12 },
    );
    io.observe(el);
    return () => {
      io.disconnect();
    };
  }, [active]);

  const geometry = VARIANT_GEOMETRY[variant];
  const isActive = active && enteredViewport;
  const stateClass = isActive ? "is-active" : "is-pending";
  const classes = [
    "axo-v14-anno",
    `axo-v14-anno-${variant}`,
    stateClass,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span ref={rootRef} className={classes}>
      <span className="axo-v14-anno-text">{children}</span>
      <svg
        className={`axo-v14-anno-svg axo-v14-anno-svg-${variant}`}
        viewBox={geometry.viewBox}
        preserveAspectRatio="none"
        aria-hidden="true"
        focusable="false"
      >
        {geometry.planePoints ? (
          <polygon
            className="axo-v14-anno-plane"
            points={geometry.planePoints}
          />
        ) : null}
        <path
          className={`axo-v14-anno-path axo-v14-anno-path-${variant}`}
          d={geometry.pathD}
          pathLength={1}
        />
        {geometry.secondaryD ? (
          <path className="axo-v14-anno-node" d={geometry.secondaryD} />
        ) : null}
      </svg>
    </span>
  );
}
