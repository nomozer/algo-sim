import { useEffect, useRef, useState } from "react";
import { useAppStore } from "../state/store";
import { IconAttach, IconSend } from "./icons";
import { analyzeViaServer, fetchHealth, type ServerHealth } from "../llm/client";
import { acceptAttr, fileToPayload, kindFromFile, kindLabel } from "../llm/input";

/**
 * Nhập đề: gõ văn bản HOẶC tải tệp (.docx / .py / ảnh) — M4.
 * Mọi đầu vào chuẩn hóa thành InputPayload rồi gọi /api/analyze (một contract).
 * Việc gọi Gemini do backend đảm nhiệm (trình duyệt không giữ API key).
 *
 * M9-UX4 — MỘT DẠNG DUY NHẤT, và CHỈ SỐNG Ở TRANG CHỦ.
 * M9-UX3 từng tách hai vỏ hero/compact vì `InputPanel` (cột trái workspace) cũng
 * nhúng composer. M9-UX4 gỡ composer khỏi workspace — Trang chủ LÀ nơi phân tích
 * đề, giữ thêm một bản trong cột 270px là hai nơi làm cùng một việc. Vỏ "compact"
 * hết người dùng nên gỡ luôn, không nuôi code chết.
 *
 * M9-UX5 — HỘP nhiều dòng thay pill một dòng, nút `+` / gửi nằm ở ĐÁY hộp.
 * Hàng chip "thử đề mẫu AI" (`SAMPLE_PROMPTS`) đã GỠ: 3 đề đó trùng nội dung với
 * 3 bài mẫu ngay bên dưới Trang chủ, chỉ khác là tốn một lượt gọi API. Trang chủ
 * có ĐÚNG MỘT đường dùng AI: gõ đề của chính em. (`SAMPLE_PROMPTS` vẫn còn trong
 * `sim-samples.ts` cho dev/test — chỉ không quảng bá cho học sinh.)
 */
export function ProblemInput() {
  const problemText = useAppStore((s) => s.problemText);
  const setProblemText = useAppStore((s) => s.setProblemText);
  const analyzing = useAppStore((s) => s.analyzing);
  const analysisError = useAppStore((s) => s.analysisError);
  const [health, setHealth] = useState<ServerHealth | null | "loading">("loading");
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    let cancelled = false;
    fetchHealth().then((h) => {
      if (!cancelled) setHealth(h);
    });
    return () => {
      cancelled = true;
    };
  }, [analyzing]);

  // Có tệp → gửi tệp; không thì gửi văn bản (≥10 ký tự)
  const canAnalyze = !analyzing && (file !== null || problemText.trim().length >= 10);

  // Pill cao dần theo nội dung (tới ~6 dòng). DOM thuần, không state, không store.
  function autoGrow(el: HTMLTextAreaElement) {
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 148)}px`;
  }

  function onChangeText(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setProblemText(e.target.value);
    autoGrow(e.target);
  }

  // Enter = gửi, Shift+Enter = xuống dòng (quy ước quen thuộc của ô chat).
  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canAnalyze) void onAnalyze();
    }
  }

  function onPickFile(e: React.ChangeEvent<HTMLInputElement>) {
    setFileError(null);
    const picked = e.target.files?.[0] ?? null;
    if (!picked) return;
    if (!kindFromFile(picked.name)) {
      setFileError(
        "Định dạng không hỗ trợ. Chọn .py, .docx hoặc ảnh .png/.jpg/.webp.",
      );
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }
    setFile(picked);
  }

  function removeFile() {
    setFile(null);
    setFileError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function onAnalyze() {
    const store = useAppStore.getState();
    store.setAnalysisError(null);
    store.setAnalyzing(true);
    try {
      const payload = file
        ? await fileToPayload(file)
        : { type: "text" as const, content: problemText.trim() };
      const result = await analyzeViaServer(payload);
      if (result.status === "ok") {
        // originalInput vào lịch sử: CHỈ text an toàn (tệp có thể là nhị phân
        // base64 — chính sách M9-UX1 cấm persist blob).
        store.loadEnvelope(result, undefined, file ? undefined : problemText.trim());
      } else {
        store.loadUnsupported(result);
      }
    } catch (err) {
      store.setAnalysisError(err instanceof Error ? err.message : String(err));
    } finally {
      store.setAnalyzing(false);
    }
  }

  // M9-UX2 §9: trạng thái kĩ thuật GIỮ IM khi mọi thứ ổn — học sinh không cần
  // biết "ngân hàng bài: N". Chỉ nói khi có việc phải làm (server tắt/thiếu key).
  const serverStatus =
    health === null ? (
      <span className="hint" style={{ color: "var(--accent-orange)" }}>
        ● Máy chủ phân tích chưa chạy — vẫn dùng được các mô phỏng mẫu bên dưới
      </span>
    ) : health !== "loading" && !health.hasKey ? (
      <span className="hint" style={{ color: "var(--accent-orange)" }}>
        ● Máy chủ thiếu khóa AI — vẫn dùng được các mô phỏng mẫu bên dưới
      </span>
    ) : null;

  return (
    <div className="composer-hero">
      {/* M9-UX5 — HỘP nhiều dòng (không còn pill một dòng): ô gõ ở trên, hai nút
          tròn ở đáy — `+` trái (tải tệp), gửi phải. Placeholder được nói đủ ý vì
          hộp cao sẵn, không sợ cắt cụt như pill. */}
      <div className={`composer-box${analyzing ? " is-busy" : ""}`}>
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptAttr()}
          onChange={onPickFile}
          style={{ display: "none" }}
        />

        <textarea
          ref={textRef}
          className="composer-text"
          rows={2}
          placeholder="Nhập đề bài Tin học của em, hoặc tải lên tệp đề…"
          value={problemText}
          onChange={onChangeText}
          onKeyDown={onKeyDown}
          disabled={file !== null}
        />

        <div className="composer-foot">
          <button
            className="composer-attach"
            onClick={() => fileInputRef.current?.click()}
            title="Tải tệp đề (.docx / .py / ảnh)"
            aria-label="Tải tệp đề"
          >
            <IconAttach size={17} />
          </button>
          <button
            className="composer-send"
            onClick={onAnalyze}
            disabled={!canAnalyze}
            title="Phân tích đề bằng AI"
            aria-label="Phân tích đề bằng AI"
          >
            {analyzing ? <span className="composer-spin" /> : <IconSend size={17} />}
          </button>
        </div>
      </div>

      {file && (
        <div className="file-chip">
          <span className="file-chip-info">
            <strong>{file.name}</strong>
            <span className="hint">{kindLabel(kindFromFile(file.name) ?? "text")}</span>
          </span>
          <button className="file-chip-remove" onClick={removeFile} title="Bỏ tệp">
            ×
          </button>
        </div>
      )}
      {fileError && <div className="error-banner">{fileError}</div>}
      {serverStatus}
      {analysisError && <div className="error-banner">{analysisError}</div>}
    </div>
  );
}
