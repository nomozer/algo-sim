import { ArrayView } from "../../../components/ArrayView";
import { VarsView } from "../../../components/VarsView";
import { PseudocodeView } from "../../../components/PseudocodeView";
import { IconCheck } from "../../../components/icons";
import { runScan, scanPseudocode, validateScanSpec, type ScanSpec } from "../../../core/scan";
import type { Trace } from "../../../core/types";
import type { ConfigResult, SimulationModule, WorkspaceProps } from "../../types";

/**
 * Module `algorithm.scan` (M12) — adapter MỎNG quanh scan-interpreter tất định
 * (`core/scan.ts`), cùng khuôn với 8 module thuật toán: init chạy engine →
 * Trace là timeline; UI đọc state, không business logic.
 *
 * Đây KHÔNG phải engine mới và KHÔNG phải "module cho một bài": MỘT module
 * này phục vụ CẢ HỌ bài single-pass qua ScanSpec khai báo (AI cấu hình enum
 * đóng — không sở hữu vòng lặp/timeline/kết quả). Bài đã có mô phỏng chuyên
 * biệt (find_max, count_if…) vẫn đi đường chuyên biệt; module này nhận các
 * BIẾN THỂ ngoài 8 bài (vd tìm phần tử ĐẦU TIÊN thỏa bất đẳng thức).
 *
 * V1 hoãn có chủ đích: prediction (decision theo cơ chế cần thiết kế riêng)
 * và what-if drag — tương tác trang trí không được admit (COVERAGE §2.6).
 */

export interface ScanSimState {
  spec: ScanSpec;
  trace: Trace;
  cursor: number;
}

function clampCursor(state: ScanSimState, step: number): number {
  return Math.max(0, Math.min(step, state.trace.steps.length - 1));
}

type Props = WorkspaceProps<ScanSpec, ScanSimState>;

export function ScanWorkspace({ state }: Props) {
  const step = state.trace.steps[clampCursor(state, state.cursor)];
  const last = state.cursor >= state.trace.steps.length - 1;
  const doneEvent = step.events.find((e) => e.type === "done");

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      <div className="sim-stage">
        <ArrayView step={step} labels={state.spec.labels ?? null} />
      </div>
      <div className="narration-bar">{step.narration}</div>
      {last && doneEvent && doneEvent.type === "done" && (
        <div className="result-banner">
          <IconCheck size={15} /> {doneEvent.result}
        </div>
      )}
    </div>
  );
}

export function ScanInspector({ state }: Props) {
  const step = state.trace.steps[clampCursor(state, state.cursor)];
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <VarsView step={step} />
      <PseudocodeView lines={scanPseudocode(state.spec)} currentLine={step.line} />
    </div>
  );
}

export function makeScanModule(): SimulationModule<ScanSpec, ScanSimState> {
  return {
    id: "algorithm.scan",
    domain: "algorithm",
    title: "Quét dãy một lượt",
    interactionMode: "progressive",
    supportedVisualModes: ["2d"],

    validateConfig: (raw): ConfigResult<ScanSpec> => {
      const v = validateScanSpec(raw);
      return v.ok ? { ok: true, config: v.spec } : { ok: false, error: v.error };
    },

    // Timeline sinh TẠI ĐÂY bởi interpreter tất định — không phải từ LLM (R0).
    init: (spec) => ({ spec, trace: runScan(spec), cursor: 0 }),

    apply: (state) => state, // v1: không action nào — thao tác qua timeline

    timeline: {
      stepCount: (s) => s.trace.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: clampCursor(s, step) }),
    },

    getExplainContext: (state) => {
      const step = state.trace.steps[clampCursor(state, state.cursor)];
      return {
        simulation_id: "algorithm.scan",
        pseudocode: scanPseudocode(state.spec),
        current_step: state.cursor + 1,
        total_steps: state.trace.steps.length,
        narration: step.narration,
        array: step.snapshot.array,
        variables: step.snapshot.vars,
        marks: step.snapshot.marks,
      };
    },

    Workspace: ScanWorkspace,
    Inspector: ScanInspector,
  };
}
