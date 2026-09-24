import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import type { ImageExtractionResponse, PhotoAssessment, PhotoExtraction } from "../llm/client";
import { PhotoProblemPanel } from "./PhotoProblemPanel";
import { ProblemInput } from "./ProblemInput";
import { initialPhotoState, photoReducer, type PhotoAction, type PhotoState } from "./photo-problem-flow";
import c03CongKhai from "./photo-c03-diagram-only.fixture.json";

/**
 * Bề mặt ảnh đề bài — PHOTO_PROBLEM_TO_SCENE_END_TO_END §3/§9 "Frontend".
 *
 * `renderToString` không chạy effect, nên đây khoá MARKUP của từng trạng thái:
 * đủ nút, nhãn cho trình đọc màn hình, chuỗi từ ảnh bị thoát ký tự, và không
 * mã kĩ thuật nào lọt ra. Hành vi bấm được khoá ở `photo-problem-flow.test.ts`.
 */

const DE = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2. Tính thể tích khối chóp.";
const ANH = { name: "de.jpg", type: "image/jpeg", size: 120_000 };
const noop = () => {};
const XU_LY = {
  onRotate: noop,
  onReplace: noop,
  onRemove: noop,
  onRead: noop,
  onEdit: noop,
  onConfirm: noop,
  onBuild: noop,
};

function phanHoi(danhGia: Partial<PhotoAssessment> = {}, trich: Partial<PhotoExtraction> = {}): ImageExtractionResponse {
  return {
    status: "ok",
    extraction: {
      problem_text_verbatim: DE,
      problem_text_normalized: DE,
      math_expressions: [],
      named_points: [],
      named_lines: [],
      named_planes: [],
      named_solids: [],
      given_relations: [],
      has_diagram: false,
      diagram_observations: [],
      text_diagram_conflicts: [],
      uncertain_tokens: [],
      missing_regions: [],
      confidence: 0.9,
      ...trich,
    },
    assessment: {
      status: "ready_for_review",
      rejection_code: null,
      review_flags: [],
      requires_confirmation: false,
      problem_text: DE,
      learner_message: null,
      flag_messages: [],
      ...danhGia,
    },
    image: {
      sha256: "b".repeat(64),
      width: 640,
      height: 480,
      source_mime: "image/jpeg",
      exif_orientation: 1,
      rotation_applied: 0,
      downscaled: false,
      metadata_removed: true,
      source_had_gps: false,
    },
    cached: false,
  };
}

const chay = (...a: PhotoAction[]): PhotoState => a.reduce(photoReducer, initialPhotoState);

function docXong(res: ImageExtractionResponse): PhotoState {
  const s = chay({ type: "select", file: ANH }, { type: "read-start" });
  return photoReducer(s, { type: "read-success", requestId: s.requestId, response: res });
}

const ve = (s: PhotoState) =>
  renderToString(<PhotoProblemPanel state={s} previewUrl="blob:anh-de-bai" {...XU_LY} />).replace(/<!-- -->/g, "");

function nutDung(html: string): string {
  return /<button[^>]*>(?:Dựng mô phỏng|Đang dựng…)<\/button>/.exec(html)?.[0] ?? "";
}

describe("ô nhập đề — hai lối vào ảnh, luồng gõ tay còn nguyên", () => {
  const html = renderToString(<ProblemInput />);

  it("có nút Chụp ảnh và Tải ảnh, có nhãn cho trình đọc màn hình", () => {
    expect(html).toContain("Chụp ảnh");
    expect(html).toContain("Tải ảnh");
    expect(html).toContain('aria-label="Chụp ảnh đề bài bằng máy ảnh"');
    expect(html).toContain('aria-label="Tải ảnh đề bài từ máy"');
  });

  it("input chụp ảnh gợi ý máy ảnh sau; cả hai chỉ nhận PNG/JPEG/WEBP", () => {
    expect(html).toContain('capture="environment"');
    expect(html.match(/accept="image\/png,image\/jpeg,image\/webp"/g)?.length).toBe(2);
  });

  it("luồng gõ tay KHÔNG đổi: ô nhập, nút gửi, nút + vẫn ở đó; chưa có khối ảnh", () => {
    expect(html).toContain('placeholder="Nhập đề hình học không gian, hoặc tải lên tệp đề…"');
    expect(html).toContain('aria-label="Phân tích đề bằng AI"');
    expect(html).toContain('aria-label="Tải tệp đề"');
    expect(html).not.toContain("photo-panel");
  });
});

describe("khối ảnh — theo trạng thái", () => {
  it("chưa có ảnh ⇒ không dựng gì", () => {
    expect(ve(initialPhotoState)).toBe("");
  });

  it("đã chọn ⇒ xem trước + xoay/thay/xoá + đọc, có vùng trạng thái aria-live", () => {
    const html = ve(chay({ type: "select", file: ANH }));
    expect(html).toContain('alt="Ảnh đề bài de.jpg"');
    expect(html).toContain("rotate(0deg)");
    for (const nhan of ["Xoay ảnh", "Thay ảnh", "Xoá ảnh", "Đọc đề trong ảnh"]) expect(html).toContain(nhan);
    expect(html).toContain('role="status"');
    expect(html).toContain('aria-live="polite"');
  });

  it("xoay ⇒ ảnh xem trước xoay theo", () => {
    expect(ve(chay({ type: "select", file: ANH }, { type: "rotate" }))).toContain("rotate(90deg)");
  });

  it("đang đọc ⇒ nút đọc khoá và báo bận", () => {
    const html = ve(chay({ type: "select", file: ANH }, { type: "read-start" }));
    expect(html).toMatch(/<button[^>]*disabled=""[^>]*aria-busy="true"[^>]*>Đang đọc…<\/button>/);
  });

  it("đọc xong, không cờ ⇒ ô nội dung có nhãn, điền sẵn, nút dựng MỞ", () => {
    const html = ve(docXong(phanHoi()));
    expect(html).toContain('<label class="photo-label" for="photo-problem-text">');
    expect(html).toContain('id="photo-problem-text"');
    expect(html).toContain(DE);
    expect(html).not.toContain('type="checkbox"');
    expect(nutDung(html)).not.toContain("disabled");
  });

  it("có cờ ⇒ cảnh báo, chỗ không chắc, quan sát từ hình gắn nhãn tham khảo, phải xác nhận", () => {
    const html = ve(
      docXong(
        phanHoi(
          {
            review_flags: ["UNCERTAIN_TOKENS", "DIAGRAM_OBSERVATIONS_NOT_USED"],
            requires_confirmation: true,
            flag_messages: ["Có chữ hoặc số đọc chưa chắc chắn — em đối chiếu lại với ảnh."],
          },
          {
            uncertain_tokens: [{ token: "0", alternatives: ["O"], location: "tâm O(0;0;0)", reason: "mờ" }],
            diagram_observations: ["Nét đứt ở cạnh SB."],
            math_expressions: [{ verbatim: "a can 3", normalized: "a√3" }],
          },
        ),
      ),
    );
    expect(html).toContain("em đối chiếu lại với ảnh");
    expect(html).toContain("“0” có thể là “O”");
    expect(html).toContain("chỉ để tham khảo, không dùng làm dữ kiện");
    expect(html).toContain("Nét đứt ở cạnh SB.");
    expect(html).toContain("a√3");
    expect(html).toContain('type="checkbox"');
    expect(nutDung(html)).toContain("disabled");
    expect(html).toContain('id="photo-build-hint"');
  });

  it("bị từ chối ⇒ lời báo tiếng Việt ở vùng role=alert", () => {
    const html = ve(
      docXong(
        phanHoi({
          status: "rejected",
          rejection_code: "MISSING_PROBLEM_TEXT",
          requires_confirmation: true,
          problem_text: "",
          learner_message: "Ảnh chỉ có hình vẽ, không có đề bài bằng chữ.",
        }),
      ),
    );
    expect(html).toMatch(/role="alert"[^>]*>Ảnh chỉ có hình vẽ, không có đề bài bằng chữ\./);
  });

  it("chuỗi đọc từ ảnh bị THOÁT ký tự — không thành thẻ HTML", () => {
    const doc = '<img src=x onerror=alert(1)> Cho hình chóp S.ABC.';
    const html = ve(docXong(phanHoi({ problem_text: doc }, { problem_text_verbatim: doc })));
    expect(html).toContain("&lt;img src=x onerror=alert(1)&gt;");
    expect(html).not.toContain("<img src=x");
  });

  it("ảnh CHỈ CÓ HÌNH (C03 thật, bản công khai sau guard) ⇒ quan sát dưới nhãn tham khảo, ô dựng trống, nút dựng khoá", () => {
    // VISION_DIAGRAM_ONLY_PROVENANCE_GUARD_FIX. Fixture là phản hồi `/api/image/extract` do BACKEND dựng từ lượt đọc
    // C03 thật (`test_vision_diagram_only_provenance_guard.py` khoá cho khớp từng byte). Mô hình đã ghi ba quan hệ
    // vuông góc đọc từ ký hiệu hình vào `given_relations`; guard cách ly chúng — bề mặt không được nhắc lại chúng.
    const ban = c03CongKhai as unknown as Pick<ImageExtractionResponse, "extraction" | "assessment">;
    const s = docXong(phanHoi(ban.assessment, ban.extraction));
    const html = ve(s);

    const tieuDe = "Quan sát từ hình vẽ — chỉ để tham khảo, không dùng làm dữ kiện";
    const dau = html.indexOf(tieuDe);
    expect(dau).toBeGreaterThan(-1);
    const khoi = html.slice(dau, html.indexOf("</ul>", dau));
    expect(ban.extraction.diagram_observations).toHaveLength(7);
    for (const q of ban.extraction.diagram_observations) expect(khoi).toContain(q);

    expect(html).not.toContain("Công thức đã chuẩn hoá");
    for (const q of ["SA vuông góc với AC", "SA vuông góc với AB", "Góc BAC là góc vuông"]) expect(html).not.toContain(q);
    expect(html).toMatch(/role="alert"[^>]*>Ảnh chỉ có hình vẽ, không có đề bài bằng chữ\./);

    expect(html).toMatch(/<textarea[^>]*id="photo-problem-text"[^>]*><\/textarea>/);
    expect(nutDung(html)).toContain("disabled");
    const daTich = photoReducer(s, { type: "confirm", value: true });
    expect(nutDung(ve(daTich))).toContain("disabled");
    expect(photoReducer(daTich, { type: "build-start" }).phase).toBe("review");
  });

  it("KHÔNG mã kĩ thuật nào lọt lên bề mặt", () => {
    const html = ve(
      docXong(
        phanHoi({
          status: "rejected",
          rejection_code: "IMAGE_NOT_READABLE",
          review_flags: ["LOW_CONFIDENCE"],
          learner_message: "Chưa đọc được đề trong ảnh.",
          flag_messages: ["Máy đọc ảnh không chắc chắn về bản chép — em đọc lại toàn bộ."],
        }),
      ),
    );
    expect(html).not.toMatch(/IMAGE_NOT_READABLE|LOW_CONFIDENCE|rejection_code|review_flags/);
  });
});
