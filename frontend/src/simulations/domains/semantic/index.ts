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

const semanticProgramModule: SimulationModule<SemanticConfig, SemanticState> = {
  id: "generic.semantic_program",
  domain: "generic",
  title: "Mô phỏng theo chương trình ngữ nghĩa",
  interactionMode: "progressive",
  supportedVisualModes: ["2d"],

  validateConfig: validateSemanticConfig,
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

  /**
   * Ngữ cảnh cho panel Giải thích. Chỉ chở SỰ KIỆN của bước hiện tại — không
   * chở `simulation_id`, tên kiểu primitive hay bất kỳ định danh kĩ thuật nào
   * (bất biến ui-hygiene: chuỗi kĩ thuật không được lọt lên bề mặt học sinh).
   */
  getExplainContext: (state, config) => {
    const buoc = state.timeline[state.cursor];
    return {
      tieuDe: config.title,
      buocHienTai: state.cursor + 1,
      tongSoBuoc: state.timeline.length,
      thuyetMinh: buoc?.narration ?? "",
      mucGop: state.groupingLevel === "iteration" ? "theo vòng lặp" : "từng bước",
    };
  },

  Workspace: SemanticWorkspace,
};

export function registerSemanticDomain(): void {
  registerSimulation(semanticProgramModule as SimulationModule);
}
