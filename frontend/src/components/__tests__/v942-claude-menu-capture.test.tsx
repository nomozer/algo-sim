import { existsSync, readFileSync, statSync } from "node:fs";
import { describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { registerAllSimulations } from "../../simulations";
import { useAppStore } from "../../state/store";
import { ProblemInput } from "../ProblemInput";
import {
  captureScreenStillFrame,
  classifyScreenCaptureError,
  classifyScreenCaptureSupportError,
  resolveUploadMenuCapabilities,
  stopAllMediaStreamTracks,
} from "../ScreenCaptureDialog";

registerAllSimulations();

describe("AXO V9.4.2 — Claude Light Mode Upload Menu, Device-Aware Screen Capture, Heading & Favicon", () => {
  it("1. resolveUploadMenuCapabilities kết hợp phân loại thiết bị + khả năng API thực tế (Desktop -> Chụp màn hình, Phone -> Chụp ảnh đề bài, Tablet hỗ trợ cả hai giữ cả hai)", () => {
    const desktopCaps = resolveUploadMenuCapabilities({
      deviceSignals: {
        userAgent:
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        platform: "Win32",
        maxTouchPoints: 0,
      },
      isSecureContext: true,
      hasDisplayMedia: true,
      hasUserMedia: true,
    });
    expect(desktopCaps).toEqual({
      deviceKind: "desktop",
      showUploadFile: true,
      showScreenCapture: true,
      showCamera: false,
      canCaptureScreen: true,
      canCaptureCamera: true,
      visibleActionCount: 2,
    });

    // Touch-screen Windows laptop still behaves as desktop (prioritizes Screen Capture, not mobile Camera)
    const touchLaptopCaps = resolveUploadMenuCapabilities({
      deviceSignals: {
        userAgentDataMobile: false,
        userAgentDataPlatform: "Windows",
        userAgent:
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        platform: "Win32",
        maxTouchPoints: 10,
      },
      isSecureContext: true,
      hasDisplayMedia: true,
      hasUserMedia: true,
    });
    expect(touchLaptopCaps.deviceKind).toBe("desktop");
    expect(touchLaptopCaps.showScreenCapture).toBe(true);
    expect(touchLaptopCaps.showCamera).toBe(false);
    expect(touchLaptopCaps.visibleActionCount).toBe(2);

    // Desktop browser without getDisplayMedia still shows Screen Capture menu item and gracefully opens fallback dialog on click
    const desktopUnsupportedApiCaps = resolveUploadMenuCapabilities({
      deviceSignals: {
        userAgent:
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        platform: "MacIntel",
        maxTouchPoints: 0,
      },
      isSecureContext: true,
      hasDisplayMedia: false,
      hasUserMedia: false,
    });
    expect(desktopUnsupportedApiCaps.showScreenCapture).toBe(true);
    expect(desktopUnsupportedApiCaps.canCaptureScreen).toBe(false);

    // Mobile phone prioritizes Camera and hides Screen Capture
    const phoneCaps = resolveUploadMenuCapabilities({
      deviceSignals: {
        userAgent:
          "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        platform: "iPhone",
        maxTouchPoints: 5,
      },
      isSecureContext: true,
      hasDisplayMedia: false,
      hasUserMedia: true,
    });
    expect(phoneCaps).toEqual({
      deviceKind: "phone",
      showUploadFile: true,
      showScreenCapture: false,
      showCamera: true,
      canCaptureScreen: false,
      canCaptureCamera: true,
      visibleActionCount: 2,
    });

    // Tablet without getDisplayMedia -> File Upload + Camera (2 items)
    const tabletCameraOnly = resolveUploadMenuCapabilities({
      deviceSignals: {
        userAgent:
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        platform: "MacIntel",
        maxTouchPoints: 5,
      },
      isSecureContext: true,
      hasDisplayMedia: false,
      hasUserMedia: true,
    });
    expect(tabletCameraOnly.deviceKind).toBe("tablet");
    expect(tabletCameraOnly.showCamera).toBe(true);
    expect(tabletCameraOnly.showScreenCapture).toBe(false);
    expect(tabletCameraOnly.visibleActionCount).toBe(2);

    // Tablet supporting BOTH getUserMedia and getDisplayMedia -> keeps both accessible (3 items)
    const tabletBoth = resolveUploadMenuCapabilities({
      deviceSignals: {
        userAgent:
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        platform: "MacIntel",
        maxTouchPoints: 5,
      },
      isSecureContext: true,
      hasDisplayMedia: true,
      hasUserMedia: true,
    });
    expect(tabletBoth.deviceKind).toBe("tablet");
    expect(tabletBoth.showCamera).toBe(true);
    expect(tabletBoth.showScreenCapture).toBe(true);
    expect(tabletBoth.visibleActionCount).toBe(3);

    const tabletHtml = renderToString(
      <ProblemInput
        initialPlusMenuOpen
        deviceSignals={{
          userAgent:
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
          platform: "MacIntel",
          maxTouchPoints: 5,
        }}
        capabilitySignals={{
          isSecureContext: true,
          hasDisplayMedia: true,
          hasUserMedia: true,
        }}
      />,
    );
    expect(tabletHtml).toContain('id="menu-item-upload-file"');
    expect(tabletHtml).toContain('id="menu-item-camera"');
    expect(tabletHtml).toContain('id="menu-item-screen-capture"');
  });

  it("2. captureScreenStillFrame gọi getDisplayMedia({ video: true, audio: false }), lấy đúng 1 ảnh tĩnh PNG và DỪNG NGAY LẬP TỨC toàn bộ media tracks cả khi thành công lẫn khi lỗi", async () => {
    const stopVideo = vi.fn();
    const stopExtra = vi.fn();
    const fakeStream = {
      getTracks: () => [{ stop: stopVideo }, { stop: stopExtra }],
    } as unknown as MediaStream;

    const getDisplayMediaMock = vi.fn().mockResolvedValue(fakeStream);
    const pngBytes = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]);

    const captured = await captureScreenStillFrame({
      isSecureContext: true,
      getDisplayMedia: getDisplayMediaMock,
      extractFrameFromStream: async (stream) => {
        expect(stream).toBe(fakeStream);
        // Tracks must still be active during frame grab, then stopped right after
        expect(stopVideo).not.toHaveBeenCalled();
        return {
          blob: new Blob([pngBytes], { type: "image/png" }),
          width: 1440,
          height: 900,
        };
      },
      createObjectURL: () => "blob:axo-screen-preview-test",
      now: () => 1700000000000,
    });

    expect(getDisplayMediaMock).toHaveBeenCalledTimes(1);
    expect(getDisplayMediaMock).toHaveBeenCalledWith({
      video: true,
      audio: false,
    });
    expect(stopVideo).toHaveBeenCalledTimes(1);
    expect(stopExtra).toHaveBeenCalledTimes(1);
    expect(captured.stoppedTracks).toBe(2);
    expect(captured.file.name).toBe("chup-man-hinh-de-toan-1700000000000.png");
    expect(captured.file.type).toBe("image/png");
    expect(captured.width).toBe(1440);
    expect(captured.height).toBe(900);
    expect(captured.previewUrl).toBe("blob:axo-screen-preview-test");

    // When frame extraction throws, tracks MUST still be stopped in finally {}
    const stopOnFailure = vi.fn();
    const failingStream = {
      getTracks: () => [{ stop: stopOnFailure }],
    } as unknown as MediaStream;

    await expect(
      captureScreenStillFrame({
        isSecureContext: true,
        getDisplayMedia: vi.fn().mockResolvedValue(failingStream),
        extractFrameFromStream: async () => {
          throw Object.assign(new Error("Canvas failed"), { name: "NotReadableError" });
        },
      }),
    ).rejects.toThrow("Canvas failed");
    expect(stopOnFailure).toHaveBeenCalledTimes(1);

    // Safe helper handles null/undefined streams gracefully
    expect(stopAllMediaStreamTracks(null)).toBe(0);
    expect(stopAllMediaStreamTracks(undefined)).toBe(0);

    // Unsupported environment rejects cleanly
    await expect(
      captureScreenStillFrame({
        isSecureContext: false,
        getDisplayMedia: getDisplayMediaMock,
      }),
    ).rejects.toMatchObject({ name: "UnsupportedScreenCaptureError" });
  });

  it("3. classifyScreenCaptureSupportError & classifyScreenCaptureError trả về thông báo tiếng Việt thân thiện, không lộ lỗi kỹ thuật thô", () => {
    expect(
      classifyScreenCaptureSupportError({ isSecureContext: true, hasDisplayMedia: true }),
    ).toBeNull();

    const unsupported = classifyScreenCaptureSupportError({
      isSecureContext: true,
      hasDisplayMedia: false,
    });
    expect(unsupported).not.toBeNull();
    expect(unsupported!.code).toBe("unsupported");
    expect(unsupported!.canRetry).toBe(false);
    expect(unsupported!.title).toContain("chưa hỗ trợ chụp màn hình");
    expect(unsupported!.description).not.toMatch(/NotAllowedError|getDisplayMedia|TypeError/i);

    const notSupportedErr = classifyScreenCaptureError({ name: "NotSupportedError" });
    expect(notSupportedErr.code).toBe("unsupported");
    expect(notSupportedErr.canRetry).toBe(false);

    const deniedByUser = classifyScreenCaptureError({ name: "NotAllowedError" });
    expect(deniedByUser.code).toBe("cancelled");
    expect(deniedByUser.canRetry).toBe(false);

    const systemBlocked = classifyScreenCaptureError({
      name: "NotAllowedError",
      message: "Permission denied by system",
    });
    expect(systemBlocked.code).toBe("permission_denied");
    expect(systemBlocked.canRetry).toBe(true);
    expect(systemBlocked.description).not.toMatch(/NotAllowedError|Permission denied by system/i);

    const aborted = classifyScreenCaptureError({ name: "AbortError" });
    expect(aborted.code).toBe("cancelled");

    const notFound = classifyScreenCaptureError({ name: "NotFoundError" });
    expect(notFound.code).toBe("not_found");
    expect(notFound.canRetry).toBe(true);

    const unreadable = classifyScreenCaptureError({ name: "NotReadableError" });
    expect(unreadable.code).toBe("unavailable");
    expect(unreadable.canRetry).toBe(true);

    const unknown = classifyScreenCaptureError(new Error("Internal OS pipe broken"));
    expect(unknown.code).toBe("unknown");
    expect(unknown.description).not.toContain("Internal OS pipe broken");
  });

  it("4. Composer không tự mở modal xác nhận chụp màn hình", () => {
    const html = renderToString(<ProblemInput />);
    expect(html).not.toContain('id="screen-capture-dialog"');
    expect(useAppStore.getState().analyzing).toBe(false);
  });

  it("5. Tiêu đề “Em muốn dựng hình nào?” tăng nhẹ lên 33px desktop (line-height 1.22) kèm thang responsive mượt và không có mục thừa ngoài phạm vi Axo trong Upload Menu", () => {
    const css = readFileSync(
      new URL("../../styles/global.css", import.meta.url),
      "utf-8",
    );
    expect(css).toContain("--axo-hero-title-size: 42px;");
    expect(css).toContain("--axo-hero-title-size: 40px;");
    expect(css).toContain("--axo-hero-title-size: 36px;");
    expect(css).toContain("--axo-hero-title-size: 32px;");
    expect(css).toContain("--axo-hero-title-size: 28px;");
    expect(css).toContain("--axo-hero-title-size: 26px;");
    expect(css).toMatch(
      /\.home-hero-title,\s*\.hero-title\s*\{[^}]*font-size:\s*var\(--axo-hero-title-size\);[^}]*line-height:\s*1\.18;/s,
    );

    const desktopOpenHtml = renderToString(<ProblemInput initialPlusMenuOpen />);
    for (const forbiddenLabel of [
      "Cowork",
      "Skills",
      "Plugins",
      "GitHub",
      "Research",
      "Web Search",
      "Sonnet",
      "Opus",
    ]) {
      expect(desktopOpenHtml).not.toContain(forbiddenLabel);
    }

    // All menu icons use uniform 18x18 viewBox="0 0 24 24" stroke-width="1.75"
    const menuStart = desktopOpenHtml.indexOf('id="plus-popover-menu"');
    const menuEnd = desktopOpenHtml.indexOf('class="composer-sr-only"', menuStart);
    const menuSlice = desktopOpenHtml.slice(menuStart, menuEnd);
    const iconMatches = [...menuSlice.matchAll(/data-icon="([^"]+)"/g)].map((m) => m[1]);
    expect(iconMatches).toEqual(["paperclip", "screen-capture"]);
    expect(menuSlice).not.toContain('stroke-width="2.4"');
  });

  it("6. Favicon Axo tối ưu viewBox='14.5 14.7 518 518', giữ nguyên nhận diện khối lập phương chữ A, bổ sung PNG 16x16 & 32x32 và liên kết chuẩn trong index.html", () => {
    const svgPath = new URL("../../../public/favicon.svg", import.meta.url);
    const png16Path = new URL("../../../public/favicon-16x16.png", import.meta.url);
    const png32Path = new URL("../../../public/favicon-32x32.png", import.meta.url);
    const indexHtmlPath = new URL("../../../index.html", import.meta.url);

    const svg = readFileSync(svgPath, "utf-8");
    expect(svg).toContain('viewBox="14.5 14.7 518 518"');
    expect(svg).toContain('transform="translate(18.0 59.5)"');
    expect(svg).toContain('stroke-width="5"');
    expect(svg).toContain('fill="#111111"');
    expect(svg).toContain('fill="#FFFFFF"');

    expect(existsSync(png16Path)).toBe(true);
    expect(existsSync(png32Path)).toBe(true);
    expect(statSync(png16Path).size).toBeGreaterThan(150);
    expect(statSync(png32Path).size).toBeGreaterThan(250);

    const indexHtml = readFileSync(indexHtmlPath, "utf-8");
    expect(indexHtml).toContain('href="/favicon.svg"');
    expect(indexHtml).toContain('sizes="32x32" href="/favicon-32x32.png"');
    expect(indexHtml).toContain('sizes="16x16" href="/favicon-16x16.png"');
  });
});
