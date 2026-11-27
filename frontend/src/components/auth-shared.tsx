import { useState } from "react";

/* ── Shared Eye Toggle Icon (HTML V2.7 P4.1) ─────────────────────────────── */

export function PwToggleButton({
  id,
  targetId,
  shown,
  onToggle,
}: {
  id: string;
  targetId: string;
  shown: boolean;
  onToggle: () => void;
}) {
  const [justClicked, setJustClicked] = useState(false);
  const label = shown ? "Ẩn mật khẩu" : "Hiện mật khẩu";
  return (
    <button
      type="button"
      className="btn-pw-toggle"
      id={id}
      data-pw-target={targetId}
      data-just-clicked={justClicked ? "1" : undefined}
      aria-label={label}
      aria-pressed={shown}
      onMouseDown={() => setJustClicked(true)}
      onMouseLeave={() => setJustClicked(false)}
      onBlur={() => setJustClicked(false)}
      onClick={onToggle}
    >
      {shown ? (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49" />
          <path d="M14.084 14.158a3 3 0 0 1-4.242-4.242" />
          <path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143" />
          <path d="m2 2 20 20" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      )}
      <span className="pw-toggle-tooltip" role="tooltip">
        {label}
      </span>
    </button>
  );
}


export function AuthInlineAlertIcon() {
  return (
    <svg
      className="auth-inline-icon"
      viewBox="0 0 16 16"
      width="14"
      height="14"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="8" cy="8" r="6.25" />
      <path d="M8 5.2v3.3" />
      <circle cx="8" cy="11" r="0.6" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function AuthInfoIcon() {
  return (
    <svg
      className="auth-inline-icon"
      viewBox="0 0 20 20"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="10" cy="10" r="7.5" />
      <path d="M10 9v4.2" />
      <circle cx="10" cy="6.4" r="0.7" fill="currentColor" stroke="none" />
    </svg>
  );
}

