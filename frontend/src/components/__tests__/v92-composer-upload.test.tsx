import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { HomeView } from "../HomeView";
import { ProblemInput } from "../ProblemInput";
import { useToastStore } from "../TopNav";
import { formatAttachmentSize, type ComposerAttachmentItem } from "../../llm/input";
import { registerAllSimulations } from "../../simulations";
import { __resetHistoryForTest } from "../../state/history";
import { useAppStore } from "../../state/store";

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

describe("AXO V9.2 — Composer Smooth Height, Multiline Animation & Compact Upload Menu", () => {
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

  it("1. V9.4 Two-Tier Claude-Inspired Composer: default two-tier layout, Shift+Enter / Paste multiline, Expand/Collapse state contract & smooth height transition rules", () => {
    const css = readFileSync(
      new URL("../../styles/global.css", import.meta.url),
      "utf-8",
    );
    const problemInputSrc = readFileSync(
      new URL("../ProblemInput.tsx", import.meta.url),
      "utf-8",
    );

    // V9.4.1 two-tier card (680px max-width chosen by owner, 118px min-height, 20px border-radius) & smooth textarea height transition
    expect(css).not.toContain(".home-composer-box.is-singleline");
    expect(css).not.toContain("has-open-plus-bottom");
    expect(css).toMatch(
      /\.home-container\.is-minimal-home\s*\{[^}]*--axo-composer-max-w:\s*680px;/s,
    );
    expect(css).toMatch(
      /\.home-composer-box\s*\{[^}]*width:\s*min\(100%,\s*var\(--axo-composer-max-w,\s*680px\)\);[^}]*max-width:\s*var\(--axo-composer-max-w,\s*680px\);[^}]*min-height:\s*118px;[^}]*border-radius:\s*20px;/s,
    );
    expect(css).toMatch(
      /\.home-composer-box\s+\.composer-textarea\s*\{[^}]*min-height:\s*48px;[^}]*height:\s*48px;[^}]*max-height:\s*192px;[^}]*transition:\s*height\s+180ms\s+cubic-bezier\(0\.2,\s*0,\s*0,\s*1\)/s,
    );
    expect(css).toContain("@media (prefers-reduced-motion: reduce)");

    // Explicit pixel height calculation in syncTextareaHeight (48px two-tier default, 48..192px auto-grow, 216..312px expanded)
    expect(problemInputSrc).toContain('el.style.height = "48px";');
    expect(problemInputSrc).toContain("Math.min(Math.max(measured, 48), 192)");
    expect(problemInputSrc).toContain("Math.min(Math.max(measured, 216), 312)");
    expect(problemInputSrc).toContain("onPaste={onPasteText}");
    expect(problemInputSrc).toContain("setSelectionRange(selStart, selEnd)");

    // Empty default render: two-tier from start (textarea tier before toolbar tier), no expand button yet
    const emptyHtml = renderToString(<HomeView />);
    expect(emptyHtml).toContain('id="home-composer-box"');
    expect(emptyHtml).toContain("home-composer-box is-two-tier");
    expect(emptyHtml).toContain('data-composer-layout="two-tier"');
    expect(emptyHtml).toContain('data-composer-multiline="false"');
    expect(emptyHtml).toContain('data-composer-expanded="false"');
    expect(emptyHtml).not.toContain('id="btn-composer-expand"');
    expect(emptyHtml.indexOf('id="composer-input-tier"')).toBeGreaterThan(0);
    expect(emptyHtml.indexOf('id="composer-toolbar"')).toBeGreaterThan(
      emptyHtml.indexOf('id="composer-input-tier"'),
    );

    // Multiline via Shift+Enter / pasted multiline text -> expand button appears
    setAppStateForSSR({
      problemText:
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a.\nSA vuông góc với mặt phẳng đáy và SA = a√2.\nTính khoảng cách từ A đến (SBC).",
    });
    const multilineHtml = renderToString(<HomeView />);
    expect(multilineHtml).toContain("is-multiline");
    expect(multilineHtml).toContain('data-composer-layout="two-tier"');
    expect(multilineHtml).toContain('data-composer-multiline="true"');
    expect(multilineHtml).toContain('id="btn-composer-expand"');
    expect(multilineHtml).toContain('data-expand-icon="expand"');

    // Multiline via attachment chips
    setAppStateForSSR({ problemText: "" });
    const att = makeAttachment("att-v92-1", "de-hinh-chop.pdf", 28_672, "document", ".pdf");
    const attachmentMultilineHtml = renderToString(
      <ProblemInput initialAttachments={[att]} />,
    );
    expect(attachmentMultilineHtml).toContain("has-attachments");
    expect(attachmentMultilineHtml).toContain('data-composer-layout="two-tier"');
    expect(attachmentMultilineHtml).toContain('data-composer-multiline="true"');
    expect(attachmentMultilineHtml).toContain('id="btn-composer-expand"');
  });

  it("2. V9.4.2 Claude Light Mode Upload Menu (#plus-popover-menu) & Guest Footer CSS in global.css", () => {
    const css = readFileSync(
      new URL("../../styles/global.css", import.meta.url),
      "utf-8",
    );

    // V9.4.2 Claude Light Mode reconstructed Upload Menu (bottom: calc(100% + 8px), width: 224px, max-width: min(236px, calc(100vw - 24px)), padding: 5px, gap: 2px, border-radius: 12px, item height: 36px, padding: 0 10px, border-radius: 8px, gap: 10px, font-size: 14px, font-weight: 450, 18x18 uniform icon stroke-width 1.75)
    expect(css).toMatch(
      /#plus-popover-menu\.plus-popover-menu\s*\{[^}]*bottom:\s*calc\(100%\s*\+\s*8px\);[^}]*min-width:\s*min\(224px,\s*calc\(100vw\s*-\s*24px\)\);[^}]*width:\s*224px;[^}]*max-width:\s*min\(236px,\s*calc\(100vw\s*-\s*24px\)\);[^}]*padding:\s*5px;[^}]*gap:\s*2px;[^}]*border-radius:\s*12px;/s,
    );
    expect(css).toMatch(
      /#plus-popover-menu\.plus-popover-menu\s+\.plus-menu-item\s*\{[^}]*min-height:\s*36px;[^}]*height:\s*36px;[^}]*padding:\s*0\s+10px;[^}]*border-radius:\s*8px;[^}]*gap:\s*10px;[^}]*color:\s*#1f1e1d;[^}]*background:\s*transparent;[^}]*font-size:\s*14px;[^}]*font-weight:\s*450;/s,
    );
    expect(css).toMatch(
      /\.plus-menu-item-icon\s*\{[^}]*width:\s*18px;[^}]*height:\s*18px;[^}]*color:\s*#3d3d3a;/s,
    );
    expect(css).toMatch(
      /\.plus-menu-item-icon\s+svg\s*\{[^}]*width:\s*18px;[^}]*height:\s*18px;[^}]*stroke-width:\s*1\.75;/s,
    );

    // Guest Footer CSS (.sb-guest-login-btn, .sb-guest-login-icon, .sb-guest-login-label)
    expect(css).toMatch(
      /\.sb-guest-login-btn,\s*#sb-guest-account-btn\.sb-guest-login-btn\s*\{[^}]*min-height:\s*40px;[^}]*height:\s*40px;[^}]*padding:\s*0\s+10px;[^}]*border-radius:\s*10px;[^}]*color:\s*#37352f;/s,
    );
    expect(css).toMatch(
      /\.sb-guest-login-icon\s*\{[^}]*width:\s*20px;[^}]*height:\s*20px;[^}]*color:\s*#57534e;/s,
    );
    expect(css).toMatch(
      /\.sb-guest-login-label\s*\{[^}]*font-size:\s*14px;[^}]*font-weight:\s*500;[^}]*color:\s*#37352f;/s,
    );

    // Desktop default: prioritizes File Upload + Screen Capture
    const openMenuHtml = renderToString(
      <ProblemInput
        initialPlusMenuOpen
        deviceSignals={{
          userAgent:
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
          platform: "Win32",
          maxTouchPoints: 0,
        }}
      />,
    );
    expect(openMenuHtml).toContain('id="plus-popover-menu"');
    expect(openMenuHtml).toContain("plus-popover-menu has-screen-capture-item open");
    expect(openMenuHtml).toContain('data-placement="top"');
    expect(openMenuHtml).toContain("plus-menu-item-icon");
    expect(openMenuHtml).toContain('id="menu-item-upload-file"');
    expect(openMenuHtml).toContain("Tải tệp từ thiết bị");
    expect(openMenuHtml).toContain('id="menu-item-screen-capture"');
    expect(openMenuHtml).toContain("Chụp màn hình");
    expect(openMenuHtml).not.toContain('id="menu-item-camera"');

    // Mobile phone: prioritizes File Upload + Camera
    const mobileMenuHtml = renderToString(
      <ProblemInput
        initialPlusMenuOpen
        deviceSignals={{
          userAgent:
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
          platform: "iPhone",
          maxTouchPoints: 5,
        }}
      />,
    );
    expect(mobileMenuHtml).toContain("plus-popover-menu has-camera-item open");
    expect(mobileMenuHtml).toContain('id="menu-item-upload-file"');
    expect(mobileMenuHtml).toContain("Tải tệp từ thiết bị");
    expect(mobileMenuHtml).toContain('id="menu-item-camera"');
    expect(mobileMenuHtml).toContain("Chụp ảnh đề bài");
    expect(mobileMenuHtml).not.toContain('id="menu-item-screen-capture"');
  });

  it("3. AXO V9.3/V9.4: Dead Classroom CSS Cleanup, Sticky Guest Footer, and Two-Tier Light Mode Composer Typography & Toolbar", () => {
    const css = readFileSync(
      new URL("../../styles/global.css", import.meta.url),
      "utf-8",
    );
    const problemInputSrc = readFileSync(
      new URL("../ProblemInput.tsx", import.meta.url),
      "utf-8",
    );

    // Phase 1.2: Dead Classroom / Assignment / Monitor / LiveSession CSS rules removed
    expect(css).not.toContain("#sidebar-group-teacher");
    expect(css).not.toContain(".class-card");
    expect(css).not.toContain(".assignment-card");
    expect(css).not.toContain(".observe-table");
    expect(css).not.toContain(".monitor-luoi");
    expect(css).not.toContain(".live-dock");
    expect(css).not.toContain(".geo3d-lop");
    expect(css).not.toContain(".home-work-o");

    // Phase 5.2: Sticky #sb-footer and 40px Guest Login Button
    expect(css).toMatch(
      /#sb-footer,\s*\.sb-footer\s*\{[^}]*position:\s*sticky;[^}]*bottom:\s*0;[^}]*margin-top:\s*auto;[^}]*flex-shrink:\s*0;/s,
    );

    // V9.4 Two-Tier Composer container, toolbar & typography
    expect(css).toMatch(
      /\.home-composer-box\s*\{[^}]*min-height:\s*118px;[^}]*padding:\s*14px\s+14px\s+10px\s+16px;[^}]*border-radius:\s*20px;/s,
    );
    expect(css).toMatch(
      /\.home-composer-box\s+\.composer-toolbar\s*\{[^}]*justify-content:\s*space-between;[^}]*min-height:\s*36px;[^}]*border-top:\s*none;/s,
    );
    expect(css).toMatch(
      /\.home-composer-box\s+\.composer-textarea\s*\{[^}]*font-size:\s*16px;[^}]*font-weight:\s*400;[^}]*line-height:\s*24px;[^}]*color:\s*#1f1f1f;/s,
    );
    expect(problemInputSrc).toContain('el.style.height = "48px";');
  });
});
