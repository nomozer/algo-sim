import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderToString } from "react-dom/server";
import { HomeView } from "./HomeView";
import {
  ProblemInput,
  describeComposerError,
  describeHomeRefusal,
  runComposerSubmit,
} from "./ProblemInput";
import { LibraryView } from "./LibraryView";
import { HistoryView } from "./HistoryView";
import {
  AuthGate,
  AuthPageView,
  AdminWorkspaceView,
  buildAdminAnalyticsChartModel,
  formatAdminLatency,
} from "./AuthGate";
import {
  HEADER_COMPACT_BREAKPOINT_PX,
  ToastContainer,
  TopNav,
  TopNavAccount,
  shouldUseCompactHeaderAccount,
  useToastStore,
} from "./TopNav";
import { starterEntries } from "../data/offline-catalog";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest, historyStore } from "../state/history";
import { useAppStore } from "../state/store";
import { useAuthStore } from "../state/auth";

registerAllSimulations();

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
  Object.assign(useToastStore.getInitialState(), useToastStore.getState());
}

describe("AXO V2.8 — Checkpoint B: Refusal Card, Duplicate Toast & Composer State Machine", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAuthStore.setState({
      user: null,
      resolved: true,
      busy: false,
      error: null,
      authGate: null,
    });
    useToastStore.getState().clearToasts();
    syncStoreForSSR();
  });

  afterEach(() => {
    useToastStore.getState().clearToasts();
    useAppStore.getState().reset();
    syncStoreForSSR();
  });

  it("1. Phản hồi đề ngoài phạm vi phát đúng 1 Toast gọn (không render #home-composer-refusal dưới ô nhập), đổi AlgoSim → Axo và giữ nguyên store diagnostics + đề đã nhập", async () => {
    const rawUnsupported = {
      status: "unsupported" as const,
      failure_category: "out_of_scope",
      error_code: "OUT_OF_SCOPE",
      reason_code: "not_geometry",
      refusal_cause: "SOURCE" as const,
      reason: "internal_out_of_scope_trace",
      learner_reason:
        "Đề bài không thuộc phạm vi hình học không gian mà AlgoSim đang hỗ trợ.",
    };
    const prompt = "Cân bằng phương trình Fe + O2 -> Fe3O4";
    useAppStore.getState().setProblemText(prompt);

    await runComposerSubmit({
      canSubmit: true,
      lockRef: { current: false },
      problemText: prompt,
      attachment: null,
      health: { ok: true, hasKey: true, cachedProblems: 6 },
      analyzeFn: async () => rawUnsupported,
    });
    syncStoreForSSR();

    const homeHtml = renderToString(<HomeView />);
    expect(homeHtml).not.toContain('id="home-composer-refusal"');
    expect(homeHtml).not.toContain("composer-refusal-wrap");

    expect(useToastStore.getState().toasts).toHaveLength(1);
    const toastHtml = renderToString(<ToastContainer />);
    expect(toastHtml).toContain("Đề bài chưa được hỗ trợ");
    expect(toastHtml).toContain(
      "Đề bài không thuộc phạm vi hình học không gian mà Axo đang hỗ trợ.",
    );
    expect(toastHtml).toContain("Bạn có thể thử các bài về thiết diện, khoảng cách, góc hoặc thể tích.");
    expect(toastHtml).not.toContain("Không xác định được");
    expect(toastHtml).not.toContain("AlgoSim");
    expect(toastHtml).not.toContain("internal_out_of_scope_trace");

    // Gửi lặp lại cùng lỗi cập nhật đúng 1 Toast, không spam chồng nhiều Toast
    await runComposerSubmit({
      canSubmit: true,
      lockRef: { current: false },
      problemText: prompt,
      attachment: null,
      health: { ok: true, hasKey: true, cachedProblems: 6 },
      analyzeFn: async () => rawUnsupported,
    });
    expect(useToastStore.getState().toasts).toHaveLength(1);

    // Raw diagnostics trong store và văn bản đã nhập phải giữ nguyên 100%
    expect(useAppStore.getState().unsupported).toEqual(rawUnsupported);
    expect(useAppStore.getState().problemText).toBe(prompt);
  });

  it("2. Phản hồi thiếu dữ kiện (MISSING_INFORMATION / SOURCE) có tiêu đề đúng bản chất và hướng dẫn bổ sung dữ kiện trên ô nhập", () => {
    const view = describeHomeRefusal({
      status: "unsupported",
      failure_category: "insufficient_specification",
      error_code: "GIVEN_VALUE_NOT_IN_SOURCE",
      refusal_cause: "SOURCE",
      reason: "missing_height",
      learner_reason: "Đề bài chưa cho đủ kích thước chiều cao để dựng hình duy nhất.",
    });
    expect(view.title).toBe("Đề bài chưa đủ dữ kiện để dựng hình");
    expect(view.body).toBe(
      "Đề bài chưa cho đủ kích thước chiều cao để dựng hình duy nhất.",
    );
    expect(view.hint).toContain("bổ sung dữ kiện");
  });

  it("3. useToastStore.showToast chống hiển thị trùng cho cùng sự kiện nhưng giữ nguyên hai lỗi độc lập", () => {
    useToastStore.getState().showToast({
      tone: "info",
      title: "Chưa thể dựng hình",
      description:
        "Dịch vụ phân tích đề hiện chưa sẵn sàng. Em vẫn có thể mở các mô hình mẫu bên dưới.",
      durationMs: 0,
    });
    useToastStore.getState().showToast({
      tone: "info",
      title: "Chưa thể dựng hình",
      description:
        "Dịch vụ phân tích đề hiện chưa sẵn sàng. Em vẫn có thể mở các mô hình mẫu bên dưới.",
      durationMs: 0,
    });
    expect(useToastStore.getState().toasts).toHaveLength(1);

    // Một lỗi độc lập khác (vd đính kèm tệp PDF) không bị nuốt mất
    useToastStore.getState().showToast({
      tone: "error",
      title: "Chưa hỗ trợ tệp PDF",
      description: "Vui lòng chọn ảnh PNG, JPEG, WEBP hoặc tệp DOCX.",
      durationMs: 0,
    });
    expect(useToastStore.getState().toasts).toHaveLength(2);
  });

  it("4. Máy trạng thái IDLE → SUBMITTING → ERROR / UNSUPPORTED / SUCCESS + RETRY: chặn nhấn nhiều lần liên tiếp và giữ nguyên đề bài khi lỗi mạng", async () => {
    const lockRef = { current: false };
    let resolveAnalyze!: (val: any) => void;
    const analyzeSpy = vi.fn(
      () =>
        new Promise((resolve) => {
          resolveAnalyze = resolve;
        }),
    );

    useAppStore.getState().setProblemText("Cho hình chóp S.ABCD có SA vuông góc đáy.");

    // Nhấn nút liên tiếp 3 lần khi request đầu đang bay
    const p1 = runComposerSubmit({
      canSubmit: true,
      lockRef,
      problemText: useAppStore.getState().problemText,
      attachment: null,
      health: { ok: true, hasKey: false, cachedProblems: 0 },
      analyzeFn: analyzeSpy as any,
    });
    const p2 = runComposerSubmit({
      canSubmit: true,
      lockRef,
      problemText: useAppStore.getState().problemText,
      attachment: null,
      health: { ok: true, hasKey: false, cachedProblems: 0 },
      analyzeFn: analyzeSpy as any,
    });
    const p3 = runComposerSubmit({
      canSubmit: true,
      lockRef,
      problemText: useAppStore.getState().problemText,
      attachment: null,
      health: { ok: true, hasKey: false, cachedProblems: 0 },
      analyzeFn: analyzeSpy as any,
    });

    expect(useAppStore.getState().analyzing).toBe(true);
    expect(analyzeSpy).toHaveBeenCalledTimes(1);

    // Kết thúc bằng UNSUPPORTED -> phát đúng 1 Toast từ chối gọn (#composer-refusal), giữ nguyên problemText
    resolveAnalyze({
      status: "unsupported",
      failure_category: "capability_gap",
      error_code: "UNSUPPORTED",
      reason: "Chưa hỗ trợ phép dựng này.",
    });
    await Promise.all([p1, p2, p3]);

    expect(useAppStore.getState().analyzing).toBe(false);
    expect(useAppStore.getState().unsupported?.failure_category).toBe("capability_gap");
    expect(useToastStore.getState().toasts).toHaveLength(1);
    expect(useToastStore.getState().toasts[0]?.id).toBe("composer-refusal");
    expect(useToastStore.getState().toasts[0]?.title).toBe("Axo chưa hỗ trợ phép dựng này");

    // Tiếp theo thử gửi lại gặp lỗi mạng -> theo quyết định Task 1 §6.2: chỉ hiện 1 Toast góc màn hình, KHÔNG tạo #home-composer-error hay nút Thử lại dưới ô nhập
    const failSpy = vi.fn().mockRejectedValue(
      new Error("Không kết nối được máy chủ phân tích."),
    );
    await runComposerSubmit({
      canSubmit: true,
      lockRef,
      problemText: useAppStore.getState().problemText,
      attachment: null,
      health: null,
      analyzeFn: failSpy as any,
    });
    await runComposerSubmit({
      canSubmit: true,
      lockRef,
      problemText: useAppStore.getState().problemText,
      attachment: null,
      health: null,
      analyzeFn: failSpy as any,
    });

    expect(useAppStore.getState().problemText).toBe(
      "Cho hình chóp S.ABCD có SA vuông góc đáy.",
    );
    expect(useAppStore.getState().unsupported).toBeNull();
    expect(useToastStore.getState().toasts).toHaveLength(1);
    expect(useToastStore.getState().toasts[0]?.title).toBe("Không kết nối được máy chủ");

    // Một lỗi độc lập khác xảy ra đồng thời không bị gộp nhầm hoặc ghi đè (§6.3)
    const aiDownSpy = vi.fn().mockRejectedValue(
      new Error("Dịch vụ phân tích đề chưa cấu hình khóa AI (503)."),
    );
    await runComposerSubmit({
      canSubmit: true,
      lockRef,
      problemText: useAppStore.getState().problemText,
      attachment: null,
      health: { ok: true, hasKey: false, cachedProblems: 0 },
      analyzeFn: aiDownSpy as any,
    });
    expect(useToastStore.getState().toasts).toHaveLength(2);
    expect(useToastStore.getState().toasts[1]?.title).toBe(
      "Dịch vụ phân tích đề hiện chưa sẵn sàng",
    );

    syncStoreForSSR();
    const errHtml = renderToString(<ProblemInput />);
    expect(errHtml).not.toContain('id="home-composer-error"');
    expect(errHtml).not.toContain('id="btn-composer-retry"');
    expect(errHtml).not.toContain("docker compose");

    // RETRY thành công -> mở đúng Workspace, xóa lỗi, chỉ ghi 1 phiên lịch sử
    const sample = starterEntries()[0]!;
    const okSpy = vi.fn().mockResolvedValue(sample.envelope);
    await runComposerSubmit({
      canSubmit: true,
      lockRef,
      problemText: useAppStore.getState().problemText,
      attachment: null,
      health: { ok: true, hasKey: true, cachedProblems: 1 },
      analyzeFn: okSpy as any,
    });

    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().analysisError).toBeNull();
    expect(historyStore.list()).toHaveLength(1);
  });

  it("5. Sửa lỗi UX nhỏ đã xác minh: AuthGate dùng tên Axo, modal đóng có aria-hidden='true', describeComposerError phân biệt lỗi mạng và dịch vụ tạm ngưng", () => {
    useAuthStore.setState({ authGate: "register" });
    syncStoreForSSR();
    const gateHtml = renderToString(<AuthGate />);
    expect(gateHtml).toContain("Em/thầy cô dùng Axo với vai trò");
    expect(gateHtml).not.toContain("AlgoSim");

    const histHtml = renderToString(<HistoryView />);
    expect(histHtml).toContain('aria-hidden="true"');

    const netInfo = describeComposerError("Không kết nối được máy chủ phân tích.", null);
    expect(netInfo?.title).toBe("Không kết nối được máy chủ");

    const svcInfo = describeComposerError(
      "Dịch vụ phân tích đề chưa cấu hình khóa AI (503).",
      { ok: true, hasKey: false, cachedProblems: 0 },
    );
    expect(svcInfo?.title).toBe("Dịch vụ phân tích đề hiện chưa sẵn sàng");

    // Forgot password view: phân biệt rõ trạng thái chưa khả dụng (không nhắc SMTP, vô hiệu hóa form ngay từ đầu) và khả dụng (§8)
    const forgotUnavailableHtml = renderToString(
      <AuthPageView mode="forgot" initialEmailRecoveryAvailable={false} />,
    );
    expect(forgotUnavailableHtml).not.toContain('id="btn-goto-reset-from-forgot"');
    expect(forgotUnavailableHtml).toContain('id="forgot-unavailable-note"');
    expect(forgotUnavailableHtml).not.toContain("SMTP");
    expect(forgotUnavailableHtml).toMatch(
      /<input[^>]*id="forgot-email-input"[^>]*disabled=""/,
    );
    expect(forgotUnavailableHtml).toMatch(
      /<button[^>]*id="btn-forgot-submit"[^>]*disabled=""/,
    );

    const forgotAvailableHtml = renderToString(
      <AuthPageView mode="forgot" initialEmailRecoveryAvailable={true} />,
    );
    expect(forgotAvailableHtml).not.toContain('id="forgot-unavailable-note"');
    expect(forgotAvailableHtml).not.toMatch(
      /<input[^>]*id="forgot-email-input"[^>]*disabled=""/,
    );

    // LibraryView đã làm sạch thuật ngữ nội bộ Workspace V6.2 (§5, §11)
    const libHtml = renderToString(<LibraryView />);
    expect(libHtml).toContain('id="library-cards-grid"');
    expect(libHtml).toContain(
      "Khám phá các bài toán hình học không gian qua mô hình 3D tương tác và từng bước dựng hình.",
    );
    expect(libHtml).not.toContain("Workspace V6.2");
  });
});

describe("AXO V2.8 — Checkpoint C: Password Reset Token, Admin RBAC, Honest Telemetry & CSV Export UI", () => {
  beforeEach(() => {
    useAppStore.getState().reset();
    useAuthStore.setState({
      user: null,
      resolved: true,
      busy: false,
      error: null,
      authGate: null,
    });
    syncStoreForSSR();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.setState({ user: null });
    syncStoreForSSR();
  });

  it("6. #view-reset yêu cầu ô nhập Mã khôi phục (#reset-token-input) và useAuthStore gửi đúng token tới /api/auth/reset-password", async () => {
    const resetHtml = renderToString(<AuthPageView mode="reset" />);
    expect(resetHtml).toContain('id="reset-token-input"');
    expect(resetHtml).toContain("Mã khôi phục");

    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url === "/api/auth/forgot-password") {
        return new Response(
          JSON.stringify({
            ok: true,
            smtpConfigured: false,
            deliveryStatus: "BLOCKED_EXTERNAL_CONFIGURATION",
            message: "Môi trường máy chủ hiện chưa cấu hình dịch vụ gửi email (SMTP).",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url === "/api/auth/reset-password") {
        const parsed = JSON.parse(String(init?.body || "{}"));
        expect(parsed.token).toBe("tok-v28-secret");
        expect(parsed.newPassword).toBe("mat-khau-moi-12345");
        return new Response(JSON.stringify({ ok: true, updated: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`Unexpected URL: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const forgotRes = await useAuthStore
      .getState()
      .requestPasswordReset("hocsinh@truong.edu.vn");
    expect(forgotRes.ok).toBe(true);
    expect(forgotRes.smtpConfigured).toBe(false);
    expect((forgotRes as any).deliveryStatus).toBe("BLOCKED_EXTERNAL_CONFIGURATION");

    const resetRes = await (useAuthStore.getState().resetPassword as any)(
      "tok-v28-secret",
      "mat-khau-moi-12345",
      "hocsinh@truong.edu.vn",
    );
    expect(resetRes.ok).toBe(true);
    expect(resetRes.updated).toBe(true);
  });

  it("7. AdminWorkspaceView chặn khách/học sinh truy cập shell quản trị, hiển thị trung thực 'Chưa đo' cho token và có nút xuất CSV ở Tài khoản & Nhật ký", () => {
    // Khách không thấy #admin-shell
    const guestAdminHtml = renderToString(<AdminWorkspaceView />);
    expect(guestAdminHtml).toContain('id="view-admin-denied"');
    expect(guestAdminHtml).not.toContain('id="admin-shell"');

    // Học sinh không thấy #admin-shell
    useAuthStore.setState({
      user: {
        id: 2,
        email: "hs@truong.edu.vn",
        displayName: "Học sinh",
        role: "student",
        mustChangePassword: false,
      },
      resolved: true,
    });
    syncStoreForSSR();
    const stuAdminHtml = renderToString(<AdminWorkspaceView />);
    expect(stuAdminHtml).toContain('id="view-admin-denied"');
    expect(stuAdminHtml).not.toContain('id="admin-shell"');

    // Quản trị viên thấy đầy đủ 4 phân hệ, trung thực "Chưa đo" và có nút xuất CSV thật
    useAuthStore.setState({
      user: {
        id: 1,
        email: "admin@axo.edu.vn",
        displayName: "Quản trị viên",
        role: "admin",
        mustChangePassword: false,
      },
      resolved: true,
    });
    syncStoreForSSR();

    const overviewHtml = renderToString(<AdminWorkspaceView initialTab="overview" />);
    expect(overviewHtml).toContain('id="admin-shell"');
    expect(overviewHtml).toContain("Chưa có dữ liệu");
    expect(overviewHtml).toContain("0/0 yêu cầu");
    expect(overviewHtml).not.toContain("0 tok");
    expect(overviewHtml).not.toContain("Ngân sách tháng (VND)");
    expect(overviewHtml).not.toContain("3.000.000");
    expect(overviewHtml).toContain('aria-hidden="true"');

    const analyticsHtml = renderToString(<AdminWorkspaceView initialTab="analytics" />);
    expect(analyticsHtml).toContain("Chưa có hoạt động phân tích trong 7 ngày qua.");
    expect(analyticsHtml).not.toContain("0%");
    expect(analyticsHtml).not.toContain("Chi phí (VND)");
    expect(analyticsHtml).not.toContain("Ngân sách &amp; chi phí (VND)");

    const accountsHtml = renderToString(<AdminWorkspaceView initialTab="accounts" />);
    expect(accountsHtml).toContain('id="btn-admin-export-users"');
    expect(accountsHtml).toContain("Xuất CSV");
    expect(accountsHtml).toContain('class="sort-arrow"');
    expect(accountsHtml).toContain('aria-sort=');
    expect(accountsHtml).not.toContain('id="admin-page-nav-group"');
    expect(accountsHtml).not.toContain('id="btn-page-prev"');
    expect(accountsHtml).not.toContain('id="btn-page-next"');

    const auditHtml = renderToString(<AdminWorkspaceView initialTab="audit" />);
    expect(auditHtml).toContain('id="btn-admin-export-audit"');
    expect(auditHtml).toContain("Xuất nhật ký CSV");
    expect(auditHtml).toContain('id="admin-audit-meta-row"');
    expect(auditHtml).toContain('class="sort-arrow"');

    // Header sản phẩm trên desktop hiển thị đầy đủ [Avatar] [Tên người dùng] [Chevron], không hardcode .is-compact-account
    useAuthStore.setState({
      user: {
        id: 3,
        email: "hocsinh@axo.edu.vn",
        displayName: "Trần Minh Khoa",
        role: "student",
        mustChangePassword: false,
      },
      resolved: true,
    });
    syncStoreForSSR();
    const desktopHeaderHtml = renderToString(<TopNavAccount initialOpen={false} />);
    expect(desktopHeaderHtml).not.toContain("is-compact-account");
    expect(desktopHeaderHtml).toContain("user-avatar-dot");
    expect(desktopHeaderHtml).toContain("user-name-txt");
    expect(desktopHeaderHtml).toContain("Trần Minh Khoa");
    expect(desktopHeaderHtml).toContain("user-caret-svg");

    // Auth forms sử dụng placeholder trung tính, không dùng tên người giả định
    const loginViewHtml = renderToString(<AuthPageView mode="login" />);
    expect(loginViewHtml).toContain('placeholder="Nhập địa chỉ email"');
    expect(loginViewHtml).toContain('placeholder="Nhập mật khẩu"');
    expect(loginViewHtml).not.toContain("ten@truong.edu.vn");

    const regViewHtml = renderToString(<AuthPageView mode="register" />);
    expect(regViewHtml).toContain('placeholder="Nhập tên của bạn"');
    expect(regViewHtml).toContain('placeholder="Nhập địa chỉ email"');
    expect(regViewHtml).toContain('placeholder="Tạo mật khẩu"');
    expect(regViewHtml).toContain('placeholder="Nhập lại mật khẩu"');
    expect(regViewHtml).not.toContain("Nguyễn Minh Anh");
  });

  it("15. Targeted Parity Correction — Header sản phẩm hiển thị [Avatar] [Tên] [Chevron] trên desktop cho cả 3 vai trò và thu gọn sang [Avatar tròn] khi viewport hẹp hoặc thiếu chỗ", () => {
    const roles: Array<{
      id: number;
      email: string;
      displayName: string;
      role: "student" | "teacher" | "admin";
      expectAdminMenuItem: boolean;
    }> = [
      {
        id: 3,
        email: "hocsinh@axo.edu.vn",
        displayName: "Trần Minh Khoa",
        role: "student",
        expectAdminMenuItem: false,
      },
      {
        id: 2,
        email: "giaovien@axo.edu.vn",
        displayName: "Nguyễn Thị Lan",
        role: "teacher",
        expectAdminMenuItem: false,
      },
      {
        id: 1,
        email: "admin@axo.edu.vn",
        displayName: "Quản trị viên",
        role: "admin",
        expectAdminMenuItem: true,
      },
    ];

    for (const r of roles) {
      useAuthStore.setState({
        user: {
          id: r.id,
          email: r.email,
          displayName: r.displayName,
          role: r.role,
          mustChangePassword: false,
        },
        resolved: true,
      });
      syncStoreForSSR();

      const closedHtml = renderToString(<TopNavAccount initialOpen={false} />);
      expect(closedHtml, `role=${r.role} không được ép cứng is-compact-account`).not.toContain(
        "is-compact-account",
      );
      expect(closedHtml).toContain('id="header-user-avatar"');
      expect(closedHtml).toContain('id="header-user-name"');
      expect(closedHtml).toContain(r.displayName);
      expect(closedHtml).toContain("user-caret-svg");

      const openHtml = renderToString(<TopNavAccount initialOpen={true} />);
      expect(openHtml).toContain('id="account-popover"');
      expect(openHtml).toContain("Hạn mức AI hôm nay");
      expect(openHtml).toContain('id="btn-acc-open-settings"');
      expect(openHtml).toContain('id="btn-acc-open-history"');
      expect(openHtml).toContain('id="btn-acc-logout"');
      if (r.expectAdminMenuItem) {
        expect(openHtml).toContain('id="btn-acc-open-admin"');
        expect(openHtml).toContain("Bảng điều khiển Quản trị");
      } else {
        expect(openHtml).not.toContain('id="btn-acc-open-admin"');
      }
    }

    // Kiểm tra logic quyết định responsive compact dựa trên ngưỡng 720px và va chạm thực tế trên Header
    expect(HEADER_COMPACT_BREAKPOINT_PX).toBe(720);
    for (const wideViewport of [1440, 1366, 1024, 820, 745]) {
      expect(
        shouldUseCompactHeaderAccount({
          viewportWidth: wideViewport,
          navRight: 520,
          navWidth: 265,
          rightClusterLeft: 560,
          rightClusterWidth: 210,
          nameScrollWidth: 112,
          nameClientWidth: 112,
        }),
        `viewport=${wideViewport} đủ không gian phải giữ đầy đủ tên + chevron`,
      ).toBe(false);
    }
    for (const narrowViewport of [720, 656, 600, 390, 360]) {
      expect(
        shouldUseCompactHeaderAccount({
          viewportWidth: narrowViewport,
          navRight: 240,
          navWidth: 140,
          rightClusterLeft: 320,
          rightClusterWidth: 74,
        }),
        `viewport=${narrowViewport} hẹp phải chuyển sang avatar compact`,
      ).toBe(true);
    }
    // Va chạm giữa capsule điều hướng và cụm phải trên màn > 720px vẫn thu gọn an toàn
    expect(
      shouldUseCompactHeaderAccount({
        viewportWidth: 820,
        navRight: 545,
        navWidth: 265,
        rightClusterLeft: 552,
        rightClusterWidth: 250,
      }),
    ).toBe(true);
    // Tên dài bị xén vượt quá max-width cũng tự thu gọn an toàn
    expect(
      shouldUseCompactHeaderAccount({
        viewportWidth: 900,
        navRight: 520,
        navWidth: 265,
        rightClusterLeft: 620,
        rightClusterWidth: 260,
        nameScrollWidth: 215,
        nameClientWidth: 190,
      }),
    ).toBe(true);

    // Kiểm tra CSS đảm bảo kiểu desktop pill 32px + avatar 24px + compact circle + focus-visible
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toMatch(/\.user-profile-btn\s*\{[^}]*height:\s*32px;[^}]*padding:\s*3px 10px 3px 5px;/s);
    expect(css).toMatch(/\.user-avatar-dot\s*\{[^}]*width:\s*24px;[^}]*height:\s*24px;/s);
    expect(css).toMatch(/\.user-profile-btn:focus-visible\s*\{[^}]*outline:\s*2px solid var\(--primary\);/s);
    expect(css).toContain("@media (max-width: 720px)");
  });

  it("16. Reference Restoration — Admin Tổng quan giữ lưới 6 thẻ & Thống kê khôi phục đúng 3 KPI + biểu đồ cột ghép + bảng chi tiết V2.7 dưới biểu đồ", () => {
    useAuthStore.setState({
      user: {
        id: 1,
        email: "admin@axo.edu.vn",
        displayName: "Quản trị viên",
        role: "admin",
        mustChangePassword: false,
      },
      resolved: true,
    });
    syncStoreForSSR();

    // 1. Trạng thái rỗng (0 lượt phân tích): không lặp lại nhiều lần "Chưa có dữ liệu"
    const emptyOverviewHtml = renderToString(<AdminWorkspaceView initialTab="overview" />);
    expect((emptyOverviewHtml.match(/Chưa có dữ liệu/g) ?? []).length).toBe(1);
    expect(emptyOverviewHtml).toContain('id="admin-overview-kpi-grid"');
    expect(emptyOverviewHtml).toContain('id="btn-admin-account-menu"');
    expect(emptyOverviewHtml).toContain("0/0 yêu cầu");
    expect(emptyOverviewHtml).not.toContain("Ngân sách tháng (VND)");

    const emptyAnalyticsHtml = renderToString(<AdminWorkspaceView initialTab="analytics" />);
    // §3.1: Không có thanh Model/Hạn mức, khôi phục đúng 3 KPI với role-chip như HTML V2.7
    expect(emptyAnalyticsHtml).not.toContain('id="admin-analytics-config-strip"');
    expect(emptyAnalyticsHtml).not.toContain("Model cấu hình");
    expect(emptyAnalyticsHtml).not.toContain("Hạn mức vai trò");
    expect(emptyAnalyticsHtml).toContain('id="admin-analytics-kpi-grid"');
    expect((emptyAnalyticsHtml.match(/class="admin-kpi-card"/g) ?? []).length).toBe(3);
    expect(emptyAnalyticsHtml).toContain("Tổng lượt phân tích");
    expect(emptyAnalyticsHtml).toContain("Tỷ lệ thành công");
    expect(emptyAnalyticsHtml).toContain("Thời gian phản hồi TB");
    expect(emptyAnalyticsHtml).not.toContain("Tổng token sử dụng");
    expect(emptyAnalyticsHtml).toContain('class="role-chip student">7 ngày<');
    expect(emptyAnalyticsHtml).toContain('class="role-chip neutral">Chưa có mẫu<');
    expect(emptyAnalyticsHtml).not.toContain("Usage metadata");
    expect(emptyAnalyticsHtml).not.toContain("usage metadata");
    expect(emptyAnalyticsHtml).not.toContain("model configured");
    expect(emptyAnalyticsHtml).not.toContain("response latency");
    expect(emptyAnalyticsHtml).not.toContain("0/0");
    expect(emptyAnalyticsHtml).not.toContain("0%");
    expect(emptyAnalyticsHtml).not.toContain("Dựng hình hợp lệ");
    expect(emptyAnalyticsHtml).not.toContain("#0075DE");
    expect(emptyAnalyticsHtml).not.toContain("#C85A32");
    expect(emptyAnalyticsHtml).not.toContain('id="admin-analytics-table"');
    expect(emptyAnalyticsHtml).toContain('id="admin-analytics-chart-frame"');
    expect(
      (emptyAnalyticsHtml.match(/Chưa có hoạt động phân tích trong 7 ngày qua\./g) ?? []).length,
    ).toBe(1);

    // 2. Trạng thái có dữ liệu telemetry qua test fixture cô lập (không sửa DB trình diễn)
    const populatedAnalyticsHtml = renderToString(
      <AdminWorkspaceView
        initialTab="analytics"
        initialOverviewFixture={{
          configuredModelId: "gemini-2.5-flash",
          aiServiceConfigured: true,
          totalAnalyses: 48,
          analysesToday: 7,
          analyses7d: 42,
          succeededRequests: 43,
          succeeded7d: 38,
          refused7d: 3,
          failed7d: 1,
          avgLatencyMs: 1250,
          avgLatency7dMs: 825,
          tokensMeasured: true,
          inputTokens7d: 39800,
          outputTokens7d: 18900,
          thoughtsTokens7d: 5500,
          totalTokens7d: 64200,
          dailyBreakdown: [
            {
              dateIso: "2026-10-30",
              dateLabel: "30/10/2026",
              totalRequests: 18,
              succeededRequests: 17,
              refusedRequests: 1,
              failedRequests: 0,
              avgLatencyMs: 790,
              tokensMeasured: true,
              inputTokens: 16400,
              outputTokens: 7800,
              thoughtsTokens: 2200,
              totalTokens: 26400,
            },
            {
              dateIso: "2026-10-29",
              dateLabel: "29/10/2026",
              totalRequests: 24,
              succeededRequests: 21,
              refusedRequests: 2,
              failedRequests: 1,
              avgLatencyMs: 851,
              tokensMeasured: true,
              inputTokens: 23400,
              outputTokens: 11100,
              thoughtsTokens: 3300,
              totalTokens: 37800,
            },
          ],
          roleQuotaSummary: {
            student: { count: 1, usedToday: 3, dailyLimitDefault: 15 },
            teacher: { count: 1, usedToday: 4, dailyLimitDefault: 80 },
            admin: { count: 1, usedToday: 0, dailyLimitDefault: 500 },
          },
        }}
      />,
    );
    expect(populatedAnalyticsHtml).not.toContain('id="admin-analytics-config-strip"');
    expect(populatedAnalyticsHtml).not.toContain("gemini-2.5-flash");
    expect((populatedAnalyticsHtml.match(/class="admin-kpi-card"/g) ?? []).length).toBe(3);
    expect(populatedAnalyticsHtml).toContain('class="role-chip teacher">Kiểm chứng tất định<');
    expect(populatedAnalyticsHtml).toContain(">42</div>");
    expect(populatedAnalyticsHtml).toContain(">90,5%</div>");
    expect(populatedAnalyticsHtml).toContain(">825 ms</div>");
    // §3.2 & §4: Loại bỏ hoàn toàn các phụ đề và chú thích thống kê thừa
    expect(populatedAnalyticsHtml).not.toContain("(38/42)");
    expect(populatedAnalyticsHtml).not.toContain("Hôm nay:");
    expect(populatedAnalyticsHtml).not.toContain("Lũy kế:");
    expect(populatedAnalyticsHtml).not.toContain("Toàn kỳ:");
    expect(populatedAnalyticsHtml).not.toContain("Đầu vào:");
    expect(populatedAnalyticsHtml).not.toContain('id="admin-analytics-failed-note"');
    expect(populatedAnalyticsHtml).not.toContain("Chi phí (VND)");
    expect(populatedAnalyticsHtml).toContain(
      "Biểu đồ số lượt phân tích AI &amp; từ chối an toàn theo ngày",
    );
    expect(populatedAnalyticsHtml).toContain('id="admin-analytics-bar-chart"');
    expect(populatedAnalyticsHtml).toContain("Xử lý thành công");
    expect(populatedAnalyticsHtml).toContain("Từ chối an toàn");
    expect(populatedAnalyticsHtml).not.toContain("#0075DE");
    expect(populatedAnalyticsHtml).not.toContain("#C85A32");
    expect(populatedAnalyticsHtml).not.toContain("Dựng hình hợp lệ");
    // Bảng chi tiết V2.7 nằm dưới biểu đồ cột, hiển thị token & tách riêng lỗi xử lý khỏi từ chối
    expect(populatedAnalyticsHtml).toContain('id="admin-analytics-table"');
    expect(populatedAnalyticsHtml.indexOf('id="admin-analytics-bar-chart"')).toBeLessThan(
      populatedAnalyticsHtml.indexOf('id="admin-analytics-table"'),
    );
    expect(populatedAnalyticsHtml).toContain("Token tiêu thụ");
    expect(populatedAnalyticsHtml).toContain("37.800 tokens");
    expect(populatedAnalyticsHtml).toContain("21 thành công · 2 từ chối · 1 lỗi xử lý");
    expect(
      populatedAnalyticsHtml,
    ).toContain("29/10/2026: Tổng 24 yêu cầu, 21 xử lý thành công, 2 từ chối an toàn, 1 lỗi xử lý");
    expect(populatedAnalyticsHtml).not.toContain("Chưa có hoạt động phân tích trong 7 ngày qua.");
  });

  it("17. buildAdminAnalyticsChartModel & formatAdminLatency — trục Y bắt đầu từ 0, sắp xếp 7 ngày tăng dần và không gộp lỗi xử lý vào từ chối an toàn", () => {
    expect(formatAdminLatency(null)).toBeNull();
    expect(formatAdminLatency(825)).toBe("825 ms");
    expect(formatAdminLatency(1250)).toBe("1,25 giây");

    const emptyModel = buildAdminAnalyticsChartModel([], 0);
    expect(emptyModel.hasActivity).toBe(false);
    expect(emptyModel.yTicks[emptyModel.yTicks.length - 1]).toBe(0);

    const activeModel = buildAdminAnalyticsChartModel(
      [
        {
          dateIso: "2026-10-30",
          dateLabel: "30/10/2026",
          totalRequests: 18,
          succeededRequests: 17,
          refusedRequests: 1,
          failedRequests: 0,
          avgLatencyMs: 790,
          tokensMeasured: true,
          inputTokens: 16400,
          outputTokens: 7800,
          thoughtsTokens: 2200,
          totalTokens: 26400,
        },
        {
          dateIso: "2026-10-29",
          dateLabel: "29/10/2026",
          totalRequests: 24,
          succeededRequests: 21,
          refusedRequests: 2,
          failedRequests: 1,
          avgLatencyMs: 851,
          tokensMeasured: true,
          inputTokens: 23400,
          outputTokens: 11100,
          thoughtsTokens: 3300,
          totalTokens: 37800,
        },
      ],
      42,
    );
    expect(activeModel.hasActivity).toBe(true);
    expect(activeModel.days).toHaveLength(7);
    expect(activeModel.days[0].dateIso).toBe("2026-10-24");
    expect(activeModel.days[5].dateIso).toBe("2026-10-29");
    expect(activeModel.days[6].dateIso).toBe("2026-10-30");
    // Trục số bắt đầu từ 0 và maxTick >= 21
    expect(activeModel.yTicks[activeModel.yTicks.length - 1]).toBe(0);
    expect(activeModel.maxTick).toBeGreaterThanOrEqual(21);
    // Không gộp failedRequests (1) vào refusedRequests (2)
    expect(activeModel.days[5].refusedRequests).toBe(2);
    expect(activeModel.days[5].failedRequests).toBe(1);
    expect(activeModel.days[5].totalRequests).toBe(24);
    expect(activeModel.days[5].refusedHeightPct).toBeCloseTo((2 / activeModel.maxTick) * 100, 1);
  });

  it("18. Admin Sidebar Brand Visual Parity — khớp viewBox 0 0 547 547, 24x24, khoảng đệm 12px 10px, typography 15px/10.8px, nút thu gọn 34x34 và không ảnh hưởng Header Public/Workspace", () => {
    useAuthStore.setState({
      user: {
        id: 1,
        email: "admin@axo.edu.vn",
        displayName: "Quản trị viên",
        role: "admin",
        mustChangePassword: false,
      },
      resolved: true,
    });
    syncStoreForSSR();

    const adminHtml = renderToString(<AdminWorkspaceView />);
    const sbBrandMatch = adminHtml.match(
      /<button[^>]*id="btn-admin-sb-brand"[^>]*>([\s\S]*?)<\/button>/,
    );
    expect(sbBrandMatch).not.toBeNull();
    const sbBrandInner = sbBrandMatch![1];

    // SVG trong Sidebar Admin dùng viewBox="0 0 547 547" của HTML V2.7 và không gắn .axo-logo-svg của Header
    expect(sbBrandInner).toContain('viewBox="0 0 547 547"');
    expect(sbBrandInner).toContain('role="img"');
    expect(sbBrandInner).toContain('aria-label="Axo logo"');
    expect(sbBrandInner).not.toContain("axo-logo-svg");
    expect(sbBrandInner).toContain('<span class="admin-sb-brand-title">Axo</span>');
    expect(sbBrandInner).toContain('<span class="admin-sb-brand-sub">Quản trị</span>');
    expect(sbBrandInner).toContain('id="admin-sb-brand-tooltip"');
    expect(sbBrandInner).toContain("Mở rộng thanh bên");

    // Nút thu gọn Sidebar có aria-expanded="true" khi đang mở rộng
    expect(adminHtml).toMatch(/id="btn-admin-sidebar-collapse"[^>]*aria-expanded="true"/);

    // Header Public giữ nguyên .axo-logo-svg viewBox="16 56 516 434"
    const appHtml = renderToString(<TopNav />);
    expect(appHtml).toContain('class="axo-logo-svg"');
    expect(appHtml).toContain('viewBox="16 56 516 434"');

    // Kiểm tra hợp đồng CSS gốc của Admin Sidebar Brand theo HTML V2.7
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).not.toContain(".admin-sidebar .axo-logo-svg");
    expect(css).toMatch(/\.admin-sidebar\s*\{[^}]*width:\s*236px;[^}]*padding:\s*12px 10px;/s);
    expect(css).toMatch(
      /\.admin-sb-brand\s*\{[^}]*display:\s*inline-flex;[^}]*gap:\s*9px;[^}]*padding:\s*4px 6px;/s,
    );
    expect(css).toMatch(/\.sb-logo-default\s*\{[^}]*width:\s*24px;[^}]*height:\s*24px;/s);
    expect(css).toMatch(/\.sb-logo-default svg\s*\{[^}]*width:\s*24px;[^}]*height:\s*24px;/s);
    expect(css).toMatch(/\.admin-sb-brand-text\s*\{[^}]*line-height:\s*1\.15;/s);
    expect(css).toMatch(
      /\.admin-sb-brand-title\s*\{[^}]*font-size:\s*15px;[^}]*font-weight:\s*700;/s,
    );
    expect(css).toMatch(
      /\.admin-sb-brand-sub\s*\{[^}]*font-size:\s*10\.8px;[^}]*font-weight:\s*500;/s,
    );
    expect(css).toMatch(/\.btn-sb-collapse\s*\{[^}]*width:\s*34px;[^}]*height:\s*34px;/s);
    expect(css).toMatch(/\.btn-sb-collapse svg\s*\{[^}]*width:\s*18px;[^}]*height:\s*18px;/s);
  });
});
