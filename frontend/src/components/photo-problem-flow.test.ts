import { describe, expect, it } from "vitest";
import type { ImageExtractionResponse, PhotoAssessment, PhotoExtraction } from "../llm/client";
import {
  PHOTO_MAX_BYTES,
  buildBlocker,
  buildFailureMessage,
  buildOutcome,
  canBuild,
  canRead,
  clientFileProblem,
  describeUncertainToken,
  initialPhotoState,
  needsConfirmation,
  nextRotation,
  photoReducer,
  photoStatusText,
  type PhotoAction,
  type PhotoState,
} from "./photo-problem-flow";

/**
 * Luồng ảnh đề bài — PHOTO_PROBLEM_TO_SCENE_END_TO_END §3/§6/§9 "Frontend".
 *
 * Vitest của kho chạy môi trường `node` (không DOM), nên hành vi tương tác được
 * khoá ở TẦNG TRẠNG THÁI: chọn/xoay/xoá/thay ảnh, chống bấm lặp, bỏ phản hồi cũ,
 * sửa nội dung, xác nhận, dựng. `ProblemInput.tsx` chỉ nối các action này.
 */

const ANH = { name: "de.jpg", type: "image/jpeg", size: 120_000 };
const ANH_KHAC = { name: "de-2.png", type: "image/png", size: 90_000 };
const DE = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2. Tính thể tích khối chóp.";

function phanHoi(
  danhGia: Partial<PhotoAssessment> = {},
  trich: Partial<PhotoExtraction> = {},
): ImageExtractionResponse {
  return {
    status: "ok",
    extraction: {
      problem_text_verbatim: DE,
      problem_text_normalized: DE,
      math_expressions: [],
      named_points: ["S", "A", "B", "C", "D"],
      named_lines: [],
      named_planes: [],
      named_solids: ["S.ABCD"],
      given_relations: [],
      has_diagram: false,
      diagram_observations: [],
      text_diagram_conflicts: [],
      uncertain_tokens: [],
      missing_regions: [],
      confidence: 0.93,
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
      sha256: "a".repeat(64),
      width: 800,
      height: 600,
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

function dangDoc(): PhotoState {
  return chay({ type: "select", file: ANH }, { type: "read-start" });
}

function docXong(res = phanHoi()): PhotoState {
  const s = dangDoc();
  return photoReducer(s, { type: "read-success", requestId: s.requestId, response: res });
}

describe("chọn · xoay · xoá · thay ảnh", () => {
  it("chọn ảnh ⇒ `selected`, chưa xoay, đọc được", () => {
    const s = chay({ type: "select", file: ANH });
    expect(s.phase).toBe("selected");
    expect(s.rotation).toBe(0);
    expect(canRead(s)).toBe(true);
  });

  it("xoay đủ một vòng 90° → 180° → 270° → 0°", () => {
    expect([nextRotation(0), nextRotation(90), nextRotation(180), nextRotation(270)]).toEqual([
      90, 180, 270, 0,
    ]);
  });

  it("xoay sau khi đã đọc ⇒ bỏ bản trích xuất (nó thuộc ảnh ở góc cũ)", () => {
    const s = photoReducer(docXong(), { type: "rotate" });
    expect(s.phase).toBe("selected");
    expect(s.rotation).toBe(90);
    expect(s.response).toBeNull();
    expect(s.text).toBe("");
  });

  it("xoá ảnh ⇒ về trạng thái rỗng", () => {
    const s = photoReducer(docXong(), { type: "remove" });
    expect(s.phase).toBe("empty");
    expect(s.file).toBeNull();
  });
});

describe("chống gửi lặp và phản hồi cũ", () => {
  it("bấm “Đọc” lần hai khi đang đọc là NO-OP — không gửi ảnh lần hai", () => {
    const s = dangDoc();
    expect(photoReducer(s, { type: "read-start" })).toBe(s);
    expect(canRead(s)).toBe(false);
  });

  it("THAY ảnh giữa lúc đọc ⇒ phản hồi của ảnh cũ bị BỎ", () => {
    const s = dangDoc();
    const idCu = s.requestId;
    const thay = photoReducer(s, { type: "select", file: ANH_KHAC });
    const sau = photoReducer(thay, { type: "read-success", requestId: idCu, response: phanHoi() });
    expect(sau).toBe(thay);
    expect(sau.file).toBe(ANH_KHAC);
    expect(sau.response).toBeNull();
  });

  it("XOAY giữa lúc đọc ⇒ phản hồi cho góc cũ bị BỎ", () => {
    const s = dangDoc();
    const xoay = photoReducer(s, { type: "rotate" });
    expect(photoReducer(xoay, { type: "read-success", requestId: s.requestId, response: phanHoi() })).toBe(xoay);
  });

  it("XOÁ giữa lúc đọc ⇒ lỗi về muộn cũng bị bỏ", () => {
    const s = dangDoc();
    const xoa = photoReducer(s, { type: "remove" });
    expect(photoReducer(xoa, { type: "read-failure", requestId: s.requestId, message: "x" })).toBe(xoa);
  });

  it("xoay rồi ĐỌC LẠI ⇒ phản hồi lượt TRƯỚC về muộn vẫn bị bỏ (khoá theo requestId, không chỉ theo phase)", () => {
    /* Ba ca trên đạt được chỉ nhờ `phase` đã rời `reading`. Chuỗi này thì
       `phase` QUAY LẠI `reading` trước khi phản hồi cũ về — chỉ `requestId`
       phân biệt được hai lượt. */
    const lan1 = dangDoc();
    const lan2 = photoReducer(photoReducer(lan1, { type: "rotate" }), { type: "read-start" });
    expect(lan2.phase).toBe("reading");
    expect(photoReducer(lan2, { type: "read-success", requestId: lan1.requestId, response: phanHoi() })).toBe(lan2);
    expect(photoReducer(lan2, { type: "read-failure", requestId: lan1.requestId, message: "cũ" })).toBe(lan2);
    const dung = photoReducer(lan2, { type: "read-success", requestId: lan2.requestId, response: phanHoi() });
    expect(dung.phase).toBe("review");
    expect(dung.rotation).toBe(90);
  });

  it("bấm “Dựng” lần hai khi đang dựng là NO-OP", () => {
    const s = photoReducer(docXong(), { type: "build-start" });
    expect(s.phase).toBe("building");
    expect(photoReducer(s, { type: "build-start" })).toBe(s);
    expect(photoReducer(s, { type: "remove" })).toBe(s);
    expect(photoReducer(s, { type: "rotate" })).toBe(s);
  });
});

describe("đọc ảnh: đang đọc · lỗi · thành công", () => {
  it("lỗi đọc ⇒ `error` kèm lời nhắn, và ĐỌC LẠI được", () => {
    const s = dangDoc();
    const loi = photoReducer(s, { type: "read-failure", requestId: s.requestId, message: "Mất kết nối." });
    expect(loi.phase).toBe("error");
    expect(loi.error).toBe("Mất kết nối.");
    expect(canRead(loi)).toBe(true);
  });

  it("lời nhắn rỗng ⇒ không dựng băng lỗi rỗng", () => {
    const s = dangDoc();
    expect(photoReducer(s, { type: "read-failure", requestId: s.requestId, message: "" }).error).toBeNull();
  });

  it("đọc xong ⇒ ô nội dung ĐIỀN SẴN văn bản do máy chủ chọn; dựng được khi không có cờ", () => {
    const s = docXong();
    expect(s.phase).toBe("review");
    expect(s.text).toBe(DE);
    expect(needsConfirmation(s)).toBe(false);
    expect(canBuild(s)).toBe(true);
  });
});

describe("xem lại · sửa · xác nhận (§6)", () => {
  it("có chỗ đọc chưa chắc ⇒ CHẶN dựng tới khi người học xác nhận", () => {
    const s = docXong(phanHoi({ requires_confirmation: true, review_flags: ["UNCERTAIN_TOKENS"] }));
    expect(canBuild(s)).toBe(false);
    expect(buildBlocker(s)).toMatch(/xác nhận/);
    expect(canBuild(photoReducer(s, { type: "confirm", value: true }))).toBe(true);
  });

  it("bị TỪ CHỐI ⇒ vẫn giữ ảnh, cho sửa; dựng chỉ khi đủ dài VÀ đã xác nhận", () => {
    let s = docXong(
      phanHoi({ status: "rejected", rejection_code: "MISSING_PROBLEM_TEXT", requires_confirmation: true, problem_text: "" }),
    );
    expect(s.file).toBe(ANH);
    expect(canBuild(s)).toBe(false);
    s = photoReducer(s, { type: "edit", text: DE });
    expect(canBuild(s)).toBe(false);
    s = photoReducer(s, { type: "confirm", value: true });
    expect(canBuild(s)).toBe(true);
  });

  it("nội dung quá ngắn ⇒ chặn", () => {
    const s = photoReducer(docXong(), { type: "edit", text: "  ngắn  " });
    expect(buildBlocker(s)).toMatch(/quá ngắn/);
  });

  it("sửa/xác nhận khi CHƯA có bản trích xuất bị bỏ qua", () => {
    const s = chay({ type: "select", file: ANH });
    expect(photoReducer(s, { type: "edit", text: DE })).toBe(s);
    expect(photoReducer(s, { type: "confirm", value: true })).toBe(s);
    expect(photoReducer(s, { type: "build-start" })).toBe(s);
  });

  it("dựng không thành ⇒ quay về xem lại, GIỮ ảnh và nội dung đã sửa", () => {
    let s = photoReducer(docXong(), { type: "edit", text: DE + " Sửa thêm." });
    s = photoReducer(s, { type: "build-start" });
    s = photoReducer(s, { type: "build-failure", message: "Đề chưa đủ dữ kiện." });
    expect(s.phase).toBe("review");
    expect(s.file).toBe(ANH);
    expect(s.text).toBe(DE + " Sửa thêm.");
    expect(s.error).toBe("Đề chưa đủ dữ kiện.");
  });

  it("dựng xong ⇒ `build-end` trả về xem lại (component rời trang khi mô phỏng mở)", () => {
    const s = photoReducer(photoReducer(docXong(), { type: "build-start" }), { type: "build-end" });
    expect(s.phase).toBe("review");
  });
});

describe("kết quả dựng từ văn bản đã xác nhận", () => {
  it("thiếu dữ kiện được gọi đúng tên, lỗi khác là chưa hỗ trợ", () => {
    expect(buildOutcome({ status: "ok" })).toBe("OK");
    expect(buildOutcome({ status: "unsupported", failure_category: "insufficient_specification" })).toBe(
      "INSUFFICIENT_GEOMETRIC_CONSTRAINTS",
    );
    expect(buildOutcome({ status: "unsupported", failure_category: "semantic_incomplete" })).toBe(
      "INSUFFICIENT_GEOMETRIC_CONSTRAINTS",
    );
    expect(buildOutcome({ status: "unsupported", failure_category: "out_of_scope" })).toBe("UNSUPPORTED_PROBLEM");
  });

  it("lời báo dùng learner_reason, KHÔNG lộ loại/mã lỗi", () => {
    const m = buildFailureMessage({
      status: "unsupported",
      failure_category: "insufficient_specification",
      learner_reason: "Đề chưa cho độ dài cạnh đáy.",
    });
    expect(m).toContain("Đề chưa cho độ dài cạnh đáy.");
    expect(m).not.toMatch(/insufficient|failure_category|[A-Z]{3,}_[A-Z_]+/);
  });
});

describe("chuỗi hiển thị cho người học", () => {
  it("trần kích thước phía trình duyệt", () => {
    expect(clientFileProblem(ANH)).toBeNull();
    expect(clientFileProblem({ ...ANH, size: 0 })).toMatch(/rỗng/);
    expect(clientFileProblem({ ...ANH, size: PHOTO_MAX_BYTES + 1 })).toMatch(/quá lớn/);
  });

  it("chỗ đọc chưa chắc được nói bằng lời", () => {
    expect(describeUncertainToken({ token: "0", alternatives: ["O"], location: "tâm O(0;0;0)", reason: "mờ" })).toBe(
      "“0” có thể là “O” — ở “tâm O(0;0;0)”",
    );
  });

  it("KHÔNG chuỗi nào lộ định danh kĩ thuật", () => {
    const chuoi = [
      photoStatusText(chay({ type: "select", file: ANH })),
      photoStatusText(dangDoc()),
      photoStatusText(docXong()),
      photoStatusText(docXong(phanHoi({ status: "rejected", rejection_code: "IMAGE_NOT_READABLE" }))),
      photoStatusText(photoReducer(docXong(), { type: "build-start" })),
      buildBlocker(chay({ type: "select", file: ANH })),
      buildBlocker(photoReducer(docXong(), { type: "edit", text: "" })),
      buildBlocker(docXong(phanHoi({ requires_confirmation: true }))),
      buildFailureMessage({ status: "unsupported" }),
    ];
    for (const c of chuoi) {
      expect(c).toBeTruthy();
      expect(c).not.toMatch(/[A-Z]{3,}_[A-Z_]+|rejection_code|review_flags/);
    }
  });
});
