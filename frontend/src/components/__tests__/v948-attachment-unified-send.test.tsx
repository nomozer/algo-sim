import { readFileSync } from "node:fs";
import { describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { ProblemInput, cancelComposerSubmit, runComposerSubmit } from "../ProblemInput";
import { PdfPreview, renderPdfFirstPageThumbnail } from "../PdfPreview";
import { useAppStore } from "../../state/store";
import { useToastStore } from "../TopNav";
import type { ComposerAttachmentItem } from "../../llm/input";

function setAppState(partial: Partial<ReturnType<typeof useAppStore.getState>>) {
  useAppStore.setState(partial);
  Object.assign(useAppStore.getInitialState(), partial);
}

describe("AXO V9.4.8 — Unified Attachment System & Send/Stop Button", () => {
  it("keeps uniform card dimensions (108x108) across all attachment types and uses object-fit: contain for thumbnails", () => {
    const css = readFileSync(new URL("../../styles/global.css", import.meta.url), "utf-8");
    const cardBlock = /\.file-preview-card\s*\{([^}]+)\}/.exec(css)?.[1] ?? "";
    expect(cardBlock).toContain("width: 108px");
    expect(cardBlock).toContain("height: 108px");
    expect(cardBlock).toContain("border-radius: 12px");

    const imgCardBlock = /\.file-preview-card\[data-kind="image"\]\s*\{([^}]+)\}/.exec(css)?.[1] ?? "";
    expect(imgCardBlock).not.toMatch(/\b(width|height)\s*:\s*96px/);
    expect(imgCardBlock).not.toMatch(/\b(width|height)\s*:\s*120px/);

    const imgThumbBlock = /\.file-preview-card\[data-kind="image"\]\s+\.composer-file-thumb\s*\{([^}]+)\}/.exec(css)?.[1] ?? "";
    expect(imgThumbBlock).toContain("object-fit: contain");

    const filePdf = new File(["%PDF-1.7\n" + "x".repeat(64)], "de-hinh-chop.pdf", { type: "application/pdf" });
    const fileDoc = new File(["doc"], "de-cuong.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const fileImg = new File(["img"], "hinh-ve.png", { type: "image/png" });

    const attachments: ComposerAttachmentItem[] = [
      { id: "p1", file: filePdf, name: filePdf.name, size: filePdf.size, sizeFormatted: "80 B", ext: ".pdf", kind: "pdf", previewUrl: "data:image/png;base64,iVBORw0KGgo=", status: "ready" },
      { id: "d1", file: fileDoc, name: fileDoc.name, size: fileDoc.size, sizeFormatted: "3 B", ext: ".docx", kind: "document", status: "ready" },
      { id: "i1", file: fileImg, name: fileImg.name, size: fileImg.size, sizeFormatted: "3 B", ext: ".png", kind: "image", previewUrl: "blob:http://localhost/img1", status: "ready" },
    ];
    const html = renderToString(<ProblemInput initialAttachments={attachments} />);
    expect(html).toContain('data-kind="pdf"');
    expect(html).toContain('data-kind="document"');
    expect(html).toContain('data-kind="image"');
    expect(html).toContain("file-preview-card has-thumb");
  });

  it("renders unified Send/Stop button cleanly across Idle, Ready, and Processing states with zero separate Cancel button", () => {
    setAppState({ problemText: "", analyzing: false });
    const idleHtml = renderToString(<ProblemInput />);
    expect(idleHtml).toContain('id="btn-composer-send"');
    expect(idleHtml).toContain('data-composer-state="idle"');
    expect(idleHtml).toMatch(/id="btn-composer-send"[^>]*\sdisabled(?:=""|\s|>)/);
    expect(idleHtml).toContain("composer-submit-arrow");
    expect(idleHtml).not.toContain('id="btn-composer-cancel"');

    setAppState({ problemText: "Cho hình chóp S.ABC có đáy là tam giác đều cạnh a.", analyzing: false });
    const readyHtml = renderToString(<ProblemInput />);
    expect(readyHtml).toContain('data-composer-state="ready"');
    expect(readyHtml).not.toMatch(/id="btn-composer-send"[^>]*\sdisabled(?:=""|\s|>)/);
    expect(readyHtml).toContain("composer-submit-arrow");

    setAppState({ analyzing: true });
    const processingHtml = renderToString(<ProblemInput />);
    expect(processingHtml).toContain('data-composer-state="processing"');
    expect(processingHtml).toContain("btn-composer-submit is-processing");
    expect(processingHtml).toContain("composer-stop-icon");
    expect(processingHtml).not.toContain('id="btn-composer-cancel"');
    expect(processingHtml).not.toMatch(/id="btn-composer-send"[^>]*\sdisabled(?:=""|\s|>)/);

    setAppState({ problemText: "", analyzing: false });
  });

  it("cancelling an in-flight submit prevents late response overwrite and allows immediate retry", async () => {
    useToastStore.setState({ toasts: [] });
    useAppStore.getState().setProblemText("Cho hình lăng trụ đứng ABC.A'B'C'.");
    const lockRef = { current: false };
    const abortRef = { current: null as AbortController | null };
    const reqRef = { current: null as string | null };

    let resolveLate!: (v: unknown) => void;
    const analyzeFn = vi
      .fn()
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveLate = resolve;
          }),
      )
      .mockResolvedValueOnce({ status: "unsupported", reason: "Retried cleanly" });

    const firstRun = runComposerSubmit({
      canSubmit: true,
      lockRef,
      abortRef,
      requestIdRef: reqRef,
      problemText: useAppStore.getState().problemText,
      health: { ok: true, hasKey: true, cachedProblems: 0 },
      analyzeFn: analyzeFn as any,
    });

    cancelComposerSubmit(lockRef, abortRef, reqRef);
    // Simulate delayed server answer arriving after client aborted
    resolveLate({ status: "unsupported", reason: "Late stale payload must be ignored" });
    await firstRun;

    expect(useToastStore.getState().toasts).toHaveLength(0);
    expect(useAppStore.getState().problemText).toBe("Cho hình lăng trụ đứng ABC.A'B'C'.");
    expect(useAppStore.getState().analyzing).toBe(false);

    // Retry succeeds cleanly with fresh request
    await runComposerSubmit({
      canSubmit: true,
      lockRef,
      abortRef,
      requestIdRef: reqRef,
      problemText: useAppStore.getState().problemText,
      health: { ok: true, hasKey: true, cachedProblems: 0 },
      analyzeFn: analyzeFn as any,
    });
    expect(analyzeFn).toHaveBeenCalledTimes(2);
    expect(useToastStore.getState().toasts).toHaveLength(1);

    useToastStore.setState({ toasts: [] });
    useAppStore.getState().setProblemText("");
  });

  it("PdfPreview renders Paper Stack DOM and thumbnail helper degrades safely without Canvas 2D", async () => {
    const pdfFile = new File(["%PDF-1.7\n"], "sample.pdf", { type: "application/pdf" });
    const html = renderToString(<PdfPreview file={pdfFile} downloadUrl="blob:http://localhost/pdf1" />);
    expect(html).toContain("attachment-pdf-preview");
    expect(html).toContain("attachment-pdf-stack");
    expect(html).toContain("attachment-pdf-stack-front");
    expect(html).toContain("attachment-pdf-stack-layer--mid");
    await expect(renderPdfFirstPageThumbnail(pdfFile)).resolves.toBeNull();
  });

  it("hides native attachment scrollbar arrows/track and styles minimal rounded thumb", () => {
    const css = readFileSync(new URL("../../styles/global.css", import.meta.url), "utf-8");
    expect(css).toMatch(/\.composer-files-row::-webkit-scrollbar-button\s*\{\s*display:\s*none/);
    expect(css).toMatch(/\.composer-files-scroll-control::-webkit-slider-runnable-track\s*\{[^}]*background:\s*transparent/);
    expect(css).toMatch(/\.composer-files-scroll-control::-webkit-slider-thumb\s*\{[^}]*border-radius:\s*9999px/);
  });
});
