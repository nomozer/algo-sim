/**
 * THEO DÕI LỚP — trang riêng, KHÔNG phải ngăn kéo đè lên canvas.
 *
 * ─── VÌ SAO LÀ MỘT TRANG, KHÔNG PHẢI MỘT CỘT ────────────────────────────
 *
 * Ba mươi hai học sinh cạnh một khung 3D thì cả hai đều không dùng được: canvas
 * mất một nửa bề rộng, còn bảng thì chật tới mức phải cắt chữ. Dạy và theo dõi
 * là hai VIỆC KHÁC NHAU của cùng một người, không phải hai vùng của một màn
 * hình — nên chúng là hai chế độ, chuyển qua lại một cú bấm.
 *
 * ─── CÁI BẢNG NÀY KHÔNG NÓI ─────────────────────────────────────────────
 *
 * Không điểm. Không đúng/sai. Không "em này đang gặp khó khăn". Đứng lâu ở một
 * bước có thể là đang nghĩ, và suy từ số lần bấm ra năng lực là đúng thứ bất
 * biến #27 cấm — engine tất định là nơi duy nhất phán được điều gì đúng.
 *
 * Bộ lọc vì thế mang tên TRUNG TÍNH: «Chưa hoạt động gần đây» mô tả một sự
 * kiện quan sát được; «đang gặp khó» thì không.
 */
import { useEffect, useMemo, useState } from "react";
import { NHIP_THEO_DOI_MS } from "../state/classroom-sync";
import { useClassroomStore, type MonitorRow } from "../state/classroom";

type Loc = "tat-ca" | "can-giup" | "im-lang";

/** Ngưỡng "chưa hoạt động gần đây". Không phải phán quyết — chỉ là một mốc. */
const IM_LANG_MS = 90_000;

function tuoi(updatedAt: string | null, mocMayChu: string): number | null {
  if (!updatedAt) return null;
  const t = Date.parse(updatedAt);
  const now = Date.parse(mocMayChu);
  if (Number.isNaN(t) || Number.isNaN(now)) return null;
  return Math.max(0, now - t);
}

function docTuoi(ms: number | null): string {
  if (ms === null) return "chưa bắt đầu";
  const giay = Math.round(ms / 1000);
  if (giay < 60) return `${giay} giây trước`;
  return `${Math.round(giay / 60)} phút trước`;
}

function docCho(giay: number | null): string {
  if (giay === null) return "";
  if (giay < 60) return `${giay} giây`;
  return `${Math.floor(giay / 60)} phút ${giay % 60} giây`;
}

/** Enum máy → tiếng người. Chuỗi lạ thì KHÔNG hiện, không đoán. */
const VIEC: Record<string, string> = {
  SELECT_ENTITY: "Chọn một vật",
  INSPECT_ENTITY: "Xem chi tiết",
  ISOLATE_ENTITY: "Chỉ xem một phần",
  EXPLODE_SOLID: "Tách khối",
  COLLAPSE_SOLID: "Ráp khối lại",
  STEP_CHANGE: "Đổi bước",
  REQUEST_HELP: "Giơ tay",
  CANCEL_HELP: "Hạ tay",
};

export function MonitorView({
  classId, className, onBack,
}: {
  classId: number;
  className: string;
  onBack: () => void;
}) {
  const monitor = useClassroomStore((s) => s.monitor);
  const load = useClassroomStore((s) => s.loadMonitor);
  const clearHelp = useClassroomStore((s) => s.clearHelp);
  const [loc, setLoc] = useState<Loc>("tat-ca");

  /* Nhịp CHẬM hơn nhịp lệnh, và có lý do: bảng trễ bốn giây thì không ai
     thiệt, còn lệnh trễ bốn giây thì cả lớp nhìn nhầm chỗ lúc thầy đang nói. */
  useEffect(() => {
    void load(classId);
    const t = setInterval(() => void load(classId), NHIP_THEO_DOI_MS);
    return () => clearInterval(t);
  }, [classId, load]);

  const rows: MonitorRow[] = monitor?.classroomId === classId ? monitor.rows : [];
  const moc = monitor?.serverNow ?? new Date().toISOString();

  const canGiup = rows.filter((r) => r.helpRequested).length;

  const hien = useMemo(() => {
    const co = rows.filter((r) => {
      if (loc === "can-giup") return r.helpRequested;
      if (loc === "im-lang") {
        const t = tuoi(r.updatedAt, moc);
        return t === null || t > IM_LANG_MS;
      }
      return true;
    });
    /* Giơ tay lên đầu — đó là việc cần làm ngay. Sau đó theo độ cũ. KHÔNG sắp
       theo "số lần bấm": xếp hạng học sinh bằng một con số hoạt động là dựng
       một bảng điểm mà không ai gọi nó là bảng điểm. */
    return co.slice().sort((a, b) => {
      if (a.helpRequested !== b.helpRequested) return a.helpRequested ? -1 : 1;
      return (tuoi(b.updatedAt, moc) ?? 0) - (tuoi(a.updatedAt, moc) ?? 0);
    });
  }, [rows, loc, moc]);

  return (
    <section className="monitor">
      <header className="monitor-dau">
        <div>
          <h2 className="monitor-ten">{className}</h2>
          <p className="monitor-tom">
            {rows.length} học sinh
            {canGiup > 0 && <> · <strong>{canGiup} cần hỗ trợ</strong></>}
          </p>
        </div>
        <button type="button" className="btn-utility" onClick={onBack}>
          Quay lại lớp học
        </button>
      </header>

      <div className="monitor-loc" role="group" aria-label="Lọc danh sách">
        {([["tat-ca", "Tất cả"],
           ["can-giup", `Cần hỗ trợ${canGiup ? ` (${canGiup})` : ""}`],
           ["im-lang", "Chưa hoạt động gần đây"]] as [Loc, string][])
          .map(([k, nhan]) => (
            <button key={k} type="button"
              className={`btn-utility${loc === k ? " is-active" : ""}`}
              aria-pressed={loc === k} onClick={() => setLoc(k)}>
              {nhan}
            </button>
          ))}
      </div>

      {hien.length === 0 ? (
        <p className="monitor-trong">
          {rows.length === 0
            ? "Chưa có học sinh nào trong lớp bắt đầu làm bài."
            : "Không có em nào trong nhóm này."}
        </p>
      ) : (
        <ul className="monitor-luoi">
          {hien.map((r) => {
            const t = tuoi(r.updatedAt, moc);
            return (
              <li key={r.studentId}
                className={`monitor-the${r.helpRequested ? " can-giup" : ""}`}>
                <div className="monitor-the-dau">
                  <strong>{r.studentName}</strong>
                  <span className="monitor-tuoi">{docTuoi(t)}</span>
                </div>
                <dl className="monitor-chi-tiet">
                  {r.currentStep !== null && (
                    <>
                      <dt>Bước</dt>
                      <dd>{r.currentStep + 1}{r.stepCount ? ` / ${r.stepCount}` : ""}</dd>
                    </>
                  )}
                  {r.selectedId && (
                    <>
                      <dt>Đang xem</dt>
                      <dd>{r.selectedId}</dd>
                    </>
                  )}
                  {r.lastAction && VIEC[r.lastAction] && (
                    <>
                      <dt>Vừa làm</dt>
                      <dd>{VIEC[r.lastAction]}</dd>
                    </>
                  )}
                </dl>
                {r.helpRequested && (
                  <div className="monitor-giup">
                    <span>Cần hỗ trợ · chờ {docCho(r.helpWaitingSeconds)}</span>
                    <button type="button" className="btn-utility"
                      onClick={() => void clearHelp(classId, r.studentId)}>
                      Đã hỗ trợ
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
