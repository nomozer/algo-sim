import { beforeEach } from "vitest";

/**
 * Guard offline cho vitest (M7.14T) — song song conftest.py phía backend.
 *
 * Test frontend là engine tất định + validator: KHÔNG được gọi mạng (kể cả
 * /api/analyze, /api/edit). Stub fetch để mọi request đều ném lỗi ⇒ toàn bộ
 * suite xanh CHỨNG MINH 0 network call, thay vì chỉ "đúng tình cờ".
 */

export const BLOCK_MESSAGE = "Network call blocked during offline vitest.";

beforeEach(() => {
  globalThis.fetch = (async (input: RequestInfo | URL) => {
    throw new Error(`${BLOCK_MESSAGE} (${String(input)})`);
  }) as typeof fetch;
});
