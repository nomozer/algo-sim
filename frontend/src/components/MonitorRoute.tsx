/**
 * Cầu nối route → `MonitorView`.
 *
 * Tách khỏi `MonitorView` để component ấy nhận `classId`/`className` qua PROPS
 * và test được bằng SSR mà không phải dựng store: zustand SSR luôn trả trạng
 * thái đầu (`§8` #8), nên một component tự đọc store sẽ render rỗng trong test
 * và mọi khẳng định về nội dung sẽ xanh vì màn hình trống.
 */
import { useEffect } from "react";
import { MonitorView } from "./MonitorView";
import { useClassroomStore } from "../state/classroom";
import { useAppStore } from "../state/store";

export function MonitorRoute() {
  const classes = useClassroomStore((s) => s.classes);
  const loadClasses = useClassroomStore((s) => s.loadClasses);
  const session = useClassroomStore((s) => s.session);
  const sessionClassId = useClassroomStore((s) => s.sessionClassId);
  const setView = useAppStore((s) => s.setView);

  useEffect(() => { void loadClasses(); }, [loadClasses]);

  /* Lớp đang dạy nếu có; nếu chưa mở tiết nào thì lớp đầu tiên. Không đoán xa
     hơn thế — chọn lớp là việc của giáo viên, và một màn hình tự nhảy sang
     lớp khác giữa tiết là thứ không ai muốn. */
  const classId = sessionClassId ?? classes[0]?.id ?? null;
  const lop = classes.find((c) => c.id === classId) ?? null;

  if (classId === null) {
    return (
      <section className="monitor">
        <p className="monitor-trong">
          Cô/thầy chưa có lớp nào. Tạo lớp ở mục <strong>Lớp học</strong> trước nhé.
        </p>
      </section>
    );
  }

  return (
    <MonitorView
      classId={classId}
      className={lop?.name ?? "Lớp"}
      onBack={() => setView(session ? "workspace" : "classes")}
    />
  );
}
