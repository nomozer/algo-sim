import { useId } from "react";

/**
 * Custom shaded multi-solid brand composition for the Final CTA section:
 * sliced warm-amber cylinder + frosted hexagonal prism + porcelain sphere with orbital ring.
 * Intentionally distinct from Hero Sculpture and mathematical pyramid/cube demonstrations.
 */
export function LandingClosingSculpture() {
  const uid = useId().replace(/:/g, "");

  return (
    <div className="axo-sp-closing-sculpture" aria-hidden="true">
      <svg
        className="axo-sp-closing-svg"
        viewBox="0 0 380 280"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <radialGradient id={`${uid}-glow`} cx="52%" cy="54%" r="48%">
            <stop offset="0%" stopColor="rgba(0, 117, 222, 0.14)" />
            <stop offset="65%" stopColor="rgba(217, 119, 6, 0.08)" />
            <stop offset="100%" stopColor="rgba(247, 247, 244, 0)" />
          </radialGradient>
          <linearGradient id={`${uid}-cyl`} x1="90" y1="80" x2="210" y2="236" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#faf8f3" />
            <stop offset="100%" stopColor="#e5dfd3" />
          </linearGradient>
          <linearGradient id={`${uid}-amber`} x1="100" y1="74" x2="204" y2="146" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#d97706" />
          </linearGradient>
          <linearGradient id={`${uid}-prism`} x1="205" y1="48" x2="316" y2="196" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#eef5fc" stopOpacity="0.94" />
            <stop offset="100%" stopColor="#dce9f9" stopOpacity="0.78" />
          </linearGradient>
          <radialGradient id={`${uid}-sphere`} cx="35%" cy="32%" r="68%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="70%" stopColor="#f0ece3" />
            <stop offset="100%" stopColor="#dcd6ca" />
          </radialGradient>
        </defs>

        {/* Soft architectural floor glow */}
        <ellipse cx="192" cy="154" rx="154" ry="98" fill={`url(#${uid}-glow)`} />
        <ellipse cx="186" cy="236" rx="126" ry="18" fill="rgba(17, 17, 16, 0.07)" />

        {/* Frosted hexagonal prism in right midground */}
        <polygon
          points="226,64 282,46 322,74 322,172 276,204 226,184"
          fill={`url(#${uid}-prism)`}
          stroke="rgba(30, 41, 59, 0.28)"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <polyline
          points="226,64 276,92 322,74"
          stroke="rgba(30, 41, 59, 0.26)"
          strokeWidth="1.35"
          strokeLinejoin="round"
        />
        <line x1="276" y1="92" x2="276" y2="204" stroke="rgba(30, 41, 59, 0.24)" strokeWidth="1.35" />
        {/* Translucent cutting ribbon across prism */}
        <polygon
          points="212,130 282,102 336,126 266,156"
          fill="rgba(0, 117, 222, 0.14)"
          stroke="rgba(0, 117, 222, 0.56)"
          strokeWidth="1.4"
          strokeLinejoin="round"
        />

        {/* Matte cylinder truncated cleanly with an oblique elliptical section */}
        <path
          d="M102 126 V206 C102 222 126 232 156 232 C186 232 210 222 210 206 V100 Z"
          fill={`url(#${uid}-cyl)`}
          stroke="rgba(17, 17, 16, 0.34)"
          strokeWidth="1.55"
          strokeLinejoin="round"
        />
        <ellipse
          cx="156"
          cy="113"
          rx="55.5"
          ry="24"
          transform="rotate(-14 156 113)"
          fill={`url(#${uid}-amber)`}
          stroke="#b45309"
          strokeWidth="1.7"
        />
        <ellipse
          cx="156"
          cy="113"
          rx="42"
          ry="16"
          transform="rotate(-14 156 113)"
          fill="none"
          stroke="rgba(255, 251, 235, 0.58)"
          strokeWidth="1.2"
        />

        {/* Matte porcelain sphere + equatorial orbit ring on left */}
        <circle
          cx="94"
          cy="112"
          r="25"
          fill={`url(#${uid}-sphere)`}
          stroke="rgba(17, 17, 16, 0.18)"
          strokeWidth="1.3"
        />
        <path
          d="M52 121 C52 108 136 92 136 104 C136 116 52 133 52 121 Z"
          fill="none"
          stroke="#0075de"
          strokeWidth="2.1"
        />
      </svg>
    </div>
  );
}
