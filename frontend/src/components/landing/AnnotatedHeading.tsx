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
      "M 334 38 C 278 14, 96 12, 28 38 C 4 58, 4 138, 56 162 C 138 179, 308 169, 350 116 C 364 86, 348 26, 260 16",
  },
  underline: {
    viewBox: "0 0 280 22",
    pathD: "M 5 12 Q 140 7 275 12",
    secondaryD: "M 5 8 L 5 16 M 275 8 L 275 16",
  },
  highlight: {
    viewBox: "0 0 320 120",
    planePoints: "10,10 312,6 306,110 4,114",
    pathD: "M 10 10 L 312 6 L 306 110 L 4 114 Z",
    secondaryD:
      "M 6 10 L 14 10 M 10 6 L 10 14 M 308 6 L 316 6 M 312 2 L 312 10 M 302 110 L 310 110 M 306 106 L 306 114 M 0 114 L 8 114 M 4 110 L 4 118",
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
