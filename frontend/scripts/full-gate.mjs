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
  { name: "benchmark chương trình", protects: "phủ đơn vị SGK, phân loại phạm vi, biến hình",
    cmd: [python, ["scripts/curriculum_benchmark_report.py"]], cwd: `${REPO}/backend` },
  { name: "ma trận catalog", protects: "danh mục target ↔ family ↔ khả năng",
    cmd: [python, ["scripts/catalog_runtime_matrix.py"]], cwd: `${REPO}/backend` },
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
