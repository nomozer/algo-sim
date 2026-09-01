import { describe, expect, it } from "vitest";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

/**
 * WAVE 8 — BỘ CHỌN TEST PHẢI TỰ ĐƯỢC KIỂM, VÀ NHÃN PHẢI TRUNG THỰC.
 *
 * ─── VÌ SAO ───────────────────────────────────────────────────────────────
 *
 * Một bộ chọn test là thứ nguy hiểm nhất có thể sai trong repo này, vì khi nó
 * sai thì mọi thứ khác vẫn xanh. Repo đã bị đúng kiểu "khớp 0 mục nhưng báo
 * thành công" nhiều lần trong chương trình này: một phép thay chuỗi không khớp,
 * một hàm tua gọi API không tồn tại, một phép tiêm bắn nhầm dòng, một guard chỉ
 * soi cột điểm mã. Mỗi lần đều đọc ra màu xanh.
 *
 * Nên bộ chọn được kiểm theo HAI CHIỀU:
 *   THIẾU  — chủ sở hữu dùng chung mà chỉ chọn một test hẹp ⇒ ĐỎ
 *   THỪA   — một renderer lẻ mà kéo cả kho ⇒ ĐỎ
 *
 * Và nhãn kết quả bị khoá: chỉ T3 được nói "FULL_PRODUCT_GATE_PASS".
 */

const REPO = new URL("../..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");

/** Chạy bộ chọn ở chế độ khô trên một tập file GIẢ ĐỊNH, không đụng cây thật. */
function planFor(files: string[]) {
  const out = execFileSync("node", ["frontend/scripts/impact.mjs", "--dry", "--files", files.join(",")],
    { cwd: REPO, encoding: "utf-8" });
  return out;
}

describe("W8 §10 — bộ chọn chọn đúng theo chủ sở hữu", () => {
  it("renderer một miền ⇒ chỉ miền đó", () => {
    const out = planFor(["frontend/src/simulations/domains/web/ui.tsx"]);
    expect(out).toContain("miền web");
    expect(out).toContain("src/simulations/domains/web/");
    /* THỪA: một renderer lẻ KHÔNG được kéo cả kho. */
    expect(out, "chọn thừa: renderer lẻ kéo cả src/").not.toMatch(/Đã chọn:.*\n?.*\bsrc\/\b(?!simulations)/);
    expect(out).not.toContain("+ pytest");
  });

  it("engine nhị phân ⇒ test miền binary", () => {
    const out = planFor(["frontend/src/simulations/domains/binary/base-conversion.ts"]);
    expect(out).toContain("miền binary");
    expect(out).toContain("src/simulations/domains/binary/");
  });

  it("CHỦ SỞ HỮU DÙNG CHUNG mở rộng bán kính, không thu về một test hẹp", () => {
    /* THIẾU: đây là chiều dễ sai nhất — `SimulationControls` chỉ chạy đúng
       `SimulationControls.test.tsx` thì mọi miền có dòng thời gian mất bảo vệ. */
    const out = planFor(["frontend/src/components/SimulationControls.tsx"]);
    expect(out).toContain("CHỦ SỞ HỮU DÙNG CHUNG");
    expect(out).toContain("src/components/");
    expect(out).toContain("experience-manifest.test.ts");
  });

  it("store ⇒ nhiều miền", () => {
    const out = planFor(["frontend/src/state/store.ts"]);
    expect(out).toContain("CHỦ SỞ HỮU DÙNG CHUNG");
    for (const t of ["src/state/", "src/components/"]) expect(out).toContain(t);
  });

  it("CSS dùng chung ⇒ guard token phải nằm trong tập chọn", () => {
    /* `var()` trỏ token không tồn tại là lỗi IM LẶNG — đồ thị import không bao
       giờ nối một file CSS tới `tokens.test.ts`, nên nó phải khai theo sở hữu. */
    const out = planFor(["frontend/src/styles/global.css"]);
    /* Phải đòi ĐÚNG thư mục chứa `tokens.test.ts`. Bản đầu chỉ đòi chuỗi
       "src/styles/" xuất hiện đâu đó trong output, và nó xanh cả khi phép tiêm
       đã gỡ hẳn `src/styles/` khỏi danh sách test — vì tên file bị đổi vẫn được
       in ở phần "Đã đổi". Soi phần liệt kê thay đổi thay vì phần chọn test là
       guard không soi gì. */
    const chosen = out.slice(out.indexOf("Lý do chọn:"));
    expect(chosen, "guard token không nằm trong tập chọn").toContain("src/styles/");
    expect(chosen).toContain("experience-manifest.test.ts");
  });

  it("validator backend ⇒ chạy pytest", () => {
    const out = planFor(["backend/app/validation/simulation.py"]);
    expect(out).toContain("pytest");
  });

  it("chỉ tài liệu ⇒ gate nhẹ, và NÓI RÕ vì sao bỏ suite hiện thực", () => {
    const out = planFor(["docs/STATUS_LEDGER.md"]);
    expect(out).toContain("TÀI LIỆU");
    expect(out).toContain("code-index-sync");
    expect(out).not.toContain("+ pytest");
  });

  it("file sản phẩm KHÔNG tra ra chủ ⇒ leo thang, KHÔNG im lặng chọn rỗng", () => {
    const out = planFor(["frontend/src/khong-biet-cua-ai.ts"]);
    expect(out).toContain("IMPACT_MAPPING_MISSING");
    expect(out).toContain("KHÔNG TRA RA CHỦ SỞ HỮU");
    expect(out).toContain("pytest");
  });

  it("KHÔNG BAO GIỜ có tập chọn rỗng cho thay đổi mã sản phẩm", () => {
    for (const f of [
      "frontend/src/simulations/domains/logic/index.ts",
      "backend/app/simulation/catalog.py",
      "frontend/src/khong-ai-so-huu.tsx",
    ]) {
      const out = planFor([f]);
      expect(out, f).toMatch(/Đã chọn: [1-9]/);
    }
  });
});

// ── NGỮ NGHĨA NHÃN (§29) ────────────────────────────────────────────────────

describe("W8 §29 — tầng nhỏ không được nói giọng tầng lớn", () => {
  const src = readFileSync(new URL("../scripts/impact.mjs", import.meta.url)
    .pathname.replace(/^\/([A-Za-z]:)/, "$1"), "utf-8");

  it("T0 phát IMPACT_GATE_PASS, tuyệt đối không phát FULL_PRODUCT_GATE_PASS", () => {
    expect(src).toContain("IMPACT_GATE_PASS");
    /* Phải soi chỗ PHÁT NHÃN, không soi cả file: bản đầu cấm chuỗi
       "FULL_PRODUCT_GATE_PASS" xuất hiện ở bất cứ đâu, và nó đỏ vì chính câu
       miễn trừ của T0 có nhắc tên nhãn ấy. Cấm nhắc tên thì T0 không tự khai
       được giới hạn của mình — guard đi ngược điều nó muốn bảo vệ. */
    const emitted = src.match(/console\.log\(`[^`]*Kết quả:[^`]*`\)/)?.[0] ?? "";
    /* KHỚP RỖNG LÀ HỎNG, KHÔNG PHẢI ĐẠT.
       Bản đầu dùng mẫu thiếu `\n` ở đầu nên nó khớp rỗng, và `""` thì không
       chứa gì cả — guard xanh trong khi phép tiêm đã nhét
       FULL_PRODUCT_GATE_PASS vào đúng dòng ấy. Đây chính là lỗi "khớp 0 mục
       nhưng báo thành công" mà cả wave này tồn tại để chống, xuất hiện ngay
       trong guard chống nó. */
    expect(emitted.length, "không tìm thấy dòng phát nhãn — mẫu hỏng, không phải đạt")
      .toBeGreaterThan(10);
    expect(emitted, "T0 đang tự nhận là gate đầy đủ").not.toContain("FULL_PRODUCT");
    expect(src, "T0 phải tự khai giới hạn của mình").toContain("KHÔNG thay được gate");
  });

  it("hợp đồng bốn tầng có tài liệu ràng buộc", () => {
    const doc = readFileSync(new URL("../../docs/TEST_TIERS.md", import.meta.url)
      .pathname.replace(/^\/([A-Za-z]:)/, "$1"), "utf-8");
    for (const label of ["IMPACT_GATE_PASS", "DOMAIN_GATE_PASS", "WAVE_GATE_PASS", "FULL_PRODUCT_GATE_PASS"]) {
      expect(doc, `TEST_TIERS.md thiếu nhãn ${label}`).toContain(label);
    }
    expect(doc, "phải ghi luật không-chọn-rỗng").toContain("không bao giờ được chọn 0 test");
  });

  it("T3 phải gồm ĐỦ các cổng con quan trọng", () => {
    /* Bỏ một cổng mà vẫn phát `FULL_PRODUCT_GATE_PASS` là kiểu nói dối tệ nhất
       trong cả hệ thống test: nó CHỨNG NHẬN một HEAD chưa được kiểm. Danh sách
       này là hợp đồng, không phải chi tiết hiện thực của script. */
    const gate = readFileSync(new URL("../scripts/full-gate.mjs", import.meta.url)
      .pathname.replace(/^\/([A-Za-z]:)/, "$1"), "utf-8");
    /* Soi MẢNG CỔNG, không soi cả file.
       Bản đầu dùng `toContain` trên toàn văn và nó xanh cả khi phép tiêm đã gỡ
       hẳn cổng benchmark khỏi mảng — vì cái tên còn sót lại trong một câu bình
       luận. Guard soi comment là guard không soi gì. */
    const arr = gate.slice(gate.indexOf("const GATES = ["), gate.indexOf("\n];"));
    expect(arr.length, "không tìm thấy mảng GATES — mẫu hỏng, không phải đạt")
      .toBeGreaterThan(200);
    const names = [...arr.matchAll(/name: "([^"]+)"/g)].map((m) => m[1]);
    /* HAI TÊN CUỐI ĐÃ ĐỔI, SỐ LƯỢNG THÌ KHÔNG (FINAL_DEAD_EVALUATION_CLEANUP).
       Trước đây là "benchmark chương trình" + "catalog" — hai cổng đo danh mục
       24 target Tin học, và cả hai đã chết khi import từ lúc danh mục ấy bị gỡ,
       nghĩa là T3 đã hỏng sẵn. Chúng được THAY, không phải bỏ: hợp đồng ở đây
       là *T3 vẫn kiểm năm thứ*, trong đó hai thứ là bằng chứng tất định của
       miền đang là sản phẩm. Hạ xuống ba cổng mới là thứ guard này sinh ra để
       chặn, nên số lượng được khoá riêng bên dưới. */
    for (const required of ["pytest", "vitest", "build", "demo khoá luận", "bề mặt sập"]) {
      expect(names.join(" | "), `T3 thiếu cổng con: ${required}`).toContain(required);
    }
    expect(names.length, "T3 bị bớt cổng — nhãn đầy đủ sẽ chứng nhận ít hơn nó nói")
      .toBeGreaterThanOrEqual(5);
    expect(gate, "chỉ T3 được phát nhãn đầy đủ").toContain("FULL_PRODUCT_GATE_PASS");
    expect(gate, "một cổng con đỏ phải chặn nhãn").toContain("FULL_PRODUCT_GATE_FAIL");
  });

  it("live AI KHÔNG nằm trong tầng tất định", () => {
    expect(src, "bộ chọn T0 không được gọi runner live").not.toMatch(/ALLOW_LIVE_AI|live_smoke|evaluation\.live/);
  });
});
