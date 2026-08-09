import { readdirSync, readFileSync, statSync } from "node:fs";
import { basename, join, relative, sep } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * SYNC-LOCK CHO `docs/CODE_INDEX.md` — file mới mà không được ghi vào index thì
 * suite ĐỎ.
 *
 * VÌ SAO CẦN. `CODE_INDEX.md` là tuyến chống-viết-trùng: agent tra "cái này đã
 * có chưa" trước khi viết. Luật cập nhật nó đã nằm trong `CLAUDE.md` từ lâu —
 * và vẫn bị bỏ bốn wave liền (W4B-2A → W4B-2C). Kết quả đo được: cả tầng tương
 * tác (`scanInteractionOf`, `ScanActionZone`, `labOpen`, `experimentGated`) tra
 * ra 0 kết quả. Một index cũ KHÔNG phải "thiếu" — nó trả lời **"không có"** một
 * cách tự tin, tức tệ hơn không có index.
 *
 * Bài học của chính kho này: nhắc thì trôi, **đỏ thì không**. Cùng khuôn với
 * `generate_dsl_contract.py` / `generate_capability_descriptors.py` — nơi
 * sync-lock đã giữ được hợp đồng suốt nhiều milestone.
 *
 * ─── VÌ SAO LÀ RATCHET, KHÔNG PHẢI DỌN SẠCH MỘT LẦN ───────────────────────
 *
 * Lúc dựng guard này có **18 file + 5 script** chưa được nhắc. Viết vội 23 mô tả
 * cho đủ chỉ tạo ra văn bản rỗng — mà một index đầy chữ vô nghĩa còn khó dùng
 * hơn một index thiếu. Nên guard KHOÁ NGUYÊN TRẠNG rồi chặn nợ MỚI:
 *
 *   - file mới không được nhắc  → ĐỎ (đây là việc chính);
 *   - file trong `KNOWN_GAPS` nay ĐÃ được nhắc → cũng ĐỎ, bắt xoá khỏi danh
 *     sách. Nhờ vế thứ hai, nợ chỉ đi xuống; `KNOWN_GAPS` không thể biến thành
 *     bãi rác.
 *
 * Muốn trả nợ thì viết entry thật vào `CODE_INDEX.md` rồi xoá dòng tương ứng ở
 * đây. Không có đường tắt nào khác.
 *
 * ─── PHÉP KHỚP ─────────────────────────────────────────────────────────────
 * Khớp theo đường dẫn tương đối HOẶC tên file. Bản đầu chỉ khớp đường dẫn đầy
 * đủ và báo 44 lỗi — trong đó phần lớn là dương tính giả, vì index CỐ Ý gom
 * nhiều file vào một tiêu đề (`SimulationWorkspace.tsx` · `SimulationControls.tsx`).
 * Một guard kêu oan là một guard sẽ bị tắt.
 */

const SRC = new URL(".", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const FRONTEND = join(SRC, "..");
const INDEX = join(FRONTEND, "..", "docs", "CODE_INDEX.md");

/**
 * NỢ ĐÃ BIẾT tại lúc dựng guard (W4B-2D). Danh sách này chỉ được PHÉP ngắn đi.
 * Thêm dòng vào đây = thừa nhận vừa tạo nợ mới, và diff sẽ phơi ra điều đó.
 */
const KNOWN_GAPS = [
  "components/AIHelpPanel.tsx",
  "components/AnalysisCard.tsx",
  "components/ArrayView.tsx",
  "components/PredictionBar.tsx",
  "components/PseudocodeView.tsx",
  "components/SimulationInspector.tsx",
  "components/StageLegend.tsx",
  "components/TraversalFrontier.tsx",
  "components/VarsView.tsx",
  "data/samples.ts",
  "data/sim-samples.ts",
  "llm/input.ts",
  "simulations/domains/database/table-module.tsx",
  "simulations/domains/logic/dag-module.tsx",
  "simulations/domains/network/edge-view.ts",
  "simulations/domains/network/traverse-module.tsx",
  "simulations/domains/tree/tree-module.tsx",
  "simulations/renderer-fit.ts",
  "capture-tree-visual.mjs",
  "capture-w2b-patch.mjs",
  "capture-w2c-program.mjs",
  "capture-w3-encoding.mjs",
  "capture-w3-live-e2e.mjs",
];

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}

/** Mã sản phẩm cần được index: nguồn `src/` (bỏ test) + runner ở `scripts/`. */
function subjects(): string[] {
  const src = walk(SRC)
    .filter((f) => /\.tsx?$/.test(f) && !/\.test\.tsx?$/.test(f))
    .map((f) => relative(SRC, f).split(sep).join("/"));
  const scripts = readdirSync(join(FRONTEND, "scripts"))
    .filter((f) => f.endsWith(".mjs"));
  return [...src, ...scripts].sort();
}

const indexText = readFileSync(INDEX, "utf-8");
const mentioned = (id: string) =>
  indexText.includes(id) || indexText.includes(basename(id));

describe("sync-lock · docs/CODE_INDEX.md không được trôi khỏi mã", () => {
  it("mọi file sản phẩm đều được CODE_INDEX nhắc tới (trừ nợ đã khai)", () => {
    const gaps = new Set(KNOWN_GAPS);
    const offenders = subjects().filter((id) => !gaps.has(id) && !mentioned(id));
    expect(
      offenders,
      "File dưới đây chưa có trong docs/CODE_INDEX.md.\n" +
        "Thêm một entry MÔ TẢ NÓ SỞ HỮU GÌ (đừng chỉ liệt kê tên) — lần sau agent\n" +
        "tra ra là khỏi viết bản thứ hai:\n" +
        offenders.map((f) => `  - ${f}`).join("\n"),
    ).toEqual([]);
  });

  it("nợ chỉ được đi xuống — mục đã trả phải xoá khỏi KNOWN_GAPS", () => {
    const paid = KNOWN_GAPS.filter((id) => mentioned(id));
    expect(
      paid,
      "Các mục sau ĐÃ có trong CODE_INDEX rồi nhưng vẫn nằm trong KNOWN_GAPS.\n" +
        "Xoá chúng khỏi danh sách để guard siết lại — nếu không, danh sách sẽ\n" +
        "phình thành bãi rác và guard mất tác dụng:\n" +
        paid.map((f) => `  - ${f}`).join("\n"),
    ).toEqual([]);
  });

  it("KNOWN_GAPS không chứa mục đã biến mất khỏi kho mã", () => {
    // File bị xoá/đổi tên mà quên dọn danh sách ⇒ nợ giả, che mất nợ thật.
    const all = new Set(subjects());
    const ghosts = KNOWN_GAPS.filter((id) => !all.has(id));
    expect(ghosts, `mục không còn tồn tại:\n${ghosts.join("\n")}`).toEqual([]);
  });
});
