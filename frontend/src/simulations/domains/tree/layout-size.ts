import type { TreeTraversalConfig } from "./tree-module";

/**
 * layout-size.ts — KÍCH THƯỚC KHUNG VẼ CÂY, TÁCH RA LÀM MODULE LÁ.
 *
 * ─── VÌ SAO PHẢI TÁCH ──────────────────────────────────────────────────────
 *
 * `renderer-fit.ts` cần biết TRẦN bề rộng của cây để `SimulationWorkspace` nâng
 * sàn `--stage-min` — nếu không, thẻ mãi kẹt ở 560px và cây không bao giờ có chỗ
 * giãn (đo được: thẻ `tree.traversal` = 560px trong khi `algorithm.find_max` =
 * 1443px, tức "mỗi target một bề rộng" đúng như người dùng thấy).
 *
 * Nhưng `renderer-fit` KHÔNG được `import` thẳng `tree-module`: renderer miền
 * nạp LƯỜI qua `<Suspense>` (`ARCHITECTURE_MAP` — Stage = `rendererFor()` trong
 * Suspense), mà `renderer-fit` lại được `SimulationWorkspace` import THẲNG. Kéo
 * cả renderer vào đó là kéo luôn nó vào bundle shell, phá code-splitting.
 *
 * Module này chỉ có HÌNH HỌC THUẦN, không import registry/React/store, nên nạp
 * sớm không tốn gì. Cả renderer lẫn `renderer-fit` cùng đọc MỘT nguồn — trần mà
 * cổng chấm dùng luôn đúng bằng trần renderer thật sự vẽ, không phải một con số
 * chép tay ở nơi thứ hai rồi trôi.
 */

/** Bề rộng một làn nút (đủ cho nhãn ~12 ký tự tiếng Việt). */
export const TREE_SLOT_W = 86;
/** Khoảng cách giữa hai tầng. */
export const TREE_LEVEL_H = 78;

/**
 * Khung vẽ CO GIÃN theo cây thật (M17-VR1 hồi quy): khung cố định 460×300 chỉ
 * đủ cho nhãn 1–2 ký tự (A, B, C). Đề đời thực dùng tên tiếng Việt dài ("Trăng
 * Khuyết", "Sương Mai") → nhãn tràn khỏi nút và chồng lên nhau. Nay bề rộng cấp
 * theo SỐ NÚT (mỗi nút một làn đủ rộng) và chiều cao theo ĐỘ SÂU.
 *
 * Giá trị trả về CHÍNH LÀ trần ngữ nghĩa: renderer vẽ `maxWidth: w`, nên cây
 * giãn tới đây rồi DỪNG chứ không phình theo khung.
 */
export function treeLayoutSize(config: TreeTraversalConfig): { w: number; h: number } {
  const map = new Map(config.nodes.map((n) => [n.id, n]));
  let maxDepth = 0;
  const walk = (id: string, d: number) => {
    maxDepth = Math.max(maxDepth, d);
    const n = map.get(id);
    if (!n) return;
    if (n.left) walk(n.left, d + 1);
    if (n.right) walk(n.right, d + 1);
  };
  walk(config.rootId, 0);
  return {
    w: Math.max(360, config.nodes.length * TREE_SLOT_W),
    h: Math.max(190, (maxDepth + 1) * TREE_LEVEL_H + 40),
  };
}
