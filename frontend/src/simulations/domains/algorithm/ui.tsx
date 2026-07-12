import { ArrayView } from "../../../components/ArrayView";
import { VarsView } from "../../../components/VarsView";
import { PseudocodeView } from "../../../components/PseudocodeView";
import { AnalysisCard } from "../../../components/AnalysisCard";
import { fmt } from "../../../core/trace-builder";
import type { WorkspaceProps } from "../../types";
import { activeTrace, clampStep, type AlgorithmConfig, type AlgorithmSimState } from "./model";

/**
 * UI adapter của domain algorithm — nơi DUY NHẤT được biết trace/mảng/mã giả.
 * ArrayView/VarsView/PseudocodeView là đồ riêng của domain này, không phải
 * requirement của core simulation UI (ràng buộc M2 #3).
 * Chỉ đọc state + phát SimAction qua dispatch — không business logic (#3).
 */

type Props = WorkspaceProps<AlgorithmConfig, AlgorithmSimState>;

export function AlgorithmWorkspace({ config, state, busy, dispatch }: Props) {
  const trace = activeTrace(state);
  const step = trace.steps[clampStep(state, state.cursor)];
  const last = state.cursor >= trace.steps.length - 1;
  const doneEvent = step.events.find((e) => e.type === "done");
  // R3.3a — kéo thả chỉ khi: đang dừng, chưa ở nhánh, chưa hết bài
  const canDrag = !busy && !state.branch && !last;

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      {state.branch && (
        <div className="branch-banner">
          <span>
            🧪 <strong>Nhánh thử nghiệm</strong> — em đã đổi chỗ vị trí thứ {state.branch.i + 1}{" "}
            và {state.branch.j + 1} tại bước {state.branch.fromStep + 1}. Dòng chính vẫn được giữ
            nguyên.
          </span>
          <button className="btn-utility" onClick={() => dispatch({ type: "exit_branch" })}>
            ⤺ Quay về dòng chính
          </button>
        </div>
      )}

      <div className="sim-stage">
        <ArrayView
          step={step}
          labels={config.data.labels}
          interactive={canDrag}
          onSwap={(i, j) => dispatch({ type: "whatif_swap", i, j })}
        />
      </div>

      <div className={`narration-bar${step.userAction ? " is-user" : ""}`}>{step.narration}</div>

      {last && doneEvent && doneEvent.type === "done" && (
        <div className="result-banner">
          ✓ {doneEvent.result}
          {state.branch && (
            <span style={{ display: "block", fontWeight: 400, marginTop: 4 }}>
              (kết quả của nhánh thử nghiệm — dãy gốc: [
              {state.trace.steps[state.trace.steps.length - 1].snapshot.array.map(fmt).join("; ")}
              ])
            </span>
          )}
        </div>
      )}

      {canDrag && (
        <span className="hint">
          Kéo một cột thả lên cột khác để thử "nếu đổi chỗ thì sao?"
        </span>
      )}
    </div>
  );
}

export function AlgorithmInspector({ config, state }: Props) {
  const trace = activeTrace(state);
  const step = trace.steps[clampStep(state, state.cursor)];
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <AnalysisCard analysis={config} />
      <VarsView step={step} />
      <PseudocodeView algorithmId={config.algorithm_id} currentLine={step.line} />
    </div>
  );
}
