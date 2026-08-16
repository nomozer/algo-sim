import { describe, expect, it } from "vitest";
import { registerAllSimulations } from "./index";
import { getSimulation } from "./registry";
import { offlineCatalog } from "../data/offline-catalog";
import { candidateActions } from "./action-probe";
import { thresholdRange } from "./domains/algorithm/condition-param";
import type { SimAction, SimulationModule } from "./types";

/**
 * W5N (Phase N) — CHỮ TRÊN MÀN HÌNH PHẢI NÓI ĐÚNG THỨ ENGINE ĐANG GIỮ.
 *
 * ─── VÌ SAO LỚP LỖI NÀY ĐÁNG MỘT CỔNG RIÊNG ────────────────────────────────
 *
 * Nó đã ship HAI LẦN trong chính kho này, cùng một nguyên nhân: bề mặt đọc
 * CONFIG GỐC của đề thay vì đọc STATE của engine.
 *
 *   `ddb24f1` — "thanh điều kiện phải soi engine, không soi đề gốc": học sinh
 *   chọn phép so sánh ">" thì engine dùng ">", nhưng ô chọn NHẢY VỀ ">=" của đề
 *   gốc. Màn hình nói một đằng, engine chấm một nẻo — và học sinh bị chấm theo
 *   giá trị KHÔNG nhìn thấy được.
 *
 * Đây không phải lỗi thẩm mỹ. `CORRECTNESS.md` trao cho engine tất định độc
 * quyền phán đúng/sai; nếu bề mặt nói khác engine thì chính độc quyền ấy bị
 * phản chứng ngay chỗ học sinh nhìn vào.
 *
 * ─── ĐIỀU KIỂM ĐƯỢC OFFLINE, VÀ ĐIỀU KHÔNG ────────────────────────────────
 *
 * Kiểm được: sau một thao tác ĐỔI ĐƯỢC state, khe thuyết minh của shell phải
 * ĐỔI THEO. Một bề mặt đóng băng trên đề gốc sẽ trả về đúng chuỗi cũ.
 *
 * KHÔNG kiểm được ở đây: highlight, legend, màu ô — chúng sống trong SVG và cần
 * trình duyệt. Chỗ của chúng là `certify-*.mjs`. Test này cố ý KHÔNG giả vờ phủ
 * chúng; nó khoá đúng phần đọc được bằng hàm thuần.
 */

interface Row {
  simId: string;
  mod: SimulationModule;
  config: unknown;
}

/* DỰNG Ở TẦNG MODULE, KHÔNG Ở `beforeAll` — `it.each(rows)` được thu thập TRƯỚC
   mọi hook, nên rows rỗng lúc ấy sẽ sinh ĐÚNG 0 ca mà cả file vẫn báo XANH. Đã
   mắc đúng lỗi này một lần trong wave W5E; một lượt chạy rỗng màu xanh là điều
   tệ nhất một bộ chọn có thể làm (`TEST_TIERS.md`). */
registerAllSimulations();

const rows: Row[] = (() => {
  const out: Row[] = [];
  const seen = new Set<string>();
  for (const e of offlineCatalog()) {
    if (seen.has(e.simId)) continue;
    const mod = getSimulation(e.simId) as SimulationModule | undefined;
    if (!mod) continue;
    const r = mod.validateConfig((e.envelope as { config: unknown }).config);
    if (!r.ok) continue;
    seen.add(e.simId);
    out.push({ simId: e.simId, mod, config: r.config });
  }
  return out;
})();

/** Thao tác đầu tiên ĐỔI ĐƯỢC state — dùng bộ dò dùng chung, không fixture riêng. */
function firstEffective(mod: SimulationModule, config: unknown, s0: unknown) {
  for (const a of candidateActions(config)) {
    let next: unknown;
    try { next = mod.apply!(s0, a as SimAction); } catch { continue; }
    if (next !== s0 && JSON.stringify(next) !== JSON.stringify(s0)) return { action: a, next };
  }
  return null;
}


describe("W5N · bề mặt soi ENGINE, không soi đề gốc", () => {
  it("phép đo phủ cả danh mục — thiếu target là quét mù", () => {
    expect(rows.length).toBe(24);
  });

  it("phép đo PHÂN BIỆT được: có target đổi được, có target không", () => {
    /* Toàn 0 hoặc toàn 1 đều là dấu hiệu bộ dò hỏng chứ không phải sự thật —
       cùng kỉ luật mồi hai chiều của `experience-audit-w4b4a`. */
    const changeable = rows.filter((r) => firstEffective(r.mod, r.config, r.mod.init(r.config)) !== null);
    expect(changeable.length, "không target nào đổi được ⇒ bộ dò hỏng").toBeGreaterThan(5);
    expect(changeable.length, "MỌI target đều đổi được ⇒ bộ dò nhận bừa").toBeLessThan(rows.length);
  });

  /* ─── VÌ SAO KHÔNG CÓ PHÉP QUÉT "MỘT BẤT BIẾN CHO CẢ 24" Ở ĐÂY ──────────
   *
   * Đã thử HAI lần trong chính wave này, cả hai đều bắt nhầm:
   *
   *   (1) "thuyết minh phải ĐỔI sau thao tác" — sai, vì thuyết minh mô tả BƯỚC
   *       HIỆN TẠI: đổi "Tin"→"Tina" thì ở bước 0 ký tự thứ nhất vẫn là T, nên
   *       chuỗi trùng nhau một cách HỢP LỆ. Bắt nhầm `character_encoding` và
   *       `relational_table_query`.
   *   (2) "`currentConfig` phải đổi sau thao tác" — sai, vì ở họ thuật toán
   *       thao tác đầu là `whatif_swap` và nó tạo NHÁNH THỬ NGHIỆM. Nhánh là
   *       thí nghiệm bên lề, đề bài chưa bị sửa, nên `currentConfig` đứng yên là
   *       ĐÚNG — nếu không `specDrift` sẽ kêu "đã đổi so với đề bài" oan mỗi lần
   *       học sinh kéo thử. Bắt nhầm cả 7 target thuật toán.
   *
   * Bài học: quan hệ giữa THAO TÁC và CONFIG khác nhau theo miền một cách chính
   * đáng, nên không có một bất biến offline nào phủ hết. Phần còn lại của Phase
   * N — `WRONG_HIGHLIGHT`, `WRONG_LEGEND`, `WRONG_SELECTED_STATE` — vốn sống
   * trong SVG và CHỈ đo được bằng `certify-*.mjs` trên Chrome thật. Test này cố
   * ý chỉ khoá phần hàm thuần kiểm được, và nói rõ phần nó KHÔNG phủ, thay vì
   * dựng một phép quét rộng rồi phải cấy đầy ngoại lệ cho tới lúc nó hết nghĩa.
   */
});

/* ══ CA ĐÃ TỪNG SHIP — giữ riêng, viết thẳng con số ═══════════════════════ */

describe("W5N · họ có-điều-kiện: ngưỡng trên màn phải là ngưỡng engine đang chấm", () => {
  it.each(["algorithm.sum_if", "algorithm.count_if"])("%s", (simId) => {
    const row = rows.find((r) => r.simId === simId)!;
    const { mod, config } = row;
    const s0 = mod.init(config);

    const cfg = config as { data: { condition: { op: string; value: number }; array: number[] } };
    const oldValue = cfg.data.condition.value;
    /* Miền ngưỡng hợp lệ = khoảng giá trị của CHÍNH dãy (`thresholdRange`), nên
       lấy giá trị mới theo đúng khuôn `explore-ownership-w4b3a` đang dùng —
       chọn bừa `max(array)` thì trúng đúng giá trị cũ ở một số đề mẫu và
       `set_param` bị từ chối, làm test đỏ vì lý do sai. */
    const range = thresholdRange(cfg.data.array)!;
    const newValue = oldValue === range.max ? range.min : range.max;
    expect(newValue, `${simId}: đề mẫu không cho hai ngưỡng phân biệt được`).not.toBe(oldValue);

    const moved = mod.apply!(s0, { type: "set_param", name: "condition.value", value: newValue });
    expect(moved, `${simId}: đổi ngưỡng mà state không đổi`).not.toBe(s0);

    /* ĐIỀU PHẢI ĐÚNG: `state.config` — thứ engine THẬT SỰ chấm — mang ngưỡng
       MỚI. Đây chính là chỗ `ddb24f1` hỏng: ô chọn nhảy về giá trị của đề gốc
       trong khi engine đã dùng giá trị mới. */
    const live = (moved as { config: { data: { condition: { value: number } } } })
      .config.data.condition.value;
    expect(live, `${simId}: engine vẫn giữ ngưỡng của đề gốc`).toBe(newValue);

    /* Và config GỐC của envelope không được bị sửa theo — nó là mốc để
       `specDrift` biết mô hình đã rời khỏi đề chưa. */
    expect(cfg.data.condition.value, `${simId}: thao tác đã ghi đè config gốc`).toBe(oldValue);
  });
});
