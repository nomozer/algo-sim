import { describe, expect, it } from "vitest";
import { execFileSync } from "node:child_process";
import {
  PROVENANCE_VERSION,
  SOURCE_PATHS,
  provenanceVerdict,
  sourceFingerprint,
} from "../scripts/evidence.mjs";

/**
 * W8 CLOSURE — XUẤT XỨ BẰNG CHỨNG PHẢI CHỨNG NHẬN ĐƯỢC MỘT TRẠNG THÁI NGUỒN.
 *
 * ─── LỖI ĐƯỢC SỬA ─────────────────────────────────────────────────────────
 *
 * Bản W0 buộc bằng chứng vào `head` rồi đòi `data.head === gitHead()`. Nghe
 * chặt nhưng TỰ MÂU THUẪN với việc commit bằng chứng: sinh ở HEAD A, commit
 * xong HEAD thành B, và artifact thành STALE vĩnh viễn. Cổng ấy chỉ xanh trong
 * đúng khoảnh khắc trước khi commit — nên nó không bảo vệ gì.
 *
 * Nay bằng chứng buộc vào DẤU VÂN TAY MÃ NGUỒN, loại trừ `docs/`. Thêm một file
 * bằng chứng KHÔNG đổi dấu vân tay; sửa một dòng mã sản phẩm thì đổi ngay.
 */

const fresh = (over: Record<string, unknown> = {}) => ({
  provenanceVersion: PROVENANCE_VERSION,
  sourceFingerprint: sourceFingerprint(),
  dirtyRelevantSources: [],
  head: "deadbeef",
  ...over,
});

describe("W8 §3 — năm trạng thái, không cái nào mặc định thành FRESH", () => {
  it("E. nguồn sạch + đúng công cụ ⇒ FRESH (kiểm soát dương tính)", () => {
    expect(provenanceVerdict(fresh()).state).toBe("FRESH");
  });

  it("A. nguồn đã đổi sau khi đo ⇒ STALE_SOURCE", () => {
    expect(provenanceVerdict(fresh({ sourceFingerprint: "0000000000000000" })).state)
      .toBe("STALE_SOURCE");
  });

  it("B. đo trên mã sản phẩm chưa commit ⇒ DIRTY_SOURCE", () => {
    const v = provenanceVerdict(fresh({ dirtyRelevantSources: ["frontend/src/x.ts"] }));
    expect(v.state).toBe("DIRTY_SOURCE");
    expect(v.reason).toContain("frontend/src/x.ts");
  });

  it("D. hợp đồng xuất xứ cũ ⇒ INCOMPATIBLE_TOOL", () => {
    expect(provenanceVerdict(fresh({ provenanceVersion: 1 })).state).toBe("INCOMPATIBLE_TOOL");
  });

  it("F. thiếu trường ⇒ UNKNOWN_PROVENANCE, KHÔNG đoán tốt", () => {
    expect(provenanceVerdict({ head: "abc" }).state).toBe("UNKNOWN_PROVENANCE");
    expect(provenanceVerdict(null).state).toBe("UNKNOWN_PROVENANCE");
    /* Artifact W0 cũ (có `head`, không có dấu vân tay) phải rơi vào đây —
       không được im lặng thành FRESH chỉ vì `head` tình cờ trùng. */
    expect(provenanceVerdict({ head: "abc", dirty: false, generatedAt: "x" }).state)
      .toBe("UNKNOWN_PROVENANCE");
  });
});

describe("W8 §2 — vòng TỰ THAM CHIẾU đã bị phá", () => {
  it("C. thêm/sửa file BẰNG CHỨNG không đổi dấu vân tay nguồn", () => {
    /* Đây là tính chất khiến bằng chứng commit được. Nếu `docs/` lọt vào
       `SOURCE_PATHS` thì mỗi lần commit artifact lại làm chính nó STALE. */
    for (const p of SOURCE_PATHS) {
      expect(p.startsWith("docs/"), `${p} không được nằm trong dấu vân tay nguồn`).toBe(false);
    }
    const before = sourceFingerprint();
    /* `git ls-files -s` chỉ đọc INDEX của SOURCE_PATHS — một file docs bẩn hay
       sạch đều không lọt vào. Kiểm bằng cách hỏi git thẳng. */
    const listing = execFileSync("git", ["ls-files", "-s", "--", ...SOURCE_PATHS],
      { encoding: "utf-8", cwd: new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1") });
    expect(listing, "dấu vân tay đang nuốt cả docs/").not.toContain("docs/");
    expect(sourceFingerprint()).toBe(before); // tất định
  });

  it("dấu vân tay TẤT ĐỊNH — gọi hai lần cho cùng kết quả", () => {
    expect(sourceFingerprint()).toBe(sourceFingerprint());
    expect(sourceFingerprint()).toMatch(/^[0-9a-f]{16}$/);
  });

  it("dấu vân tay PHÂN BIỆT ĐƯỢC — không phải băm của chuỗi rỗng", () => {
    /* TEST NÀY TỒN TẠI VÌ MỘT LỖI THẬT.
       Bản đầu chạy `git ls-files` với cwd của tiến trình (`frontend/`), nên
       không khớp file nào và dấu vân tay ra sha256("") = e3b0c442… — GIỐNG HỆT
       NHAU ở mọi trạng thái nguồn, tức `STALE_SOURCE` không bao giờ kích hoạt
       được. Các test khác vẫn xanh vì chúng so hàm với chính nó.
       Một dấu vân tay không phân biệt được thì bằng chứng nào cũng "tươi". */
    const EMPTY_SHA256 = "e3b0c44298fc1c14";
    expect(sourceFingerprint(), "dấu vân tay đang băm một danh sách RỖNG")
      .not.toBe(EMPTY_SHA256);

    const root = new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
    const listing = execFileSync("git", ["ls-files", "-s", "--", ...SOURCE_PATHS],
      { encoding: "utf-8", cwd: root });
    /* Và nó phải bao được lượng mã thật, không phải một nhánh lẻ. */
    expect(listing.split("\n").filter(Boolean).length,
      "dấu vân tay chỉ bao vài file — nhiều mã sản phẩm không được bảo vệ")
      .toBeGreaterThan(100);
    for (const p of SOURCE_PATHS) {
      expect(listing, `dấu vân tay bỏ sót ${p}`).toContain(p);
    }
  });

  it("phán quyết KHÔNG còn đọc `head` làm khoá", () => {
    /* Hai artifact khác `head` nhưng cùng nguồn phải cùng FRESH — đó chính là
       ca mà mô hình cũ phán sai. */
    expect(provenanceVerdict(fresh({ head: "aaaa" })).state).toBe("FRESH");
    expect(provenanceVerdict(fresh({ head: "bbbb" })).state).toBe("FRESH");
  });
});
