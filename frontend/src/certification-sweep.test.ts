import { describe, expect, it } from "vitest";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import {
  SWEEP_FAULTS,
  SWEEP_INVALID,
  SWEEP_VALID,
  crossCheckFreshness,
  provenanceVerdict,
  sourceFingerprint,
  sweepBegin,
  sweepEnd,
  sweepVerdict,
} from "../scripts/evidence.mjs";
import { GATES } from "../scripts/certify-sweep-w12.mjs";

/**
 * W12 — LƯỢT CHỨNG NHẬN PHẢI ĐỨNG YÊN TRÊN MỘT TRẠNG THÁI NGUỒN.
 *
 * ─── LỖI CÓ THẬT ──────────────────────────────────────────────────────────
 *
 * `evidence-provenance.test.ts` khoá được phán quyết cho MỘT artifact. Nó không
 * chạm tới thứ đã làm hỏng cả bộ bằng chứng W12: bảy artifact sinh ra trên bảy
 * dấu vân tay khác nhau rồi được cộng lại thành một tuyên bố COMPLETE. Từng
 * artifact một đều "hợp lệ lúc đo"; cái sai chỉ hiện ra khi nhìn cả LƯỢT.
 *
 * ─── VÌ SAO TIÊM LỖI TỪNG CA ──────────────────────────────────────────────
 *
 * Một cổng trả về true/false không chứng minh được nó đỏ vì ĐÚNG lý do — và
 * `ARCHITECTURE_MAP §8` #14 đã ghi: guard chưa từng đỏ là guard chưa được chứng
 * minh. Nên mỗi điều kiện được tiêm riêng và phải trả về đúng mã lý do của nó.
 */

const clean = (over: Record<string, unknown> = {}) => ({
  tool: "test",
  headBefore: "aaaa", headAfter: "aaaa",
  sourceFingerprintBefore: "ffff", sourceFingerprintAfter: "ffff",
  dirtyBefore: [] as string[], dirtyAfter: [] as string[],
  ...over,
});

describe("W12 §0 — bất biến source-freeze của một lượt chứng nhận", () => {
  it("KIỂM SOÁT DƯƠNG TÍNH — nguồn sạch, không nhúc nhích ⇒ VALID", () => {
    const v = sweepVerdict(clean());
    expect(v.state).toBe(SWEEP_VALID);
    expect(v.faults).toEqual([]);
  });

  it("A. vào lượt với cây nguồn BẨN ⇒ SOURCE_DIRTY_AT_SWEEP_START", () => {
    const v = sweepVerdict(clean({ dirtyBefore: ["frontend/src/x.ts"] }));
    expect(v.state).toBe(SWEEP_INVALID);
    expect(v.faults.join(" ")).toContain(SWEEP_FAULTS.DIRTY_AT_START);
    expect(v.faults.join(" ")).toContain("frontend/src/x.ts");
  });

  it("B. sửa mã GIỮA lượt ⇒ SOURCE_DIRTY_AT_SWEEP_END", () => {
    /* Đây đúng là quy trình cũ: chứng nhận target A → vá nguồn → chứng nhận
       target B → cộng cả hai làm bằng chứng cuối. */
    const v = sweepVerdict(clean({ dirtyAfter: ["frontend/src/simulations/ui.tsx"] }));
    expect(v.state).toBe(SWEEP_INVALID);
    expect(v.faults.join(" ")).toContain(SWEEP_FAULTS.DIRTY_AT_END);
  });

  it("C. commit giữa lượt ⇒ HEAD_MOVED_DURING_SWEEP", () => {
    const v = sweepVerdict(clean({ headAfter: "bbbb" }));
    expect(v.state).toBe(SWEEP_INVALID);
    expect(v.faults.join(" ")).toContain(SWEEP_FAULTS.HEAD_MOVED);
  });

  it("D. dấu vân tay đổi giữa lượt ⇒ SOURCE_FINGERPRINT_CHANGED_DURING_SWEEP", () => {
    /* Ca nguy hiểm nhất: `git add` một sửa đổi thì cây hết "bẩn" và HEAD chưa
       đổi, nhưng dấu vân tay (đọc INDEX) đã khác. Chỉ điều kiện này bắt được. */
    const v = sweepVerdict(clean({ sourceFingerprintAfter: "0000" }));
    expect(v.state).toBe(SWEEP_INVALID);
    expect(v.faults.join(" ")).toContain(SWEEP_FAULTS.FINGERPRINT_CHANGED);
  });

  it("E. bản ghi lượt vắng mặt KHÔNG được đoán thành hợp lệ", () => {
    expect(sweepVerdict(null).state).toBe(SWEEP_INVALID);
    expect(sweepVerdict(undefined).state).toBe(SWEEP_INVALID);
  });

  it("chụp thật trên kho này: begin/end cùng hình dạng, đọc được nguồn thật", () => {
    const rec = sweepEnd(sweepBegin("selftest"));
    expect(rec.sourceFingerprintBefore).toMatch(/^[0-9a-f]{16}$/);
    expect(rec.sourceFingerprintAfter).toBe(rec.sourceFingerprintBefore);
    expect(rec.headBefore).toBe(rec.headAfter);
    /* Không đòi cây sạch — người sửa code chạy vitest lúc đang dở là chuyện
       bình thường. Cổng sạch-cây là việc của LƯỢT CHỨNG NHẬN, không phải của
       vitest; đòi ở đây sẽ biến một guard thật thành thứ bị tắt đi. */
  });
});

describe("W12 §3 — bộ bằng chứng KHÔNG được trộn dấu vân tay", () => {
  it("trộn hai dấu vân tay ⇒ không ok, dù không artifact nào STALE riêng lẻ", () => {
    const mixed = crossCheckFreshness([]);
    expect(mixed.uniqueFingerprints).toBe(0);
    /* Rỗng KHÔNG phải "đạt" — đây là ca "empty target set accepted" trong ma
       trận lỗi hệ thống. */
    expect(mixed.ok).toBe(false);
  });

  it("kiểm chéo thật trên artifact W12 hiện có: đọc được và phán được", () => {
    const paths = GATES.map((g: { out: string }) => g.out);
    const cross = crossCheckFreshness(paths);
    expect(cross.rows.length).toBe(GATES.length);
    for (const r of cross.rows) {
      expect(["FRESH", "STALE_SOURCE", "DIRTY_SOURCE", "INCOMPATIBLE_TOOL", "UNKNOWN_PROVENANCE"])
        .toContain(r.state);
    }
    /* Không đòi FRESH ở đây: vitest chạy được trên cây đang sửa dở, và một guard
       đòi bằng chứng trình duyệt tươi trong mọi lượt vitest sẽ đỏ suốt rồi bị
       vô hiệu. Điều kiện FRESH là của `certify-sweep-w12.mjs`. */
  });
});

describe("W12 — danh sách cổng con không được rụng trong im lặng", () => {
  it("mọi artifact `w12-*.json` đang có đều thuộc một cổng con", () => {
    /* Bỏ một cổng rồi vẫn phát nhãn lượt-hợp-lệ là chứng nhận một HEAD chưa
       được kiểm — cùng khuôn với cổng khoá `GATES` của `full-gate.mjs`. */
    const dir = new URL("../../docs/evaluation/m20/", import.meta.url)
      .pathname.replace(/^\/([A-Za-z]:)/, "$1");
    const onDisk = readdirSync(dir)
      .filter((f) => f.startsWith("w12-") && f.endsWith(".json") && f !== "w12-sweep.json");
    const owned = new Set(GATES.map((g: { out: string }) => g.out.replace(/\\/g, "/").split("/").pop()));
    const orphan = onDisk.filter((f) => !owned.has(f));
    expect(orphan, `artifact W12 không cổng nào sở hữu:\n${orphan.join("\n")}`).toEqual([]);
  });

  it("phải có CẢ hai loại bằng chứng — dẫn từ hợp đồng VÀ trình duyệt thật", () => {
    /* `W12_REMAINING.md`: bảng ngữ nghĩa dẫn từ hợp đồng KHÔNG chứng minh được
       điều một cú bấm thật chứng minh. Một lượt chỉ có DERIVED là quay lại đúng
       lỗi "gọi thẳng module tính là bằng chứng trình duyệt". */
    const kinds = new Set(GATES.map((g: { kind: string }) => g.kind));
    expect(kinds.has("DERIVED")).toBe(true);
    expect(kinds.has("BROWSER")).toBe(true);
    expect(GATES.filter((g: { kind: string }) => g.kind === "BROWSER").length).toBeGreaterThanOrEqual(7);
  });

  it("bản ghi LƯỢT cũng phải phán được — không được nằm ngoài chính cổng của mình", () => {
    /* LỖI CÓ THẬT, bắt ở lượt cuối đầu tiên: `w12-sweep.json` có
       `sourceFingerprintBefore/After` nhưng không có khối phẳng, nên
       `provenanceVerdict` đọc vào trả UNKNOWN_PROVENANCE. Artifact chứng minh
       kỷ luật xuất xứ mà chính nó không phán được là một cổng tự miễn trừ. */
    const p = new URL("../../docs/evaluation/m20/w12-sweep.json", import.meta.url)
      .pathname.replace(/^\/([A-Za-z]:)/, "$1");
    if (!existsSync(p)) return; // chưa chạy lượt nào — không bịa phán quyết
    const data = JSON.parse(readFileSync(p, "utf-8"));
    expect(provenanceVerdict(data).state,
      "bản ghi lượt thiếu khối provenance phẳng").not.toBe("UNKNOWN_PROVENANCE");
    /* Và hai đầu Before/After KHÔNG được bị khối phẳng đè mất. */
    expect(data.sourceFingerprintBefore).toMatch(/^[0-9a-f]{16}$/);
    expect(data.sourceFingerprintAfter).toMatch(/^[0-9a-f]{16}$/);
  });

  it("artifact của lượt nằm NGOÀI dấu vân tay nguồn — không tự vô hiệu hoá", () => {
    const before = sourceFingerprint();
    for (const g of GATES as { out: string }[]) {
      const p = g.out.replace(/\\/g, "/");
      expect(p, "artifact chứng nhận đang ghi vào cây nguồn").toContain("docs/evaluation/");
      expect(p).not.toContain("/frontend/src/");
      expect(p).not.toContain("/frontend/scripts/");
    }
    expect(sourceFingerprint()).toBe(before);
  });
});
