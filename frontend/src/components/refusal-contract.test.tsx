import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import {
  NHAN_GIAI_DOAN,
  NHAN_LOAI_VAN_DE,
  UnsupportedNotice,
} from "./SimulationWorkspace";

/**
 * (PRODUCT_RESPONSE_CONTRACT_ALIGNMENT) BỀ MẶT TỪ CHỐI PHẢI NÓI ĐỦ VÀ NÓI THẬT.
 *
 * `THESIS_DRAFT §1.6/§3.9` hứa một *"từ chối có cấu trúc — nêu giai đoạn dừng,
 * loại thất bại, mã lỗi"*. Lượt đo cuối giao `n1` với `stage_reached = null` và
 * `error_code = null`, và màn hình không hiện một chữ nào về giai đoạn dừng.
 *
 * Hai luật chia đôi trách nhiệm, và bộ test này khoá cả hai:
 *
 *   BACKEND sở hữu PHÂN LOẠI — `stage_reached`, `failure_category`,
 *     `error_code`. Frontend không được suy ra chúng, và tuyệt đối không được
 *     đoán chúng bằng cách dò chữ trong `reason`/`learner_reason`.
 *   FRONTEND sở hữu CÁCH NÓI — bảng nhãn tiếng Việt. Khoá kĩ thuật vào, tên
 *     tiếng Việt ra; đúng cách dùng mà `ui-hygiene.test.ts` cho phép.
 *
 * Fixture đọc từ `docs/evaluation/…/product-ui-result-rendering/fixtures` —
 * phản hồi THẬT của lượt đo cuối, dựng lại 0 lượt gọi. Không dựng envelope giả
 * cho hai ca trung tâm: một bề mặt xanh trên envelope tự bịa không chứng minh
 * gì về sản phẩm.
 */

const FIXTURES = join(
  __dirname,
  "..",
  "..",
  "..",
  "docs",
  "evaluation",
  "geometry",
  "product-ui-result-rendering",
  "fixtures",
);

type Envelope = {
  status: string;
  reason: string;
  learner_reason?: string;
  failure_category?: string;
  error_code?: string;
  stage_reached?: string;
};

function docFixture(id: string): Envelope {
  return JSON.parse(readFileSync(join(FIXTURES, `${id}.json`), "utf8")).envelope;
}

function html(unsupported: Partial<Envelope> & { reason: string }): string {
  return renderToString(
    <UnsupportedNotice unsupported={unsupported} />,
  ).replace(/<!--.*?-->/g, "");
}

const N1 = "n1_khoi_tron_xoay_tong_quat";
const N2 = "n2_khoi_ghep_bu_can_boolean";

describe("hai ca âm của lượt đo cuối hiện đủ bốn sự thật", () => {
  it.each([N1, N2])("%s — envelope mang đủ trường cấu trúc", (id) => {
    const e = docFixture(id);
    expect(e.status).toBe("unsupported");
    expect(e.stage_reached, "giai đoạn dừng").toBeTruthy();
    expect(e.error_code, "mã lỗi").toBeTruthy();
    expect(e.failure_category).toBeTruthy();
    expect(e.learner_reason).toBeTruthy();
  });

  it.each([N1, N2])("%s — màn hình hiện giai đoạn và loại vấn đề", (id) => {
    const out = html(docFixture(id));
    expect(out).toContain("Dừng ở bước");
    expect(out).toContain("Loại vấn đề");
    expect(out).not.toContain("Không xác định được từ phản hồi cũ");
  });

  it.each([N1, N2])("%s — KHÔNG lộ mã kĩ thuật ra màn hình", (id) => {
    const e = docFixture(id);
    const out = html(e);
    expect(out).not.toContain(e.error_code!);
    expect(out).not.toContain(e.stage_reached!);
    expect(out).not.toContain(e.failure_category!);
  });

  it("n2 — tiêu đề và lý do KHÔNG nói hai kết luận khác nhau", () => {
    const out = html(docFixture(N2));
    // Ngoài bao đóng: không được vừa nói "ngoài các phép dựng" vừa khuyên
    // "diễn đạt lại đề" — viết lại không tạo ra một phép dựng chưa tồn tại.
    expect(out).toContain("ngoài các phép dựng");
    expect(out).not.toContain("diễn đạt lại");
  });

  it("n1 — không hứa hệ mô phỏng được dạng bài này", () => {
    const out = html(docFixture(N1));
    expect(out).not.toContain("Dạng bài này hệ có mô phỏng");
  });
});

describe("envelope CŨ thiếu trường vẫn render an toàn", () => {
  it("thiếu cả stage lẫn code → nói KHÔNG XÁC ĐỊNH, không đoán", () => {
    const out = html({
      reason: "Bài này chưa có mô phỏng phù hợp trong danh mục.",
      learner_reason: "Hệ chưa dựng được mô phỏng cho đề này.",
    });
    expect(out).toContain("Không xác định được từ phản hồi cũ");
    expect(out).toContain("Dừng ở bước");
  });

  it("mã lạ (backend mới hơn FE) → nhãn trung tính, KHÔNG in mã thô", () => {
    const out = html({
      reason: "x",
      learner_reason: "y",
      stage_reached: "mot_giai_doan_chua_co_nhan",
      error_code: "mot_ma_chua_co_nhan",
    });
    expect(out).not.toContain("mot_giai_doan_chua_co_nhan");
    expect(out).not.toContain("mot_ma_chua_co_nhan");
    expect(out).toContain("Không xác định được từ phản hồi cũ");
  });

  it("không có learner_reason lẫn reason → vẫn có một câu tử tế", () => {
    const out = html({ reason: undefined as unknown as string });
    expect(out).toContain("chưa được kiểm chứng");
  });
});

describe("ca dương KHÔNG bao giờ đi qua bề mặt từ chối", () => {
  it("mọi fixture dương đều status ok và không có trường từ chối", () => {
    const duong = readdirSync(FIXTURES).filter((f) => f.startsWith("p"));
    expect(duong.length).toBe(7);
    for (const f of duong) {
      const e = docFixture(f.replace(/\.json$/, ""));
      expect(e.status, f).toBe("ok");
      expect(e.learner_reason, f).toBeUndefined();
    }
  });
});

/**
 * §9.7 — GUARD KIẾN TRÚC. Thay bảng tra bằng phép DÒ CHUỖI phải làm test này
 * đỏ. Không có nó, một bản vá "tiện tay" kiểu `reason.includes("phủ")` sẽ xanh
 * hết và dựng lại đúng thẩm quyền phân loại thứ hai mà `error_codes.py` tồn
 * tại để thay.
 */
describe("frontend KHÔNG suy phân loại từ chuỗi", () => {
  const src = readFileSync(join(__dirname, "SimulationWorkspace.tsx"), "utf8");
  const than = src.slice(src.indexOf("export function UnsupportedNotice"));

  it("không dò chuỗi trên reason/learner_reason", () => {
    const toi: string[] = [];
    for (const m of than.matchAll(
      /\b(reason|learner_reason)\b\s*[?.]*\s*\.\s*(includes|match|indexOf|startsWith|endsWith|search|test)\b/g,
    )) {
      toi.push(m[0]);
    }
    // Cả chiều ngược lại: regex/`test()` lấy `reason` làm đối số.
    for (const m of than.matchAll(/\.test\(\s*[a-zA-Z_.]*reason/g)) toi.push(m[0]);
    expect(toi, `phân loại phải đọc TRƯỜNG, không đọc văn xuôi:\n${toi.join("\n")}`)
      .toEqual([]);
  });

  it("mỗi nhánh phân loại đều so bằng === trên một trường có cấu trúc", () => {
    const truong = ["failure_category", "error_code", "stage_reached"];
    for (const t of truong) {
      const dung = than.includes(`unsupported.${t}`);
      if (!dung) continue;
      // Chỉ chấp nhận so sánh hằng hoặc tra bảng — không toán tử chuỗi nào.
      const xau = new RegExp(
        `unsupported\\.${t}\\s*\\.\\s*(includes|match|indexOf|search|slice|replace)`,
      );
      expect(xau.test(than), `${t} bị xử lý như văn xuôi`).toBe(false);
    }
  });
});

describe("bảng nhãn phủ hết thứ fixture thật mang tới", () => {
  it("mọi stage/code trong 9 fixture đều có nhãn", () => {
    const thieu: string[] = [];
    for (const f of readdirSync(FIXTURES)) {
      const e = docFixture(f.replace(/\.json$/, ""));
      if (e.status !== "unsupported") continue;
      if (e.stage_reached && !NHAN_GIAI_DOAN[e.stage_reached]) {
        thieu.push(`giai đoạn ${e.stage_reached}`);
      }
      const khoa = e.error_code ?? e.failure_category;
      if (khoa && !NHAN_LOAI_VAN_DE[khoa]) thieu.push(`loại ${khoa}`);
    }
    expect(thieu, `bảng nhãn thiếu:\n${thieu.join("\n")}`).toEqual([]);
  });
});
