import type { ReactNode } from "react";

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
    viewBox: "0 0 320 136",
    pathD:
      "M 278 40 C 232 14, 86 14, 28 46 C -2 64, 14 108, 82 120 C 166 134, 284 118, 302 74 C 312 50, 282 28, 224 22",
  },
  underline: {
    viewBox: "0 0 280 22",
    pathD: "M 5 12 Q 140 7 275 12",
    secondaryD: "M 5 7 L 5 17 M 275 7 L 275 17",
  },
  highlight: {
    viewBox: "0 0 300 104",
    planePoints: "10,16 292,8 286,90 4,96",
    pathD: "M 10 16 L 292 8 L 286 90 L 4 96 Z",
  },
};

export function AnnotatedPhrase({
  variant,
  children,
  active = true,
  className,
}: AnnotatedPhraseProps) {
  const geometry = VARIANT_GEOMETRY[variant];
  const stateClass = active ? "is-active" : "is-pending";
  const classes = [
    "axo-v14-anno",
    `axo-v14-anno-${variant}`,
    stateClass,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={classes}>
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
