/**
 * Phân loại lỗi tại nguồn cho không gian mô phỏng 3D và quy định chính sách
 * khôi phục có kiểm soát (không retry mù quáng dữ liệu toán học sai, giữ đề bài
 * và các bước dựng hợp lệ khi chỉ lớp Renderer WebGL/Canvas gặp sự cố).
 */

export type SimulationErrorCategory =
  | "invalid_scene_data"
  | "geometry_contradiction"
  | "unsupported_simulation"
  | "renderer_runtime_failure";

export type SimulationErrorCode =
  | "SCENE_INVALID_SCHEMA"
  | "SCENE_UNAVAILABLE"
  | "GEOMETRY_CONTRADICTION"
  | "UNSUPPORTED_SIMULATION"
  | "WEBGL_INIT_FAILED"
  | "WEBGL_CONTEXT_LOST"
  | "VIEWER_RENDER_CRASH";

export interface SimulationErrorClassification {
  readonly code: SimulationErrorCode | string;
  readonly category: SimulationErrorCategory;
  readonly recoverable: boolean;
  readonly omitConstructionSteps: boolean;
  readonly suppressStageNavigationActions: boolean;
}

export interface ClassifySimulationErrorInput {
  readonly invalidSceneReason?: string | null;
  readonly unavailableOverride?: boolean;
  readonly mathValid?: boolean;
  readonly contradictionId?: string | null;
  readonly unsupported?: boolean;
  readonly viewerBoundaryCrashed?: boolean;
  readonly stageWebglFailed?: boolean;
  readonly webglPhase?: "healthy" | "recovering" | "failed";
  readonly webglAttempt?: number;
}

export function classifySimulationError(
  input: ClassifySimulationErrorInput,
): SimulationErrorClassification | null {
  if (input.invalidSceneReason) {
    return {
      code: input.unavailableOverride ? "SCENE_UNAVAILABLE" : "SCENE_INVALID_SCHEMA",
      category: "invalid_scene_data",
      recoverable: false,
      omitConstructionSteps: true,
      suppressStageNavigationActions: true,
    };
  }

  if (input.mathValid === false) {
    return {
      code: input.contradictionId?.trim() || "GEOMETRY_CONTRADICTION",
      category: "geometry_contradiction",
      recoverable: false,
      omitConstructionSteps: true,
      suppressStageNavigationActions: true,
    };
  }

  if (input.unsupported) {
    return {
      code: "UNSUPPORTED_SIMULATION",
      category: "unsupported_simulation",
      recoverable: false,
      omitConstructionSteps: true,
      suppressStageNavigationActions: true,
    };
  }

  if (input.viewerBoundaryCrashed) {
    return {
      code: "VIEWER_RENDER_CRASH",
      category: "renderer_runtime_failure",
      recoverable: true,
      omitConstructionSteps: false,
      suppressStageNavigationActions: true,
    };
  }

  if (input.stageWebglFailed || (input.webglPhase && input.webglPhase !== "healthy")) {
    return {
      code: (input.webglAttempt ?? 0) > 0 ? "WEBGL_CONTEXT_LOST" : "WEBGL_INIT_FAILED",
      category: "renderer_runtime_failure",
      recoverable: true,
      omitConstructionSteps: false,
      suppressStageNavigationActions: true,
    };
  }

  return null;
}

export function shouldOmitDockConstructionSteps(
  classification: SimulationErrorClassification | null,
): boolean {
  return Boolean(classification?.omitConstructionSteps);
}

/**
 * Bảo vệ trước object `Scene3D` đã bị đóng băng (`Object.freeze`) khi đính kèm
 * metadata phiên hiển thị, tránh làm sập pipeline hình học hợp lệ.
 */
export function ensureMutableSceneForAttachment<T extends object>(scene: T): T {
  if (!scene || typeof scene !== "object") return scene;
  if (Object.isFrozen(scene) || !Object.isExtensible(scene)) {
    return { ...scene };
  }
  return scene;
}
