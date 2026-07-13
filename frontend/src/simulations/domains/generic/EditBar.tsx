import { useState } from "react";
import { ADDABLE_TYPE_LABEL, type EditPolicy, type EditUiAction } from "./edit-policy";

/**
 * Thanh công cụ chỉnh sửa (M7.14D) — component RIÊNG, không phải để "cho gọn".
 *
 * Lý do kiến trúc: `editText` từng nằm cùng component với SVG → MỖI KÝ TỰ gõ
 * re-render toàn bộ sân khấu (đã đo: ~0.7 ms/render compute, nhưng vẫn là
 * reconcile ~60 phần tử SVG mỗi phím, ×2 ở StrictMode dev). Tách ra đây thì
 * gõ chỉ re-render đúng thanh này.
 *
 * Toolbar DẪN XUẤT TỪ EditPolicy — cảnh văn bản không có "Thêm điểm/Nối",
 * cảnh giá trị/logic không có công cụ cấu trúc nào.
 */

export type EditTool = "add_node" | "add_content" | "connect" | "delete" | null;

interface Props {
  policy: EditPolicy;
  tool: EditTool;
  /** Loại nội dung đang chọn cho "Thêm nội dung" (family structural). */
  contentType: string;
  connectFrom: string | null;
  busy: boolean;
  message: string | null;
  onPickTool: (tool: EditTool) => void;
  onPickContentType: (t: string) => void;
  onSubmitInstruction: (text: string) => void;
}

const ACTION_LABEL: Record<Exclude<EditUiAction, "edit_text">, string> = {
  add_node: "＋ Thêm điểm",
  add_content: "＋ Thêm nội dung",
  connect: "⌁ Nối",
  delete: "✕ Xóa",
};

/** Hướng dẫn theo công cụ đang "lên đạn" — người học luôn biết click tiếp theo làm gì. */
export function toolHint(tool: EditTool, connectFrom: string | null, contentLabel: string): string {
  switch (tool) {
    case "add_node":
      return "Bấm vào chỗ trống trên sân khấu để thêm một điểm mới. (Esc để hủy)";
    case "add_content":
      return `Bấm "Thêm ${contentLabel}" một lần nữa để chèn vào cuối cảnh, hoặc mô tả bằng lời. (Esc để hủy)`;
    case "connect":
      return connectFrom === null
        ? "Đang chờ đối tượng THỨ NHẤT — bấm vào một điểm. (Esc để hủy)"
        : `Đã chọn "${connectFrom}" — bấm đối tượng THỨ HAI để nối. (Esc để hủy)`;
    case "delete":
      return "Bấm vào đối tượng muốn xóa (cạnh chạm nó sẽ được gỡ theo). (Esc để hủy)";
    default:
      return "Chọn một công cụ, hoặc mô tả chỉnh sửa bằng lời rồi bấm Thực hiện.";
  }
}

export function EditBar({
  policy,
  tool,
  contentType,
  connectFrom,
  busy,
  message,
  onPickTool,
  onPickContentType,
  onSubmitInstruction,
}: Props) {
  // State nhập liệu sống Ở ĐÂY → gõ không đụng tới SVG.
  const [text, setText] = useState("");

  const structural = policy.family === "structural";
  const actions = policy.uiActions.filter((a): a is Exclude<EditUiAction, "edit_text"> => a !== "edit_text");
  const contentLabel = ADDABLE_TYPE_LABEL[contentType] ?? contentType;

  function submit() {
    const value = text.trim();
    if (!value || busy) return;
    onSubmitInstruction(value);
    setText("");
  }

  return (
    <div className="stack" style={{ gap: "var(--sp-xs)" }}>
      <div className="player-controls" style={{ flexWrap: "wrap", gap: 6 }}>
        {actions.length === 0 && (
          <span className="hint">
            Cảnh này không có công cụ sửa cấu trúc — {policy.note.toLowerCase()}
          </span>
        )}
        {actions.map((action) => {
          const armed = tool === action;
          const label =
            action === "add_content" ? `＋ Thêm ${contentLabel.toLowerCase()}` : ACTION_LABEL[action];
          return (
            <button
              key={action}
              className={`btn-utility${armed ? " is-active" : ""}`}
              aria-pressed={armed}
              disabled={busy}
              onClick={() => onPickTool(armed ? null : action)}
            >
              {label}
            </button>
          );
        })}
        {structural && policy.addableTypes.length > 1 && (
          <select
            value={contentType}
            disabled={busy}
            onChange={(e) => onPickContentType(e.target.value)}
            aria-label="Loại nội dung muốn thêm"
            style={{
              padding: "5px 8px",
              borderRadius: 8,
              border: "1px solid var(--ink-faint)",
              background: "var(--surface)",
              color: "var(--ink)",
            }}
          >
            {policy.addableTypes.map((t) => (
              <option key={t} value={t}>
                {ADDABLE_TYPE_LABEL[t] ?? t}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="player-controls" style={{ gap: 6 }}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder={
            structural
              ? 'Mô tả chỉnh sửa, vd: "Thêm một đoạn văn về lợi ích của mạng máy tính"'
              : 'Mô tả chỉnh sửa, vd: "Thêm điểm D và nối D với A, B"'
          }
          disabled={busy}
          style={{
            flex: 1,
            minWidth: 200,
            padding: "6px 10px",
            borderRadius: 8,
            border: "1px solid var(--ink-faint)",
            background: "var(--surface)",
            color: "var(--ink)",
          }}
        />
        <button className="btn-primary" onClick={submit} disabled={busy || !text.trim()}>
          {busy ? "Đang xử lý..." : "Thực hiện"}
        </button>
      </div>

      <div className="hint">{message ?? toolHint(tool, connectFrom, contentLabel)}</div>
    </div>
  );
}
