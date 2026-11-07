import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import type { ImageExtractionResponse, PhotoAssessment, PhotoExtraction } from "../llm/client";
import {
  buildCameraConstraints,
  cameraErrorMessage,
  cameraSupport,
  canSwitchCamera,
  fallbackCameraConstraints,
  initialCameraTarget,
  isMobileCameraPreferred,
  nextCameraTarget,
} from "./PhotoCameraView";
import { PhotoProblemDialog, type PhotoProblemDialogProps } from "./PhotoProblemDialog";
import { ProblemInput } from "./ProblemInput";
import {
  initialPhotoState,
  photoReducer,
  type PhotoAction,
  type PhotoState,
  type PhotoUpload,
} from "./photo-problem-flow";
import c03CongKhai from "./photo-c03-diagram-only.fixture.json";

/**
 * Bề mặt ảnh đề bài — PHOTO_PROBLEM_TO_SCENE_END_TO_END §3/§9 + run `image-capture-crop-extraction`.
 *
 * `renderToString` không chạy effect (không mở máy ảnh, không giải mã ảnh), nên đây khoá MARKUP của từng màn hộp
 * thoại: mở thẳng màn máy ảnh (không có hộp thoại chọn trung gian), đủ nút có nhãn, vùng trạng thái, chuỗi từ ảnh bị
 * thoát ký tự, không mã kĩ thuật nào lọt ra. Các hàm chọn ràng buộc / đổi camera được khoá trực tiếp bằng unit test.
 */

const DE = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2. Tính thể tích khối chóp.";
const ANH = { name: "de.jpg", type: "image/jpeg", size: 120_000 };
const VUNG: PhotoUpload = { file: { name: "de-vung-chon.jpg", type: "image/jpeg", size: 40_000 }, rotation: 0, cropped: true };
const noop = () => {};
const XU_LY: Omit<PhotoProblemDialogProps, "open" | "state" | "composerText"> = {
  onClose: noop,
  onPickFile: noop,
  onNativeCamera: noop,
  onCaptured: noop,
  onChangeImage: noop,
  onRotate: noop,
  onPrepare: noop,
  onInvalid: noop,
  onEditImage: noop,
  onRead: noop,
  onCancelRead: noop,
  onEdit: noop,
  onConfirm: noop,
  onAccept: noop,
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
const chuanBi = (upload = VUNG) => chay({ type: "select", file: ANH }, { type: "prepare", upload });

function docXong(res: ImageExtractionResponse): PhotoState {
  const s = photoReducer(chuanBi(), { type: "read-start" });
  return photoReducer(s, { type: "read-success", requestId: s.requestId, response: res });
}

const ve = (s: PhotoState, open = true, composerText = "") =>
  renderToString(<PhotoProblemDialog open={open} state={s} composerText={composerText} {...XU_LY} />).replace(/<!-- -->/g, "");

const nut = (html: string, chu: string) => {
  for (const m of html.matchAll(/<button\b[^>]*>([\s\S]*?)<\/button>/g)) {
    const text = m[1]!.replace(/<[^>]+>/g, "").trim();
    if (text === chu) return m[0];
  }
  return "";
};

describe("ô nhập đề — lối vào camera-first, luồng gõ tay còn nguyên", () => {
  const html = renderToString(<ProblemInput />);

  it("menu + có mục “Chụp ảnh đề bài” mở thẳng hộp thoại máy ảnh (không mở máy ảnh lúc tải trang)", () => {
    expect(html).toContain("Chụp ảnh đề bài");
    expect(html).toMatch(/id="menu-item-camera"[^>]*aria-haspopup="dialog"/);
    expect(html).not.toContain("Chụp hoặc chọn ảnh đề bài");
    expect(html).toContain('aria-label="Tải ảnh đề bài từ máy"');
    expect(html).not.toContain("photo-dialog");
    expect(html).not.toContain("<video");
  });

  it("input chụp ảnh dự phòng gợi ý máy ảnh sau; cả hai chỉ nhận PNG/JPEG/WEBP", () => {
    expect(html).toContain('capture="environment"');
    expect(html.match(/accept="image\/png,image\/jpeg,image\/webp"/g)?.length).toBe(2);
  });

  it("luồng gõ tay KHÔNG đổi: ô nhập, nút gửi, nút + vẫn ở đó", () => {
    expect(html).toContain('placeholder="Nhập đề toán hình học không gian..."');
    expect(html).toContain('aria-label="Phân tích đề bằng AI"');
    expect(html).toContain('aria-label="Tải tệp đề"');
  });
});

describe("máy ảnh trực tiếp — ràng buộc desktop/mobile, đổi camera, fallback", () => {
  it("nhận diện thiết bị theo năng lực & UA, không dựa vào bề rộng màn hình", () => {
    // Laptop cảm ứng trên Windows (userAgentData.mobile = false) vẫn là desktop webcam mặc định
    expect(
      isMobileCameraPreferred({
        userAgentDataMobile: false,
        userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        maxTouchPoints: 10,
        anyCoarsePointer: true,
      }),
    ).toBe(false);

    // Điện thoại báo userAgentData.mobile = true hoặc UA di động / cảm ứng thô ⇒ ưu tiên camera sau
    expect(isMobileCameraPreferred({ userAgentDataMobile: true })).toBe(true);
    expect(
      isMobileCameraPreferred({
        userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
        maxTouchPoints: 5,
        anyCoarsePointer: true,
      }),
    ).toBe(true);
  });

  it("desktop ưu tiên webcam mặc định; mobile ưu tiên facingMode environment không khoá cứng deviceId", () => {
    const desktop = buildCameraConstraints(initialCameraTarget(false));
    expect(desktop).toEqual({
      video: { width: { ideal: 2560 }, height: { ideal: 1920 } },
      audio: false,
    });
    expect(JSON.stringify(desktop)).not.toContain("facingMode");
    expect(JSON.stringify(desktop)).not.toContain("deviceId");

    const mobile = buildCameraConstraints(initialCameraTarget(true));
    expect(mobile).toEqual({
      video: { facingMode: { ideal: "environment" }, width: { ideal: 2560 }, height: { ideal: 1920 } },
      audio: false,
    });
  });

  it("camera sau hoặc deviceId không khả dụng ⇒ fallback sang bất kỳ camera nào khả dụng", () => {
    const overconstrained = { name: "OverconstrainedError" };
    const notFound = { name: "NotFoundError" };
    const denied = { name: "NotAllowedError" };

    expect(fallbackCameraConstraints(overconstrained, { kind: "facing", facing: "environment" })).toEqual({
      video: { width: { ideal: 2560 }, height: { ideal: 1920 } },
      audio: false,
    });
    expect(fallbackCameraConstraints(notFound, { kind: "device", deviceId: "cam-usb" })).toEqual({
      video: { width: { ideal: 2560 }, height: { ideal: 1920 } },
      audio: false,
    });
    expect(fallbackCameraConstraints(overconstrained, { kind: "default" })).toEqual({
      video: true,
      audio: false,
    });
    // Từ chối quyền KHÔNG được tự thử vượt qua lời nhắc trình duyệt
    expect(fallbackCameraConstraints(denied, { kind: "facing", facing: "environment" })).toBeNull();
  });

  it("đổi máy ảnh: xoay vòng khi nhiều webcam, lật trước/sau trên di động", () => {
    expect(canSwitchCamera(["cam-1"], false)).toBe(false);
    expect(canSwitchCamera(["cam-1", "cam-2"], false)).toBe(true);
    expect(canSwitchCamera(["cam-1"], true)).toBe(true);

    const t1 = nextCameraTarget({ kind: "default" }, "cam-1", ["cam-1", "cam-2", "cam-3"], false);
    expect(t1).toEqual({ kind: "device", deviceId: "cam-2" });
    const t2 = nextCameraTarget(t1, "cam-2", ["cam-1", "cam-2", "cam-3"], false);
    expect(t2).toEqual({ kind: "device", deviceId: "cam-3" });
    const t3 = nextCameraTarget(t2, "cam-3", ["cam-1", "cam-2", "cam-3"], false);
    expect(t3).toEqual({ kind: "device", deviceId: "cam-1" });

    // Di động chỉ lộ 1 deviceId ẩn danh vẫn đổi được giữa environment ↔ user
    const m1 = nextCameraTarget({ kind: "facing", facing: "environment" }, "", ["anon"], true);
    expect(m1).toEqual({ kind: "facing", facing: "user" });
    const m2 = nextCameraTarget(m1, "", ["anon"], true);
    expect(m2).toEqual({ kind: "facing", facing: "environment" });
  });

  it("kiểm hỗ trợ và thông báo lỗi máy ảnh ngắn gọn, hướng dẫn chọn ảnh từ máy", () => {
    expect(cameraSupport({ isSecureContext: true, hasGetUserMedia: true })).toEqual({ ok: true });
    expect(cameraSupport({ isSecureContext: false, hasGetUserMedia: true }).ok).toBe(false);
    expect(cameraSupport({ isSecureContext: true, hasGetUserMedia: false }).ok).toBe(false);

    expect(cameraErrorMessage({ name: "NotAllowedError" })).toMatch(/cấp quyền máy ảnh|chọn ảnh từ máy/);
    expect(cameraErrorMessage({ name: "NotFoundError" })).toMatch(/Không tìm thấy máy ảnh.*chọn ảnh từ máy/);
    expect(cameraErrorMessage({ name: "NotReadableError" })).toMatch(/bận.*chọn ảnh từ máy/);
  });
});

describe("hộp thoại ảnh — từng màn", () => {
  it("đóng ⇒ không dựng gì", () => {
    expect(ve(initialPhotoState, false)).toBe("");
  });

  it("MỞ ĐẦU = MÀN MÁY ẢNH TRỰC TIẾP: không còn màn lựa chọn trung gian, có khung ngắm, nút chụp và chọn ảnh có sẵn", () => {
    const html = ve(initialPhotoState);
    expect(html).toMatch(/role="dialog"[^>]*aria-modal="true"[^>]*aria-labelledby="photo-dialog-title"/);
    expect(html).toContain('data-photo-screen="camera"');
    expect(html).toContain(">Chụp ảnh đề bài<");
    expect(html).not.toContain("Chụp hoặc chọn ảnh đề bài");
    expect(html).not.toContain("Chụp bằng máy ảnh");
    expect(nut(html, "Chọn ảnh có sẵn")).toBeTruthy();
    expect(nut(html, "Chụp ảnh") || html.includes(">Chụp ảnh<") || html.includes("Chọn ảnh từ máy")).toBeTruthy();
    expect(html).toContain('aria-label="Đóng hộp thoại ảnh đề bài"');
  });

  it("CHỈNH ẢNH: xoay trái/phải, đặt lại khung, đổi ảnh, giữ nguyên, cắt theo khung — chưa có nút đọc (chọn ảnh không tự đọc)", () => {
    const html = ve(chay({ type: "select", file: ANH }));
    expect(html).toContain(">Khoanh vùng đề bài<");
    for (const chu of ["Xoay trái", "Xoay phải", "Đặt lại khung", "Đổi ảnh", "Giữ nguyên ảnh", "Cắt theo khung"]) {
      expect(nut(html, chu)).toBeTruthy();
    }
    expect(html).not.toContain("Đọc đề trong ảnh");
  });

  it("ẢNH SẼ GỬI: xem trước + chỉnh lại + đọc, vùng trạng thái aria-live", () => {
    const html = ve(chuanBi());
    expect(html).toContain(">Ảnh sẽ gửi đi đọc<");
    expect(nut(html, "Chỉnh lại ảnh")).toBeTruthy();
    expect(nut(html, "Đọc đề trong ảnh")).not.toContain("disabled");
    expect(html).toMatch(/role="status"[^>]*aria-live="polite"/);
  });

  it("ĐANG ĐỌC: nút đọc khoá + báo bận, có nút huỷ, lời “Đang đọc nội dung đề bài…”", () => {
    const html = ve(photoReducer(chuanBi(), { type: "read-start" }));
    expect(html).toMatch(/<button[^>]*disabled=""[^>]*aria-busy="true"[^>]*>Đang đọc…<\/button>/);
    expect(nut(html, "Huỷ đọc")).toBeTruthy();
    expect(html).toContain("Đang đọc nội dung đề bài…");
  });

  it("XEM LẠI, không cờ: ô nội dung có nhãn, điền sẵn; “Dùng đề này” mở; có lối đối chiếu ảnh và tự nhập", () => {
    const html = ve(docXong(phanHoi()));
    expect(html).toContain('<label class="photo-label" for="photo-problem-text">');
    expect(html).toContain(DE);
    expect(html).not.toContain('type="checkbox"');
    expect(nut(html, "Dùng đề này")).not.toContain("disabled");
    expect(html).toContain("Xem ảnh đã đọc để đối chiếu");
    expect(nut(html, "Tự nhập đề")).toBeTruthy();
    expect(nut(html, "Chỉnh lại ảnh")).toBeTruthy();
  });

  it("XEM LẠI, có cờ: cảnh báo, chỗ không chắc, quan sát từ hình gắn nhãn tham khảo, phải xác nhận", () => {
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
    expect(html).toContain("a√3");
    expect(html).toContain('type="checkbox"');
    expect(nut(html, "Dùng đề này")).toContain("disabled");
    expect(html).toContain('id="photo-accept-hint"');
  });

  it("bị từ chối ⇒ lời báo tiếng Việt ở vùng role=alert", () => {
    const html = ve(docXong(phanHoi({
      status: "rejected", rejection_code: "MISSING_PROBLEM_TEXT", requires_confirmation: true, problem_text: "",
      learner_message: "Ảnh chỉ có hình vẽ, không có đề bài bằng chữ.",
    })));
    expect(html).toMatch(/role="alert"[^>]*>Ảnh chỉ có hình vẽ, không có đề bài bằng chữ\./);
  });

  it("chuỗi đọc từ ảnh bị THOÁT ký tự — không thành thẻ HTML", () => {
    const doc = '<img src=x onerror=alert(1)> Cho hình chóp S.ABC.';
    const html = ve(docXong(phanHoi({ problem_text: doc }, { problem_text_verbatim: doc })));
    expect(html).toContain("&lt;img src=x onerror=alert(1)&gt;");
    expect(html).not.toContain("<img src=x");
  });

  it("ảnh CHỈ CÓ HÌNH (C03 thật, bản công khai sau guard) ⇒ quan sát dưới nhãn tham khảo, ô trống, không dùng được", () => {
    const ban = c03CongKhai as unknown as Pick<ImageExtractionResponse, "extraction" | "assessment">;
    const s = docXong(phanHoi(ban.assessment, ban.extraction));
    const html = ve(s);
    const tieuDe = "Quan sát từ hình vẽ — chỉ để tham khảo, không dùng làm dữ kiện";
    const dau = html.indexOf(tieuDe);
    expect(dau).toBeGreaterThan(-1);
    const khoi = html.slice(dau, html.indexOf("</ul>", dau));
    for (const q of ban.extraction.diagram_observations) expect(khoi).toContain(q);
    for (const q of ["SA vuông góc với AC", "SA vuông góc với AB", "Góc BAC là góc vuông"]) expect(html).not.toContain(q);
    expect(html).toMatch(/<textarea[^>]*id="photo-problem-text"[^>]*><\/textarea>/);
    expect(nut(html, "Dùng đề này")).toContain("disabled");
    expect(nut(ve(photoReducer(s, { type: "confirm", value: true })), "Dùng đề này")).toContain("disabled");
  });

  it("LỖI đọc: lời ở role=alert, thử đọc lại / chỉnh lại / chụp ảnh khác / chọn ảnh từ máy", () => {
    const s = photoReducer(chuanBi(), { type: "read-start" });
    const html = ve(photoReducer(s, { type: "read-failure", requestId: s.requestId, message: "Dịch vụ đọc ảnh đang bận." }));
    expect(html).toMatch(/role="alert"[^>]*>Dịch vụ đọc ảnh đang bận\./);
    for (const chu of ["Thử đọc lại", "Chỉnh lại ảnh", "Chụp ảnh khác", "Chọn ảnh từ máy"]) expect(nut(html, chu)).toBeTruthy();
  });

  it("KHÔNG mã kĩ thuật nào lọt lên bề mặt", () => {
    const html = ve(docXong(phanHoi({
      status: "rejected", rejection_code: "IMAGE_NOT_READABLE", review_flags: ["LOW_CONFIDENCE"],
      learner_message: "Chưa đọc được đề trong ảnh.",
      flag_messages: ["Máy đọc ảnh không chắc chắn về bản chép — em đọc lại toàn bộ."],
    })));
    expect(html).not.toMatch(/IMAGE_NOT_READABLE|LOW_CONFIDENCE|rejection_code|review_flags/);
  });
});
