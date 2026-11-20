export function HeroPortalFallbackSvg({
  selectedId = null,
}: {
  readonly selectedId?: "construction" | "exploration" | "relationships" | null;
}) {
  return (
    <div id="v14-hero-portal-fallback" className="axo-v14-portal-fallback">
      <svg
        viewBox="0 0 560 400"
        className="axo-v14-portal-fallback-svg"
        role="img"
        aria-label="Ba cổng trải nghiệm hình học không gian Axo: Dựng hình, Quan sát 3D và Thiết diện"
      >
        <rect
          x="36"
          y="58"
          width="146"
          height="236"
          rx="16"
          className={`axo-v14-fb-card axo-v14-fb-card-light${selectedId === "construction" ? " is-active" : ""}`}
        />
        <rect
          x="207"
          y="42"
          width="146"
          height="252"
          rx="16"
          className={`axo-v14-fb-card axo-v14-fb-card-indigo${selectedId === "exploration" ? " is-active" : ""}`}
        />
        <rect
          x="378"
          y="58"
          width="146"
          height="236"
          rx="16"
          className={`axo-v14-fb-card axo-v14-fb-card-sky${selectedId === "relationships" ? " is-active" : ""}`}
        />

        {/* Portal 01 Prism ABC.A'B'C' */}
        <polygon points="109,144 68,230 150,230" className="axo-v14-fb-edge-dark" />
        <polygon points="82,188 136,188 128,214 90,214" className="axo-v14-fb-section" />

        {/* Portal 02 Cube MNEPFQ */}
        <rect x="242" y="138" width="76" height="76" className="axo-v14-fb-edge-light" />
        <polygon points="242,164 280,138 318,164 302,214 258,214" className="axo-v14-fb-section-bright" />

        {/* Portal 03 Pyramid MENPF */}
        <polygon points="451,126 404,232 498,232" className="axo-v14-fb-edge-dark" />
        <polygon points="421,188 451,166 481,188 472,216 430,216" className="axo-v14-fb-section" />
      </svg>
    </div>
  );
}
