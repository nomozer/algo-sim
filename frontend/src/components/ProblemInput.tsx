import { useEffect, useRef, useState } from "react";
import { useAppStore } from "../state/store";
import { analyzeViaServer, fetchHealth, type ServerHealth } from "../llm/client";
import { acceptAttr, fileToPayload, kindFromFile, kindLabel } from "../llm/input";

/**
 * Nhập đề: gõ văn bản HOẶC tải tệp (.docx / .py / ảnh) — M4.
 * Mọi đầu vào chuẩn hóa thành InputPayload rồi gọi /api/analyze (một contract).
 * Việc gọi Gemini do backend đảm nhiệm (trình duyệt không giữ API key).
 *
 * M9-UX3 — HAI VỎ, MỘT LÕI. Component này phục vụ hai chỗ có ràng buộc bề rộng
 * khác hẳn nhau, nên tách LỚP VỎ chứ không nhân đôi hành vi:
 *   - "hero"    (HomeView): pill — ô một dòng tự cao dần, kẹp tệp và nút gửi
 *                nằm TRONG ô. Đây là hành động chính của Trang chủ.
 *   - "compact" (InputPanel, cột trái workspace 264px): form xếp dọc như cũ —
 *                pill có icon hai đầu sẽ vỡ ở bề rộng đó.
 * Mọi logic (analyze, tệp, health, lỗi) DÙNG CHUNG — chỉ khác JSX bao ngoài.
 */
export function ProblemInput({ variant = "compact" }: { variant?: "hero" | "compact" }) {
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
    if (variant === "hero") autoGrow(e.target);
  }

  // Enter = gửi, Shift+Enter = xuống dòng (quy ước quen thuộc của ô chat).
  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (variant !== "hero") return;
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

  // Dùng chung cho cả hai vỏ — input tệp ẩn, chip tệp đã chọn, băng lỗi.
  const hiddenFileInput = (
    <input
      ref={fileInputRef}
      type="file"
      accept={acceptAttr()}
      onChange={onPickFile}
      style={{ display: "none" }}
    />
  );

  const fileChip = file && (
    <div className="file-chip">
      <span className="file-chip-info">
        <strong>{file.name}</strong>
        <span className="hint">{kindLabel(kindFromFile(file.name) ?? "text")}</span>
      </span>
      <button className="file-chip-remove" onClick={removeFile} title="Bỏ tệp">
        ×
      </button>
    </div>
  );

  if (variant === "hero") {
    return (
      <div className="composer-hero">
        <div className={`composer-pill${analyzing ? " is-busy" : ""}`}>
          {hiddenFileInput}
          <button
            className="composer-attach"
            onClick={() => fileInputRef.current?.click()}
            title="Tải tệp (.docx / .py / ảnh)"
            aria-label="Tải tệp"
          >
            📎
          </button>
          {/* Pill cao 1 dòng → placeholder phải NGẮN, nếu không nó xuống dòng và
              bị cắt cụt (auto-grow chỉ chạy khi gõ). Ví dụ dài đã nằm ở phụ đề. */}
          <textarea
            ref={textRef}
            className="composer-text"
            rows={1}
            placeholder="Nhập đề bài Tin học của em…"
            value={problemText}
            onChange={onChangeText}
            onKeyDown={onKeyDown}
            disabled={file !== null}
          />
          <button
            className="composer-send"
            onClick={onAnalyze}
            disabled={!canAnalyze}
            title="Phân tích đề bằng AI"
            aria-label="Phân tích đề bằng AI"
          >
            {analyzing ? "…" : "↑"}
          </button>
        </div>

        {/* Ví dụ cụ thể: học sinh chưa dùng bao giờ thì không biết gõ gì cho vừa. */}
        {!file && problemText.length === 0 && (
          <p className="composer-example">
            Ví dụ: “Lớp 10A có các bạn với điểm kiểm tra khác nhau. Tìm bạn có điểm cao nhất.”
          </p>
        )}

        {fileChip}
        {fileError && <div className="error-banner">{fileError}</div>}
        {serverStatus}
        {analysisError && <div className="error-banner">{analysisError}</div>}
      </div>
    );
  }

  return (
    <section className="card stack home-composer-card" style={{ gap: "var(--sp-sm)" }}>
      <textarea
        className="text-input"
        rows={5}
        placeholder='Nhập đề bài, ví dụ: "Lớp 10A có các bạn với điểm kiểm tra khác nhau. Tìm bạn có điểm cao nhất."'
        value={problemText}
        onChange={onChangeText}
        disabled={file !== null}
      />

      <div className="upload-row">
        {hiddenFileInput}
        <button className="btn-utility" onClick={() => fileInputRef.current?.click()}>
          📎 Tải tệp (.docx / .py / ảnh)
        </button>
      </div>

      {fileChip}
      {fileError && <div className="error-banner">{fileError}</div>}

      <button className="btn-primary" onClick={onAnalyze} disabled={!canAnalyze}>
        {analyzing ? "Đang phân tích…" : "Phân tích đề bằng AI"}
      </button>
      {serverStatus}
      {analysisError && <div className="error-banner">{analysisError}</div>}
    </section>
  );
}
