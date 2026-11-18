import { describe, expect, it, vi } from "vitest";
import { executeScreenCaptureFlow } from "../ProblemInput";
import { captureScreenStillFrame } from "../ScreenCaptureDialog";
import { validateComposerFile } from "../../llm/input";

describe("one-step screen capture", () => {
  it("passes the captured file directly to the composer and releases the temporary preview", async () => {
    const file = new File(["image"], "screen.png", { type: "image/png" });
    const onCaptured = vi.fn();
    const revokeUrl = vi.fn();
    const result = await executeScreenCaptureFlow({
      busyRef: { current: false },
      onCaptured,
      checkSupport: () => null,
      captureFrame: async () => ({ file, previewUrl: "blob:temporary", width: 10, height: 10, stoppedTracks: 1 }),
      revokeUrl,
    });
    expect(result).toBe("attached");
    expect(onCaptured).toHaveBeenCalledExactlyOnceWith(file);
    expect(revokeUrl).toHaveBeenCalledExactlyOnceWith("blob:temporary");
  });

  it("rejects a stream without a video track and releases all tracks", async () => {
    const stop = vi.fn();
    const stream = { getVideoTracks: () => [], getTracks: () => [{ stop }] } as unknown as MediaStream;
    await expect(captureScreenStillFrame({ isSecureContext: true, getDisplayMedia: async () => stream }))
      .rejects.toMatchObject({ name: "NotReadableError" });
    expect(stop).toHaveBeenCalledOnce();
  });

  it("rejects a selection exceeding the backend total size limit", () => {
    const result = validateComposerFile({ name: "last.png", type: "image/png", size: 6 * 1024 * 1024 }, [
      { name: "first.png", size: 10 * 1024 * 1024 },
      { name: "second.png", size: 10 * 1024 * 1024 },
    ]);
    expect(result.ok).toBe(false);
  });
});
