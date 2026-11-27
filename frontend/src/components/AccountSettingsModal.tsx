import { useEffect, useRef, useState } from "react";
import { useAuthStore } from "../state/auth";
import { useAppStore } from "../state/store";
import { PwToggleButton } from "./auth-shared";

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


export default AccountSettingsModal;
