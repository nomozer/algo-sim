/**
 * DẢI VIỆC — câu trả lời nhanh cho ba câu hỏi lúc vừa mở app.
 *
 *   học sinh:  Em học lớp nào? · Có bài nào đang chờ? · Vào đâu để làm?
 *   giáo viên: Tôi có lớp nào? · Đã giao bao nhiêu bài? · Vào đâu để dạy?
 *
 * ─── VÌ SAO KHÔNG PHẢI MỘT DASHBOARD ─────────────────────────────────────
 *
 * Trang chủ là chỗ BẮT ĐẦU MỘT VIỆC, không phải chỗ ngắm số liệu. Một bảng
 * thống kê đầy thẻ sẽ đẩy ô nhập đề — hành động chính — xuống dưới màn hình
 * thứ nhất, đúng thứ M9-UX5 đã gỡ một lần rồi (5 mục lịch sử ⇒ 5 thẻ). Nên
 * đây là MỘT dải, không phình theo dữ liệu, và luôn kết bằng một đường đi
 * tiếp chứ không tự trở thành nơi làm việc.
 *
 * ─── KHÔNG CÓ DỮ LIỆU THÌ KHÔNG DỰNG GÌ ──────────────────────────────────
 *
 * Chưa vào lớp nào ⇒ trả `null`, không dựng ô rỗng và tuyệt đối không bịa thẻ
 * mẫu cho màn hình trông đông. Một ô "Bạn chưa có lớp" nằm thường trực chỉ là
 * chỗ chiếm đất; còn thẻ bịa thì dạy người dùng rằng số trên màn hình không
 * đáng tin.
 *
 * 0 gọi LLM. Dữ liệu lấy từ store lớp học, đúng hai endpoint đã có.
 */
import { useEffect } from "react";
import { useAuthStore } from "../state/auth";
import { useClassroomStore } from "../state/classroom";
import { useAppStore } from "../state/store";

export interface OViec {
  nhan: string;
  so: number;
  di: "classes" | "assignments";
}

/**
 * Dải hiện những gì — hàm THUẦN, và luật sống ở đây chứ không trong component.
 *
 * Component đọc ba store, mà zustand ở SSR luôn trả trạng thái đầu (`§8` #13):
 * một test dựng component sẽ thấy màn hình rỗng và mọi khẳng định xanh vì
 * không có gì để sai. Tách ra thì luật kiểm được thật.
 *
 * Trả mảng RỖNG = không dựng gì. Đó là câu trả lời đúng khi người dùng chưa có
 * lớp nào: một ô "Bạn chưa có lớp" thường trực chỉ chiếm đất, còn thẻ bịa thì
 * dạy người dùng rằng số trên màn hình không đáng tin.
 */
export function oViec(
  laGiaoVien: boolean,
  soLop: number,
  baiDangMo: { completed: boolean }[],
): OViec[] {
  if (soLop === 0 && baiDangMo.length === 0) return [];
  if (laGiaoVien) {
    return [
      { nhan: "lớp", so: soLop, di: "classes" },
      { nhan: "bài đã giao", so: baiDangMo.length, di: "assignments" },
    ];
  }
  return [
    { nhan: "lớp của em", so: soLop, di: "classes" },
    { nhan: "bài chưa xong", so: baiDangMo.filter((b) => !b.completed).length,
      di: "assignments" },
  ];
}

export function HomeWorkStrip() {
  const user = useAuthStore((s) => s.user);
  const classes = useClassroomStore((s) => s.classes);
  const assignments = useClassroomStore((s) => s.assignments);
  const loadClasses = useClassroomStore((s) => s.loadClasses);
  const loadAssignments = useClassroomStore((s) => s.loadAssignments);
  const setView = useAppStore((s) => s.setView);

  /* Nạp MỘT LẦN lúc mở, không nhịp lặp: đây là ảnh chụp để định hướng, không
     phải bảng theo dõi trực tiếp — cái đó là `MonitorView`, và nó có nhịp
     riêng vì nó phục vụ một việc khác. */
  useEffect(() => {
    if (!user) return;
    void loadClasses();
    void loadAssignments();
  }, [user, loadClasses, loadAssignments]);

  if (!user) return null;

  const laGiaoVien = user.role === "teacher";
  const dangMo = assignments.filter((a) => !a.closed);
  /* "Xong" đọc từ `myPractice` của CHÍNH người đang đăng nhập — không suy từ
     số thao tác. Suy từ số click là đoán, và đoán về việc học thì sai. */
  const o = oViec(laGiaoVien, classes.length,
                  dangMo.map((a) => ({ completed: !!a.myPractice?.completed })));
  if (o.length === 0) return null;
  const chuaXong = dangMo.filter((a) => !a.myPractice?.completed);

  return (
    <section className="home-work" aria-label={laGiaoVien ? "Lớp của tôi" : "Việc của em"}>
      {o.map((x) => (
        <button key={x.nhan} type="button" className="home-work-o"
                onClick={() => setView(x.di)}>
          <strong className="home-work-so">{x.so}</strong>
          <span className="home-work-nhan">{x.nhan}</span>
        </button>
      ))}
      {!laGiaoVien && chuaXong.length > 0 && (
        <span className="home-work-goi">
          Bài gần nhất: <strong>{chuaXong[0].title}</strong>
        </span>
      )}
    </section>
  );
}
