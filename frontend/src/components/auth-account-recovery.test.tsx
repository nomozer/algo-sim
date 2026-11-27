import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { AuthPageView } from "./AuthGate";
import { canonicalPathForView, resolveLocationRoute } from "./AxoErrorExperience";
import { useToastStore } from "./TopNav";
import { useAppStore } from "../state/store";
import { useAuthStore } from "../state/auth";

/** Xác minh email & khôi phục mật khẩu (run `authentication-account-recovery`). */

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
  Object.assign(useToastStore.getInitialState(), useToastStore.getState());
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

const STUDENT = {
  id: 7,
  email: "hs@example.test",
  displayName: "Học sinh",
  role: "student" as const,
  mustChangePassword: false,
  emailVerified: false,
};

describe("Xác minh email và khôi phục mật khẩu", () => {
  beforeEach(() => {
    useAppStore.getState().reset();
    useAuthStore.setState({ user: null, resolved: true, busy: false, error: null, authGate: null, lastVerificationStatus: null });
    syncStoreForSSR();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    useAuthStore.setState({ user: null, lastVerificationStatus: null });
    syncStoreForSSR();
  });

  it("định tuyến /verify-email ⇄ view `verify`", () => {
    expect(resolveLocationRoute("/verify-email")).toEqual({ kind: "view", view: "verify" });
    expect(resolveLocationRoute("/verify-email", "", "?token=abc")).toEqual({ kind: "view", view: "verify" });
    expect(canonicalPathForView("verify")).toBe("/verify-email");
    expect(resolveLocationRoute("/reset", "", "?reset_token=abc")).toEqual({ kind: "view", view: "reset" });
  });

  it("trang xác minh không có token báo liên kết không đầy đủ, không tự gọi API", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const html = renderToString(<AuthPageView mode="verify" />);
    expect(html).toContain('id="view-verify"');
    expect(html).toContain('id="verify-error-banner"');
    expect(html).toContain("Liên kết xác minh không đầy đủ");
    expect(html).not.toContain('id="btn-verify-submit"');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("verifyEmail gửi POST token và đánh dấu emailVerified; lỗi trả câu tiếng Việt của máy chủ", async () => {
    useAuthStore.setState({ user: { ...STUDENT } });
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        calls.push({ url, init });
        if (url === "/api/auth/verify-email") {
          const body = JSON.parse(String(init?.body));
          return body.token === "tok-ok"
            ? json({ ok: true, verified: true })
            : json({ detail: "Liên kết xác minh email không hợp lệ, đã được dùng hoặc đã hết hạn." }, 400);
        }
        if (url === "/api/auth/me") return json({ user: { ...STUDENT, emailVerified: true }, entitlement: null });
        throw new Error(`Unexpected URL: ${url}`);
      }),
    );
    const bad = await useAuthStore.getState().verifyEmail("tok-bad");
    expect(bad).toEqual({ ok: false, error: "Liên kết xác minh email không hợp lệ, đã được dùng hoặc đã hết hạn." });
    const ok = await useAuthStore.getState().verifyEmail("tok-ok");
    expect(ok.ok).toBe(true);
    expect(useAuthStore.getState().user?.emailVerified).toBe(true);
    const verifyCall = calls.find((c) => c.url === "/api/auth/verify-email");
    expect(verifyCall?.init?.method).toBe("POST");
    expect(verifyCall?.init?.credentials).toBe("include");
  });

  it("resendVerification phân biệt queued / throttled / unavailable", async () => {
    const replies = [
      json({ ok: true, status: "queued" }),
      json({ detail: "Bạn vừa yêu cầu gửi thư xác minh. Vui lòng đợi một chút rồi thử lại." }, 429),
      json({ ok: false, status: "unavailable" }),
    ];
    vi.stubGlobal("fetch", vi.fn(async () => replies.shift()!));
    expect(await useAuthStore.getState().resendVerification()).toEqual({ ok: true, status: "queued" });
    const throttled = await useAuthStore.getState().resendVerification();
    expect(throttled.ok).toBe(false);
    expect(throttled.status).toBe("throttled");
    expect(await useAuthStore.getState().resendVerification()).toEqual({ ok: false, status: "unavailable" });
  });

  it("đăng ký ghi lại trạng thái thư xác minh do máy chủ trả", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => json({ user: STUDENT, entitlement: null, verification: { status: "queued" } })),
    );
    const ok = await useAuthStore.getState().register({ email: STUDENT.email, displayName: "HS", password: "x".repeat(10) });
    expect(ok).toBe(true);
    expect(useAuthStore.getState().lastVerificationStatus).toBe("queued");
  });

  it("trang đặt lại/xác minh gỡ token khỏi thanh địa chỉ và tắt Referer; quên mật khẩu dùng câu trung tính", () => {
    const src = readFileSync(new URL("./AuthPageView.tsx", import.meta.url), "utf8");
    expect(src).toContain('meta.content = "no-referrer"');
    expect(src).toContain("window.history.replaceState(");
    expect(src).toContain('mode === "reset" ? "/reset" : "/verify-email"');
    expect(src).toContain(
      "Nếu địa chỉ email đủ điều kiện khôi phục tài khoản, bạn sẽ nhận được hướng dẫn đặt lại mật khẩu.",
    );
    expect(src).not.toContain("hướng dẫn đặt lại mật khẩu (hiệu lực 15 phút) sẽ được gửi");
  });
});
