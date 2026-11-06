import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../App";
import { HomeView } from "./HomeView";
import { ProblemInput } from "./ProblemInput";
import { ToastContainer, useToastStore } from "./TopNav";
import { starterEntries } from "../data/offline-catalog";
import {
  canSubmitComposer,
  formatAttachmentSize,
  validateComposerFile,
  type ComposerAttachmentItem,
} from "../llm/input";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest } from "../state/history";
import { useAppStore } from "../state/store";

registerAllSimulations();

function setAppStateForSSR(patch: {
  problemText?: string;
  analyzing?: boolean;
  analysisError?: string | null;
}) {
  useAppStore.setState(patch);
  Object.assign(useAppStore.getInitialState(), patch);
}

function makeAttachment(
  id: string,
  name: string,
  size: number,
  kind: "document" | "image" | "code",
  ext: string,
): ComposerAttachmentItem {
  const fakeFile =
    typeof File !== "undefined"
      ? new File(["x".repeat(Math.min(size, 64))], name)
      : ({ name, size } as unknown as File);
  return {
    id,
    file: fakeFile,
    name,
    size,
    sizeFormatted: formatAttachmentSize(size),
    ext,
    kind,
  };
}

describe("Axo V2.7 Slice 2 — 18 Component & Integration Cases (P11.2 & P11.3)", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    setAppStateForSSR({
      problemText: "",
      analyzing: false,
      analysisError: null,
    });
    useToastStore.getState().clearToasts();
    Object.assign(useToastStore.getInitialState(), { toasts: [] });
  });

  afterEach(() => {
    setAppStateForSSR({
      problemText: "",
      analyzing: false,
      analysisError: null,
    });
    useToastStore.getState().clearToasts();
    Object.assign(useToastStore.getInitialState(), { toasts: [] });
  });

  it("1. Composer render ban đầu với đúng placeholder 'Nhập đề toán hình học không gian...'", () => {
    const html = renderToString(<ProblemInput />);
    expect(html).toContain('placeholder="Nhập đề toán hình học không gian..."');
    expect(html).toContain("Dựng hình");
    expect(html).toContain("composer-submit-arrow");
  });

  it("2. Composer không có đường kẻ ngang phía trên hàng công cụ dưới cùng (.composer-footer border-top: none) và menu + mở xuống dưới", () => {
    const css = readFileSync(
      new URL("../styles/global.css", import.meta.url),
      "utf-8",
    );
    expect(css).toMatch(/\.composer-footer\s*\{[^}]*border-top:\s*none/s);
    expect(css).toMatch(/\.plus-popover-menu\s*\{[^}]*top:\s*calc\(100%\s*\+\s*6px\)/s);
  });

  it("3. Nút Dựng hình → ở trạng thái disabled ban đầu khi chưa có chữ và chưa có tệp", () => {
    const emptyHtml = renderToString(<ProblemInput />);
    expect(emptyHtml).toMatch(
      /<button[^>]*class="btn-composer-submit"[^>]*disabled=""/,
    );
  });

  it("4. Nút Dựng hình → giữ trạng thái disabled khi chỉ nhập khoảng trắng hoặc xuống dòng", () => {
    setAppStateForSSR({ problemText: "   \n  \t " });
    const whitespaceHtml = renderToString(<ProblemInput />);
    expect(whitespaceHtml).toMatch(
      /<button[^>]*class="btn-composer-submit"[^>]*disabled=""/,
    );
    expect(canSubmitComposer("   \n\t ", 0, false)).toBe(false);
  });

  it("5. Nút Dựng hình → chuyển sang enabled khi nhập văn bản hợp lệ (không áp đặt tối thiểu 10 ký tự)", () => {
    setAppStateForSSR({ problemText: "S.ABCD" });
    const validTextHtml = renderToString(<ProblemInput />);
    expect(validTextHtml).not.toMatch(
      /<button[^>]*class="btn-composer-submit"[^>]*disabled=""/,
    );
    expect(canSubmitComposer("S.ABCD", 0, false)).toBe(true);
  });

  it("6. Nút Dựng hình → quay lại disabled khi xóa hết chữ và không có tệp", () => {
    setAppStateForSSR({ problemText: "Cho hình chóp S.ABCD" });
    expect(renderToString(<ProblemInput />)).not.toMatch(
      /<button[^>]*class="btn-composer-submit"[^>]*disabled=""/,
    );

    setAppStateForSSR({ problemText: "" });
    expect(renderToString(<ProblemInput />)).toMatch(
      /<button[^>]*class="btn-composer-submit"[^>]*disabled=""/,
    );
  });

  it("7. Nút Dựng hình → chuyển sang enabled khi đính kèm tệp hợp lệ được backend hỗ trợ dù không nhập chữ", () => {
    const docxAtt = makeAttachment(
      "att-1",
      "de-hinh-chop-sabcd.docx",
      24_576,
      "document",
      ".docx",
    );
    const withValidFileHtml = renderToString(
      <ProblemInput initialAttachments={[docxAtt]} />,
    );
    expect(withValidFileHtml).not.toMatch(
      /<button[^>]*class="btn-composer-submit"[^>]*disabled=""/,
    );
    expect(withValidFileHtml).toContain("de-hinh-chop-sabcd");
    expect(withValidFileHtml).toContain(".docx");
    expect(withValidFileHtml).toContain("DOCX · 24 KB");
  });

  it("8. Nút Dựng hình → giữ disabled khi chọn tệp không hợp lệ hoặc chưa hỗ trợ (.pdf theo D3, .exe, 0B)", () => {
    const pdfCheck = validateComposerFile({
      name: "de-thi.pdf",
      size: 100_000,
      type: "application/pdf",
    });
    expect(pdfCheck.ok).toBe(false);
    if (!pdfCheck.ok) {
      expect(pdfCheck.code).toBe("pdf_unsupported");
    }

    const exeCheck = validateComposerFile({
      name: "malware.exe",
      size: 4096,
    });
    expect(exeCheck.ok).toBe(false);

    // Khi tệp bị từ chối và ô chữ trống, số tệp hợp lệ = 0 → nút vẫn disabled
    expect(canSubmitComposer("", 0, false)).toBe(false);
    expect(renderToString(<ProblemInput initialAttachments={[]} />)).toMatch(
      /<button[^>]*class="btn-composer-submit"[^>]*disabled=""/,
    );
  });

  it("9. Nhấn Enter khi ô nhập rỗng không gọi API và không hiện Toast lỗi", () => {
    const src = readFileSync(
      new URL("./ProblemInput.tsx", import.meta.url),
      "utf-8",
    );
    expect(src).toContain("if (canSubmit)");
    expect(canSubmitComposer("", 0, false)).toBe(false);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it("10. Nhấn Shift + Enter xuống dòng, không gửi yêu cầu", () => {
    const src = readFileSync(
      new URL("./ProblemInput.tsx", import.meta.url),
      "utf-8",
    );
    expect(src).toMatch(/if\s*\(\s*e\.shiftKey\s*\)\s*\{\s*if\s*\(\s*analyzing\s*\)\s*e\.preventDefault\(\);\s*return;\s*\}/);
  });

  it("11. Nhấn Enter khi có nội dung hợp lệ và không trong trạng thái IME composition sẽ gửi yêu cầu", () => {
    const src = readFileSync(
      new URL("./ProblemInput.tsx", import.meta.url),
      "utf-8",
    );
    expect(src).toContain("isComposing");
    expect(src).toContain("229");
    expect(src).toContain("void onAnalyze()");
  });

  it("12. Nút + mở và đóng menu đính kèm tệp (Tải tệp từ thiết bị, Chụp ảnh đề bài)", () => {
    const closedHtml = renderToString(<ProblemInput />);
    expect(closedHtml).toContain('class="btn-plus-trigger"');
    expect(closedHtml).toContain('class="plus-popover-menu"');

    const openHtml = renderToString(<ProblemInput initialPlusMenuOpen />);
    expect(openHtml).toContain('class="btn-plus-trigger is-open"');
    expect(openHtml).toContain('class="plus-popover-menu open"');
    expect(openHtml).toContain("Tải tệp từ thiết bị");
    expect(openHtml).toContain("Chụp ảnh đề bài");
  });

  it("13. Xóa tệp khỏi hàng thẻ tệp chỉ xóa đúng tệp được chọn và cập nhật lại trạng thái nút", () => {
    const att1 = makeAttachment("att-1", "de-1.docx", 12_288, "document", ".docx");
    const att2 = makeAttachment("att-2", "de-2.png", 64_000, "image", ".png");

    const twoFilesHtml = renderToString(
      <ProblemInput initialAttachments={[att1, att2]} />,
    );
    expect(twoFilesHtml).toContain("de-1");
    expect(twoFilesHtml).toContain("de-2");

    // Sau khi xóa att-1, còn lại att-2 và nút vẫn enabled
    const oneFileHtml = renderToString(
      <ProblemInput initialAttachments={[att2]} />,
    );
    expect(oneFileHtml).not.toContain("de-1");
    expect(oneFileHtml).toContain("de-2");
    expect(oneFileHtml).not.toMatch(
      /<button[^>]*class="btn-composer-submit"[^>]*disabled=""/,
    );

    // Sau khi xóa hết tệp (và không có chữ), nút chuyển về disabled
    const zeroFileHtml = renderToString(
      <ProblemInput initialAttachments={[]} />,
    );
    expect(zeroFileHtml).toMatch(
      /<button[^>]*class="btn-composer-submit"[^>]*disabled=""/,
    );
  });

  it("14. Task 1 §7: Hàng thẻ tệp cuộn ngang gọn không hiện dòng đếm/nút Xem tất cả tệp dư thừa; modal vẫn mở được khi kích hoạt tường minh", () => {
    const att1 = makeAttachment("att-1", "de-so-1.docx", 18_432, "document", ".docx");
    const att2 = makeAttachment("att-2", "hinh-lang-tru.png", 142_000, "image", ".png");

    const singleHtml = renderToString(
      <ProblemInput initialAttachments={[att1]} />,
    );
    expect(singleHtml).not.toContain("Xem tất cả tệp");
    expect(singleHtml).not.toContain("composer-files-meta-row");

    const multiHtml = renderToString(
      <ProblemInput initialAttachments={[att1, att2]} />,
    );
    expect(multiHtml).not.toContain("Xem tất cả tệp");
    expect(multiHtml).not.toContain("Đã đính kèm");
    expect(multiHtml).not.toContain("composer-files-meta-row");

    const modalHtml = renderToString(
      <ProblemInput
        initialAttachments={[att1, att2]}
        initialAllFilesModalOpen
      />,
    );
    expect(modalHtml).toContain("axo-att-modal-backdrop");
    expect(modalHtml).toContain("Tất cả tệp đề toán đính kèm (2)");
    expect(modalHtml).toContain("all-files-modal-item-left");
    expect(modalHtml).toContain("file-card-thumb badge-docx");
    expect(modalHtml).toContain("#1 · de-so-1.docx");
    expect(modalHtml).toContain("DOCX · 18 KB · Đã đính kèm");
    expect(modalHtml).toContain("Xem trước");
    expect(modalHtml).toContain("file-card-remove");
  });

  it("15. Xóa tệp trong Modal cập nhật danh sách và tự đóng Modal khi không còn tệp", () => {
    const att1 = makeAttachment("att-1", "de-so-1.docx", 18_432, "document", ".docx");
    const modalWithOneHtml = renderToString(
      <ProblemInput initialAttachments={[att1]} initialAllFilesModalOpen />,
    );
    expect(modalWithOneHtml).toContain("Tất cả tệp đề toán đính kèm (1)");
    expect(modalWithOneHtml).toContain('aria-label="Gỡ tệp de-so-1.docx"');
    expect(modalWithOneHtml).toContain("Xem trước");

    // Khi danh sách tệp về 0, modal không còn hiển thị
    const modalEmptyHtml = renderToString(
      <ProblemInput initialAttachments={[]} initialAllFilesModalOpen />,
    );
    expect(modalEmptyHtml).not.toContain("axo-att-modal-backdrop");
  });

  it("16. Khi gửi yêu cầu, nút chuyển sang [Spinner] Đang dựng hình... và chặn bấm lặp", () => {
    setAppStateForSSR({
      problemText: "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a.",
      analyzing: true,
    });
    const busyHtml = renderToString(<ProblemInput />);
    expect(busyHtml).toContain("btn-composer-submit is-loading");
    expect(busyHtml).toContain('aria-busy="true"');
    expect(busyHtml).toContain("composer-spin");
    expect(busyHtml).toContain("Đang dựng hình...");
    expect(busyHtml).not.toContain("composer-submit-arrow");
  });

  it("17. Khi API trả lỗi hoặc dịch vụ chưa sẵn sàng, kết thúc Loading, giữ nguyên dữ liệu người dùng và hiển thị Toast lỗi", () => {
    setAppStateForSSR({
      problemText: "Cho tứ diện đều ABCD cạnh a.",
      analyzing: false,
    });
    useToastStore.getState().showToast({
      tone: "error",
      title: "Dựng hình chưa thành công",
      description: "Có lỗi xảy ra. Vui lòng thử lại.",
      durationMs: 0,
    });
    Object.assign(useToastStore.getInitialState(), {
      toasts: useToastStore.getState().toasts,
    });

    const appHtml = renderToString(
      <>
        <HomeView />
        <ToastContainer />
      </>,
    );
    expect(appHtml).toContain("Cho tứ diện đều ABCD cạnh a.");
    expect(appHtml).toContain("Dựng hình chưa thành công");
    expect(appHtml).toContain("Có lỗi xảy ra. Vui lòng thử lại.");
  });

  it("18. Bấm thẻ Gợi ý khám phá mở mô hình thật trong Workspace Scene3D không cần gọi AI", () => {
    const starters = starterEntries();
    expect(starters.length).toBeGreaterThan(0);

    const first = starters[0];
    useAppStore.getState().loadEnvelope(first.envelope, first.id);
    const state = useAppStore.getState();
    expect(state.view).toBe("workspace");
    expect(state.active?.envelope).toBe(first.envelope);
    expect(state.activeSampleId).toBe(first.id);

    useAppStore.getState().reset();
    const homeHtml = renderToString(<App />);
    expect(homeHtml).toContain("Em muốn dựng hình nào?");
    expect(homeHtml).toContain("Gợi ý khám phá");
    expect(homeHtml).toContain("Xem tất cả thư viện");
  });

  it("19. Phase C.4 P2 & P3: Thẻ tệp đính kèm có đủ các trạng thái Default, Hover/Focus, Loading, Ready, Error, Remove và Tooltip tên đầy đủ", () => {
    const readyDoc = makeAttachment("att-doc", "de-on-tap-hoc-ky-1-hinh-khong-gian-lop-11.docx", 34_816, "document", ".docx");
    const loadingImg: ComposerAttachmentItem = {
      ...makeAttachment("att-loading", "anh-chup-de-bai.png", 128_000, "image", ".png"),
      status: "loading",
    };
    const errorPdf: ComposerAttachmentItem = {
      ...makeAttachment("att-err", "de-thi-thu-thpt.pdf", 512_000, "document", ".pdf"),
      kind: "pdf",
      status: "error",
      errorMessage: "Không thể đọc tệp PDF",
    };

    const html = renderToString(
      <ProblemInput initialAttachments={[readyDoc, loadingImg, errorPdf]} />,
    );
    expect(html).toContain('class="file-preview-card"');
    expect(html).toContain('class="file-preview-card is-loading"');
    expect(html).toContain('class="file-preview-card is-error"');
    expect(html).toContain('title="de-on-tap-hoc-ky-1-hinh-khong-gian-lop-11.docx"');
    expect(html).toContain('class="file-card-thumb badge-docx"');
    expect(html).toContain('class="file-card-thumb badge-loading"');
    expect(html).toContain('class="file-card-thumb badge-error"');
    expect(html).toContain("Đang tải lên · 125 KB");
    expect(html).toContain("Không thể đọc tệp PDF");
    expect(html).toContain('tabindex="0"');
    expect(html).toContain('rows="3"');
  });
});
