import React, { useEffect, useRef, useState } from "react";

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
  onCancel: () => void;
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

  useEffect(() => {
    setDraft(initialValue);
  }, [stepIndex, initialValue]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.focus();
    el.style.height = "auto";
    el.style.height = `${Math.min(220, Math.max(68, el.scrollHeight))}px`;
    const len = el.value.length;
    try {
      el.setSelectionRange(len, len);
    } catch {
      // Ignore selection range failures in non-browser DOM shims
    }
  }, [stepIndex]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(220, Math.max(68, el.scrollHeight))}px`;
  }, [draft]);

  const trimmedEmpty = draft.trim().length === 0;

  return (
    <form
      className="step-edit-form"
      onClick={(e) => e.stopPropagation()}
      onPointerDown={(e) => e.stopPropagation()}
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
        rows={3}
        value={draft}
        aria-label={`Nội dung bước dựng ${stepIndex + 1}`}
        disabled={running}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          e.stopPropagation();
          if (e.key === "Escape") {
            e.preventDefault();
            if (!running) {
              onCancel();
            }
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
          disabled={running}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!running) {
              onCancel();
            }
          }}
        >
          Hủy
        </button>
        <button
          type="submit"
          className="step-edit-btn step-edit-btn--run"
          disabled={running || trimmedEmpty}
        >
          {running ? "Đang chạy..." : "Chạy"}
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
