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
    /* M10: 3D SƯ PHẠM — Z = tầng giao thức (nghĩa khái niệm thật, không phải bố cục).
     * W4B-2S: khai thêm ĐÍCH DANH 3D thắng ở đâu. Cơ chế của bài là LỒNG NHAU —
     * mỗi tầng bọc gói tin của tầng trên rồi tầng nhận bóc ngược lại. Trên mặt
     * phẳng, "bọc" phải vẽ thành xếp chồng hoặc thụt lề, tức mượn một quy ước
     * khác để nói chuyện chứa-đựng; trong không gian nó CHÍNH LÀ chiều sâu. */
    threeD: {
      role: "pedagogical",
      meaningOfZ: "độ sâu tầng giao thức (Application → Network Access)",
      pedagogicalFit: ["relation_clarity", "dimensional_value", "mechanism_fidelity"],
      whyNot2d:
        "2D phải quy ước hoá quan hệ BỌC NHAU thành xếp chồng/thụt lề; ở 3D quan hệ " +
        "chứa-đựng đọc thẳng từ chiều sâu, và gói tin đi xuống rồi đi lên đúng như " +
        "thứ tự đóng/mở gói.",
    },

    /* W4B-2V — BIỂU DIỄN CHÍNH LÀ 2D; 3D LÀ CÁCH XEM BỔ SUNG.
     *
     * Cơ chế của bài có HAI trục: tầng giao thức, và chiều truyền gửi→nhận.
     * Bản 2D nói được CẢ HAI cùng lúc (dọc = tầng, ngang = hai đầu + đường
     * truyền) mà không che khuất gì và không cần điều khiển camera — nên nó là
     * thứ học sinh nên gặp trước. Thêm nữa, xếp chồng KHÔNG phải quy ước đi
     * mượn: sơ đồ chồng tầng chính là quy ước chuẩn của chính miền này.
     *
     * 3D vẫn đáng giữ vì quan hệ BỌC NHAU đọc thẳng từ chiều sâu — nhưng đó là
     * một góc nhìn LÀM RÕ THÊM, không phải cách đọc mặc định. Nên nó là
     * `ALTERNATE_FOR_EXPLANATION`, và học sinh không bị hỏi "2D hay 3D?" trước
     * khi kịp hiểu cơ chế.
     */
    representation: {
      /* W12 §3 — ĐÃ THỬ 3D CÔNG KHAI VÀ ĐÃ TRẢ LẠI. Ghi để không thử lại mù.
         Tôi đổi `primary` sang "3d" bằng đúng một lời khai rồi KHÔNG kiểm cảnh
         3D có đọc được không. Kết quả trên màn thật: nhãn tầng chồng lên nhãn
         MÁY GỬI, chữ trên khối PDU không đọc nổi, bốn phiến gần như nằm ngang
         nên mất hẳn cảm giác BỌC NHAU — tức mất đúng lí do 3D tồn tại.
         Bài học: chuyển biểu diễn công khai là việc THIẾT KẾ, không phải việc
         khai báo. Cơ chế công tắc rẻ nên dễ tưởng việc kia cũng rẻ.
         3D quay lại khi cảnh đọc được ở cả bốn bề rộng — cùng hạng mục với
         `packet_routing` 3D ở `docs/W12_REMAINING.md`.

         Vị thế cũ (đang dùng lại):
         Đóng gói TCP/IP dạy một quan hệ KHÔNG GIAN: mỗi tầng BỌC gói của tầng
         trên. 2D phải diễn đạt quan hệ bọc-nhau bằng hai cột xếp chồng — học
         sinh đọc ra "bốn ô nằm cạnh nhau", tức đúng thứ mà chiều sâu sinh ra để
         nói. Người dùng đã yêu cầu điều này nhiều lần; quyết định là của họ.
         Bỏ luôn công tắc: `learnerFacingModes` trả rỗng khi `alternate` là
         NO_ALTERNATE_NEEDED, nên học sinh không phải trả lời câu hỏi "bài này
         nên đọc ở 2D hay 3D" mà chính họ chưa có cơ sở để trả lời.
         2D KHÔNG bị gỡ — nó còn nguyên cho parity renderer và bằng chứng hồi
         quy (`encap-render3d.test.tsx`, `render-parity.test.tsx`). */
      primary: "2d",
      alternate: "ALTERNATE_FOR_EXPLANATION",
      alternateReason:
        "Chiều sâu cho thấy quan hệ BỌC NHAU giữa các tầng — thứ 2D phải diễn " +
        "đạt bằng xếp chồng. 2D giữ lại làm biểu diễn NỘI BỘ cho parity, không " +
        "bày cho học sinh.",
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

    // (SHELL-N) MỘT nguồn chữ cho cả `encap-ui.tsx` (2D) lẫn `encap-ui3d.tsx` (3D).
    narrate: (state) => ({ text: currentStep(state).narration }),

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
