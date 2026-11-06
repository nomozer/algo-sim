import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuthStore, type Role } from "../state/auth";
import { useAppStore } from "../state/store";
import { useToastStore } from "./TopNav";
import { IconAxoLogo, IconAxoSidebarLogo, IconCheck } from "./icons";
import { AxoScrollbar } from "./AxoScrollbar";

/* ── Shared Eye Toggle Icon (HTML V2.7 P4.1) ─────────────────────────────── */

function PwToggleButton({
  id,
  targetId,
  shown,
  onToggle,
}: {
  id: string;
  targetId: string;
  shown: boolean;
  onToggle: () => void;
}) {
  const [justClicked, setJustClicked] = useState(false);
  const label = shown ? "Ẩn mật khẩu" : "Hiện mật khẩu";
  return (
    <button
      type="button"
      className="btn-pw-toggle"
      id={id}
      data-pw-target={targetId}
      data-just-clicked={justClicked ? "1" : undefined}
      aria-label={label}
      aria-pressed={shown}
      onMouseDown={() => setJustClicked(true)}
      onMouseLeave={() => setJustClicked(false)}
      onBlur={() => setJustClicked(false)}
      onClick={onToggle}
    >
      {shown ? (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49" />
          <path d="M14.084 14.158a3 3 0 0 1-4.242-4.242" />
          <path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143" />
          <path d="m2 2 20 20" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      )}
      <span className="pw-toggle-tooltip" role="tooltip">
        {label}
      </span>
    </button>
  );
}

/* ── AuthGate Modal (Guest Trial Limit & Must-Change-Password Guard) ────── */

export function AuthGate() {
  const mode = useAuthStore((s) => s.authGate);
  const busy = useAuthStore((s) => s.busy);
  const error = useAuthStore((s) => s.error);
  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);
  const close = useAuthStore((s) => s.closeAuthGate);
  const open = useAuthStore((s) => s.openAuthGate);

  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("student");
  const [teacherCode, setTeacherCode] = useState("");

  if (!mode) return null;
  const isRegister = mode === "register";

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isRegister) {
      await register({
        email,
        displayName: name,
        password,
        role: role === "admin" ? "student" : role,
        teacherCode: role === "teacher" ? teacherCode : undefined,
      });
    } else {
      await login(email, password);
    }
  };

  return (
    <div
      className="auth-overlay"
      role="dialog"
      aria-modal="true"
      aria-label={isRegister ? "Đăng ký tài khoản" : "Đăng nhập"}
      onClick={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div className="auth-card">
        <div className="auth-head">
          <h2 className="auth-title">{isRegister ? "Tạo tài khoản" : "Đăng nhập"}</h2>
          <button
            type="button"
            className="auth-close"
            onClick={close}
            aria-label="Đóng"
          >
            ×
          </button>
        </div>

        <form className="auth-form" onSubmit={(e) => void submit(e)}>
          {isRegister && (
            <label className="auth-field">
              <span>Tên hiển thị</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
                required
                placeholder="Nhập tên của bạn"
              />
            </label>
          )}
          <label className="auth-field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              placeholder="Nhập địa chỉ email"
            />
          </label>
          <label className="auth-field">
            <span>Mật khẩu</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isRegister ? "new-password" : "current-password"}
              required
              minLength={8}
              placeholder={isRegister ? "Tạo mật khẩu" : "Nhập mật khẩu"}
            />
          </label>

          {isRegister && (
            <fieldset className="auth-roles">
              <legend>Em/thầy cô dùng Axo với vai trò</legend>
              <label className="auth-role">
                <input
                  type="radio"
                  name="role"
                  checked={role === "student"}
                  onChange={() => setRole("student")}
                />
                <span>Học sinh</span>
              </label>
              <label className="auth-role">
                <input
                  type="radio"
                  name="role"
                  checked={role === "teacher"}
                  onChange={() => setRole("teacher")}
                />
                <span>Giáo viên</span>
              </label>
            </fieldset>
          )}

          {isRegister && role === "teacher" && (
            <label className="auth-field">
              <span>Mã giáo viên</span>
              <input
                value={teacherCode}
                onChange={(e) => setTeacherCode(e.target.value)}
                placeholder="Mã do nhà trường cấp"
              />
              <small className="auth-hint">
                Tài khoản giáo viên cần mã mời từ người quản trị hệ thống.
              </small>
            </label>
          )}

          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="btn-primary auth-submit" disabled={busy}>
            {busy ? "Đang xử lý…" : isRegister ? "Tạo tài khoản" : "Đăng nhập"}
          </button>
        </form>

        <p className="auth-swap">
          {isRegister ? "Đã có tài khoản? " : "Chưa có tài khoản? "}
          <button
            type="button"
            className="link-button"
            onClick={() => open(isRegister ? "login" : "register")}
          >
            {isRegister ? "Đăng nhập" : "Đăng ký"}
          </button>
        </p>
      </div>
    </div>
  );
}

/* ── AuthPageView (Standalone Views 5–8: #view-login, #view-register, #view-forgot, #view-reset) ── */

export function AuthPageView({
  mode,
  initialEmailRecoveryAvailable = null,
}: {
  mode: "login" | "register" | "forgot" | "reset";
  initialEmailRecoveryAvailable?: boolean | null;
}) {
  const goHome = useAppStore((s) => s.goHome);
  const setView = useAppStore((s) => s.setView);
  const authResetEmail = useAppStore((s) => s.authResetEmail);
  const setAuthResetEmail = useAppStore((s) => s.setAuthResetEmail);

  const user = useAuthStore((s) => s.user);
  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);
  const requestPasswordReset = useAuthStore((s) => s.requestPasswordReset);
  const fetchRecoveryStatus = useAuthStore((s) => s.fetchRecoveryStatus);
  const resetPassword = useAuthStore((s) => s.resetPassword);
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
  const [, setForgotSent] = useState(false);
  const [forgotBanner, setForgotBanner] = useState<{ tone: "warn" | "neutral" | ""; text: string }>({
    tone: "neutral",
    text: "",
  });

  const [resetToken, setResetToken] = useState(() => {
    if (typeof window === "undefined") return "";
    return new URLSearchParams(window.location.search).get("reset_token")?.trim() || "";
  });
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

  const isPlausibleEmail = (raw: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(raw.trim());
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
    if (!em) {
      errs.email = "Vui lòng nhập địa chỉ email.";
    } else if (!isPlausibleEmail(em)) {
      errs.email = "Địa chỉ email chưa đúng định dạng.";
    }
    if (!loginPw) {
      errs.pw = "Vui lòng nhập mật khẩu.";
    }
    if (errs.email || errs.pw) {
      setLoginErrors(errs);
      setLoginBanner({ tone: "", text: "" });
      focusById(errs.email ? "login-email-input" : "login-pw-input");
      return;
    }
    setLoginErrors({});
    setLoginBanner({ tone: "", text: "" });
    await login(em, loginPw);
    const currentUser = useAuthStore.getState().user;
    const currentErr = useAuthStore.getState().error;
    if (currentUser) {
      if (currentUser.role === "admin") {
        setView("admin");
      } else {
        goHome();
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
      if (errs.name) focusById("reg-name-input");
      else if (errs.email) focusById("reg-email-input");
      else if (errs.pw) focusById("reg-pw-input");
      else focusById("reg-pw-confirm-input");
      return;
    }
    setRegErrors({});
    setRegBanner({ tone: "", text: "" });
    await register({
      email: em,
      displayName: nm,
      password: regPw,
      role: "student",
    });
    const currentUser = useAuthStore.getState().user;
    const currentErr = useAuthStore.getState().error;
    if (currentUser) {
      goHome();
    } else if (currentErr) {
      setRegBanner({ tone: "warn", text: currentErr });
    }
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (emailRecoveryAvailable === false || busy) {
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
        setForgotBanner({ tone: "neutral", text: "" });
        useToastStore.getState().showToast({
          id: "forgot-password-submitted",
          tone: "info",
          title: "Đã tiếp nhận yêu cầu khôi phục",
          description:
            "Nếu email có trong hệ thống, hướng dẫn đặt lại mật khẩu (hiệu lực 15 phút) sẽ được gửi trong ít phút.",
          durationMs: 7000,
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

  const renderTopBar = () => (
    <div className="auth-top-bar">
      <button
        type="button"
        className="auth-brand-link"
        data-auth-home="1"
        aria-label="Về Trang chủ"
        title="Về Trang chủ"
        onClick={goHome}
      >
        <IconAxoLogo size={22} />
        <span>Axo</span>
      </button>
    </div>
  );

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
                <h2 className="auth-title">Đăng nhập</h2>
                <p className="auth-subtitle">Nhập email và mật khẩu để tiếp tục học tập trên Axo.</p>
              </div>

              <div
                className={`auth-feedback-banner${bannerTone ? ` ${bannerTone}` : ""}${bannerMsg ? " visible" : ""}`}
                id="login-feedback-banner"
                role="status"
              >
                {bannerMsg}
              </div>

              <form className="auth-form" id="form-login" noValidate onSubmit={(e) => void handleLoginSubmit(e)}>
                <div className="auth-field">
                  <label className="auth-label" htmlFor="login-email-input">
                    Email
                  </label>
                  <input
                    type="email"
                    id="login-email-input"
                    className={`auth-input${loginErrors.email ? " is-invalid" : ""}`}
                    placeholder="Nhập địa chỉ email"
                    value={loginEmail}
                    onChange={(e) => {
                      setLoginEmail(e.target.value);
                      if (loginErrors.email) setLoginErrors((p) => ({ ...p, email: undefined }));
                      if (loginBanner.text) setLoginBanner({ tone: "", text: "" });
                    }}
                    aria-invalid={Boolean(loginErrors.email)}
                    aria-describedby={loginErrors.email ? "err-login-email" : undefined}
                    autoComplete="username"
                  />
                  <div
                    className={`field-inline-error${loginErrors.email ? " visible" : ""}`}
                    id="err-login-email"
                    role="alert"
                  >
                    {loginErrors.email}
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
                    {loginErrors.pw}
                  </div>
                </div>

                <button type="submit" className={`btn-auth-submit${busy ? " is-loading" : ""}`} id="btn-login-submit" disabled={busy}>
                  {busy ? "Đang đăng nhập..." : "Đăng nhập"}
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
                <h2 className="auth-title">Tạo tài khoản</h2>
                <p className="auth-subtitle">
                  Tạo tài khoản cá nhân để lưu lịch sử dựng hình và sử dụng đầy đủ tính năng của Axo.
                </p>
              </div>

              <div
                className={`auth-feedback-banner${bannerTone ? ` ${bannerTone}` : ""}${bannerMsg ? " visible" : ""}`}
                id="register-feedback-banner"
                role="status"
              >
                {bannerMsg}
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
                    {regErrors.name}
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
                    {regErrors.email}
                  </div>
                </div>

                <div className="auth-field">
                  <div className="auth-label-row">
                    <label className="auth-label" htmlFor="reg-pw-input">
                      Mật khẩu
                    </label>
                    <span className="auth-field-meta-hint">Tối thiểu 8 ký tự</span>
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
                      }}
                      aria-invalid={Boolean(regErrors.pw)}
                      aria-describedby={regErrors.pw ? "err-reg-pw" : undefined}
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
                    {regErrors.pw}
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
                    {regErrors.pwConfirm}
                  </div>
                </div>

                <button type="submit" className={`btn-auth-submit${busy ? " is-loading" : ""}`} id="btn-register-submit" disabled={busy}>
                  {busy ? "Đang tạo tài khoản..." : "Tạo tài khoản"}
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

  if (mode === "forgot") {
    const recoveryDisabled = emailRecoveryAvailable === false;
    return (
      <section className="axo-page-view active" id="view-forgot" aria-label="Quên mật khẩu Axo">
        <div className="auth-standalone-shell">
          {renderTopBar()}
          <div className="auth-center-stage">
            <div className="auth-card">
              <div className="auth-head">
                <h2 className="auth-title">Quên mật khẩu?</h2>
                <p className="auth-subtitle">
                  {recoveryDisabled
                    ? "Khôi phục mật khẩu tài khoản Axo của bạn."
                    : "Nhập địa chỉ email của bạn để nhận hướng dẫn đặt lại mật khẩu."}
                </p>
              </div>

              {recoveryDisabled && (
                <p className="forgot-status-note" id="forgot-unavailable-note" role="status">
                  Tính năng gửi mã khôi phục qua email hiện chưa được bật trên hệ thống này. Vui
                  lòng liên hệ giáo viên hoặc quản trị viên để được hỗ trợ đặt lại mật khẩu.
                </p>
              )}

              {forgotBanner.text && !recoveryDisabled && (
                <div
                  className={`auth-feedback-banner ${forgotBanner.tone || "neutral"} visible`}
                  id="forgot-feedback-banner"
                  role="status"
                >
                  {forgotBanner.text}
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
                    }}
                    aria-invalid={Boolean(forgotEmailErr)}
                    aria-describedby={forgotEmailErr ? "err-forgot-email" : undefined}
                    autoComplete="email"
                    disabled={recoveryDisabled || busy}
                  />
                  <div
                    className={`field-inline-error${forgotEmailErr ? " visible" : ""}`}
                    id="err-forgot-email"
                    role="alert"
                  >
                    {forgotEmailErr}
                  </div>
                </div>

                <button
                  type="submit"
                  className={`btn-auth-submit${busy ? " is-loading" : ""}`}
                  id="btn-forgot-submit"
                  disabled={busy || recoveryDisabled}
                >
                  {busy ? "Đang gửi..." : "Gửi hướng dẫn"}
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
                {!recoveryDisabled && (
                  <>
                    <span aria-hidden="true"> · </span>
                    <button
                      type="button"
                      className="btn-text-link"
                      id="btn-forgot-have-token"
                      onClick={() => setView("reset")}
                    >
                      Nhập mã khôi phục →
                    </button>
                  </>
                )}
              </div>
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
              <h2 className="auth-title">Đặt lại mật khẩu</h2>
              <p className="auth-subtitle">Nhập mật khẩu mới cho tài khoản Axo của bạn.</p>
            </div>

            <form className="auth-form" id="reset-valid-box" noValidate onSubmit={(e) => void handleResetSubmit(e)}>
              <div
                className={`auth-feedback-banner${resetBanner.tone ? ` ${resetBanner.tone}` : ""}${resetBanner.text || resetDone ? " visible" : ""}`}
                id="reset-success-banner"
                role="status"
              >
                {resetBanner.text ||
                  "Mật khẩu của bạn đã được đặt lại thành công. Bạn có thể đăng nhập bằng mật khẩu mới."}
              </div>

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
                    {resetErrors.token}
                  </div>
                </div>
              )}

              <div className="auth-field">
                <div className="auth-label-row">
                  <label className="auth-label" htmlFor="reset-pw-input">
                    Mật khẩu mới
                  </label>
                  <span className="auth-field-meta-hint">Tối thiểu 8 ký tự</span>
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
                    aria-describedby={resetErrors.pw ? "err-reset-pw" : undefined}
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
                  {resetErrors.pw}
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
                  {resetErrors.pwConfirm}
                </div>
              </div>

              <button type="submit" className={`btn-auth-submit${busy ? " is-loading" : ""}`} id="btn-reset-submit" disabled={busy}>
                {busy ? "Đang cập nhật..." : "Đặt lại mật khẩu"}
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

/* ── AccountSettingsModal (#user-account-settings-modal — HTML V2.7 P3–P12) ── */

const GRADE_OPTIONS = [
  { id: "opt-stu-grade-empty", value: "", label: "Chọn khối lớp", isPlaceholder: true },
  { id: "opt-stu-grade-10", value: "Khối 10", label: "Khối 10", isPlaceholder: false },
  { id: "opt-stu-grade-11", value: "Khối 11", label: "Khối 11", isPlaceholder: false },
  { id: "opt-stu-grade-12", value: "Khối 12", label: "Khối 12", isPlaceholder: false },
  { id: "opt-stu-grade-other", value: "Khác", label: "Khác", isPlaceholder: false },
];

export function AccountSettingsModal() {
  const open = useAppStore((s) => s.accountModalOpen);
  const tab = useAppStore((s) => s.accountModalTab);
  const openAccountModal = useAppStore((s) => s.openAccountModal);
  const closeAccountModal = useAppStore((s) => s.closeAccountModal);

  const user = useAuthStore((s) => s.user);
  const updateProfile = useAuthStore((s) => s.updateProfile);
  const changePassword = useAuthStore((s) => s.changePassword);
  const busy = useAuthStore((s) => s.busy);

  const [displayName, setDisplayName] = useState("");
  const [studentSchool, setStudentSchool] = useState("");
  const [studentGrade, setStudentGrade] = useState("");
  const [studentClass, setStudentClass] = useState("");
  const [teacherSchool, setTeacherSchool] = useState("");
  const [teacherSubject, setTeacherSubject] = useState("");
  const [gradeMenuOpen, setGradeMenuOpen] = useState(false);

  const [savedExtra, setSavedExtra] = useState({
    studentSchool: "",
    studentGrade: "",
    studentClass: "",
    teacherSchool: "",
    teacherSubject: "",
  });

  const [nameError, setNameError] = useState("");
  const [profileFeedback, setProfileFeedback] = useState<{ tone: "warn" | ""; text: string }>({
    tone: "",
    text: "",
  });

  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [showConfirmPw, setShowConfirmPw] = useState(false);
  const [pwFeedback, setPwFeedback] = useState<{ tone: "warn" | ""; text: string }>({
    tone: "",
    text: "",
  });

  const gradeWrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (open && user) {
      setDisplayName(user.displayName || "");
      const initStuSchool = user.school || "";
      const initStuGrade = user.grade || "";
      const initStuClass = user.className || "";
      const initTeaSchool = user.workplace || user.school || "";
      const initTeaSubject = user.subject || "";
      setStudentSchool(initStuSchool);
      setStudentGrade(initStuGrade);
      setStudentClass(initStuClass);
      setTeacherSchool(initTeaSchool);
      setTeacherSubject(initTeaSubject);
      setSavedExtra({
        studentSchool: initStuSchool,
        studentGrade: initStuGrade,
        studentClass: initStuClass,
        teacherSchool: initTeaSchool,
        teacherSubject: initTeaSubject,
      });
      setNameError("");
      setProfileFeedback({ tone: "", text: "" });
      setPwFeedback({ tone: "", text: "" });
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
      setGradeMenuOpen(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, user?.id]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (gradeMenuOpen) {
          setGradeMenuOpen(false);
          return;
        }
        closeAccountModal();
      }
    };
    const onMouseDown = (e: MouseEvent) => {
      if (gradeMenuOpen && gradeWrapRef.current && !gradeWrapRef.current.contains(e.target as Node)) {
        setGradeMenuOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("mousedown", onMouseDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("mousedown", onMouseDown);
    };
  }, [open, gradeMenuOpen, closeAccountModal]);

  if (!user) return null;

  const roleLabel =
    user.role === "admin"
      ? "Quản trị viên"
      : user.role === "teacher"
        ? "Giáo viên"
        : "Học sinh";

  const quotaMax =
    typeof user.dailyLimit === "number" && user.dailyLimit > 0
      ? user.dailyLimit
      : user.role === "admin"
        ? 500
        : user.role === "teacher"
          ? 80
          : 15;
  const quotaUsed = Math.min(
    quotaMax,
    typeof user.usedToday === "number" ? user.usedToday : 0,
  );
  const nameParts = (user.displayName || "U").trim().split(/\s+/).filter(Boolean);
  const initialChar = (nameParts[nameParts.length - 1] ?? "U").charAt(0).toUpperCase();

  const isProfileDirty =
    displayName.trim() !== (user.displayName || "").trim() ||
    studentSchool.trim() !== savedExtra.studentSchool ||
    studentGrade !== savedExtra.studentGrade ||
    studentClass.trim() !== savedExtra.studentClass ||
    teacherSchool.trim() !== savedExtra.teacherSchool ||
    teacherSubject.trim() !== savedExtra.teacherSubject;

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = displayName.trim();
    if (!trimmed) {
      setNameError("Vui lòng nhập tên hiển thị.");
      return;
    }
    setNameError("");
    const res = await updateProfile({
      displayName: trimmed,
      school: user.role === "teacher" ? teacherSchool.trim() : studentSchool.trim(),
      grade: studentGrade,
      className: studentClass.trim(),
      workplace: teacherSchool.trim(),
      subject: teacherSubject.trim(),
    });
    if (res.ok) {
      setSavedExtra({
        studentSchool: studentSchool.trim(),
        studentGrade,
        studentClass: studentClass.trim(),
        teacherSchool: teacherSchool.trim(),
        teacherSubject: teacherSubject.trim(),
      });
      setProfileFeedback({ tone: "", text: "Đã lưu thông tin cá nhân thành công." });
    } else {
      setProfileFeedback({ tone: "warn", text: res.error || "Không thể cập nhật thông tin." });
    }
  };

  const handleSavePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPw) {
      setPwFeedback({ tone: "warn", text: "Vui lòng nhập mật khẩu hiện tại." });
      return;
    }
    if (!newPw || newPw.length < 8) {
      setPwFeedback({ tone: "warn", text: "Mật khẩu mới phải có tối thiểu 8 ký tự." });
      return;
    }
    if (newPw !== confirmPw) {
      setPwFeedback({ tone: "warn", text: "Xác nhận mật khẩu mới không khớp." });
      return;
    }
    const res = await changePassword(currentPw, newPw);
    if (res.ok) {
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
      setPwFeedback({ tone: "", text: "Đã đổi mật khẩu thành công." });
    } else {
      setPwFeedback({ tone: "warn", text: res.error || "Không thể đổi mật khẩu." });
    }
  };

  return (
    <div
      className={`axo-modal-backdrop${open ? " open" : ""}`}
      id="user-account-settings-modal"
      role="dialog"
      aria-modal="true"
      aria-hidden={!open}
      aria-labelledby="user-account-settings-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) closeAccountModal();
      }}
    >
      <div className="axo-modal-dialog account-settings-dialog">
        <div className="axo-modal-head">
          <span className="axo-modal-title" id="user-account-settings-title">
            Cài đặt tài khoản
          </span>
          <button
            type="button"
            className="context-close-icon-btn"
            id="btn-close-account-settings-modal"
            aria-label="Đóng cài đặt tài khoản"
            title="Đóng (Esc)"
            onClick={closeAccountModal}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div
          className="acc-modal-tabs"
          id="user-account-settings-tabs"
          role="tablist"
          aria-label="Danh mục cài đặt tài khoản"
        >
          <button
            type="button"
            role="tab"
            className={`acc-modal-tab-btn${tab === "profile" ? " is-active" : ""}`}
            id="tab-btn-acc-profile"
            data-acc-tab="profile"
            aria-selected={tab === "profile"}
            aria-controls="acc-modal-sec-profile"
            tabIndex={tab === "profile" ? 0 : -1}
            onClick={() => openAccountModal("profile")}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            <span>Thông tin cá nhân</span>
          </button>
          <button
            type="button"
            role="tab"
            className={`acc-modal-tab-btn${tab === "security" ? " is-active" : ""}`}
            id="tab-btn-acc-security"
            data-acc-tab="security"
            aria-selected={tab === "security"}
            aria-controls="acc-modal-sec-security"
            tabIndex={tab === "security" ? 0 : -1}
            onClick={() => openAccountModal("security")}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <span>Bảo mật</span>
          </button>
        </div>

        <div className="axo-modal-body" id="user-account-settings-body">
          {/* Tab 1: Thông tin cá nhân */}
          <section
            className={`acc-modal-section acc-modal-tab-panel${tab === "profile" ? " is-active" : ""}`}
            id="acc-modal-sec-profile"
            role="tabpanel"
            aria-labelledby="tab-btn-acc-profile"
            hidden={tab !== "profile"}
          >
            <div className="acc-profile-summary-bar">
              <div className="acc-profile-id-left">
                <span
                  className={`acc-modal-avatar${user.role === "student" ? "" : ` ${user.role}`}`}
                  id="acc-settings-avatar"
                >
                  {initialChar}
                </span>
                <div>
                  <div className="acc-summary-name" id="acc-settings-summary-name">
                    {user.displayName}
                  </div>
                  <div className="acc-summary-quota" id="acc-settings-summary-quota">
                    Hạn mức phân tích AI hôm nay: Đã dùng {quotaUsed}/{quotaMax} lượt
                  </div>
                </div>
              </div>
              <span className={`role-chip ${user.role}`} id="acc-settings-role-chip">
                {roleLabel}
              </span>
            </div>

            <div
              className={`auth-feedback-banner${profileFeedback.tone ? ` ${profileFeedback.tone}` : ""}${profileFeedback.text ? " visible" : ""}`}
              id="acc-profile-feedback"
              role="status"
            >
              {profileFeedback.text}
            </div>

            <form
              className="auth-form"
              id="form-acc-profile"
              noValidate
              onSubmit={(e) => void handleSaveProfile(e)}
            >
              <div className="auth-field">
                <label className="auth-label" htmlFor="acc-settings-name-input">
                  Tên hiển thị
                </label>
                <input
                  type="text"
                  id="acc-settings-name-input"
                  className={`auth-input${nameError ? " is-invalid" : ""}`}
                  value={displayName}
                  onChange={(e) => {
                    setDisplayName(e.target.value);
                    setNameError("");
                    setProfileFeedback({ tone: "", text: "" });
                  }}
                  autoComplete="name"
                />
                <div
                  className={`field-inline-error${nameError ? " visible" : ""}`}
                  id="err-acc-settings-name"
                  role="alert"
                >
                  {nameError}
                </div>
              </div>

              <div className="acc-modal-grid-2">
                <div className="auth-field">
                  <label className="auth-label" htmlFor="acc-settings-email-input">
                    Email đang sử dụng
                  </label>
                  <input
                    type="email"
                    id="acc-settings-email-input"
                    className="auth-input is-readonly-static"
                    value={user.email}
                    readOnly
                    aria-readonly="true"
                    tabIndex={-1}
                  />
                </div>
                <div className="auth-field">
                  <span className="auth-label" id="acc-settings-role-label">
                    Vai trò hiện tại
                  </span>
                  <div
                    className="acc-readonly-role-box"
                    id="acc-settings-role-display"
                    aria-labelledby="acc-settings-role-label"
                    aria-readonly="true"
                  >
                    <span className={`role-chip ${user.role}`} id="acc-settings-role-badge">
                      {roleLabel}
                    </span>
                    <span className="acc-readonly-role-note">Chỉ đọc</span>
                  </div>
                </div>
              </div>

              {user.role === "student" && (
                <div className="acc-role-extra-group" id="acc-student-academic-group">
                  <div className="acc-subsec-head">
                    <span className="acc-subsec-title">Thông tin học tập</span>
                    <span className="acc-subsec-optional">Không bắt buộc</span>
                  </div>

                  <div className="auth-field">
                    <label className="auth-label" htmlFor="acc-student-school-input">
                      Trường đang học
                    </label>
                    <input
                      type="text"
                      id="acc-student-school-input"
                      className="auth-input"
                      placeholder="Ví dụ: THPT Chuyên Hà Nội - Amsterdam"
                      value={studentSchool}
                      onChange={(e) => setStudentSchool(e.target.value)}
                      autoComplete="organization"
                    />
                  </div>

                  <div className="acc-modal-grid-2">
                    <div className="auth-field">
                      <label
                        className="auth-label"
                        id="lbl-acc-student-grade"
                        htmlFor="btn-acc-student-grade-trigger"
                      >
                        Khối lớp
                      </label>
                      <div
                        className={`axo-custom-select${gradeMenuOpen ? " is-open" : ""}`}
                        id="student-grade-dropdown-wrap"
                        ref={gradeWrapRef}
                      >
                        <input type="hidden" id="acc-student-grade-select" value={studentGrade} />
                        <button
                          type="button"
                          className="axo-custom-select-trigger"
                          id="btn-acc-student-grade-trigger"
                          role="combobox"
                          aria-haspopup="listbox"
                          aria-expanded={gradeMenuOpen}
                          aria-labelledby="lbl-acc-student-grade"
                          aria-controls="menu-acc-student-grade"
                          onClick={() => setGradeMenuOpen((v) => !v)}
                        >
                          <span
                            className={`axo-custom-select-value${!studentGrade ? " is-placeholder" : ""}`}
                            id="val-acc-student-grade"
                          >
                            {studentGrade || "Chọn khối lớp"}
                          </span>
                          <svg className="axo-custom-select-chevron" viewBox="0 0 24 24" aria-hidden="true">
                            <polyline points="6 9 12 15 18 9" />
                          </svg>
                        </button>
                        <div
                          className="axo-custom-select-menu"
                          id="menu-acc-student-grade"
                          role="listbox"
                          tabIndex={-1}
                          aria-labelledby="lbl-acc-student-grade"
                        >
                          {GRADE_OPTIONS.map((opt) => {
                            const selected = studentGrade === opt.value;
                            return (
                              <div
                                key={opt.id}
                                className={`axo-custom-select-option${selected ? " is-selected" : ""}`}
                                id={opt.id}
                                role="option"
                                data-select-value={opt.value}
                                data-select-label={opt.label}
                                data-is-placeholder={opt.isPlaceholder ? "true" : undefined}
                                aria-selected={selected}
                                onClick={() => {
                                  setStudentGrade(opt.value);
                                  setGradeMenuOpen(false);
                                }}
                              >
                                <div className="axo-opt-row">
                                  <span className="axo-opt-main">{opt.label}</span>
                                  <svg className="axo-opt-check" viewBox="0 0 24 24" aria-hidden="true">
                                    <polyline points="20 6 9 17 4 12" />
                                  </svg>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>

                    <div className="auth-field">
                      <label className="auth-label" htmlFor="acc-student-class-input">
                        Lớp
                      </label>
                      <input
                        type="text"
                        id="acc-student-class-input"
                        className="auth-input"
                        placeholder="Ví dụ: 11A1"
                        value={studentClass}
                        onChange={(e) => setStudentClass(e.target.value)}
                        autoComplete="off"
                      />
                    </div>
                  </div>
                </div>
              )}

              {user.role === "teacher" && (
                <div className="acc-role-extra-group" id="acc-teacher-work-group">
                  <div className="acc-subsec-head">
                    <span className="acc-subsec-title">Thông tin công tác</span>
                    <span className="acc-subsec-optional">Không bắt buộc</span>
                  </div>

                  <div className="auth-field">
                    <label className="auth-label" htmlFor="acc-teacher-school-input">
                      Trường/Đơn vị công tác
                    </label>
                    <input
                      type="text"
                      id="acc-teacher-school-input"
                      className="auth-input"
                      placeholder="Ví dụ: THPT Chu Văn An"
                      value={teacherSchool}
                      onChange={(e) => setTeacherSchool(e.target.value)}
                      autoComplete="organization"
                    />
                  </div>

                  <div className="auth-field">
                    <label className="auth-label" htmlFor="acc-teacher-subject-input">
                      Bộ môn giảng dạy
                    </label>
                    <input
                      type="text"
                      id="acc-teacher-subject-input"
                      className="auth-input"
                      placeholder="Ví dụ: Toán"
                      value={teacherSubject}
                      onChange={(e) => setTeacherSubject(e.target.value)}
                      autoComplete="off"
                    />
                  </div>
                </div>
              )}

              <div className="acc-modal-actions-row">
                <button
                  type="submit"
                  className="btn-settings-save"
                  id="btn-save-acc-profile"
                  disabled={!isProfileDirty || busy}
                >
                  {busy ? "Đang lưu..." : "Lưu thay đổi"}
                </button>
              </div>
            </form>
          </section>

          {/* Tab 2: Bảo mật */}
          <section
            className={`acc-modal-section acc-modal-tab-panel${tab === "security" ? " is-active" : ""}`}
            id="acc-modal-sec-security"
            role="tabpanel"
            aria-labelledby="tab-btn-acc-security"
            hidden={tab !== "security"}
          >
            <div className="acc-modal-sec-head">
              <span className="acc-modal-sec-title">Đổi mật khẩu</span>
              <span className="acc-pw-scope-hint" id="acc-pw-scope-hint">
                Đổi mật khẩu của tài khoản đang đăng nhập
              </span>
            </div>

            <div
              className={`auth-feedback-banner${pwFeedback.tone ? ` ${pwFeedback.tone}` : ""}${pwFeedback.text ? " visible" : ""}`}
              id="acc-pw-feedback"
              role="status"
            >
              {pwFeedback.text}
            </div>

            <form
              className="auth-form acc-pw-stack-1col"
              id="form-acc-password"
              noValidate
              onSubmit={(e) => void handleSavePassword(e)}
            >
              <div className="auth-field">
                <label className="auth-label" htmlFor="acc-pw-current-input">
                  Mật khẩu hiện tại
                </label>
                <div className="auth-input-wrap">
                  <input
                    type={showCurrentPw ? "text" : "password"}
                    id="acc-pw-current-input"
                    className="auth-input has-toggle"
                    placeholder="Nhập mật khẩu hiện tại"
                    value={currentPw}
                    onChange={(e) => setCurrentPw(e.target.value)}
                    autoComplete="current-password"
                  />
                  <PwToggleButton
                    id="btn-toggle-acc-pw-current"
                    targetId="acc-pw-current-input"
                    shown={showCurrentPw}
                    onToggle={() => setShowCurrentPw((v) => !v)}
                  />
                </div>
              </div>

              <div className="auth-field">
                <label className="auth-label" htmlFor="acc-pw-new-input">
                  Mật khẩu mới
                </label>
                <div className="auth-input-wrap">
                  <input
                    type={showNewPw ? "text" : "password"}
                    id="acc-pw-new-input"
                    className="auth-input has-toggle"
                    placeholder="Tối thiểu 8 ký tự"
                    value={newPw}
                    onChange={(e) => setNewPw(e.target.value)}
                    autoComplete="new-password"
                  />
                  <PwToggleButton
                    id="btn-toggle-acc-pw-new"
                    targetId="acc-pw-new-input"
                    shown={showNewPw}
                    onToggle={() => setShowNewPw((v) => !v)}
                  />
                </div>
              </div>

              <div className="auth-field">
                <label className="auth-label" htmlFor="acc-pw-confirm-input">
                  Xác nhận mật khẩu mới
                </label>
                <div className="auth-input-wrap">
                  <input
                    type={showConfirmPw ? "text" : "password"}
                    id="acc-pw-confirm-input"
                    className="auth-input has-toggle"
                    placeholder="Nhập lại mật khẩu mới"
                    value={confirmPw}
                    onChange={(e) => setConfirmPw(e.target.value)}
                    autoComplete="new-password"
                  />
                  <PwToggleButton
                    id="btn-toggle-acc-pw-confirm"
                    targetId="acc-pw-confirm-input"
                    shown={showConfirmPw}
                    onToggle={() => setShowConfirmPw((v) => !v)}
                  />
                </div>
              </div>

              <div className="acc-modal-actions-row">
                <button
                  type="submit"
                  className="btn-admin-sm"
                  id="btn-submit-acc-pw"
                  disabled={busy}
                >
                  {busy ? "Đang xử lý..." : "Đổi mật khẩu"}
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}

/* ── AdminWorkspaceView (#view-admin — HTML V2.7 P1–P6) ──────────────────── */

export interface AdminUserItem {
  id: number | string;
  name: string;
  email: string;
  role: "student" | "teacher" | "admin";
  status: "active" | "verified" | "pending_teacher" | "pending_activation" | "locked";
  school: string;
  adminNote?: string;
  passwordResetRequestedAt?: string;
  joinedAt: string;
  joinedTs: number;
  dailyLimit: number;
  tokenCap: number;
  usedToday: number;
  tokensToday: string;
}

interface AdminAuditLogItem {
  id: string;
  time: string;
  timestamp?: string;
  timeTs?: number;
  actor: string;
  action: string;
  target: string;
  detail: string;
}

interface BulkImportRowItem {
  rowNum: number;
  name: string;
  rawName: string;
  email: string;
  rawEmail: string;
  school: string;
  rawSchool: string;
  isValid: boolean;
  category: string;
  reason: string;
}

export interface AdminOverviewStatsFixture {
  configuredModelId?: string | null;
  totalAnalyses?: number;
  analysesToday?: number;
  analyses7d?: number;
  aiRequestsToday?: number;
  succeededRequests?: number;
  refusedRequests?: number;
  failedRequests?: number;
  succeeded7d?: number;
  refused7d?: number;
  failed7d?: number;
  avgLatencyMs?: number | null;
  avgLatency7dMs?: number | null;
  totalHistoryEntries?: number;
  totalClasses?: number;
  totalSessions?: number;
  tokensMeasured?: boolean;
  tokensToday?: number | null;
  inputTokens7d?: number | null;
  outputTokens7d?: number | null;
  thoughtsTokens7d?: number | null;
  totalTokens7d?: number | null;
  aiServiceConfigured?: boolean | null;
  cachedProblems?: number;
  dailyBreakdown?: Array<{
    dateIso: string;
    dateLabel: string;
    totalRequests: number;
    succeededRequests: number;
    refusedRequests: number;
    failedRequests: number;
    avgLatencyMs: number | null;
    tokensMeasured: boolean;
    inputTokens: number | null;
    outputTokens: number | null;
    thoughtsTokens: number | null;
    totalTokens: number | null;
  }>;
  roleQuotaSummary?: {
    student: { count: number; usedToday: number; dailyLimitDefault: number };
    teacher: { count: number; usedToday: number; dailyLimitDefault: number };
    admin: { count: number; usedToday: number; dailyLimitDefault: number };
  } | null;
}

export interface AdminDailyTelemetryItem {
  dateIso: string;
  dateLabel: string;
  totalRequests: number;
  succeededRequests: number;
  refusedRequests: number;
  failedRequests: number;
  avgLatencyMs: number | null;
  tokensMeasured: boolean;
  inputTokens: number | null;
  outputTokens: number | null;
  thoughtsTokens: number | null;
  totalTokens: number | null;
}

export interface AdminAnalyticsChartDay extends AdminDailyTelemetryItem {
  weekdayShort: string;
  shortDate: string;
  xAxisLabel: string;
  succeededHeightPct: number;
  refusedHeightPct: number;
  ariaLabel: string;
}

export interface AdminAnalyticsChartModel {
  hasActivity: boolean;
  maxTick: number;
  midTick: number;
  yTicks: [number, number, number];
  days: AdminAnalyticsChartDay[];
}

const VI_WEEKDAY_SHORT = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"] as const;

export function formatAdminLatency(ms: number | null | undefined): string | null {
  if (ms === null || ms === undefined || !Number.isFinite(ms) || ms < 0) {
    return null;
  }
  if (ms >= 1000) {
    return `${(ms / 1000).toLocaleString("vi-VN", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    })} giây`;
  }
  return `${Math.round(ms).toLocaleString("vi-VN")} ms`;
}

function computeNiceHalfTick(peakBarValue: number): number {
  const padded = Math.max(2, Math.ceil(peakBarValue * 1.1));
  const rawHalf = Math.max(1, Math.ceil(padded / 2));
  if (rawHalf <= 6) return rawHalf;
  const exp = Math.pow(10, Math.floor(Math.log10(rawHalf)));
  const norm = rawHalf / exp;
  const steps = [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];
  const chosen = steps.find((s) => s >= norm) ?? 10;
  return Math.max(1, Math.round(chosen * exp));
}

function parseIsoUtcParts(dateIso: string): { year: number; month: number; day: number } | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateIso.trim());
  if (!m) return null;
  return { year: Number(m[1]), month: Number(m[2]), day: Number(m[3]) };
}

function formatIsoDayMeta(dateIso: string, fallbackLabel?: string) {
  const parts = parseIsoUtcParts(dateIso);
  if (!parts) {
    return {
      weekdayShort: "",
      shortDate: fallbackLabel ?? dateIso,
      dateLabel: fallbackLabel ?? dateIso,
      xAxisLabel: fallbackLabel ?? dateIso,
    };
  }
  const utc = new Date(Date.UTC(parts.year, parts.month - 1, parts.day));
  const weekdayShort = VI_WEEKDAY_SHORT[utc.getUTCDay()] ?? "";
  const dd = String(parts.day).padStart(2, "0");
  const mm = String(parts.month).padStart(2, "0");
  const shortDate = `${dd}/${mm}`;
  const dateLabel = fallbackLabel || `${dd}/${mm}/${parts.year}`;
  return {
    weekdayShort,
    shortDate,
    dateLabel,
    xAxisLabel: weekdayShort ? `${weekdayShort} (${shortDate})` : shortDate,
  };
}

export function buildAdminAnalyticsChartModel(
  dailyBreakdown: AdminDailyTelemetryItem[],
  analyses7d: number,
): AdminAnalyticsChartModel {
  const sorted = [...dailyBreakdown].sort((a, b) => a.dateIso.localeCompare(b.dateIso));
  let normalizedSeven: AdminDailyTelemetryItem[] = [];

  if (sorted.length >= 7) {
    normalizedSeven = sorted.slice(-7);
  } else if (sorted.length > 0) {
    const byIso = new Map(sorted.map((item) => [item.dateIso, item]));
    const latestParts = parseIsoUtcParts(sorted[sorted.length - 1].dateIso);
    if (latestParts) {
      const anchorMs = Date.UTC(latestParts.year, latestParts.month - 1, latestParts.day);
      for (let offset = 6; offset >= 0; offset -= 1) {
        const dt = new Date(anchorMs - offset * 86_400_000);
        const yyyy = dt.getUTCFullYear();
        const mm = String(dt.getUTCMonth() + 1).padStart(2, "0");
        const dd = String(dt.getUTCDate()).padStart(2, "0");
        const iso = `${yyyy}-${mm}-${dd}`;
        const existing = byIso.get(iso);
        normalizedSeven.push(
          existing ?? {
            dateIso: iso,
            dateLabel: `${dd}/${mm}/${yyyy}`,
            totalRequests: 0,
            succeededRequests: 0,
            refusedRequests: 0,
            failedRequests: 0,
            avgLatencyMs: null,
            tokensMeasured: false,
            inputTokens: null,
            outputTokens: null,
            thoughtsTokens: null,
            totalTokens: null,
          },
        );
      }
    } else {
      normalizedSeven = sorted;
    }
  }

  const totalFromDays = normalizedSeven.reduce((acc, d) => acc + d.totalRequests, 0);
  const hasActivity = analyses7d > 0 || totalFromDays > 0;
  const peakBarValue = normalizedSeven.reduce(
    (acc, d) => Math.max(acc, d.succeededRequests, d.refusedRequests),
    0,
  );
  const midTick = hasActivity ? computeNiceHalfTick(peakBarValue) : 2;
  const maxTick = midTick * 2;

  const days: AdminAnalyticsChartDay[] = normalizedSeven.map((d) => {
    const meta = formatIsoDayMeta(d.dateIso, d.dateLabel);
    const succeededHeightPct =
      d.succeededRequests > 0
        ? Math.min(100, Number(((d.succeededRequests / maxTick) * 100).toFixed(2)))
        : 0;
    const refusedHeightPct =
      d.refusedRequests > 0
        ? Math.min(100, Number(((d.refusedRequests / maxTick) * 100).toFixed(2)))
        : 0;
    const failedSuffix =
      d.failedRequests > 0
        ? `, ${d.failedRequests.toLocaleString("vi-VN")} lỗi xử lý`
        : "";
    const ariaLabel = `Ngày ${meta.dateLabel}: Tổng ${d.totalRequests.toLocaleString("vi-VN")} yêu cầu, ${d.succeededRequests.toLocaleString("vi-VN")} xử lý thành công, ${d.refusedRequests.toLocaleString("vi-VN")} từ chối an toàn${failedSuffix}`;
    return {
      ...d,
      dateLabel: meta.dateLabel,
      weekdayShort: meta.weekdayShort,
      shortDate: meta.shortDate,
      xAxisLabel: meta.xAxisLabel,
      succeededHeightPct,
      refusedHeightPct,
      ariaLabel,
    };
  });

  return {
    hasActivity,
    maxTick,
    midTick,
    yTicks: [maxTick, midTick, 0],
    days,
  };
}

export type AdminPaginationItem =
  | { type: "page"; page: number }
  | { type: "ellipsis"; key: string };

export function computeAdminPagination(
  totalItems: number,
  pageSize: number,
  currentPage: number,
) {
  const safeTotalItems = Math.max(0, Math.floor(totalItems));
  const safePageSize = Math.max(1, Math.floor(pageSize));
  const totalPages = Math.max(1, Math.ceil(safeTotalItems / safePageSize));
  const safePage = Math.min(Math.max(1, Math.floor(currentPage)), totalPages);
  const startIndex = safeTotalItems === 0 ? 0 : (safePage - 1) * safePageSize;
  const endIndex =
    safeTotalItems === 0 ? 0 : Math.min(safeTotalItems, startIndex + safePageSize);
  return {
    totalItems: safeTotalItems,
    pageSize: safePageSize,
    totalPages,
    safePage,
    startIndex,
    endIndex,
    hasMultiplePages: totalPages > 1,
  };
}

export function buildAdminPaginationItems(
  totalPages: number,
  currentPage: number,
): AdminPaginationItem[] {
  const safeTotal = Math.max(1, Math.floor(totalPages));
  if (safeTotal <= 1) return [];
  const safePage = Math.min(Math.max(1, Math.floor(currentPage)), safeTotal);
  if (safeTotal <= 7) {
    return Array.from({ length: safeTotal }, (_, i) => ({ type: "page", page: i + 1 }));
  }
  const anchors = new Set<number>([1, safeTotal, safePage - 1, safePage, safePage + 1]);
  if (safePage <= 2) {
    anchors.add(2);
    anchors.add(3);
  } else if (safePage >= safeTotal - 1) {
    anchors.add(safeTotal - 2);
    anchors.add(safeTotal - 1);
  }
  const sorted = [...anchors]
    .filter((p) => p >= 1 && p <= safeTotal)
    .sort((a, b) => a - b);
  const items: AdminPaginationItem[] = [];
  for (let i = 0; i < sorted.length; i++) {
    const p = sorted[i];
    if (i > 0) {
      const prev = sorted[i - 1];
      if (p - prev === 2) {
        items.push({ type: "page", page: prev + 1 });
      } else if (p - prev > 2) {
        items.push({ type: "ellipsis", key: `ellipsis-${prev}-${p}` });
      }
    }
    items.push({ type: "page", page: p });
  }
  return items;
}

export function AdminAccountsPaginationBar({
  totalItems,
  pageSize,
  currentPage,
  pageSizeOpen,
  onTogglePageSize,
  onSelectPageSize,
  onPageChange,
}: {
  totalItems: number;
  pageSize: number;
  currentPage: number;
  pageSizeOpen: boolean;
  onTogglePageSize: (e: React.MouseEvent<HTMLButtonElement>) => void;
  onSelectPageSize: (size: number) => void;
  onPageChange: (page: number) => void;
}) {
  const {
    totalPages,
    safePage,
    startIndex,
    endIndex,
    hasMultiplePages,
  } = computeAdminPagination(totalItems, pageSize, currentPage);
  const navItems = buildAdminPaginationItems(totalPages, safePage);

  return (
    <div className="admin-pagination-bar" id="admin-accounts-pagination">
      <div className="admin-pagination-info" id="admin-pagination-summary">
        {totalItems === 0 ? (
          "Hiển thị 0 tài khoản"
        ) : (
          <>
            Hiển thị <strong>{startIndex + 1}–{endIndex}</strong> trong tổng số{" "}
            <strong>{totalItems}</strong> tài khoản
            {hasMultiplePages ? (
              <>
                {" · Trang "}
                <strong>
                  {safePage}/{totalPages}
                </strong>
              </>
            ) : null}
          </>
        )}
      </div>
      <div className="admin-pagination-controls">
        <div className="admin-page-size-wrap" id="admin-page-size-wrap">
          <span className="admin-page-size-label" id="admin-page-size-label">
            Số dòng mỗi trang:
          </span>
          <div
            className={`admin-page-size-dropdown${pageSizeOpen ? " open" : ""}`}
            id="admin-page-size-dropdown"
          >
            <button
              type="button"
              id="admin-page-size-select"
              className={`admin-page-size-select admin-page-size-trigger${pageSizeOpen ? " is-open" : ""}`}
              aria-haspopup="listbox"
              aria-expanded={pageSizeOpen}
              aria-labelledby="admin-page-size-label admin-page-size-value"
              aria-controls="admin-page-size-listbox"
              onClick={onTogglePageSize}
            >
              <span className="admin-page-size-value" id="admin-page-size-value">
                {pageSize} / trang
              </span>
              <svg className="admin-page-size-caret" viewBox="0 0 24 24" aria-hidden="true">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
            <div
              id="admin-page-size-listbox"
              className={`admin-page-size-listbox${pageSizeOpen ? " open" : ""}`}
              role="listbox"
              aria-labelledby="admin-page-size-label"
              tabIndex={-1}
              onClick={(e) => e.stopPropagation()}
            >
              {[10, 20, 50].map((sz) => (
                <button
                  key={sz}
                  type="button"
                  role="option"
                  id={`admin-page-size-opt-${sz}`}
                  className={`admin-page-size-option${pageSize === sz ? " is-selected active" : ""}`}
                  data-page-size-opt={sz}
                  aria-selected={pageSize === sz}
                  onClick={() => onSelectPageSize(sz)}
                >
                  <span className="opt-label">{sz} / trang</span>
                  <svg className="opt-check-svg" viewBox="0 0 24 24" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </button>
              ))}
            </div>
          </div>
        </div>

        {hasMultiplePages && (
          <div
            className="admin-page-nav-group"
            id="admin-page-nav-group"
            role="navigation"
            aria-label="Phân trang danh sách tài khoản"
          >
            <button
              type="button"
              className="btn-page-nav"
              id="btn-page-prev"
              disabled={safePage <= 1}
              aria-label="Trang trước"
              onClick={() => onPageChange(Math.max(1, safePage - 1))}
            >
              <svg className="page-nav-ico" viewBox="0 0 24 24" aria-hidden="true">
                <polyline points="15 18 9 12 15 6" />
              </svg>
              <span>Trước</span>
            </button>
            {navItems.map((item) =>
              item.type === "ellipsis" ? (
                <span key={item.key} className="admin-page-ellipsis" aria-hidden="true">
                  …
                </span>
              ) : (
                <button
                  key={item.page}
                  type="button"
                  className={`btn-page-nav is-page-num${item.page === safePage ? " is-current" : ""}`}
                  data-page-num={item.page}
                  aria-label={`Trang ${item.page}`}
                  aria-current={item.page === safePage ? "page" : undefined}
                  onClick={() => onPageChange(item.page)}
                >
                  {item.page}
                </button>
              ),
            )}
            <button
              type="button"
              className="btn-page-nav"
              id="btn-page-next"
              disabled={safePage >= totalPages}
              aria-label="Trang sau"
              onClick={() => onPageChange(Math.min(totalPages, safePage + 1))}
            >
              <span>Sau</span>
              <svg className="page-nav-ico" viewBox="0 0 24 24" aria-hidden="true">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export function AdminWorkspaceView({
  initialTab = "overview",
  initialOverviewFixture,
  initialUsersFixture,
}: {
  initialTab?: "overview" | "accounts" | "analytics" | "audit";
  initialOverviewFixture?: AdminOverviewStatsFixture;
  initialUsersFixture?: AdminUserItem[];
} = {}) {
  const user = useAuthStore((s) => s.user);
  const resolved = useAuthStore((s) => s.resolved);
  const logout = useAuthStore((s) => s.logout);
  const goHome = useAppStore((s) => s.goHome);
  const setView = useAppStore((s) => s.setView);
  const openAccountModal = useAppStore((s) => s.openAccountModal);

  const [adminTab, setAdminTab] = useState<"overview" | "accounts" | "analytics" | "audit">(
    initialTab,
  );
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const [notifOpen, setNotifOpen] = useState(false);
  const [accMenuOpen, setAccMenuOpen] = useState(false);
  const [addAccMenuOpen, setAddAccMenuOpen] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const [pageSizeOpen, setPageSizeOpen] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<"all" | "student" | "teacher" | "admin">("all");
  const [statusFilter, setStatusFilter] = useState<
    "all" | "active" | "pending_teacher" | "pending_activation" | "locked"
  >("all");
  const [pageSize, setPageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);

  const [sortState, setSortState] = useState<{ field: string; dir: "asc" | "desc" }>({
    field: "joinedTs",
    dir: "desc",
  });
  const [pendingSort, setPendingSort] = useState<{ field: string; dir: "asc" | "desc" }>({
    field: "joinedTs",
    dir: "asc",
  });
  const [auditSort, setAuditSort] = useState<{ field: string; dir: "asc" | "desc" }>({
    field: "timeTs",
    dir: "desc",
  });
  const [analyticsSort, setAnalyticsSort] = useState<{ field: string; dir: "asc" | "desc" }>({
    field: "dateIso",
    dir: "desc",
  });
  const [activeChartDayIso, setActiveChartDayIso] = useState<string | null>(null);

  const [users, setUsers] = useState<AdminUserItem[]>(() => initialUsersFixture ?? []);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLogItem[]>([]);
  const [overviewStats, setOverviewStats] = useState<{
    configuredModelId: string | null;
    totalAnalyses: number;
    analysesToday: number;
    analyses7d: number;
    aiRequestsToday: number;
    succeededRequests: number;
    refusedRequests: number;
    failedRequests: number;
    succeeded7d: number;
    refused7d: number;
    failed7d: number;
    avgLatencyMs: number | null;
    avgLatency7dMs: number | null;
    totalHistoryEntries: number;
    totalClasses: number;
    totalSessions: number;
    tokensMeasured: boolean;
    tokensToday: number | null;
    inputTokens7d: number | null;
    outputTokens7d: number | null;
    thoughtsTokens7d: number | null;
    totalTokens7d: number | null;
    aiServiceConfigured: boolean | null;
    cachedProblems: number;
    dailyBreakdown: Array<{
      dateIso: string;
      dateLabel: string;
      totalRequests: number;
      succeededRequests: number;
      refusedRequests: number;
      failedRequests: number;
      avgLatencyMs: number | null;
      tokensMeasured: boolean;
      inputTokens: number | null;
      outputTokens: number | null;
      thoughtsTokens: number | null;
      totalTokens: number | null;
    }>;
    roleQuotaSummary: {
      student: { count: number; usedToday: number; dailyLimitDefault: number };
      teacher: { count: number; usedToday: number; dailyLimitDefault: number };
      admin: { count: number; usedToday: number; dailyLimitDefault: number };
    } | null;
  }>(() => ({
    configuredModelId: null,
    totalAnalyses: 0,
    analysesToday: 0,
    analyses7d: 0,
    aiRequestsToday: 0,
    succeededRequests: 0,
    refusedRequests: 0,
    failedRequests: 0,
    succeeded7d: 0,
    refused7d: 0,
    failed7d: 0,
    avgLatencyMs: null,
    avgLatency7dMs: null,
    totalHistoryEntries: 0,
    totalClasses: 0,
    totalSessions: 0,
    tokensMeasured: false,
    tokensToday: null,
    inputTokens7d: null,
    outputTokens7d: null,
    thoughtsTokens7d: null,
    totalTokens7d: null,
    aiServiceConfigured: null,
    cachedProblems: 0,
    dailyBreakdown: [],
    roleQuotaSummary: null,
    ...initialOverviewFixture,
  }));

  const [quotaConfig, setQuotaConfig] = useState({
    studentDailyRequests: 15,
    teacherDailyRequests: 80,
    studentDailyTokens: 45000,
    teacherDailyTokens: 240000,
    studentRatePerMin: 4,
    teacherRatePerMin: 10,
    vndBudgetRaw: "",
    autoCutoffEnabled: true,
    allowNewRegistrations: true,
    maintenanceMode: false,
  });

  const [quotaDraft, setQuotaDraft] = useState(quotaConfig);
  const [autoCutoffMenuOpen, setAutoCutoffMenuOpen] = useState(false);
  const [sysDiscardConfirmOpen, setSysDiscardConfirmOpen] = useState(false);

  const [dotsMenu, setDotsMenu] = useState<{
    userId: number | string;
    left: number;
    top: number;
    flippedUp: boolean;
  } | null>(null);

  const [detailUser, setDetailUser] = useState<AdminUserItem | null>(null);
  const [quotaModalUser, setQuotaModalUser] = useState<AdminUserItem | null>(null);
  const [quotaInputVal, setQuotaInputVal] = useState("5");

  const [confirmAction, setConfirmAction] = useState<{
    type: "grant_teacher" | "revert_student" | "lock" | "unlock" | "delete_account" | "reset_password";
    user: AdminUserItem;
  } | null>(null);

  const [createUserOpen, setCreateUserOpen] = useState(false);
  const [newUserName, setNewUserName] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserSchool, setNewUserSchool] = useState("");
  const [newUserNote, setNewUserNote] = useState("");
  const [createUserErr, setCreateUserErr] = useState("");

  const [bulkImportOpen, setBulkImportOpen] = useState(false);
  const [bulkStep, setBulkStep] = useState<1 | 2 | 3 | 4 | "result">(1);
  const [bulkFileName, setBulkFileName] = useState("");
  const [bulkFileSize, setBulkFileSize] = useState("");
  const [bulkFileExt, setBulkFileExt] = useState("");
  const [bulkRows, setBulkRows] = useState<BulkImportRowItem[]>([]);
  const [bulkFilter, setBulkFilter] = useState<"all" | "valid" | "error">("all");
  const [bulkPreviewPage, setBulkPreviewPage] = useState(1);
  const [bulkErrorMsg, setBulkErrorMsg] = useState("");
  const [bulkStep4Error, setBulkStep4Error] = useState("");
  const [bulkDragOver, setBulkDragOver] = useState(false);
  const bulkFileInputRef = useRef<HTMLInputElement | null>(null);
  const previewTableRef = useRef<HTMLDivElement | null>(null);
  const [bulkResult, setBulkResult] = useState<{
    totalRecords: number;
    createdCount: number;
    errorCount: number;
    operatedAt: string;
  } | null>(null);

  const [sysSettingsOpen, setSysSettingsOpen] = useState(false);
  const [sysSettingsTab, setSysSettingsTab] = useState<"quotas" | "service">("quotas");
  const [actionToast, setActionToast] = useState("");
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToastMsg = useCallback((msg: string) => {
    setActionToast(msg);
    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current);
    }
    toastTimerRef.current = setTimeout(() => {
      setActionToast("");
      toastTimerRef.current = null;
    }, 4500);
  }, []);

  const fetchAdminUsers = useCallback(async () => {
    if (!user || user.role !== "admin") return;
    try {
      const r = await fetch("/api/admin/overview", { credentials: "include" });
      if (!r.ok) return;
      const body = (await r.json()) as {
        users?: Array<{
          id: number;
          email: string;
          displayName: string;
          role: "student" | "teacher" | "admin";
          status?:
            | "active"
            | "verified"
            | "pending_teacher"
            | "pending_activation"
            | "locked"
            | "suspended";
          mustChangePassword: boolean;
          isSuspended?: boolean;
          school?: string;
          workplace?: string;
          adminNote?: string;
          passwordResetRequestedAt?: string;
          dailyLimit?: number;
          tokenCap?: number;
          usedToday?: number;
          tokensToday?: string;
          createdAt: string;
        }>;
        stats?: {
          configuredModelId?: string | null;
          totalAnalyses?: number;
          analysesToday?: number;
          analyses7d?: number;
          aiRequestsToday?: number;
          succeededRequests?: number;
          refusedRequests?: number;
          failedRequests?: number;
          succeeded7d?: number;
          refused7d?: number;
          failed7d?: number;
          avgLatencyMs?: number | null;
          avgLatency7dMs?: number | null;
          totalHistoryEntries?: number;
          totalClasses?: number;
          totalSessions?: number;
          tokensMeasured?: boolean;
          tokensToday?: number | null;
          inputTokens7d?: number | null;
          outputTokens7d?: number | null;
          thoughtsTokens7d?: number | null;
          totalTokens7d?: number | null;
          aiServiceConfigured?: boolean;
          cachedProblems?: number;
          dailyBreakdown?: Array<{
            dateIso: string;
            dateLabel: string;
            totalRequests: number;
            succeededRequests: number;
            refusedRequests: number;
            failedRequests: number;
            avgLatencyMs: number | null;
            tokensMeasured: boolean;
            inputTokens: number | null;
            outputTokens: number | null;
            thoughtsTokens: number | null;
            totalTokens: number | null;
          }>;
          roleQuotaSummary?: {
            student: { count: number; usedToday: number; dailyLimitDefault: number };
            teacher: { count: number; usedToday: number; dailyLimitDefault: number };
            admin: { count: number; usedToday: number; dailyLimitDefault: number };
          } | null;
        };
        settings?: Record<string, unknown>;
        auditLogs?: Array<{
          id: string;
          time?: string;
          timestamp?: string;
          timeTs?: number;
          actor: string;
          action: string;
          target: string;
          detail: string;
        }>;
      };
      if (body.stats) {
        const st = body.stats;
        setOverviewStats({
          configuredModelId:
            typeof st.configuredModelId === "string" && st.configuredModelId.trim()
              ? st.configuredModelId.trim()
              : null,
          totalAnalyses: Number(st.totalAnalyses) || 0,
          analysesToday: Number(st.analysesToday ?? st.aiRequestsToday) || 0,
          analyses7d: Number(st.analyses7d) || 0,
          aiRequestsToday: Number(st.aiRequestsToday) || 0,
          succeededRequests: Number(st.succeededRequests) || 0,
          refusedRequests: Number(st.refusedRequests) || 0,
          failedRequests: Number(st.failedRequests) || 0,
          succeeded7d: Number(st.succeeded7d) || 0,
          refused7d: Number(st.refused7d) || 0,
          failed7d: Number(st.failed7d) || 0,
          avgLatencyMs: typeof st.avgLatencyMs === "number" ? st.avgLatencyMs : null,
          avgLatency7dMs: typeof st.avgLatency7dMs === "number" ? st.avgLatency7dMs : null,
          totalHistoryEntries: Number(st.totalHistoryEntries) || 0,
          totalClasses: Number(st.totalClasses) || 0,
          totalSessions: Number(st.totalSessions) || 0,
          tokensMeasured: Boolean(st.tokensMeasured),
          tokensToday: typeof st.tokensToday === "number" ? st.tokensToday : null,
          inputTokens7d: typeof st.inputTokens7d === "number" ? st.inputTokens7d : null,
          outputTokens7d: typeof st.outputTokens7d === "number" ? st.outputTokens7d : null,
          thoughtsTokens7d: typeof st.thoughtsTokens7d === "number" ? st.thoughtsTokens7d : null,
          totalTokens7d: typeof st.totalTokens7d === "number" ? st.totalTokens7d : null,
          aiServiceConfigured:
            typeof st.aiServiceConfigured === "boolean" ? st.aiServiceConfigured : null,
          cachedProblems: Number(st.cachedProblems) || 0,
          dailyBreakdown: Array.isArray(st.dailyBreakdown) ? st.dailyBreakdown : [],
          roleQuotaSummary: st.roleQuotaSummary ?? null,
        });
      }
      if (body.settings && typeof body.settings === "object") {
        const s = body.settings;
        const monthlyNum = Number(s.monthlyBudgetVnd) || 0;
        const budgetRaw =
          typeof s.vndBudgetRaw === "string"
            ? s.vndBudgetRaw
            : monthlyNum > 0
              ? monthlyNum.toLocaleString("vi-VN")
              : "";
        const nextCfg = {
          studentDailyRequests:
            Number(s.studentDailyRequests ?? s.studentDailyLimit ?? s.defaultStudentQuota) || 15,
          teacherDailyRequests:
            Number(s.teacherDailyRequests ?? s.teacherDailyLimit ?? s.defaultTeacherQuota) || 80,
          studentDailyTokens:
            Number(s.studentDailyTokens ?? s.studentTokenLimit) || 45000,
          teacherDailyTokens:
            Number(s.teacherDailyTokens ?? s.teacherTokenLimit) || 240000,
          studentRatePerMin:
            Number(s.studentRatePerMin ?? s.studentRpmLimit) || 4,
          teacherRatePerMin:
            Number(s.teacherRatePerMin ?? s.teacherRpmLimit) || 10,
          vndBudgetRaw: budgetRaw,
          autoCutoffEnabled: s.autoCutoffEnabled !== false,
          allowNewRegistrations: s.allowNewRegistrations !== false,
          maintenanceMode: Boolean(s.maintenanceMode),
        };
        setQuotaConfig(nextCfg);
        setQuotaDraft(nextCfg);
      }
      if (Array.isArray(body.auditLogs)) {
        const totalLogs = body.auditLogs.length;
        setAuditLogs(
          body.auditLogs.map((item, idx) => ({
            id: item.id,
            time: item.time || item.timestamp || "",
            timestamp: item.timestamp,
            timeTs:
              typeof item.timeTs === "number" && item.timeTs > 0
                ? item.timeTs
                : Date.now() * 1000 + (totalLogs - idx),
            actor: item.actor,
            action: item.action,
            target: item.target,
            detail: item.detail,
          })),
        );
      }
      if (body.users) {
        setUsers(
          body.users.map((u) => {
            const dLimit =
              typeof u.dailyLimit === "number" && u.dailyLimit > 0
                ? u.dailyLimit
                : u.role === "admin"
                  ? 500
                  : u.role === "teacher"
                    ? 80
                    : 15;
            const tCap =
              typeof u.tokenCap === "number" && u.tokenCap > 0
                ? u.tokenCap
                : u.role === "admin"
                  ? 500000
                  : u.role === "teacher"
                    ? 240000
                    : 45000;
            const dt = u.createdAt ? new Date(u.createdAt) : new Date();
            const joinedStr = Number.isNaN(dt.getTime())
              ? new Date().toLocaleDateString("vi-VN")
              : dt.toLocaleDateString("vi-VN");
            const normalizedStatus = u.status === "suspended" ? "locked" : u.status;
            const resolvedStatus =
              normalizedStatus ??
              (u.isSuspended
                ? "locked"
                : u.mustChangePassword
                  ? "pending_activation"
                  : u.role === "teacher"
                    ? "verified"
                    : "active");
            return {
              id: u.id,
              name: u.displayName,
              email: u.email,
              role: u.role,
              status: resolvedStatus,
              school: (u.school || u.workplace || "").trim() || "Chưa cập nhật đơn vị",
              adminNote: u.adminNote || "",
              passwordResetRequestedAt: u.passwordResetRequestedAt || undefined,
              joinedAt: joinedStr,
              joinedTs: Number.isNaN(dt.getTime()) ? Date.now() : dt.getTime(),
              dailyLimit: dLimit,
              tokenCap: tCap,
              usedToday: Number(u.usedToday) || 0,
              tokensToday: u.tokensToday || "Chưa đo token",
            };
          }),
        );
      }
    } catch {
      /* ignore network errors in offline tests */
    }
  }, [user]);

  useEffect(() => {
    void fetchAdminUsers();
  }, [fetchAdminUsers]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setDotsMenu(null);
        setNotifOpen(false);
        setAccMenuOpen(false);
        setAddAccMenuOpen(false);
        setFilterOpen(false);
        setPageSizeOpen(false);
        setAutoCutoffMenuOpen(false);
        setDetailUser(null);
        setQuotaModalUser(null);
        setConfirmAction(null);
        setCreateUserOpen(false);
        setBulkImportOpen(false);
        setSysSettingsOpen(false);
        setSysDiscardConfirmOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const totalUsersCount = users.length;
  const studentCount = users.filter((u) => u.role === "student").length;
  const teacherVerifiedCount = users.filter((u) => u.role === "teacher").length;
  const adminCount = users.filter((u) => u.role === "admin").length;
  const activeCount = users.filter((u) => u.status === "active" || u.status === "verified").length;
  const pendingTeachers = users.filter((u) => u.status === "pending_teacher");
  const pendingActivationCount = users.filter((u) => u.status === "pending_activation").length;
  const lockedCount = users.filter((u) => u.status === "locked").length;
  const totalUsedToday = users.reduce((sum, u) => sum + (Number(u.usedToday) || 0), 0);

  const ROLE_SORT_RANK: Record<string, number> = {
    student: 1,
    teacher: 2,
    admin: 3,
  };
  const STATUS_SORT_RANK: Record<string, number> = {
    active: 1,
    verified: 2,
    pending_teacher: 3,
    pending_activation: 4,
    locked: 5,
  };

  const filteredUsers = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return users
      .filter((u) => {
        const matchRole = roleFilter === "all" || u.role === roleFilter;
        const matchStatus =
          statusFilter === "all" ||
          (statusFilter === "active" && (u.status === "active" || u.status === "verified")) ||
          (statusFilter === "pending_teacher" && u.status === "pending_teacher") ||
          (statusFilter === "pending_activation" && u.status === "pending_activation") ||
          (statusFilter === "locked" && u.status === "locked");
        const matchQ =
          !q ||
          u.name.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q) ||
          u.school.toLowerCase().includes(q);
        return matchRole && matchStatus && matchQ;
      })
      .sort((a, b) => {
        const dirMul = sortState.dir === "asc" ? 1 : -1;
        let cmp = 0;
        if (sortState.field === "name") {
          cmp = a.name.localeCompare(b.name, "vi") * dirMul;
        } else if (sortState.field === "roleOrder") {
          cmp = ((ROLE_SORT_RANK[a.role] ?? 9) - (ROLE_SORT_RANK[b.role] ?? 9)) * dirMul;
        } else if (sortState.field === "statusOrder") {
          cmp = ((STATUS_SORT_RANK[a.status] ?? 9) - (STATUS_SORT_RANK[b.status] ?? 9)) * dirMul;
        } else if (sortState.field === "dailyLimit") {
          cmp = (a.dailyLimit - b.dailyLimit) * dirMul;
        } else if (sortState.field === "usedToday") {
          cmp = (a.usedToday - b.usedToday) * dirMul;
        } else {
          cmp = (a.joinedTs - b.joinedTs) * dirMul;
        }
        if (cmp !== 0) return cmp;
        return Number(b.id) - Number(a.id);
      });
  }, [users, searchQuery, roleFilter, statusFilter, sortState]);

  const sortedPendingTeachers = useMemo(() => {
    const dirMul = pendingSort.dir === "asc" ? 1 : -1;
    return [...pendingTeachers].sort((a, b) => {
      let cmp = 0;
      if (pendingSort.field === "name") {
        cmp = a.name.localeCompare(b.name, "vi") * dirMul;
      } else if (pendingSort.field === "school") {
        cmp = a.school.localeCompare(b.school, "vi") * dirMul;
      } else if (pendingSort.field === "statusOrder") {
        cmp = ((STATUS_SORT_RANK[a.status] ?? 9) - (STATUS_SORT_RANK[b.status] ?? 9)) * dirMul;
      } else {
        cmp = (a.joinedTs - b.joinedTs) * dirMul;
      }
      if (cmp !== 0) return cmp;
      return Number(a.id) - Number(b.id);
    });
  }, [pendingTeachers, pendingSort]);

  const sortedAuditLogs = useMemo(() => {
    const dirMul = auditSort.dir === "asc" ? 1 : -1;
    return [...auditLogs].sort((a, b) => {
      let cmp = 0;
      if (auditSort.field === "actor") {
        cmp = a.actor.localeCompare(b.actor, "vi") * dirMul;
      } else if (auditSort.field === "action") {
        cmp = a.action.localeCompare(b.action, "vi") * dirMul;
      } else if (auditSort.field === "target") {
        cmp = a.target.localeCompare(b.target, "vi") * dirMul;
      } else {
        cmp = ((a.timeTs ?? 0) - (b.timeTs ?? 0)) * dirMul;
      }
      if (cmp !== 0) return cmp;
      return a.id.localeCompare(b.id);
    });
  }, [auditLogs, auditSort]);

  const analyticsChartModel = useMemo(
    () => buildAdminAnalyticsChartModel(overviewStats.dailyBreakdown, overviewStats.analyses7d),
    [overviewStats.dailyBreakdown, overviewStats.analyses7d],
  );

  const sortedAnalyticsDays = useMemo(() => {
    const dirMul = analyticsSort.dir === "asc" ? 1 : -1;
    return [...analyticsChartModel.days].sort((a, b) => {
      let cmp = 0;
      if (analyticsSort.field === "totalRequests") {
        cmp = (a.totalRequests - b.totalRequests) * dirMul;
      } else if (analyticsSort.field === "totalTokens") {
        const tokA = a.tokensMeasured && a.totalTokens !== null ? a.totalTokens : -1;
        const tokB = b.tokensMeasured && b.totalTokens !== null ? b.totalTokens : -1;
        cmp = (tokA - tokB) * dirMul;
      } else if (analyticsSort.field === "avgLatencyMs") {
        cmp = ((a.avgLatencyMs ?? -1) - (b.avgLatencyMs ?? -1)) * dirMul;
      } else {
        cmp = a.dateIso.localeCompare(b.dateIso) * dirMul;
      }
      if (cmp !== 0) return cmp;
      return b.dateIso.localeCompare(a.dateIso);
    });
  }, [analyticsChartModel.days, analyticsSort]);

  const activeFilterCount = (roleFilter !== "all" ? 1 : 0) + (statusFilter !== "all" ? 1 : 0);
  const {
    totalItems: totalFiltered,
    safePage,
    startIndex,
  } = computeAdminPagination(filteredUsers.length, pageSize, currentPage);
  const pageItems = filteredUsers.slice(startIndex, startIndex + pageSize);

  useEffect(() => {
    if (currentPage !== safePage) {
      setCurrentPage(safePage);
    }
  }, [currentPage, safePage]);

  const toggleSort = (field: string, defaultDir: "asc" | "desc" = "asc") => {
    setSortState((prev) =>
      prev.field === field
        ? { field, dir: prev.dir === "asc" ? "desc" : "asc" }
        : { field, dir: defaultDir },
    );
  };

  const togglePendingSort = (field: string, defaultDir: "asc" | "desc" = "asc") => {
    setPendingSort((prev) =>
      prev.field === field
        ? { field, dir: prev.dir === "asc" ? "desc" : "asc" }
        : { field, dir: defaultDir },
    );
  };

  const toggleAuditSort = (field: string, defaultDir: "asc" | "desc" = "asc") => {
    setAuditSort((prev) =>
      prev.field === field
        ? { field, dir: prev.dir === "asc" ? "desc" : "asc" }
        : { field, dir: defaultDir },
    );
  };

  const toggleAnalyticsSort = (field: string, defaultDir: "asc" | "desc" = "desc") => {
    setAnalyticsSort((prev) =>
      prev.field === field
        ? { field, dir: prev.dir === "asc" ? "desc" : "asc" }
        : { field, dir: defaultDir },
    );
  };

  const renderSortableTh = (
    label: string,
    field: string,
    defaultDir: "asc" | "desc",
    currentSort: { field: string; dir: "asc" | "desc" },
    onToggle: (f: string, d: "asc" | "desc") => void,
  ) => {
    const isSorted = currentSort.field === field;
    const ariaSort = isSorted
      ? currentSort.dir === "asc"
        ? "ascending"
        : "descending"
      : "none";
    const arrow = isSorted ? (currentSort.dir === "asc" ? "↑" : "↓") : "↕";
    return (
      <th className="is-sortable" aria-sort={ariaSort}>
        <button
          type="button"
          className={`th-sort-btn${isSorted ? " is-sorted" : ""}`}
          data-sort-field={field}
          onClick={() => onToggle(field, defaultDir)}
        >
          <span>{label}</span>
          <span className="sort-arrow" aria-hidden="true">
            {arrow}
          </span>
        </button>
      </th>
    );
  };

  const handleOpenDotsMenu = (u: AdminUserItem, e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    const rect = e.currentTarget.getBoundingClientRect();
    const menuWidth = 274;
    const menuHeight = 226;
    const left = Math.max(12, Math.min(window.innerWidth - menuWidth - 12, rect.right - menuWidth));
    let top = rect.bottom + 6;
    let flippedUp = false;
    if (top + menuHeight > window.innerHeight - 16 && rect.top - menuHeight - 6 >= 12) {
      top = rect.top - menuHeight - 6;
      flippedUp = true;
    }
    setDotsMenu((prev) =>
      prev && prev.userId === u.id ? null : { userId: u.id, left: Math.round(left), top: Math.round(top), flippedUp },
    );
  };

  const extractServerError = async (res: Response, fallback: string): Promise<string> => {
    try {
      const body = (await res.json()) as { detail?: unknown; error?: unknown };
      if (typeof body?.detail === "string" && body.detail.trim()) return body.detail;
      if (typeof body?.error === "string" && body.error.trim()) return body.error;
    } catch {
      /* ignore non-JSON body */
    }
    return fallback;
  };

  const handleExportCsv = async (endpoint: string, fallbackName: string) => {
    try {
      const r = await fetch(endpoint, { credentials: "include" });
      if (!r.ok) {
        const msg = await extractServerError(
          r,
          `Không thể xuất dữ liệu lúc này (HTTP ${r.status}).`,
        );
        showToastMsg(msg);
        return;
      }
      const disp = r.headers.get("content-disposition") || "";
      const fnMatch = disp.match(/filename="?([^";]+)"?/i);
      const filename = fnMatch?.[1]?.trim() || fallbackName;
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      await fetchAdminUsers();
      showToastMsg(`Đã tải xuống tệp ${filename}.`);
    } catch {
      showToastMsg("Không kết nối được máy chủ để xuất tệp CSV.");
    }
  };

  const handleExecuteConfirm = async () => {
    if (!confirmAction) return;
    const { type, user: targetUser } = confirmAction;
    const actorEmail = user?.email || "admin@axo.edu.vn";
    const nowStr =
      new Date().toLocaleDateString("vi-VN") +
      " · " +
      new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });

    if (type === "grant_teacher" || type === "revert_student") {
      const nextRole = type === "grant_teacher" ? "teacher" : "student";
      const nextStatus = nextRole === "teacher" ? "verified" : "active";
      let serverHandled = false;
      try {
        const r = await fetch(`/api/admin/users/${targetUser.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ role: nextRole, status: nextStatus }),
        });
        if (!r.ok) {
          const errMsg = await extractServerError(r, "Không thể cập nhật vai trò người dùng.");
          setConfirmAction(null);
          showToastMsg(errMsg);
          return;
        }
        serverHandled = true;
      } catch {
        /* fallback to local update in offline preview */
      }
      if (serverHandled) {
        await fetchAdminUsers();
      } else {
        setUsers((prev) =>
          prev.map((item) =>
            item.id === targetUser.id
              ? {
                  ...item,
                  role: nextRole,
                  status: nextRole === "teacher" ? "verified" : "active",
                  dailyLimit:
                    nextRole === "teacher"
                      ? quotaConfig.teacherDailyRequests
                      : quotaConfig.studentDailyRequests,
                }
              : item,
          ),
        );
        setAuditLogs((prev) => [
          {
            id: `aud-${Date.now()}`,
            time: nowStr,
            timeTs: Date.now(),
            actor: actorEmail,
            action: nextRole === "teacher" ? "Cấp quyền Giáo viên" : "Chuyển vai trò về Học sinh",
            target: targetUser.email,
            detail: `Cập nhật vai trò của ${targetUser.name} (${targetUser.email}) sang ${nextRole === "teacher" ? "Giáo viên" : "Học sinh"}.`,
          },
          ...prev,
        ]);
      }
      showToastMsg(
        nextRole === "teacher"
          ? `Đã cấp quyền Giáo viên cho ${targetUser.name} (${targetUser.email}).`
          : `Đã chuyển ${targetUser.name} (${targetUser.email}) về vai trò Học sinh.`,
      );
    } else if (type === "lock" || type === "unlock") {
      const isLock = type === "lock";
      const nextStatus = isLock ? "locked" : targetUser.role === "teacher" ? "verified" : "active";
      let serverHandled = false;
      try {
        const r = await fetch(`/api/admin/users/${targetUser.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ isSuspended: isLock }),
        });
        if (!r.ok) {
          const errMsg = await extractServerError(r, "Không thể thay đổi trạng thái khóa tài khoản.");
          setConfirmAction(null);
          showToastMsg(errMsg);
          return;
        }
        serverHandled = true;
      } catch {
        /* ignore in offline preview */
      }
      if (serverHandled) {
        await fetchAdminUsers();
      } else {
        setUsers((prev) =>
          prev.map((item) => (item.id === targetUser.id ? { ...item, status: nextStatus } : item)),
        );
        setAuditLogs((prev) => [
          {
            id: `aud-${Date.now()}`,
            time: nowStr,
            timeTs: Date.now(),
            actor: actorEmail,
            action: isLock ? "Khóa tạm thời tài khoản" : "Mở khóa tài khoản",
            target: targetUser.email,
            detail: `${isLock ? "Khóa tạm thời" : "Mở khóa"} tài khoản ${targetUser.name} (${targetUser.email}).`,
          },
          ...prev,
        ]);
      }
      showToastMsg(
        `${isLock ? "Đã khóa tạm thời" : "Đã mở khóa"} tài khoản ${targetUser.name}.`,
      );
    } else if (type === "delete_account") {
      let serverHandled = false;
      try {
        const r = await fetch(`/api/admin/users/${targetUser.id}`, {
          method: "DELETE",
          credentials: "include",
        });
        if (!r.ok) {
          const errMsg = await extractServerError(r, "Không thể xóa tài khoản này.");
          setConfirmAction(null);
          showToastMsg(errMsg);
          return;
        }
        serverHandled = true;
      } catch {
        /* ignore in offline preview */
      }
      if (serverHandled) {
        await fetchAdminUsers();
      } else {
        setUsers((prev) => prev.filter((item) => item.id !== targetUser.id));
        setAuditLogs((prev) => [
          {
            id: `aud-${Date.now()}`,
            time: nowStr,
            timeTs: Date.now(),
            actor: actorEmail,
            action: "Xóa tài khoản",
            target: targetUser.email,
            detail: `Đã xóa tài khoản ${targetUser.name} (${targetUser.email}).`,
          },
          ...prev,
        ]);
      }
      showToastMsg(`Đã xóa tài khoản ${targetUser.name} (${targetUser.email}).`);
    } else if (type === "reset_password") {
      let serverHandled = false;
      try {
        const r = await fetch(`/api/admin/users/${targetUser.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ mustChangePassword: true }),
        });
        if (!r.ok) {
          const errMsg = await extractServerError(r, "Không thể ghi nhận yêu cầu đặt lại mật khẩu.");
          setConfirmAction(null);
          showToastMsg(errMsg);
          return;
        }
        serverHandled = true;
      } catch {
        /* ignore in offline preview */
      }
      if (serverHandled) {
        await fetchAdminUsers();
      } else {
        setUsers((prev) =>
          prev.map((item) =>
            item.id === targetUser.id ? { ...item, passwordResetRequestedAt: nowStr } : item,
          ),
        );
        setAuditLogs((prev) => [
          {
            id: `aud-${Date.now()}`,
            time: nowStr,
            timeTs: Date.now(),
            actor: actorEmail,
            action: "Yêu cầu đặt lại mật khẩu",
            target: targetUser.email,
            detail: `Đã yêu cầu đặt lại mật khẩu cho ${targetUser.name} (${targetUser.email}).`,
          },
          ...prev,
        ]);
      }
      showToastMsg(`Đã ghi nhận yêu cầu đặt lại mật khẩu cho ${targetUser.name}.`);
    }

    setConfirmAction(null);
  };

  const handleCreateUserSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const nm = newUserName.trim();
    const em = newUserEmail.trim().toLowerCase();
    const sch = newUserSchool.trim();
    const note = newUserNote.trim();
    if (!nm) {
      setCreateUserErr("Vui lòng nhập họ và tên người dùng.");
      return;
    }
    if (!em || !em.includes("@")) {
      setCreateUserErr("Vui lòng nhập địa chỉ email hợp lệ.");
      return;
    }
    setCreateUserErr("");
    try {
      const r = await fetch("/api/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          displayName: nm,
          email: em,
          role: "student",
          school: sch,
          adminNote: note,
        }),
      });
      if (r.ok) {
        await fetchAdminUsers();
      } else {
        const msg = await extractServerError(r, "Không thể tạo tài khoản.");
        setCreateUserErr(msg);
        return;
      }
    } catch {
      /* fallback in offline preview */
      setUsers((prev) => [
        {
          id: `local-${Date.now()}`,
          name: nm,
          email: em,
          role: "student",
          status: "pending_activation",
          school: sch || "Chưa cập nhật đơn vị",
          adminNote: note,
          joinedAt: new Date().toLocaleDateString("vi-VN"),
          joinedTs: Date.now(),
          dailyLimit: quotaConfig.studentDailyRequests,
          tokenCap: quotaConfig.studentDailyTokens,
          usedToday: 0,
          tokensToday: `0 / ${quotaConfig.studentDailyTokens.toLocaleString("vi-VN")}`,
        },
        ...prev,
      ]);
    }
    setCreateUserOpen(false);
    setNewUserName("");
    setNewUserEmail("");
    setNewUserSchool("");
    setNewUserNote("");
    showToastMsg(`Đã tạo tài khoản ${nm} (${em}) · Trạng thái: Chờ kích hoạt.`);
  };

  const analyzeBulkInput = (
    rawList: Array<{ rowNum: number; name: string; email: string; school: string }>,
  ): BulkImportRowItem[] => {
    const existingEmails = new Set(users.map((u) => u.email.trim().toLowerCase()));
    const seen = new Map<string, number>();
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
    const formulaRe = /^[=+\-@\t\r]/;
    return rawList.map((r, idx) => {
      const rowNum = r.rowNum || idx + 1;
      const rawName = String(r.name ?? "");
      const rawEmail = String(r.email ?? "");
      const rawSchool = String(r.school ?? "");
      const name = rawName.trim();
      const email = rawEmail.trim();
      const school = rawSchool.trim();
      const lower = email.toLowerCase();
      let category = "valid";
      let reason = "";
      if (formulaRe.test(name) || formulaRe.test(email) || formulaRe.test(school)) {
        category = "other_invalid";
        reason = "Dòng không hợp lệ khác: Chứa ký tự công thức bảng tính không an toàn (=, +, -, @)";
      } else if (!name) {
        category = "missing_info";
        reason = "Thiếu thông tin: Chưa nhập Họ và tên";
      } else if (!email) {
        category = "missing_info";
        reason = "Thiếu thông tin: Chưa nhập địa chỉ Email";
      } else if (!school) {
        category = "missing_info";
        reason = "Thiếu thông tin: Chưa nhập Trường/Đơn vị";
      } else if (!emailRe.test(email)) {
        category = "invalid_email";
        reason = "Email sai định dạng";
      } else if (seen.has(lower)) {
        category = "duplicate_in_file";
        reason = `Email trùng trong tệp (trùng với dòng #${seen.get(lower)})`;
      } else if (existingEmails.has(lower)) {
        category = "existing_email";
        reason = "Email đã tồn tại trong danh sách tài khoản";
      }
      if (email && emailRe.test(email) && !seen.has(lower)) {
        seen.set(lower, rowNum);
      }
      return {
        rowNum,
        name: name || "(Trống)",
        rawName,
        email: email || "(Trống)",
        rawEmail,
        school: school || "(Trống)",
        rawSchool,
        isValid: category === "valid",
        category,
        reason,
      };
    });
  };

  const handleDownloadSampleCsv = () => {
    const csv = "Họ và tên,Email,Trường/Đơn vị\r\n";
    try {
      const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "axo-mau-nhap-tai-khoan.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      /* ignore in headless test */
    }
    showToastMsg("Đã tải tệp mẫu axo-mau-nhap-tai-khoan.csv (cấu trúc 3 cột chuẩn).");
  };

  const handleDownloadBulkErrorCsv = () => {
    const errRows = bulkRows.filter((r) => !r.isValid);
    if (errRows.length === 0) {
      showToastMsg("Không có dòng lỗi nào cần tải.");
      return;
    }
    const header = "Số dòng,Họ và tên,Email,Trường/Đơn vị,Lý do lỗi";
    const lines = errRows.map((r) => {
      const esc = (v: string) => `"${String(v ?? "").replace(/"/g, '""')}"`;
      return [r.rowNum, esc(r.rawName), esc(r.rawEmail), esc(r.rawSchool), esc(r.reason)].join(",");
    });
    const csv = [header, ...lines].join("\r\n");
    try {
      const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "axo-danh-sach-loi-nhap-tai-khoan.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      /* ignore in headless test */
    }
    showToastMsg(`Đã tải danh sách ${errRows.length} dòng lỗi (.csv).`);
  };

  const splitBulkCsvLine = (line: string): string[] => {
    const cells: string[] = [];
    let cur = "";
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        if (inQuotes && line[i + 1] === '"') {
          cur += '"';
          i++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (ch === "," && !inQuotes) {
        cells.push(cur);
        cur = "";
      } else {
        cur += ch;
      }
    }
    cells.push(cur);
    return cells;
  };

  const parseBulkCsvText = (
    text: string,
  ): {
    error: string;
    rows: Array<{ rowNum: number; name: string; email: string; school: string }>;
  } => {
    const clean = String(text ?? "")
      .replace(/^\uFEFF/, "")
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n");
    const lines = clean
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    if (lines.length === 0) {
      return {
        error: "Tệp tải lên đang trống. Vui lòng kiểm tra lại nội dung tệp.",
        rows: [],
      };
    }
    const firstCells = splitBulkCsvLine(lines[0]).map((c) => c.trim());
    const normHeaders = firstCells.map((c) =>
      c
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/đ/g, "d")
        .replace(/[^a-z0-9_]/g, "_"),
    );

    const hasEmailLikeInRow0 = firstCells.some((c) => c.includes("@"));
    let startIdx = 0;
    let nameCol = 0;
    let emailCol = 1;
    let schoolCol = 2;

    if (!hasEmailLikeInRow0) {
      startIdx = 1;
      const foundNameIdx = normHeaders.findIndex(
        (h) =>
          h.includes("ho_va_ten") ||
          h.includes("ho_ten") ||
          h === "ten" ||
          h === "name" ||
          h === "full_name" ||
          h === "display_name",
      );
      const foundEmailIdx = normHeaders.findIndex(
        (h) => h.includes("email") || h.includes("thu_dien_tu") || h === "mail",
      );
      const foundSchoolIdx = normHeaders.findIndex(
        (h) =>
          h.includes("truong") ||
          h.includes("don_vi") ||
          h.includes("school") ||
          h.includes("vai_tro") ||
          h.includes("role"),
      );
      if (firstCells.length < 3 || foundNameIdx === -1 || foundEmailIdx === -1 || foundSchoolIdx === -1) {
        return {
          error:
            "Tệp thiếu cột bắt buộc (Họ và tên / ho_ten, Email / email, Trường/Đơn vị / vai_tro). Vui lòng dùng đúng tệp mẫu 3 cột chuẩn.",
          rows: [],
        };
      }
      nameCol = foundNameIdx;
      emailCol = foundEmailIdx;
      schoolCol = foundSchoolIdx;
    } else if (firstCells.length < 2) {
      return {
        error:
          "Tệp thiếu cột bắt buộc (Họ và tên, Email, Trường/Đơn vị). Vui lòng dùng đúng tệp mẫu 3 cột chuẩn.",
        rows: [],
      };
    }

    const out: Array<{ rowNum: number; name: string; email: string; school: string }> = [];
    for (let i = startIdx; i < lines.length && out.length < 500; i++) {
      const cells = splitBulkCsvLine(lines[i]);
      out.push({
        rowNum: out.length + 1,
        name: cells[nameCol] ?? "",
        email: cells[emailCol] ?? "",
        school: cells[schoolCol] ?? "",
      });
    }
    if (out.length === 0) {
      return {
        error: "Tệp không có dòng dữ liệu nào sau dòng tiêu đề. Vui lòng kiểm tra lại.",
        rows: [],
      };
    }
    return { error: "", rows: out };
  };

  const parseXlsxBufferToCsvText = async (buf: ArrayBuffer): Promise<string | null> => {
    const bytes = new Uint8Array(buf);
    if (bytes.length < 4 || bytes[0] !== 0x50 || bytes[1] !== 0x4b) {
      return null;
    }
    const view = new DataView(buf);
    const entries = new Map<string, string>();
    const decoder = new TextDecoder("utf-8");

    let eocdOffset = -1;
    const minEocd = Math.max(0, bytes.length - 65557);
    for (let i = bytes.length - 22; i >= minEocd; i--) {
      if (view.getUint32(i, true) === 0x06054b50) {
        eocdOffset = i;
        break;
      }
    }
    if (eocdOffset === -1) return null;

    const totalEntries = view.getUint16(eocdOffset + 10, true);
    let cdOffset = view.getUint32(eocdOffset + 16, true);

    for (let e = 0; e < totalEntries && cdOffset + 46 <= bytes.length; e++) {
      if (view.getUint32(cdOffset, true) !== 0x02014b50) break;
      const method = view.getUint16(cdOffset + 10, true);
      const compSize = view.getUint32(cdOffset + 20, true);
      const nameLen = view.getUint16(cdOffset + 28, true);
      const extraLen = view.getUint16(cdOffset + 30, true);
      const commentLen = view.getUint16(cdOffset + 32, true);
      const localHeaderOffset = view.getUint32(cdOffset + 42, true);

      const entryName = decoder.decode(bytes.subarray(cdOffset + 46, cdOffset + 46 + nameLen));
      cdOffset += 46 + nameLen + extraLen + commentLen;

      if (
        entryName !== "xl/sharedStrings.xml" &&
        !entryName.startsWith("xl/worksheets/sheet")
      ) {
        continue;
      }
      if (localHeaderOffset + 30 > bytes.length) continue;
      if (view.getUint32(localHeaderOffset, true) !== 0x04034b50) continue;

      const lNameLen = view.getUint16(localHeaderOffset + 26, true);
      const lExtraLen = view.getUint16(localHeaderOffset + 28, true);
      const dataStart = localHeaderOffset + 30 + lNameLen + lExtraLen;
      const compBytes = bytes.subarray(dataStart, dataStart + compSize);

      if (method === 0) {
        entries.set(entryName, decoder.decode(compBytes));
      } else if (method === 8 && typeof DecompressionStream !== "undefined") {
        try {
          const ds = new DecompressionStream("deflate-raw");
          const writer = ds.writable.getWriter();
          void writer.write(compBytes);
          void writer.close();
          const decompBuf = await new Response(ds.readable).arrayBuffer();
          entries.set(entryName, decoder.decode(new Uint8Array(decompBuf)));
        } catch {
          return null;
        }
      }
    }

    const sheetXml =
      entries.get("xl/worksheets/sheet1.xml") ??
      Array.from(entries.entries()).find(([k]) => k.startsWith("xl/worksheets/sheet"))?.[1];
    if (!sheetXml) return null;

    const decodeXmlEntities = (s: string) =>
      s
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">")
        .replace(/&quot;/g, '"')
        .replace(/&apos;/g, "'")
        .replace(/&amp;/g, "&");

    const sharedStrings: string[] = [];
    const sstXml = entries.get("xl/sharedStrings.xml");
    if (sstXml) {
      const siMatches = sstXml.match(/<si[\s>][\s\S]*?<\/si>/g) ?? [];
      for (const si of siMatches) {
        const tMatches = si.match(/<t(?:\s[^>]*)?>([\s\S]*?)<\/t>/g) ?? [];
        const combined = tMatches
          .map((t) => decodeXmlEntities(t.replace(/^<t(?:\s[^>]*)?>|<\/t>$/g, "")))
          .join("");
        sharedStrings.push(combined);
      }
    }

    const colIndexFromRef = (ref: string): number => {
      const m = ref.match(/^[A-Z]+/i);
      if (!m) return -1;
      let idx = 0;
      const letters = m[0].toUpperCase();
      for (let i = 0; i < letters.length; i++) {
        idx = idx * 26 + (letters.charCodeAt(i) - 64);
      }
      return idx - 1;
    };

    const rowMatches = sheetXml.match(/<row[\s>][\s\S]*?<\/row>/g) ?? [];
    const csvLines: string[] = [];
    for (const rowXml of rowMatches) {
      const cellMatches = rowXml.match(/<c[\s>][\s\S]*?<\/c>/g) ?? [];
      const rowCells: string[] = [];
      let nextFallbackIdx = 0;
      for (const cellXml of cellMatches) {
        const refMatch = cellXml.match(/\br="([A-Z]+\d+)"/i);
        const typeMatch = cellXml.match(/\bt="([^"]+)"/);
        const cIdx = refMatch ? colIndexFromRef(refMatch[1]) : nextFallbackIdx;
        nextFallbackIdx = Math.max(nextFallbackIdx, cIdx + 1);
        const cType = typeMatch ? typeMatch[1] : "";
        let val = "";
        if (cType === "inlineStr") {
          const tMatches = cellXml.match(/<t(?:\s[^>]*)?>([\s\S]*?)<\/t>/g) ?? [];
          val = tMatches
            .map((t) => decodeXmlEntities(t.replace(/^<t(?:\s[^>]*)?>|<\/t>$/g, "")))
            .join("");
        } else {
          const vMatch = cellXml.match(/<v>([\s\S]*?)<\/v>/);
          const rawV = vMatch ? decodeXmlEntities(vMatch[1].trim()) : "";
          if (cType === "s") {
            const sstIdx = Number.parseInt(rawV, 10);
            val = Number.isFinite(sstIdx) && sharedStrings[sstIdx] !== undefined ? sharedStrings[sstIdx] : "";
          } else {
            val = rawV;
          }
        }
        while (rowCells.length <= cIdx) rowCells.push("");
        rowCells[cIdx] = val;
      }
      if (rowCells.some((c) => c.trim() !== "")) {
        const escaped = rowCells.map((c) => `"${String(c ?? "").replace(/"/g, '""')}"`);
        csvLines.push(escaped.join(","));
      }
    }
    return csvLines.join("\n");
  };

  const handleBulkFileObject = async (file: File | null | undefined) => {
    if (!file) return;
    setBulkErrorMsg("");
    setBulkStep4Error("");
    const name = String(file.name || "danh-sach.csv");
    const lower = name.toLowerCase();
    const isCsv = lower.endsWith(".csv");
    const isXlsx = lower.endsWith(".xlsx");
    if (!isCsv && !isXlsx) {
      setBulkFileName("");
      setBulkRows([]);
      setBulkErrorMsg("Định dạng tệp không được hỗ trợ. Vui lòng chỉ chọn tệp .csv hoặc .xlsx.");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setBulkFileName("");
      setBulkRows([]);
      setBulkErrorMsg(
        "Dung lượng tệp vượt quá giới hạn 2 MB. Vui lòng chia nhỏ tệp (tối đa 500 bản ghi/lần nhập).",
      );
      return;
    }
    const kb = Math.max(0.1, file.size / 1024).toFixed(1).replace(".", ",") + " KB";
    if (isCsv) {
      try {
        const text = await file.text();
        const parsed = parseBulkCsvText(text);
        if (parsed.error) {
          setBulkFileName("");
          setBulkRows([]);
          setBulkErrorMsg(parsed.error);
          return;
        }
        setBulkFileName(name);
        setBulkFileSize(kb);
        setBulkFileExt("CSV");
        setBulkFilter("all");
        setBulkPreviewPage(1);
        setBulkRows(analyzeBulkInput(parsed.rows));
      } catch {
        setBulkFileName("");
        setBulkRows([]);
        setBulkErrorMsg("Không thể đọc tệp CSV. Vui lòng kiểm tra mã hóa UTF-8 của tệp.");
      }
      return;
    }
    // .xlsx handling (real OpenXML ZIP or text-formatted .xlsx in test fixtures; never inject fake rows)
    try {
      const text = await file.text();
      if (text && !text.startsWith("PK") && text.includes(",")) {
        const parsed = parseBulkCsvText(text);
        if (parsed.error) {
          setBulkFileName("");
          setBulkRows([]);
          setBulkErrorMsg(parsed.error);
          return;
        }
        setBulkFileName(name);
        setBulkFileSize(kb);
        setBulkFileExt("XLSX");
        setBulkFilter("all");
        setBulkPreviewPage(1);
        setBulkRows(analyzeBulkInput(parsed.rows));
        return;
      }
      if (typeof file.arrayBuffer === "function") {
        const buf = await file.arrayBuffer();
        const extractedCsv = await parseXlsxBufferToCsvText(buf);
        if (extractedCsv !== null) {
          const parsed = parseBulkCsvText(extractedCsv);
          if (parsed.error) {
            setBulkFileName("");
            setBulkRows([]);
            setBulkErrorMsg(parsed.error);
            return;
          }
          setBulkFileName(name);
          setBulkFileSize(kb);
          setBulkFileExt("XLSX");
          setBulkFilter("all");
          setBulkPreviewPage(1);
          setBulkRows(analyzeBulkInput(parsed.rows));
          return;
        }
      }
    } catch {
      /* handled below with honest error */
    }
    setBulkFileName("");
    setBulkRows([]);
    setBulkErrorMsg(
      "Không thể đọc nội dung tệp .xlsx này. Vui lòng kiểm tra lại định dạng tệp Excel chuẩn (3 cột bắt buộc: Họ và tên, Email, Trường/Đơn vị) hoặc lưu dưới dạng .csv (UTF-8).",
    );
  };

  const isSysDraftDirty =
    quotaDraft.studentDailyRequests !== quotaConfig.studentDailyRequests ||
    quotaDraft.teacherDailyRequests !== quotaConfig.teacherDailyRequests ||
    quotaDraft.studentDailyTokens !== quotaConfig.studentDailyTokens ||
    quotaDraft.teacherDailyTokens !== quotaConfig.teacherDailyTokens ||
    quotaDraft.studentRatePerMin !== quotaConfig.studentRatePerMin ||
    quotaDraft.teacherRatePerMin !== quotaConfig.teacherRatePerMin ||
    quotaDraft.vndBudgetRaw !== quotaConfig.vndBudgetRaw ||
    quotaDraft.autoCutoffEnabled !== quotaConfig.autoCutoffEnabled;

  const attemptCloseSysSettings = () => {
    if (isSysDraftDirty) {
      setSysDiscardConfirmOpen(true);
      return;
    }
    setSysSettingsOpen(false);
    setSysDiscardConfirmOpen(false);
    setAutoCutoffMenuOpen(false);
  };

  const dotsTargetUser = dotsMenu ? users.find((u) => u.id === dotsMenu.userId) ?? null : null;

  if (!user || user.role !== "admin") {
    return (
      <section
        className="axo-page-view active"
        id="view-admin-denied"
        aria-label="Từ chối truy cập Quản trị"
      >
        <div className="auth-standalone-shell">
          <div className="auth-top-bar">
            <button
              type="button"
              className="auth-brand-link"
              data-auth-home="1"
              aria-label="Về Trang chủ"
              title="Về Trang chủ"
              onClick={goHome}
            >
              <IconAxoLogo size={22} />
              <span>Axo</span>
            </button>
          </div>
          <div className="auth-center-stage">
            <div className="auth-card" role="alert">
              <div className="auth-head">
                <h2 className="auth-title">
                  {!resolved
                    ? "Đang kiểm tra quyền truy cập..."
                    : !user
                      ? "Khu vực Quản trị yêu cầu đăng nhập"
                      : "Không có quyền truy cập Quản trị"}
                </h2>
                <p className="auth-subtitle">
                  {!resolved
                    ? "Vui lòng chờ hệ thống xác thực phiên đăng nhập hiện tại."
                    : !user
                      ? "Vui lòng đăng nhập bằng tài khoản Quản trị viên hệ thống để tiếp tục."
                      : "Tài khoản hiện tại không có quyền quản trị hệ thống Axo."}
                </p>
              </div>
              {resolved && !user && (
                <button
                  type="button"
                  className="btn-auth-submit"
                  id="btn-rbac-go-login"
                  onClick={() => {
                    if (typeof window !== "undefined" && window.location.hash === "#admin") {
                      window.history.replaceState(null, "", window.location.pathname);
                    }
                    setView("login");
                  }}
                >
                  Đăng nhập Quản trị
                </button>
              )}
              <div className="auth-footer-Switch">
                <button
                  type="button"
                  className="btn-text-link"
                  id="btn-rbac-back-home"
                  onClick={() => {
                    if (typeof window !== "undefined" && window.location.hash === "#admin") {
                      window.history.replaceState(null, "", window.location.pathname);
                    }
                    goHome();
                  }}
                >
                  ← Về Trang chủ
                </button>
              </div>
            </div>
          </div>
          <div className="auth-bottom-spacer" />
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="axo-page-view active" id="view-admin" aria-label="Bảng điều khiển Quản trị Axo">
        <div
          className={`admin-shell${sidebarCollapsed ? " sb-collapsed" : ""}${mobileDrawerOpen ? " sb-mobile-open" : ""}`}
          id="admin-shell"
          onClick={() => {
            setDotsMenu(null);
            setNotifOpen(false);
            setAccMenuOpen(false);
            setAddAccMenuOpen(false);
            setFilterOpen(false);
            setPageSizeOpen(false);
          }}
        >
          <div
            className={`admin-sidebar-backdrop${mobileDrawerOpen ? " open" : ""}`}
            id="admin-sidebar-backdrop"
            onClick={() => setMobileDrawerOpen(false)}
          />

          <aside
            className={`admin-sidebar${sidebarCollapsed ? " is-collapsed" : ""}${mobileDrawerOpen ? " mobile-open" : ""}`}
            id="admin-sidebar"
            aria-label="Điều hướng Quản trị"
          >
            <div className="admin-sb-top">
              <div className="admin-sb-brand-row">
                <button
                  type="button"
                  className={`admin-sb-brand${sidebarCollapsed && !mobileDrawerOpen ? " is-expand-trigger" : " is-static-brand"}`}
                  id="btn-admin-sb-brand"
                  tabIndex={sidebarCollapsed && !mobileDrawerOpen ? 0 : -1}
                  aria-label={sidebarCollapsed && !mobileDrawerOpen ? "Mở rộng thanh bên" : "Axo Quản trị"}
                  aria-expanded={sidebarCollapsed && !mobileDrawerOpen ? false : undefined}
                  onClick={(e) => {
                    if (sidebarCollapsed && !mobileDrawerOpen) {
                      const wasKeyboard = e.detail === 0;
                      setSidebarCollapsed(false);
                      if (wasKeyboard) {
                        requestAnimationFrame(() => {
                          document.getElementById("btn-admin-sidebar-collapse")?.focus();
                        });
                      }
                    }
                  }}
                >
                  <span className="sb-logo-slot">
                    <span className="sb-logo-default">
                      <IconAxoSidebarLogo />
                    </span>
                    <span className="sb-logo-expand-icon" aria-hidden="true">
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <rect x="3" y="3" width="18" height="18" rx="2.5" />
                        <line x1="9" y1="3" x2="9" y2="21" />
                        <polyline points="13 9 16 12 13 15" />
                      </svg>
                    </span>
                  </span>
                  <div className="admin-sb-brand-text">
                    <span className="admin-sb-brand-title">Axo</span>
                    <span className="admin-sb-brand-sub">Quản trị</span>
                  </div>
                  <span className="admin-sb-tooltip" id="admin-sb-brand-tooltip">
                    Mở rộng thanh bên
                  </span>
                </button>

                <button
                  type="button"
                  className="btn-sb-collapse"
                  id="btn-admin-sidebar-collapse"
                  aria-label="Thu gọn thanh bên"
                  aria-expanded={!sidebarCollapsed}
                  title="Thu gọn thanh bên"
                  onClick={() => setSidebarCollapsed((v) => !v)}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <rect x="3" y="3" width="18" height="18" rx="2.5" />
                    <line x1="9" y1="3" x2="9" y2="21" />
                    <polyline points="15 9 12 12 15 15" />
                  </svg>
                  <span className="admin-sb-tooltip" id="admin-sb-collapse-tooltip">
                    Thu gọn thanh bên
                  </span>
                </button>

                <button
                  type="button"
                  className="btn-admin-drawer-close"
                  id="btn-admin-drawer-close"
                  aria-label="Đóng menu điều hướng quản trị"
                  title="Đóng menu"
                  onClick={() => setMobileDrawerOpen(false)}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>

              <nav className="admin-sb-nav" aria-label="Danh mục quản trị">
                <button
                  type="button"
                  className={`admin-sb-item${adminTab === "overview" ? " is-active" : ""}`}
                  data-admin-tab="overview"
                  aria-label="Tổng quan"
                  title="Tổng quan"
                  onClick={() => {
                    setAdminTab("overview");
                    setMobileDrawerOpen(false);
                  }}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <rect x="3" y="3" width="7" height="7" rx="1.5" />
                    <rect x="14" y="3" width="7" height="7" rx="1.5" />
                    <rect x="3" y="14" width="7" height="7" rx="1.5" />
                    <rect x="14" y="14" width="7" height="7" rx="1.5" />
                  </svg>
                  <span className="admin-sb-label">Tổng quan</span>
                  <span className="admin-sb-tooltip">Tổng quan</span>
                </button>

                <button
                  type="button"
                  className={`admin-sb-item${adminTab === "accounts" ? " is-active" : ""}`}
                  data-admin-tab="accounts"
                  aria-label="Tài khoản"
                  title="Tài khoản"
                  onClick={() => {
                    setAdminTab("accounts");
                    setMobileDrawerOpen(false);
                  }}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                  </svg>
                  <span className="admin-sb-label">Tài khoản</span>
                  <span className="admin-sb-tooltip">Tài khoản</span>
                </button>

                <button
                  type="button"
                  className={`admin-sb-item${adminTab === "analytics" ? " is-active" : ""}`}
                  data-admin-tab="analytics"
                  aria-label="Thống kê"
                  title="Thống kê"
                  onClick={() => {
                    setAdminTab("analytics");
                    setMobileDrawerOpen(false);
                  }}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <line x1="18" y1="20" x2="18" y2="10" />
                    <line x1="12" y1="20" x2="12" y2="4" />
                    <line x1="6" y1="20" x2="6" y2="14" />
                  </svg>
                  <span className="admin-sb-label">Thống kê</span>
                  <span className="admin-sb-tooltip">Thống kê</span>
                </button>

                <button
                  type="button"
                  className={`admin-sb-item${adminTab === "audit" ? " is-active" : ""}`}
                  data-admin-tab="audit"
                  aria-label="Nhật ký quản trị"
                  title="Nhật ký quản trị"
                  onClick={() => {
                    setAdminTab("audit");
                    setMobileDrawerOpen(false);
                  }}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                  </svg>
                  <span className="admin-sb-label">Nhật ký quản trị</span>
                  <span className="admin-sb-tooltip">Nhật ký quản trị</span>
                </button>
              </nav>
            </div>
          </aside>

          <div className="admin-content-col">
            <header className="admin-header" id="admin-header" aria-label="Thanh tiêu đề Quản trị">
              <div className="admin-header-left">
                <button
                  type="button"
                  className="btn-admin-mobile-menu"
                  id="btn-admin-mobile-menu"
                  aria-label="Mở menu điều hướng quản trị"
                  title="Menu điều hướng"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMobileDrawerOpen(true);
                  }}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <line x1="3" y1="6" x2="21" y2="6" />
                    <line x1="3" y1="12" x2="21" y2="12" />
                    <line x1="3" y1="18" x2="21" y2="18" />
                  </svg>
                </button>
              </div>

              <div className="admin-header-right" id="admin-header-right">
                <button
                  type="button"
                  className={`btn-admin-hdr-icon${notifOpen ? " is-open" : ""}`}
                  id="btn-admin-notif-bell"
                  aria-label="Thông báo quản trị"
                  aria-haspopup="dialog"
                  aria-expanded={notifOpen}
                  title="Thông báo quản trị"
                  onClick={(e) => {
                    e.stopPropagation();
                    setAccMenuOpen(false);
                    setNotifOpen((v) => !v);
                  }}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                  </svg>
                  {pendingTeachers.length > 0 && (
                    <span className="admin-notif-badge" id="admin-notif-badge">
                      {pendingTeachers.length}
                    </span>
                  )}
                </button>

                <button
                  type="button"
                  className={`btn-admin-account-trigger${accMenuOpen ? " is-open" : ""}`}
                  id="btn-admin-account-menu"
                  aria-label="Tài khoản Quản trị viên"
                  aria-haspopup="menu"
                  aria-expanded={accMenuOpen}
                  title="Tài khoản Quản trị viên"
                  onClick={(e) => {
                    e.stopPropagation();
                    setNotifOpen(false);
                    setAccMenuOpen((v) => !v);
                  }}
                >
                  <span className="admin-hdr-avatar">A</span>
                  <svg className="admin-hdr-caret" viewBox="0 0 24 24" aria-hidden="true">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                <div
                  className={`admin-notif-popover${notifOpen ? " open" : ""}`}
                  id="admin-notif-popover"
                  role="dialog"
                  aria-label="Thông báo quản trị"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="notif-pop-head">
                    <span className="notif-pop-title">Thông báo quản trị</span>
                  </div>
                  {pendingTeachers.length === 0 ? (
                    <div className="notif-empty">Hệ thống vận hành ổn định, không có yêu cầu tồn đọng.</div>
                  ) : (
                    <div className="notif-list">
                      {pendingTeachers.map((pt) => (
                        <button
                          key={pt.id}
                          type="button"
                          className="notif-item is-unread"
                          onClick={() => {
                            setNotifOpen(false);
                            setAdminTab("accounts");
                            setStatusFilter("pending_teacher");
                          }}
                        >
                          <span className="notif-item-title">Yêu cầu cấp quyền Giáo viên: {pt.name}</span>
                          <span className="notif-item-sub">{pt.email}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div
                  className={`admin-account-dropdown${accMenuOpen ? " open" : ""}`}
                  id="admin-account-dropdown"
                  role="menu"
                  aria-label="Tài khoản Quản trị viên"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="admin-acc-head" id="admin-account-dropdown-info-head">
                    <div className="admin-acc-kicker">Thông tin tài khoản</div>
                    <div className="admin-acc-name">{user?.displayName || "Quản trị viên"}</div>
                    <div className="admin-acc-email">{user?.email || "admin@axo.edu.vn"}</div>
                    <div className="admin-acc-role-badge">
                      <span className="role-chip admin">Quản trị viên</span>
                    </div>
                  </div>
                  <div className="admin-acc-menu-list">
                    <button
                      type="button"
                      className="admin-acc-menu-item"
                      role="menuitem"
                      data-admin-acc-act="account-info"
                      onClick={() => {
                        setAccMenuOpen(false);
                        const adminItem = users.find((u) => u.role === "admin") ?? users[0] ?? null;
                        if (adminItem) setDetailUser(adminItem);
                      }}
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                      </svg>
                      <span>Thông tin tài khoản</span>
                    </button>
                    <button
                      type="button"
                      className="admin-acc-menu-item"
                      role="menuitem"
                      data-admin-acc-act="profile"
                      onClick={() => {
                        setAccMenuOpen(false);
                        openAccountModal("profile");
                      }}
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                        <circle cx="12" cy="7" r="4" />
                      </svg>
                      <span>Cài đặt tài khoản</span>
                    </button>
                    <button
                      type="button"
                      className={`admin-acc-menu-item${sysSettingsOpen ? " is-active" : ""}`}
                      role="menuitem"
                      data-admin-acc-act="system-settings"
                      onClick={() => {
                        setAccMenuOpen(false);
                        setSysSettingsOpen(true);
                      }}
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <line x1="4" y1="21" x2="4" y2="14" />
                        <line x1="4" y1="10" x2="4" y2="3" />
                        <line x1="12" y1="21" x2="12" y2="12" />
                        <line x1="12" y1="8" x2="12" y2="3" />
                        <line x1="20" y1="21" x2="20" y2="16" />
                        <line x1="20" y1="12" x2="20" y2="3" />
                        <line x1="1" y1="14" x2="7" y2="14" />
                        <line x1="9" y1="8" x2="15" y2="8" />
                        <line x1="17" y1="16" x2="23" y2="16" />
                      </svg>
                      <span>Cài đặt hệ thống</span>
                    </button>
                    <button
                      type="button"
                      className="admin-acc-menu-item"
                      role="menuitem"
                      data-admin-acc-act="learning"
                      onClick={() => {
                        setAccMenuOpen(false);
                        goHome();
                      }}
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="m3 10 9-7 9 7v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V10Z" />
                        <path d="M9 21V12h6v9" />
                      </svg>
                      <span>Về trang học tập</span>
                    </button>
                    <div className="admin-acc-menu-sep" role="separator" />
                    <button
                      type="button"
                      className="admin-acc-menu-item danger"
                      role="menuitem"
                      data-admin-acc-act="logout"
                      onClick={() => {
                        setAccMenuOpen(false);
                        void logout();
                        goHome();
                      }}
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                        <polyline points="16 17 21 12 16 7" />
                        <line x1="21" y1="12" x2="9" y2="12" />
                      </svg>
                      <span>Đăng xuất</span>
                    </button>
                  </div>
                </div>
              </div>
            </header>

            <div className="admin-main-area" id="admin-main-mount" data-admin-page={adminTab}>
              {adminTab === "overview" ? (
                <>
                  <div className="admin-page-head-group" id="admin-page-head-group">
                    <h1 className="admin-content-page-title" id="admin-page-title">
                      Tổng quan hệ thống
                    </h1>
                    <p className="admin-page-intro" id="admin-page-intro">
                      Theo dõi các chỉ số vận hành và những yêu cầu cần xử lý.
                    </p>
                  </div>

                  <div className="admin-kpi-grid" id="admin-overview-kpi-grid">
                    <div className="admin-kpi-card">
                      <div className="admin-kpi-lbl">
                        <span>Tổng số tài khoản</span>
                        <span className="role-chip student">Đang quản lý</span>
                      </div>
                      <div className="admin-kpi-val">{totalUsersCount} tài khoản</div>
                      <div className="admin-kpi-sub">
                        {studentCount} Học sinh · {teacherVerifiedCount} Giáo viên · {lockedCount} Đã khóa · {adminCount} Quản trị
                      </div>
                    </div>
                    <div className="admin-kpi-card">
                      <div className="admin-kpi-lbl">
                        <span>Yêu cầu cấp quyền Giáo viên</span>
                        <span className={pendingTeachers.length > 0 ? "role-chip pending" : "role-chip neutral"}>
                          {pendingTeachers.length} chờ duyệt
                        </span>
                      </div>
                      <div className="admin-kpi-val">{pendingTeachers.length} hồ sơ</div>
                      <div className="admin-kpi-sub">
                        {pendingTeachers.length > 0
                          ? "Ưu tiên xử lý yêu cầu gửi sớm nhất trước để tránh tồn đọng"
                          : "Hiện không có hồ sơ đăng ký Giáo viên đang tồn đọng"}
                      </div>
                    </div>
                    <div className="admin-kpi-card">
                      <div className="admin-kpi-lbl">
                        <span>Lượt phân tích AI hôm nay</span>
                        <span className="role-chip student">Hôm nay</span>
                      </div>
                      <div className="admin-kpi-val">
                        {Math.max(overviewStats.analysesToday, totalUsedToday)} lượt
                      </div>
                      <div className="admin-kpi-sub">
                        {overviewStats.totalAnalyses > 0
                          ? `${overviewStats.succeededRequests}/${overviewStats.totalAnalyses} yêu cầu thành công · 7 ngày: ${overviewStats.analyses7d} lượt`
                          : `0/0 yêu cầu · 7 ngày qua: 0 lượt · ${overviewStats.totalHistoryEntries} phiên lưu`}
                      </div>
                    </div>
                    <div className="admin-kpi-card">
                      <div className="admin-kpi-lbl">
                        <span>Token tiêu thụ (7 ngày)</span>
                        <span className={overviewStats.tokensMeasured ? "role-chip teacher" : "role-chip neutral"}>
                          {overviewStats.tokensMeasured ? "Đã ghi nhận" : "Theo dõi token"}
                        </span>
                      </div>
                      <div className={`admin-kpi-val${overviewStats.tokensMeasured && overviewStats.totalTokens7d !== null ? "" : " is-empty-metric"}`}>
                        {overviewStats.tokensMeasured && overviewStats.totalTokens7d !== null
                          ? `${overviewStats.totalTokens7d.toLocaleString("vi-VN")} tokens`
                          : "Chưa có dữ liệu"}
                      </div>
                      <div className="admin-kpi-sub">
                        {overviewStats.tokensMeasured
                          ? `Đầu vào: ${(overviewStats.inputTokens7d ?? 0).toLocaleString("vi-VN")} · Đầu ra: ${(overviewStats.outputTokens7d ?? 0).toLocaleString("vi-VN")}${overviewStats.thoughtsTokens7d ? ` · Suy luận: ${overviewStats.thoughtsTokens7d.toLocaleString("vi-VN")}` : ""}`
                          : "Ghi nhận tự động khi phát sinh lượt gọi Gemini trực tuyến"}
                      </div>
                    </div>
                    <div className="admin-kpi-card">
                      <div className="admin-kpi-lbl">
                        <span>Hạn mức sử dụng hôm nay</span>
                        <span className="role-chip student">
                          {quotaConfig.autoCutoffEnabled ? "Đang bảo vệ" : "Theo dõi hạn mức"}
                        </span>
                      </div>
                      <div className="admin-kpi-val">{totalUsedToday} lượt đã dùng</div>
                      <div className="admin-kpi-sub">
                        Định mức ngày: Học sinh {quotaConfig.studentDailyRequests} lượt · Giáo viên {quotaConfig.teacherDailyRequests} lượt
                      </div>
                    </div>
                    <div className="admin-kpi-card">
                      <div className="admin-kpi-lbl">
                        <span>Trạng thái dịch vụ AI</span>
                        {overviewStats.aiServiceConfigured === false ? (
                          <span className="role-chip neutral">Chế độ đệm</span>
                        ) : (
                          <span className="role-chip teacher">Hoạt động</span>
                        )}
                      </div>
                      <div className="admin-kpi-val">
                        {quotaConfig.studentRatePerMin}–{quotaConfig.teacherRatePerMin} req/phút
                      </div>
                      <div className="admin-kpi-sub">
                        Model: {overviewStats.configuredModelId || "gemini-2.5-flash"}
                        {overviewStats.avgLatencyMs !== null
                          ? ` · TB ${overviewStats.avgLatencyMs.toLocaleString("vi-VN")} ms`
                          : ` · ${overviewStats.cachedProblems} đề lưu đệm`}
                      </div>
                    </div>
                  </div>

                  <div className="admin-panel-card">
                    <div className="admin-panel-head">
                      <div>
                        <h2 className="admin-panel-title">
                          Yêu cầu chờ cấp quyền Giáo viên ({pendingTeachers.length})
                        </h2>
                        <div className="admin-panel-sub">
                          Mặc định sắp xếp yêu cầu cũ nhất trước để xử lý theo thứ tự gửi.
                        </div>
                      </div>
                      <button
                        type="button"
                        className="btn-admin-sm"
                        data-goto-admin-tab="accounts"
                        onClick={() => setAdminTab("accounts")}
                      >
                        Xem tất cả tài khoản ({totalUsersCount}) →
                      </button>
                    </div>
                    {pendingTeachers.length === 0 ? (
                      <div className="lib-empty-state admin-empty-inline">
                        Hiện không có yêu cầu cấp quyền Giáo viên nào đang chờ xử lý.
                      </div>
                    ) : (
                      <div className="admin-table-wrap">
                        <table className="admin-table" id="admin-pending-table">
                          <thead>
                            <tr>
                              {renderSortableTh("Người đăng ký", "name", "asc", pendingSort, togglePendingSort)}
                              {renderSortableTh("Đơn vị công tác", "school", "asc", pendingSort, togglePendingSort)}
                              {renderSortableTh("Ngày gửi yêu cầu", "joinedTs", "asc", pendingSort, togglePendingSort)}
                              {renderSortableTh("Trạng thái yêu cầu", "statusOrder", "asc", pendingSort, togglePendingSort)}
                              <th>Thao tác</th>
                            </tr>
                          </thead>
                          <tbody>
                            {sortedPendingTeachers.map((u) => (
                              <tr key={u.id}>
                                <td>
                                  <strong>{u.name}</strong>
                                  <div className="admin-cell-sub">{u.email}</div>
                                </td>
                                <td>{u.school}</td>
                                <td>{u.joinedAt}</td>
                                <td>
                                  <span className="role-chip pending">Học sinh · Chờ cấp quyền GV</span>
                                </td>
                                <td>
                                  <div className="admin-action-cell">
                                    <button
                                      type="button"
                                      className="btn-admin-sm approve"
                                      onClick={() =>
                                        setConfirmAction({ type: "grant_teacher", user: u })
                                      }
                                    >
                                      Cấp quyền Giáo viên
                                    </button>
                                    <button
                                      type="button"
                                      className="btn-admin-sm"
                                      onClick={() => setDetailUser(u)}
                                    >
                                      Chi tiết
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </>
              ) : adminTab === "accounts" ? (
                <>
                  <div className="admin-page-head-row" id="admin-accounts-head-row">
                    <div className="admin-page-head-group" id="admin-page-head-group">
                      <h1 className="admin-content-page-title" id="admin-page-title">
                        Tài khoản
                      </h1>
                      <p className="admin-page-intro" id="admin-page-intro">
                        Tra cứu, lọc theo vai trò và trạng thái, điều chỉnh hạn mức cá nhân và quản lý tài khoản người dùng.
                      </p>
                    </div>
                    <div className="admin-head-actions">
                      <button
                        type="button"
                        className="btn-admin-export"
                        id="btn-admin-export-users"
                        onClick={() =>
                          void handleExportCsv(
                            "/api/admin/export/users",
                            "axo-danh-sach-tai-khoan.csv",
                          )
                        }
                      >
                        Xuất CSV
                      </button>
                      <div className="admin-add-account-wrap" id="admin-add-account-dropdown-wrap">
                      <button
                        type="button"
                        className={`btn-admin-add-account${addAccMenuOpen ? " is-open" : ""}`}
                        id="btn-admin-add-account-menu"
                        aria-haspopup="menu"
                        aria-expanded={addAccMenuOpen}
                        aria-controls="admin-add-account-dropdown"
                        onClick={(e) => {
                          e.stopPropagation();
                          setAddAccMenuOpen((v) => !v);
                        }}
                      >
                        <svg className="add-acc-plus-ico" viewBox="0 0 24 24" aria-hidden="true">
                          <line x1="12" y1="5" x2="12" y2="19" />
                          <line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                        <span>Thêm tài khoản</span>
                        <svg className="add-acc-caret" viewBox="0 0 24 24" aria-hidden="true">
                          <polyline points="6 9 12 15 18 9" />
                        </svg>
                      </button>
                      <div
                        className={`admin-add-account-dropdown${addAccMenuOpen ? " open" : ""}`}
                        id="admin-add-account-dropdown"
                        role="menu"
                        aria-label="Tùy chọn thêm tài khoản"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          type="button"
                          className="admin-add-account-item"
                          role="menuitem"
                          id="btn-add-acc-manual"
                          data-add-acc-act="manual"
                          onClick={() => {
                            setAddAccMenuOpen(false);
                            setCreateUserOpen(true);
                          }}
                        >
                          <span className="item-ico" aria-hidden="true">
                            <svg viewBox="0 0 24 24">
                              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                              <circle cx="9" cy="7" r="4" />
                              <line x1="19" y1="8" x2="19" y2="14" />
                              <line x1="22" y1="11" x2="16" y2="11" />
                            </svg>
                          </span>
                          <span className="admin-add-account-item-txt">
                            <span className="admin-add-account-item-title">Tạo tài khoản thủ công</span>
                            <span className="admin-add-account-item-sub">
                              Nhập từng học sinh · Mặc định Học sinh
                            </span>
                          </span>
                        </button>
                        <button
                          type="button"
                          className="admin-add-account-item"
                          role="menuitem"
                          id="btn-add-acc-excel"
                          data-add-acc-act="excel"
                          onClick={() => {
                            setAddAccMenuOpen(false);
                            setBulkStep(1);
                            setBulkFileName("");
                            setBulkFileSize("");
                            setBulkFileExt("");
                            setBulkRows([]);
                            setBulkFilter("all");
                            setBulkPreviewPage(1);
                            setBulkErrorMsg("");
                            setBulkStep4Error("");
                            setBulkResult(null);
                            if (bulkFileInputRef.current) bulkFileInputRef.current.value = "";
                            setBulkImportOpen(true);
                          }}
                        >
                          <span className="item-ico" aria-hidden="true">
                            <svg viewBox="0 0 24 24">
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                              <polyline points="14 2 14 8 20 8" />
                              <path d="M12 18v-6" />
                              <polyline points="9 15 12 12 15 15" />
                            </svg>
                          </span>
                          <span className="admin-add-account-item-txt">
                            <span className="admin-add-account-item-title">Nhập danh sách từ Excel</span>
                            <span className="admin-add-account-item-sub">
                              Kiểm tra & xem trước 4 bước (.csv, .xlsx)
                            </span>
                          </span>
                        </button>
                        <div className="admin-add-account-sep" role="separator" />
                        <button
                          type="button"
                          className="admin-add-account-item"
                          role="menuitem"
                          id="btn-add-acc-template"
                          data-add-acc-act="template"
                          onClick={() => {
                            setAddAccMenuOpen(false);
                            handleDownloadSampleCsv();
                          }}
                        >
                          <span className="item-ico" aria-hidden="true">
                            <svg viewBox="0 0 24 24">
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                              <polyline points="7 10 12 15 17 10" />
                              <line x1="12" y1="15" x2="12" y2="3" />
                            </svg>
                          </span>
                          <span className="admin-add-account-item-txt">
                            <span className="admin-add-account-item-title">Tải tệp mẫu</span>
                            <span className="admin-add-account-item-sub">
                              Mẫu 3 cột chuẩn: Họ và tên, Email, Trường/Đơn vị
                            </span>
                          </span>
                        </button>
                      </div>
                    </div>
                    </div>
                  </div>

                  <div className="admin-panel-card">
                    <div className="admin-accounts-toolbar" id="admin-accounts-toolbar">
                      <div className="admin-accounts-search-col">
                        <input
                          type="search"
                          id="admin-user-search-input"
                          className="auth-input"
                          placeholder="Tìm theo tên, email hoặc trường học..."
                          value={searchQuery}
                          onChange={(e) => {
                            setSearchQuery(e.target.value);
                            setCurrentPage(1);
                          }}
                          aria-label="Tìm theo tên, email hoặc trường học"
                        />
                      </div>

                      <div className="admin-accounts-filter-wrap" id="admin-accounts-filter-wrap">
                        {activeFilterCount > 0 && (
                          <button
                            type="button"
                            className="btn-admin-filter-clear-inline"
                            id="btn-admin-filter-clear-inline"
                            onClick={() => {
                              setRoleFilter("all");
                              setStatusFilter("all");
                              setCurrentPage(1);
                            }}
                          >
                            Đặt lại bộ lọc
                          </button>
                        )}
                        <button
                          type="button"
                          className={`btn-admin-filter-trigger${filterOpen ? " is-open" : ""}${activeFilterCount > 0 ? " is-filtered" : ""}`}
                          id="btn-admin-accounts-filter"
                          aria-haspopup="dialog"
                          aria-expanded={filterOpen}
                          aria-controls="admin-accounts-filter-popover"
                          onClick={(e) => {
                            e.stopPropagation();
                            setFilterOpen((v) => !v);
                          }}
                        >
                          <svg viewBox="0 0 24 24" aria-hidden="true">
                            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                          </svg>
                          <span>Bộ lọc</span>
                          {activeFilterCount > 0 && (
                            <span className="filter-active-badge" id="admin-filter-active-badge">
                              {activeFilterCount}
                            </span>
                          )}
                          <svg className="filter-caret-svg" viewBox="0 0 24 24" aria-hidden="true">
                            <polyline points="6 9 12 15 18 9" />
                          </svg>
                        </button>

                        <div
                          className={`admin-filter-popover${filterOpen ? " open" : ""}`}
                          id="admin-accounts-filter-popover"
                          role="dialog"
                          aria-label="Bộ lọc tài khoản người dùng"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="admin-filter-group">
                            <div className="admin-filter-group-title">Vai trò</div>
                            <div className="admin-filter-options" role="group" aria-label="Lọc theo vai trò">
                              {[
                                { id: "all", label: "Tất cả vai trò", count: totalUsersCount },
                                { id: "student", label: "Học sinh", count: studentCount },
                                { id: "teacher", label: "Giáo viên", count: teacherVerifiedCount },
                                { id: "admin", label: "Quản trị viên", count: adminCount },
                              ].map((opt) => (
                                <button
                                  key={opt.id}
                                  type="button"
                                  className={`admin-filter-opt-btn${roleFilter === opt.id ? " is-selected" : ""}`}
                                  data-admin-role-filter={opt.id}
                                  aria-pressed={roleFilter === opt.id}
                                  onClick={() => {
                                    setRoleFilter(opt.id as typeof roleFilter);
                                    setCurrentPage(1);
                                  }}
                                >
                                  <span className="admin-filter-opt-left">
                                    <span className="admin-filter-check" aria-hidden="true">
                                      <IconCheck size={12} />
                                    </span>
                                    <span>{opt.label}</span>
                                  </span>
                                  <span className="admin-filter-count-pill">{opt.count}</span>
                                </button>
                              ))}
                            </div>
                          </div>

                          <div className="admin-filter-group">
                            <div className="admin-filter-group-title">Trạng thái</div>
                            <div className="admin-filter-options" role="group" aria-label="Lọc theo trạng thái">
                              {[
                                { id: "all", label: "Tất cả trạng thái", count: totalUsersCount },
                                { id: "active", label: "Hoạt động", count: activeCount },
                                {
                                  id: "pending_teacher",
                                  label: "Chờ cấp quyền Giáo viên",
                                  count: pendingTeachers.length,
                                },
                                {
                                  id: "pending_activation",
                                  label: "Chờ kích hoạt",
                                  count: pendingActivationCount,
                                },
                                { id: "locked", label: "Đã khóa", count: lockedCount },
                              ].map((opt) => (
                                <button
                                  key={opt.id}
                                  type="button"
                                  className={`admin-filter-opt-btn${statusFilter === opt.id ? " is-selected" : ""}`}
                                  data-admin-status-filter={opt.id}
                                  aria-pressed={statusFilter === opt.id}
                                  onClick={() => {
                                    setStatusFilter(opt.id as typeof statusFilter);
                                    setCurrentPage(1);
                                  }}
                                >
                                  <span className="admin-filter-opt-left">
                                    <span className="admin-filter-check" aria-hidden="true">
                                      <IconCheck size={12} />
                                    </span>
                                    <span>{opt.label}</span>
                                  </span>
                                  <span className="admin-filter-count-pill">{opt.count}</span>
                                </button>
                              ))}
                            </div>
                          </div>

                          <div className="admin-filter-pop-foot">
                            <span className="admin-filter-match-txt">
                              Khớp <strong>{totalFiltered}</strong> / {totalUsersCount} tài khoản
                            </span>
                            <button
                              type="button"
                              className="btn-admin-filter-reset"
                              id="btn-admin-filter-reset"
                              disabled={activeFilterCount === 0}
                              onClick={() => {
                                setRoleFilter("all");
                                setStatusFilter("all");
                                setCurrentPage(1);
                              }}
                            >
                              Đặt lại bộ lọc
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="admin-table-wrap" id="admin-accounts-table-wrap">
                      <table className="admin-table" id="admin-accounts-table">
                        <thead>
                          <tr>
                            {renderSortableTh("Người dùng", "name", "asc", sortState, toggleSort)}
                            {renderSortableTh("Vai trò", "roleOrder", "asc", sortState, toggleSort)}
                            {renderSortableTh("Trạng thái", "statusOrder", "asc", sortState, toggleSort)}
                            {renderSortableTh("Ngày đăng ký", "joinedTs", "desc", sortState, toggleSort)}
                            {renderSortableTh("Hạn mức AI / ngày", "dailyLimit", "desc", sortState, toggleSort)}
                            {renderSortableTh("Đã dùng hôm nay", "usedToday", "desc", sortState, toggleSort)}
                            <th>Thao tác</th>
                          </tr>
                        </thead>
                        <tbody>
                          {pageItems.length === 0 ? (
                            <tr>
                              <td colSpan={7} className="admin-table-empty">
                                Không tìm thấy tài khoản nào phù hợp với bộ lọc hiện tại.
                              </td>
                            </tr>
                          ) : (
                            pageItems.map((u) => {
                              const rLabel =
                                u.role === "admin"
                                  ? "Quản trị viên"
                                  : u.role === "teacher"
                                    ? "Giáo viên"
                                    : "Học sinh";
                              const isMenuOpen = dotsMenu?.userId === u.id;
                              return (
                                <tr key={u.id} data-account-row-id={u.id}>
                                  <td>
                                    <strong>{u.name}</strong>
                                    <div className="admin-cell-sub">
                                      {u.email} · {u.school}
                                    </div>
                                  </td>
                                  <td>
                                    <span className={`role-chip ${u.role}`}>{rLabel}</span>
                                  </td>
                                  <td>
                                    {u.status === "verified" ? (
                                      <span className="role-chip teacher">Đã xác minh</span>
                                    ) : u.status === "pending_teacher" ? (
                                      <span className="role-chip pending">Chờ cấp quyền GV</span>
                                    ) : u.status === "pending_activation" ? (
                                      <span className="role-chip pending-activation">Chờ kích hoạt</span>
                                    ) : u.status === "locked" ? (
                                      <span className="role-chip locked">Đã khóa</span>
                                    ) : (
                                      <span className="role-chip student">Hoạt động</span>
                                    )}
                                  </td>
                                  <td>{u.joinedAt}</td>
                                  <td>
                                    <strong>{u.dailyLimit} lượt/ngày</strong>
                                  </td>
                                  <td>
                                    {u.usedToday}/{u.dailyLimit} lượt
                                    <div className="admin-cell-sub">{u.tokensToday}</div>
                                  </td>
                                  <td>
                                    <div className="admin-action-cell">
                                      <button
                                        type="button"
                                        className="btn-admin-sm"
                                        data-admin-detail-id={u.id}
                                        onClick={() => setDetailUser(u)}
                                      >
                                        Chi tiết
                                      </button>
                                      <button
                                        type="button"
                                        className={`btn-admin-dots${isMenuOpen ? " is-open" : ""}`}
                                        data-admin-menu-btn-id={u.id}
                                        aria-label={`Mở menu thao tác quản trị cho ${u.name}`}
                                        aria-haspopup="menu"
                                        aria-expanded={isMenuOpen}
                                        title="Thao tác quản trị (⋯)"
                                        onClick={(e) => handleOpenDotsMenu(u, e)}
                                      >
                                        ⋯
                                      </button>
                                    </div>
                                  </td>
                                </tr>
                              );
                            })
                          )}
                        </tbody>
                      </table>
                    </div>

                    <AdminAccountsPaginationBar
                      totalItems={totalFiltered}
                      pageSize={pageSize}
                      currentPage={safePage}
                      pageSizeOpen={pageSizeOpen}
                      onTogglePageSize={(e) => {
                        e.stopPropagation();
                        setPageSizeOpen((v) => !v);
                      }}
                      onSelectPageSize={(sz) => {
                        setPageSize(sz);
                        setCurrentPage(1);
                        setPageSizeOpen(false);
                      }}
                      onPageChange={setCurrentPage}
                    />
                  </div>
                </>
              ) : adminTab === "analytics" ? (
                <>
                  <div className="admin-page-head-group" id="admin-page-head-group">
                    <h1 className="admin-content-page-title" id="admin-page-title">
                      Thống kê
                    </h1>
                    <p className="admin-page-intro" id="admin-page-intro">
                      Theo dõi lưu lượng phân tích AI, tỷ lệ xử lý thành công và thời gian phản hồi trong 7 ngày qua.
                    </p>
                  </div>

                  <div className="admin-kpi-grid admin-analytics-kpi-grid" id="admin-analytics-kpi-grid">
                    <div className="admin-kpi-card">
                      <div className="admin-kpi-lbl">
                        <span>Tổng lượt phân tích</span>
                        <span className="role-chip student">7 ngày</span>
                      </div>
                      <div className="admin-kpi-val">
                        {overviewStats.analyses7d.toLocaleString("vi-VN")}
                      </div>
                      <div className="admin-kpi-sub">
                        {overviewStats.analyses7d > 0
                          ? "Tổng yêu cầu phân tích trong 7 ngày qua"
                          : "Chưa phát sinh lượt phân tích trong 7 ngày qua"}
                      </div>
                    </div>

                    <div className="admin-kpi-card">
                      <div className="admin-kpi-lbl">
                        <span>Tỷ lệ thành công</span>
                        <span
                          className={
                            overviewStats.analyses7d > 0 ? "role-chip teacher" : "role-chip neutral"
                          }
                        >
                          {overviewStats.analyses7d > 0 ? "Kiểm chứng tất định" : "Chưa có mẫu"}
                        </span>
                      </div>
                      <div
                        className={`admin-kpi-val${overviewStats.analyses7d > 0 ? "" : " is-empty-dash"}`}
                      >
                        {overviewStats.analyses7d > 0
                          ? `${((overviewStats.succeeded7d / overviewStats.analyses7d) * 100).toLocaleString(
                              "vi-VN",
                              { maximumFractionDigits: 1 },
                            )}%`
                          : "—"}
                      </div>
                      <div className="admin-kpi-sub">
                        {overviewStats.analyses7d > 0
                          ? `${overviewStats.succeeded7d.toLocaleString("vi-VN")} thành công · ${overviewStats.refused7d.toLocaleString("vi-VN")} từ chối${overviewStats.failed7d > 0 ? ` · ${overviewStats.failed7d.toLocaleString("vi-VN")} lỗi xử lý` : ""}`
                          : "Chưa có mẫu đánh giá trong 7 ngày qua"}
                      </div>
                    </div>

                    <div className="admin-kpi-card">
                      <div className="admin-kpi-lbl">
                        <span>Thời gian phản hồi TB</span>
                        <span
                          className={
                            overviewStats.avgLatency7dMs !== null
                              ? "role-chip student"
                              : "role-chip neutral"
                          }
                        >
                          {overviewStats.avgLatency7dMs !== null ? "7 ngày" : "Chưa có mẫu"}
                        </span>
                      </div>
                      <div
                        className={`admin-kpi-val${overviewStats.avgLatency7dMs !== null ? "" : " is-empty-dash"}`}
                      >
                        {formatAdminLatency(overviewStats.avgLatency7dMs) ?? "—"}
                      </div>
                      <div className="admin-kpi-sub">
                        {overviewStats.avgLatency7dMs !== null
                          ? "Trung bình mỗi yêu cầu trong 7 ngày qua"
                          : "Chưa có mẫu đo thời gian phản hồi"}
                      </div>
                    </div>
                  </div>

                  <div className="admin-panel-card" id="admin-analytics-panel">
                    <div className="admin-analytics-chart-frame" id="admin-analytics-chart-frame">
                      <div className="admin-analytics-chart-head">
                        <h2 className="admin-analytics-chart-title">
                          Biểu đồ số lượt phân tích AI &amp; từ chối an toàn theo ngày
                        </h2>
                        <div className="admin-analytics-legend" aria-label="Chú giải nhóm dữ liệu biểu đồ">
                          <span className="admin-chart-legend-item">
                            <span className="admin-chart-swatch is-succeeded" aria-hidden="true" />
                            <span>Xử lý thành công</span>
                          </span>
                          <span className="admin-chart-legend-item">
                            <span className="admin-chart-swatch is-refused" aria-hidden="true" />
                            <span>Từ chối an toàn</span>
                          </span>
                        </div>
                      </div>

                      {!analyticsChartModel.hasActivity ? (
                        <div
                          className="admin-analytics-chart-empty"
                          id="admin-analytics-chart-empty"
                          role="status"
                        >
                          Chưa có hoạt động phân tích trong 7 ngày qua.
                        </div>
                      ) : (
                        <>
                          <div
                            className="admin-analytics-plot-wrap"
                            id="admin-analytics-bar-chart"
                            role="region"
                            aria-label="Biểu đồ cột yêu cầu phân tích theo ngày trong 7 ngày qua"
                            onKeyDown={(e) => {
                              if (e.key === "Escape") {
                                setActiveChartDayIso(null);
                              }
                            }}
                          >
                            <div className="admin-analytics-plot-stage">
                              <div className="admin-chart-yaxis" aria-hidden="true">
                                <span className="admin-chart-yaxis-tick is-top">
                                  {analyticsChartModel.yTicks[0].toLocaleString("vi-VN")}
                                </span>
                                <span className="admin-chart-yaxis-tick is-mid">
                                  {analyticsChartModel.yTicks[1].toLocaleString("vi-VN")}
                                </span>
                                <span className="admin-chart-yaxis-tick is-zero">0</span>
                              </div>

                              <div className="admin-chart-stage">
                                <div className="admin-chart-canvas">
                                  <div className="admin-chart-gridline is-top" aria-hidden="true" />
                                  <div className="admin-chart-gridline is-mid" aria-hidden="true" />

                                  {(() => {
                                    const activeIndex = analyticsChartModel.days.findIndex(
                                      (d) => d.dateIso === activeChartDayIso,
                                    );
                                    if (activeIndex < 0) return null;
                                    const activeDay = analyticsChartModel.days[activeIndex];
                                    const totalCols = analyticsChartModel.days.length;
                                    const placeOnLeft = activeIndex >= Math.ceil(totalCols / 2);
                                    const posStyle = placeOnLeft
                                      ? {
                                          right: `calc(${((totalCols - activeIndex) / totalCols) * 100}% + 4px)`,
                                        }
                                      : {
                                          left: `calc(${((activeIndex + 1) / totalCols) * 100}% + 4px)`,
                                        };
                                    return (
                                      <div
                                        className="admin-chart-tooltip"
                                        id="admin-analytics-chart-tooltip"
                                        role="status"
                                        style={posStyle}
                                      >
                                        <div className="admin-chart-tooltip-date">
                                          {activeDay.weekdayShort
                                            ? `${activeDay.weekdayShort} · ${activeDay.dateLabel}`
                                            : activeDay.dateLabel}
                                        </div>
                                        <div className="admin-chart-tooltip-row">
                                          <span>Tổng yêu cầu</span>
                                          <strong>{activeDay.totalRequests.toLocaleString("vi-VN")}</strong>
                                        </div>
                                        <div className="admin-chart-tooltip-row">
                                          <span className="admin-chart-tooltip-lbl">
                                            <span className="admin-chart-swatch is-succeeded" aria-hidden="true" />
                                            <span>Xử lý thành công</span>
                                          </span>
                                          <strong>{activeDay.succeededRequests.toLocaleString("vi-VN")}</strong>
                                        </div>
                                        <div className="admin-chart-tooltip-row">
                                          <span className="admin-chart-tooltip-lbl">
                                            <span className="admin-chart-swatch is-refused" aria-hidden="true" />
                                            <span>Từ chối an toàn</span>
                                          </span>
                                          <strong>{activeDay.refusedRequests.toLocaleString("vi-VN")}</strong>
                                        </div>
                                        {activeDay.failedRequests > 0 ? (
                                          <div className="admin-chart-tooltip-row">
                                            <span className="admin-chart-tooltip-lbl">
                                              <span className="admin-chart-swatch is-failed" aria-hidden="true" />
                                              <span>Lỗi xử lý</span>
                                            </span>
                                            <strong>{activeDay.failedRequests.toLocaleString("vi-VN")}</strong>
                                          </div>
                                        ) : null}
                                      </div>
                                    );
                                  })()}

                                  <div className="admin-chart-columns">
                                    {analyticsChartModel.days.map((day) => {
                                      const isActive = activeChartDayIso === day.dateIso;
                                      return (
                                        <button
                                          key={day.dateIso}
                                          type="button"
                                          className={`admin-chart-day-btn${isActive ? " is-active" : ""}`}
                                          data-chart-date={day.dateIso}
                                          data-succeeded={day.succeededRequests}
                                          data-refused={day.refusedRequests}
                                          data-failed={day.failedRequests}
                                          data-total={day.totalRequests}
                                          aria-label={day.ariaLabel}
                                          onMouseEnter={() => setActiveChartDayIso(day.dateIso)}
                                          onMouseLeave={() =>
                                            setActiveChartDayIso((prev) =>
                                              prev === day.dateIso ? null : prev,
                                            )
                                          }
                                          onFocus={() => setActiveChartDayIso(day.dateIso)}
                                          onBlur={() =>
                                            setActiveChartDayIso((prev) =>
                                              prev === day.dateIso ? null : prev,
                                            )
                                          }
                                        >
                                          <span className="admin-chart-bar-pair" aria-hidden="true">
                                            <span className="admin-chart-bar-col is-succeeded">
                                              {day.succeededRequests > 0 ? (
                                                <span
                                                  className="admin-chart-bar-val"
                                                  style={{
                                                    bottom: `calc(${day.succeededHeightPct}% + 4px)`,
                                                  }}
                                                >
                                                  {day.succeededRequests.toLocaleString("vi-VN")}
                                                </span>
                                              ) : null}
                                              <span
                                                className="admin-chart-bar is-succeeded"
                                                style={{
                                                  height:
                                                    day.succeededRequests > 0
                                                      ? `max(3px, ${day.succeededHeightPct}%)`
                                                      : "0px",
                                                }}
                                              />
                                            </span>
                                            <span className="admin-chart-bar-col is-refused">
                                              <span
                                                className="admin-chart-bar is-refused"
                                                style={{
                                                  height:
                                                    day.refusedRequests > 0
                                                      ? `max(3px, ${day.refusedHeightPct}%)`
                                                      : "0px",
                                                }}
                                              />
                                            </span>
                                          </span>
                                        </button>
                                      );
                                    })}
                                  </div>
                                </div>

                                <div className="admin-chart-xaxis" aria-hidden="true">
                                  {analyticsChartModel.days.map((day) => (
                                    <div key={day.dateIso} className="admin-chart-xlabel">
                                      <span className="admin-chart-x-full">{day.xAxisLabel}</span>
                                      <span className="admin-chart-x-short">{day.shortDate}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="composer-sr-only">
                            <table aria-label="Bảng dữ liệu yêu cầu phân tích theo ngày trong 7 ngày qua">
                              <thead>
                                <tr>
                                  <th scope="col">Ngày</th>
                                  <th scope="col">Tổng yêu cầu</th>
                                  <th scope="col">Xử lý thành công</th>
                                  <th scope="col">Từ chối an toàn</th>
                                  <th scope="col">Lỗi xử lý</th>
                                </tr>
                              </thead>
                              <tbody>
                                {analyticsChartModel.days.map((day) => (
                                  <tr key={day.dateIso}>
                                    <td>{day.dateLabel}</td>
                                    <td>{day.totalRequests}</td>
                                    <td>{day.succeededRequests}</td>
                                    <td>{day.refusedRequests}</td>
                                    <td>{day.failedRequests}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </>
                      )}
                    </div>

                    {analyticsChartModel.hasActivity ? (
                      <div className="admin-table-wrap">
                        <table className="admin-table" id="admin-analytics-table">
                          <thead>
                            <tr>
                              {renderSortableTh(
                                "Thời gian",
                                "dateIso",
                                "desc",
                                analyticsSort,
                                toggleAnalyticsSort,
                              )}
                              {renderSortableTh(
                                "Số lượt sử dụng",
                                "totalRequests",
                                "desc",
                                analyticsSort,
                                toggleAnalyticsSort,
                              )}
                              {renderSortableTh(
                                "Token tiêu thụ",
                                "totalTokens",
                                "desc",
                                analyticsSort,
                                toggleAnalyticsSort,
                              )}
                              {renderSortableTh(
                                "Thời gian phản hồi TB",
                                "avgLatencyMs",
                                "desc",
                                analyticsSort,
                                toggleAnalyticsSort,
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            {sortedAnalyticsDays.map((day) => (
                              <tr key={day.dateIso}>
                                <td className="admin-td-tabular">
                                  <strong>
                                    {day.weekdayShort
                                      ? `${day.weekdayShort} · ${day.dateLabel}`
                                      : day.dateLabel}
                                  </strong>
                                </td>
                                <td>
                                  <strong>{day.totalRequests.toLocaleString("vi-VN")} lượt</strong>
                                  {day.totalRequests > 0 ? (
                                    <>
                                      {" "}
                                      <span className="admin-cell-sub-inline">
                                        {`(${day.succeededRequests.toLocaleString("vi-VN")} thành công · ${day.refusedRequests.toLocaleString("vi-VN")} từ chối${day.failedRequests > 0 ? ` · ${day.failedRequests.toLocaleString("vi-VN")} lỗi xử lý` : ""})`}
                                      </span>
                                    </>
                                  ) : null}
                                </td>
                                <td className="admin-td-tabular">
                                  {day.tokensMeasured && day.totalTokens !== null ? (
                                    `${day.totalTokens.toLocaleString("vi-VN")} tokens`
                                  ) : day.totalRequests === 0 ? (
                                    <span className="admin-cell-sub-inline">—</span>
                                  ) : (
                                    <span className="admin-cell-sub-inline">Chưa đo</span>
                                  )}
                                </td>
                                <td className="admin-td-tabular">
                                  {day.avgLatencyMs !== null ? (
                                    formatAdminLatency(day.avgLatencyMs)
                                  ) : (
                                    <span className="admin-cell-sub-inline">—</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : null}
                  </div>
                </>
              ) : (
                <>
                  <div className="admin-page-head-row" id="admin-audit-head-row">
                    <div className="admin-page-head-group" id="admin-page-head-group">
                      <h1 className="admin-content-page-title" id="admin-page-title">
                        Nhật ký quản trị
                      </h1>
                      <p className="admin-page-intro" id="admin-page-intro">
                        Tra cứu lịch sử các thay đổi về phân quyền, trạng thái tài khoản và thiết lập hệ thống.
                      </p>
                    </div>
                    <div className="admin-head-actions">
                      <button
                        type="button"
                        className="btn-admin-export"
                        id="btn-admin-export-audit"
                        onClick={() =>
                          void handleExportCsv(
                            "/api/admin/export/audit-logs",
                            "axo-nhat-ky-quan-tri.csv",
                          )
                        }
                      >
                        Xuất nhật ký CSV
                      </button>
                    </div>
                  </div>

                  <div className="admin-panel-card">
                    <div className="admin-audit-meta-row" id="admin-audit-meta-row">
                      <span>
                        Tổng cộng <strong>{auditLogs.length}</strong> bản ghi · Mặc định hiển thị{" "}
                        <strong>hoạt động mới nhất trước</strong>
                      </span>
                      <span>Nhấn vào tiêu đề cột để đổi chiều sắp xếp</span>
                    </div>
                    <div className="admin-table-wrap">
                      <table className="admin-table" id="admin-audit-table">
                        <thead>
                          <tr>
                            {renderSortableTh("Thời gian", "timeTs", "desc", auditSort, toggleAuditSort)}
                            {renderSortableTh("Quản trị viên", "actor", "asc", auditSort, toggleAuditSort)}
                            {renderSortableTh("Thao tác", "action", "asc", auditSort, toggleAuditSort)}
                            {renderSortableTh("Tài khoản / Đối tượng", "target", "asc", auditSort, toggleAuditSort)}
                            <th>Chi tiết thay đổi</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sortedAuditLogs.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="admin-table-empty">
                                Chưa ghi nhận thao tác quản trị nào.
                              </td>
                            </tr>
                          ) : (
                            sortedAuditLogs.map((log) => (
                              <tr key={log.id}>
                                <td>{log.time || log.timestamp || "—"}</td>
                                <td>
                                  <code>{log.actor}</code>
                                </td>
                                <td>
                                  <strong>{log.action}</strong>
                                </td>
                                <td>{log.target}</td>
                                <td>{log.detail}</td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* P2: Floating Three-Dots Context Menu */}
      <div
        className={`admin-floating-dots-menu${dotsTargetUser ? " open" : ""}${dotsMenu?.flippedUp ? " flipped-up" : ""}`}
        id="admin-floating-dots-menu"
        role="menu"
        aria-label="Thao tác quản trị tài khoản"
        style={dotsMenu ? { left: `${dotsMenu.left}px`, top: `${dotsMenu.top}px` } : undefined}
      >
        {dotsTargetUser && (
          <>
            <div className="admin-dots-menu-head">
              <div className="admin-dots-menu-name">{dotsTargetUser.name}</div>
              <div className="admin-dots-menu-email">{dotsTargetUser.email}</div>
            </div>
            {dotsTargetUser.role === "student" && (
              <button
                type="button"
                className="admin-dots-menu-item approve-item"
                role="menuitem"
                data-dots-act="grant_teacher"
                onClick={() => {
                  setDotsMenu(null);
                  setConfirmAction({ type: "grant_teacher", user: dotsTargetUser });
                }}
              >
                <span className="menu-item-ico" aria-hidden="true">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    <polyline points="9 12 11 14 15 10" />
                  </svg>
                </span>
                <span>Cấp quyền Giáo viên ({quotaConfig.teacherDailyRequests} lượt/ngày)</span>
              </button>
            )}
            {dotsTargetUser.role === "teacher" && (
              <button
                type="button"
                className="admin-dots-menu-item"
                role="menuitem"
                data-dots-act="revert_student"
                onClick={() => {
                  setDotsMenu(null);
                  setConfirmAction({ type: "revert_student", user: dotsTargetUser });
                }}
              >
                <span className="menu-item-ico" aria-hidden="true">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <polyline points="1 4 1 10 7 10" />
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                  </svg>
                </span>
                <span>Chuyển về Học sinh ({quotaConfig.studentDailyRequests} lượt/ngày)</span>
              </button>
            )}
            <button
              type="button"
              className="admin-dots-menu-item"
              role="menuitem"
              data-dots-act="adjust_quota"
              onClick={() => {
                setDotsMenu(null);
                setQuotaModalUser(dotsTargetUser);
                setQuotaInputVal(String(dotsTargetUser.dailyLimit));
              }}
            >
              <span className="menu-item-ico" aria-hidden="true">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <line x1="4" y1="21" x2="4" y2="14" />
                  <line x1="4" y1="10" x2="4" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12" y2="3" />
                  <line x1="20" y1="21" x2="20" y2="16" />
                  <line x1="20" y1="12" x2="20" y2="3" />
                  <line x1="1" y1="14" x2="7" y2="14" />
                  <line x1="9" y1="8" x2="15" y2="8" />
                  <line x1="17" y1="16" x2="23" y2="16" />
                </svg>
              </span>
              <span>Điều chỉnh hạn mức AI</span>
            </button>
            <button
              type="button"
              className="admin-dots-menu-item"
              role="menuitem"
              data-dots-act="reset_password"
              onClick={() => {
                setDotsMenu(null);
                setConfirmAction({ type: "reset_password", user: dotsTargetUser });
              }}
            >
              <span className="menu-item-ico" aria-hidden="true">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <rect x="3" y="5" width="18" height="14" rx="2" />
                  <polyline points="3 7 12 13 21 7" />
                </svg>
              </span>
              <span>Yêu cầu đặt lại mật khẩu</span>
            </button>
            <div className="admin-dots-menu-sep" role="separator" />
            {dotsTargetUser.role !== "admin" ? (
              <>
                <button
                  type="button"
                  className={`admin-dots-menu-item ${dotsTargetUser.status === "locked" ? "approve-item" : "warn-item"}`}
                  role="menuitem"
                  data-dots-act={dotsTargetUser.status === "locked" ? "unlock" : "lock"}
                  onClick={() => {
                    setDotsMenu(null);
                    setConfirmAction({
                      type: dotsTargetUser.status === "locked" ? "unlock" : "lock",
                      user: dotsTargetUser,
                    });
                  }}
                >
                  <span className="menu-item-ico" aria-hidden="true">
                    {dotsTargetUser.status === "locked" ? (
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                        <path d="M7 11V7a5 5 0 0 1 9.9-1" />
                      </svg>
                    ) : (
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                      </svg>
                    )}
                  </span>
                  <span>
                    {dotsTargetUser.status === "locked"
                      ? "Mở khóa tài khoản"
                      : "Khóa tạm thời tài khoản"}
                  </span>
                </button>
                <button
                  type="button"
                  className="admin-dots-menu-item danger-item"
                  role="menuitem"
                  data-dots-act="delete_account"
                  onClick={() => {
                    setDotsMenu(null);
                    setConfirmAction({ type: "delete_account", user: dotsTargetUser });
                  }}
                >
                  <span className="menu-item-ico" aria-hidden="true">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      <line x1="10" y1="11" x2="10" y2="17" />
                      <line x1="14" y1="11" x2="14" y2="17" />
                    </svg>
                  </span>
                  <span>Xóa tài khoản</span>
                </button>
              </>
            ) : (
              <button
                type="button"
                className="admin-dots-menu-item"
                role="menuitem"
                disabled
                aria-disabled="true"
              >
                <span className="menu-item-ico" aria-hidden="true">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                </span>
                <span>Admin đang đăng nhập (Được bảo vệ)</span>
              </button>
            )}
          </>
        )}
      </div>

      {/* Admin Action Toast */}
      <div
        className={`admin-action-toast${actionToast ? " visible" : ""}`}
        id="admin-action-toast"
        role="status"
        aria-live="polite"
      >
        <span id="admin-action-toast-text">{actionToast}</span>
        <button
          type="button"
          className="admin-action-toast-close"
          id="btn-close-admin-action-toast"
          aria-label="Đóng thông báo"
          onClick={() => setActionToast("")}
        >
          ×
        </button>
      </div>

      {/* Modal: Chi tiết tài khoản (#admin-user-modal — 3 Sections) */}
      <div
        className={`axo-modal-backdrop${detailUser ? " open" : ""}`}
        id="admin-user-modal"
        role="dialog"
        aria-modal="true"
        aria-hidden={!detailUser}
        aria-label="Chi tiết tài khoản"
        onClick={(e) => {
          if (e.target === e.currentTarget) setDetailUser(null);
        }}
      >
        <div className="axo-modal-dialog">
          <div className="axo-modal-head">
            <span className="axo-modal-title" id="admin-user-modal-title">
              {detailUser ? `Chi tiết tài khoản: ${detailUser.name}` : "Chi tiết tài khoản"}
            </span>
            <button
              type="button"
              className="context-close-icon-btn"
              id="btn-close-admin-user-modal"
              aria-label="Đóng chi tiết tài khoản"
              onClick={() => setDetailUser(null)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <div className="axo-modal-body" id="admin-user-modal-body">
            {detailUser && (() => {
              const roleName =
                detailUser.role === "admin"
                  ? "Quản trị viên"
                  : detailUser.role === "teacher"
                    ? "Giáo viên"
                    : "Học sinh";
              const defaultRoleLimit =
                detailUser.role === "admin"
                  ? 200
                  : detailUser.role === "teacher"
                    ? quotaConfig.teacherDailyRequests
                    : quotaConfig.studentDailyRequests;
              return (
                <>
                  <section
                    className="user-detail-section soft-bg"
                    id="user-detail-sec-info"
                    aria-label="1. Thông tin tài khoản"
                  >
                    <div className="user-detail-sec-head">
                      <span className="user-detail-sec-title">1. Thông tin tài khoản</span>
                      <span className={`role-chip ${detailUser.role}`}>{roleName}</span>
                    </div>
                    <div className="user-detail-info-grid">
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Họ tên</span>
                        <div className="user-detail-kv-val" id="detail-user-name">
                          {detailUser.name}
                        </div>
                      </div>
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Email</span>
                        <div className="user-detail-kv-val" id="detail-user-email">
                          {detailUser.email}
                        </div>
                      </div>
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Trường / Đơn vị</span>
                        <div className="user-detail-kv-val" id="detail-user-school">
                          {detailUser.school}
                        </div>
                      </div>
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Vai trò</span>
                        <div className="user-detail-kv-val" id="detail-user-role">
                          <span className={`role-chip ${detailUser.role}`}>{roleName}</span>
                        </div>
                      </div>
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Ngày đăng ký</span>
                        <div className="user-detail-kv-val" id="detail-user-joined">
                          {detailUser.joinedAt}
                        </div>
                      </div>
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Trạng thái hoạt động</span>
                        <div className="user-detail-kv-val" id="detail-user-status">
                          {detailUser.status === "verified" ? (
                            <span className="role-chip teacher">Đã xác minh</span>
                          ) : detailUser.status === "pending_teacher" ? (
                            <span className="role-chip pending">Chờ cấp quyền GV</span>
                          ) : detailUser.status === "pending_activation" ? (
                            <span className="role-chip pending-activation">Chờ kích hoạt</span>
                          ) : detailUser.status === "locked" ? (
                            <span className="role-chip locked">Đã khóa</span>
                          ) : (
                            <span className="role-chip student">Hoạt động</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </section>

                  <section
                    className="user-detail-section"
                    id="user-detail-sec-ai"
                    aria-label="2. Sử dụng AI"
                  >
                    <div className="user-detail-sec-head">
                      <span className="user-detail-sec-title">2. Sử dụng AI</span>
                      <span className="user-detail-sec-sub">
                        Mặc định vai trò {roleName}: {defaultRoleLimit} lượt/ngày
                      </span>
                    </div>
                    <div className="user-detail-info-grid">
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Hạn mức hiện tại</span>
                        <div className="user-detail-kv-val" id="detail-ai-daily-limit">
                          {detailUser.dailyLimit} lượt/ngày
                        </div>
                      </div>
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Lượt đã dùng hôm nay</span>
                        <div className="user-detail-kv-val" id="detail-ai-used-today">
                          {detailUser.usedToday} / {detailUser.dailyLimit} lượt
                        </div>
                      </div>
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Token tiêu thụ</span>
                        <div className="user-detail-kv-val" id="detail-ai-tokens-today">
                          {detailUser.tokensToday}
                        </div>
                      </div>
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Trạng thái sử dụng</span>
                        <div className="user-detail-kv-val" id="detail-ai-usage-state">
                          {detailUser.status === "locked" ? (
                            <span className="role-chip locked">Tạm dừng (Tài khoản đang khóa)</span>
                          ) : detailUser.status === "pending_activation" ? (
                            <span className="role-chip pending-activation">Chờ kích hoạt lần đầu</span>
                          ) : detailUser.usedToday >= detailUser.dailyLimit ? (
                            <span className="role-chip pending">Đã dùng hết hạn mức hôm nay</span>
                          ) : (
                            <span className="role-chip student">
                              Đang trong hạn mức (Còn {Math.max(0, detailUser.dailyLimit - detailUser.usedToday)} lượt)
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </section>

                  <section
                    className="user-detail-section"
                    id="user-detail-sec-governance"
                    aria-label="3. Trạng thái quản trị"
                  >
                    <div className="user-detail-sec-head">
                      <span className="user-detail-sec-title">3. Trạng thái quản trị</span>
                      <span className="user-detail-sec-sub">Thao tác thực hiện tại menu ⋯</span>
                    </div>
                    <div className="user-detail-info-grid">
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Tình trạng xác minh Giáo viên</span>
                        <div className="user-detail-kv-val" id="detail-gov-teacher-verify">
                          {detailUser.role === "teacher" ? (
                            <span className="role-chip teacher">Đã xác minh Giáo viên</span>
                          ) : detailUser.status === "pending_teacher" ? (
                            <span className="role-chip pending">Đang chờ duyệt GV</span>
                          ) : detailUser.role === "admin" ? (
                            <span className="role-chip admin">Quản trị viên hệ thống</span>
                          ) : (
                            <span className="role-chip student">Chưa gửi yêu cầu (Học sinh)</span>
                          )}
                        </div>
                      </div>
                      <div className="user-detail-kv">
                        <span className="user-detail-kv-lbl">Trạng thái khóa tài khoản</span>
                        <div className="user-detail-kv-val" id="detail-gov-lock-state">
                          {detailUser.status === "locked" ? (
                            <span className="role-chip locked">Đang khóa tạm thời</span>
                          ) : (
                            <span className="role-chip student">Không bị khóa (Bình thường)</span>
                          )}
                        </div>
                      </div>
                      <div className="user-detail-kv full-span">
                        <span className="user-detail-kv-lbl">Yêu cầu đặt lại mật khẩu gần nhất</span>
                        <div className="user-detail-kv-val" id="detail-gov-reset-state">
                          {detailUser.passwordResetRequestedAt ? (
                            <span className="detail-reset-requested">
                              Đã ghi nhận yêu cầu lúc {detailUser.passwordResetRequestedAt}
                            </span>
                          ) : (
                            <span className="detail-reset-none">Chưa có yêu cầu đặt lại mật khẩu</span>
                          )}
                        </div>
                      </div>
                      {detailUser.adminNote && (
                        <div className="user-detail-kv full-span">
                          <span className="user-detail-kv-lbl">Ghi chú quản trị</span>
                          <div className="user-detail-kv-val" id="detail-gov-admin-note">
                            {detailUser.adminNote}
                          </div>
                        </div>
                      )}
                    </div>
                  </section>

                  <div className="acc-modal-actions-row">
                    <button
                      type="button"
                      className="btn-confirm-cancel"
                      id="btn-modal-close-footer"
                      onClick={() => setDetailUser(null)}
                    >
                      Đóng
                    </button>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      </div>

      {/* Modal: Xác nhận thao tác quản trị (#admin-confirm-modal) */}
      <div
        className={`axo-modal-backdrop${confirmAction ? " open" : ""}`}
        id="admin-confirm-modal"
        role="dialog"
        aria-modal="true"
        aria-hidden={!confirmAction}
        aria-label="Xác nhận thao tác quản trị"
        onClick={(e) => {
          if (e.target === e.currentTarget) setConfirmAction(null);
        }}
      >
        <div className="axo-modal-dialog">
          <div className="axo-modal-head">
            <span className="axo-modal-title" id="admin-confirm-modal-title">
              Xác nhận thao tác
            </span>
            <button
              type="button"
              className="context-close-icon-btn"
              id="btn-close-admin-confirm-modal"
              aria-label="Đóng hộp xác nhận"
              onClick={() => setConfirmAction(null)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <div className="axo-modal-body">
            <p id="admin-confirm-modal-desc">
              {confirmAction
                ? `Bạn có chắc chắn muốn thực hiện thao tác quản trị cho tài khoản ${confirmAction.user.name} (${confirmAction.user.email})?`
                : ""}
            </p>
            <div className="acc-modal-actions-row">
              <button
                type="button"
                className="btn-confirm-cancel"
                id="btn-admin-confirm-cancel"
                onClick={() => setConfirmAction(null)}
              >
                Hủy
              </button>
              <button
                type="button"
                className="btn-confirm-danger"
                id="btn-admin-confirm-ok"
                onClick={() => void handleExecuteConfirm()}
              >
                Xác nhận
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Modal: Tạo tài khoản mới thủ công (#admin-create-user-modal) */}
      <div
        className={`axo-modal-backdrop${createUserOpen ? " open" : ""}`}
        id="admin-create-user-modal"
        role="dialog"
        aria-modal="true"
        aria-hidden={!createUserOpen}
        aria-labelledby="admin-create-user-modal-title"
        onClick={(e) => {
          if (e.target === e.currentTarget) setCreateUserOpen(false);
        }}
      >
        <div className="axo-modal-dialog">
          <div className="axo-modal-head">
            <span className="axo-modal-title" id="admin-create-user-modal-title">
              Tạo tài khoản mới
            </span>
            <button
              type="button"
              className="context-close-icon-btn"
              id="btn-close-create-user-modal"
              aria-label="Đóng tạo tài khoản mới"
              onClick={() => setCreateUserOpen(false)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <div className="axo-modal-body" id="admin-create-user-modal-body">
            <div className="confirm-policy-note info-tone" id="create-user-default-role-note">
              Tài khoản mới mặc định có vai trò <strong>Học sinh</strong> ({quotaConfig.studentDailyRequests} lượt AI/ngày) và trạng thái{" "}
              <strong>Chờ kích hoạt</strong>.
            </div>
            <form
              className="auth-form"
              id="form-admin-create-user"
              noValidate
              onSubmit={(e) => void handleCreateUserSubmit(e)}
            >
              <div className="auth-field">
                <label className="auth-label" htmlFor="inp-create-user-name">
                  Họ và tên *
                </label>
                <input
                  type="text"
                  id="inp-create-user-name"
                  className="auth-input"
                  placeholder="Nhập họ và tên"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  autoComplete="off"
                />
              </div>
              <div className="auth-field">
                <label className="auth-label" htmlFor="inp-create-user-email">
                  Email *
                </label>
                <input
                  type="email"
                  id="inp-create-user-email"
                  className="auth-input"
                  placeholder="Nhập địa chỉ email"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  autoComplete="off"
                />
              </div>
              <div className="auth-field">
                <label className="auth-label" htmlFor="inp-create-user-school">
                  Trường học / Đơn vị công tác (tùy chọn)
                </label>
                <input
                  type="text"
                  id="inp-create-user-school"
                  className="auth-input"
                  placeholder="Ví dụ: THPT Chu Văn An"
                  value={newUserSchool}
                  onChange={(e) => setNewUserSchool(e.target.value)}
                  autoComplete="off"
                />
              </div>
              <div className="auth-field">
                <label className="auth-label" htmlFor="inp-create-user-note">
                  Ghi chú quản trị (tùy chọn)
                </label>
                <textarea
                  id="inp-create-user-note"
                  className="auth-textarea"
                  placeholder="Ghi chú nội bộ phục vụ quản lý hồ sơ (người dùng không xem mục này)..."
                  value={newUserNote}
                  onChange={(e) => setNewUserNote(e.target.value)}
                />
              </div>
              {createUserErr && (
                <div className="field-inline-error visible" role="alert">
                  {createUserErr}
                </div>
              )}
              <div className="acc-modal-actions-row">
                <button
                  type="button"
                  className="btn-confirm-cancel"
                  id="btn-cancel-create-user"
                  onClick={() => setCreateUserOpen(false)}
                >
                  Hủy
                </button>
                <button type="submit" className="btn-auth-primary" id="btn-submit-create-user">
                  Tạo tài khoản
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Modal: Nhập danh sách từ Excel (#admin-bulk-import-modal — 4 Steps) */}
      <div
        className={`axo-modal-backdrop${bulkImportOpen ? " open" : ""}`}
        id="admin-bulk-import-modal"
        role="dialog"
        aria-modal="true"
        aria-hidden={!bulkImportOpen}
        aria-labelledby="admin-bulk-import-modal-title"
        onClick={(e) => {
          if (e.target === e.currentTarget) setBulkImportOpen(false);
        }}
      >
        <div className="axo-modal-dialog bulk-import-dialog">
          <div className="axo-modal-head">
            <span className="axo-modal-title" id="admin-bulk-import-modal-title">
              Nhập danh sách tài khoản từ Excel / CSV
            </span>
            <button
              type="button"
              className="context-close-icon-btn"
              id="btn-close-bulk-import-modal"
              aria-label="Đóng nhập danh sách từ Excel"
              onClick={() => setBulkImportOpen(false)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <div className="axo-modal-body" id="admin-bulk-import-modal-body">
            <div className="bulk-stepper" id="bulk-import-stepper" role="navigation" aria-label="Các bước nhập danh sách tài khoản">
              {[
                { id: 1, label: "Bước 1. Chọn tệp" },
                { id: 2, label: "Bước 2. Kiểm tra dữ liệu" },
                { id: 3, label: "Bước 3. Xem trước" },
                { id: 4, label: "Bước 4. Xác nhận" },
              ].map((s) => {
                const isDone = bulkStep === "result" || (typeof bulkStep === "number" && bulkStep > s.id);
                const isActive = bulkStep === s.id;
                return (
                  <div
                    key={s.id}
                    className={`bulk-step-pill${isActive ? " is-active" : ""}${isDone ? " is-done" : ""}`}
                    data-step-indicator={s.id}
                  >
                    <span className="bulk-step-num">
                      {isDone ? (
                        <svg viewBox="0 0 24 24" aria-hidden="true" width="11" height="11">
                          <polyline points="20 6 9 17 4 12" fill="none" stroke="currentColor" strokeWidth="2.5" />
                        </svg>
                      ) : (
                        s.id
                      )}
                    </span>
                    <span>{s.label}</span>
                  </div>
                );
              })}
            </div>

            {bulkStep === 1 && (
              <div className="bulk-step-panel is-active" id="bulk-step-1">
                <div className="confirm-policy-note info-tone" id="bulk-step1-policy-note">
                  Tệp danh sách gồm 3 cột bắt buộc: <code>Họ và tên</code>, <code>Email</code>, <code>Trường/Đơn vị</code>. Tài khoản hợp lệ sau khi nhập mặc định có vai trò <strong>Học sinh</strong> và trạng thái <strong>Chờ kích hoạt</strong> (không gửi email tự động).
                </div>

                <input
                  ref={bulkFileInputRef}
                  type="file"
                  id="inp-bulk-file-upload"
                  accept=".csv,.xlsx"
                  style={{ display: "none" }}
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) void handleBulkFileObject(f);
                  }}
                />

                <div
                  className={`bulk-dropzone${bulkDragOver ? " is-dragover" : ""}${bulkFileName ? " has-file" : ""}`}
                  id="bulk-dropzone"
                  role="button"
                  tabIndex={0}
                  aria-label="Kéo thả hoặc chọn tệp CSV hoặc Excel từ thiết bị"
                  onClick={() => {
                    if (bulkFileInputRef.current) {
                      bulkFileInputRef.current.click();
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      bulkFileInputRef.current?.click();
                    }
                  }}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setBulkDragOver(true);
                  }}
                  onDragLeave={(e) => {
                    e.preventDefault();
                    setBulkDragOver(false);
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    setBulkDragOver(false);
                    const f = e.dataTransfer?.files?.[0];
                    if (f) void handleBulkFileObject(f);
                  }}
                >
                  <svg viewBox="0 0 24 24" className="bulk-dropzone-icon" aria-hidden="true">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  <div className="bulk-dropzone-title">
                    Kéo thả tệp vào đây hoặc bấm để chọn tệp từ thiết bị
                  </div>
                  <div className="bulk-dropzone-sub">
                    Hỗ trợ định dạng <strong>.csv</strong> (phân tích trực tiếp) và <strong>.xlsx</strong> · Dung lượng tối đa 2 MB (500 bản ghi)
                  </div>
                </div>

                {bulkFileName && (
                  <div className="bulk-selected-file-card" id="bulk-selected-file-card">
                    <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
                      <span className="role-chip teacher" id="bulk-file-ext-badge">
                        {bulkFileExt || "CSV"}
                      </span>
                      <div style={{ minWidth: 0 }}>
                        <div
                          id="bulk-file-name-txt"
                          style={{
                            fontWeight: 700,
                            color: "var(--ink)",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {bulkFileName}
                        </div>
                        <div id="bulk-file-meta-txt" style={{ fontSize: 11, color: "var(--ink-muted)" }}>
                          {bulkFileSize} · Đọc được {bulkRows.length} dòng dữ liệu
                        </div>
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <button
                        type="button"
                        className="btn-admin-sm"
                        id="btn-bulk-replace-file"
                        onClick={() => {
                          if (bulkFileInputRef.current) {
                            bulkFileInputRef.current.value = "";
                            bulkFileInputRef.current.click();
                          }
                        }}
                      >
                        Thay tệp khác
                      </button>
                      <button
                        type="button"
                        className="btn-admin-sm danger"
                        id="btn-bulk-clear-file"
                        onClick={() => {
                          setBulkFileName("");
                          setBulkFileSize("");
                          setBulkFileExt("");
                          setBulkRows([]);
                          setBulkErrorMsg("");
                          if (bulkFileInputRef.current) bulkFileInputRef.current.value = "";
                        }}
                      >
                        Gỡ tệp
                      </button>
                    </div>
                  </div>
                )}

                {bulkErrorMsg && (
                  <div className="confirm-policy-note danger-tone" id="bulk-step1-error" role="alert">
                    {bulkErrorMsg}
                  </div>
                )}

                <div className="bulk-presets-box" id="bulk-presets-box">
                  <div className="bulk-presets-row">
                    <span style={{ fontWeight: 600, color: "var(--ink-secondary)" }}>
                      Tệp mẫu nhập liệu chuẩn (3 cột):
                    </span>
                    <button
                      type="button"
                      className="btn-admin-sm"
                      id="btn-bulk-step1-download-template"
                      onClick={handleDownloadSampleCsv}
                    >
                      Tải tệp mẫu (.csv)
                    </button>
                  </div>
                </div>

                <div className="bulk-modal-foot">
                  <button
                    type="button"
                    className="btn-confirm-cancel"
                    id="btn-bulk-step1-cancel"
                    onClick={() => setBulkImportOpen(false)}
                  >
                    Hủy
                  </button>
                  <button
                    type="button"
                    className="btn-auth-primary"
                    id="btn-bulk-step1-next"
                    disabled={bulkRows.length === 0}
                    onClick={() => {
                      setBulkFilter("all");
                      setBulkPreviewPage(1);
                      setBulkStep(2);
                    }}
                  >
                    Tiếp tục: Kiểm tra dữ liệu →
                  </button>
                </div>
              </div>
            )}

            {bulkStep === 2 &&
              (() => {
                const cValid = bulkRows.filter((r) => r.category === "valid").length;
                const cMissing = bulkRows.filter((r) => r.category === "missing_info").length;
                const cInvalidEmail = bulkRows.filter((r) => r.category === "invalid_email").length;
                const cDupFile = bulkRows.filter((r) => r.category === "duplicate_in_file").length;
                const cExisting = bulkRows.filter((r) => r.category === "existing_email").length;
                const cOther = bulkRows.filter((r) => r.category === "other_invalid").length;
                const totalErr = bulkRows.length - cValid;
                const bannerTone =
                  totalErr === 0 ? "info-tone" : cValid === 0 ? "danger-tone" : "warn-tone";
                return (
                  <div className="bulk-step-panel is-active" id="bulk-step-2">
                    <div className="bulk-selected-file-card">
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span className="role-chip teacher" id="bulk-step2-file-badge">
                          {bulkFileExt || "CSV"}
                        </span>
                        <div>
                          <div id="bulk-step2-file-name" style={{ fontWeight: 700, color: "var(--ink)" }}>
                            {bulkFileName}
                          </div>
                          <div id="bulk-step2-file-total" style={{ fontSize: 11, color: "var(--ink-muted)" }}>
                            Tổng số dòng đọc được: {bulkRows.length} dòng
                          </div>
                        </div>
                      </div>
                      <button
                        type="button"
                        className="btn-admin-sm"
                        id="btn-bulk-step2-change-file"
                        onClick={() => setBulkStep(1)}
                      >
                        Chọn lại tệp
                      </button>
                    </div>

                    <div className="bulk-cat-grid" id="bulk-step2-cat-grid">
                      <div className="bulk-cat-card ok-tone">
                        <span className="bulk-cat-lbl">1. Dòng hợp lệ</span>
                        <span className="bulk-cat-val" id="bulk-cat-valid">
                          {cValid}
                        </span>
                      </div>
                      <div className={`bulk-cat-card${cMissing > 0 ? " warn-tone" : ""}`}>
                        <span className="bulk-cat-lbl">2. Dòng thiếu thông tin</span>
                        <span className="bulk-cat-val" id="bulk-cat-missing">
                          {cMissing}
                        </span>
                      </div>
                      <div className={`bulk-cat-card${cInvalidEmail > 0 ? " err-tone" : ""}`}>
                        <span className="bulk-cat-lbl">3. Email sai định dạng</span>
                        <span className="bulk-cat-val" id="bulk-cat-invalid-email">
                          {cInvalidEmail}
                        </span>
                      </div>
                      <div className={`bulk-cat-card${cDupFile > 0 ? " warn-tone" : ""}`}>
                        <span className="bulk-cat-lbl">4. Email trùng trong tệp</span>
                        <span className="bulk-cat-val" id="bulk-cat-dup-file">
                          {cDupFile}
                        </span>
                      </div>
                      <div className={`bulk-cat-card${cExisting > 0 ? " warn-tone" : ""}`}>
                        <span className="bulk-cat-lbl">5. Email đã tồn tại</span>
                        <span className="bulk-cat-val" id="bulk-cat-existing">
                          {cExisting}
                        </span>
                      </div>
                      <div className={`bulk-cat-card${cOther > 0 ? " err-tone" : ""}`}>
                        <span className="bulk-cat-lbl">6. Dòng không hợp lệ khác</span>
                        <span className="bulk-cat-val" id="bulk-cat-other">
                          {cOther}
                        </span>
                      </div>
                    </div>

                    <div className={`confirm-policy-note ${bannerTone}`} id="bulk-step2-summary-banner">
                      {totalErr === 0 ? (
                        <>
                          <strong>Kiểm tra hoàn tất:</strong> Tất cả <strong>{cValid}/{bulkRows.length}</strong> dòng đều hợp lệ và sẵn sàng xem trước.
                        </>
                      ) : cValid === 0 ? (
                        <>
                          <strong>Không có dòng hợp lệ nào:</strong> Cả <strong>{totalErr}/{bulkRows.length}</strong> dòng đều có lỗi hoặc trùng lặp. Vui lòng xem trước chi tiết lỗi hoặc chọn lại tệp.
                        </>
                      ) : (
                        <>
                          <strong>Kết quả phân loại:</strong> Có <strong>{cValid}</strong> dòng hợp lệ có thể tạo tài khoản và <strong>{totalErr}</strong> dòng có lỗi sẽ được bỏ qua khi nhập.
                        </>
                      )}
                    </div>

                    <div className="bulk-modal-foot">
                      <button
                        type="button"
                        className="btn-confirm-cancel"
                        id="btn-bulk-step2-back"
                        onClick={() => setBulkStep(1)}
                      >
                        ← Quay lại Bước 1
                      </button>
                      <button
                        type="button"
                        className="btn-auth-primary"
                        id="btn-bulk-step2-next"
                        onClick={() => {
                          setBulkFilter("all");
                          setBulkPreviewPage(1);
                          setBulkStep(3);
                        }}
                      >
                        Tiếp tục: Xem trước bảng dữ liệu →
                      </button>
                    </div>
                  </div>
                );
              })()}

            {bulkStep === 3 &&
              (() => {
                const validCount = bulkRows.filter((r) => r.isValid).length;
                const errorCount = bulkRows.length - validCount;
                const filtered = bulkRows.filter((r) =>
                  bulkFilter === "valid" ? r.isValid : bulkFilter === "error" ? !r.isValid : true,
                );
                const pageSizeStep3 = 15;
                const totalPagesStep3 = Math.max(1, Math.ceil(filtered.length / pageSizeStep3));
                const safePageStep3 = Math.min(Math.max(1, bulkPreviewPage), totalPagesStep3);
                const startIdxStep3 = (safePageStep3 - 1) * pageSizeStep3;
                const sliceStep3 = filtered.slice(startIdxStep3, startIdxStep3 + pageSizeStep3);
                const endIdxStep3 = startIdxStep3 + sliceStep3.length;
                const resetPreviewScroll = () => {
                  if (typeof document !== "undefined") {
                    const wrap = document.getElementById("bulk-preview-table-wrap");
                    if (wrap) wrap.scrollTop = 0;
                  }
                };
                return (
                  <div className="bulk-step-panel is-active" id="bulk-step-3">
                    <div className="bulk-preview-toolbar">
                      <div
                        className="bulk-filter-pills"
                        id="bulk-preview-filter-group"
                        role="group"
                        aria-label="Lọc bảng xem trước"
                      >
                        <button
                          type="button"
                          className={`bulk-filter-pill${bulkFilter === "all" ? " is-active" : ""}`}
                          data-bulk-filter="all"
                          onClick={() => {
                            setBulkFilter("all");
                            setBulkPreviewPage(1);
                            resetPreviewScroll();
                          }}
                        >
                          Tất cả ({bulkRows.length})
                        </button>
                        <button
                          type="button"
                          className={`bulk-filter-pill${bulkFilter === "valid" ? " is-active" : ""}`}
                          data-bulk-filter="valid"
                          onClick={() => {
                            setBulkFilter("valid");
                            setBulkPreviewPage(1);
                            resetPreviewScroll();
                          }}
                        >
                          Hợp lệ ({validCount})
                        </button>
                        <button
                          type="button"
                          className={`bulk-filter-pill${bulkFilter === "error" ? " is-active" : ""}`}
                          data-bulk-filter="error"
                          onClick={() => {
                            setBulkFilter("error");
                            setBulkPreviewPage(1);
                            resetPreviewScroll();
                          }}
                        >
                          Có lỗi ({errorCount})
                        </button>
                      </div>
                      <div id="bulk-preview-page-info" style={{ fontSize: 11.6, color: "var(--ink-muted)" }}>
                        Hiển thị{" "}
                        <strong>
                          {filtered.length === 0 ? 0 : `${startIdxStep3 + 1}–${endIdxStep3}`}
                        </strong>{" "}
                        / {filtered.length} dòng · Trang {safePageStep3}/{totalPagesStep3}
                      </div>
                    </div>

                    <div className="bulk-preview-table-wrap axo-custom-scroll" id="bulk-preview-table-wrap" ref={previewTableRef}>
                      <table className="bulk-preview-table" id="bulk-preview-table">
                        <thead>
                          <tr>
                            <th>Số dòng</th>
                            <th>Họ tên</th>
                            <th>Email</th>
                            <th>Trường/Đơn vị</th>
                            <th>Trạng thái</th>
                            <th>Lý do lỗi</th>
                          </tr>
                        </thead>
                        <tbody id="bulk-preview-tbody">
                          {sliceStep3.length === 0 ? (
                            <tr>
                              <td colSpan={6} style={{ textAlign: "center", padding: 18, color: "var(--ink-muted)" }}>
                                Không có bản ghi nào trong bộ lọc này.
                              </td>
                            </tr>
                          ) : (
                            sliceStep3.map((r) => (
                              <tr
                                key={r.rowNum}
                                className={r.isValid ? "" : "is-error-row"}
                                data-preview-row={r.rowNum}
                              >
                                <td
                                  style={{
                                    fontVariantNumeric: "tabular-nums",
                                    fontWeight: 600,
                                    color: "var(--ink-muted)",
                                  }}
                                >
                                  #{r.rowNum}
                                </td>
                                <td>
                                  <strong>{r.name}</strong>
                                </td>
                                <td>
                                  <code>{r.email}</code>
                                </td>
                                <td>{r.school}</td>
                                <td>
                                  {r.isValid ? (
                                    <span className="role-chip teacher">Hợp lệ</span>
                                  ) : (
                                    <span className="role-chip locked">Có lỗi</span>
                                  )}
                                </td>
                                <td
                                  style={{
                                    color: r.isValid ? "var(--ink-muted)" : "#B91C1C",
                                    fontWeight: r.isValid ? 400 : 600,
                                  }}
                                >
                                  {r.isValid ? "Mặc định Học sinh (Chờ kích hoạt)" : r.reason}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                    <AxoScrollbar targetRef={previewTableRef} />

                    <div
                      id="bulk-preview-pagination-bar"
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: 8,
                        flexWrap: "wrap",
                        fontSize: 11.6,
                        flexShrink: 0,
                      }}
                    >
                      <span id="bulk-preview-pagination-label" style={{ color: "var(--ink-muted)" }}>
                        Bảng xem trước tự động phân trang &amp; cuộn nội bộ để giữ kích thước modal ổn định.
                      </span>
                      <div style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                        <button
                          type="button"
                          className="btn-page-nav"
                          id="btn-bulk-prev-page"
                          disabled={safePageStep3 <= 1}
                          onClick={() => {
                            setBulkPreviewPage((p) => Math.max(1, p - 1));
                            resetPreviewScroll();
                          }}
                        >
                          ← Trước
                        </button>
                        <span id="bulk-preview-page-indicator" style={{ padding: "0 8px", fontWeight: 600 }}>
                          Trang {safePageStep3} / {totalPagesStep3}
                        </span>
                        <button
                          type="button"
                          className="btn-page-nav"
                          id="btn-bulk-next-page"
                          disabled={safePageStep3 >= totalPagesStep3}
                          onClick={() => {
                            setBulkPreviewPage((p) => Math.min(totalPagesStep3, p + 1));
                            resetPreviewScroll();
                          }}
                        >
                          Sau →
                        </button>
                      </div>
                    </div>

                    <div className="bulk-modal-foot">
                      <button
                        type="button"
                        className="btn-confirm-cancel"
                        id="btn-bulk-step3-back"
                        onClick={() => {
                      setBulkFilter("all");
                      setBulkPreviewPage(1);
                      setBulkStep(2);
                    }}
                      >
                        ← Quay lại Bước 2
                      </button>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                        {errorCount > 0 && (
                          <button
                            type="button"
                            className="btn-admin-sm warn"
                            id="btn-bulk-step3-download-errors"
                            onClick={handleDownloadBulkErrorCsv}
                          >
                            Tải danh sách lỗi ({errorCount})
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn-auth-primary"
                          id="btn-bulk-step3-next"
                          style={{ height: 36, padding: "0 16px" }}
                          disabled={validCount === 0}
                          onClick={() => {
                            setBulkStep4Error("");
                            setBulkStep(4);
                          }}
                        >
                          {validCount > 0
                            ? `Tiếp tục: Xác nhận nhập (${validCount} dòng) →`
                            : "Không có dòng hợp lệ để nhập"}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })()}

            {bulkStep === 4 &&
              (() => {
                const validRows = bulkRows.filter((r) => r.isValid);
                const errorCount = bulkRows.length - validRows.length;
                return (
                  <div className="bulk-step-panel is-active" id="bulk-step-4">
                    <div className="bulk-cat-grid" id="bulk-step4-summary-cards">
                      <div className="bulk-cat-card">
                        <span className="bulk-cat-lbl">Tổng bản ghi trong tệp</span>
                        <span className="bulk-cat-val" id="bulk-step4-total">
                          {bulkRows.length}
                        </span>
                      </div>
                      <div className="bulk-cat-card ok-tone">
                        <span className="bulk-cat-lbl">Sẽ tạo tài khoản mới</span>
                        <span className="bulk-cat-val" id="bulk-step4-valid">
                          {validRows.length}
                        </span>
                      </div>
                      <div className="bulk-cat-card warn-tone">
                        <span className="bulk-cat-lbl">Bỏ qua do có lỗi / trùng</span>
                        <span className="bulk-cat-val" id="bulk-step4-skip">
                          {errorCount}
                        </span>
                      </div>
                    </div>

                    <div className="confirm-target-card" id="bulk-step4-confirm-card">
                      <div className="confirm-target-row">
                        <span className="confirm-target-lbl">Vai trò mặc định sau khi nhập:</span>
                        <span className="confirm-target-val">
                          <span className="role-chip student">
                            Học sinh ({quotaConfig.studentDailyRequests} lượt AI/ngày)
                          </span>
                        </span>
                      </div>
                      <div className="confirm-target-row">
                        <span className="confirm-target-lbl">Trạng thái tài khoản mới:</span>
                        <span className="confirm-target-val">
                          <span className="role-chip pending-activation">Chờ kích hoạt</span>
                        </span>
                      </div>
                      <div className="confirm-target-row">
                        <span className="confirm-target-lbl">Trạng thái gửi email kích hoạt:</span>
                        <span className="confirm-target-val">
                          <span className="role-chip" id="bulk-step4-invite-chip">
                            Chưa gửi lời mời kích hoạt
                          </span>
                        </span>
                      </div>
                    </div>

                    <div className="confirm-policy-note info-tone">
                      <strong>Chính sách nhập an toàn:</strong> Hệ thống chỉ tạo mới các dòng hợp lệ. Các dòng lỗi hoặc trùng email được bỏ qua và có thể tải về tệp báo cáo lỗi để chỉnh sửa sau.
                    </div>

                    {bulkStep4Error && (
                      <div className="confirm-policy-note danger-tone" id="bulk-step4-error" role="alert">
                        {bulkStep4Error}
                      </div>
                    )}

                    <div className="bulk-modal-foot">
                      <button
                        type="button"
                        className="btn-confirm-cancel"
                        id="btn-bulk-step4-back"
                        onClick={() => {
                          setBulkFilter("all");
                          setBulkPreviewPage(1);
                          setBulkStep(3);
                        }}
                      >
                        ← Quay lại
                      </button>
                      <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                        <button
                          type="button"
                          className="btn-confirm-cancel"
                          id="btn-bulk-cancel-all"
                          onClick={() => setBulkImportOpen(false)}
                        >
                          Hủy bỏ toàn bộ
                        </button>
                        {errorCount > 0 && (
                          <button
                            type="button"
                            className="btn-admin-sm"
                            id="btn-bulk-download-errors"
                            onClick={handleDownloadBulkErrorCsv}
                          >
                            Tải danh sách lỗi (.csv)
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn-auth-primary"
                          id="btn-bulk-confirm-import"
                          disabled={validRows.length === 0}
                          onClick={async () => {
                            setBulkStep4Error("");
                            let createdCount = 0;
                            let backendReachable = false;
                            let backendErrorStatus: number | null = null;
                            let backendErrorText = "";

                            for (const row of validRows) {
                              try {
                                const res = await fetch("/api/admin/users", {
                                  method: "POST",
                                  headers: { "Content-Type": "application/json" },
                                  credentials: "include",
                                  body: JSON.stringify({
                                    displayName: row.rawName.trim(),
                                    email: row.rawEmail.trim(),
                                    role: "student",
                                    school: row.rawSchool.trim(),
                                  }),
                                });
                                const cType = res.headers.get("content-type") || "";
                                if (res.ok) {
                                  backendReachable = true;
                                  createdCount++;
                                } else if (cType.includes("application/json") || res.status < 500) {
                                  backendReachable = true;
                                  backendErrorStatus = res.status;
                                  try {
                                    const errBody = (await res.json()) as {
                                      error?: string;
                                      message?: string;
                                      detail?: string;
                                    };
                                    if (errBody?.error || errBody?.message || errBody?.detail) {
                                      backendErrorText = String(
                                        errBody.error || errBody.message || errBody.detail,
                                      );
                                    }
                                  } catch {
                                    /* ignore json parse error */
                                  }
                                }
                              } catch {
                                /* offline preview fallback */
                              }
                            }

                            if (backendReachable && createdCount === 0 && backendErrorStatus !== null) {
                              setBulkStep4Error(
                                backendErrorText ||
                                  `Không thể nhập danh sách tài khoản do máy chủ trả về lỗi (HTTP ${backendErrorStatus}). Không có tài khoản nào được tạo.`,
                              );
                              return;
                            }

                            if (!backendReachable) {
                              const nowStr = new Date().toLocaleDateString("vi-VN");
                              const nowTs = Date.now();
                              const newItems: AdminUserItem[] = validRows.map((r, idx) => ({
                                id: `bulk-${nowTs}-${idx}`,
                                name: r.rawName.trim(),
                                email: r.rawEmail.trim(),
                                role: "student",
                                status: "pending_activation",
                                school: r.rawSchool.trim(),
                                adminNote: `Nhập từ tệp ${bulkFileName}`,
                                joinedAt: nowStr,
                                joinedTs: nowTs + idx,
                                dailyLimit: quotaConfig.studentDailyRequests,
                                tokenCap: quotaConfig.studentDailyTokens,
                                usedToday: 0,
                                tokensToday: `0 / ${quotaConfig.studentDailyTokens.toLocaleString("vi-VN")}`,
                              }));
                              setUsers((prev) => [...newItems, ...prev]);
                              createdCount = validRows.length;
                            } else {
                              await fetchAdminUsers();
                            }

                            setBulkResult({
                              totalRecords: bulkRows.length,
                              createdCount,
                              errorCount: bulkRows.length - createdCount,
                              operatedAt: new Date().toLocaleDateString("vi-VN"),
                            });
                            setBulkStep("result");
                            showToastMsg(
                              `Đã nhập thành công ${createdCount}/${bulkRows.length} tài khoản Học sinh (Chờ kích hoạt).`,
                            );
                          }}
                        >
                          Xác nhận tạo {validRows.length} tài khoản hợp lệ
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })()}

            {bulkStep === "result" && bulkResult && (
              <div className="bulk-step-panel is-active" id="bulk-step-result">
                <div className="confirm-policy-note info-tone" id="bulk-import-result-banner">
                  <strong>Hoàn tất nhập danh sách tài khoản:</strong> Đã thêm{" "}
                  <strong>{bulkResult.createdCount}</strong> tài khoản Học sinh (trạng thái{" "}
                  <strong>Chờ kích hoạt</strong>) vào danh sách quản lý.
                </div>

                <div className="confirm-target-card" id="bulk-import-result-panel">
                  <div className="confirm-target-row">
                    <span className="confirm-target-lbl">Tổng bản ghi trong tệp:</span>
                    <span className="confirm-target-val" id="bulk-res-total">
                      {bulkResult.totalRecords} dòng
                    </span>
                  </div>
                  <div className="confirm-target-row">
                    <span className="confirm-target-lbl">Đã tạo thành công:</span>
                    <span className="confirm-target-val" id="bulk-res-created">
                      {bulkResult.createdCount} tài khoản (Học sinh · Chờ kích hoạt)
                    </span>
                  </div>
                  <div className="confirm-target-row">
                    <span className="confirm-target-lbl">Đã bỏ qua:</span>
                    <span className="confirm-target-val" id="bulk-res-skipped">
                      {bulkResult.errorCount} dòng
                    </span>
                  </div>
                  <div className="confirm-target-row">
                    <span className="confirm-target-lbl">Số dòng lỗi / trùng:</span>
                    <span className="confirm-target-val" id="bulk-res-errors">
                      {bulkResult.errorCount} dòng
                    </span>
                  </div>
                  <div className="confirm-target-row">
                    <span className="confirm-target-lbl">Thời điểm thực hiện:</span>
                    <span className="confirm-target-val" id="bulk-res-time">
                      {bulkResult.operatedAt}
                    </span>
                  </div>
                  <div className="confirm-target-row">
                    <span className="confirm-target-lbl">Người thực hiện:</span>
                    <span className="confirm-target-val" id="bulk-res-actor">
                      {user?.displayName || "Trần Quản Trị"} ({user?.email || "admin@axo.edu.vn"})
                    </span>
                  </div>
                  <div className="confirm-target-row">
                    <span className="confirm-target-lbl">Trạng thái gửi email:</span>
                    <span className="confirm-target-val">
                      <span className="role-chip" id="bulk-res-invite-state">
                        Chưa gửi lời mời kích hoạt
                      </span>
                    </span>
                  </div>
                </div>

                <div className="bulk-modal-foot">
                  <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                    {bulkResult.errorCount > 0 && (
                      <button
                        type="button"
                        className="btn-admin-sm"
                        id="btn-bulk-res-download-errors"
                        onClick={handleDownloadBulkErrorCsv}
                      >
                        Tải danh sách dòng lỗi (.csv)
                      </button>
                    )}
                  </div>
                  <button
                    type="button"
                    className="btn-auth-primary"
                    id="btn-bulk-result-close"
                    onClick={() => setBulkImportOpen(false)}
                  >
                    Đóng và xem bảng Tài khoản
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal: Điều chỉnh hạn mức AI cá nhân (#admin-quota-modal) */}
      <div
        className={`axo-modal-backdrop${quotaModalUser ? " open" : ""}`}
        id="admin-quota-modal"
        role="dialog"
        aria-modal="true"
        aria-hidden={!quotaModalUser}
        aria-labelledby="admin-quota-modal-title"
        onClick={(e) => {
          if (e.target === e.currentTarget) setQuotaModalUser(null);
        }}
      >
        <div className="axo-modal-dialog">
          <div className="axo-modal-head">
            <span className="axo-modal-title" id="admin-quota-modal-title">
              {quotaModalUser
                ? `Điều chỉnh hạn mức AI: ${quotaModalUser.name}`
                : "Điều chỉnh hạn mức AI cá nhân"}
            </span>
            <button
              type="button"
              className="context-close-icon-btn"
              id="btn-close-admin-quota-modal"
              aria-label="Đóng điều chỉnh hạn mức AI"
              onClick={() => setQuotaModalUser(null)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <div className="axo-modal-body" id="admin-quota-modal-body">
            {quotaModalUser && (
              <>
                <div className="confirm-target-card" id="quota-modal-target-card">
                  <div className="confirm-target-row">
                    <span className="confirm-target-lbl">Người dùng:</span>
                    <strong className="confirm-target-val">{quotaModalUser.name}</strong>
                  </div>
                  <div className="confirm-target-row">
                    <span className="confirm-target-lbl">Email &amp; vai trò:</span>
                    <span className="confirm-target-val">
                      <code>{quotaModalUser.email}</code> ·{" "}
                      {quotaModalUser.role === "admin"
                        ? "Quản trị viên"
                        : quotaModalUser.role === "teacher"
                          ? "Giáo viên"
                          : "Học sinh"}
                    </span>
                  </div>
                  <div className="confirm-target-row">
                    <span className="confirm-target-lbl">Mặc định vai trò / Đã dùng hôm nay:</span>
                    <span className="confirm-target-val">
                      {quotaModalUser.role === "admin"
                        ? 200
                        : quotaModalUser.role === "teacher"
                          ? quotaConfig.teacherDailyRequests
                          : quotaConfig.studentDailyRequests}{" "}
                      lượt/ngày · Đã dùng {quotaModalUser.usedToday}/{quotaModalUser.dailyLimit} lượt
                    </span>
                  </div>
                </div>

                <div className="quota-modal-input-block">
                  <label className="auth-label" htmlFor="inp-modal-user-daily-limit">
                    Hạn mức phân tích AI cá nhân (lượt / ngày)
                  </label>
                  <div className="quota-modal-input-row">
                    <input
                      type="number"
                      id="inp-modal-user-daily-limit"
                      className="quota-num-input"
                      min={1}
                      max={500}
                      value={quotaInputVal}
                      onChange={(e) => setQuotaInputVal(e.target.value)}
                    />
                    <button
                      type="button"
                      className="btn-admin-sm"
                      id="btn-modal-user-bump-10"
                      onClick={() =>
                        setQuotaInputVal((prev) =>
                          String(Math.min(500, (Number(prev) || quotaModalUser.dailyLimit) + 10)),
                        )
                      }
                    >
                      +10 lượt/ngày
                    </button>
                  </div>
                </div>

                <div className="acc-modal-actions-row">
                  <button
                    type="button"
                    className="btn-confirm-cancel"
                    id="btn-modal-cancel-user-quota"
                    onClick={() => setQuotaModalUser(null)}
                  >
                    Hủy
                  </button>
                  <button
                    type="button"
                    className="btn-auth-primary"
                    id="btn-modal-save-user-quota"
                    onClick={async () => {
                      const nextLim = Math.max(1, Math.min(500, Number(quotaInputVal) || 5));
                      let serverHandled = false;
                      try {
                        const r = await fetch(`/api/admin/users/${quotaModalUser.id}`, {
                          method: "PATCH",
                          headers: { "Content-Type": "application/json" },
                          credentials: "include",
                          body: JSON.stringify({ dailyLimit: nextLim }),
                        });
                        if (!r.ok) {
                          const errMsg = await extractServerError(
                            r,
                            "Không thể lưu hạn mức AI cá nhân.",
                          );
                          showToastMsg(errMsg);
                          return;
                        }
                        serverHandled = true;
                      } catch {
                        /* ignore in offline preview */
                      }
                      if (serverHandled) {
                        await fetchAdminUsers();
                      } else {
                        setUsers((prev) =>
                          prev.map((item) =>
                            item.id === quotaModalUser.id ? { ...item, dailyLimit: nextLim } : item,
                          ),
                        );
                      }
                      setQuotaModalUser(null);
                      showToastMsg(
                        `Đã lưu hạn mức AI cá nhân (${nextLim} lượt/ngày) cho ${quotaModalUser.name} (${quotaModalUser.email}).`,
                      );
                    }}
                  >
                    Lưu hạn mức cá nhân
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Modal: Cài đặt hệ thống Admin (#admin-system-settings-modal) */}
      <div
        className={`axo-modal-backdrop${sysSettingsOpen ? " open" : ""}`}
        id="admin-system-settings-modal"
        role="dialog"
        aria-modal="true"
        aria-hidden={!sysSettingsOpen}
        aria-labelledby="admin-system-settings-title"
        onClick={(e) => {
          if (e.target === e.currentTarget) attemptCloseSysSettings();
        }}
      >
        <div
          className="axo-modal-dialog sys-settings-dialog"
          onClick={() => setAutoCutoffMenuOpen(false)}
        >
          <div className="axo-modal-head sys-settings-modal-head">
            <div className="sys-settings-head-titles">
              <span className="axo-modal-title" id="admin-system-settings-title">
                Cài đặt hệ thống
              </span>
              <p className="sys-settings-modal-subtitle" id="admin-system-settings-subtitle">
                Quản lý cấu hình vận hành Axo
              </p>
            </div>
            <button
              type="button"
              className="context-close-icon-btn"
              id="btn-close-system-settings-modal"
              aria-label="Đóng cài đặt hệ thống"
              title="Đóng (Esc)"
              onClick={attemptCloseSysSettings}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div className="sys-settings-modal-body-layout">
            <nav
              className="sys-settings-modal-nav"
              id="admin-settings-modal-nav"
              role="tablist"
              aria-label="Danh mục cài đặt hệ thống"
            >
              <button
                type="button"
                role="tab"
                className={`sys-settings-nav-btn${sysSettingsTab === "quotas" ? " is-active" : ""}`}
                id="tab-btn-sys-quotas"
                data-settings-nav="quotas"
                aria-selected={sysSettingsTab === "quotas"}
                aria-controls="settings-panel-quotas"
                onClick={() => setSysSettingsTab("quotas")}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <line x1="4" y1="21" x2="4" y2="14" />
                  <line x1="4" y1="10" x2="4" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12" y2="3" />
                  <line x1="20" y1="21" x2="20" y2="16" />
                  <line x1="20" y1="12" x2="20" y2="3" />
                  <line x1="1" y1="14" x2="7" y2="14" />
                  <line x1="9" y1="8" x2="15" y2="8" />
                  <line x1="17" y1="16" x2="23" y2="16" />
                </svg>
                <span>Hạn mức và chi phí</span>
              </button>
              <button
                type="button"
                role="tab"
                className={`sys-settings-nav-btn${sysSettingsTab === "service" ? " is-active" : ""}`}
                id="tab-btn-sys-service"
                data-settings-nav="service"
                aria-selected={sysSettingsTab === "service"}
                aria-controls="settings-panel-service"
                onClick={() => setSysSettingsTab("service")}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <rect x="2" y="3" width="20" height="14" rx="2" />
                  <line x1="8" y1="21" x2="16" y2="21" />
                  <line x1="12" y1="17" x2="12" y2="21" />
                </svg>
                <span>Dịch vụ AI</span>
              </button>
            </nav>

            <div className="sys-settings-modal-content" id="admin-settings-main-mount">
              <div className="admin-page-head-group" id="admin-settings-page-head-group">
                <h2 className="admin-content-page-title" id="admin-settings-page-title">
                  {sysSettingsTab === "quotas" ? "Hạn mức và chi phí" : "Dịch vụ AI"}
                </h2>
                <p className="admin-page-intro" id="admin-settings-page-intro">
                  {sysSettingsTab === "quotas"
                    ? "So sánh, thiết lập hạn mức phân tích AI mặc định theo vai trò và cấu hình cơ chế bảo vệ ngân sách tháng."
                    : "Theo dõi trạng thái kết nối dịch vụ phân tích ngữ nghĩa AI và bộ dựng hình học tất định."}
                </p>
              </div>

              <div className="settings-workspace-wrap" id="admin-settings-workspace">
                {sysSettingsTab === "quotas" ? (
                  <section
                    className="settings-clean-card"
                    id="settings-panel-quotas"
                    role="tabpanel"
                    aria-labelledby="tab-btn-sys-quotas"
                  >
                    <div>
                      <div className="settings-block-title">
                        Hạn mức sử dụng AI mặc định theo vai trò
                      </div>
                      <div className="settings-block-sub">
                        So sánh và thiết lập giới hạn mặc định trong ngày cho Học sinh và Giáo viên.
                      </div>
                    </div>

                    <table
                      className="settings-compare-table"
                      id="settings-quota-compare-table"
                      aria-label="Bảng thiết lập hạn mức theo vai trò"
                    >
                      <colgroup>
                        <col className="col-metric" />
                        <col className="col-student" />
                        <col className="col-teacher" />
                      </colgroup>
                      <thead>
                        <tr>
                          <th scope="col">Thông số</th>
                          <th scope="col">Học sinh</th>
                          <th scope="col">Giáo viên</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>
                            <div className="settings-metric-name">Số lượt phân tích AI / ngày</div>
                            <div className="settings-metric-hint">Số đề bài tự do tối đa mỗi ngày</div>
                          </td>
                          <td data-role-col="Học sinh">
                            <div className="settings-input-unit-wrap">
                              <input
                                type="number"
                                id="inp-q-student-req"
                                className="quota-num-input"
                                min={1}
                                max={100}
                                value={quotaDraft.studentDailyRequests}
                                onChange={(e) =>
                                  setQuotaDraft((prev) => ({
                                    ...prev,
                                    studentDailyRequests: Math.max(1, Number(e.target.value) || 5),
                                  }))
                                }
                              />
                              <span className="settings-unit-lbl">lượt/ngày</span>
                            </div>
                          </td>
                          <td data-role-col="Giáo viên">
                            <div className="settings-input-unit-wrap">
                              <input
                                type="number"
                                id="inp-q-teacher-req"
                                className="quota-num-input"
                                min={5}
                                max={500}
                                value={quotaDraft.teacherDailyRequests}
                                onChange={(e) =>
                                  setQuotaDraft((prev) => ({
                                    ...prev,
                                    teacherDailyRequests: Math.max(5, Number(e.target.value) || 30),
                                  }))
                                }
                              />
                              <span className="settings-unit-lbl">lượt/ngày</span>
                            </div>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <div className="settings-metric-name">Ngân sách token / ngày</div>
                            <div className="settings-metric-hint">Tổng độ dài dữ kiện xử lý trong ngày</div>
                          </td>
                          <td data-role-col="Học sinh">
                            <div className="settings-input-unit-wrap">
                              <input
                                type="number"
                                id="inp-q-student-tok"
                                className="quota-num-input"
                                step={1000}
                                min={1000}
                                max={200000}
                                value={quotaDraft.studentDailyTokens}
                                onChange={(e) =>
                                  setQuotaDraft((prev) => ({
                                    ...prev,
                                    studentDailyTokens: Math.max(1000, Number(e.target.value) || 20000),
                                  }))
                                }
                              />
                              <span className="settings-unit-lbl">tokens/ngày</span>
                            </div>
                          </td>
                          <td data-role-col="Giáo viên">
                            <div className="settings-input-unit-wrap">
                              <input
                                type="number"
                                id="inp-q-teacher-tok"
                                className="quota-num-input"
                                step={5000}
                                min={5000}
                                max={1000000}
                                value={quotaDraft.teacherDailyTokens}
                                onChange={(e) =>
                                  setQuotaDraft((prev) => ({
                                    ...prev,
                                    teacherDailyTokens: Math.max(5000, Number(e.target.value) || 120000),
                                  }))
                                }
                              />
                              <span className="settings-unit-lbl">tokens/ngày</span>
                            </div>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <div className="settings-metric-name">Giới hạn yêu cầu / phút</div>
                            <div className="settings-metric-hint">Ngăn gửi yêu cầu liên tiếp bất thường</div>
                          </td>
                          <td data-role-col="Học sinh">
                            <div className="settings-input-unit-wrap">
                              <input
                                type="number"
                                id="inp-q-student-rate"
                                className="quota-num-input"
                                min={1}
                                max={30}
                                value={quotaDraft.studentRatePerMin}
                                onChange={(e) =>
                                  setQuotaDraft((prev) => ({
                                    ...prev,
                                    studentRatePerMin: Math.max(1, Number(e.target.value) || 5),
                                  }))
                                }
                              />
                              <span className="settings-unit-lbl">yêu cầu/phút</span>
                            </div>
                          </td>
                          <td data-role-col="Giáo viên">
                            <div className="settings-input-unit-wrap">
                              <input
                                type="number"
                                id="inp-q-teacher-rate"
                                className="quota-num-input"
                                min={1}
                                max={60}
                                value={quotaDraft.teacherRatePerMin}
                                onChange={(e) =>
                                  setQuotaDraft((prev) => ({
                                    ...prev,
                                    teacherRatePerMin: Math.max(1, Number(e.target.value) || 15),
                                  }))
                                }
                              />
                              <span className="settings-unit-lbl">yêu cầu/phút</span>
                            </div>
                          </td>
                        </tr>
                      </tbody>
                    </table>

                    <div className="settings-cost-grid" id="settings-cost-grid">
                      <div className="settings-cost-box" id="settings-cost-box-vnd">
                        <div className="settings-cost-head">
                          <label htmlFor="inp-q-budget-vnd">Ngân sách dự kiến tháng (VND)</label>
                          <span
                            className={`vnd-status-badge${quotaDraft.vndBudgetRaw.trim() !== quotaConfig.vndBudgetRaw.trim() ? " is-mockup" : ""}`}
                            id="vnd-budget-status-badge"
                          >
                            {quotaDraft.vndBudgetRaw.trim() !== quotaConfig.vndBudgetRaw.trim()
                              ? "Chưa lưu"
                              : quotaConfig.vndBudgetRaw.trim()
                                ? "Ngưỡng dự kiến"
                                : "Chưa thiết lập"}
                          </span>
                        </div>
                        <div className="vnd-input-group">
                          <input
                            type="text"
                            inputMode="numeric"
                            id="inp-q-budget-vnd"
                            className="quota-num-input"
                            value={quotaDraft.vndBudgetRaw}
                            onChange={(e) =>
                              setQuotaDraft((prev) => ({ ...prev, vndBudgetRaw: e.target.value }))
                            }
                            placeholder="Nhập ngưỡng ngân sách dự kiến"
                            aria-label="Ngân sách dự kiến tháng (VND)"
                          />
                          <span className="vnd-unit-pill" aria-hidden="true">
                            VND (₫)
                          </span>
                        </div>
                        <p className="field-hint" id="vnd-budget-hint">
                          Ngưỡng ngân sách dự kiến phục vụ cấu hình quản trị, không phải chi phí API thực tế đã phát sinh.
                        </p>
                      </div>

                      <div className="settings-cost-box" id="settings-cost-box-cutoff">
                        <div className="settings-cost-head">
                          <label id="lbl-q-autocutoff" htmlFor="btn-q-autocutoff-trigger">
                            Hành vi khi chạm giới hạn chi phí
                          </label>
                          <span className="vnd-status-badge">Cơ chế bảo vệ</span>
                        </div>
                        <div
                          className={`axo-custom-select${autoCutoffMenuOpen ? " is-open" : ""}`}
                          id="autocutoff-dropdown-wrap"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="hidden"
                            id="sel-q-autocutoff"
                            value={quotaDraft.autoCutoffEnabled ? "true" : "false"}
                          />
                          <button
                            type="button"
                            className="axo-custom-select-trigger"
                            id="btn-q-autocutoff-trigger"
                            role="combobox"
                            aria-haspopup="listbox"
                            aria-expanded={autoCutoffMenuOpen}
                            aria-labelledby="lbl-q-autocutoff"
                            aria-controls="menu-q-autocutoff"
                            onClick={() => setAutoCutoffMenuOpen((v) => !v)}
                          >
                            <span className="axo-custom-select-value" id="val-q-autocutoff">
                              {quotaDraft.autoCutoffEnabled
                                ? "Tạm dừng phân tích AI"
                                : "Chỉ gửi cảnh báo"}
                            </span>
                            <svg className="axo-custom-select-chevron" viewBox="0 0 24 24" aria-hidden="true">
                              <polyline points="6 9 12 15 18 9" />
                            </svg>
                          </button>
                          <div
                            className="axo-custom-select-menu"
                            id="menu-q-autocutoff"
                            role="listbox"
                            tabIndex={-1}
                            aria-labelledby="lbl-q-autocutoff"
                          >
                            <div
                              className={`axo-custom-select-option${quotaDraft.autoCutoffEnabled ? " is-selected" : ""}`}
                              id="opt-autocutoff-true"
                              role="option"
                              aria-selected={quotaDraft.autoCutoffEnabled}
                              onClick={() => {
                                setQuotaDraft((prev) => ({ ...prev, autoCutoffEnabled: true }));
                                setAutoCutoffMenuOpen(false);
                              }}
                            >
                              <div className="axo-opt-row">
                                <div className="axo-opt-text">
                                  <span className="axo-opt-main">Tạm dừng phân tích AI</span>
                                  <span className="axo-opt-sub">
                                    Tự động tạm dừng phân tích đề mới khi chạm trần; giữ mở Thư viện 3D
                                  </span>
                                </div>
                                <svg className="axo-opt-check" viewBox="0 0 24 24" aria-hidden="true">
                                  <polyline points="20 6 9 17 4 12" />
                                </svg>
                              </div>
                            </div>
                            <div
                              className={`axo-custom-select-option${!quotaDraft.autoCutoffEnabled ? " is-selected" : ""}`}
                              id="opt-autocutoff-false"
                              role="option"
                              aria-selected={!quotaDraft.autoCutoffEnabled}
                              onClick={() => {
                                setQuotaDraft((prev) => ({ ...prev, autoCutoffEnabled: false }));
                                setAutoCutoffMenuOpen(false);
                              }}
                            >
                              <div className="axo-opt-row">
                                <div className="axo-opt-text">
                                  <span className="axo-opt-main">Chỉ gửi cảnh báo</span>
                                  <span className="axo-opt-sub">
                                    Chỉ gửi thông báo cảnh báo cho Quản trị viên, không chặn phân tích
                                  </span>
                                </div>
                                <svg className="axo-opt-check" viewBox="0 0 24 24" aria-hidden="true">
                                  <polyline points="20 6 9 17 4 12" />
                                </svg>
                              </div>
                            </div>
                          </div>
                        </div>
                        <p className="field-hint" id="autocutoff-field-hint">
                          Khi chạm ngưỡng bảo vệ, 11 mô hình 3D dựng sẵn trong Thư viện và Lịch sử học vẫn mở bình thường.
                        </p>
                      </div>
                    </div>
                  </section>
                ) : (
                  <section
                    className="settings-clean-card"
                    id="settings-panel-service"
                    role="tabpanel"
                    aria-labelledby="tab-btn-sys-service"
                  >
                    <div className="service-status-banner">
                      <div className="service-status-indicator">
                        <span className="status-dot-live" aria-hidden="true" />
                        <span>
                          {overviewStats.aiServiceConfigured === false
                            ? "Chưa cấu hình khóa AI · Đang phục vụ Thư viện 3D & bộ nhớ đệm"
                            : "Đang hoạt động · Phản hồi ổn định"}
                        </span>
                      </div>
                      {overviewStats.aiServiceConfigured === false ? (
                        <span className="role-chip pending">Chế độ giới hạn</span>
                      ) : (
                        <span className="role-chip teacher">Kết nối sẵn sàng</span>
                      )}
                    </div>

                    <div className="service-info-list" aria-label="Thông tin vận hành dịch vụ AI">
                      <div className="service-info-row">
                        <span className="service-info-lbl">Trạng thái kết nối dịch vụ AI</span>
                        <span className="service-info-val">
                          {overviewStats.aiServiceConfigured === false
                            ? "Chưa cấu hình GEMINI_API_KEY trên máy chủ · Phục vụ bài mẫu & đề lưu đệm"
                            : "Đang kết nối · Thời gian phản hồi ổn định"}
                        </span>
                      </div>
                      <div className="service-info-row">
                        <span className="service-info-lbl">Trạng thái bộ dựng hình học 3D</span>
                        <span className="service-info-val">
                          Hoạt động bình thường · Kiểm chứng dữ kiện tất định (Fail-closed)
                        </span>
                      </div>
                      <div className="service-info-row">
                        <span className="service-info-lbl">Tổng số phiên dựng hình đã lưu</span>
                        <span className="service-info-val">
                          {overviewStats.totalHistoryEntries} phiên hợp lệ
                        </span>
                      </div>
                      <div className="service-info-row">
                        <span className="service-info-lbl">Giới hạn tần suất yêu cầu hiện hành</span>
                        <span className="service-info-val">
                          Học sinh: {quotaConfig.studentRatePerMin} yêu cầu/phút · Giáo viên:{" "}
                          {quotaConfig.teacherRatePerMin} yêu cầu/phút
                        </span>
                      </div>
                      <div className="service-info-row">
                        <span className="service-info-lbl">Tình trạng bảo vệ dịch vụ</span>
                        <span className="service-info-val">
                          {quotaConfig.autoCutoffEnabled
                            ? "Đang bật · Tự động tạm dừng phân tích AI mới khi chạm ngưỡng chi phí (Giữ mở Thư viện 3D)"
                            : "Chế độ cảnh báo · Chỉ gửi thông báo cho Quản trị viên khi chạm ngưỡng"}
                        </span>
                      </div>
                      <div className="service-info-row">
                        <span className="service-info-lbl">Quản lý cấu hình máy chủ</span>
                        <span className="service-info-val">
                          Thông tin kết nối dịch vụ AI được quản lý ở môi trường máy chủ. Không hiển thị khóa API trên giao diện quản trị.
                        </span>
                      </div>
                    </div>
                  </section>
                )}
              </div>
            </div>
          </div>

          <div className="sys-settings-modal-foot" id="admin-system-settings-footer">
            <span className="settings-footer-note" id="sys-settings-footer-note">
              {sysSettingsTab === "quotas" ? (
                <>
                  Hạn mức riêng của từng cá nhân được quản lý tại trang <strong>Tài khoản</strong>.
                </>
              ) : (
                "Thông tin trạng thái vận hành dịch vụ AI (chỉ đọc)."
              )}
            </span>
            <div className="sys-settings-footer-actions" id="sys-settings-footer-actions">
              {sysSettingsTab === "quotas" && isSysDraftDirty && (
                <button
                  type="button"
                  className="btn-admin-sm sys-foot-btn"
                  id="btn-reset-quota-draft"
                  onClick={() => setQuotaDraft(quotaConfig)}
                >
                  Hoàn tác
                </button>
              )}
              <button
                type="button"
                className="btn-admin-sm sys-foot-btn"
                id="btn-cancel-system-settings"
                onClick={attemptCloseSysSettings}
              >
                {sysSettingsTab === "quotas" ? "Hủy" : "Đóng"}
              </button>
              {sysSettingsTab === "quotas" && (
                <button
                  type="button"
                  className="btn-settings-save sys-foot-btn"
                  id="btn-save-quota-config"
                  disabled={!isSysDraftDirty}
                  onClick={async () => {
                    let serverHandled = false;
                    try {
                      const r = await fetch("/api/admin/settings", {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        credentials: "include",
                        body: JSON.stringify({ settings: quotaDraft }),
                      });
                      if (!r.ok) {
                        const errMsg = await extractServerError(
                          r,
                          "Không thể lưu cấu hình hạn mức hệ thống.",
                        );
                        showToastMsg(errMsg);
                        return;
                      }
                      serverHandled = true;
                    } catch {
                      /* ignore in offline preview */
                    }
                    if (serverHandled) {
                      await fetchAdminUsers();
                    } else {
                      setQuotaConfig(quotaDraft);
                    }
                    setSysSettingsOpen(false);
                    setSysDiscardConfirmOpen(false);
                    showToastMsg("Đã lưu cấu hình hạn mức hệ thống.");
                  }}
                >
                  Lưu thay đổi
                </button>
              )}
            </div>
          </div>

          <div
            className={`sys-settings-discard-overlay${sysDiscardConfirmOpen ? " open" : ""}`}
            id="sys-settings-discard-confirm"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="sys-settings-discard-title"
            aria-describedby="sys-settings-discard-desc"
          >
            <div className="sys-settings-discard-card">
              <div className="sys-settings-discard-title" id="sys-settings-discard-title">
                Bỏ các thay đổi chưa lưu?
              </div>
              <p className="sys-settings-discard-desc" id="sys-settings-discard-desc">
                Bạn đang có thay đổi cấu hình hạn mức chưa lưu. Nếu đóng lúc này, các thông số vừa nhập sẽ bị hủy.
              </p>
              <div className="sys-settings-discard-actions">
                <button
                  type="button"
                  className="btn-admin-sm"
                  id="btn-sys-discard-stay"
                  onClick={() => setSysDiscardConfirmOpen(false)}
                >
                  Tiếp tục chỉnh sửa
                </button>
                <button
                  type="button"
                  className="btn-confirm-danger"
                  id="btn-sys-discard-confirm"
                  onClick={() => {
                    setQuotaDraft(quotaConfig);
                    setSysDiscardConfirmOpen(false);
                    setSysSettingsOpen(false);
                  }}
                >
                  Bỏ thay đổi
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
