import { useEffect, useRef, useState } from "react";

let pdfWorkerConfigured = false;

async function loadPdfJs() {
  const pdfjs = await import("pdfjs-dist");
  if (!pdfWorkerConfigured || !pdfjs.GlobalWorkerOptions.workerSrc) {
    pdfjs.GlobalWorkerOptions.workerSrc = new URL(
      "../../node_modules/pdfjs-dist/build/pdf.worker.min.mjs",
      import.meta.url,
    ).toString();
    pdfWorkerConfigured = true;
  }
  return pdfjs;
}

/**
 * Render trang đầu tiên của PDF thành ảnh PNG thu nhỏ cho thẻ đính kèm (client-side).
 * Trả về `null` nếu môi trường không có Canvas 2D (VD: JSDOM/SSR) hoặc tệp lỗi.
 */
export async function renderPdfFirstPageThumbnail(
  file: File,
  maxWidth = 192,
): Promise<string | null> {
  if (typeof document === "undefined") return null;
  let canvas: HTMLCanvasElement | null = null;
  let task: { destroy: () => Promise<void>; promise: Promise<any> } | null = null;
  try {
    canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    const pdfjs = await loadPdfJs();
    const data = new Uint8Array(await file.arrayBuffer());
    task = pdfjs.getDocument({ data, enableXfa: false, useSystemFonts: true });
    const doc = await task.promise;
    const page = await doc.getPage(1);
    const natural = page.getViewport({ scale: 1 });
    const scale = Math.max(0.2, Math.min(2, maxWidth / Math.max(1, natural.width)));
    const viewport = page.getViewport({ scale });
    canvas.width = Math.ceil(viewport.width);
    canvas.height = Math.ceil(viewport.height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    await page.render({ canvas, canvasContext: ctx, viewport }).promise;
    return canvas.toDataURL("image/png");
  } catch {
    return null;
  } finally {
    await task?.destroy().catch(() => {});
  }
}

export function PdfPreview({
  file,
  downloadUrl,
}: {
  file: File;
  downloadUrl: string | null;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [state, setState] = useState<{
    kind: "loading" | "ready" | "error";
    pages?: number;
    orientation?: "portrait" | "landscape";
  }>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    let destroy: (() => Promise<void>) | undefined;
    setState({ kind: "loading" });
    void (async () => {
      try {
        const pdfjs = await loadPdfJs();
        const data = new Uint8Array(await file.arrayBuffer());
        if (cancelled) return;
        const task = pdfjs.getDocument({ data, enableXfa: false, useSystemFonts: true });
        destroy = () => task.destroy();
        const doc = await task.promise;
        const page = await doc.getPage(1);
        const natural = page.getViewport({ scale: 1 });
        const ratio = natural.width / Math.max(1, natural.height);
        const orientation: "portrait" | "landscape" = ratio > 1.08 ? "landscape" : "portrait";

        const vw = typeof window !== "undefined" ? window.innerWidth : 1280;
        const vh = typeof window !== "undefined" ? window.innerHeight : 800;
        const maxCssW = Math.max(180, Math.min(orientation === "landscape" ? 440 : 296, vw - 72));
        const maxCssH = Math.max(200, Math.min(orientation === "landscape" ? 310 : 386, vh - 210));
        const cssScale = Math.min(1.8, maxCssW / Math.max(1, natural.width), maxCssH / Math.max(1, natural.height));
        const dpr = Math.min(2, typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1);
        const viewport = page.getViewport({ scale: cssScale * dpr });

        const canvas = canvasRef.current;
        if (cancelled || !canvas) return;
        const ctx = canvas.getContext("2d");
        canvas.width = Math.ceil(viewport.width);
        canvas.height = Math.ceil(viewport.height);
        canvas.style.width = `${Math.round(natural.width * cssScale)}px`;
        canvas.style.height = `${Math.round(natural.height * cssScale)}px`;
        if (ctx) {
          ctx.fillStyle = "#ffffff";
          ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
        await page.render({ canvas, ...(ctx ? { canvasContext: ctx } : {}), viewport }).promise;
        if (!cancelled) {
          setState({ kind: "ready", pages: doc.numPages, orientation });
        }
      } catch {
        if (!cancelled) setState({ kind: "error" });
      }
    })();
    return () => {
      cancelled = true;
      void destroy?.().catch(() => {});
    };
  }, [file]);

  return (
    <div
      className="attachment-pdf-preview"
      data-orientation={state.orientation ?? "portrait"}
      data-pages={state.pages ?? 0}
      data-state={state.kind}
    >
      {state.kind === "loading" && (
        <p className="attachment-pdf-status" role="status">
          Đang mở tệp PDF…
        </p>
      )}
      {state.kind === "error" && (
        <p className="attachment-pdf-status" role="status">
          Không thể đọc hoặc xem trước tệp PDF này.
        </p>
      )}

      <div className="attachment-pdf-stack" hidden={state.kind !== "ready"}>
        {(!state.pages || state.pages > 1) && (
          <div className="attachment-pdf-stack-layer attachment-pdf-stack-layer--back" aria-hidden="true" />
        )}
        <div className="attachment-pdf-stack-layer attachment-pdf-stack-layer--mid" aria-hidden="true" />
        <div className="attachment-pdf-stack-front">
          <canvas
            ref={canvasRef}
            id="pdf-preview-canvas"
            aria-label="Trang đầu của PDF"
            hidden={state.kind !== "ready"}
          />
        </div>
      </div>

      {state.kind === "ready" && (
        <div className="attachment-pdf-action-slot">
          <span className="attachment-pdf-page-count">{state.pages} trang</span>
          {downloadUrl && (
            <a
              className="attachment-pdf-download-btn"
              href={downloadUrl}
              download={file.name}
              aria-label={`Tải tệp ${file.name} xuống`}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              <span>Tải xuống</span>
            </a>
          )}
        </div>
      )}

      {state.kind === "error" && downloadUrl && (
        <a
          className="attachment-doc-download-btn"
          href={downloadUrl}
          download={file.name}
          aria-label={`Tải tệp ${file.name} xuống`}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          <span>Tải tệp xuống</span>
        </a>
      )}
    </div>
  );
}
