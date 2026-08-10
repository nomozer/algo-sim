import { useEffect } from "react";
import { getSimulation } from "../simulations/registry";
import { useAppStore } from "../state/store";
import { challengeEntryVisible } from "./SimulationWorkspace";
import {
  IconNext,
  IconPause,
  IconPlay,
  IconPrev,
  IconReset,
  IconToEnd,
  IconToStart,
} from "./icons";

/**
 * Thanh điều khiển đáy — CAPABILITY-DRIVEN (M2 #4):
 * - module có timeline → đủ bộ về-đầu / lùi / chạy-dừng / tiến / đến-cuối +
 *   seek + tốc độ + Đặt lại + phím tắt;
 * - module không có timeline (exploratory) → chỉ Đặt lại, không nút step giả.
 * M9-UX5: icon là component SVG (`icons.tsx`), không còn ký tự ⏮ ◀ ▶ ⏸ ⏭ ⟳.
 */
export function SimulationControls() {
  const active = useAppStore((s) => s.active);
  const playing = useAppStore((s) => s.playing);
  const speedMs = useAppStore((s) => s.speedMs);
  const nextStep = useAppStore((s) => s.nextStep);
  const prevStep = useAppStore((s) => s.prevStep);
  const toStart = useAppStore((s) => s.toStart);
  const toEnd = useAppStore((s) => s.toEnd);
  const goToStep = useAppStore((s) => s.goToStep);
  const resetSim = useAppStore((s) => s.resetSim);
  const setPlaying = useAppStore((s) => s.setPlaying);
  const setSpeedMs = useAppStore((s) => s.setSpeedMs);

  const mod = active ? getSimulation(active.moduleId) : undefined;
  const challengeOpen = useAppStore((s) => s.challengeOpen);
  const setChallengeOpen = useAppStore((s) => s.setChallengeOpen);
  const timeline = mod?.timeline;

  // Tự chạy: hẹn giờ gọi nextStep; store tự dừng khi hết timeline
  useEffect(() => {
    if (!playing || !timeline) return;
    const id = window.setInterval(() => useAppStore.getState().nextStep(), speedMs);
    return () => window.clearInterval(id);
  }, [playing, speedMs, timeline]);

  // Phím tắt ← → Space — chỉ khi có timeline
  useEffect(() => {
    if (!timeline) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return;
      // Phím tắt TOÀN CỤC không được cướp phím của một control đang focus.
      // Đã cháy HAI lần, cùng một nguyên nhân:
      //  1. node đầu vào A/B/C của boolean_dag (`role="button"`) — bấm Space
      //     vừa đổi giá trị đầu vào, VỪA bật Tự chạy;
      //  2. (W1) nút đáp án dự đoán — `<button>` THẬT, không có `role`, nên
      //     guard cũ không che: đo trong Chrome thấy Space làm `playing = true`
      //     và câu trả lời mất trắng.
      // Nên guard theo NĂNG LỰC "tự xử lý Enter/Space", không theo một thuộc
      // tính cụ thể: control gốc và control giả đều tự lo phím của mình.
      const target = e.target as Element | null;
      if (target?.closest?.('button, a[href], select, [role="button"]')) return;
      if (e.key === "ArrowRight") {
        e.preventDefault();
        useAppStore.getState().nextStep();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        useAppStore.getState().prevStep();
      } else if (e.key === " ") {
        e.preventDefault();
        const s = useAppStore.getState();
        s.setPlaying(!s.playing);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [timeline]);

  if (!active || !mod) return null;

  /* W4B-2Z §20/§23 — Thử thách là HÀNH ĐỘNG PHỤ NẰM CẠNH ĐIỀU KHIỂN, không phải
     một dải nội dung dưới mô hình. Đặt ở đây (thay vì trong `SimulationWorkspace`)
     vì đây đã là chỗ của "việc học sinh làm với mô phỏng" — gộp vào chứ KHÔNG
     đẻ thêm container để chứa nó. Năng lực `predict` và bên chấm `predict.check`
     không đổi một dòng; đây là dời TRÌNH BÀY. */
  const challengeEntry = challengeEntryVisible(mod, active.state) ? (
    <button
      type="button"
      className={`sim-secondary-action${challengeOpen ? " is-active" : ""}`}
      onClick={() => setChallengeOpen(!challengeOpen)}
      aria-expanded={challengeOpen}
    >
      {challengeOpen ? "Đóng thử thách" : "Thử thách: tự dự đoán bước này"}
    </button>
  ) : null;

  // Capability-driven (không switch-case id): hiện nút bước KHI có timeline VÀ
  // thực sự có >1 bước để đi. Cảnh khám phá (1 khung) chỉ hiện Đặt lại —
  // không "step giả". Áp dụng cho cả generic exploratory lẫn module chuyên biệt.
  const hasSteps = timeline !== undefined && timeline.stepCount(active.state) > 1;
  if (!hasSteps) {
    return (
      <div className="player-controls">
        <button className="btn-utility" onClick={resetSim}>
          <IconReset size={14} />
          Đặt lại
        </button>
        <span className="hint">Mô phỏng khám phá — thao tác trực tiếp trên sân khấu.</span>
        {challengeEntry}
      </div>
    );
  }

  const cursor = timeline.currentStep(active.state);
  const total = timeline.stepCount(active.state);
  const last = cursor >= total - 1;

  /* POLISH-3 — GOM NHÓM. Sáu nút, đúng thứ tự, đúng nhãn, không thêm bớt cái
     nào; chỉ bọc thành các nhóm có nghĩa để mắt không phải quét một hàng phẳng:
     [điều hướng bước + play] · [đặt lại] · [tiến độ] · [tốc độ] · [phím tắt]. */
  return (
    <div className="stack" style={{ gap: "var(--sp-xs)" }}>
      <div className="player-controls">
        <span className="control-group control-group-transport">
          <button className="btn-icon" onClick={toStart} disabled={cursor === 0} title="Về đầu">
            <IconToStart />
          </button>
          <button className="btn-icon" onClick={prevStep} disabled={cursor === 0} title="Lùi một bước">
            <IconPrev />
          </button>
          <button
            className="btn-primary btn-play"
            onClick={() => setPlaying(!playing)}
            disabled={last && !playing}
          >
            {playing ? <IconPause size={15} /> : <IconPlay size={15} />}
            {playing ? "Dừng" : "Tự chạy"}
          </button>
          <button className="btn-icon" onClick={nextStep} disabled={last} title="Tiến một bước">
            <IconNext />
          </button>
          <button className="btn-icon" onClick={toEnd} disabled={last} title="Đến cuối">
            <IconToEnd />
          </button>
        </span>

        <span className="control-divider" aria-hidden="true" />

        <button className="btn-utility" onClick={resetSim} title="Dựng lại từ đầu">
          <IconReset size={14} />
          Đặt lại
        </button>

        <span className="step-indicator">
          Bước {cursor + 1} / {total}
        </span>

        <label className="speed-control">
          Tốc độ
          <input
            type="range"
            min={300}
            max={2500}
            step={100}
            value={2800 - speedMs}
            onChange={(e) => setSpeedMs(2800 - Number(e.target.value))}
          />
        </label>
        <span className="hint control-hint">← → tiến/lùi · Space tự chạy</span>
        {challengeEntry}
      </div>
      <input
        type="range"
        min={0}
        max={total - 1}
        value={cursor}
        onChange={(e) => goToStep(Number(e.target.value))}
        style={{ width: "100%" }}
        aria-label="Tua đến bước"
      />
    </div>
  );
}
