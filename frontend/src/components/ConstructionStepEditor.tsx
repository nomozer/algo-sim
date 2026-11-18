import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import {
  COMPACT_MATH_TOKEN_RE,
  MathDisplay,
} from "../simulations/domains/geometry/scene3d-view";

const useIsomorphicLayoutEffect =
  typeof window !== "undefined" ? useLayoutEffect : useEffect;

export const STEP_TEXTAREA_MIN_HEIGHT_PX = 32;
export const STEP_TEXTAREA_MAX_HEIGHT_PX = 144;

const STEP_TITLE_CONNECTOR_RE_SRC =
  "(?:cạnh|của|với|qua|tại|và|đến|thuộc|trên|bởi|đỉnh|điểm|tâm|đoạn|trục|đáy|mặt|khối|tia|góc|bán\\s+kính|hình\\s+chóp|thẳng)";
const STEP_TITLE_SHORT_SYM_RE_SRC =
  "(?:\\([A-ZĐα-ω0-9′'°]{1,8}\\)|[A-ZĐ][A-ZĐ0-9′']{0,5}(?:\\.[A-ZĐ0-9′']{1,6})?)";
const STEP_TITLE_STANDALONE_SYM_RE_SRC =
  "(?:\\([A-ZĐα-ω0-9′'°]{1,10}\\)|[A-ZĐ][A-ZĐ0-9′']*(?:[′']|\\.[A-ZĐ0-9′']+)[A-ZĐ0-9′']*|[A-ZĐ]{2,6}(?![\\p{L}\\p{N}]))";

const STEP_TITLE_CHUNK_RE = new RegExp(
  `(${COMPACT_MATH_TOKEN_RE.source}|(?<![\\p{L}\\p{N}])${STEP_TITLE_CONNECTOR_RE_SRC}\\s+${STEP_TITLE_SHORT_SYM_RE_SRC}(?=$|[,;.)])(?![ \\t]*(?:⊥|∥|∩|=|≤|≥|≠))|${STEP_TITLE_STANDALONE_SYM_RE_SRC})`,
  "gu",
);

export function StepTitleText({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  STEP_TITLE_CHUNK_RE.lastIndex = 0;
  let match: RegExpExecArray | null;
  let keyIdx = 0;

  while ((match = STEP_TITLE_CHUNK_RE.exec(text)) !== null) {
    const start = match.index;
    const token = match[0];
    if (start > lastIndex) {
      parts.push(
        <MathDisplay
          key={`txt-${keyIdx++}`}
          text={text.slice(lastIndex, start)}
        />,
      );
    }
    const isRelational = new RegExp(`^(?:${COMPACT_MATH_TOKEN_RE.source})$`, "u").test(
      token,
    );
    if (isRelational) {
      parts.push(<MathDisplay key={`rel-${keyIdx++}`} text={token} />);
    } else {
      parts.push(
        <span key={`wrap-${keyIdx++}`} className="math-nowrap">
          <MathDisplay text={token} />
        </span>,
      );
    }
    lastIndex = start + token.length;
  }

  if (lastIndex < text.length) {
    parts.push(<MathDisplay key={`tail-${keyIdx++}`} text={text.slice(lastIndex)} />);
  }

  return <>{parts}</>;
}

export function syncStepTextareaHeight(
  el: HTMLTextAreaElement,
  minH = STEP_TEXTAREA_MIN_HEIGHT_PX,
  maxH = STEP_TEXTAREA_MAX_HEIGHT_PX,
): { heightPx: number; scrollable: boolean } {
  const scrollHost =
    typeof el.closest === "function" ? el.closest<HTMLElement>(".dock-scroll") : null;
  const savedHostScrollTop = scrollHost ? scrollHost.scrollTop : 0;
  const savedTaScrollTop = el.scrollTop;

  el.style.overflowX = "hidden";
  el.style.overflowY = "hidden";
  el.style.height = "auto";

  // Under box-sizing: border-box, scrollHeight excludes top/bottom borders; add them
  // so 1-2+ line content never triggers a false internal vertical scrollbar.
  let borderV = 2;
  if (typeof window !== "undefined" && typeof window.getComputedStyle === "function") {
    try {
      const cs = window.getComputedStyle(el);
      const bt = parseFloat(cs.borderTopWidth);
      const bb = parseFloat(cs.borderBottomWidth);
      if (Number.isFinite(bt) || Number.isFinite(bb)) {
        borderV = (Number.isFinite(bt) ? bt : 0) + (Number.isFinite(bb) ? bb : 0);
      }
    } catch {
      borderV = 2;
    }
  }

  const rawScrollH = el.scrollHeight;
  const needed = rawScrollH > 0 ? Math.ceil(rawScrollH + borderV) : minH;
  const heightPx = Math.min(maxH, Math.max(minH, needed));
  const scrollable = needed > maxH;

  el.style.height = `${heightPx}px`;
  el.style.overflowY = scrollable ? "auto" : "hidden";
  if (scrollable) {
    el.scrollTop = savedTaScrollTop;
  }
  if (scrollHost && scrollHost.scrollTop !== savedHostScrollTop) {
    scrollHost.scrollTop = savedHostScrollTop;
  }

  return { heightPx, scrollable };
}

export interface StepEditPencilButtonProps {
  stepNumber: number;
  disabled?: boolean;
  onStartEdit: () => void;
}

export const StepEditPencilButton: React.FC<StepEditPencilButtonProps> = ({
  stepNumber,
  disabled = false,
  onStartEdit,
}) => {
  return (
    <button
      type="button"
      className="step-edit-pencil-btn"
      aria-label={`Chỉnh sửa bước ${stepNumber}`}
      title="Chỉnh sửa bước dựng hình"
      disabled={disabled}
      onPointerDown={(e) => {
        e.stopPropagation();
      }}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!disabled) {
          onStartEdit();
        }
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          e.stopPropagation();
          if (!disabled) {
            onStartEdit();
          }
        }
      }}
    >
      <svg
        width="13"
        height="13"
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M11.5 2.5a1.768 1.768 0 0 1 2.5 2.5L5.25 13.75 2 14.5l.75-3.25L11.5 2.5z" />
      </svg>
    </button>
  );
};

export interface InlineConstructionStepEditorProps {
  stepIndex: number;
  initialValue: string;
  running: boolean;
  errorText: string | null;
  onCancel: (restoreKeyboardFocus?: boolean) => void;
  onSubmit: (draft: string) => void;
}

export const InlineConstructionStepEditor: React.FC<InlineConstructionStepEditorProps> = ({
  stepIndex,
  initialValue,
  running,
  errorText,
  onCancel,
  onSubmit,
}) => {
  const [draft, setDraft] = useState(initialValue);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const prevStepIndexRef = useRef<number>(stepIndex);

  useEffect(() => {
    if (prevStepIndexRef.current !== stepIndex) {
      prevStepIndexRef.current = stepIndex;
      setDraft(initialValue);
    }
  }, [stepIndex, initialValue]);

  useIsomorphicLayoutEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    try {
      el.focus({ preventScroll: true });
    } catch {
      el.focus();
    }
    syncStepTextareaHeight(el);
    const len = el.value.length;
    try {
      el.setSelectionRange(len, len);
    } catch {
      // Ignore selection range failures in non-browser DOM shims
    }
  }, [stepIndex]);

  useIsomorphicLayoutEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    syncStepTextareaHeight(el);
  }, [draft]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => {
      syncStepTextareaHeight(el);
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
    };
  }, [stepIndex]);

  const trimmedEmpty = draft.trim().length === 0;

  return (
    <form
      className="step-edit-form"
      onClick={(e) => e.stopPropagation()}
      onPointerDown={(e) => e.stopPropagation()}
      onKeyDown={(e) => {
        if (e.key === "Escape") {
          e.preventDefault();
          e.stopPropagation();
          onCancel(true);
          return;
        }
        if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End", " "].includes(e.key)) {
          e.stopPropagation();
        }
      }}
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!running && !trimmedEmpty) {
          onSubmit(draft);
        }
      }}
    >
      <textarea
        ref={textareaRef}
        className="step-edit-textarea"
        rows={1}
        value={draft}
        aria-label={`Nội dung bước dựng ${stepIndex + 1}`}
        disabled={running}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          e.stopPropagation();
          if (e.key === "Escape") {
            e.preventDefault();
            onCancel(true);
          } else if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            if (!running && !trimmedEmpty) {
              onSubmit(draft);
            }
          }
        }}
      />
      {errorText ? (
        <div className="step-edit-error" role="alert">
          {errorText}
        </div>
      ) : null}
      <div className="step-edit-actions">
        <button
          type="button"
          className="step-edit-btn step-edit-btn--cancel"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onCancel(e.detail === 0);
          }}
        >
          Hủy
        </button>
        <button
          type="submit"
          className="step-edit-btn step-edit-btn--run"
          disabled={running || trimmedEmpty}
        >
          {running ? (
            <>
              <span className="step-edit-spinner" aria-hidden="true" />
              <span>Đang chạy...</span>
            </>
          ) : (
            "Chạy"
          )}
        </button>
      </div>
      {running ? (
        <span className="step-edit-sr-live" aria-live="polite">
          Đang kiểm tra và dựng lại hình học bước {stepIndex + 1}...
        </span>
      ) : null}
    </form>
  );
};
