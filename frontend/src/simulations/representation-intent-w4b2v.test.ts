import { beforeAll, describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { getSimulation, listSimulations } from "./registry";
import { registerAllSimulations } from "./index";
import {
  alternateStatusOf,
  availableVisualModes,
  effectiveVisualMode,
  learnerFacingModes,
  primaryRepresentationOf,
  representationPolicyProblems,
} from "./renderer";

/**
 * W4B-2V — CHẾ ĐỘ RENDER ĐƯỢC HỖ TRỢ ≠ BIỂU DIỄN CHÍNH CỦA HỌC SINH.
 *
 * Lỗi đang khoá: hễ một target dựng được hai renderer là UI bày `[2D] [3D]`.
 * Đó là đem một CHI TIẾT CÀI ĐẶT lên làm QUYẾT ĐỊNH CỦA HỌC SINH — mà học sinh
 * chưa hiểu cơ chế thì lấy gì để chọn giữa 2D và 3D?
 *
 * Phân bố 21/0/1 của các wave trước là TRẠNG THÁI ĐO ĐƯỢC, không phải chỉ tiêu
 * phải giữ. Các test dưới đây khoá LUẬT, không khoá con số.
 */

beforeAll(() => {
  if (listSimulations().length === 0) registerAllSimulations();
});

const mods = () => listSimulations().map((m) => getSimulation(m.id)!);

describe("W4B-2V · công tắc đổi cách xem KHÔNG dẫn xuất từ số renderer", () => {
  it("(1) có ≥2 renderer mà không có lý do sư phạm ⇒ KHÔNG bày công tắc", () => {
    for (const m of mods()) {
      if (availableVisualModes(m).length < 2) continue;
      if (alternateStatusOf(m) !== "NO_ALTERNATE_NEEDED") continue;
      expect(learnerFacingModes(m), `${m.id}: bày công tắc chỉ vì có hai renderer`)
        .toEqual([]);
    }
  });

  it("target một mode: không bao giờ có công tắc", () => {
    for (const m of mods()) {
      if (availableVisualModes(m).length >= 2) continue;
      expect(learnerFacingModes(m), `${m.id}`).toEqual([]);
      expect(alternateStatusOf(m)).toBe("NO_ALTERNATE_NEEDED");
    }
  });

  it("mọi target đều có ĐÚNG MỘT biểu diễn chính, và nó dựng được", () => {
    for (const m of mods()) {
      const primary = primaryRepresentationOf(m);
      expect(availableVisualModes(m), `${m.id}: biểu diễn chính không dựng được`)
        .toContain(primary);
    }
  });

  it("bày cách xem thay thế thì PHẢI nói vì sao — không thì chính sách báo lỗi", () => {
    const problems = mods().flatMap(representationPolicyProblems);
    expect(problems, problems.join("\n")).toEqual([]);
  });
});

describe("W4B-2V · quyết định theo capability, KHÔNG theo chuỗi ngữ cảnh", () => {
  it("(2) chủ sở hữu chính sách chỉ biết `./types` — không chạm đề bài/tiêu đề", () => {
    const src = readFileSync(new URL("./renderer.ts", import.meta.url), "utf-8")
      .replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    for (const bad of ["title", "summary", "problem", "description", "notes"]) {
      expect(src, `renderer.ts rẽ nhánh theo ngữ cảnh (${bad})`).not.toContain(bad);
    }
    expect(src).not.toMatch(/id\s*===\s*["']/);
    const imports = [...src.matchAll(/from\s+["']([^"']+)["']/g)].map((x) => x[1]);
    expect(imports.sort()).toEqual(["./types", "react"]);
  });
});

describe("W4B-2V · đổi cách xem là TRÌNH BÀY THUẦN", () => {
  it("(3) mode hiệu lực chỉ phụ thuộc module + yêu cầu — không đụng state", () => {
    /* `effectiveVisualMode` là hàm thuần: gọi bao nhiêu lần với cùng đầu vào
       cũng ra một kết quả, và nó không nhận state nên không thể reset mô phỏng. */
    for (const m of mods()) {
      const a = effectiveVisualMode(m, "3d");
      const b = effectiveVisualMode(m, "3d");
      expect(a).toBe(b);
      expect(availableVisualModes(m)).toContain(a);
    }
  });

  it("(3b) yêu cầu một mode KHÔNG được bày ⇒ rơi về biểu diễn chính, không nổ", () => {
    for (const m of mods()) {
      if (learnerFacingModes(m).length > 0) continue;
      expect(effectiveVisualMode(m, "3d"), `${m.id}`).toBe(primaryRepresentationOf(m));
    }
  });

  it("(4) hai cách xem của cùng target dùng CHUNG module ⇒ không thể lệch đáp án", () => {
    for (const m of mods()) {
      if (learnerFacingModes(m).length < 2) continue;
      // Cùng một `SimulationModule` ⇒ cùng init/apply/timeline/predict theo định nghĩa.
      expect(m.id, "3D không được có simulation_id riêng").not.toMatch(/_?3d$/i);
      expect(typeof m.init).toBe("function");
      expect(Object.keys(m.renderers ?? {}).length).toBeGreaterThan(0);
    }
  });
});

describe("W4B-2V · trạng thái hiện tại của danh mục (mô tả, không phải chỉ tiêu)", () => {
  it("ghi lại target nào đang bày công tắc và vì sao", () => {
    const exposed = mods().filter((m) => learnerFacingModes(m).length > 1);
    // Con số này ĐƯỢC PHÉP đổi khi có bằng chứng cơ chế mới — test chỉ đòi
    // mỗi target đang bày công tắc phải khai đủ lý do.
    for (const m of exposed) {
      expect(m.representation?.alternate).not.toBe("NO_ALTERNATE_NEEDED");
      expect((m.representation?.alternateReason ?? "").length).toBeGreaterThan(20);
    }
    /* W12 §3: KHÔNG target nào còn bày công tắc cho học sinh.
       `protocol_encapsulation` — target duy nhất từng bày — nay khai 3D là biểu
       diễn chính, 2D lùi về nội bộ. Danh sách rỗng là kết quả MONG MUỐN, nhưng
       một danh sách rỗng cũng làm vòng lặp trên chạy 0 lần, nên phải khẳng định
       riêng rằng phép quét có thật sự nhìn thấy danh mục. */
    expect(mods().length, "không quét được module nào ⇒ mọi khẳng định trên vô nghĩa")
      .toBeGreaterThan(20);
    expect(exposed.map((m) => m.id)).toEqual([]);
  });

  it("W12 §3 — `protocol_encapsulation`: 3D là biểu diễn CÔNG KHAI, 2D lùi về nội bộ", () => {
    /* TIỀN ĐỀ ĐỔI theo quyết định sản phẩm của người dùng, nêu lại nhiều lần:
       đóng gói TCP/IP dạy quan hệ BỌC NHAU — một quan hệ không gian mà 2D phải
       diễn đạt bằng xếp chồng, và học sinh đọc ra "bốn ô cạnh nhau".
       2D KHÔNG bị gỡ: nó còn nguyên cho parity renderer (`render-parity`,
       `encap-render3d`) — chỉ thôi không bày cho học sinh. */
    const m = getSimulation("network.protocol_encapsulation")!;
    expect(primaryRepresentationOf(m)).toBe("3d");
    expect(alternateStatusOf(m)).toBe("NO_ALTERNATE_NEEDED");
    expect(learnerFacingModes(m), "công tắc 2D/3D vẫn còn bày cho học sinh").toEqual([]);
    /* Năng lực KỸ THUẬT vẫn hai mode — đó là điều kiện để parity nội bộ chạy. */
    expect(availableVisualModes(m).sort()).toEqual(["2d", "3d"]);
  });
});
