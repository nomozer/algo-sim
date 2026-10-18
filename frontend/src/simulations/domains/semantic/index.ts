/**
 * Đăng ký route sinh ngữ nghĩa `generic.semantic_program`.
 *
 * ⚠️ SERVING GATE (spec §10.2): đăng ký route **KHÔNG** đồng nghĩa bật cho học
 * sinh. Backend chỉ phát envelope của route này sau khi ĐỦ chuỗi assurance
 * (`RequestContract → P2 → C₁a → validator → interpreter → C₁b → C₂ → STRONG`).
 * Module ở đây chỉ bảo đảm: khi envelope tới, có thứ vẽ được nó.
 *
 * 2D ONLY theo MVP §1.1.
 */
import { registerSimulation } from "../../registry";
import type { SimulationModule } from "../../types";
import {
  buildSemanticState,
  goToStep,
  stepCount,
  validateSemanticConfig,
  type SemanticConfig,
  type SemanticState,
} from "./model";
import { SemanticWorkspace } from "./ui";
import { hopLeScene3D } from "../geometry/scene3d-model";
import { veKhongGian } from "../geometry/scene3d-chart";

const semanticProgramModule: SimulationModule<SemanticConfig, SemanticState> = {
  id: "generic.semantic_program",
  domain: "generic",
  title: "Mô phỏng theo chương trình ngữ nghĩa",
  interactionMode: "progressive",
  supportedVisualModes: ["2d"],

  validateConfig: validateSemanticConfig,
  validateEnvelope: (envelope) => {
    const scene = (envelope as { scene3d?: unknown }).scene3d;
    // No scene is the legacy 2D contract; a supplied invalid scene is never a 2D fallback.
    if (scene != null) {
      if (!hopLeScene3D(scene)) return { ok: false, error: "Dữ liệu hình không vượt qua kiểm tra an toàn. Hãy phân tích lại đề." };
      try {
        veKhongGian(scene);
      } catch {
        return { ok: false, error: "Hệ chưa thể hiển thị an toàn dữ liệu hình này. Hãy phân tích lại đề." };
      }
    }
    return validateSemanticConfig(envelope.config);
  },
  init: (config) => buildSemanticState(config),

  // Chưa có thao tác học sinh nào trên route này: mô phỏng do chương trình đã
  // sinh quyết định, và `explore` phải chạm CƠ CHẾ chứ không phải trang trí
  // (COVERAGE §2.6). Không khai `explore` = không có lối vào — mặc định an toàn.
  apply: (state) => state,

  timeline: {
    stepCount,
    currentStep: (state) => state.cursor,
    goToStep,
  },

  narrate: (state) => {
    const buoc = state.timeline[state.cursor];
    return buoc ? { text: buoc.narration } : null;
  },

  Workspace: SemanticWorkspace,
};

export function registerSemanticDomain(): void {
  registerSimulation(semanticProgramModule as SimulationModule);
}
