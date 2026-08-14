/**
 * impact.mjs — T0 IMPACT GATE: chọn test theo thứ VỪA ĐỔI, và NÓI VÌ SAO.
 *
 * ─── LUẬT KHÔNG ĐƯỢC VI PHẠM ──────────────────────────────────────────────
 *
 * Thay đổi mã sản phẩm KHÔNG BAO GIỜ được chọn 0 test. Không tra ra chủ sở hữu
 * thì trả `IMPACT_MAPPING_MISSING` và LEO THANG lên tầng rộng hơn.
 *
 * Repo này đã bị đúng kiểu "khớp 0 mục nhưng báo thành công" nhiều lần: một
 * phép thay chuỗi không khớp, một hàm tua gọi API không tồn tại, một phép tiêm
 * bắn nhầm dòng. Mỗi lần đều đọc ra màu xanh. Một bộ chọn test im lặng chọn
 * rỗng là cùng một lỗi ấy, đặt ở chỗ nguy hiểm nhất.
 *
 * ─── BA NGUỒN, GHÉP LẠI, IN RA LÝ DO ──────────────────────────────────────
 *
 *   1. SỞ HỮU THEO THƯ MỤC        domains/web/** → miền web
 *   2. SỔ CHỦ SỞ HỮU DÙNG CHUNG   store.ts → nhiều miền
 *   3. LEO THANG BẢO THỦ          không tra ra ⇒ tầng rộng hơn
 *
 * Guard kiến trúc (`code-index-sync`, `tokens`, `ui-hygiene`) KHÔNG import file
 * bị đổi nên đồ thị import không bao giờ chọn được chúng — chúng phải khai theo
 * sở hữu. Đó là lý do bộ chọn này không dùng `vitest --related` một mình.
 *
 * Dùng: node frontend/scripts/impact.mjs [--base <ref>] [--dry] [--json <path>]
 */
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const DRY = args.includes("--dry");
const BASE = argOf("--base", "");
const JSON_OUT = argOf("--json", "");
const REPO = resolve(new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));

const git = (...a) => {
  try { return execFileSync("git", a, { cwd: REPO, encoding: "utf-8", stdio: ["ignore", "pipe", "ignore"] }).trim(); }
  catch { return ""; }
};

/** File đã đổi: so với `--base` nếu có, không thì lấy cây làm việc + staged. */
function changedFiles() {
  /* `--files a,b,c` — tập file GIẢ ĐỊNH, để `test-tiers.test.ts` kiểm được
     chính bộ chọn mà không phải dựng commit thật. Không có nó thì bộ chọn là
     thứ duy nhất trong repo không ai kiểm được. */
  const forced = argOf("--files", "");
  if (forced) return forced.split(",").map((s) => s.trim()).filter(Boolean);
  if (BASE) return git("diff", "--name-only", BASE).split("\n").filter(Boolean);
  const set = new Set([
    ...git("diff", "--name-only").split("\n"),
    ...git("diff", "--name-only", "--cached").split("\n"),
    ...git("ls-files", "--others", "--exclude-standard").split("\n"),
  ].filter(Boolean));
  return [...set];
}

/**
 * MIỀN theo thư mục sản phẩm. Khoá của bảng là mẫu đường dẫn, giá trị là mẫu
 * test — cùng ngôn ngữ mà `vitest run <pattern>` hiểu.
 */
const DOMAIN_OF = [
  [/^frontend\/src\/simulations\/domains\/([a-z_]+)\//, (m) => m[1]],
  [/^backend\/app\/simulation\/(dsl|families)\//, () => "backend-core"],
  [/^backend\/app\/accounts\//, () => "classroom"],
  [/^backend\/app\/persistence\/classroom/, () => "classroom"],
  [/^frontend\/src\/state\/classroom/, () => "classroom"],
  /* `frontend/scripts/**` là HẠ TẦNG ĐO, không phải mã chạy cho học sinh —
     nhưng nó vẫn là mã sản phẩm theo nghĩa `code-index-sync` quản nó, nên nó
     phải có chủ thay vì rơi vào nhánh leo thang mỗi lần sửa một harness. */
  [/^frontend\/scripts\//, () => "harness"],
];

const DOMAIN_TESTS = {
  algorithm: ["src/simulations/domains/algorithm/"],
  binary: ["src/simulations/domains/binary/"],
  logic: ["src/simulations/domains/logic/"],
  network: ["src/simulations/domains/network/"],
  database: ["src/simulations/domains/database/"],
  web: ["src/simulations/domains/web/"],
  generic: ["src/simulations/domains/generic/"],
  tree: ["src/simulations/domains/tree/"],
  "shared-ui": ["src/components/"],
  classroom: ["src/state/"],
  harness: ["src/code-index-sync.test.ts"],
};

/**
 * SỔ CHỦ SỞ HỮU DÙNG CHUNG — nhỏ và tường minh có chủ đích.
 *
 * Mỗi dòng phải nói VÌ SAO bán kính rộng, nếu không nó sẽ bị cắt gọn "cho
 * nhanh" trong một lần dọn dẹp nào đó.
 */
const SHARED_OWNERS = [
  {
    match: /^frontend\/src\/components\/SimulationControls\.tsx$/,
    tests: ["src/components/", "src/simulations/experience-manifest.test.ts"],
    why: "Dải điều khiển là chủ sở hữu DUY NHẤT của lối vào Thử thách/Khám phá và của ba chế độ transport — đổi nó chạm mọi miền có dòng thời gian.",
  },
  {
    match: /^frontend\/src\/simulations\/transport-policy\.ts$/,
    tests: ["src/components/transport-w7.test.tsx", "src/simulations/experience-manifest.test.ts"],
    why: "Chính sách transport quyết định bộ điều khiển của cả 23 target; manifest trải nghiệm đọc lại chính bảng này.",
  },
  {
    match: /^frontend\/src\/state\/store\.ts$/,
    tests: ["src/state/", "src/components/", "src/simulations/experience-manifest.test.ts"],
    why: "Store sở hữu `active`/`challengeOpen`/`exploreOpen` và điều phối mọi dispatch — mọi miền đọc state qua nó.",
  },
  {
    match: /^frontend\/src\/styles\/(global\.css|tokens\.css)$/,
    tests: ["src/styles/", "src/components/", "src/simulations/experience-manifest.test.ts"],
    why: "`var()` trỏ token không tồn tại là lỗi IM LẶNG (trình duyệt vứt cả dòng) — đã trôi 5 milestone; guard token phải chạy cùng mọi thay đổi CSS.",
  },
  {
    match: /^frontend\/src\/simulations\/(types|registry|renderer)\.ts$/,
    tests: ["src/simulations/", "src/components/"],
    why: "Hợp đồng `SimulationModule` và registry là nền của mọi module — đổi nó là đổi luật chung của cả danh mục.",
  },
  {
    match: /^frontend\/src\/data\/(offline-catalog|sim-samples|samples)\.ts$/,
    tests: ["src/simulations/", "src/data/"],
    why: "Danh mục mẫu là đầu vào của parity mẫu↔AI và của mọi phép đo trình duyệt.",
  },
  {
    match: /^backend\/app\/validation\//,
    tests: ["PYTEST"],
    why: "Validator là NGUỒN của hợp đồng hai tầng; frontend chỉ là bản chiếu, nên đổi nó phải chạy cả backend lẫn parity descriptor.",
  },
  {
    match: /^backend\/app\/simulation\/(catalog|scope|scope_gate)\.py$/,
    tests: ["PYTEST"],
    why: "Catalog/cổng phạm vi quyết định target nào tồn tại và đề nào bị từ chối — chạm gần như mọi test backend.",
  },
];

/** File KHÔNG phải mã sản phẩm — được phép chạy gate nhẹ, và phải nói rõ vì sao. */
const NON_PRODUCTION = /^(docs\/|README|\.gitignore|Makefile|CLAUDE\.md|.*\.md$)/;

const changed = changedFiles();
const plan = { domains: new Set(), patterns: new Set(), pytest: false, reasons: [], unknown: [] };
let docsOnly = changed.length > 0;

for (const f of changed) {
  if (NON_PRODUCTION.test(f)) {
    plan.reasons.push({ file: f, why: "TÀI LIỆU — chạy guard chỉ mục, bỏ suite hiện thực", tests: ["src/code-index-sync.test.ts"] });
    plan.patterns.add("src/code-index-sync.test.ts");
    continue;
  }
  docsOnly = false;

  let matched = false;
  for (const owner of SHARED_OWNERS) {
    if (owner.match.test(f)) {
      matched = true;
      plan.reasons.push({ file: f, why: `CHỦ SỞ HỮU DÙNG CHUNG — ${owner.why}`, tests: owner.tests });
      for (const t of owner.tests) { if (t === "PYTEST") plan.pytest = true; else plan.patterns.add(t); }
    }
  }
  for (const [re, pick] of DOMAIN_OF) {
    const m = f.match(re);
    if (!m) continue;
    const d = pick(m);
    if (d === "backend-core" || d === "classroom") plan.pytest = true;
    if (DOMAIN_TESTS[d]) { matched = true; plan.domains.add(d); for (const t of DOMAIN_TESTS[d]) plan.patterns.add(t); plan.reasons.push({ file: f, why: `SỞ HỮU THEO THƯ MỤC — miền ${d}`, tests: DOMAIN_TESTS[d] }); }
    else if (d === "backend-core" || d === "classroom") { matched = true; plan.reasons.push({ file: f, why: `SỞ HỮU THEO THƯ MỤC — miền ${d} (backend)`, tests: ["PYTEST"] }); }
  }
  if (f.startsWith("backend/")) { matched = true; plan.pytest = true; plan.reasons.push({ file: f, why: "Mã backend — chạy pytest", tests: ["PYTEST"] }); }

  if (!matched) plan.unknown.push(f);
}

/* LEO THANG — file sản phẩm không tra ra chủ thì KHÔNG được im lặng bỏ qua. */
let status = "IMPACT_GATE";
if (plan.unknown.length) {
  status = "IMPACT_MAPPING_MISSING";
  plan.patterns.add("src/");
  plan.pytest = true;
  plan.reasons.push({
    files: plan.unknown,
    why: "KHÔNG TRA RA CHỦ SỞ HỮU — leo thang lên gate miền rộng. Thêm file vào " +
         "`SHARED_OWNERS`/`DOMAIN_OF` (và `docs/CODE_INDEX.md`) để lần sau chọn hẹp lại.",
    tests: ["src/", "PYTEST"],
  });
}

/* Tạo file sản phẩm mới ⇒ guard đồng bộ CODE_INDEX phải chạy. */
const tracked = new Set(git("ls-files").split(String.fromCharCode(10)).filter(Boolean));
const newProd = changed.filter((f) => !NON_PRODUCTION.test(f) && !tracked.has(f)
  && (f.startsWith("frontend/src/") || f.startsWith("frontend/scripts/")));
if (newProd.length) {
  plan.patterns.add("src/code-index-sync.test.ts");
  plan.reasons.push({ files: newProd, why: "CODE_INDEX_UPDATE_REQUIRED — file sản phẩm mới phải có entry mô tả nó sở hữu gì", tests: ["src/code-index-sync.test.ts"] });
}

console.log("T0 IMPACT GATE\n");
console.log(`Đã đổi (${changed.length}):`);
for (const f of changed.slice(0, 12)) console.log(`  - ${f}`);
if (changed.length > 12) console.log(`  … và ${changed.length - 12} file nữa`);
console.log("\nLý do chọn:");
for (const r of plan.reasons) {
  const who = r.file ?? (r.files ?? []).join(", ");
  console.log(`  ${who}\n    → ${r.why}\n    → ${r.tests.join(" · ")}`);
}
const patterns = [...plan.patterns];
/* Đếm TỔNG số đơn vị được chọn, không chỉ mẫu vitest. Bản đầu in "Đã chọn: 0
   mẫu vitest + pytest" cho một thay đổi backend — đúng về vitest nhưng đọc ra
   như một lượt chọn rỗng, tức đúng thứ luật không-chọn-rỗng cấm. */
const selectedCount = patterns.length + (plan.pytest ? 1 : 0);
console.log(`\nĐã chọn: ${selectedCount} đơn vị — ${patterns.length} mẫu vitest${plan.pytest ? " + pytest" : ""}`);

if (!changed.length) {
  console.log("\nKhông có thay đổi nào — không chạy gì.");
  process.exit(0);
}
if (!patterns.length && !plan.pytest) {
  console.error("\n✘ IMPACT_MAPPING_MISSING — thay đổi mã sản phẩm mà chọn 0 test.");
  process.exit(3);
}

const record = { status, changed, patterns, pytest: plan.pytest, docsOnly, reasons: plan.reasons };
if (JSON_OUT) { mkdirSync(dirname(resolve(JSON_OUT)), { recursive: true }); writeFileSync(resolve(JSON_OUT), JSON.stringify(record, null, 2), "utf-8"); }
if (DRY) { console.log(`\n(dry) ${status}`); process.exit(0); }

const t0 = Date.now();
let ok = true;
if (patterns.length) {
  const r = spawnSync("npx", ["vitest", "run", ...patterns], { cwd: `${REPO}/frontend`, stdio: "inherit", shell: true });
  ok = ok && r.status === 0;
}
if (plan.pytest) {
  const py = `${REPO}/backend/.venv/Scripts/python.exe`;
  const r = spawnSync(existsSync(py) ? py : "python", ["-m", "pytest", "-q"],
    { cwd: `${REPO}/backend`, stdio: "inherit", shell: false, env: { ...process.env, PYTHONIOENCODING: "utf-8" } });
  ok = ok && r.status === 0;
}
const secs = ((Date.now() - t0) / 1000).toFixed(1);
console.log(`\nKết quả: ${ok ? (status === "IMPACT_MAPPING_MISSING" ? "IMPACT_GATE_PASS (đã leo thang)" : "IMPACT_GATE_PASS") : "IMPACT_GATE_FAIL"}`);
console.log(`Thời gian: ${secs}s`);
console.log("\n⚠️ IMPACT_GATE_PASS chỉ nói về tập vừa chọn. Nó KHÔNG thay được gate\n" +
  "   sản phẩm đầy đủ (T3) — xem docs/TEST_TIERS.md.");
process.exit(ok ? 0 : 1);
