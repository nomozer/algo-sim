#!/usr/bin/env node
/**
 * bash-source-write-guard — BUỘC MỌI SỬA MÃ NGUỒN ĐI QUA Edit/Write.
 *
 * VÌ SAO TỒN TẠI (sự cố có thật, 2026-08-17):
 * `code-index-guard.mjs` chỉ khớp `Edit|Write`. Agent xoá ba khối code bằng
 * `sed -i` qua Bash — hook KHÔNG chạy, nên ba file đó được sửa mà không ai tra
 * `CODE_INDEX.md` và không ai in ra bán kính ảnh hưởng. Đúng cái lưới dựng lên
 * để chống ghi đè nhầm thì bị đi vòng qua, và đi vòng qua một cách im lặng.
 *
 * Luật: lệnh Bash nào GHI vào mã nguồn thì bị chặn — không phải để làm khó, mà
 * để đẩy thao tác sang Edit/Write, nơi guard kia chạy được.
 *
 * HAI MỨC, cố ý khác nhau:
 *
 *   deny  — `sed -i`, `>`, `>>`, `tee` vào file nguồn.
 *           Có công cụ thay thế đầy đủ (Edit/Write), nên không có lý do gì để
 *           dùng shell. Chặn thẳng.
 *
 *   ask   — `rm`, `mv`, `cp` chạm file nguồn.
 *           KHÔNG có tool nào xoá/đổi tên file được, nên chặn thẳng là bịt
 *           đường. Hỏi người dùng: quyết định thuộc về họ, và ít nhất nó không
 *           còn xảy ra lặng lẽ.
 *
 * KHÔNG chặn: đọc (`grep`, `cat`, `sed` không có `-i`), `> /dev/null`, ghi vào
 * `docs/`, `/tmp`, scratchpad, hay bất cứ đâu ngoài ba thư mục dưới. Guard này
 * chỉ giữ MÃ SẢN PHẨM.
 */

const PROTECTED = /(?:^|[\s"'=(])(?:\.[\/\\])?(?:frontend[\/\\]src|backend[\/\\]app|backend[\/\\]tests)[\/\\]\S+/;

/** Tách theo toán tử chuỗi lệnh để mỗi mệnh đề được xét riêng. */
const segmentsOf = (cmd) => cmd.split(/\|\||&&|[;|]/);

function verdict(command) {
  for (const raw of segmentsOf(command)) {
    const seg = raw.trim();
    if (!seg) continue;

    // 1. sed ghi tại chỗ
    if (/\bsed\b/.test(seg) && /\s-(?:[a-zA-Z]*i|-in-place)\b/.test(seg) && PROTECTED.test(seg)) {
      return { decision: "deny", why: "`sed -i` ghi thẳng vào mã nguồn" };
    }

    // 2. chuyển hướng ghi/nối — `2>/dev/null` không dính vì đích không phải mã nguồn
    for (const m of seg.matchAll(/(?:^|\s)\d?>>?\s*(['"]?)([^\s'"|;&]+)\1/g)) {
      if (PROTECTED.test(` ${m[2]}`)) {
        return { decision: "deny", why: `chuyển hướng ghi đè "${m[2]}"` };
      }
    }

    // 3. tee
    const tee = seg.match(/\btee\b\s+(?:-a\s+)?(['"]?)([^\s'"|;&]+)\1/);
    if (tee && PROTECTED.test(` ${tee[2]}`)) {
      return { decision: "deny", why: `\`tee\` ghi vào "${tee[2]}"` };
    }

    // 4. xoá / đổi tên / chép đè — hỏi, không chặn (không có tool thay thế)
    const fs = seg.match(/(?:^|\s)(rm|mv|cp)\b/);
    if (fs && PROTECTED.test(seg)) {
      return { decision: "ask", why: `\`${fs[1]}\` chạm file mã nguồn` };
    }
  }
  return null;
}

let stdin = "";
process.stdin.on("data", (c) => (stdin += c));
process.stdin.on("end", () => {
  let command = "";
  try {
    command = JSON.parse(stdin)?.tool_input?.command ?? "";
  } catch {
    process.exit(0); // không đọc được payload thì KHÔNG chặn — guard hỏng không được thành cửa khoá
  }

  const v = command ? verdict(command) : null;
  if (!v) process.exit(0);

  const reason =
    `${v.why}. Guard CODE_INDEX chỉ chạy trên Edit|Write, nên đường này sửa mã ` +
    `mà không ai tra chủ sở hữu và bán kính ảnh hưởng.\n` +
    (v.decision === "deny"
      ? `Dùng Edit (hoặc Write) cho file này. Xoá cả khối thì Edit với old_string là nguyên khối.`
      : `Không có tool thay thế cho thao tác này — xác nhận với người dùng trước.`);

  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: v.decision,
      permissionDecisionReason: reason,
    },
  }));
  process.exit(0);
});
