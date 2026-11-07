import { describe, expect, it } from "vitest";
import { AxoClientError, type ImageExtractionResponse, type PhotoAssessment, type PhotoExtraction } from "../llm/client";
import {
  PHOTO_MAX_BYTES,
  acceptBlocker,
  canAccept,
  canRead,
  clientFileProblem,
  describeUncertainToken,
  initialPhotoState,
  needsConfirmation,
  needsReplaceConfirmation,
  nextRotation,
  photoReadErrorMessage,
  photoReducer,
  photoStatusText,
  type PhotoAction,
  type PhotoState,
  type PhotoUpload,
} from "./photo-problem-flow";

/**
 * Luồng ảnh đề bài — PHOTO_PROBLEM_TO_SCENE_END_TO_END §3/§6 + run `image-capture-crop-extraction`.
 *
 * Vitest của kho chạy môi trường `node` (không DOM), nên hành vi tương tác được khoá ở TẦNG TRẠNG THÁI: chọn ảnh
 * không tự đọc, khoanh vùng/xoay, chuẩn bị ảnh gửi, chống bấm lặp, bỏ phản hồi cũ, huỷ, sửa, xác nhận, đưa vào ô
 * nhập. `ProblemInput.tsx` + `PhotoProblemDialog.tsx` chỉ nối các action này.
 */

const ANH = { name: "de.jpg", type: "image/jpeg", size: 120_000 };
const ANH_KHAC = { name: "de-2.png", type: "image/png", size: 90_000 };
const VUNG: PhotoUpload = { file: { name: "de-vung-chon.jpg", type: "image/jpeg", size: 40_000 }, rotation: 0, cropped: true };
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
const chuanBi = (upload: PhotoUpload = VUNG) =>
  chay({ type: "select", file: ANH }, { type: "prepare", upload });

function dangDoc(): PhotoState {
  return photoReducer(chuanBi(), { type: "read-start" });
}

function docXong(res = phanHoi()): PhotoState {
  const s = dangDoc();
  return photoReducer(s, { type: "read-success", requestId: s.requestId, response: res });
}

describe("chọn · khoanh vùng · xoay · chuẩn bị ảnh gửi", () => {
  it("chọn ảnh ⇒ `selected` (màn chỉnh ảnh); CHƯA đọc được — chọn ảnh không bao giờ tự đọc", () => {
    const s = chay({ type: "select", file: ANH });
    expect(s.phase).toBe("selected");
    expect(s.rotation).toBe(0);
    expect(s.upload).toBeNull();
    expect(canRead(s)).toBe(false);
    expect(photoReducer(s, { type: "read-start" })).toBe(s);
  });

  it("xoay trái/phải đủ vòng", () => {
    expect([nextRotation(0), nextRotation(90), nextRotation(180), nextRotation(270)]).toEqual([90, 180, 270, 0]);
    let s = chay({ type: "select", file: ANH });
    s = photoReducer(s, { type: "rotate", direction: "left" });
    expect(s.rotation).toBe(270);
    s = photoReducer(photoReducer(s, { type: "rotate", direction: "right" }), { type: "rotate" });
    expect(s.rotation).toBe(90);
  });

  it("chuẩn bị ảnh (cắt hoặc giữ nguyên) ⇒ `prepared`, đọc được; chỉ từ màn chỉnh ảnh", () => {
    const s = chuanBi();
    expect(s.phase).toBe("prepared");
    expect(s.upload).toEqual(VUNG);
    expect(canRead(s)).toBe(true);
    expect(photoReducer(initialPhotoState, { type: "prepare", upload: VUNG })).toBe(initialPhotoState);
    expect(photoReducer(s, { type: "rotate" })).toBe(s);           // xoay chỉ ở màn chỉnh ảnh
  });

  it("giữ nguyên ảnh đã xoay ⇒ gửi tệp GỐC kèm góc xoay cho máy chủ", () => {
    const s = chay({ type: "select", file: ANH }, { type: "rotate" },
      { type: "prepare", upload: { file: ANH, rotation: 90, cropped: false } });
    expect(s.upload).toEqual({ file: ANH, rotation: 90, cropped: false });
  });

  it("chỉnh lại ảnh (từ ảnh sẽ gửi / lỗi / xem lại) ⇒ về màn chỉnh, GIỮ ảnh gốc + góc xoay, bỏ ảnh gửi và bản đọc", () => {
    for (const s of [chuanBi(), docXong()]) {
      const lai = photoReducer(s, { type: "edit-image" });
      expect(lai.phase).toBe("selected");
      expect(lai.file).toBe(ANH);
      expect(lai.upload).toBeNull();
      expect(lai.response).toBeNull();
      expect(lai.text).toBe("");
    }
    expect(photoReducer(dangDoc(), { type: "edit-image" }).phase).toBe("reading");   // đang đọc: phải huỷ trước
  });

  it("ảnh không giải mã được / quá nhiều điểm ảnh ⇒ `error`, bỏ ảnh; không đọc được", () => {
    const s = photoReducer(chay({ type: "select", file: ANH }), { type: "image-invalid", message: "Ảnh có quá nhiều điểm ảnh." });
    expect(s.phase).toBe("error");
    expect(s.file).toBeNull();
    expect(s.error).toMatch(/điểm ảnh/);
    expect(canRead(s)).toBe(false);
  });

  it("xoá ảnh ⇒ về trạng thái rỗng", () => {
    const s = photoReducer(docXong(), { type: "remove" });
    expect(s.phase).toBe("empty");
    expect(s.file).toBeNull();
    expect(s.upload).toBeNull();
  });
});

describe("chống gửi lặp, phản hồi cũ, huỷ", () => {
  it("bấm “Đọc” lần hai khi đang đọc là NO-OP — không gửi ảnh lần hai", () => {
    const s = dangDoc();
    expect(photoReducer(s, { type: "read-start" })).toBe(s);
    expect(canRead(s)).toBe(false);
  });

  it("THAY ảnh giữa lúc đọc ⇒ phản hồi của ảnh cũ bị BỎ", () => {
    const s = dangDoc();
    const thay = photoReducer(s, { type: "select", file: ANH_KHAC });
    const sau = photoReducer(thay, { type: "read-success", requestId: s.requestId, response: phanHoi() });
    expect(sau).toBe(thay);
    expect(sau.file).toBe(ANH_KHAC);
    expect(sau.response).toBeNull();
  });

  it("HUỶ đọc ⇒ về ảnh sẽ gửi; phản hồi/lỗi về muộn của lượt đã huỷ bị BỎ", () => {
    const s = dangDoc();
    const huy = photoReducer(s, { type: "read-cancel" });
    expect(huy.phase).toBe("prepared");
    expect(canRead(huy)).toBe(true);
    expect(photoReducer(huy, { type: "read-success", requestId: s.requestId, response: phanHoi() })).toBe(huy);
    expect(photoReducer(huy, { type: "read-failure", requestId: s.requestId, message: "x" })).toBe(huy);
  });

  it("XOÁ (đóng hộp thoại) giữa lúc đọc ⇒ lỗi về muộn cũng bị bỏ", () => {
    const s = dangDoc();
    const xoa = photoReducer(s, { type: "remove" });
    expect(photoReducer(xoa, { type: "read-failure", requestId: s.requestId, message: "x" })).toBe(xoa);
  });

  it("khoanh lại rồi ĐỌC LẠI ⇒ phản hồi lượt TRƯỚC về muộn vẫn bị bỏ (khoá theo requestId, không chỉ theo phase)", () => {
    /* `phase` QUAY LẠI `reading` trước khi phản hồi cũ về — chỉ `requestId` phân biệt được hai lượt. */
    const lan1 = dangDoc();
    let lan2 = photoReducer(photoReducer(lan1, { type: "read-cancel" }), { type: "edit-image" });
    lan2 = photoReducer(photoReducer(lan2, { type: "prepare", upload: VUNG }), { type: "read-start" });
    expect(lan2.phase).toBe("reading");
    expect(photoReducer(lan2, { type: "read-success", requestId: lan1.requestId, response: phanHoi() })).toBe(lan2);
    expect(photoReducer(lan2, { type: "read-failure", requestId: lan1.requestId, message: "cũ" })).toBe(lan2);
    expect(photoReducer(lan2, { type: "read-success", requestId: lan2.requestId, response: phanHoi() }).phase).toBe("review");
  });
});

describe("đọc ảnh: đang đọc · lỗi · thành công", () => {
  it("lỗi đọc ⇒ `error` kèm lời nhắn, GIỮ ảnh gửi và ĐỌC LẠI được", () => {
    const s = dangDoc();
    const loi = photoReducer(s, { type: "read-failure", requestId: s.requestId, message: "Mất kết nối." });
    expect(loi.phase).toBe("error");
    expect(loi.error).toBe("Mất kết nối.");
    expect(loi.upload).toEqual(VUNG);
    expect(canRead(loi)).toBe(true);
  });

  it("lời nhắn rỗng ⇒ không dựng băng lỗi rỗng", () => {
    const s = dangDoc();
    expect(photoReducer(s, { type: "read-failure", requestId: s.requestId, message: "" }).error).toBeNull();
  });

  it("đọc xong ⇒ ô nội dung ĐIỀN SẴN văn bản do máy chủ chọn; dùng được khi không có cờ", () => {
    const s = docXong();
    expect(s.phase).toBe("review");
    expect(s.text).toBe(DE);
    expect(needsConfirmation(s)).toBe(false);
    expect(canAccept(s)).toBe(true);
  });
});

describe("xem lại · sửa · xác nhận · đưa vào ô nhập (§6)", () => {
  it("có chỗ đọc chưa chắc ⇒ CHẶN tới khi người học xác nhận", () => {
    const s = docXong(phanHoi({ requires_confirmation: true, review_flags: ["UNCERTAIN_TOKENS"] }));
    expect(canAccept(s)).toBe(false);
    expect(acceptBlocker(s)).toMatch(/xác nhận/);
    expect(canAccept(photoReducer(s, { type: "confirm", value: true }))).toBe(true);
  });

  it("bị TỪ CHỐI ⇒ vẫn giữ ảnh, cho sửa; dùng chỉ khi đủ dài VÀ đã xác nhận", () => {
    let s = docXong(
      phanHoi({ status: "rejected", rejection_code: "MISSING_PROBLEM_TEXT", requires_confirmation: true, problem_text: "" }),
    );
    expect(s.file).toBe(ANH);
    expect(canAccept(s)).toBe(false);
    s = photoReducer(s, { type: "edit", text: DE });
    expect(canAccept(s)).toBe(false);
    s = photoReducer(s, { type: "confirm", value: true });
    expect(canAccept(s)).toBe(true);
  });

  it("văn bản sửa được, ký hiệu toán và xuống dòng giữ NGUYÊN — hệ không tự đổi quan hệ", () => {
    const sua = "Cho hình chóp S.ABC có SA ⊥ SB, AB ∥ CD, ∠SBA = 60°.\nTính √3·π, α, β, A′, a², a³.";
    const s = photoReducer(docXong(), { type: "edit", text: sua });
    expect(s.text).toBe(sua);
    expect(canAccept(s)).toBe(true);
  });

  it("nội dung quá ngắn ⇒ chặn", () => {
    expect(acceptBlocker(photoReducer(docXong(), { type: "edit", text: "  ngắn  " }))).toMatch(/quá ngắn/);
  });

  it("sửa/xác nhận khi CHƯA có bản trích xuất bị bỏ qua", () => {
    const s = chay({ type: "select", file: ANH });
    expect(photoReducer(s, { type: "edit", text: DE })).toBe(s);
    expect(photoReducer(s, { type: "confirm", value: true })).toBe(s);
    expect(canAccept(s)).toBe(false);
  });

  it("ô nhập đang có nội dung KHÁC ⇒ hỏi trước khi thay; rỗng hoặc trùng ⇒ không hỏi", () => {
    expect(needsReplaceConfirmation("", DE)).toBe(false);
    expect(needsReplaceConfirmation("   ", DE)).toBe(false);
    expect(needsReplaceConfirmation(` ${DE} `, DE)).toBe(false);
    expect(needsReplaceConfirmation("Cho hình lập phương cạnh 3.", DE)).toBe(true);
  });
});

describe("lỗi đọc ảnh → lời cho người học", () => {
  const http = (status: number, message: string, reasonCode?: string) =>
    new AxoClientError({ kind: "http", code: "SERVICE_UNAVAILABLE", status, message, reasonCode });

  it("huỷ chủ động ⇒ im lặng", () => {
    expect(photoReadErrorMessage(Object.assign(new Error("x"), { name: "AbortError" }))).toBeNull();
  });

  it("công tắc dừng LIVE_AI_DISABLED và thiếu khoá ⇒ lời người học, KHÔNG nhắc tên cấu hình kĩ thuật", () => {
    const tat = photoReadErrorMessage(http(503, "… (ALLOW_LIVE_AI=0).", "LIVE_AI_DISABLED"))!;
    const khoa = photoReadErrorMessage(http(503, "Máy chủ chưa cấu hình GEMINI_API_KEY. Tạo file …"))!;
    for (const m of [tat, khoa]) {
      expect(m).toMatch(/gõ đề vào ô nhập/);
      expect(m).not.toMatch(/ALLOW_LIVE_AI|GEMINI|API|_KEY/);
    }
  });

  it("lỗi ảnh/provider có lời tiếng Việt của máy chủ ⇒ giữ lời ấy", () => {
    expect(photoReadErrorMessage(http(400, "Ảnh quá lớn (tối đa 10MB).", "IMAGE_TOO_LARGE"))).toBe("Ảnh quá lớn (tối đa 10MB).");
    expect(photoReadErrorMessage(http(503, "Dịch vụ đọc ảnh đang bận hoặc mất kết nối.", "VISION_UNAVAILABLE")))
      .toBe("Dịch vụ đọc ảnh đang bận hoặc mất kết nối.");
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
      photoStatusText(chuanBi()),
      photoStatusText(chuanBi({ file: ANH, rotation: 90, cropped: false })),
      photoStatusText(dangDoc()),
      photoStatusText(docXong()),
      photoStatusText(docXong(phanHoi({ status: "rejected", rejection_code: "IMAGE_NOT_READABLE" }))),
      acceptBlocker(chay({ type: "select", file: ANH })),
      acceptBlocker(photoReducer(docXong(), { type: "edit", text: "" })),
      acceptBlocker(docXong(phanHoi({ requires_confirmation: true }))),
    ];
    for (const c of chuoi) {
      expect(c).toBeTruthy();
      expect(c).not.toMatch(/[A-Z]{3,}_[A-Z_]+|rejection_code|review_flags/);
    }
  });
});
