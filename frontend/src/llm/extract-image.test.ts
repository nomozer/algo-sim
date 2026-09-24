import { describe, expect, it } from "vitest";
import { extractImageViaServer } from "./client";

/**
 * `extractImageViaServer` — PHOTO_PROBLEM_TO_SCENE_END_TO_END §7. 0 lượt gọi mạng:
 * `fetch` bị thay bằng bản giả ngay trong từng test (guard offline vẫn đứng sau).
 */

interface LuotGoi {
  url: string;
  init: RequestInit;
}

function giaFetch(tra: () => Response | Promise<Response>): LuotGoi[] {
  const goi: LuotGoi[] = [];
  globalThis.fetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
    goi.push({ url: String(url), init: init ?? {} });
    return tra();
  }) as typeof fetch;
  return goi;
}

describe("extractImageViaServer", () => {
  it("POST đúng đường, đúng thân, mang theo signal để huỷ được", async () => {
    const goi = giaFetch(() => new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    const ctl = new AbortController();
    await extractImageViaServer(
      { content: "AAAA", mime_type: "image/png", filename: "a.png", rotation: 90 },
      ctl.signal,
    );
    expect(goi).toHaveLength(1);
    expect(goi[0].url).toBe("/api/image/extract");
    expect(goi[0].init.method).toBe("POST");
    expect(JSON.parse(String(goi[0].init.body))).toEqual({
      content: "AAAA",
      mime_type: "image/png",
      filename: "a.png",
      rotation: 90,
    });
    expect(goi[0].init.signal).toBe(ctl.signal);
  });

  it("huỷ CHỦ ĐỘNG ném AbortError — không bị đổi thành lời nhắc bật máy chủ", async () => {
    globalThis.fetch = (async () => {
      throw new DOMException("aborted", "AbortError");
    }) as typeof fetch;
    await expect(extractImageViaServer({ content: "A", rotation: 0 })).rejects.toMatchObject({
      name: "AbortError",
    });
  });

  it("lỗi mạng thường vẫn là lời nhắc kết nối", async () => {
    globalThis.fetch = (async () => {
      throw new TypeError("Failed to fetch");
    }) as typeof fetch;
    await expect(extractImageViaServer({ content: "A", rotation: 0 })).rejects.toThrow(
      /Không kết nối được máy chủ/,
    );
  });

  it("máy chủ từ chối ảnh ⇒ thông điệp tiếng Việt của máy chủ đi nguyên", async () => {
    giaFetch(
      () =>
        new Response(JSON.stringify({ error: "Ảnh quá lớn (tối đa 10MB).", reason_code: "IMAGE_TOO_LARGE" }), {
          status: 400,
        }),
    );
    await expect(extractImageViaServer({ content: "A", rotation: 0 })).rejects.toThrow(
      "Ảnh quá lớn (tối đa 10MB).",
    );
  });
});
