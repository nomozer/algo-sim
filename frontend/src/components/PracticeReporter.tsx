import { useEffect, useRef } from "react";
import { getSimulation } from "../simulations/registry";
import type { SimulationModule } from "../simulations/types";
import { useClassroomStore, type ProgressBody } from "../state/classroom";
import { useAppStore } from "../state/store";

/**
 * M18 — BẰNG CHỨNG THỰC HÀNH: TỪ STATE CỦA ENGINE, KHÔNG TỪ RENDERER.
 *
 * ─── CHỖ DỄ SAI NHẤT CỦA CẢ TẦNG LỚP HỌC ──────────────────────────────────
 *
 * Cám dỗ tự nhiên là đọc những gì đang hiện trên màn hình. Làm thế thì bảng
 * quan sát của giáo viên phụ thuộc vào renderer nào đang vẽ, chế độ 2D hay 3D,
 * và panel nào đang mở — tức là bằng chứng lớp học sẽ đổi khi giao diện đổi.
 * Đó đúng là lỗi mà bài tiêm lỗi §38.6 dựng lại.
 *
 * Nên mọi con số ở đây đi qua HỢP ĐỒNG NĂNG LỰC của module:
 *   `timeline.currentStep` / `timeline.stepCount` — engine sở hữu;
 *   `exploreOpen` / `challengeOpen` — cờ TRÌNH BÀY của store, đúng là thứ chúng
 *   mô tả ("em ấy đang mở gì"), không phải kết quả.
 *
 * Không có trường nào nói đúng/sai. Số lần cam kết là ĐẾM, không phải điểm.
 *
 * ─── NHỊP GỬI ─────────────────────────────────────────────────────────────
 *
 * Gửi khi state THẬT SỰ đổi (so chữ ký), có chặn nhịp tối thiểu. `§22` cấm phát
 * telemetry mỗi khung hình; chữ ký + hàng đợi 1500ms là cách rẻ nhất đạt điều
 * đó mà không cần hạ tầng gì.
 */

const MIN_INTERVAL_MS = 1500;

/** Chữ ký state — đổi thì mới đáng gửi. */
function signatureOf(body: ProgressBody): string {
  return [body.cursor, body.stepCount, body.exploreOpen, body.challengeOpen,
    body.actionCount, body.commitmentCount, body.completed].join("|");
}

export function readProgress(
  mod: SimulationModule | undefined,
  state: unknown,
  flags: { exploreOpen: boolean; challengeOpen: boolean; actionCount: number;
    commitmentCount: number },
): ProgressBody {
  let cursor = 0;
  let stepCount = 0;
  if (mod?.timeline) {
    try {
      cursor = mod.timeline.currentStep(state);
      stepCount = mod.timeline.stepCount(state);
    } catch { /* module chưa dựng xong state ⇒ để 0, không đoán */ }
  }
  return {
    cursor,
    stepCount,
    exploreOpen: flags.exploreOpen,
    challengeOpen: flags.challengeOpen,
    actionCount: flags.actionCount,
    commitmentCount: flags.commitmentCount,
    /* "Xong" = đã tới bước cuối của timeline do ENGINE dựng. Bài không có
       timeline thì không có khái niệm xong theo bước ⇒ để false, không bịa. */
    completed: stepCount > 1 && cursor >= stepCount - 1,
  };
}

/**
 * Component KHÔNG VẼ GÌ. Nó chỉ theo dõi phiên và gửi bằng chứng.
 * Không có bài nào đang làm ⇒ không gửi gì cả (tự luyện không đẻ ra telemetry).
 */
export function PracticeReporter() {
  const assignment = useAppStore((s) => s.activeAssignment);
  const active = useAppStore((s) => s.active);
  const exploreOpen = useAppStore((s) => s.exploreOpen);
  const challengeOpen = useAppStore((s) => s.challengeOpen);
  const report = useClassroomStore((s) => s.reportProgress);

  const lastSig = useRef<string>("");
  const lastSent = useRef<number>(0);
  const actions = useRef<number>(0);
  const commitments = useRef<number>(0);
  const timer = useRef<number | null>(null);

  /* Đổi bài ⇒ đếm lại từ đầu. Không reset thì số thao tác của bài trước chảy
     sang bài sau và bảng quan sát nói một điều không xảy ra. */
  useEffect(() => {
    actions.current = 0;
    commitments.current = 0;
    lastSig.current = "";
  }, [assignment?.id]);

  const stateRef = active?.state;
  useEffect(() => { if (stateRef !== undefined) actions.current += 1; }, [stateRef]);

  const prediction = useAppStore((s) => s.prediction);
  useEffect(() => { if (prediction) commitments.current += 1; }, [prediction]);

  useEffect(() => {
    if (!assignment || !active) return;
    const mod = getSimulation(active.moduleId) as SimulationModule | undefined;
    const body = readProgress(mod, active.state, {
      exploreOpen, challengeOpen,
      actionCount: actions.current, commitmentCount: commitments.current,
    });
    const sig = signatureOf(body);
    if (sig === lastSig.current) return;

    const send = () => {
      lastSig.current = sig;
      lastSent.current = Date.now();
      void report(assignment.id, body);
    };
    const since = Date.now() - lastSent.current;
    if (since >= MIN_INTERVAL_MS) { send(); return; }
    /* Còn trong nhịp chặn: hẹn gửi phần dư. Hẹn LẠI mỗi lần state đổi nên chỉ
       lần cuối cùng trong chuỗi thao tác nhanh được gửi. */
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(send, MIN_INTERVAL_MS - since);
    return () => { if (timer.current) window.clearTimeout(timer.current); };
  }, [assignment, active, exploreOpen, challengeOpen, prediction, report]);

  return null;
}
