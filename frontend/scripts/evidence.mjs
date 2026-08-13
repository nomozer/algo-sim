/**
 * evidence.mjs — XUẤT XỨ CỦA MỌI BẰNG CHỨNG SINH RA.
 *
 * ─── VẤN ĐỀ NÓ GIẢI ───────────────────────────────────────────────────────
 *
 * Trước file này, mọi artifact chỉ có `when` (một dấu thời gian). Một artifact
 * như thế KHÔNG chứng minh được điều người đọc tưởng nó chứng minh: nó có thể
 * được sinh ra từ một commit khác hẳn commit đang xét, và vẫn trông "mới".
 * Bằng chứng phải THUỘC VỀ một commit, nếu không nó chỉ là một tập số.
 *
 * Nên mọi artifact từ nay mang `head` (git SHA lúc sinh) + `dirty` (cây làm
 * việc có thay đổi chưa commit không) + phiên bản công cụ + môi trường đo.
 *
 * `assertFresh()` là cổng: script nghiệm thu nào đọc lại artifact cũ phải gọi
 * nó, và artifact sinh từ commit khác bị xếp **STALE_EVIDENCE** — không được
 * dùng để chống lưng cho trạng thái DONE.
 *
 * `dirty: true` cũng là một cảnh báo thật: số đo lấy từ mã CHƯA commit thì
 * commit đó không tái lập được nó.
 */
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";

/** SHA của HEAD hiện tại. Ném lỗi nếu không phải kho git — im lặng ở đây sẽ
 *  đẻ ra artifact không có xuất xứ, đúng thứ file này sinh ra để chặn. */
export function gitHead() {
  return execSync("git rev-parse HEAD", { encoding: "utf-8" }).trim();
}

/** Cây làm việc có thay đổi chưa commit không. */
export function gitDirty() {
  return execSync("git status --porcelain", { encoding: "utf-8" }).trim().length > 0;
}

/**
 * Khối xuất xứ gắn vào MỌI artifact.
 * @param {string} tool  tên script sinh ra artifact
 * @param {object} env   thông tin môi trường đo (bề rộng, số target…)
 */
export function provenance(tool, env = {}) {
  return {
    head: gitHead(),
    dirty: gitDirty(),
    generatedAt: new Date().toISOString(),
    tool,
    toolVersion: "1",
    environment: { node: process.version, platform: process.platform, ...env },
  };
}

/**
 * Đọc lại một artifact và KHẲNG ĐỊNH nó thuộc về HEAD hiện tại.
 * Trả về `{ ok, reason, data }` — người gọi quyết định thoát hay báo cáo.
 */
export function assertFresh(path) {
  let data;
  try {
    data = JSON.parse(readFileSync(path, "utf-8"));
  } catch (err) {
    return { ok: false, reason: `không đọc được: ${String(err)}`, data: null };
  }
  if (!data.head) {
    return { ok: false, reason: "STALE_EVIDENCE: artifact không mang dấu HEAD", data };
  }
  const head = gitHead();
  if (data.head !== head) {
    return {
      ok: false,
      data,
      reason: `STALE_EVIDENCE: sinh từ ${data.head.slice(0, 8)}, HEAD nay là ${head.slice(0, 8)}`,
    };
  }
  return { ok: true, reason: null, data };
}
