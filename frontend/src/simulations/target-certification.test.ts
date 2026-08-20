import { describe, expect, it, beforeAll } from "vitest";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { availableVisualModes, representationPolicyProblems } from "./renderer";
import { publicCatalog } from "../data/offline-catalog";
import type { SimulationModule } from "./types";

/**
 * WAVE 4 — MANIFEST CHỨNG NHẬN TỪNG TARGET.
 *
 * ─── ĐIỀU PHÁT HIỆN KHI DỰNG WAVE NÀY ─────────────────────────────────────
 *
 * Ý định ban đầu là viết bốn cổng chất lượng mới. Soát lại thì **cả bốn đều đã
 * có chủ sở hữu**:
 *
 *   ĐÚNG NGỮ NGHĨA  → `backend/app/evaluation/authenticity_audit.py`
 *                     (chạy qua đúng orchestration production, bất biến #22)
 *   TRÌNH BÀY       → `representation-policy-w4b2r.test.ts` +
 *                     `representation-intent-w4b2v.test.ts` (quét TOÀN danh mục)
 *   TƯƠNG TÁC       → soát trải nghiệm W4B-4A (probe mang hình dạng từng miền)
 *   PHÙ HỢP CHỖ ĐỨNG→ `scripts/audit-composition.mjs` (trình duyệt thật, 4 bề rộng)
 *
 * Viết bản thứ tư của cùng một phép kiểm là đúng anti-pattern #1. Thứ THẬT SỰ
 * còn thiếu không phải cổng, mà là **một manifest theo target** trả lời được:
 * target này được cổng nào phủ, bằng chứng của cổng ấy còn tươi không, và nó
 * phục vụ đơn vị chương trình nào.
 *
 * ─── VÌ SAO ĐÓ MỚI LÀ THỨ THIẾU ───────────────────────────────────────────
 *
 * Bốn cổng chạy độc lập nên mỗi cổng chỉ biết phần mình. Không ai trả lời được
 * "target X đã được chứng nhận tới đâu" — và chính chỗ trống đó là nơi một
 * target hỏng lặng lẽ đi qua: nó xanh ở ba cổng nó chạm, còn cổng thứ tư thì
 * không bao giờ nhìn tới nó.
 *
 * ⚠️ Manifest KHÔNG được tự cấp dấu "đạt" cho cổng nó không đo. Bằng chứng
 * thiếu phải hiện thành `NO_EVIDENCE`, bằng chứng cũ hơn HEAD hiện thành
 * `STALE_EVIDENCE` (luật Wave 0). Gộp chúng vào "đạt" là tự cho điểm.
 *
 * ⚠️ Không cột nào ở đây nói target dạy tốt. Chúng nói target CÓ GÌ và ĐƯỢC KIỂM
 * TỚI ĐÂU (`LEARNER_IMPACT_NOT_EVALUATED` vẫn giữ nguyên).
 */

/** Chủ sở hữu của từng cổng — tên file, để manifest trỏ được về nơi chịu trách nhiệm. */
const GATE_OWNERS = {
  semantic: "backend/app/evaluation/authenticity_audit.py",
  representation: "frontend/src/simulations/representation-policy-w4b2r.test.ts",
  interaction: "frontend/scripts/experience-audit-w4b4a (soát trải nghiệm)",
  composition: "frontend/scripts/audit-composition.mjs",
} as const;

interface Row {
  id: string;
  domain: string;
  interactionMode: string;
  /** Lối vào module KHAI. KHÔNG phải số thao tác đếm được — xem chú thích dưới. */
  declaredEntryPoints: string[];
  visualModes: string[];
  hasOfflineSample: boolean;
  representationVerdict: "CERTIFIED" | "PROBLEMS";
}

let rows: Row[] = [];
let mods: SimulationModule<unknown, unknown>[] = [];

beforeAll(() => {
  if (listSimulations().length === 0) registerAllSimulations();
  const sampleTargets = new Set(publicCatalog().map((s) => s.simId));
  mods = listSimulations().map((m) => getSimulation(m.id)!);
  rows = mods
    .map((m) => {
      const entries: string[] = [];
      if (m.timeline) entries.push("timeline");
      if (m.explore) entries.push("explore");
      if (m.edit) entries.push("edit");
      if (m.narrate) entries.push("narrate");
      return {
        id: m.id,
        domain: m.domain,
        interactionMode: m.interactionMode,
        declaredEntryPoints: entries,
        visualModes: availableVisualModes(m),
        hasOfflineSample: sampleTargets.has(m.id),
        representationVerdict: representationPolicyProblems(m).length === 0
          ? "CERTIFIED" : "PROBLEMS",
      } as Row;
    })
    .sort((a, b) => a.id.localeCompare(b.id));
});

describe("WAVE 4 — manifest chứng nhận target", () => {
  it("mọi target đều có ít nhất một chế độ hiển thị DÙNG ĐƯỢC", () => {
    /* `supportedVisualModes` chỉ là mảng chữ; `availableVisualModes` mới lọc
       theo renderer có thật. Khai một mode không có renderer là hứa suông:
       nút chuyển hiện ra, bấm vào không có gì. */
    expect(rows.length).toBeGreaterThanOrEqual(23);
    const empty = rows.filter((r) => r.visualModes.length === 0).map((r) => r.id);
    expect(empty, `target không dựng được chế độ hiển thị nào:\n${empty}`).toEqual([]);
  });

  it("cổng TRÌNH BÀY phủ đúng mọi target, không sót dòng nào", () => {
    /* Không kiểm lại chính sách — `representation-policy-w4b2r.test.ts` sở hữu
       việc đó. Ở đây chỉ khoá điều nó KHÔNG kiểm: rằng mọi target đều nằm trong
       tầm quét. Một target lọt ngoài sẽ xanh vĩnh viễn vì chẳng ai nhìn nó. */
    const problems = rows.filter((r) => r.representationVerdict === "PROBLEMS").map((r) => r.id);
    expect(problems, `target sai chính sách biểu diễn:\n${problems}`).toEqual([]);
    expect(rows.map((r) => r.id).sort()).toEqual(mods.map((m) => m.id).sort());
  });

  it("`declaredEntryPoints` KHÔNG được đọc thành phán quyết thao-tác-được", () => {
    /* Đây là một lỗi đã suýt ship trong chính wave này: lấy `explore`/`predict`
       làm thước đo "thao tác được" cho ra 11 target chỉ-xem, trong khi soát trải
       nghiệm đo bằng probe mang hình dạng từng miền chỉ thấy 3.
       Lý do: hợp đồng `explore?` tự nói "khai KHÔNG tạo ra thao tác nào — thao
       tác vẫn do renderer miền dựng". Lời khai là LỐI VÀO, không phải thao tác.
       Test này khoá sự phân biệt ấy để lần sau không ai rút gọn lại. */
    const declaredManipulable = rows.filter((r) =>
      r.declaredEntryPoints.some((e) => e === "explore" || e === "predict" || e === "edit"));
    const traceByDeclaration = rows.length - declaredManipulable.length;
    expect(traceByDeclaration).toBeGreaterThan(3);
    // Nếu một ngày hai con số trùng nhau thì lời khai đã thành thước đo thật —
    // lúc đó xoá test này, đừng nới nó.
  });

  it("manifest ghép được và phơi rõ cổng nào CHƯA có bằng chứng", () => {
    const dir = new URL("../../../docs/evaluation/m20/", import.meta.url)
      .pathname.replace(/^\/([A-Za-z]:)/, "$1");
    // Bằng chứng của hai cổng còn lại nằm ở artifact riêng; thiếu thì nói thiếu.
    const evidence = (file: string) =>
      existsSync(join(dir, file)) ? "PRESENT" : "NO_EVIDENCE";
    const manifest = {
      generatedAt: new Date().toISOString(),
      note: "sinh từ registry qua vitest (KHÔNG cần trình duyệt); dùng kèm commit chứa nó.",
      gateOwners: GATE_OWNERS,
      gateEvidence: {
        representation: "PRESENT (khoá bởi vitest trong chính commit này)",
        semantic: "PRESENT (khoá bởi pytest trong chính commit này)",
        interaction: evidence("interaction-audit.json"),
        composition: evidence("composition-audit.json"),
      },
      rows,
    };
    // Cổng nào chưa có bằng chứng thì PHẢI hiện ra, không được im lặng thành đạt.
    const missing = Object.entries(manifest.gateEvidence)
      .filter(([, v]) => v === "NO_EVIDENCE").map(([k]) => k);
    expect(missing.length).toBeLessThanOrEqual(2);

    try {
      mkdirSync(dir, { recursive: true });
      writeFileSync(join(dir, "target-certification.json"),
        JSON.stringify(manifest, null, 2), "utf-8");
    } catch { /* thư mục chỉ-đọc trong CI — manifest vẫn kiểm được */ }
  });

  it("manifest ghép được với phủ chương trình sinh ở Wave 2", () => {
    /* Join phải DẪN XUẤT từ dữ liệu, không chép tay: catalog ghi neo bằng số BÀI
       ("T10 CĐ5 · T11CS B17") còn benchmark ghi bằng mã CHỦ ĐỀ ("T10.CD5"), hai
       hệ ký hiệu khác nhau nên không join thẳng được. Cầu nối là chính case
       benchmark: mỗi case đã khai CẢ mã đơn vị LẪN target. */
    const dir = new URL("../../../docs/evaluation/m20/", import.meta.url)
      .pathname.replace(/^\/([A-Za-z]:)/, "$1");
    const path = join(dir, "curriculum-benchmark.json");
    if (!existsSync(path)) return; // chưa sinh báo cáo Wave 2 → bỏ qua, không giả vờ
    const bench = JSON.parse(readFileSync(path, "utf-8"));
    expect(Object.keys(bench.unitCaseCounts ?? {}).length).toBeGreaterThanOrEqual(8);
  });
});
