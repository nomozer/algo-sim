/**
 * flake-repeat.mjs — CHẠY LẶP MỘT CỔNG VÀ ĐO ĐỘ CHẬP CHỜN CỦA NÓ.
 *
 * ─── VÌ SAO CẦN MỘT BỘ ĐO RIÊNG CHO CHÍNH BỘ ĐO ───────────────────────────
 *
 * Một cổng cho `17/21` rồi `19/21` rồi `17/21` **không** nói cho ta biết nó
 * hỏng ở đâu. Tổng số là một con số đã mất thông tin: nó gộp "assertion X luôn
 * đỏ" với "assertion bất kỳ thỉnh thoảng đỏ", mà hai bệnh ấy có hai nguyên
 * nhân hoàn toàn khác nhau. Script này giữ lại **từng assertion của từng
 * lượt**, nên phân bố lộ ra thay vì bị trung bình hoá.
 *
 * ⚠️ **HARNESS NÀY KHÔNG CHẠY LẠI MỘT LƯỢT ĐỎ.** Một lượt đỏ được ghi là đỏ;
 * chạy lại tới khi xanh rồi báo "xanh" là cách một cổng chập chờn được cấp
 * giấy thông hành. `RETRY_COUNTS` ở đây đếm một thứ KHÁC hẳn: số lần **cổng tự
 * mở lại trình duyệt** vì phiên Chrome không tải nổi trang
 * (`BrowserSession.TRAN_MO_LAI`). Đó là dựng lại HẠ TẦNG, không phải lặp lại
 * một khẳng định — nhưng nó vẫn được đếm và **báo riêng** (`§8`), vì một lượt
 * cần mở lại hai lần không được lặng lẽ trở thành "đạt ngay lần đầu".
 *
 * ⚠️ **KHÔNG dọn môi trường giữa các lượt** trừ khi `--kill-chrome`. Nếu tiến
 * trình sót của lượt trước là một phần nguyên nhân thì dọn dẹp im lặng sẽ xoá
 * mất đúng bằng chứng ấy. Số tiến trình Chrome trước/sau mỗi lượt được GHI LẠI.
 *
 * Dùng:
 *   node scripts/flake-repeat.mjs --label <tên> --runs 10 \
 *     --cmd "node scripts/certify-x.mjs" [--artifact <đường/dẫn.json>] \
 *     [--kill-chrome] [--out <đường/dẫn.json>]
 */
import { execSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const FE = fileURLToPath(new URL("..", import.meta.url));
const GOC = resolve(FE, "..");

function co(ten, mac = null) {
  const i = process.argv.indexOf(`--${ten}`);
  return i > 0 && process.argv[i + 1] && !process.argv[i + 1].startsWith("--")
    ? process.argv[i + 1] : mac;
}
const CO_CO = (ten) => process.argv.includes(`--${ten}`);

const LABEL = co("label", "khong-ten");
const RUNS = Number(co("runs", "10"));
const CMD = co("cmd");
const ARTIFACT = co("artifact");
const OUT = co("out", join(GOC, "docs", "evaluation", "geometry",
  "final-system-release", `REPEAT_${LABEL}.json`));

if (!CMD) { console.error("thiếu --cmd"); process.exit(2); }

const demChrome = () => {
  try {
    const r = execSync(
      'powershell -NoProfile -Command "(Get-Process chrome -ErrorAction ' +
      'SilentlyContinue | Measure-Object).Count"', { encoding: "utf8" });
    return Number(r.trim()) || 0;
  } catch { return -1; }
};

const dietChrome = () => {
  try {
    execSync('powershell -NoProfile -Command "Get-Process chrome ' +
      '-ErrorAction SilentlyContinue | Stop-Process -Force ' +
      '-ErrorAction SilentlyContinue"', { stdio: "ignore" });
  } catch { /* không có gì để diệt */ }
};

/** Đọc artifact của cổng và quy về `[{t, ok}]` — hai hình dạng đã có trong kho. */
function docAssertion(p) {
  if (!p || !existsSync(p)) return null;
  let j;
  try { j = JSON.parse(readFileSync(p, "utf8")); } catch { return null; }
  if (Array.isArray(j.R)) return j.R.map((x) => ({ t: x.t, ok: !!x.ok }));
  if (Array.isArray(j.rows)) {
    return j.rows.map((x) => ({ t: `${x.case} · ${x.action}`, ok: !!x.pass }));
  }
  if (Array.isArray(j.checks)) return j.checks.map((x) => ({ t: x.ten ?? x.t, ok: !!x.pass }));
  return null;
}

const luot = [];
console.log(`LẶP ${RUNS} lượt · ${LABEL}\n  ${CMD}\n`);

for (let i = 1; i <= RUNS; i++) {
  if (CO_CO("kill-chrome")) dietChrome();
  const truoc = demChrome();
  const t0 = Date.now();
  /* ⚠️ `cwd` và `PYTHONIOENCODING` truyền qua ĐỐI TƯỢNG, không viết vào chuỗi
     lệnh. Bản đầu nhận `"cd ../backend && PYTHONIOENCODING=utf-8 python …"`;
     trên Windows `shell: true` là `cmd.exe`, nơi tiền tố biến môi trường kiểu
     POSIX là cú pháp SAI — lệnh chết sau 20 ms và harness ghi "3/3 đỏ", tức
     báo một cổng XANH thành hỏng. Cùng lớp lỗi wave này đi sửa: nhầm sự cố hạ
     tầng thành kết luận về nội dung. */
  const r = spawnSync(CMD, {
    cwd: resolve(FE, co("cwd", ".")), shell: true, encoding: "utf8",
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  const ms = Date.now() - t0;
  const sau = demChrome();
  const out = `${r.stdout ?? ""}${r.stderr ?? ""}`;
  const as = docAssertion(ARTIFACT ? resolve(FE, ARTIFACT) : null);
  const dat = as ? as.filter((x) => x.ok).length : null;
  const tong = as ? as.length : null;
  // Nhiều cổng in tổng ở dòng cuối; giữ nó làm phép đối chứng với artifact.
  const dongTong = out.trim().split("\n").filter((l) =>
    /ĐẠT|phép kiểm|PASS|\d+\/\d+/.test(l)).slice(-1)[0]?.trim() ?? "";

  /* MỞ LẠI TRÌNH DUYỆT được ĐẾM RIÊNG (`§8`). Một lượt cần mở lại vẫn là một
     lượt đạt — nhưng nó KHÔNG được im lặng trở thành "đạt ngay lần đầu", vì
     khi ấy báo cáo giấu mất đúng thứ đang cần theo dõi. */
  const moLai = (out.match(/mở lại lần \d+\//g) ?? []).length;

  luot.push({
    luot: i, exit: r.status, ms, mo_lai_trinh_duyet: moLai,
    chrome_truoc: truoc, chrome_sau: sau,
    assertions: tong, pass: dat, fail: tong == null ? null : tong - dat,
    dong_tong: dongTong.slice(0, 160),
    do: as ? as.filter((x) => !x.ok).map((x) => x.t) : null,
  });
  const nhan = (dat == null ? `exit=${r.status}` : `${dat}/${tong}`)
    + (moLai ? ` · mở lại ${moLai}` : "");
  console.log(`  lượt ${String(i).padStart(2)} · ${nhan} · ${ms} ms · `
    + `chrome ${truoc}→${sau}` + (dat != null && dat < tong
      ? `\n           đỏ: ${luot[i - 1].do.join(" | ")}` : ""));
}

// ── Tổng hợp. Assertion nào đỏ ở một số lượt mà xanh ở số khác = CHẬP CHỜN ──
const theoAssertion = {};
for (const l of luot) {
  if (!l.do) continue;
  for (const t of l.do) theoAssertion[t] = (theoAssertion[t] ?? 0) + 1;
}
/* "Sạch" đọc từ ARTIFACT khi có (từng assertion), từ MÃ THOÁT khi không. Bản
   đầu chỉ xét `fail === 0`, nên một cổng không ghi artifact — như oracle
   Python — luôn bị ghi là đỏ dù thoát 0. Lại đúng lớp lỗi ấy: bộ đo kết luận
   về cổng trong khi thứ nó đo là chính nó. */
const sachHoanToan = luot.filter(
  (l) => (l.fail === null ? l.exit === 0 : l.fail === 0)).length;
const tom = {
  label: LABEL,
  cmd: CMD,
  EXECUTIONS: RUNS,
  ASSERTIONS_PER_EXECUTION: luot[0]?.assertions ?? null,
  PASS_COUNTS: luot.map((l) => l.pass),
  FAIL_COUNTS: luot.map((l) => l.fail),
  RETRY_COUNTS: luot.map((l) => l.mo_lai_trinh_duyet ?? 0),
  TONG_MO_LAI_TRINH_DUYET: luot.reduce((a, l) => a + (l.mo_lai_trinh_duyet ?? 0), 0),
  LUOT_SACH_HOAN_TOAN: sachHoanToan,
  FLAKE_RATE: RUNS ? Number(((RUNS - sachHoanToan) / RUNS).toFixed(4)) : null,
  assertion_do_bao_nhieu_luot: theoAssertion,
  thoi_gian_ms: { min: Math.min(...luot.map((l) => l.ms)),
                  max: Math.max(...luot.map((l) => l.ms)) },
  luot,
};
mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(tom, null, 1), "utf8");

console.log(`\n  LƯỢT SẠCH ${sachHoanToan}/${RUNS} · FLAKE_RATE ${tom.FLAKE_RATE}`);
if (Object.keys(theoAssertion).length) {
  console.log("  assertion đỏ (số lượt):");
  for (const [t, n] of Object.entries(theoAssertion).sort((a, b) => b[1] - a[1])) {
    console.log(`    ${n}/${RUNS}  ${t}`);
  }
}
console.log(`  ghi: ${OUT.replace(GOC, "").replace(/\\/g, "/")}`);
process.exit(sachHoanToan === RUNS ? 0 : 1);
