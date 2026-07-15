import { lazy } from "react";
import type { ConfigResult, SimulationModule } from "../../types";
import {
  buildEncapState, currentStep, LAYER_LABEL, PROTOCOL_PIECES, pieceForComponents,
  type EncapConfig, type EncapState,
} from "./encap-model";
import { EncapWorkspace, EncapInspector } from "./encap-ui";

/**
 * network.protocol_encapsulation (M10) — mô phỏng TIẾN TRÌNH (progressive).
 *
 * Module THỨ HAI của domain network. Cùng khuôn packet_routing: engine tất định
 * dựng toàn bộ timeline; 2D + 3D dùng chung state; PredictionCapability chấm bằng
 * chính engine. threeD = "pedagogical" vì Z mã hoá TẦNG GIAO THỨC (nghĩa thật).
 */

const Encap3DWorkspace = lazy(() =>
  import("./encap-ui3d").then((m) => ({ default: m.Encap3DWorkspace })),
);

function validateEncapConfig(raw: unknown): ConfigResult<EncapConfig> {
  if (typeof raw !== "object" || raw === null) {
    return { ok: false, error: "Config không phải đối tượng JSON." };
  }
  const r = raw as Record<string, unknown>;
  const payloadLabel =
    typeof r.payloadLabel === "string" && r.payloadLabel.trim()
      ? r.payloadLabel.trim()
      : "Dữ liệu ứng dụng";
  const appProtocol =
    typeof r.appProtocol === "string" && r.appProtocol.trim() ? r.appProtocol.trim() : null;
  const notes = typeof r.notes === "string" ? r.notes : null;
  return { ok: true, config: { payloadLabel, appProtocol, notes } };
}

export function makeEncapsulationModule(): SimulationModule<EncapConfig, EncapState> {
  return {
    id: "network.protocol_encapsulation",
    domain: "network",
    title: "Đóng gói dữ liệu qua các tầng TCP/IP",
    interactionMode: "progressive",
    supportedVisualModes: ["2d", "3d"],
    // M10: 3D SƯ PHẠM — Z = tầng giao thức (nghĩa khái niệm thật, không phải bố cục).
    threeD: {
      role: "pedagogical",
      meaningOfZ: "độ sâu tầng giao thức (Application → Network Access)",
    },

    validateConfig: validateEncapConfig,
    init: buildEncapState,
    apply: (state) => state, // điều khiển qua timeline; không what-if

    timeline: {
      stepCount: (s) => s.steps.length,
      currentStep: (s) => s.cursor,
      goToStep: (s, step) => ({ ...s, cursor: Math.max(0, Math.min(step, s.steps.length - 1)) }),
    },

    /**
     * Nhịp DỰ ĐOÁN — hỏi tại điểm quyết định (add ở máy gửi, remove ở máy nhận).
     * Ground truth = delta của bước KẾ TIẾP (engine đã dựng). LINK+FCS là MỘT
     * đáp án gộp. Chấm là hàm thuần, KHÔNG đụng canonical state.
     */
    predict: {
      challenge: (s) => {
        const next = s.steps[s.cursor + 1];
        if (!next) return null;
        if (next.delta.kind === "add") {
          return {
            question: "Theo em, tầng kế tiếp sẽ THÊM phần thông tin giao thức nào?",
            options: PROTOCOL_PIECES.map((p) => ({ id: p.id, label: p.label })),
          };
        }
        if (next.delta.kind === "remove") {
          return {
            question: "Ở máy nhận, phần thông tin giao thức nào được GỠ tiếp theo?",
            options: PROTOCOL_PIECES.map((p) => ({ id: p.id, label: p.label })),
          };
        }
        return null;
      },
      check: (s, answerId) => {
        const next = s.steps[s.cursor + 1];
        if (!next || (next.delta.kind !== "add" && next.delta.kind !== "remove")) {
          return {
            verdict: "unsupported_to_verify",
            answerId,
            message: "Ở bước này không có phần thông tin giao thức nào được thêm hoặc gỡ để dự đoán.",
          };
        }
        const expected = pieceForComponents(next.delta.componentIds)!;
        const layerName = next.delta.layer ? LAYER_LABEL[next.delta.layer] : "";
        const verb = next.delta.kind === "add" ? "thêm" : "gỡ";
        if (answerId === expected.id) {
          return {
            verdict: "correct",
            answerId,
            expectedId: expected.id,
            message: `Chính xác. Ở bước kế tiếp, ${layerName} ${verb} ${expected.label.toLowerCase()}.`,
          };
        }
        return {
          verdict: "incorrect",
          answerId,
          expectedId: expected.id,
          message: `Chưa đúng. Ở bước kế tiếp, ${layerName} ${verb} ${expected.label.toLowerCase()}.`,
        };
      },
    },

    getExplainContext: (state) => {
      const step = currentStep(state);
      return {
        simulation_id: "network.protocol_encapsulation",
        phase: step.phase,
        side: step.side,
        active_layer: step.activeLayer,
        pdu: step.pdu.map((c) => c.label),
        current_step: state.cursor + 1,
        total_steps: state.steps.length,
        narration: step.narration,
      };
    },

    Workspace: EncapWorkspace,
    renderers: { "3d": Encap3DWorkspace },
    Inspector: EncapInspector,
  };
}
