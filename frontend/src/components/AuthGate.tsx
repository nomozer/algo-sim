import { useState } from "react";
import { useAuthStore, type Role } from "../state/auth";

/**
 * M18 — CỬA ĐĂNG NHẬP / ĐĂNG KÝ.
 *
 * Một hộp thoại, hai chế độ. Không phải hai trang riêng vì đổi chế độ giữa
 * chừng là việc thường xảy ra ("à mình chưa có tài khoản"), và bắt người dùng
 * đi qua một lần điều hướng nữa để làm việc đó là thêm ma sát không đổi lấy gì.
 *
 * VAI TRÒ GIÁO VIÊN: ô nhập mã hiện ra khi người dùng chọn "Tôi là giáo viên".
 * Nó KHÔNG phải cơ chế bảo mật — máy chủ mới là bên quyết (`§8`: không giả vờ
 * an toàn bằng cách giấu nút). Giấu ô này đi cũng không ngăn được ai gửi thẳng
 * một request; điều ngăn được là `resolve_signup_role` trên máy chủ.
 */
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
        email, displayName: name, password,
        role, teacherCode: role === "teacher" ? teacherCode : undefined,
      });
    } else {
      await login(email, password);
    }
  };

  return (
    <div className="auth-overlay" role="dialog" aria-modal="true"
      aria-label={isRegister ? "Đăng ký tài khoản" : "Đăng nhập"}
      onClick={(e) => { if (e.target === e.currentTarget) close(); }}>
      <div className="auth-card">
        <div className="auth-head">
          <h2 className="auth-title">{isRegister ? "Tạo tài khoản" : "Đăng nhập"}</h2>
          <button type="button" className="auth-close" onClick={close}
            aria-label="Đóng">×</button>
        </div>

        <form className="auth-form" onSubmit={submit}>
          {isRegister && (
            <label className="auth-field">
              <span>Tên hiển thị</span>
              <input value={name} onChange={(e) => setName(e.target.value)}
                autoComplete="name" required placeholder="Nguyễn Văn An" />
            </label>
          )}
          <label className="auth-field">
            <span>Email</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              autoComplete="email" required placeholder="an@truong.edu.vn" />
          </label>
          <label className="auth-field">
            <span>Mật khẩu</span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              autoComplete={isRegister ? "new-password" : "current-password"}
              required minLength={8} placeholder="ít nhất 8 ký tự" />
          </label>

          {isRegister && (
            <fieldset className="auth-roles">
              <legend>Em/thầy cô dùng AlgoSim với vai trò</legend>
              <label className="auth-role">
                <input type="radio" name="role" checked={role === "student"}
                  onChange={() => setRole("student")} />
                <span>Học sinh</span>
              </label>
              <label className="auth-role">
                <input type="radio" name="role" checked={role === "teacher"}
                  onChange={() => setRole("teacher")} />
                <span>Giáo viên</span>
              </label>
            </fieldset>
          )}

          {isRegister && role === "teacher" && (
            <label className="auth-field">
              <span>Mã giáo viên</span>
              <input value={teacherCode} onChange={(e) => setTeacherCode(e.target.value)}
                placeholder="Mã do nhà trường cấp" />
              {/* Nói thẳng đây là mã mời, không phải xác minh danh tính. */}
              <small className="auth-hint">
                Tài khoản giáo viên cần mã mời từ người quản trị hệ thống.
              </small>
            </label>
          )}

          {error && <p className="auth-error" role="alert">{error}</p>}

          <button type="submit" className="btn-primary auth-submit" disabled={busy}>
            {busy ? "Đang xử lý…" : isRegister ? "Tạo tài khoản" : "Đăng nhập"}
          </button>
        </form>

        <p className="auth-swap">
          {isRegister ? "Đã có tài khoản? " : "Chưa có tài khoản? "}
          <button type="button" className="link-button"
            onClick={() => open(isRegister ? "login" : "register")}>
            {isRegister ? "Đăng nhập" : "Đăng ký"}
          </button>
        </p>
      </div>
    </div>
  );
}
