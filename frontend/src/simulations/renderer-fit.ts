import { arrayChartLayout } from "../components/ArrayView";
import { TREE_SLOT_W, treeLayoutSize } from "./domains/tree/layout-size";
import { useAppStore } from "../state/store";

/**
 * HỢP ĐỒNG VỪA-KHUNG CỦA RENDERER (W4B-2A).
 *
 * Một renderer hỏng được theo **hai** hướng, không phải một:
 *
 *   UNDER_UTILIZED   khung rộng ra mà hình vẽ đứng yên dù chưa chạm trần;
 *   OVER_EXPANDED    hình vẽ phình quá mật độ ngữ nghĩa đã khai.
 *
 * Nên cổng chấm KHÔNG được là "hình phải chiếm ≥ X% sân khấu": luật đó thưởng
 * cho hướng hỏng thứ hai. Chính lỗi đó đã xảy ra thật trong milestone này — trần
 * cột đầu tiên đặt ở 96px làm bảy cột ra 864px, thích ứng đúng về kỹ thuật nhưng
 * bố cục mất cân đối.
 *
 * File này là **chủ sở hữu khai báo** để runner đo không phải hard-code theo
 * `moduleId`. Mười target họ `ArrayView` thừa hưởng CÙNG một hợp đồng.
 */

export type RendererFitClass = "adaptive_layout" | "canvas_fill" | "fixed_semantic_size";

export interface RendererFit {
  simulationId: string;
  cls: RendererFitClass;
  /**
   * Bề rộng bố cục tối đa theo hợp đồng ngữ nghĩa, tính cho TRẠNG THÁI HIỆN
   * TẠI (số phần tử thật). `null` = lớp này không khai trần bề rộng.
   */
  semanticMaxWidth: number | null;
  /**
   * RÀNG BUỘC MẬT ĐỘ ĐỘC LẬP với cài đặt — bề rộng tối đa cho mỗi phần tử.
   *
   * `semanticMaxWidth` được tính TỪ chính hàm bố cục, nên nếu ai đó nới trần
   * cột thì trần cũng nới theo và cổng chấm sẽ không bao giờ thấy vượt mức.
   * Con số dưới đây là ràng buộc **khai riêng**: nó phát biểu điều kiện sư phạm
   * (hai cột kề nhau phải nằm gọn trong một lần nhìn) chứ không mô tả cài đặt,
   * nên nới trần cột lên 96px sẽ làm nó ĐỎ.
   *
   * `null` = lớp này không khai ràng buộc mật độ.
   */
  maxWidthPerItem: number | null;
  /** Số phần tử ở trạng thái hiện tại, nếu đếm được. */
  itemCount: number | null;
  /** Vì sao lớp này — để artifact đọc được mà không phải tra mã. */
  reason: string;
}

/**
 * Bề rộng tối đa cho mỗi cột của biểu đồ dãy.
 *
 * Đây là **ràng buộc thiết kế hiện hành**, suy từ yêu cầu đọc được của phép so
 * sánh hai cột KỀ NHAU — cơ chế trung tâm của các bài sắp xếp. Nó **không phải**
 * bằng chứng về tác động học tập, và không được trích dẫn như vậy.
 */
export const ARRAY_MAX_WIDTH_PER_ITEM = 100;

/** Target vẽ bằng `ArrayView` — cùng một chủ sở hữu sizing. */
export const ARRAY_VIEW_TARGETS = new Set([
  "algorithm.scan",
  "algorithm.find_max",
  "algorithm.find_min",
  "algorithm.count_if",
  "algorithm.sum_if",
  "algorithm.linear_search",
  "algorithm.binary_search",
  "algorithm.bubble_sort",
  "algorithm.selection_sort",
  "algorithm.insertion_sort",
]);

/** Renderer dùng canvas (Three.js) — canvas bám khung, vật thể giữ tỉ lệ ngữ nghĩa. */
export const CANVAS_TARGETS = new Set([
  "network.packet_routing",
  "network.protocol_encapsulation",
]);

/**
 * Target mà phóng to hình KHÔNG tăng giá trị nhận thức. Với lớp này, phản ứng
 * 0px theo bề rộng là **chủ đích**; thứ cần xét là sân khấu có giữ lại khoảng
 * trống vô nghĩa hay không — một phép đo khác, không thuộc bề rộng hình.
 */
export const FIXED_SIZE_TARGETS = new Set([
  "logic.and_gate",
  "binary.decimal_to_binary",
  "binary.base_conversion",
  "binary.character_encoding",
  "algorithm.bounded_control_flow",
]);

/**
 * Renderer dạng BẢNG — hợp đồng riêng, không so tỉ lệ với renderer SVG.
 * Bảng đã khai  trong  nên nó vốn co giãn theo khung;
 * đo được 1306x273 trong sân khấu 1306x273 (tỉ lệ 1.0). Phép đo "phần tử vẽ
 * lớn nhất" trước đây bắt nhầm một icon 12x12 rồi báo nó chiếm 1% - lỗi của
 * phép đo, không phải của renderer.
 */
export const TABLE_TARGETS = new Set(["database.relational_table_query"]);

/** Số phần tử của dãy ở trạng thái hiện tại, nếu renderer là ArrayView. */
function arrayItemCount(state: unknown): number | null {
  const s = state as { trace?: { steps?: { snapshot?: { array?: unknown[] } }[] }; cursor?: number };
  const steps = s?.trace?.steps;
  if (!Array.isArray(steps) || steps.length === 0) return null;
  const at = Math.max(0, Math.min(s.cursor ?? 0, steps.length - 1));
  const arr = steps[at]?.snapshot?.array;
  return Array.isArray(arr) ? arr.length : null;
}

export function rendererFitOf(
  simulationId: string,
  state: unknown,
  visualMode: string = "2d",
): RendererFit {
  /* Lớp phụ thuộc CHẾ ĐỘ TRÌNH BÀY, không chỉ phụ thuộc target. Hai target
     mạng có canvas Three.js, nhưng ở chế độ 2D chúng vẽ bằng SVG và phải được
     chấm theo hợp đồng adaptive. Guard bắt được đúng ca này ngay lần chạy đầu:
     `packet_routing` 2D bị xếp nhầm `canvas_fill` rồi báo canvas 610px không
     bám sân khấu 1306px — trong khi nó có phải canvas đâu. */
  if (CANVAS_TARGETS.has(simulationId) && visualMode !== "3d") {
    return { simulationId, cls: "adaptive_layout", semanticMaxWidth: null,
             maxWidthPerItem: null, itemCount: null,
             reason: "chế độ 2D của một target có 3D — SVG, chưa khai trần bề rộng" };
  }
  if (ARRAY_VIEW_TARGETS.has(simulationId)) {
    const n = arrayItemCount(state);
    // Trần = bố cục ở bề rộng vô hạn: chính là lúc cột chạm trần ngữ nghĩa.
    const max = n === null ? null : arrayChartLayout(n, Number.MAX_SAFE_INTEGER).width;
    return {
      simulationId,
      cls: "adaptive_layout",
      semanticMaxWidth: max,
      maxWidthPerItem: ARRAY_MAX_WIDTH_PER_ITEM,
      itemCount: n,
      reason: "ArrayView — bố cục tính lại từ bề rộng khả dụng, có trần mật độ",
    };
  }
  if (CANVAS_TARGETS.has(simulationId)) {
    return { simulationId, cls: "canvas_fill", semanticMaxWidth: null,
             maxWidthPerItem: null, itemCount: null,
             reason: "canvas Three.js — bám khung sân khấu, vật thể giữ tỉ lệ ngữ nghĩa" };
  }
  if (TABLE_TARGETS.has(simulationId)) {
    return { simulationId, cls: "adaptive_layout", semanticMaxWidth: null,
             maxWidthPerItem: null, itemCount: null,
             reason: "bảng HTML width:100% - đã bám khung theo CSS, hợp đồng riêng" };
  }
  /* W5AA — LỚP SVG TỰ TÍNH KHUNG: khai TRẦN để thẻ nâng sàn được.
     Trước wave này chỉ nhóm `ArrayView` khai `semanticMaxWidth`, nên 14 target
     còn lại rơi về sàn mặc định 560px trong khi `algorithm.find_max` ra 1443px —
     đo được, và đúng là thứ người dùng thấy là "mỗi cái một design riêng".
     Renderer cây đã tự chặn (`maxWidth: w`), nên nâng sàn KHÔNG làm nó phình:
     cây giãn tới trần của chính nó rồi dừng. */
  if (simulationId === "tree.traversal") {
    const config = (state as { config?: unknown } | null)?.config;
    const w = config ? treeLayoutSize(config as Parameters<typeof treeLayoutSize>[0]).w : null;
    const totalWidth = w ? w + 360 : null;
    return { simulationId, cls: "adaptive_layout", semanticMaxWidth: totalWidth,
             maxWidthPerItem: TREE_SLOT_W, itemCount: null,
             reason: "SVG cây — trần suy từ chính hàm bố cục (layout-size.ts) + cột trạng thái side-by-side" };
  }
  if (simulationId === "network.graph_traversal") {
    return { simulationId, cls: "adaptive_layout", semanticMaxWidth: 960,
             maxWidthPerItem: null, itemCount: null,
             reason: "SVG đồ thị — bố cục 2 cột side-by-side (đồ thị + hàng đợi/ngăn xếp)" };
  }
  if (FIXED_SIZE_TARGETS.has(simulationId)) {
    return { simulationId, cls: "fixed_semantic_size", semanticMaxWidth: null,
             maxWidthPerItem: null, itemCount: null,
             reason: "phóng to không tăng giá trị nhận thức — xét khoảng trống sân khấu, không xét bề rộng hình" };
  }
  // Chưa phân lớp: mặc định adaptive để guard còn nói được điều gì đó, và ghi
  // rõ là chưa khai — im lặng xếp nhầm lớp còn tệ hơn.
  return { simulationId, cls: "adaptive_layout", semanticMaxWidth: null,
           maxWidthPerItem: null, itemCount: null,
           reason: "CHƯA KHAI LỚP — mặc định adaptive, cần phân loại từ phép đo" };
}

/** Hợp đồng của mô phỏng ĐANG MỞ — runner đo gọi qua đây. */
export function currentRendererFit(): RendererFit | null {
  const s = useAppStore.getState();
  if (!s.active) return null;
  return rendererFitOf(s.active.moduleId, s.active.state, s.visualMode);
}
