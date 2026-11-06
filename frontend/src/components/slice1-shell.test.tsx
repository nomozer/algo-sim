import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../App";
import {
  NotificationDropdown,
  ToastContainer,
  TopNav,
  TopNavAccount,
  itemsForRole,
  useToastStore,
} from "./TopNav";
import { useAuthStore, type AuthUser } from "../state/auth";
import { useAppStore } from "../state/store";
import { useClassroomStore, type Assignment, type Classroom } from "../state/classroom";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest } from "../state/history";

registerAllSimulations();

function setAuthForSSR(user: AuthUser | null) {
  useAuthStore.setState({ user, resolved: true });
  Object.assign(useAuthStore.getInitialState(), { user, resolved: true });
}

function setClassroomForSSR(patch: {
  classes?: Classroom[];
  assignments?: Assignment[];
}) {
  const next = {
    classes: patch.classes ?? [],
    assignments: patch.assignments ?? [],
    session: null,
  };
  useClassroomStore.setState(next);
  Object.assign(useClassroomStore.getInitialState(), next);
}

describe("Axo V2.7 Slice 1 — Application Shell, Header, Navigation, Dropdowns & Toast", () => {
  beforeEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useToastStore.getState().clearToasts();
    Object.assign(useToastStore.getInitialState(), { toasts: [] });
    setAuthForSSR(null);
    setClassroomForSSR({ classes: [], assignments: [] });
  });

  afterEach(() => {
    setAuthForSSR(null);
    setClassroomForSSR({ classes: [], assignments: [] });
    useToastStore.getState().clearToasts();
    Object.assign(useToastStore.getInitialState(), { toasts: [] });
  });

  it("Header khách (Guest): hiển thị thương hiệu Axo, capsule 3 mục (Trang chủ, Thư viện, Lịch sử), nút Đăng nhập và Đăng ký", () => {
    const html = renderToString(<App />);
    expect(html).toContain("Axo");
    expect(html).toContain("axo-logo-svg");
    expect(html).toContain("nav-n1-capsule");
    expect(html).toContain("Trang chủ");
    expect(html).toContain("Thư viện");
    expect(html).toContain("Lịch sử");
    expect(html).toContain("Đăng nhập");
    expect(html).toContain("Đăng ký");
    for (const legacyLabel of ["Mô phỏng mới", "Bài thực hành", "Lớp của em", "Quan sát lớp"]) {
      expect(html).not.toContain(legacyLabel);
    }
  });

  it("TopNav đã đăng nhập: nhất quán đúng 3 mục (Trang chủ, Thư viện, Lịch sử) cho cả Học sinh và Giáo viên (P3)", () => {
    setAuthForSSR({
      id: 101,
      email: "minhanh@axo.edu.vn",
      displayName: "Nguyễn Minh Anh",
      role: "student",
      mustChangePassword: false,
    });

    const navHtml = renderToString(<TopNav />);
    expect(navHtml).toContain("Axo");
    expect(navHtml).toContain("nav-n1-capsule");
    expect(itemsForRole("student").map((i) => i.label)).toEqual([
      "Trang chủ",
      "Thư viện",
      "Lịch sử",
    ]);
    expect(itemsForRole("teacher").map((i) => i.label)).toEqual([
      "Trang chủ",
      "Thư viện",
      "Lịch sử",
    ]);
    for (const item of itemsForRole("student")) {
      expect(navHtml).toContain(item.label);
    }
    for (const legacyLabel of ["Mô phỏng mới", "Bài thực hành", "Lớp của em", "Quan sát lớp"]) {
      expect(navHtml).not.toContain(legacyLabel);
    }
  });

  it("TopNavAccount: hiển thị nút hồ sơ người dùng và menu dropdown chuẩn V2.7 (loại bỏ Lớp học/Bài thực hành/Quan sát lớp)", () => {
    setAuthForSSR({
      id: 202,
      email: "thay.huy@axo.edu.vn",
      displayName: "Thầy Lê Quang Huy",
      role: "teacher",
      mustChangePassword: false,
    });

    const accHtml = renderToString(<TopNavAccount initialOpen />);
    expect(accHtml).toContain("Thầy Lê Quang Huy");
    expect(accHtml).toContain("thay.huy@axo.edu.vn");
    expect(accHtml).toContain("Giáo viên");
    expect(accHtml).toContain("account-pop-avatar");
    expect(accHtml).toContain("Hạn mức AI hôm nay");
    expect(accHtml).toContain("Cài đặt tài khoản");
    expect(accHtml).toContain("Lịch sử học tập");
    expect(accHtml).toContain("Đăng xuất");
    expect(accHtml).toContain("user-profile-btn");
    for (const removedItem of ["Lớp học của tôi", "Quản lý lớp học", "Bài thực hành", "Bài đã giao", "Quan sát lớp học"]) {
      expect(accHtml).not.toContain(removedItem);
    }
  });

  it("NotificationDropdown: chỉ phản ánh dữ liệu lớp học/bài giao thực tế từ store, không có thông báo demo cứng", () => {
    setAuthForSSR({
      id: 101,
      email: "minhanh@axo.edu.vn",
      displayName: "Nguyễn Minh Anh",
      role: "student",
      mustChangePassword: false,
    });

    const emptyHtml = renderToString(<NotificationDropdown initialOpen />);
    expect(emptyHtml).toContain("Chưa có thông báo mới.");
    expect(emptyHtml).not.toContain("DEMO");

    setClassroomForSSR({
      classes: [
        {
          id: 11,
          name: "11A1",
          archived: false,
          createdAt: "2026-10-27T07:00:00Z",
        },
      ],
      assignments: [
        {
          id: 501,
          classroomId: 11,
          title: "Thiết diện hình chóp S.ABCD",
          instruction: "Tìm giao tuyến của (MNP) với các mặt bên",
          simulationId: "generic.semantic_program",
          closed: false,
          createdAt: "2026-10-27T08:00:00Z",
          myPractice: null,
        },
      ],
    });

    const withAsgHtml = renderToString(<NotificationDropdown initialOpen />);
    expect(withAsgHtml).toContain("Thiết diện hình chóp S.ABCD");
    expect(withAsgHtml).toContain("11A1");
    expect(withAsgHtml).toContain("Đánh dấu đã đọc");
  });

  it("ToastContainer: hiển thị thông báo góc trên bên phải đúng chuẩn V2.7 với phân loại tone và nút đóng", () => {
    useToastStore.getState().showToast({
      tone: "error",
      title: "Chưa thể dựng hình",
      description: "Vui lòng kiểm tra kết nối mạng và thử lại.",
      durationMs: 0,
    });
    Object.assign(useToastStore.getInitialState(), {
      toasts: useToastStore.getState().toasts,
    });

    const html = renderToString(<ToastContainer />);
    expect(html).toContain("axo-composer-toast");
    expect(html).toContain('data-toast-tone="error"');
    expect(html).toContain("Chưa thể dựng hình");
    expect(html).toContain("Vui lòng kiểm tra kết nối mạng và thử lại.");
    expect(html).toContain('aria-label="Đóng thông báo"');
  });
});
