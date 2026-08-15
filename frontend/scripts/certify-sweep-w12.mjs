/**
 * certify-sweep-w12.mjs — MỘT LƯỢT CHỨNG NHẬN, MỘT TRẠNG THÁI NGUỒN.
 *
 * ─── LỖI CÓ THẬT MÀ FILE NÀY SỬA ──────────────────────────────────────────
 *
 * Bảy cổng W12 đều đã gắn `provenance()`, và mỗi cổng riêng lẻ vẫn đúng số lúc
 * đo. Nhưng quy trình thực tế là:
 *
 *     sửa mã/script  →  chạy cổng trên cây bẩn  →  commit mã  →  chạy cổng kế
 *
 * nên bảy artifact ra đời trên BẢY dấu vân tay nguồn khác nhau (đo được ở
 * `5047508`: 2111b53a · 13b17a50 · 37157506 · 75540b23 · 1f4f8011 · c1a50ad4 ·
 * 762e50db). Ghép chúng lại thành một tuyên bố COMPLETE là nói về một sản phẩm
 * chưa từng tồn tại ở bất kì thời điểm nào.
 *
 * Không cổng nào kêu, vì `provenanceVerdict` phán MỘT artifact tại MỘT thời
 * điểm. Thứ chưa ai đo là **lượt chạy**: nguồn ở đầu lượt có bằng nguồn ở cuối
 * lượt không.
 *
 * ─── HỢP ĐỒNG ─────────────────────────────────────────────────────────────
 *
 *   vào lượt   cây nguồn SẠCH  (bẩn ⇒ SOURCE_DIRTY_AT_SWEEP_START)
 *   trong lượt KHÔNG sửa file nào thuộc `SOURCE_PATHS`
 *   ra lượt    HEAD và dấu vân tay y nguyên
 *   kết quả    mọi artifact FRESH và uniqueFingerprints === 1
 *
 * Vi phạm bất kì ⇒ `CERTIFICATION_SWEEP_INVALID`, thoát != 0. Đầu ra của chính
 * lượt này rơi vào `docs/evaluation/` — ngoài dấu vân tay — nên nó không tự vô
 * hiệu hoá mình.
 *
 * ─── VÌ SAO DANH SÁCH CỔNG BỊ KHOÁ BỞI TEST ───────────────────────────────
 *
 * Cùng lí do `full-gate.mjs` bị khoá: bỏ im lặng một cổng con rồi vẫn phát nhãn
 * lượt-hợp-lệ là chứng nhận một HEAD chưa được kiểm. `certification-sweep.test.ts`
 * đối chiếu mảng `GATES` với danh sách artifact W12 hiện hành.
 *
 * ⚠️ CẦN `npm run dev` chạy ở cửa sổ khác + Chrome thật (các cổng con dùng CDP).
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import {
  crossCheckFreshness, provenance, sweepBegin, sweepEnd, sweepVerdict, SWEEP_VALID,
} from "./evidence.mjs";

const FRONTEND = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const REPO = new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const artifact = (name) => resolve(REPO, "docs/evaluation/m20", name);

/**
 * MỌI CỔNG CON CỦA W12, kèm artifact nó sở hữu.
 *
 * `kind` phân biệt hai loại bằng chứng — trộn chúng là một lỗi đã có tên trong
 * `W12_REMAINING.md`: bảng ngữ nghĩa DẪN TỪ HỢP ĐỒNG không chứng minh được điều
 * mà một lượt bấm chuột thật chứng minh, và ngược lại.
 */
export const GATES = [
  { name: "ngữ nghĩa tương tác (dẫn từ hợp đồng)", kind: "DERIVED",
    cmd: ["npx", ["vitest", "run", "src/simulations/interaction-semantics.test.ts"]],
    out: artifact("w12-interaction-semantics.json") },
  { name: "tương tác trình duyệt thật", kind: "BROWSER",
    cmd: ["node", ["scripts/certify-w12.mjs"]], out: artifact("w12-interaction.json") },
  { name: "trải nghiệm (công cụ vs chỉ lộ dần)", kind: "BROWSER",
    cmd: ["node", ["scripts/certify-experience-w12.mjs"]], out: artifact("w12-experience-audit.json") },
  { name: "sức nặng thị giác", kind: "BROWSER",
    cmd: ["node", ["scripts/certify-visual-weight-w12.mjs"]], out: artifact("w12-visual-weight.json") },
  { name: "tiêm lỗi sức nặng thị giác", kind: "BROWSER",
    cmd: ["node", ["scripts/faultcheck-visual-weight-w12.mjs"]], out: artifact("w12-visual-weight-faults.json") },
  { name: "ma trận bề rộng", kind: "BROWSER",
    cmd: ["node", ["scripts/certify-viewports-w12.mjs"]], out: artifact("w12-viewport-matrix.json") },
  { name: "quyền sở hữu cuộn của vỏ", kind: "BROWSER",
    cmd: ["node", ["scripts/certify-scroll-w12.mjs"]], out: artifact("w12-scroll-shell.json") },
  { name: "mùi quiz", kind: "BROWSER",
    cmd: ["node", ["scripts/quiz-dominance-w12.mjs"]], out: artifact("w12-quiz-dominance.json") },
];

/* Chạy trực tiếp thì thi hành; `import` thì chỉ lấy `GATES` cho test. */
const invokedDirectly = process.argv[1]
  && resolve(process.argv[1]) === resolve(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
if (invokedDirectly) await main();

async function main() {
  const OUT = artifact("w12-sweep.json");
  mkdirSync(dirname(OUT), { recursive: true });

  const begin = sweepBegin("certify-sweep-w12");
  console.log("━━ LƯỢT CHỨNG NHẬN W12");
  console.log(`  HEAD_BEFORE        ${begin.headBefore}`);
  console.log(`  FINGERPRINT_BEFORE ${begin.sourceFingerprintBefore}`);
  console.log(`  DIRTY_BEFORE       ${begin.dirtyBefore.length ? begin.dirtyBefore.join(", ") : "—"}\n`);

  /* DỪNG SỚM khi vào lượt đã bẩn. Chạy tiếp chỉ sinh ra bằng chứng phải vứt. */
  if (begin.dirtyBefore.length) {
    const rec = sweepEnd(begin);
    const v = sweepVerdict(rec);
    writeFileSync(OUT, JSON.stringify({
      ...provenance("certify-sweep-w12", { gates: 0 }), ...rec, verdict: v, gates: [], crossCheck: null,
    }, null, 2), "utf-8");
    console.error(`  ${v.state}\n  ${v.faults.join("\n  ")}`);
    process.exit(1);
  }

  const results = [];
  for (const g of GATES) {
    const t0 = Date.now();
    const r = spawnSync(g.cmd[0], g.cmd[1], { cwd: FRONTEND, stdio: "inherit", shell: true });
    results.push({
      name: g.name, kind: g.kind, out: g.out.replace(REPO, "").replace(/\\/g, "/"),
      ok: r.status === 0, seconds: Number(((Date.now() - t0) / 1000).toFixed(1)),
    });
    console.log(`\n  ${r.status === 0 ? "✔" : "✘"} ${g.name}`);
  }

  const record = sweepEnd(begin);
  const verdict = sweepVerdict(record);
  const crossCheck = crossCheckFreshness(GATES.map((g) => g.out));

  console.log("\n── TỔNG KẾT LƯỢT ──");
  for (const r of results) console.log(`  ${r.ok ? "✔" : "✘"} ${r.name.padEnd(38)} ${r.seconds}s`);
  console.log(`\n  HEAD_AFTER         ${record.headAfter}`);
  console.log(`  FINGERPRINT_AFTER  ${record.sourceFingerprintAfter}`);
  console.log(`  DIRTY_AFTER        ${record.dirtyAfter.length ? record.dirtyAfter.join(", ") : "—"}`);
  console.log(`  ${verdict.state}${verdict.faults.length ? "\n  " + verdict.faults.join("\n  ") : ""}`);
  console.log(`\n  UNIQUE_CERTIFICATION_SOURCE_FINGERPRINT_COUNT = ${crossCheck.uniqueFingerprints}`);
  console.log(`  trạng thái artifact: ${JSON.stringify(crossCheck.counts)}`);
  for (const row of crossCheck.rows.filter((r) => r.state !== "FRESH")) {
    console.log(`  ✘ ${row.state}  ${row.path.replace(REPO, "")}`);
  }

  const gatesOk = results.every((r) => r.ok);
  const ok = gatesOk && verdict.state === SWEEP_VALID && crossCheck.ok;
  /* BẢN GHI LƯỢT CŨNG PHẢI PHÁN ĐƯỢC.
     Lượt đầu tiên chạy file này sinh ra một `w12-sweep.json` mà chính
     `provenanceVerdict` đọc vào ra `UNKNOWN_PROVENANCE`: nó có `headBefore/After`
     và `sourceFingerprintBefore/After` nhưng không có khối phẳng mà cổng đọc.
     Tức artifact CHỨNG MINH kỷ luật xuất xứ lại nằm ngoài chính cổng ấy — đúng
     họ lỗi wave này tồn tại để diệt. `provenance()` đặt TRƯỚC `record` để
     `sourceFingerprint` phẳng không đè mất hai đầu Before/After. */
  writeFileSync(OUT, JSON.stringify({
    ...provenance("certify-sweep-w12", { gates: GATES.length }),
    ...record, verdict, gates: results, crossCheck, ok,
  }, null, 2), "utf-8");
  console.log(`\n→ ${OUT}`);
  if (!ok) process.exit(1);
}
