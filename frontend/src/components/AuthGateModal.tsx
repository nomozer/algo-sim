import { useState } from "react";
import { useAuthStore, type Role } from "../state/auth";

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
            <span>{isRegister ? "Email" : "Email hoặc tên đăng nhập"}</span>
            <input
              type={isRegister ? "email" : "text"}
              inputMode="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete={isRegister ? "email" : "username"}
              required
              placeholder={isRegister ? "Nhập địa chỉ email" : "Nhập email hoặc tên đăng nhập"}
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


export default AuthGate;
