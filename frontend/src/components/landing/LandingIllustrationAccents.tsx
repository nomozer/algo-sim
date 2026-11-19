/**
 * Purposeful, lightweight geometric line-art accents reinforcing Axo's
 * spatial drafting grammar across Storytelling & Closing sections.
 * Styled exclusively via classes in landing.css (zero CSS variables in TSX).
 */
export function StoryBridgeAccent() {
  return (
    <svg
      className="axo-sp-accent-bridge"
      viewBox="0 0 120 36"
      fill="none"
      aria-hidden="true"
    >
      <path d="M4 28 L34 8 L76 14 L114 4" className="axo-sp-accent-stroke-muted" />
      <path d="M18 32 L54 12 L92 22" className="axo-sp-accent-stroke-blue" />
      <circle cx="34" cy="8" r="2.6" className="axo-sp-accent-node-blue" />
      <circle cx="76" cy="14" r="2.6" className="axo-sp-accent-node-amber" />
    </svg>
  );
}

export function FinalCtaCornerAccent() {
  return (
    <svg
      className="axo-sp-accent-corner"
      viewBox="0 0 140 140"
      fill="none"
      aria-hidden="true"
    >
      <polygon points="70,14 122,44 70,74 18,44" className="axo-sp-accent-plane" />
      <polygon points="18,44 70,74 70,126 18,96" className="axo-sp-accent-stroke-muted" />
      <line x1="70" y1="14" x2="122" y2="96" className="axo-sp-accent-stroke-dashed" />
      <circle cx="70" cy="74" r="3.2" className="axo-sp-accent-node-amber" />
    </svg>
  );
}
