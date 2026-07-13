import {
  CONTAINER_TYPES,
  STRUCTURAL_TYPES,
  TEXT_CONTENT_TYPES,
  type ObjectType,
  type SimulationSpec,
} from "./model";

/**
 * EditPolicy v1 (M7.14D) — mirror app/simulation/edit_policy.py.
 *
 * Affordance chỉnh sửa DẪN XUẤT TỪ NĂNG LỰC của cảnh, không phải mặc định cho
 * mọi cảnh generic. Suy từ CHÍNH SPEC (object/process types) — spec vẫn đúng
 * sau khi patch, khác với analysis của đề gốc (không có ở sample offline).
 * TUYỆT ĐỐI không hard-code theo tên bài/môn/tiêu đề.
 *
 * PHẠM VI: `EditFamily` là phân loại của EditPolicy **v1**, KHÔNG phải taxonomy
 * vĩnh viễn của hệ (taxonomy vĩnh viễn là SEMANTIC_ROLES trong manifest).
 * Cảnh LAI dùng precedence bảo thủ — multi-family edit CHƯA hỗ trợ.
 */

export type EditFamily = "spatial" | "structural" | "value_only" | "observation";

export type PatchOpKind = "add_object" | "remove_object" | "update_object" | "connect" | "disconnect";

/** Thao tác UI (không phải patch op): quyết định nút nào hiện ra. */
export type EditUiAction = "add_node" | "add_content" | "connect" | "delete" | "edit_text";

export interface EditPolicy {
  family: EditFamily;
  allowedOps: PatchOpKind[];
  addableTypes: ObjectType[];
  uiActions: EditUiAction[];
  note: string;
}

/** reason_code — hai namespace, mirror backend. */
export const POLICY_OPERATION_NOT_ALLOWED = "policy.operation_not_allowed";
export const POLICY_OBJECT_TYPE_NOT_ALLOWED = "policy.object_type_not_allowed";
export const POLICY_PATH_TOPOLOGY_LOCKED = "policy.path_topology_locked";
export const POLICY_FAMILY_MISMATCH = "policy.family_mismatch"; // fallback, ưu tiên code cụ thể
export const STRUCTURE_INVALID = "structure.invalid";

const RELATIONAL_TYPES = new Set<string>(["node", "edge"]);
const MAX_NESTING_DEPTH = 4; // mirror manifest limits.max_nesting_depth

function hasMoveProcess(spec: SimulationSpec): boolean {
  return spec.processes.some((p) => p.type === "move_along_path");
}

function maxDepth(spec: SimulationSpec): number {
  const byId = new Map(spec.objects.map((o) => [o.id, o]));
  let best = 0;
  for (const o of spec.objects) {
    let depth = 0;
    let cur: string | undefined = o.id;
    const seen = new Set<string>([o.id]);
    while (cur !== undefined && byId.get(cur)?.parent !== undefined) {
      cur = byId.get(cur)!.parent;
      if (cur === undefined || seen.has(cur)) break;
      seen.add(cur);
      depth += 1;
    }
    best = Math.max(best, depth);
  }
  return best;
}

/**
 * Precedence BẢO THỦ (cảnh lai → chọn family hạn chế hơn):
 *   move_along_path > structural > spatial > value_only
 */
export function editPolicyOf(spec: SimulationSpec): EditPolicy {
  const types = new Set<string>(spec.objects.map((o) => o.type));
  const hasStructural = [...types].some((t) => STRUCTURAL_TYPES.has(t));
  const hasRelational = [...types].some((t) => RELATIONAL_TYPES.has(t));

  // 1) Tiến trình di chuyển: thêm/xóa node đổi ngữ nghĩa path → KHÓA topology.
  if (hasMoveProcess(spec)) {
    return {
      family: "observation",
      allowedOps: ["update_object"],
      addableTypes: [],
      uiActions: ["edit_text"],
      note: "Cảnh có tiến trình di chuyển theo đường — cấu trúc topology bị khóa.",
    };
  }

  // 2) Cảnh cấu trúc/nội dung: thêm mục nội dung, KHÔNG thêm điểm/nối.
  if (hasStructural) {
    const addable = [...TEXT_CONTENT_TYPES].sort() as ObjectType[];
    if (maxDepth(spec) + 1 < MAX_NESTING_DEPTH) {
      addable.push(...([...CONTAINER_TYPES].sort() as ObjectType[]));
    }
    return {
      family: "structural",
      allowedOps: ["add_object", "remove_object", "update_object"],
      addableTypes: addable,
      uiActions: ["add_content", "edit_text", "delete"],
      note: "Cảnh nội dung có bố cục — thêm/sửa/xóa mục nội dung.",
    };
  }

  // 3) Cảnh quan hệ điểm–cạnh: CHỈ ở đây mới có Thêm điểm/Nối.
  if (hasRelational) {
    return {
      family: "spatial",
      allowedOps: ["add_object", "remove_object", "update_object", "connect", "disconnect"],
      addableTypes: ["node", "edge", "label"],
      uiActions: ["add_node", "connect", "delete", "edit_text"],
      note: "Cảnh điểm–cạnh — thêm điểm, nối, xóa.",
    };
  }

  // 4) Còn lại (switch/lamp/value_box + rule): tương tác giữ nguyên, không sửa cấu trúc.
  return {
    family: "value_only",
    allowedOps: ["update_object"],
    addableTypes: [],
    uiActions: ["edit_text"],
    note: "Cảnh giá trị/logic — dùng tương tác sẵn có (bật/tắt), không sửa cấu trúc.",
  };
}

/**
 * Có công cụ sửa nào ĐÁNG để mở chế độ Chỉnh sửa không? (M7.14D.1)
 *
 * Suy TỪ POLICY, không hard-code theo binary/logic/tiêu đề. `edit_text` một
 * mình KHÔNG tính là "đáng": nó không có công cụ trực quan nào trên sân khấu,
 * nên mở chế độ Chỉnh sửa chỉ để hiện một ô nhập trống là quảng bá một
 * affordance rỗng. Backend policy vẫn giữ nguyên (update_object qua NL edit vẫn
 * hợp lệ nếu ai đó gọi API) — đây chỉ là chuyện UI không mời gọi.
 */
export function hasMeaningfulEditAffordance(policy: EditPolicy): boolean {
  return policy.uiActions.some((a) => a !== "edit_text");
}

export interface PolicyViolation {
  reasonCode: string;
  error: string;
}

/** Kiểm ops theo policy. null = hợp lệ. Code CỤ THỂ được ưu tiên hơn family_mismatch. */
export function checkOpsAgainstPolicy(
  spec: SimulationSpec,
  ops: { op?: string; object?: { type?: string } }[],
): PolicyViolation | null {
  const policy = editPolicyOf(spec);
  const allowed = new Set<string>(policy.allowedOps);
  const addable = new Set<string>(policy.addableTypes);
  const locked = policy.family === "observation";

  for (const op of ops) {
    const kind = op?.op ?? "";
    if (!allowed.has(kind)) {
      if (locked && ["add_object", "remove_object", "connect", "disconnect"].includes(kind)) {
        return {
          reasonCode: POLICY_PATH_TOPOLOGY_LOCKED,
          error: `Không thể "${kind}" trong cảnh này: có tiến trình di chuyển theo đường, thay đổi topology sẽ làm sai đường đi. ${policy.note}`,
        };
      }
      return {
        reasonCode: POLICY_OPERATION_NOT_ALLOWED,
        error: `Thao tác "${kind}" không phù hợp với cảnh này. ${policy.note}`,
      };
    }
    if (kind === "add_object") {
      const objType = op.object?.type;
      if (!objType || !addable.has(objType)) {
        return {
          reasonCode: POLICY_OBJECT_TYPE_NOT_ALLOWED,
          error:
            `Không thể thêm đối tượng loại "${String(objType)}" vào cảnh này. ` +
            (addable.size > 0
              ? `Chỉ thêm được: ${[...addable].sort().join(", ")}.`
              : "Cảnh này không cho thêm đối tượng mới."),
        };
      }
    }
  }
  return null;
}

/** Nhãn tiếng Việt của loại nội dung thêm được (dropdown "Thêm nội dung"). */
export const ADDABLE_TYPE_LABEL: Record<string, string> = {
  heading: "Tiêu đề",
  paragraph: "Đoạn văn",
  text: "Dòng chữ",
  container: "Khung chứa",
  group: "Nhóm",
  node: "Điểm/nút",
  edge: "Cạnh",
  label: "Nhãn",
};
