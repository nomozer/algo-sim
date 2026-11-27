import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FocusEvent as ReactFocusEvent,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { useAuthStore } from "../../state/auth";
import { enterAxoWorkspace } from "./landing-geometry-data";

export const HERO_SCENE_DWELL_MS = 6000;

export function nextHeroSceneIndex(
  current: number,
  total: number = HERO_SCENES.length,
): number {
  return total > 0 ? (current + 1) % total : 0;
}

export interface HeroSceneSpec {
  readonly id: "dodecahedron" | "cylinder-section" | "dihedral-planes";
  readonly svgId: string;
  readonly label: string;
}

export const HERO_SCENES: readonly HeroSceneSpec[] = [
  {
    id: "dodecahedron",
    svgId: "hero-scene-dodecahedron",
    label: "Khối thập nhị diện đều ngoại tiếp trong không gian",
  },
  {
    id: "cylinder-section",
    svgId: "hero-scene-cylinder-section",
    label: "Mặt phẳng cắt khối trụ tạo thiết diện elip",
  },
  {
    id: "dihedral-planes",
    svgId: "hero-scene-dihedral-planes",
    label: "Hai mặt phẳng cắt nhau và góc nhị diện theo giao tuyến Δ",
  },
];

function renderSceneSvg(scene: HeroSceneSpec) {
  if (scene.id === "dodecahedron") {
    return (
      <svg
        id={scene.svgId}
        className="axo-hero-scene-svg"
        viewBox="54 42 372 336"
        fill="none"
        aria-hidden="true"
        focusable="false"
      >
        <path
          className="axo-geo-face-soft"
          d="M265.9 342.4 L272.3 361.0 L352.0 294.0 L394.8 234.1 L341.6 263.9 Z M128.0 126.0 L85.2 185.9 L107.4 294.2 L163.9 301.1 L176.7 197.1 Z M265.9 342.4 L163.9 301.1 L107.4 294.2 L174.3 331.2 L272.3 361.0 Z M341.6 263.9 L394.8 234.1 L372.6 125.8 L305.7 88.8 L286.5 174.2 Z"
        />
        <path
          className="axo-geo-face-tint"
          d="M305.7 88.8 L207.7 59.0 L128.0 126.0 L176.7 197.1 L286.5 174.2 Z"
        />
        <path
          className="axo-geo-face-tint-strong"
          d="M176.7 197.1 L163.9 301.1 L265.9 342.4 L341.6 263.9 L286.5 174.2 Z"
        />
        <path
          className="axo-geo-edge-hidden"
          d="M193.5 245.8 L174.3 331.2 M193.5 245.8 L138.4 156.1 M193.5 245.8 L303.3 222.9 M214.1 77.6 L138.4 156.1 M214.1 77.6 L207.7 59.0 M214.1 77.6 L316.1 118.9 M352.0 294.0 L303.3 222.9 M372.6 125.8 L316.1 118.9 M138.4 156.1 L85.2 185.9 M303.3 222.9 L316.1 118.9"
        />
        <path
          className="axo-geo-edge-main"
          d="M352.0 294.0 L394.8 234.1 M352.0 294.0 L272.3 361.0 M372.6 125.8 L394.8 234.1 M372.6 125.8 L305.7 88.8 M107.4 294.2 L174.3 331.2 M107.4 294.2 L163.9 301.1 M107.4 294.2 L85.2 185.9 M128.0 126.0 L207.7 59.0 M128.0 126.0 L85.2 185.9 M128.0 126.0 L176.7 197.1 M265.9 342.4 L272.3 361.0 M286.5 174.2 L305.7 88.8 M174.3 331.2 L272.3 361.0 M207.7 59.0 L305.7 88.8 M394.8 234.1 L341.6 263.9"
        />
        <path
          className="axo-geo-accent-main"
          d="M265.9 342.4 L163.9 301.1 M265.9 342.4 L341.6 263.9 M286.5 174.2 L341.6 263.9 M286.5 174.2 L176.7 197.1 M163.9 301.1 L176.7 197.1"
        />
        <path
          className="axo-geo-vertex"
          d="M176.7 194.1 L179.7 197.1 L176.7 200.1 L173.7 197.1 Z M163.9 298.1 L166.9 301.1 L163.9 304.1 L160.9 301.1 Z M265.9 339.4 L268.9 342.4 L265.9 345.4 L262.9 342.4 Z M341.6 260.9 L344.6 263.9 L341.6 266.9 L338.6 263.9 Z M286.5 171.2 L289.5 174.2 L286.5 177.2 L283.5 174.2 Z"
        />
      </svg>
    );
  }

  if (scene.id === "cylinder-section") {
    return (
      <svg
        id={scene.svgId}
        className="axo-hero-scene-svg"
        viewBox="54 42 372 336"
        fill="none"
        aria-hidden="true"
        focusable="false"
      >
        <path
          className="axo-geo-edge-hidden"
          d="M189.6 88.0 L155.5 157.0 M322.7 113.4 L189.6 88.0"
        />
        <path
          className="axo-geo-face-soft"
          d="M189.6 88.0 L87.9 293.4 L290.4 332.0 L392.1 126.6 Z"
        />
        <path
          className="axo-geo-body-mask"
          d="M155.9 329.2 L156.1 331.3 L156.7 333.4 L157.6 335.6 L158.8 337.7 L160.4 339.7 L162.3 341.7 L164.6 343.7 L167.2 345.6 L170.1 347.4 L173.3 349.2 L176.8 350.8 L180.6 352.4 L184.6 353.8 L188.8 355.2 L193.3 356.5 L198.0 357.6 L202.8 358.6 L207.8 359.5 L213.0 360.3 L218.2 360.9 L223.6 361.4 L229.0 361.7 L234.5 361.9 L240.0 362.0 L245.5 361.9 L251.0 361.7 L256.4 361.4 L261.8 360.9 L267.0 360.3 L272.2 359.5 L277.2 358.6 L282.0 357.6 L286.7 356.5 L291.2 355.2 L295.4 353.8 L299.4 352.4 L303.2 350.8 L306.7 349.2 L309.9 347.4 L312.8 345.6 L315.4 343.7 L317.7 341.7 L319.6 339.7 L321.2 337.7 L322.4 335.6 L323.3 333.4 L323.9 331.3 L324.1 329.2 L324.1 90.8 L323.9 93.0 L323.3 95.1 L322.4 97.3 L321.2 99.3 L319.6 101.4 L317.7 103.4 L315.4 105.4 L312.8 107.3 L309.9 109.1 L306.7 110.8 L303.2 112.5 L299.4 114.1 L295.4 115.5 L291.2 116.9 L286.7 118.2 L282.0 119.3 L277.2 120.3 L272.2 121.2 L267.0 121.9 L261.8 122.6 L256.4 123.1 L251.0 123.4 L245.5 123.6 L240.0 123.7 L234.5 123.6 L229.0 123.4 L223.6 123.1 L218.2 122.6 L213.0 121.9 L207.8 121.2 L202.8 120.3 L198.0 119.3 L193.3 118.2 L188.8 116.9 L184.6 115.5 L180.6 114.1 L176.8 112.5 L173.3 110.8 L170.1 109.1 L167.2 107.3 L164.6 105.4 L162.3 103.4 L160.4 101.4 L158.8 99.3 L157.6 97.3 L156.7 95.1 L156.1 93.0 L155.9 90.8 Z"
        />
        <path
          className="axo-geo-face-soft"
          d="M203.2 120.4 L208.2 121.2 L213.3 122.0 L218.6 122.6 L224.0 123.1 L229.4 123.4 L234.9 123.6 L240.4 123.7 L245.9 123.6 L251.3 123.4 L256.8 123.0 L262.1 122.5 L267.4 121.9 L272.5 121.1 L277.5 120.2 L282.3 119.2 L287.0 118.1 L291.5 116.8 L295.7 115.4 L299.7 114.0 L303.4 112.4 L306.9 110.7 L310.1 109.0 L313.0 107.1 L315.5 105.2 L317.8 103.3 L319.7 101.3 L321.3 99.2 L322.5 97.1 L323.4 95.0 L323.9 92.8 L324.1 90.7 L323.9 88.6 L323.3 86.4 L322.4 84.3 L321.1 82.2 L319.5 80.2 L317.5 78.1 L315.2 76.2 L312.6 74.3 L309.7 72.5 L306.5 70.7 L303.0 69.1 L299.2 67.5 L295.1 66.1 L290.9 64.7 L286.4 63.5 L281.7 62.3 L276.8 61.3 L271.8 60.4 L266.7 59.7 L261.4 59.1 L256.0 58.6 L250.6 58.3 L245.1 58.1 L239.6 58.0 L234.1 58.1 L228.7 58.3 L223.2 58.7 L217.9 59.2 L212.6 59.8 L207.5 60.6 L202.5 61.5 L197.7 62.5 L193.0 63.6 L188.5 64.9 L184.3 66.2 L180.3 67.7 L176.6 69.3 L173.1 71.0 L169.9 72.7 L167.0 74.5 L164.5 76.4 L162.2 78.4 L160.3 80.4 L158.7 82.5 L157.5 84.6 L156.6 86.7 L156.1 88.8 L155.9 91.0 L156.1 93.1 L156.7 95.3 L157.6 97.4 L158.9 99.5 L160.5 101.5 L162.5 103.5 L164.8 105.5 L167.4 107.4 L170.3 109.2 L173.5 111.0 L177.0 112.6 L180.8 114.2 L184.9 115.6 L189.1 117.0 L193.6 118.2 L198.3 119.4 Z"
        />
        <path
          className="axo-geo-face-tint"
          d="M203.2 284.4 L208.2 285.2 L213.3 285.6 L218.6 285.8 L224.0 285.6 L229.4 285.1 L234.9 284.2 L240.4 283.1 L245.9 281.6 L251.3 279.9 L256.8 277.8 L262.1 275.4 L267.4 272.8 L272.5 269.9 L277.5 266.7 L282.3 263.3 L287.0 259.7 L291.5 255.8 L295.7 251.8 L299.7 247.5 L303.4 243.2 L306.9 238.6 L310.1 234.0 L313.0 229.2 L315.5 224.4 L317.8 219.5 L319.7 214.6 L321.3 209.6 L322.5 204.7 L323.4 199.7 L323.9 194.8 L324.1 190.0 L323.9 185.3 L323.3 180.6 L322.4 176.1 L321.1 171.8 L319.5 167.6 L317.5 163.6 L315.2 159.7 L312.6 156.1 L309.7 152.8 L306.5 149.6 L303.0 146.8 L299.2 144.2 L295.1 141.9 L290.9 139.8 L286.4 138.1 L281.7 136.7 L276.8 135.6 L271.8 134.8 L266.7 134.4 L261.4 134.2 L256.0 134.4 L250.6 134.9 L245.1 135.8 L239.6 136.9 L234.1 138.4 L228.7 140.1 L223.2 142.2 L217.9 144.6 L212.6 147.2 L207.5 150.1 L202.5 153.3 L197.7 156.7 L193.0 160.3 L188.5 164.2 L184.3 168.2 L180.3 172.5 L176.6 176.8 L173.1 181.4 L169.9 186.0 L167.0 190.8 L164.5 195.6 L162.2 200.5 L160.3 205.4 L158.7 210.4 L157.5 215.3 L156.6 220.3 L156.1 225.2 L155.9 230.0 L156.1 234.7 L156.7 239.4 L157.6 243.9 L158.9 248.2 L160.5 252.4 L162.5 256.4 L164.8 260.3 L167.4 263.9 L170.3 267.2 L173.5 270.4 L177.0 273.2 L180.8 275.8 L184.9 278.1 L189.1 280.2 L193.6 281.9 L198.3 283.3 Z"
        />
        <path
          className="axo-geo-edge-hidden"
          d="M324.1 329.0 L323.9 326.9 L323.3 324.7 L322.4 322.6 L321.1 320.5 L319.5 318.5 L317.5 316.5 L315.2 314.5 L312.6 312.6 L309.7 310.8 L306.5 309.0 L303.0 307.4 L299.2 305.8 L295.1 304.4 L290.9 303.0 L286.4 301.8 L281.7 300.6 L276.8 299.6 L271.8 298.8 L266.7 298.0 L261.4 297.4 L256.0 296.9 L250.6 296.6 L245.1 296.4 L239.6 296.3 L234.1 296.4 L228.7 296.6 L223.2 297.0 L217.9 297.5 L212.6 298.1 L207.5 298.9 L202.5 299.8 L197.7 300.8 L193.0 301.9 L188.5 303.2 L184.3 304.6 L180.3 306.0 L176.6 307.6 L173.1 309.3 L169.9 311.0 L167.0 312.9 L164.5 314.8 L162.2 316.7 L160.3 318.7 L158.7 320.8 L157.5 322.9 L156.6 325.0 L156.1 327.2 L155.9 329.3"
        />
        <path
          className="axo-geo-axis"
          d="M240.0 329.2 L240.0 90.8 M240.0 329.2 L196.1 357.2"
        />
        <path
          className="axo-geo-edge-secondary"
          d="M229.5 335.9 L229.5 317.3 L240.0 310.6 M155.5 157.0 L87.9 293.4 M87.9 293.4 L290.4 332.0 M290.4 332.0 L392.1 126.6 M392.1 126.6 L322.7 113.4"
        />
        <path
          className="axo-geo-edge-main"
          d="M155.9 329.3 L156.1 331.4 L156.7 333.6 L157.6 335.7 L158.9 337.8 L160.5 339.8 L162.5 341.9 L164.8 343.8 L167.4 345.7 L170.3 347.5 L173.5 349.3 L177.0 350.9 L180.8 352.5 L184.9 353.9 L189.1 355.3 L193.6 356.5 L198.3 357.7 L203.2 358.7 L208.2 359.6 L213.3 360.3 L218.6 360.9 L224.0 361.4 L229.4 361.7 L234.9 361.9 L240.4 362.0 L245.9 361.9 L251.3 361.7 L256.8 361.3 L262.1 360.8 L267.4 360.2 L272.5 359.4 L277.5 358.5 L282.3 357.5 L287.0 356.4 L291.5 355.1 L295.7 353.8 L299.7 352.3 L303.4 350.7 L306.9 349.0 L310.1 347.3 L313.0 345.5 L315.5 343.6 L317.8 341.6 L319.7 339.6 L321.3 337.5 L322.5 335.4 L323.4 333.3 L323.9 331.2 L324.1 329.0 M203.2 120.4 L208.2 121.2 L213.3 122.0 L218.6 122.6 L224.0 123.1 L229.4 123.4 L234.9 123.6 L240.4 123.7 L245.9 123.6 L251.3 123.4 L256.8 123.0 L262.1 122.5 L267.4 121.9 L272.5 121.1 L277.5 120.2 L282.3 119.2 L287.0 118.1 L291.5 116.8 L295.7 115.4 L299.7 114.0 L303.4 112.4 L306.9 110.7 L310.1 109.0 L313.0 107.1 L315.5 105.2 L317.8 103.3 L319.7 101.3 L321.3 99.2 L322.5 97.1 L323.4 95.0 L323.9 92.8 L324.1 90.7 L323.9 88.6 L323.3 86.4 L322.4 84.3 L321.1 82.2 L319.5 80.2 L317.5 78.1 L315.2 76.2 L312.6 74.3 L309.7 72.5 L306.5 70.7 L303.0 69.1 L299.2 67.5 L295.1 66.1 L290.9 64.7 L286.4 63.5 L281.7 62.3 L276.8 61.3 L271.8 60.4 L266.7 59.7 L261.4 59.1 L256.0 58.6 L250.6 58.3 L245.1 58.1 L239.6 58.0 L234.1 58.1 L228.7 58.3 L223.2 58.7 L217.9 59.2 L212.6 59.8 L207.5 60.6 L202.5 61.5 L197.7 62.5 L193.0 63.6 L188.5 64.9 L184.3 66.2 L180.3 67.7 L176.6 69.3 L173.1 71.0 L169.9 72.7 L167.0 74.5 L164.5 76.4 L162.2 78.4 L160.3 80.4 L158.7 82.5 L157.5 84.6 L156.6 86.7 L156.1 88.8 L155.9 91.0 L156.1 93.1 L156.7 95.3 L157.6 97.4 L158.9 99.5 L160.5 101.5 L162.5 103.5 L164.8 105.5 L167.4 107.4 L170.3 109.2 L173.5 111.0 L177.0 112.6 L180.8 114.2 L184.9 115.6 L189.1 117.0 L193.6 118.2 L198.3 119.4 Z M155.9 329.2 L155.9 90.8 M324.1 329.2 L324.1 90.8"
        />
        <path
          className="axo-geo-accent-hidden"
          d="M324.1 190.0 L323.9 185.3 L323.3 180.6 L322.4 176.1 L321.1 171.8 L319.5 167.6 L317.5 163.6 L315.2 159.7 L312.6 156.1 L309.7 152.8 L306.5 149.6 L303.0 146.8 L299.2 144.2 L295.1 141.9 L290.9 139.8 L286.4 138.1 L281.7 136.7 L276.8 135.6 L271.8 134.8 L266.7 134.4 L261.4 134.2 L256.0 134.4 L250.6 134.9 L245.1 135.8 L239.6 136.9 L234.1 138.4 L228.7 140.1 L223.2 142.2 L217.9 144.6 L212.6 147.2 L207.5 150.1 L202.5 153.3 L197.7 156.7 L193.0 160.3 L188.5 164.2 L184.3 168.2 L180.3 172.5 L176.6 176.8 L173.1 181.4 L169.9 186.0 L167.0 190.8 L164.5 195.6 L162.2 200.5 L160.3 205.4 L158.7 210.4 L157.5 215.3 L156.6 220.3 L156.1 225.2 L155.9 230.0"
        />
        <path
          className="axo-geo-accent-main"
          d="M155.9 230.0 L156.1 234.7 L156.7 239.4 L157.6 243.9 L158.9 248.2 L160.5 252.4 L162.5 256.4 L164.8 260.3 L167.4 263.9 L170.3 267.2 L173.5 270.4 L177.0 273.2 L180.8 275.8 L184.9 278.1 L189.1 280.2 L193.6 281.9 L198.3 283.3 L203.2 284.4 L208.2 285.2 L213.3 285.6 L218.6 285.8 L224.0 285.6 L229.4 285.1 L234.9 284.2 L240.4 283.1 L245.9 281.6 L251.3 279.9 L256.8 277.8 L262.1 275.4 L267.4 272.8 L272.5 269.9 L277.5 266.7 L282.3 263.3 L287.0 259.7 L291.5 255.8 L295.7 251.8 L299.7 247.5 L303.4 243.2 L306.9 238.6 L310.1 234.0 L313.0 229.2 L315.5 224.4 L317.8 219.5 L319.7 214.6 L321.3 209.6 L322.5 204.7 L323.4 199.7 L323.9 194.8 L324.1 190.0"
        />
        <path
          className="axo-geo-vertex"
          d="M240.0 88.3 L242.5 90.8 L240.0 93.3 L237.5 90.8 Z M240.0 207.2 L242.8 210.0 L240.0 212.8 L237.2 210.0 Z M240.0 326.7 L242.5 329.2 L240.0 331.7 L237.5 329.2 Z"
        />
      </svg>
    );
  }

  return (
    <svg
      id={scene.svgId}
      className="axo-hero-scene-svg"
      viewBox="54 42 372 336"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <path
        className="axo-geo-face-soft"
        d="M275.3 176.7 L71.0 222.5 L204.7 299.2 L409.0 253.4 Z"
      />
      <path
        className="axo-geo-face-tint"
        d="M226.3 274.9 L152.5 68.4 L286.3 145.1 L360.0 351.6 Z"
      />
      <path
        className="axo-geo-edge-hidden"
        d="M275.3 176.7 L197.4 194.2 M302.9 192.6 L275.3 176.7 M226.3 274.9 L197.3 193.6 M250.5 288.8 L226.3 274.9"
      />
      <path
        className="axo-geo-face-tint-strong"
        d="M264.3 232.5 L217.3 243.0 L217.3 241.1 L217.4 239.1 L217.6 237.1 L217.8 235.1 L218.2 233.0 L218.5 231.0 L219.0 229.0 L219.5 227.0 L220.1 225.0 L220.7 223.0 L221.4 221.0 L222.2 219.1 L223.0 217.1 L223.9 215.2 L224.8 213.3 L225.8 211.5 L226.9 209.6 L228.0 207.8 L229.1 206.1 L230.4 204.3 L231.6 202.6 L232.9 201.0 L234.3 199.4 L235.7 197.9 L237.1 196.4 L238.6 194.9 L240.1 193.5 L241.7 192.2 L243.3 190.9 L244.9 189.7 L246.6 188.6 L248.2 187.5 Z"
      />
      <path
        className="axo-geo-edge-main"
        d="M197.4 194.2 L71.0 222.5 M71.0 222.5 L204.7 299.2 M204.7 299.2 L409.0 253.4 M409.0 253.4 L302.9 192.6 M197.3 193.6 L152.5 68.4 M152.5 68.4 L286.3 145.1 M286.3 145.1 L360.0 351.6 M360.0 351.6 L250.5 288.8"
      />
      <path
        className="axo-geo-edge-secondary"
        d="M264.3 232.5 L163.8 255.0 M264.3 232.5 L229.9 136.2 M246.5 236.5 L257.6 242.9 L275.5 238.9 M258.2 215.4 L269.4 221.8 L275.5 238.9"
      />
      <path
        className="axo-geo-accent-main"
        d="M194.4 192.4 L334.2 272.6 M217.3 243.0 L217.3 241.1 L217.4 239.1 L217.6 237.1 L217.8 235.1 L218.2 233.0 L218.5 231.0 L219.0 229.0 L219.5 227.0 L220.1 225.0 L220.7 223.0 L221.4 221.0 L222.2 219.1 L223.0 217.1 L223.9 215.2 L224.8 213.3 L225.8 211.5 L226.9 209.6 L228.0 207.8 L229.1 206.1 L230.4 204.3 L231.6 202.6 L232.9 201.0 L234.3 199.4 L235.7 197.9 L237.1 196.4 L238.6 194.9 L240.1 193.5 L241.7 192.2 L243.3 190.9 L244.9 189.7 L246.6 188.6 L248.2 187.5"
      />
      <path
        className="axo-geo-vertex"
        d="M264.3 229.3 L267.5 232.5 L264.3 235.7 L261.1 232.5 Z M163.8 252.5 L166.3 255.0 L163.8 257.5 L161.3 255.0 Z M229.9 133.7 L232.4 136.2 L229.9 138.7 L227.4 136.2 Z"
      />
      <text className="axo-geo-label" x="100" y="224.9">α</text>
      <text className="axo-geo-label-accent" x="181.9" y="72.3">β</text>
      <text className="axo-geo-label-accent" x="345.0" y="285.0">Δ</text>
    </svg>
  );
}

export function LandingHeroV14() {
  const user = useAuthStore((s) => s.user);
  const [activeIndex, setActiveIndex] = useState(0);
  const [userPaused, setUserPaused] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isFocusWithin, setIsFocusWithin] = useState(false);
  const [isTabHidden, setIsTabHidden] = useState(false);
  const [isInViewport, setIsInViewport] = useState(true);

  const showcaseRef = useRef<HTMLDivElement | null>(null);
  const mediaLayerRef = useRef<HTMLDivElement | null>(null);
  const parallaxRafRef = useRef<number | null>(null);

  const activeScene = HERO_SCENES[activeIndex] ?? HERO_SCENES[0];
  const shouldAutoplay =
    !userPaused &&
    !reducedMotion &&
    !isHovered &&
    !isFocusWithin &&
    !isTabHidden &&
    isInViewport;

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mql = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const sync = () => setReducedMotion(Boolean(mql?.matches));
    sync();
    mql?.addEventListener?.("change", sync);
    return () => mql?.removeEventListener?.("change", sync);
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const syncVisibility = () => {
      setIsTabHidden(document.visibilityState === "hidden");
    };
    syncVisibility();
    document.addEventListener("visibilitychange", syncVisibility);
    return () => document.removeEventListener("visibilitychange", syncVisibility);
  }, []);

  useEffect(() => {
    const el = showcaseRef.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.target === el) {
            setIsInViewport(entry.isIntersecting && entry.intersectionRatio >= 0.1);
          }
        }
      },
      { threshold: [0, 0.1, 0.25] },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!shouldAutoplay || typeof window === "undefined") return;
    const timer = window.setTimeout(() => {
      setActiveIndex((prev) => nextHeroSceneIndex(prev));
    }, HERO_SCENE_DWELL_MS);
    return () => window.clearTimeout(timer);
  }, [shouldAutoplay, activeIndex]);

  const applyParallax = useCallback((nx: number, ny: number) => {
    if (mediaLayerRef.current) {
      mediaLayerRef.current.style.transform = `translate3d(${(nx * 4.0).toFixed(2)}px, ${(ny * 3.0).toFixed(2)}px, 0)`;
    }
  }, []);

  const resetParallax = useCallback(() => {
    if (parallaxRafRef.current !== null && typeof cancelAnimationFrame === "function") {
      cancelAnimationFrame(parallaxRafRef.current);
      parallaxRafRef.current = null;
    }
    showcaseRef.current?.removeAttribute("data-pointer-active");
    if (mediaLayerRef.current) {
      mediaLayerRef.current.style.transform = "";
    }
  }, []);

  useEffect(() => {
    if (reducedMotion) {
      resetParallax();
    }
  }, [reducedMotion, resetParallax]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.addEventListener("blur", resetParallax);
    return () => {
      window.removeEventListener("blur", resetParallax);
      if (parallaxRafRef.current !== null && typeof cancelAnimationFrame === "function") {
        cancelAnimationFrame(parallaxRafRef.current);
        parallaxRafRef.current = null;
      }
    };
  }, [resetParallax]);

  const handlePointerEnter = useCallback((e: ReactPointerEvent<HTMLDivElement>) => {
    if (e.pointerType !== "touch") {
      setIsHovered(true);
    }
  }, []);

  const handlePointerMove = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      if (reducedMotion || e.pointerType === "touch") return;
      const stage = showcaseRef.current;
      if (!stage) return;
      const rect = stage.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;
      stage.setAttribute("data-pointer-active", "true");
      const nx = Math.max(-1, Math.min(1, ((e.clientX - rect.left) / rect.width) * 2 - 1));
      const ny = Math.max(-1, Math.min(1, ((e.clientY - rect.top) / rect.height) * 2 - 1));
      if (parallaxRafRef.current !== null && typeof cancelAnimationFrame === "function") {
        cancelAnimationFrame(parallaxRafRef.current);
      }
      parallaxRafRef.current = requestAnimationFrame(() => {
        parallaxRafRef.current = null;
        applyParallax(nx, ny);
      });
    },
    [applyParallax, reducedMotion],
  );

  const handlePointerLeave = useCallback(() => {
    setIsHovered(false);
    resetParallax();
  }, [resetParallax]);

  const handleFocus = useCallback(() => {
    setIsFocusWithin(true);
  }, []);

  const handleBlur = useCallback((e: ReactFocusEvent<HTMLDivElement>) => {
    if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
      setIsFocusWithin(false);
    }
  }, []);

  const handleAboutScroll = useCallback(
    (e: ReactMouseEvent<HTMLAnchorElement>) => {
      const target = document.getElementById("about-axo");
      if (!target) return;
      e.preventDefault();
      const isReduced =
        reducedMotion ||
        (typeof window !== "undefined" &&
          Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches));
      target.scrollIntoView({ behavior: isReduced ? "auto" : "smooth", block: "start" });
    },
    [reducedMotion],
  );

  const selectManualScene = useCallback((idx: number) => {
    setActiveIndex(idx);
    setUserPaused(true);
  }, []);

  const handleDotKeyDown = useCallback(
    (e: ReactKeyboardEvent<HTMLButtonElement>, index: number) => {
      let nextIndex = -1;
      if (e.key === "ArrowRight") nextIndex = (index + 1) % HERO_SCENES.length;
      else if (e.key === "ArrowLeft") {
        nextIndex = (index - 1 + HERO_SCENES.length) % HERO_SCENES.length;
      } else if (e.key === "Home") nextIndex = 0;
      else if (e.key === "End") nextIndex = HERO_SCENES.length - 1;
      if (nextIndex < 0) return;
      e.preventDefault();
      selectManualScene(nextIndex);
      document.getElementById(`hero-scene-dot-${nextIndex}`)?.focus();
    },
    [selectManualScene],
  );

  return (
    <section
      id="landing-hero"
      className="axo-v14-hero"
      aria-labelledby="axo-v14-hero-heading"
    >
      <div className="axo-v14-hero-grid">
        <div className="axo-v14-hero-copy">
          <h1 id="axo-v14-hero-heading" className="axo-v14-hero-title">
            <span className="axo-v14-hero-title-line">Hình học không gian,</span>
            <span className="axo-v14-hero-title-line">dễ hình dung hơn.</span>
          </h1>

          <p className="axo-v14-hero-lead">
            Mô hình hóa bài toán tiếng Việt thành không gian 3D trực quan, giúp
            bạn dựng hình, xoay góc nhìn và quan sát từng mặt cắt rõ ràng.
          </p>

          <div className="axo-v14-hero-actions">
            <button
              id="btn-landing-hero-start"
              type="button"
              className="axo-v14-btn axo-v14-btn-primary"
              onClick={enterAxoWorkspace}
            >
              {user ? "Vào ứng dụng" : "Bắt đầu dựng hình"}
            </button>
            <a
              id="btn-landing-hero-about"
              href="#about-axo"
              className="axo-v14-btn axo-v14-btn-secondary"
              onClick={handleAboutScroll}
            >
              Tìm hiểu về Axo
            </a>
          </div>
        </div>

        <div
          id="landing-hero-sculpture"
          ref={showcaseRef}
          className="axo-hero-showcase"
          data-hero-mode="automatic-geometric-showcase"
          data-active-scene={activeScene.id}
          data-paused={String(!shouldAutoplay)}
          onPointerEnter={handlePointerEnter}
          onPointerMove={handlePointerMove}
          onPointerLeave={handlePointerLeave}
          onPointerCancel={handlePointerLeave}
          onFocus={handleFocus}
          onBlur={handleBlur}
        >
          <div
            id="hero-showcase-stage"
            className="axo-hero-showcase-stage"
            role="img"
            aria-label={activeScene.label}
          >
            <div ref={mediaLayerRef} className="axo-hero-showcase-media">
              {HERO_SCENES.map((scene, idx) => {
                const isActive = idx === activeIndex;
                return (
                  <div
                    key={scene.id}
                    className={`axo-hero-scene-layer${isActive ? " is-active" : ""}`}
                    aria-hidden={!isActive}
                  >
                    {renderSceneSvg(scene)}
                  </div>
                );
              })}
            </div>
          </div>

          <div
            className="axo-hero-showcase-controls"
            role="group"
            aria-label="Điều khiển trình diễn hình học"
          >
            {HERO_SCENES.map((scene, idx) => {
              const selected = idx === activeIndex;
              return (
                <button
                  key={scene.id}
                  id={`hero-scene-dot-${idx}`}
                  type="button"
                  className={`axo-hero-dot-btn${selected ? " is-active" : ""}`}
                  aria-label={`Cảnh ${idx + 1}: ${scene.label}`}
                  aria-pressed={selected}
                  onClick={() => selectManualScene(idx)}
                  onKeyDown={(e) => handleDotKeyDown(e, idx)}
                >
                  <span className="axo-hero-dot-pill" aria-hidden="true" />
                </button>
              );
            })}

            <button
              id="hero-scene-toggle"
              type="button"
              className="axo-hero-toggle-btn"
              aria-label={
                userPaused
                  ? "Tiếp tục chuyển cảnh hình học"
                  : "Tạm dừng chuyển cảnh hình học"
              }
              aria-pressed={userPaused}
              onClick={() => setUserPaused((prev) => !prev)}
            >
              {userPaused ? (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 16 16"
                  fill="none"
                  aria-hidden="true"
                  focusable="false"
                >
                  <path d="M5 3.5L12.5 8L5 12.5V3.5Z" fill="currentColor" />
                </svg>
              ) : (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 16 16"
                  fill="none"
                  aria-hidden="true"
                  focusable="false"
                >
                  <path
                    d="M5.5 3.5V12.5M10.5 3.5V12.5"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
