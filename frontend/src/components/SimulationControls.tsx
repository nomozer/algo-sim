import { useEffect } from "react";
import { getSimulation } from "../simulations/registry";
import { useAppStore } from "../state/store";

/**
 * Thanh điều khiển đáy — CAPABILITY-DRIVEN (M2 #4):
 * - module có timeline → đủ bộ ⏮ ◀ ▶/⏸ ▶ ⏭ + seek + tốc độ + Reset + phím tắt;
 * - module không có timeline (exploratory) → chỉ Reset, không nút step giả.
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

  // Capability-driven (không switch-case id): hiện nút bước KHI có timeline VÀ
  // thực sự có >1 bước để đi. Cảnh khám phá (1 khung) chỉ hiện Đặt lại —
  // không "step giả". Áp dụng cho cả generic exploratory lẫn module chuyên biệt.
  const hasSteps = timeline !== undefined && timeline.stepCount(active.state) > 1;
  if (!hasSteps) {
    return (
      <div className="player-controls">
        <button className="btn-utility" onClick={resetSim}>
          ⟳ Đặt lại
        </button>
        <span className="hint">Mô phỏng khám phá — thao tác trực tiếp trên sân khấu.</span>
      </div>
    );
  }

  const cursor = timeline.currentStep(active.state);
  const total = timeline.stepCount(active.state);
  const last = cursor >= total - 1;

  return (
    <div className="stack" style={{ gap: "var(--sp-xs)" }}>
      <div className="player-controls">
        <button className="btn-icon" onClick={toStart} disabled={cursor === 0} title="Về đầu">
          ⏮
        </button>
        <button className="btn-icon" onClick={prevStep} disabled={cursor === 0} title="Lùi một bước">
          ◀
        </button>
        <button
          className="btn-primary"
          onClick={() => setPlaying(!playing)}
          disabled={last && !playing}
          style={{ minWidth: 110 }}
        >
          {playing ? "⏸ Dừng" : "▶ Tự chạy"}
        </button>
        <button className="btn-icon" onClick={nextStep} disabled={last} title="Tiến một bước">
          ▶
        </button>
        <button className="btn-icon" onClick={toEnd} disabled={last} title="Đến cuối">
          ⏭
        </button>
        <button className="btn-utility" onClick={resetSim} title="Dựng lại từ đầu">
          ⟳ Đặt lại
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
        <span className="hint">← → tiến/lùi · Space tự chạy</span>
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
