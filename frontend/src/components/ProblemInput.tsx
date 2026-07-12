import { useEffect, useRef, useState } from "react";
import { useAppStore } from "../state/store";
import { analyzeViaServer, fetchHealth, type ServerHealth } from "../llm/client";
import { acceptAttr, fileToPayload, kindFromFile, kindLabel } from "../llm/input";

/**
 * Nhập đề: gõ văn bản HOẶC tải tệp (.docx / .py / ảnh) — M4.
 * Mọi đầu vào chuẩn hóa thành InputPayload rồi gọi /api/analyze (một contract).
 * Việc gọi Gemini do backend đảm nhiệm (trình duyệt không giữ API key).
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
        store.loadEnvelope(result);
      } else {
        store.loadUnsupported(result);
      }
    } catch (err) {
      store.setAnalysisError(err instanceof Error ? err.message : String(err));
    } finally {
      store.setAnalyzing(false);
    }
  }

  const serverStatus =
    health === "loading" ? (
      <span className="hint">Đang kiểm tra máy chủ…</span>
    ) : health === null ? (
      <span className="hint" style={{ color: "var(--accent-orange)" }}>
        ● Máy chủ phân tích chưa chạy — chạy <code>docker compose up -d --build</code>
      </span>
    ) : !health.hasKey ? (
      <span className="hint" style={{ color: "var(--accent-orange)" }}>
        ● Máy chủ đang chạy nhưng thiếu key — tạo <code>backend/.env</code> với{" "}
        <code>GEMINI_API_KEY=…</code>
      </span>
    ) : (
      <span className="hint" style={{ color: "var(--accent-green)" }}>
        ● Máy chủ sẵn sàng · ngân hàng bài: {health.cachedProblems} bài
      </span>
    );

  return (
    <section className="card stack" style={{ gap: "var(--sp-sm)" }}>
      <span className="eyebrow">ĐỀ BÀI</span>
      <textarea
        className="text-input"
        rows={5}
        placeholder='Nhập đề bài, ví dụ: "Lớp 10A có các bạn với điểm kiểm tra khác nhau. Tìm bạn có điểm cao nhất."'
        value={problemText}
        onChange={(e) => setProblemText(e.target.value)}
        disabled={file !== null}
      />

      <div className="upload-row">
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptAttr()}
          onChange={onPickFile}
          style={{ display: "none" }}
        />
        <button className="btn-utility" onClick={() => fileInputRef.current?.click()}>
          📎 Tải tệp (.docx / .py / ảnh)
        </button>
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

      <button className="btn-primary" onClick={onAnalyze} disabled={!canAnalyze}>
        {analyzing ? "Đang phân tích…" : "Phân tích đề bằng AI"}
      </button>
      {serverStatus}
      {analysisError && <div className="error-banner">{analysisError}</div>}
    </section>
  );
}
