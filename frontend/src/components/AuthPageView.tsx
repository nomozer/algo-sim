import { useEffect, useState } from "react";
import { useAuthStore } from "../state/auth";
import { useAppStore } from "../state/store";
import { useToastStore } from "./TopNav";
import { IconAxoLogo } from "./icons";
import {
  applyIntendedDestination,
  clearIntendedDestination,
  consumeIntendedDestination,
  restoreSavedDraftIfEmpty,
} from "./landing/landing-geometry-data";
import { AuthInfoIcon, AuthInlineAlertIcon, PwToggleButton } from "./auth-shared";

/* ── AuthPageView (Standalone Views 5–9: #view-login, #view-register, #view-forgot, #view-reset, #view-verify) ── */

/** Câu trả lời trung tính của "Quên mật khẩu" — trùng câu máy chủ trả, không tiết lộ email có tồn tại hay không. */
const RECOVERY_NEUTRAL_MESSAGE =
  "Nếu địa chỉ email đủ điều kiện khôi phục tài khoản, bạn sẽ nhận được hướng dẫn đặt lại mật khẩu.";

/** Liên kết trong thư mang token ở query: đọc MỘT lần khi mở trang (trước khi gỡ khỏi thanh địa chỉ). */
function readQueryToken(name: string): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get(name)?.trim() || "";
}

export function AuthPageView({
  mode,
  initialEmailRecoveryAvailable = null,
}: {
  mode: "login" | "register" | "forgot" | "reset" | "verify";
  initialEmailRecoveryAvailable?: boolean | null;
}) {
  const goHome = useAppStore((s) => s.goHome);
  const setView = useAppStore((s) => s.setView);
  const authResetEmail = useAppStore((s) => s.authResetEmail);
  const setAuthResetEmail = useAppStore((s) => s.setAuthResetEmail);

  const user = useAuthStore((s) => s.user);
  const authResolved = useAuthStore((s) => s.resolved);
  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);
  const requestPasswordReset = useAuthStore((s) => s.requestPasswordReset);
  const fetchRecoveryStatus = useAuthStore((s) => s.fetchRecoveryStatus);
  const resetPassword = useAuthStore((s) => s.resetPassword);
  const verifyEmail = useAuthStore((s) => s.verifyEmail);
  const resendVerification = useAuthStore((s) => s.resendVerification);
  const clearError = useAuthStore((s) => s.clearError);
  const busy = useAuthStore((s) => s.busy);
  const authError = useAuthStore((s) => s.error);

  const [emailRecoveryAvailable, setEmailRecoveryAvailable] = useState<boolean | null>(
    initialEmailRecoveryAvailable,
  );

  useEffect(() => {
    useToastStore.getState().clearToasts();
  }, []);

  useEffect(() => {
    if (mode !== "forgot") return;
    let cancelled = false;
    void fetchRecoveryStatus().then((st) => {
      if (!cancelled) {
        setEmailRecoveryAvailable(st.emailRecoveryAvailable);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [mode, fetchRecoveryStatus]);

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPw, setLoginPw] = useState("");
  const [showLoginPw, setShowLoginPw] = useState(false);
  const [loginErrors, setLoginErrors] = useState<{ email?: string; pw?: string }>({});
  const [loginBanner, setLoginBanner] = useState<{ tone: "warn" | "neutral" | ""; text: string }>({
    tone: "",
    text: "",
  });

  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPw, setRegPw] = useState("");
  const [regPwConfirm, setRegPwConfirm] = useState("");
  const [showRegPw, setShowRegPw] = useState(false);
  const [showRegPwConfirm, setShowRegPwConfirm] = useState(false);
  const [regErrors, setRegErrors] = useState<{
    name?: string;
    email?: string;
    pw?: string;
    pwConfirm?: string;
  }>({});
  const [regBanner, setRegBanner] = useState<{ tone: "warn" | "neutral" | ""; text: string }>({
    tone: "",
    text: "",
  });

  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotEmailErr, setForgotEmailErr] = useState("");
  const [forgotSent, setForgotSent] = useState(false);
  const [forgotBanner, setForgotBanner] = useState<{ tone: "warn" | "neutral" | ""; text: string }>({
    tone: "neutral",
    text: "",
  });

  const [resetToken, setResetToken] = useState(() => readQueryToken("reset_token"));
  const [verifyToken] = useState(() => (mode === "verify" ? readQueryToken("token") : ""));
  const [verifyState, setVerifyState] = useState<"idle" | "done" | "failed">("idle");
  const [verifyMessage, setVerifyMessage] = useState("");
  const [resendNote, setResendNote] = useState<{ tone: "warn" | "neutral"; text: string } | null>(null);

  // Token trong liên kết thư: gỡ khỏi thanh địa chỉ và lịch sử ngay sau khi đọc, và không gửi Referer từ trang này.
  useEffect(() => {
    if (mode !== "reset" && mode !== "verify") return;
    if (typeof document === "undefined") return;
    const meta = document.createElement("meta");
    meta.name = "referrer";
    meta.content = "no-referrer";
    document.head.appendChild(meta);
    try {
      const params = new URLSearchParams(window.location.search);
      const key = mode === "reset" ? "reset_token" : "token";
      if (params.has(key) || (mode === "reset" && window.location.hash === "#reset")) {
        window.history.replaceState(
          window.history.state,
          "",
          mode === "reset" ? "/reset" : "/verify-email",
        );
      }
    } catch {
      /* môi trường chặn history API — token vẫn chỉ nằm trong bộ nhớ trang */
    }
    return () => {
      meta.remove();
    };
  }, [mode]);
  const [resetPw, setResetPw] = useState("");
  const [resetPwConfirm, setResetPwConfirm] = useState("");
  const [showResetPw, setShowResetPw] = useState(false);
  const [showResetPwConfirm, setShowResetPwConfirm] = useState(false);
  const [resetErrors, setResetErrors] = useState<{
    token?: string;
    pw?: string;
    pwConfirm?: string;
  }>({});
  const [resetDone, setResetDone] = useState(false);
  const [resetBanner, setResetBanner] = useState<{ tone: "warn" | "neutral" | ""; text: string }>({
    tone: "",
    text: "",
  });

  useEffect(() => {
    clearError();
    setLoginErrors({});
    setLoginBanner({ tone: "", text: "" });
    setLoginPw("");
    setShowLoginPw(false);
    setRegErrors({});
    setRegBanner({ tone: "", text: "" });
    setRegPw("");
    setRegPwConfirm("");
    setShowRegPw(false);
    setShowRegPwConfirm(false);
    setForgotEmailErr("");
    setForgotBanner({ tone: "neutral", text: "" });
    setForgotSent(false);
    setResetErrors({});
    setResetBanner({ tone: "", text: "" });
    setResetPw("");
    setResetPwConfirm("");
    setShowResetPw(false);
    setShowResetPwConfirm(false);
  }, [mode, clearError]);

  const hasSessionHint =
    typeof window !== "undefined" &&
    (() => {
      try {
        return window.sessionStorage.getItem("axo_auth_session_hint") === "1";
      } catch {
        return false;
      }
    })();

  const isPlausibleEmail = (raw: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(raw.trim());
  const isPlausibleUsername = (raw: string) => /^[a-zA-Z0-9][a-zA-Z0-9._-]{1,63}$/.test(raw.trim());
  const validateLoginIdentifier = (raw: string): string | undefined => {
    const trimmed = raw.trim();
    if (!trimmed) return "Vui lòng nhập email hoặc tên đăng nhập.";
    if (trimmed.includes("@")) {
      return isPlausibleEmail(trimmed) ? undefined : "Địa chỉ email chưa đúng định dạng.";
    }
    return isPlausibleUsername(trimmed)
      ? undefined
      : "Tên đăng nhập chỉ gồm chữ, số và ký tự . _ -.";
  };
  const focusById = (id: string) => {
    if (typeof document !== "undefined") {
      (document.getElementById(id) as HTMLElement | null)?.focus();
    }
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    const em = loginEmail.trim();
    const errs: { email?: string; pw?: string } = {};
    const idErr = validateLoginIdentifier(em);
    if (idErr) {
      errs.email = idErr;
    }
    if (!loginPw) {
      errs.pw = "Vui lòng nhập mật khẩu.";
    }
    if (errs.email || errs.pw) {
      setLoginErrors(errs);
      setLoginBanner({ tone: "", text: "" });
      clearError();
      focusById(errs.email ? "login-email-input" : "login-pw-input");
      return;
    }
    setLoginErrors({});
    setLoginBanner({ tone: "", text: "" });
    await login(em, loginPw);
    const currentUser = useAuthStore.getState().user;
    const currentErr = useAuthStore.getState().error;
    if (currentUser) {
      setLoginPw("");
      setShowLoginPw(false);
      if (currentUser.mustChangePassword) {
        setView("reset");
        return;
      }
      const pending = consumeIntendedDestination();
      if (pending) {
        applyIntendedDestination(pending, currentUser);
      } else {
        const curView = useAppStore.getState().view;
        if (curView === "login" || curView === "register") {
          if (currentUser.role === "admin") {
            setView("admin");
          } else {
            useAppStore.getState().setGuestEnteredApp(true);
            goHome();
            restoreSavedDraftIfEmpty();
          }
        }
      }
    } else if (currentErr) {
      setLoginBanner({ tone: "warn", text: currentErr });
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    const nm = regName.trim();
    const em = regEmail.trim();
    const errs: { name?: string; email?: string; pw?: string; pwConfirm?: string } = {};
    if (!nm) {
      errs.name = "Vui lòng nhập tên hiển thị.";
    }
    if (!em) {
      errs.email = "Vui lòng nhập địa chỉ email.";
    } else if (!isPlausibleEmail(em)) {
      errs.email = "Địa chỉ email chưa đúng định dạng.";
    }
    if (!regPw) {
      errs.pw = "Vui lòng tạo mật khẩu.";
    } else if (regPw.length < 8) {
      errs.pw = "Mật khẩu cần có tối thiểu 8 ký tự.";
    }
    if (!regPwConfirm) {
      errs.pwConfirm = "Vui lòng nhập lại mật khẩu.";
    } else if (regPw !== regPwConfirm) {
      errs.pwConfirm = "Mật khẩu xác nhận không khớp.";
    }
    if (errs.name || errs.email || errs.pw || errs.pwConfirm) {
      setRegErrors(errs);
      setRegBanner({ tone: "", text: "" });
      clearError();
      if (errs.name) focusById("reg-name-input");
      else if (errs.email) focusById("reg-email-input");
      else if (errs.pw) focusById("reg-pw-input");
      else focusById("reg-pw-confirm-input");
      return;
    }
    setRegErrors({});
    setRegBanner({ tone: "", text: "" });
    const ok = await register({
      email: em,
      displayName: nm,
      password: regPw,
      role: "student",
    });
    const currentUser = useAuthStore.getState().user;
    const currentErr = useAuthStore.getState().error;
    if (ok && currentUser) {
      setRegPw("");
      setRegPwConfirm("");
      setShowRegPw(false);
      setShowRegPwConfirm(false);
      if (useAuthStore.getState().lastVerificationStatus === "queued") {
        useToastStore.getState().showToast({
          tone: "success",
          title: "Đã gửi email xác minh",
          description: `Mở thư gửi tới ${em} và bấm liên kết để xác minh địa chỉ email.`,
          durationMs: 8000,
        });
      }
      if (currentUser.mustChangePassword) {
        setView("reset");
        return;
      }
      const pending = consumeIntendedDestination();
      if (pending) {
        applyIntendedDestination(pending, currentUser);
      } else {
        const curView = useAppStore.getState().view;
        if (curView === "login" || curView === "register") {
          useAppStore.getState().setGuestEnteredApp(true);
          goHome();
          restoreSavedDraftIfEmpty();
        }
      }
    } else if (ok && !currentUser) {
      setRegPw("");
      setRegPwConfirm("");
      setRegBanner({
        tone: "neutral",
        text: "Tài khoản đã được tạo. Vui lòng đăng nhập để tiếp tục.",
      });
    } else if (currentErr) {
      setRegBanner({ tone: "warn", text: currentErr });
    }
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (emailRecoveryAvailable !== true || busy) {
      return;
    }
    const em = forgotEmail.trim();
    if (!em) {
      setForgotEmailErr("Vui lòng nhập địa chỉ email.");
      focusById("forgot-email-input");
      return;
    }
    if (!isPlausibleEmail(em)) {
      setForgotEmailErr("Địa chỉ email chưa đúng định dạng.");
      focusById("forgot-email-input");
      return;
    }
    setForgotEmailErr("");
    const res = await requestPasswordReset(em);
    if (res.ok) {
      setAuthResetEmail(em);
      const smtpReady = Boolean(res.smtpConfigured);
      setForgotSent(smtpReady);
      if (smtpReady) {
        setForgotBanner({
          tone: "neutral",
          text: res.message || RECOVERY_NEUTRAL_MESSAGE,
        });
      } else {
        setEmailRecoveryAvailable(false);
        setForgotBanner({ tone: "neutral", text: "" });
      }
    } else {
      setForgotBanner({
        tone: "warn",
        text: res.error || res.message || "Không gửi được yêu cầu đặt lại mật khẩu.",
      });
    }
  };

  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    const cleanToken = resetToken.trim();
    const errs: { token?: string; pw?: string; pwConfirm?: string } = {};
    if (!user?.mustChangePassword && !cleanToken) {
      errs.token = "Vui lòng nhập mã khôi phục hợp lệ.";
    }
    if (!resetPw) {
      errs.pw = "Vui lòng nhập mật khẩu mới.";
    } else if (resetPw.length < 8) {
      errs.pw = "Mật khẩu mới cần có tối thiểu 8 ký tự.";
    }
    if (!resetPwConfirm) {
      errs.pwConfirm = "Vui lòng nhập lại mật khẩu.";
    } else if (resetPw !== resetPwConfirm) {
      errs.pwConfirm = "Mật khẩu xác nhận không khớp.";
    }
    if (errs.token || errs.pw || errs.pwConfirm) {
      setResetErrors(errs);
      setResetBanner({ tone: "", text: "" });
      if (errs.token) focusById("reset-token-input");
      else if (errs.pw) focusById("reset-pw-input");
      else focusById("reset-pw-confirm-input");
      return;
    }
    setResetErrors({});
    const res = await resetPassword(cleanToken, resetPw, authResetEmail || undefined);
    if (res.ok) {
      setResetDone(true);
      setResetToken("");
      setResetPw("");
      setResetPwConfirm("");
      setResetBanner({
        tone: "",
        text: "Mật khẩu của bạn đã được đặt lại thành công. Bạn có thể đăng nhập bằng mật khẩu mới.",
      });
    } else {
      setResetBanner({
        tone: "warn",
        text: res.error ?? "Không đặt lại được mật khẩu.",
      });
    }
  };

  const handleAuthBrandExit = () => {
    clearError();
    if (!useAuthStore.getState().user) {
      clearIntendedDestination();
      useAppStore.getState().setGuestEnteredApp(false);
      useAppStore.getState().openLanding();
      return;
    }
    goHome();
  };

  const renderTopBar = () => (
    <div className="auth-top-bar">
      <button
        type="button"
        className="auth-brand-link"
        data-auth-home="1"
        aria-label="Về Trang chủ"
        title="Về Trang chủ"
        onClick={handleAuthBrandExit}
      >
        <IconAxoLogo size={26} />
        <span>Axo</span>
      </button>
    </div>
  );

  if ((mode === "login" || mode === "register") && !authResolved && hasSessionHint) {
    return (
      <section
        className="axo-page-view active"
        id={mode === "login" ? "view-login" : "view-register"}
        aria-label="Đang kiểm tra phiên đăng nhập"
      >
        <div className="auth-standalone-shell">
          {renderTopBar()}
          <div className="auth-center-stage">
            <div className="auth-card">
              <div className="auth-checking-state" id="auth-session-checking" role="status">
                <span className="auth-checking-spinner" aria-hidden="true" />
                <span>Đang kiểm tra phiên đăng nhập...</span>
              </div>
            </div>
          </div>
          <div className="auth-bottom-spacer" />
        </div>
      </section>
    );
  }

  if (mode === "login") {
    const bannerMsg = loginBanner.text || authError || "";
    const bannerTone = loginBanner.tone || (authError ? "warn" : "");
    return (
      <section className="axo-page-view active" id="view-login" aria-label="Đăng nhập Axo">
        <div className="auth-standalone-shell">
          {renderTopBar()}
          <div className="auth-center-stage">
            <div className="auth-card">
              <div className="auth-head">
                <h1 className="auth-title">Đăng nhập</h1>
                <p className="auth-subtitle">Nhập email hoặc tên đăng nhập và mật khẩu để tiếp tục trên Axo.</p>
              </div>

              <div
                className={`auth-feedback-banner${bannerTone ? ` ${bannerTone}` : ""}${bannerMsg ? " visible" : ""}`}
                id="login-feedback-banner"
                role={bannerTone === "warn" ? "alert" : "status"}
              >
                {bannerMsg && bannerTone === "warn" && <AuthInlineAlertIcon />}
                <span>{bannerMsg}</span>
              </div>

              <form className="auth-form" id="form-login" noValidate onSubmit={(e) => void handleLoginSubmit(e)}>
                <div className="auth-field">
                  <label className="auth-label" htmlFor="login-email-input">
                    Email hoặc tên đăng nhập
                  </label>
                  <input
                    type="text"
                    inputMode="email"
                    id="login-email-input"
                    className={`auth-input${loginErrors.email ? " is-invalid" : ""}`}
                    placeholder="Nhập email hoặc tên đăng nhập"
                    value={loginEmail}
                    onChange={(e) => {
                      setLoginEmail(e.target.value);
                      if (loginErrors.email) setLoginErrors((p) => ({ ...p, email: undefined }));
                      if (loginBanner.text) setLoginBanner({ tone: "", text: "" });
                      if (authError) clearError();
                    }}
                    onBlur={() => {
                      const em = loginEmail.trim();
                      if (em.length > 0) {
                        const err = validateLoginIdentifier(em);
                        if (err) {
                          setLoginErrors((p) => ({ ...p, email: err }));
                        }
                      }
                    }}
                    aria-invalid={Boolean(loginErrors.email)}
                    aria-describedby={loginErrors.email ? "err-login-email" : undefined}
                    autoComplete="username"
                    autoCapitalize="none"
                    spellCheck={false}
                  />
                  <div
                    className={`field-inline-error${loginErrors.email ? " visible" : ""}`}
                    id="err-login-email"
                    role="alert"
                  >
                    {loginErrors.email && <AuthInlineAlertIcon />}
                    <span>{loginErrors.email}</span>
                  </div>
                </div>

                <div className="auth-field">
                  <div className="auth-label-row">
                    <label className="auth-label" htmlFor="login-pw-input">
                      Mật khẩu
                    </label>
                    <button
                      type="button"
                      className="btn-text-link"
                      id="btn-login-to-forgot"
                      onClick={() => setView("forgot")}
                    >
                      Quên mật khẩu?
                    </button>
                  </div>
                  <div className="auth-input-wrap">
                    <input
                      type={showLoginPw ? "text" : "password"}
                      id="login-pw-input"
                      className={`auth-input has-toggle${loginErrors.pw ? " is-invalid" : ""}`}
                      placeholder="Nhập mật khẩu"
                      value={loginPw}
                      onChange={(e) => {
                        setLoginPw(e.target.value);
                        if (loginErrors.pw) setLoginErrors((p) => ({ ...p, pw: undefined }));
                        if (loginBanner.text) setLoginBanner({ tone: "", text: "" });
                        if (authError) clearError();
                      }}
                      aria-invalid={Boolean(loginErrors.pw)}
                      aria-describedby={loginErrors.pw ? "err-login-pw" : undefined}
                      autoComplete="current-password"
                    />
                    <PwToggleButton
                      id="btn-toggle-login-pw"
                      targetId="login-pw-input"
                      shown={showLoginPw}
                      onToggle={() => setShowLoginPw((v) => !v)}
                    />
                  </div>
                  <div
                    className={`field-inline-error${loginErrors.pw ? " visible" : ""}`}
                    id="err-login-pw"
                    role="alert"
                  >
                    {loginErrors.pw && <AuthInlineAlertIcon />}
                    <span>{loginErrors.pw}</span>
                  </div>
                </div>

                <button
                  type="submit"
                  className={`btn-auth-submit${busy ? " is-loading" : ""}`}
                  id="btn-login-submit"
                  disabled={busy}
                  aria-busy={busy}
                >
                  {busy && <span className="auth-btn-spinner" aria-hidden="true" />}
                  <span>{busy ? "Đang đăng nhập..." : "Đăng nhập"}</span>
                </button>
              </form>

              <div className="auth-footer-Switch">
                <span>Chưa có tài khoản?</span>
                <button
                  type="button"
                  className="btn-text-link"
                  id="btn-login-to-register"
                  onClick={() => setView("register")}
                >
                  Đăng ký
                </button>
              </div>
            </div>
          </div>
          <div className="auth-bottom-spacer" />
        </div>
      </section>
    );
  }

  if (mode === "register") {
    const bannerMsg = regBanner.text || authError || "";
    const bannerTone = regBanner.tone || (authError ? "warn" : "");
    return (
      <section className="axo-page-view active" id="view-register" aria-label="Tạo tài khoản Axo">
        <div className="auth-standalone-shell">
          {renderTopBar()}
          <div className="auth-center-stage">
            <div className="auth-card">
              <div className="auth-head">
                <h1 className="auth-title">Tạo tài khoản</h1>
                <p className="auth-subtitle">
                  Tạo tài khoản cá nhân để lưu lịch sử dựng hình và sử dụng đầy đủ tính năng của Axo.
                </p>
              </div>

              <div
                className={`auth-feedback-banner${bannerTone ? ` ${bannerTone}` : ""}${bannerMsg ? " visible" : ""}`}
                id="register-feedback-banner"
                role={bannerTone === "warn" ? "alert" : "status"}
              >
                {bannerMsg && bannerTone === "warn" && <AuthInlineAlertIcon />}
                <span>{bannerMsg}</span>
              </div>

              <form className="auth-form" id="form-register" noValidate onSubmit={(e) => void handleRegisterSubmit(e)}>
                <div className="auth-field">
                  <label className="auth-label" htmlFor="reg-name-input">
                    Tên hiển thị
                  </label>
                  <input
                    type="text"
                    id="reg-name-input"
                    className={`auth-input${regErrors.name ? " is-invalid" : ""}`}
                    placeholder="Nhập tên của bạn"
                    value={regName}
                    onChange={(e) => {
                      setRegName(e.target.value);
                      if (regErrors.name) setRegErrors((p) => ({ ...p, name: undefined }));
                      if (regBanner.text) setRegBanner({ tone: "", text: "" });
                      if (authError) clearError();
                    }}
                    aria-invalid={Boolean(regErrors.name)}
                    aria-describedby={regErrors.name ? "err-reg-name" : undefined}
                    autoComplete="name"
                  />
                  <div
                    className={`field-inline-error${regErrors.name ? " visible" : ""}`}
                    id="err-reg-name"
                    role="alert"
                  >
                    {regErrors.name && <AuthInlineAlertIcon />}
                    <span>{regErrors.name}</span>
                  </div>
                </div>

                <div className="auth-field">
                  <label className="auth-label" htmlFor="reg-email-input">
                    Email
                  </label>
                  <input
                    type="email"
                    id="reg-email-input"
                    className={`auth-input${regErrors.email ? " is-invalid" : ""}`}
                    placeholder="Nhập địa chỉ email"
                    value={regEmail}
                    onChange={(e) => {
                      setRegEmail(e.target.value);
                      if (regErrors.email) setRegErrors((p) => ({ ...p, email: undefined }));
                      if (regBanner.text) setRegBanner({ tone: "", text: "" });
                      if (authError) clearError();
                    }}
                    onBlur={() => {
                      const em = regEmail.trim();
                      if (em.length > 0 && !isPlausibleEmail(em)) {
                        setRegErrors((p) => ({ ...p, email: "Địa chỉ email chưa đúng định dạng." }));
                      }
                    }}
                    aria-invalid={Boolean(regErrors.email)}
                    aria-describedby={regErrors.email ? "err-reg-email" : undefined}
                    autoComplete="email"
                  />
                  <div
                    className={`field-inline-error${regErrors.email ? " visible" : ""}`}
                    id="err-reg-email"
                    role="alert"
                  >
                    {regErrors.email && <AuthInlineAlertIcon />}
                    <span>{regErrors.email}</span>
                  </div>
                </div>

                <div className="auth-field">
                  <div className="auth-label-row">
                    <label className="auth-label" htmlFor="reg-pw-input">
                      Mật khẩu
                    </label>
                    <span className="auth-field-meta-hint" id="hint-reg-pw">
                      Tối thiểu 8 ký tự
                    </span>
                  </div>
                  <div className="auth-input-wrap">
                    <input
                      type={showRegPw ? "text" : "password"}
                      id="reg-pw-input"
                      className={`auth-input has-toggle${regErrors.pw ? " is-invalid" : ""}`}
                      placeholder="Tạo mật khẩu"
                      value={regPw}
                      onChange={(e) => {
                        setRegPw(e.target.value);
                        if (regErrors.pw) setRegErrors((p) => ({ ...p, pw: undefined }));
                        if (regBanner.text) setRegBanner({ tone: "", text: "" });
                        if (authError) clearError();
                      }}
                      onBlur={() => {
                        if (regPw.length > 0 && regPw.length < 8) {
                          setRegErrors((p) => ({ ...p, pw: "Mật khẩu cần có tối thiểu 8 ký tự." }));
                        }
                      }}
                      aria-invalid={Boolean(regErrors.pw)}
                      aria-describedby={regErrors.pw ? "hint-reg-pw err-reg-pw" : "hint-reg-pw"}
                      autoComplete="new-password"
                    />
                    <PwToggleButton
                      id="btn-toggle-reg-pw"
                      targetId="reg-pw-input"
                      shown={showRegPw}
                      onToggle={() => setShowRegPw((v) => !v)}
                    />
                  </div>
                  <div
                    className={`field-inline-error${regErrors.pw ? " visible" : ""}`}
                    id="err-reg-pw"
                    role="alert"
                  >
                    {regErrors.pw && <AuthInlineAlertIcon />}
                    <span>{regErrors.pw}</span>
                  </div>
                </div>

                <div className="auth-field">
                  <label className="auth-label" htmlFor="reg-pw-confirm-input">
                    Xác nhận mật khẩu
                  </label>
                  <div className="auth-input-wrap">
                    <input
                      type={showRegPwConfirm ? "text" : "password"}
                      id="reg-pw-confirm-input"
                      className={`auth-input has-toggle${regErrors.pwConfirm ? " is-invalid" : ""}`}
                      placeholder="Nhập lại mật khẩu"
                      value={regPwConfirm}
                      onChange={(e) => {
                        setRegPwConfirm(e.target.value);
                        if (regErrors.pwConfirm)
                          setRegErrors((p) => ({ ...p, pwConfirm: undefined }));
                        if (regBanner.text) setRegBanner({ tone: "", text: "" });
                        if (authError) clearError();
                      }}
                      onBlur={() => {
                        if (regPwConfirm.length > 0 && regPw !== regPwConfirm) {
                          setRegErrors((p) => ({ ...p, pwConfirm: "Mật khẩu xác nhận không khớp." }));
                        }
                      }}
                      aria-invalid={Boolean(regErrors.pwConfirm)}
                      aria-describedby={regErrors.pwConfirm ? "err-reg-pw-confirm" : undefined}
                      autoComplete="new-password"
                    />
                    <PwToggleButton
                      id="btn-toggle-reg-pw-confirm"
                      targetId="reg-pw-confirm-input"
                      shown={showRegPwConfirm}
                      onToggle={() => setShowRegPwConfirm((v) => !v)}
                    />
                  </div>
                  <div
                    className={`field-inline-error${regErrors.pwConfirm ? " visible" : ""}`}
                    id="err-reg-pw-confirm"
                    role="alert"
                  >
                    {regErrors.pwConfirm && <AuthInlineAlertIcon />}
                    <span>{regErrors.pwConfirm}</span>
                  </div>
                </div>

                <button
                  type="submit"
                  className={`btn-auth-submit${busy ? " is-loading" : ""}`}
                  id="btn-register-submit"
                  disabled={busy}
                  aria-busy={busy}
                >
                  {busy && <span className="auth-btn-spinner" aria-hidden="true" />}
                  <span>{busy ? "Đang tạo tài khoản..." : "Tạo tài khoản"}</span>
                </button>
              </form>

              <div className="auth-footer-Switch">
                <span>Đã có tài khoản?</span>
                <button
                  type="button"
                  className="btn-text-link"
                  id="btn-reg-to-login"
                  onClick={() => setView("login")}
                >
                  Đăng nhập
                </button>
              </div>
            </div>
          </div>
          <div className="auth-bottom-spacer" />
        </div>
      </section>
    );
  }

  if (mode === "verify") {
    const handleVerify = async () => {
      if (busy || !verifyToken) return;
      const res = await verifyEmail(verifyToken);
      if (res.ok) {
        setVerifyState("done");
        setVerifyMessage("");
      } else {
        setVerifyState("failed");
        setVerifyMessage(res.error ?? "Không xác minh được địa chỉ email.");
      }
    };
    const handleResend = async () => {
      const res = await resendVerification();
      if (res.status === "queued") {
        setResendNote({ tone: "neutral", text: "Đã gửi lại email xác minh. Vui lòng kiểm tra hộp thư." });
      } else if (res.status === "already_verified") {
        setVerifyState("done");
        setResendNote(null);
      } else if (res.status === "unavailable") {
        setResendNote({ tone: "warn", text: "Hệ thống hiện chưa gửi được email. Vui lòng thử lại sau." });
      } else {
        setResendNote({ tone: "warn", text: res.error ?? "Không gửi lại được email xác minh." });
      }
    };
    const continueAfterVerify = () => {
      const current = useAuthStore.getState().user;
      if (!current) {
        setView("login");
      } else if (current.role === "admin") {
        setView("admin");
      } else {
        useAppStore.getState().setGuestEnteredApp(true);
        goHome();
      }
    };
    const missingToken = !verifyToken && verifyState === "idle";
    const canResend = Boolean(user && user.role !== "admin" && !user.emailVerified);
    return (
      <section className="axo-page-view active" id="view-verify" aria-label="Xác minh email Axo">
        <div className="auth-standalone-shell">
          {renderTopBar()}
          <div className="auth-center-stage">
            <div className="auth-card">
              <div className="auth-head">
                <h1 className="auth-title">Xác minh email</h1>
                <p className="auth-subtitle">
                  {verifyState === "done"
                    ? "Địa chỉ email của bạn đã được xác minh."
                    : "Xác nhận rằng bạn sở hữu địa chỉ email của tài khoản Axo."}
                </p>
              </div>

              {verifyState === "done" && (
                <>
                  <div className="auth-feedback-banner neutral visible" id="verify-success-banner" role="status">
                    <span>Xác minh thành công. Bạn có thể dùng email này để khôi phục mật khẩu khi cần.</span>
                  </div>
                  <button type="button" className="btn-auth-submit" id="btn-verify-continue" onClick={continueAfterVerify}>
                    <span>{user ? "Tiếp tục vào Axo" : "Đăng nhập"}</span>
                  </button>
                </>
              )}

              {(verifyState === "failed" || missingToken) && (
                <>
                  <div className="auth-feedback-banner warn visible" id="verify-error-banner" role="alert">
                    <AuthInlineAlertIcon />
                    <span>
                      {missingToken
                        ? "Liên kết xác minh không đầy đủ. Vui lòng mở lại liên kết trong email."
                        : verifyMessage}
                    </span>
                  </div>
                  {resendNote && (
                    <div
                      className={`auth-feedback-banner ${resendNote.tone} visible`}
                      id="verify-resend-note"
                      role={resendNote.tone === "warn" ? "alert" : "status"}
                    >
                      <span>{resendNote.text}</span>
                    </div>
                  )}
                  {canResend ? (
                    <button type="button" className="btn-auth-submit" id="btn-verify-resend" onClick={() => void handleResend()}>
                      <span>Gửi lại email xác minh</span>
                    </button>
                  ) : (
                    <button type="button" className="btn-auth-submit" id="btn-verify-continue" onClick={continueAfterVerify}>
                      <span>{user ? "Tiếp tục vào Axo" : "Đăng nhập"}</span>
                    </button>
                  )}
                </>
              )}

              {verifyState === "idle" && !missingToken && (
                <button
                  type="button"
                  className={`btn-auth-submit${busy ? " is-loading" : ""}`}
                  id="btn-verify-submit"
                  disabled={busy}
                  aria-busy={busy}
                  onClick={() => void handleVerify()}
                >
                  {busy && <span className="auth-btn-spinner" aria-hidden="true" />}
                  <span>{busy ? "Đang xác minh..." : "Xác minh email"}</span>
                </button>
              )}
            </div>
          </div>
          <div className="auth-bottom-spacer" />
        </div>
      </section>
    );
  }

  if (mode === "forgot") {
    const recoveryChecking = emailRecoveryAvailable === null;
    const recoveryDisabled = emailRecoveryAvailable === false;
    return (
      <section className="axo-page-view active" id="view-forgot" aria-label="Quên mật khẩu Axo">
        <div className="auth-standalone-shell">
          {renderTopBar()}
          <div className="auth-center-stage">
            <div className="auth-card">
              <div className="auth-head">
                <h1 className="auth-title">Quên mật khẩu?</h1>
                <p className="auth-subtitle">
                  {recoveryChecking
                    ? "Đang kiểm tra trạng thái khôi phục mật khẩu của hệ thống."
                    : recoveryDisabled
                      ? "Khôi phục mật khẩu qua email hiện chưa khả dụng trên hệ thống này."
                      : "Nhập địa chỉ email của bạn để nhận hướng dẫn đặt lại mật khẩu."}
                </p>
              </div>

              {recoveryChecking && (
                <>
                  <div className="auth-checking-state" id="forgot-checking-state" role="status">
                    <span className="auth-checking-spinner" aria-hidden="true" />
                    <span>Đang kiểm tra trạng thái khôi phục...</span>
                  </div>
                  <div className="auth-footer-Switch">
                    <button
                      type="button"
                      className="btn-text-link"
                      id="btn-forgot-to-login"
                      onClick={() => setView("login")}
                    >
                      ← Quay về Đăng nhập
                    </button>
                  </div>
                </>
              )}

              {recoveryDisabled && (
                <>
                  <div className="auth-recovery-notice" id="forgot-unavailable-note" role="status">
                    <span className="auth-recovery-notice-icon" aria-hidden="true">
                      <AuthInfoIcon />
                    </span>
                    <div className="auth-recovery-notice-body">
                      <p className="auth-recovery-notice-title">
                        Tính năng gửi email khôi phục chưa được bật
                      </p>
                      <p className="auth-recovery-notice-copy">
                        Hệ thống hiện chưa hỗ trợ gửi mã đặt lại mật khẩu tự động qua email. Vui
                        lòng liên hệ giáo viên hoặc quản trị viên hệ thống để được hỗ trợ đặt lại
                        mật khẩu.
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="btn-auth-submit"
                    id="btn-forgot-to-login"
                    onClick={() => setView("login")}
                  >
                    <span>Quay về Đăng nhập</span>
                  </button>
                </>
              )}

              {emailRecoveryAvailable === true && (
                <>
                  {forgotBanner.text && (
                    <div
                      className={`auth-feedback-banner ${forgotBanner.tone || "neutral"} visible`}
                      id="forgot-feedback-banner"
                      role={forgotBanner.tone === "warn" ? "alert" : "status"}
                    >
                      {forgotBanner.tone === "warn" && <AuthInlineAlertIcon />}
                      <span>{forgotBanner.text}</span>
                    </div>
                  )}

                  <form className="auth-form" id="form-forgot" noValidate onSubmit={(e) => void handleForgotSubmit(e)}>
                    <div className="auth-field">
                      <label className="auth-label" htmlFor="forgot-email-input">
                        Email
                      </label>
                      <input
                        type="email"
                        id="forgot-email-input"
                        className={`auth-input${forgotEmailErr ? " is-invalid" : ""}`}
                        placeholder="Nhập địa chỉ email"
                        value={forgotEmail}
                        onChange={(e) => {
                          setForgotEmail(e.target.value);
                          if (forgotEmailErr) setForgotEmailErr("");
                          if (forgotBanner.text) setForgotBanner({ tone: "neutral", text: "" });
                        }}
                        onBlur={() => {
                          const em = forgotEmail.trim();
                          if (em.length > 0 && !isPlausibleEmail(em)) {
                            setForgotEmailErr("Địa chỉ email chưa đúng định dạng.");
                          }
                        }}
                        aria-invalid={Boolean(forgotEmailErr)}
                        aria-describedby={forgotEmailErr ? "err-forgot-email" : undefined}
                        autoComplete="email"
                        disabled={busy}
                      />
                      <div
                        className={`field-inline-error${forgotEmailErr ? " visible" : ""}`}
                        id="err-forgot-email"
                        role="alert"
                      >
                        {forgotEmailErr && <AuthInlineAlertIcon />}
                        <span>{forgotEmailErr}</span>
                      </div>
                    </div>

                    <button
                      type="submit"
                      className={`btn-auth-submit${busy ? " is-loading" : ""}`}
                      id="btn-forgot-submit"
                      disabled={busy}
                      aria-busy={busy}
                    >
                      {busy && <span className="auth-btn-spinner" aria-hidden="true" />}
                      <span>{busy ? "Đang gửi..." : forgotSent ? "Gửi lại hướng dẫn" : "Gửi hướng dẫn"}</span>
                    </button>
                  </form>

                  <div className="auth-footer-Switch">
                    <button
                      type="button"
                      className="btn-text-link"
                      id="btn-forgot-to-login"
                      onClick={() => setView("login")}
                    >
                      ← Quay về Đăng nhập
                    </button>
                    <span aria-hidden="true"> · </span>
                    <button
                      type="button"
                      className="btn-text-link"
                      id="btn-forgot-have-token"
                      onClick={() => setView("reset")}
                    >
                      Nhập mã khôi phục →
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
          <div className="auth-bottom-spacer" />
        </div>
      </section>
    );
  }

  return (
    <section className="axo-page-view active" id="view-reset" aria-label="Đặt lại mật khẩu Axo">
      <div className="auth-standalone-shell">
        {renderTopBar()}
        <div className="auth-center-stage">
          <div className="auth-card">
            <div className="auth-head">
              <h1 className="auth-title">Đặt lại mật khẩu</h1>
              <p className="auth-subtitle">Nhập mật khẩu mới cho tài khoản Axo của bạn.</p>
            </div>

            <form className="auth-form" id="reset-valid-box" noValidate onSubmit={(e) => void handleResetSubmit(e)}>
              <div
                className={`auth-feedback-banner${resetBanner.tone ? ` ${resetBanner.tone}` : ""}${resetBanner.text || resetDone ? " visible" : ""}`}
                id="reset-success-banner"
                role={resetBanner.tone === "warn" ? "alert" : "status"}
              >
                {resetBanner.tone === "warn" && <AuthInlineAlertIcon />}
                <span>
                  {resetBanner.text ||
                    "Mật khẩu của bạn đã được đặt lại thành công. Bạn có thể đăng nhập bằng mật khẩu mới."}
                </span>
              </div>
              {resetBanner.tone === "warn" && !user?.mustChangePassword && (
                <button
                  type="button"
                  className="btn-text-link"
                  id="btn-reset-request-new-link"
                  onClick={() => setView("forgot")}
                >
                  Yêu cầu liên kết đặt lại mới →
                </button>
              )}

              {!user?.mustChangePassword && (
                <div className="auth-field">
                  <label className="auth-label" htmlFor="reset-token-input">
                    Mã khôi phục
                  </label>
                  <input
                    type="text"
                    id="reset-token-input"
                    className={`auth-input${resetErrors.token ? " is-invalid" : ""}`}
                    placeholder="Nhập mã khôi phục gồm chữ và số"
                    value={resetToken}
                    onChange={(e) => {
                      setResetToken(e.target.value);
                      if (resetErrors.token) setResetErrors((p) => ({ ...p, token: undefined }));
                    }}
                    aria-invalid={Boolean(resetErrors.token)}
                    aria-describedby={resetErrors.token ? "err-reset-token" : undefined}
                    autoComplete="one-time-code"
                  />
                  <div
                    className={`field-inline-error${resetErrors.token ? " visible" : ""}`}
                    id="err-reset-token"
                    role="alert"
                  >
                    {resetErrors.token && <AuthInlineAlertIcon />}
                    <span>{resetErrors.token}</span>
                  </div>
                </div>
              )}

              <div className="auth-field">
                <div className="auth-label-row">
                  <label className="auth-label" htmlFor="reset-pw-input">
                    Mật khẩu mới
                  </label>
                  <span className="auth-field-meta-hint" id="hint-reset-pw">
                    Tối thiểu 8 ký tự
                  </span>
                </div>
                <div className="auth-input-wrap">
                  <input
                    type={showResetPw ? "text" : "password"}
                    id="reset-pw-input"
                    className={`auth-input has-toggle${resetErrors.pw ? " is-invalid" : ""}`}
                    placeholder="Tạo mật khẩu mới"
                    value={resetPw}
                    onChange={(e) => {
                      setResetPw(e.target.value);
                      if (resetErrors.pw) setResetErrors((p) => ({ ...p, pw: undefined }));
                    }}
                    aria-invalid={Boolean(resetErrors.pw)}
                    aria-describedby={resetErrors.pw ? "hint-reset-pw err-reset-pw" : "hint-reset-pw"}
                    autoComplete="new-password"
                  />
                  <PwToggleButton
                    id="btn-toggle-reset-pw"
                    targetId="reset-pw-input"
                    shown={showResetPw}
                    onToggle={() => setShowResetPw((v) => !v)}
                  />
                </div>
                <div
                  className={`field-inline-error${resetErrors.pw ? " visible" : ""}`}
                  id="err-reset-pw"
                  role="alert"
                >
                  {resetErrors.pw && <AuthInlineAlertIcon />}
                  <span>{resetErrors.pw}</span>
                </div>
              </div>

              <div className="auth-field">
                <label className="auth-label" htmlFor="reset-pw-confirm-input">
                  Xác nhận mật khẩu
                </label>
                <div className="auth-input-wrap">
                  <input
                    type={showResetPwConfirm ? "text" : "password"}
                    id="reset-pw-confirm-input"
                    className={`auth-input has-toggle${resetErrors.pwConfirm ? " is-invalid" : ""}`}
                    placeholder="Nhập lại mật khẩu"
                    value={resetPwConfirm}
                    onChange={(e) => {
                      setResetPwConfirm(e.target.value);
                      if (resetErrors.pwConfirm)
                        setResetErrors((p) => ({ ...p, pwConfirm: undefined }));
                    }}
                    aria-invalid={Boolean(resetErrors.pwConfirm)}
                    aria-describedby={resetErrors.pwConfirm ? "err-reset-pw-confirm" : undefined}
                    autoComplete="new-password"
                  />
                  <PwToggleButton
                    id="btn-toggle-reset-pw-confirm"
                    targetId="reset-pw-confirm-input"
                    shown={showResetPwConfirm}
                    onToggle={() => setShowResetPwConfirm((v) => !v)}
                  />
                </div>
                <div
                  className={`field-inline-error${resetErrors.pwConfirm ? " visible" : ""}`}
                  id="err-reset-pw-confirm"
                  role="alert"
                >
                  {resetErrors.pwConfirm && <AuthInlineAlertIcon />}
                  <span>{resetErrors.pwConfirm}</span>
                </div>
              </div>

              <button
                type="submit"
                className={`btn-auth-submit${busy ? " is-loading" : ""}`}
                id="btn-reset-submit"
                disabled={busy}
                aria-busy={busy}
              >
                {busy && <span className="auth-btn-spinner" aria-hidden="true" />}
                <span>{busy ? "Đang cập nhật..." : "Đặt lại mật khẩu"}</span>
              </button>
            </form>

            <div className="auth-footer-Switch">
              <button
                type="button"
                className="btn-text-link"
                id="btn-reset-to-login"
                onClick={() => setView("login")}
              >
                ← Quay về Đăng nhập
              </button>
            </div>
          </div>
        </div>
        <div className="auth-bottom-spacer" />
      </div>
    </section>
  );
}


export default AuthPageView;
