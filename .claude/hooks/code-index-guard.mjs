/**
 * code-index-guard.mjs — CHẶN TRƯỚC MỌI SỬA ĐỔI Ở `frontend/src`.
 *
 * ─── VÌ SAO CÓ FILE NÀY ────────────────────────────────────────────────────
 *
 * `CLAUDE.md §1` và `docs/RULES.md §2` đã bắt đọc `docs/CODE_INDEX.md` TRƯỚC khi
 * sửa. Hook `SessionStart` cũng đã in thứ tự đọc ấy ra mỗi phiên. Cả hai đều là
 * LỜI NHẮC — agent đọc lướt rồi vẫn sửa thẳng, và đã trả giá thật:
 *
 *   `flex: 0 0 auto` cấm SVG co    → đẻ tràn ngang
 *   `flex-wrap: wrap` chữa tràn    → đẻ chú giải dựng cột
 *   gỡ chú giải dựng cột           → `.dag-legend` mất sạch CSS (class-coverage ĐỎ)
 *
 * Ba lần liên tiếp trong một phiên, cùng một nguyên nhân: sửa một chủ sở hữu
 * dùng chung mà KHÔNG biết nó còn chở gì. Lời nhắc không chữa được lớp lỗi này
 * vì nó không nổ ĐÚNG LÚC tay đặt lên file.
 *
 * Hook này nổ đúng lúc đó. Nó KHÔNG chặn (không trả `permissionDecision`) — nó
 * bơm vào ngữ cảnh hai thứ agent lẽ ra phải tự tra:
 *
 *   1. `CODE_INDEX.md` NÓI GÌ về chính file sắp sửa (chủ sở hữu, đang chở gì);
 *      im lặng ⇒ cảnh báo, vì `code-index-sync.test.ts` sẽ ĐỎ.
 *   2. BÁN KÍNH ẢNH HƯỞNG của từng lớp CSS trong bản vá — bao nhiêu module đang
 *      dùng nó. `.stage-legend` có nhiều module dùng; `.dag-legend` chỉ dag. Con
 *      số đó là khác biệt giữa một bản vá và một hồi quy.
 *
 * ─── HỢP ĐỒNG ──────────────────────────────────────────────────────────────
 *
 * stdin  : JSON `PreToolUse` (`{tool_name, tool_input:{file_path, …}}`)
 * stdout : JSON `{hookSpecificOutput:{hookEventName, additionalContext}}`
 * exit   : LUÔN 0. Một guard làm hỏng được luồng sửa code là guard sẽ bị tắt.
 *
 * Chỉ soi `frontend/src/**` (`.ts` · `.tsx` · `.css`). File khác ⇒ im lặng.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

/* `.claude/hooks/` → gốc kho. Bám vào vị trí script chứ KHÔNG bám `cwd`: hook
   có thể chạy từ thư mục con và khi ấy mọi đường dẫn tương đối đều trượt. */
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SRC = join(ROOT, "frontend", "src");
const INDEX = join(ROOT, "docs", "CODE_INDEX.md");

/** Mọi file nguồn dưới `frontend/src`, đọc một lượt (≈224 file, ≈3 MB). */
function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name.startsWith(".")) continue;
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (/\.(ts|tsx|css)$/.test(name)) out.push(p);
  }
  return out;
}

/** Thoát escape regex cho token lớp CSS (chỉ chữ/số/gạch nối nên rất hẹp). */
const esc = (t) => t.replace(/[^\w]/g, (c) => `\\${c}`);

/* ⚠ KHÔNG dùng `process.exit()` trong file này. Trên Windows `process.stdout`
   nối vào PIPE là kênh BẤT ĐỒNG BỘ; `exit()` ngay sau `write()` vứt luôn phần
   chưa kịp đẩy, và hook "chạy xong, im lặng" — đúng kiểu hỏng khó thấy nhất
   (đã mắc đúng lần chạy thử đầu tiên). Thân guard nằm gọn trong `main()` trả về
   chuỗi, ghi một lần ở cuối, rồi để tiến trình tự kết thúc. */
function main() {
  const raw = readFileSync(0, "utf8");
  let input;
  try { input = JSON.parse(raw); } catch { return null; }

  const toolInput = input?.tool_input ?? {};
  const filePath = toolInput.file_path;
  if (typeof filePath !== "string" || !filePath) return null;

  const rel = relative(ROOT, resolve(filePath)).split("\\").join("/");
  if (!rel.startsWith("frontend/src/")) return null;
  if (!/\.(ts|tsx|css)$/.test(rel)) return null;

  const base = rel.slice(rel.lastIndexOf("/") + 1);

  /* ── 1. CODE_INDEX.md nói gì về CHÍNH file này ─────────────────────────── */

  let indexLines = [];
  let indexReadable = true;
  try {
    /* Khớp cả đường dẫn lẫn tên file trần — `code-index-sync.test.ts` chấp nhận
       cả hai dạng, nên guard phải soi cùng một luật, không thì nó báo "chưa ghi"
       cho một entry vốn hợp lệ. */
    indexLines = readFileSync(INDEX, "utf8")
      .split(/\r?\n/)
      .filter((l) => l.includes(rel) || l.includes(base))
      .map((l) => l.trim())
      .filter(Boolean)
      .slice(0, 8);
  } catch { indexReadable = false; }

  /* ── 2. Bán kính ảnh hưởng của các lớp CSS trong bản vá ────────────────── */

  /* Payload = toàn bộ `tool_input`: phủ được `old_string`/`new_string` của Edit,
     `content` của Write, và cả mảng `edits` nếu công cụ đổi hình dạng sau này. */
  const payload = JSON.stringify(toolInput).slice(0, 60000);

  /* Ứng viên: token có gạch nối (`workspace-card`, `dag-legend`) hoặc token
     đứng sau dấu chấm. Bộ lọc "phải có định nghĩa trong một file .css" ở dưới
     mới là thứ quyết định, nên ở đây cứ bắt rộng — nhận bừa một từ tiếng Anh
     cũng bị loại ngay sau đó. */
  const candidates = new Set();
  for (const m of payload.matchAll(/\.?([a-zA-Z][a-zA-Z0-9]*(?:-[a-zA-Z0-9]+)+)/g)) candidates.add(m[1]);
  for (const m of payload.matchAll(/\.([a-zA-Z][a-zA-Z0-9_]*)[\s,{:>.]/g)) candidates.add(m[1]);

  let rows = [];
  let scanned = 0;
  if (candidates.size) {
    const files = walk(SRC).map((p) => ({
      rel: relative(ROOT, p).split("\\").join("/"),
      text: readFileSync(p, "utf8"),
    }));
    scanned = files.length;

    for (const token of candidates) {
      /* Chỉ giữ token THẬT SỰ là một lớp CSS có định nghĩa — bộ lọc này là thứ
         giữ báo cáo còn đọc được thay vì phun ra mọi chuỗi kebab trong bản vá. */
      const defRe = new RegExp(`\\.${esc(token)}(?![\\w-])`);
      const defs = files.filter((f) => f.rel.endsWith(".css") && defRe.test(f.text));
      if (!defs.length) continue;

      const useRe = new RegExp(`(?<![\\w-])${esc(token)}(?![\\w-])`);
      const users = files.filter((f) => !f.rel.endsWith(".css") && useRe.test(f.text));
      rows.push({ token, defs: defs.length, users });
    }
    /* Sắp theo độ dùng chung giảm dần: thứ nguy hiểm nhất phải nằm dòng đầu. */
    rows.sort((a, b) => b.users.length - a.users.length);
    rows = rows.slice(0, 12);
  }

  /* ── 3. Báo cáo ────────────────────────────────────────────────────────── */

  const L = [`── CODE_INDEX GUARD · ${rel} ──`];

  if (!indexReadable) {
    L.push("⚠ Không đọc được docs/CODE_INDEX.md — tra tay trước khi sửa.");
  } else if (indexLines.length) {
    L.push("CODE_INDEX.md nói gì về file này:");
    for (const l of indexLines) L.push(`  ${l}`);
  } else {
    L.push("⚠ CODE_INDEX.md KHÔNG nhắc file này.");
    L.push("  File mới ⇒ phải thêm entry MÔ TẢ NÓ SỞ HỮU GÌ, không thì code-index-sync.test.ts ĐỎ.");
    L.push("  File cũ  ⇒ đang là nợ trong KNOWN_GAPS; đừng sửa mù, tra chủ sở hữu thật trước.");
  }

  const shared = rows.filter((r) => r.users.length > 1);
  if (rows.length) {
    L.push(`Bán kính ảnh hưởng (quét ${scanned} file dưới frontend/src):`);
    for (const r of rows) {
      const names = r.users.map((u) => u.rel.slice(u.rel.lastIndexOf("/") + 1));
      const shown = names.slice(0, 4).join(", ") + (names.length > 4 ? `, +${names.length - 4}` : "");
      const flag = r.users.length > 1 ? "  ⚠ DÙNG CHUNG" : "";
      L.push(`  .${r.token} → ${r.users.length} module dùng${names.length ? ` (${shown})` : ""} · ${r.defs} file CSS định nghĩa${flag}`);
    }
  }

  if (shared.length) {
    L.push(`⚠ ${shared.length} lớp DÙNG CHUNG bởi nhiều module: nêu rõ bán kính ảnh hưởng TRƯỚC khi sửa,`);
    L.push("  và sau khi sửa phải chụp 4 mức (capture-phase-evidence.mjs) + chạy audit-composition.mjs.");
  }

  L.push("Nhắc: audit-composition CHỈ soi .workspace-card và CHỈ chạy khi chưa đăng nhập — lỗi ở shell (sidebar, panel Giải thích, tràn trang) nằm NGOÀI tầm nó.");

  return L.join("\n");
}

let context = null;
try { context = main(); } catch (e) {
  /* Guard hỏng thì nói ra, KHÔNG im lặng và KHÔNG chặn: im lặng là lại rơi về
     đúng trạng thái "không có guard" mà lần này còn tưởng là có. */
  context = `── CODE_INDEX GUARD LỖI ── ${String(e?.message ?? e)}\nTra docs/CODE_INDEX.md bằng tay trước khi sửa.`;
}

if (context) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: { hookEventName: "PreToolUse", additionalContext: context },
  }));
}
