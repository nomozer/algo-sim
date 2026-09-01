/**
 * full-gate.mjs — T3 FULL PRODUCT GATE, chủ sở hữu DUY NHẤT của nhãn
 * `FULL_PRODUCT_GATE_PASS`.
 *
 * ─── LUẬT ─────────────────────────────────────────────────────────────────
 *
 * Danh sách cổng con nằm NGAY ĐÂY và được `test-tiers.test.ts` khoá lại: bỏ
 * một cổng quan trọng (benchmark chương trình, cổng phạm vi, parity mẫu↔AI) mà
 * vẫn phát nhãn đầy đủ là kiểu nói dối tệ nhất trong cả hệ thống test — nó
 * chứng nhận một HEAD chưa được kiểm.
 *
 * Cổng nào đỏ thì KHÔNG có nhãn. Không có "đạt một phần".
 */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

const REPO = resolve(new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const PY = `${REPO}/backend/.venv/Scripts/python.exe`;
const python = existsSync(PY) ? PY : "python";

/** Mỗi cổng con phải nói nó bảo vệ ĐIỀU GÌ — danh sách này là hợp đồng, không phải script. */
const GATES = [
  { name: "pytest (toàn bộ backend)", protects: "engine tất định, validator, cổng phạm vi, lớp học",
    cmd: [python, ["-m", "pytest", "-q"]], cwd: `${REPO}/backend` },
  { name: "vitest (toàn bộ frontend)", protects: "module, renderer, guard kiến trúc, manifest",
    cmd: ["npx", ["vitest", "run"]], cwd: `${REPO}/frontend`, shell: true },
  { name: "typecheck + build production", protects: "cổng kiểu duy nhất của repo",
    cmd: ["npm", ["run", "build"]], cwd: `${REPO}/frontend`, shell: true },
  /* ─── HAI CỔNG CUỐI ĐÃ ĐỔI CHỦ ĐỀ, KHÔNG PHẢI BỊ BỎ ────────────────────
   *
   * Trước `FINAL_DEAD_EVALUATION_CLEANUP` chúng là `curriculum_benchmark_report.py`
   * (phủ đơn vị SGK Tin học) và `catalog_runtime_matrix.py` (danh mục target ↔
   * family). Cả hai đo danh mục 24 target Tin học và đã CHẾT KHI IMPORT từ lúc
   * danh mục ấy bị gỡ — nghĩa là T3 đã hỏng sẵn trước lượt xoá này.
   *
   * Bỏ trống hai chỗ thì `FULL_PRODUCT_GATE_PASS` vẫn phát ra y hệt trong khi
   * nó bảo vệ ít hơn hẳn — đúng kiểu cổng nói giọng to hơn thứ nó kiểm. Nên
   * thay bằng bằng chứng tất định của miền ĐANG LÀ sản phẩm. Cả hai script đã
   * tồn tại, 0 API call, và là thứ mọi wave hình học vẫn chạy tay. */
  { name: "tập demo khoá luận", protects: "chuỗi dựng tất định chạy hết, thiết diện/thể tích ra hình",
    cmd: [python, ["scripts/replay_demo_cases.py"]], cwd: `${REPO}/backend` },
  { name: "bề mặt sập của demo", protects: "sáu biên từ chối ĐÚNG KIỂU, không ném 500",
    cmd: [python, ["scripts/audit_demo_crash_surface.py"]], cwd: `${REPO}/backend` },
];

console.log("T3 FULL PRODUCT GATE\n");
const results = [];
const t0 = Date.now();
for (const g of GATES) {
  const start = Date.now();
  const r = spawnSync(g.cmd[0], g.cmd[1], {
    cwd: g.cwd, stdio: "inherit", shell: Boolean(g.shell),
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  const secs = ((Date.now() - start) / 1000).toFixed(1);
  results.push({ name: g.name, protects: g.protects, ok: r.status === 0, secs });
  console.log(`\n  ${r.status === 0 ? "✔" : "✘"} ${g.name} — ${secs}s`);
}

console.log("\n── TỔNG KẾT ──");
for (const r of results) console.log(`  ${r.ok ? "✔" : "✘"} ${r.name.padEnd(34)} ${r.secs}s   (${r.protects})`);
const ok = results.every((r) => r.ok);
console.log(`\nTổng: ${((Date.now() - t0) / 1000).toFixed(1)}s`);
console.log(ok ? "\nFULL_PRODUCT_GATE_PASS" : "\nFULL_PRODUCT_GATE_FAIL — không cổng con nào được bỏ qua.");
process.exit(ok ? 0 : 1);
