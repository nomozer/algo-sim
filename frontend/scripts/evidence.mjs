/**
 * evidence.mjs — XUẤT XỨ CỦA MỌI BẰNG CHỨNG SINH RA.
 *
 * ─── VẤN ĐỀ BAN ĐẦU (W0) ──────────────────────────────────────────────────
 *
 * Trước file này, mọi artifact chỉ có một dấu thời gian. Một artifact như thế
 * KHÔNG chứng minh được điều người đọc tưởng nó chứng minh: nó có thể sinh ra
 * từ một commit khác hẳn commit đang xét mà vẫn trông "mới".
 *
 * ─── LỖI CỦA CHÍNH BẢN VÁ ĐÓ (phát hiện ở W8 closure) ─────────────────────
 *
 * Bản W0 buộc bằng chứng vào `head` rồi đòi `data.head === gitHead()`. Nghe
 * chặt, nhưng nó TỰ MÂU THUẪN với việc commit bằng chứng:
 *
 *     sinh artifact ở HEAD A  →  artifact ghi head = A
 *     commit artifact         →  HEAD thành B
 *     assertFresh()           →  A ≠ B  ⇒  STALE_EVIDENCE
 *
 * Tức một artifact ĐÃ COMMIT không bao giờ tự chứng nhận được, vĩnh viễn. Cổng
 * ấy chỉ xanh trong đúng khoảnh khắc trước khi commit — nên trên thực tế nó
 * không bảo vệ gì cả, và cách duy nhất để nó xanh là sinh lại artifact sau mỗi
 * lần commit rồi... lại làm cây bẩn.
 *
 * ─── MÔ HÌNH NAY: DẤU VÂN TAY MÃ NGUỒN ────────────────────────────────────
 *
 * Câu hỏi đúng không phải "artifact này thuộc commit nào" mà là:
 *
 *     **TRẠNG THÁI MÃ NGUỒN NÀO đã được đo?**
 *
 * Nên bằng chứng buộc vào `sourceFingerprint` — băm của danh sách blob SHA của
 * MÃ SẢN PHẨM (`frontend/src`, `frontend/scripts`, `backend/app`,
 * `backend/tests`), **loại trừ `docs/evaluation/`**. Thêm hay sửa một file bằng
 * chứng KHÔNG đổi dấu vân tay, nên vòng tự tham chiếu biến mất; sửa một dòng mã
 * sản phẩm thì đổi ngay, và artifact cũ lập tức thành `STALE_SOURCE`.
 *
 * `head` vẫn được ghi, nhưng chỉ để người đọc định vị — nó KHÔNG còn là khoá
 * phán quyết.
 */
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

/** Phiên bản HỢP ĐỒNG xuất xứ. Đổi hình dạng khối này thì tăng số. */
export const PROVENANCE_VERSION = 2;

/**
 * Đường dẫn được coi là MÃ NGUỒN SẢN PHẨM.
 *
 * `docs/` cố ý KHÔNG có mặt: bằng chứng và tài liệu nằm trong đó, và nếu chúng
 * tham gia dấu vân tay thì ta quay lại đúng vòng tự tham chiếu vừa gỡ.
 */
export const SOURCE_PATHS = [
  "frontend/src",
  "frontend/scripts",
  "backend/app",
  "backend/tests",
];

/**
 * GỐC KHO — bắt buộc, không dùng cwd của tiến trình.
 *
 * ⚠️ Bản đầu chạy git với cwd mặc định. Script sinh bằng chứng chạy từ
 * `frontend/`, nên `git ls-files -- frontend/src` khớp KHÔNG file nào và dấu vân
 * tay ra sha256 của chuỗi rỗng — giống hệt nhau ở MỌI trạng thái nguồn, tức
 * `STALE_SOURCE` không bao giờ kích hoạt được. Một cổng luôn xanh.
 */
const REPO_ROOT = new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");

const git = (...a) =>
  execFileSync("git", a, { encoding: "utf-8", cwd: REPO_ROOT, stdio: ["ignore", "pipe", "ignore"] });

export function gitHead() {
  return git("rev-parse", "HEAD").trim();
}

/**
 * Dấu vân tay của MÃ NGUỒN ở trạng thái ĐÃ ĐƯA VÀO INDEX.
 *
 * `git ls-files -s` cho `<mode> <blob-sha> <stage>\t<path>` của từng file. Sau
 * một lượt commit, index bằng đúng tree của commit ấy — nên dấu vân tay KHÔNG
 * đổi khi commit chỉ thêm file bằng chứng. Đó chính là tính chất phá được vòng
 * tự tham chiếu.
 */
export function sourceFingerprint() {
  const listing = git("ls-files", "-s", "--", ...SOURCE_PATHS);
  /* RỖNG LÀ HỎNG, KHÔNG PHẢI "nguồn trống".
     Đây là chỗ bản đầu sai câm: chạy sai thư mục ⇒ danh sách rỗng ⇒ dấu vân tay
     là sha256("") ⇒ mọi trạng thái nguồn trông giống nhau. Ném lỗi ở đây biến
     một cổng-luôn-xanh thành một lỗi nhìn thấy được. */
  if (!listing.trim()) {
    throw new Error(
      "sourceFingerprint: `git ls-files` không khớp file nào trong " +
      SOURCE_PATHS.join(", ") + " — sai thư mục gốc hoặc sai đường dẫn nguồn.",
    );
  }
  return createHash("sha256").update(listing).digest("hex").slice(0, 16);
}

/**
 * Những file MÃ NGUỒN đang bẩn (sửa chưa đưa vào index).
 *
 * Chỉ soi `SOURCE_PATHS`: sửa một file `docs/` rồi đo thì phép đo vẫn tái lập
 * được, nên gọi nó là bẩn sẽ làm cảnh báo mất giá trị và người ta thôi đọc.
 */
export function dirtyRelevantSources() {
  const out = git("diff", "--name-only", "--", ...SOURCE_PATHS).trim();
  return out ? out.split("\n").filter(Boolean) : [];
}

/**
 * Khối xuất xứ gắn vào MỌI artifact.
 * @param {string} tool  tên script sinh ra artifact
 * @param {object} env   thông tin môi trường đo (bề rộng, số target…)
 */
export function provenance(tool, env = {}) {
  const dirty = dirtyRelevantSources();
  return {
    provenanceVersion: PROVENANCE_VERSION,
    sourceFingerprint: sourceFingerprint(),
    dirtyRelevantSources: dirty,
    /* Giữ lại để người đọc định vị. KHÔNG phải khoá phán quyết — xem docstring. */
    head: gitHead(),
    dirty: dirty.length > 0,
    generatedAt: new Date().toISOString(),
    tool,
    toolVersion: "1",
    environment: { node: process.version, platform: process.platform, ...env },
  };
}

/**
 * Năm trạng thái, và KHÔNG trạng thái nào mặc định thành FRESH.
 *
 *   FRESH               đo trên đúng mã nguồn hiện tại, nguồn sạch
 *   STALE_SOURCE        mã sản phẩm đã đổi kể từ lúc đo
 *   DIRTY_SOURCE        đo trên mã sản phẩm chưa commit ⇒ không tái lập được
 *   INCOMPATIBLE_TOOL   hợp đồng xuất xứ đã đổi hình dạng
 *   UNKNOWN_PROVENANCE  thiếu trường ⇒ không phán được, và KHÔNG được đoán tốt
 */
export function provenanceVerdict(data) {
  if (!data || typeof data !== "object") return { state: "UNKNOWN_PROVENANCE", reason: "artifact rỗng" };
  if (typeof data.provenanceVersion !== "number" || typeof data.sourceFingerprint !== "string") {
    return {
      state: "UNKNOWN_PROVENANCE",
      reason: "thiếu `provenanceVersion`/`sourceFingerprint` — artifact sinh trước hợp đồng v2",
    };
  }
  if (data.provenanceVersion !== PROVENANCE_VERSION) {
    return {
      state: "INCOMPATIBLE_TOOL",
      reason: `xuất xứ v${data.provenanceVersion}, công cụ nay v${PROVENANCE_VERSION}`,
    };
  }
  if (Array.isArray(data.dirtyRelevantSources) && data.dirtyRelevantSources.length) {
    return {
      state: "DIRTY_SOURCE",
      reason: `đo trên mã chưa commit: ${data.dirtyRelevantSources.slice(0, 3).join(", ")}`,
    };
  }
  const now = sourceFingerprint();
  if (data.sourceFingerprint !== now) {
    return {
      state: "STALE_SOURCE",
      reason: `đo trên nguồn ${data.sourceFingerprint}, nguồn nay là ${now}`,
    };
  }
  return { state: "FRESH", reason: null };
}

/**
 * Đọc lại một artifact và phán nó có chứng nhận được mã nguồn HIỆN TẠI không.
 * Trả `{ ok, state, reason, data }` — người gọi quyết định thoát hay báo cáo.
 */
export function assertFresh(path) {
  let data;
  try {
    data = JSON.parse(readFileSync(path, "utf-8"));
  } catch (err) {
    return { ok: false, state: "UNKNOWN_PROVENANCE", reason: `không đọc được: ${String(err)}`, data: null };
  }
  const v = provenanceVerdict(data);
  return { ok: v.state === "FRESH", state: v.state, reason: v.reason, data };
}
