/**
 * scene3d-student-presentation-policy.ts — TẦNG CHÍNH SÁCH HIỂN THỊ CHO MÔ PHỎNG HỌC SINH.
 *
 * Nguyên tắc kiến trúc cốt lõi của Axo:
 * - Engine chịu trách nhiệm về tính đúng đắn toán học (`INTERNAL_MATH_RESULT`).
 * - Construction Planner chịu trách nhiệm về trình tự dựng hình học (`CONSTRUCTION_OBJECT`, `GEOMETRIC_CONSTRUCTION_RELATION`).
 * - Student Presentation Policy chịu trách nhiệm về những gì học sinh được nhìn thấy trên giao diện mô phỏng:
 *   + Chỉ hiển thị các dữ kiện đề cho trực tiếp (`GIVEN_FACT`), đối tượng hình học được dựng (`CONSTRUCTION_OBJECT`)
 *     và quan hệ hình học tiền đề phục vụ bước dựng (`GEOMETRIC_CONSTRUCTION_RELATION`).
 *   + Giữ nguyên 100% phép tính/kết quả/chứng chỉ ở tầng Engine (và `goalCompletion` của kế hoạch sư phạm)
 *     để kiểm chứng nội bộ, nhưng luồng dựng hình KHÔNG trình bày đáp số mục tiêu hay đại lượng trung gian:
 *     không bảng kết luận, không nút xem kết quả (quyết định sản phẩm 2026-11-05).
 */
import {
  classifyQuantityProvenance,
  type Scene3D,
  type SceneObject,
} from "./scene3d-model";
import { veTrenKhung } from "./scene3d-presentation";
import {
  buildPedagogicalStepNarration,
  canonicalizeSceneFaceTokensInText,
  resolveSemanticObjectContract,
  resolveStudentObjectPresentation,
  verifyVisualContinuity,
  type PedagogicalStepNarration,
  type StudentObjectPresentation,
  type VisualContinuityDimension,
  type VisualContinuityReport,
  type VisualContinuityViolation,
  type VisualContinuityViolationCode,
} from "./scene3d-semantic-policy";

export {
  buildPedagogicalStepNarration,
  canonicalizeSceneFaceTokensInText,
  resolveStudentObjectPresentation,
  verifyVisualContinuity,
  type PedagogicalStepNarration,
  type StudentObjectPresentation,
  type VisualContinuityDimension,
  type VisualContinuityReport,
  type VisualContinuityViolation,
  type VisualContinuityViolationCode,
};

export type SimulationInformationCategory =
  | "GIVEN_FACT"
  | "CONSTRUCTION_OBJECT"
  | "GEOMETRIC_CONSTRUCTION_RELATION"
  | "INTERNAL_MATH_RESULT";

export interface GoalCompletionLike {
  status: "reached" | "missing_goal_output" | "unverified_or_contradictory";
  headline: string;
  detail: string;
  items: readonly {
    id: string;
    label: string;
    valueText: string | null;
    provenance: string;
    witnessSummary?: string | null;
    kind?: string;
  }[];
}

export interface StudentPresentationPolicy {
  /** Bảng phân tích/kết quả toán học không bao giờ hiện trong luồng dựng hình. */
  showMathResultsPanel: false;
  /** Chỉ hiển thị hộp chẩn đoán khi thiếu dữ kiện (`UNDERDETERMINED`) hoặc mâu thuẫn (`INVALID`). */
  showDiagnosticNotice: boolean;
  canRenderGeometricObject: (obj: Pick<SceneObject, "render">) => boolean;
  canDisplayEntityValue: (obj: SceneObject) => boolean;
  canDisplayEntityFormula: (_obj: SceneObject) => boolean;
  formatStudentObjectRole: (obj: SceneObject) => string | null;
  safeWorkspaceTitle: string;
}

/**
 * Làm sạch chuỗi nhãn/vai trò mô tả đối tượng khi hiển thị cho học sinh:
 * giữ nguyên mô tả quan hệ hình học hợp lệ nhưng loại bỏ phần gán đáp số đại số/số học (`= 16π`, `= 4`, `= √2`, ...)
 * nếu payload đầu vào vô tình nhúng kết quả tính toán vào `role` hoặc `label`.
 */
export function sanitizeStudentDescriptorText(raw: string | null | undefined): string {
  if (!raw) return "";
  const trimmed = raw.replace(/«([^»]+)»/gu, "$1").replace(/\s+/gu, " ").trim();
  if (!trimmed) return "";
  // Loại bỏ mệnh đề gán giá trị số/căn/π hoặc biểu thức tham số đại số ở cuối chuỗi
  // (vd: "Bán kính thiết diện = 4", "Khoảng cách d = √2", "Độ dài AH = a√3/3", "Thể tích V = a³/6"),
  // nhưng giữ nguyên biểu thức quan hệ hình học như "d = (SAB) ∩ (SCD)" hay "Q = SD ∩ (MNP)".
  return trimmed
    .replace(
      /\s*(?:⇒|->|=)\s*[-+(]*(?:\d|[√π]|\\sqrt|\\frac|(?:[aRhb]\b|[aRhb](?=[0-9√π^²³/*+-])))[^∩⊥∥;,]*$/u,
      "",
    )
    .trim();
}

export function classifySimulationEntityCategory(
  scene: Scene3D | null | undefined,
  obj: SceneObject,
): SimulationInformationCategory {
  const oc = scene ? resolveSemanticObjectContract(scene, obj.id) : undefined;
  if (obj.type === "quantity" || obj.render === "readout") {
    if (oc) {
      return oc.informationCategory === "GIVEN_FACT" ? "GIVEN_FACT" : "INTERNAL_MATH_RESULT";
    }
    return classifyQuantityProvenance(obj, scene ?? undefined) === "GIVEN"
      ? "GIVEN_FACT"
      : "INTERNAL_MATH_RESULT";
  }
  if (obj.render === "non_visual" || oc?.informationCategory === "INTERNAL_MATH_RESULT") {
    return "INTERNAL_MATH_RESULT";
  }
  if (Boolean(obj.perpendicular_witness)) {
    return "GEOMETRIC_CONSTRUCTION_RELATION";
  }
  return "CONSTRUCTION_OBJECT";
}

export function evaluateStudentPresentationPolicy(
  scene: Scene3D | null | undefined,
  goalCompletion?: GoalCompletionLike | null,
): StudentPresentationPolicy {
  const safeWorkspaceTitle =
    goalCompletion && goalCompletion.items.length > 0
      ? goalCompletion.items
          .map((it) => sanitizeStudentDescriptorText(it.label))
          .filter(Boolean)
          .join(" · ")
      : goalCompletion && goalCompletion.status !== "reached"
        ? goalCompletion.headline
        : "";
  return {
    showMathResultsPanel: false,
    showDiagnosticNotice: Boolean(goalCompletion && goalCompletion.status !== "reached"),
    canRenderGeometricObject: (obj) => veTrenKhung(obj),
    canDisplayEntityValue: (obj) => classifySimulationEntityCategory(scene, obj) === "GIVEN_FACT",
    canDisplayEntityFormula: () => false,
    formatStudentObjectRole: (obj) => {
      if (classifySimulationEntityCategory(scene, obj) === "INTERNAL_MATH_RESULT") {
        return null;
      }
      const cleaned = sanitizeStudentDescriptorText(obj.role);
      if (scene) {
        const sceneObj = scene.objects.find((x) => x.id === obj.id);
        if (cleaned && cleaned.length <= 26 && sceneObj && obj.role !== sceneObj.role) {
          return cleaned;
        }
        const pres = resolveStudentObjectPresentation(scene, obj.id);
        if (pres?.role) return pres.role;
      }
      if (!cleaned) return null;
      return cleaned.length <= 26 ? cleaned : `${cleaned.slice(0, 25).trimEnd()}…`;
    },
    safeWorkspaceTitle,
  };
}
