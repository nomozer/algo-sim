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
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/** `URL.pathname` giữ `%20`: worktree `D:/tmp/w09 repro` từng thành thư mục
 *  không tồn tại, mọi cổng chết ENOENT trong 0,0 s mà không in lý do. */
export const repoRootOf = (moduleUrl) => fileURLToPath(new URL("../..", moduleUrl)).replace(/[\\/]$/, "");

/** Phiên bản của image backend (`backend/Dockerfile`: `python:3.12-slim`). */
const REQUIRED_PYTHON = "3.12";
const PROBE = "import sys, pytest, fastapi; print('%d.%d' % sys.version_info[:2])";

export class PythonEnvError extends Error {
  constructor(code, message, tried = []) {
    super(`${code}: ${message}`);
    this.code = code;
    this.tried = tried;
  }
}

const venvPython = (root) => join(root, "backend", ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python");

function probePython(path, required) {
  if (!existsSync(path)) return { code: "PYTHON_NOT_FOUND", reason: "không tồn tại" };
  const r = spawnSync(path, ["-c", PROBE], { encoding: "utf-8", timeout: 60_000 });
  if (r.error || r.status !== 0) {
    return { code: "PYTHON_INVALID",
      reason: r.error?.code ?? (r.stderr || "").trim().split("\n").at(-1) ?? `exit ${r.status}` };
  }
  const version = r.stdout.trim();
  return version === required ? { version }
    : { code: "PYTHON_VERSION_MISMATCH", reason: `${version} ≠ ${required}` };
}

/** Thứ tự thẩm quyền: `--python`/`ALGO_SIM_PYTHON` → venv đang kích hoạt →
 *  venv của cây này → venv của worktree chính (git common dir). Hết ứng viên ⇒
 *  lỗi có cấu trúc; KHÔNG BAO GIỜ rơi về `python` trên PATH. */
export function resolvePython({ repo, explicit, env = process.env, required = REQUIRED_PYTHON }) {
  const chosen = explicit ?? env.ALGO_SIM_PYTHON;
  if (chosen) {
    const p = probePython(chosen, required);
    if (p.code) throw new PythonEnvError(p.code, `${chosen} — ${p.reason}`, [{ path: chosen, reason: p.reason }]);
    return { path: chosen, version: p.version, source: "explicit" };
  }
  const candidates = [];
  if (env.VIRTUAL_ENV) {
    candidates.push({ path: join(env.VIRTUAL_ENV, process.platform === "win32" ? "Scripts/python.exe" : "bin/python"),
      source: "active_venv" });
  }
  candidates.push({ path: venvPython(repo), source: "repo_venv" });
  const common = spawnSync("git", ["-C", repo, "rev-parse", "--path-format=absolute", "--git-common-dir"],
    { encoding: "utf-8" });
  if (common.status === 0) {
    const mainRoot = dirname(common.stdout.trim());
    if (mainRoot !== repo) candidates.push({ path: venvPython(mainRoot), source: "main_worktree_venv" });
  }
  const tried = [];
  for (const c of candidates) {
    const p = probePython(c.path, required);
    if (!p.code) return { path: c.path, version: p.version, source: c.source };
    tried.push({ path: c.path, source: c.source, reason: `${p.code} ${p.reason}` });
  }
  throw new PythonEnvError("PYTHON_ENV_UNRESOLVED",
    "không ứng viên nào dùng được; truyền --python <đường dẫn> hoặc ALGO_SIM_PYTHON", tried);
}

export function runGate(g) {
  const r = spawnSync(g.cmd[0], g.cmd[1], {
    cwd: g.cwd, stdio: "inherit", shell: Boolean(g.shell),
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  return { ok: r.status === 0, status: r.status, error: r.error?.code ?? null };
}

const IS_MAIN = import.meta.filename === process.argv[1];
const REPO = repoRootOf(import.meta.url);
const argPython = process.argv.includes("--python")
  ? process.argv[process.argv.indexOf("--python") + 1] : undefined;
let python = "python";
if (IS_MAIN) {
  try {
    const resolved = resolvePython({ repo: REPO, explicit: argPython });
    python = resolved.path;
    console.log(`PYTHON ${resolved.source} ${resolved.version} ${resolved.path}`);
  } catch (e) {
    console.error(JSON.stringify({ code: e.code, message: e.message, tried: e.tried }, null, 2));
    console.log("\nFULL_PRODUCT_GATE_FAIL — không xác định được môi trường Python của backend.");
    process.exit(1);
  }
}

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

if (IS_MAIN) {
  console.log("T3 FULL PRODUCT GATE\n");
  const results = [];
  const t0 = Date.now();
  for (const g of GATES) {
    const start = Date.now();
    const r = runGate(g);
    const secs = ((Date.now() - start) / 1000).toFixed(1);
    results.push({ name: g.name, protects: g.protects, ...r, secs });
    console.log(`\n  ${r.ok ? "✔" : "✘"} ${g.name} — ${secs}s`
      + (r.ok ? "" : `  (exit ${r.status}${r.error ? `, ${r.error}` : ""})`));
  }

  console.log("\n── TỔNG KẾT ──");
  for (const r of results) console.log(`  ${r.ok ? "✔" : "✘"} ${r.name.padEnd(34)} ${r.secs}s   (${r.protects})`);
  const ok = results.every((r) => r.ok);
  console.log(`\nTổng: ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  console.log(ok ? "\nFULL_PRODUCT_GATE_PASS" : "\nFULL_PRODUCT_GATE_FAIL — không cổng con nào được bỏ qua.");
  process.exit(ok ? 0 : 1);
}
