import { useEffect, useReducer, useRef, useState } from "react";
import { useAppStore } from "../state/store";
import { useAuthStore } from "../state/auth";
import { IconAttach, IconSend } from "./icons";
import {
  analyzeViaServer,
  extractImageViaServer,
  fetchHealth,
  type ServerHealth,
} from "../llm/client";
import {
  IMAGE_ACCEPT,
  acceptAttr,
  fileToPayload,
  imageMimeOf,
  isImageFile,
  kindFromFile,
  kindLabel,
  readAsBase64,
} from "../llm/input";
import { PhotoProblemPanel } from "./PhotoProblemPanel";
import {
  buildFailureMessage,
  canBuild,
  canRead,
  clientFileProblem,
  initialPhotoState,
  photoReducer,
} from "./photo-problem-flow";

/**
 * Nhập đề: gõ văn bản HOẶC tải tệp (.docx / .py / ảnh) — M4.
 * Mọi đầu vào chuẩn hóa thành InputPayload rồi gọi /api/analyze (một contract).
 * Việc gọi Gemini do backend đảm nhiệm (trình duyệt không giữ API key).
 *
 * M9-UX4 — MỘT DẠNG DUY NHẤT, và CHỈ SỐNG Ở TRANG CHỦ.
 * M9-UX3 từng tách hai vỏ hero/compact vì `InputPanel` (cột trái workspace) cũng
 * nhúng composer. M9-UX4 gỡ composer khỏi workspace — Trang chủ LÀ nơi phân tích
 * đề, giữ thêm một bản trong cột 270px là hai nơi làm cùng một việc. Vỏ "compact"
 * hết người dùng nên gỡ luôn, không nuôi code chết.
 *
 * M9-UX5 — HỘP nhiều dòng thay pill một dòng, nút `+` / gửi nằm ở ĐÁY hộp.
 * Hàng chip "thử đề mẫu AI" (`SAMPLE_PROMPTS`) đã GỠ: 3 đề đó trùng nội dung với
 * 3 bài mẫu ngay bên dưới Trang chủ, chỉ khác là tốn một lượt gọi API. Trang chủ
 * có ĐÚNG MỘT đường dùng AI: gõ đề của chính em. (`SAMPLE_PROMPTS` vẫn còn trong
 * `sim-samples.ts` cho dev/test — chỉ không quảng bá cho học sinh.)
 *
 * PHOTO_PROBLEM_TO_SCENE_END_TO_END (2026-09-13) — ẢNH ĐỀ BÀI CÓ BƯỚC XEM LẠI.
 * Ảnh (từ "Chụp ảnh", "Tải ảnh" hay nút `+`) KHÔNG còn gửi thẳng vào
 * `/api/analyze`: nó đi `/api/image/extract` → người học đọc lại, sửa, xác nhận
 * → "Dựng mô phỏng" gửi VĂN BẢN qua `analyzeViaServer`, đúng đường gõ tay. Luồng
 * gõ tay và `.docx` giữ nguyên. Luật trạng thái: `photo-problem-flow.ts`.
 */
export function ProblemInput() {
  const problemText = useAppStore((s) => s.problemText);
  const setProblemText = useAppStore((s) => s.setProblemText);
  const analyzing = useAppStore((s) => s.analyzing);
  const analysisError = useAppStore((s) => s.analysisError);
  const [health, setHealth] = useState<ServerHealth | null | "loading">("loading");
  const [file, setFile] = useState<File | null>(null);
  /* W5X — XEM TRƯỚC ẢNH ĐÃ DÁN.
     Dùng `URL.createObjectURL` chứ KHÔNG đọc thành `data:` URL: ảnh đề bài của
     học sinh có thể vài MB, mà `data:` sẽ nhét trọn base64 vào React state rồi
     vào cả DOM. `objectURL` chỉ là một con trỏ — nhưng nó GIỮ tệp trong bộ nhớ
     tới khi được thu hồi, nên phải `revokeObjectURL` khi đổi/bỏ tệp. Không thu
     hồi thì mỗi lần chọn lại một ảnh là rò thêm một tệp. */
  const [preview, setPreview] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);

  const [photo, dispatchPhoto] = useReducer(photoReducer, initialPhotoState);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const uploadImageRef = useRef<HTMLInputElement>(null);
  const cameraImageRef = useRef<HTMLInputElement>(null);
  /* Chốt ĐỒNG BỘ chống bấm lặp: `dispatch` chỉ đổi state ở lượt render sau, nên
     hai cú bấm trong cùng một khung vẫn thấy state cũ. Ref thì thấy ngay. */
  const readAbortRef = useRef<AbortController | null>(null);
  const buildingRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    fetchHealth().then((h) => {
      if (!cancelled) setHealth(h);
    });
    return () => {
      cancelled = true;
    };
  }, [analyzing]);

  const photoActive = photo.phase !== "empty";
  // Có tệp → gửi tệp; không thì gửi văn bản (≥10 ký tự). Ảnh có luồng riêng.
  const canAnalyze =
    !analyzing && !photoActive && (file !== null || problemText.trim().length >= 10);

  // Pill cao dần theo nội dung (tới ~6 dòng). DOM thuần, không state, không store.
/** Trần chiều cao ô nhập — MỘT nguồn, dùng cho cả JS lẫn CSS (`--composer-max`).
 *
 * W5V — trước đây có HAI trần cho cùng một hành vi: JS kẹp 148px còn CSS kẹp
 * 200px. Chữ vượt 148 là bị cuộn trong khi hộp vẫn còn chỗ, nên phần đầu đề bài
 * khuất đi mà nhìn thì tưởng ô chưa đầy. Hai con số cho một luật thì luôn có một
 * con số sai, và ở đây nó sai theo hướng giấu mất chữ người dùng vừa gõ. */
const COMPOSER_MAX_H = 320;

  function autoGrow(el: HTMLTextAreaElement) {
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, COMPOSER_MAX_H)}px`;
  }

  function onChangeText(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setProblemText(e.target.value);
    autoGrow(e.target);
  }

  // Enter = gửi, Shift+Enter = xuống dòng (quy ước quen thuộc của ô chat).
  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canAnalyze) void onAnalyze();
    }
  }

  function cancelRead() {
    readAbortRef.current?.abort();
    readAbortRef.current = null;
  }

  // Rời trang chủ giữa lúc đang đọc ⇒ huỷ, không để phản hồi về một component đã tháo.
  useEffect(() => () => readAbortRef.current?.abort(), []);

  function acceptImage(picked: File | null) {
    setFileError(null);
    if (!picked) return;
    if (!isImageFile(picked)) {
      setFileError("Chỉ nhận ảnh PNG, JPEG hoặc WEBP.");
      return;
    }
    const problem = clientFileProblem(picked);
    if (problem) {
      setFileError(problem);
      return;
    }
    cancelRead();
    setFile(null);
    dispatchPhoto({ type: "select", file: picked });
  }

  function onPickImage(e: React.ChangeEvent<HTMLInputElement>) {
    acceptImage(e.target.files?.[0] ?? null);
    // Xoá giá trị để chọn lại CÙNG một ảnh vẫn phát `onChange`.
    e.target.value = "";
  }

  function onPickFile(e: React.ChangeEvent<HTMLInputElement>) {
    setFileError(null);
    const picked = e.target.files?.[0] ?? null;
    if (!picked) return;
    if (isImageFile(picked)) {
      // Ảnh từ nút `+` cũng đi luồng có bước xem lại — không có đường thứ hai.
      acceptImage(picked);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }
    if (!kindFromFile(picked.name)) {
      setFileError(
        "Định dạng không hỗ trợ. Chọn .py, .docx hoặc ảnh .png/.jpg/.webp.",
      );
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }
    setFile(picked);
  }

  /* Sinh và THU HỒI ảnh xem trước theo vòng đời của `file`. Đặt trong `useEffect`
     chứ không trong `onPickFile`: tệp còn bị bỏ bằng `removeFile` và bị thay khi
     chọn tệp khác, nên nơi duy nhất thấy đủ mọi lối đổi là hiệu ứng theo `file`. */
  useEffect(() => {
    if (!file || kindFromFile(file.name) !== "image") {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  // Cùng luật W5X cho ảnh đề bài của luồng xem lại.
  useEffect(() => {
    const f = photo.file as File | null;
    if (!f) {
      setPhotoPreview(null);
      return;
    }
    const url = URL.createObjectURL(f);
    setPhotoPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [photo.file]);

  function removeFile() {
    setFile(null);
    setFileError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function onAnalyze() {
    const store = useAppStore.getState();
    store.setAnalysisError(null);
    store.setAnalyzing(true);
    try {
      const payload = file
        ? await fileToPayload(file)
        : { type: "text" as const, content: problemText.trim() };
      const result = await analyzeViaServer(payload);
      if (result.status === "ok") {
        // originalInput vào lịch sử: CHỈ text an toàn (tệp có thể là nhị phân
        // base64 — chính sách M9-UX1 cấm persist blob).
        store.loadEnvelope(result, undefined, file ? undefined : problemText.trim());
      } else {
        store.loadUnsupported(result);
      }
    } catch (err) {
      store.setAnalysisError(err instanceof Error ? err.message : String(err));
    } finally {
      store.setAnalyzing(false);
    }
  }

  async function onReadPhoto() {
    if (!canRead(photo) || readAbortRef.current) return;
    const picked = photo.file as File;
    const requestId = photo.requestId + 1;
    dispatchPhoto({ type: "read-start" });
    const ctl = new AbortController();
    readAbortRef.current = ctl;
    try {
      const content = await readAsBase64(picked);
      if (ctl.signal.aborted) return;
      const response = await extractImageViaServer(
        { content, mime_type: imageMimeOf(picked), filename: picked.name, rotation: photo.rotation },
        ctl.signal,
      );
      if (!ctl.signal.aborted) dispatchPhoto({ type: "read-success", requestId, response });
    } catch (err) {
      if (ctl.signal.aborted) return;
      const message = err instanceof Error ? err.message : String(err);
      if (/lượt mô phỏng thử/.test(message)) {
        // Hết lượt thử: dùng lại đúng thẻ mời đăng nhập bên dưới, không băng đỏ thứ hai.
        useAppStore.getState().setAnalysisError(message);
        dispatchPhoto({ type: "read-failure", requestId, message: "" });
      } else {
        dispatchPhoto({ type: "read-failure", requestId, message });
      }
    } finally {
      if (readAbortRef.current === ctl) readAbortRef.current = null;
    }
  }

  async function onBuildPhoto() {
    if (!canBuild(photo) || buildingRef.current) return;
    buildingRef.current = true;
    const text = photo.text.trim();
    dispatchPhoto({ type: "build-start" });
    const store = useAppStore.getState();
    store.setAnalysisError(null);
    store.setAnalyzing(true);
    try {
      const result = await analyzeViaServer({ type: "text", content: text });
      if (result.status === "ok") {
        store.loadEnvelope(result, undefined, text);
        dispatchPhoto({ type: "build-end" });
      } else {
        // §6: GIỮ ảnh và nội dung đã đọc để người học sửa tiếp — không rời trang.
        dispatchPhoto({ type: "build-failure", message: buildFailureMessage(result) });
      }
    } catch (err) {
      store.setAnalysisError(err instanceof Error ? err.message : String(err));
      dispatchPhoto({ type: "build-end" });
    } finally {
      store.setAnalyzing(false);
      buildingRef.current = false;
    }
  }

  // M9-UX2 §9: trạng thái kĩ thuật GIỮ IM khi mọi thứ ổn — học sinh không cần
  // biết "ngân hàng bài: N". Chỉ nói khi có việc phải làm (server tắt/thiếu key).
  const serverStatus =
    health === null ? (
      <span className="hint" style={{ color: "var(--accent-orange)" }}>
        ● Máy chủ phân tích chưa chạy — vẫn dùng được các mô phỏng mẫu bên dưới
      </span>
    ) : health !== "loading" && !health.hasKey ? (
      <span className="hint" style={{ color: "var(--accent-orange)" }}>
        ● Máy chủ thiếu khóa AI — vẫn dùng được các mô phỏng mẫu bên dưới
      </span>
    ) : null;

  return (
    <div className="composer-hero">
      {/* M9-UX5 — HỘP nhiều dòng (không còn pill một dòng): ô gõ ở trên, hai nút
          tròn ở đáy — `+` trái (tải tệp), gửi phải. Placeholder được nói đủ ý vì
          hộp cao sẵn, không sợ cắt cụt như pill. */}
      <div className={`composer-box${analyzing ? " is-busy" : ""}`}>
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptAttr()}
          onChange={onPickFile}
          style={{ display: "none" }}
        />
        {/* Hai lối vào ảnh đề bài. `capture` chỉ là GỢI Ý mở máy ảnh sau trên
            điện thoại; trình duyệt máy tính bỏ qua và mở hộp chọn tệp. */}
        <input
          ref={cameraImageRef}
          type="file"
          accept={IMAGE_ACCEPT}
          capture="environment"
          onChange={onPickImage}
          style={{ display: "none" }}
        />
        <input
          ref={uploadImageRef}
          type="file"
          accept={IMAGE_ACCEPT}
          onChange={onPickImage}
          style={{ display: "none" }}
        />

        {/* W5W — TỆP ĐÍNH KÈM NẰM TRONG KHUNG SOẠN, TRÊN Ô NHẬP.
            Trước đây nó là một khối full-width nằm NGOÀI `.composer-box`, nên
            mắt đọc thành hai vật thể rời trong khi tệp là MỘT PHẦN của đề bài
            sắp gửi. Khối ấy còn nặng hơn cả ô nhập, tức phần phụ lấn phần chính.
            Nay là một chip gọn bên trong cùng một khung — một vật thể, một biên. */}
        {file && (
          <div className="composer-file">
            {/* Ảnh thì xem trước được; `.docx`/`.py` thì không có gì để xem nên
                KHÔNG dựng ô rỗng — chip chỉ còn tên tệp và loại. */}
            {preview && (
              <img className="composer-file-thumb" src={preview} alt={`Xem trước ${file.name}`} />
            )}
            <span className="composer-file-info">
              <strong>{file.name}</strong>
              <span className="hint">{kindLabel(kindFromFile(file.name) ?? "text")}</span>
            </span>
            <button
              className="composer-file-remove"
              onClick={removeFile}
              title="Bỏ tệp"
              aria-label={`Bỏ tệp ${file.name}`}
            >
              ×
            </button>
          </div>
        )}

        <textarea
          ref={textRef}
          className="composer-text"
          rows={1}
          placeholder="Nhập đề hình học không gian, hoặc tải lên tệp đề…"
          aria-label="Đề bài hình học không gian"
          value={problemText}
          onChange={onChangeText}
          onKeyDown={onKeyDown}
          disabled={file !== null || photoActive}
        />

        <div className="composer-foot">
          <div className="composer-tools">
            <button
              className="composer-attach"
              onClick={() => fileInputRef.current?.click()}
              title="Tải tệp đề (.docx / .py / ảnh)"
              aria-label="Tải tệp đề"
            >
              <IconAttach size={17} />
            </button>
            <button
              type="button"
              className="composer-photo-btn"
              onClick={() => cameraImageRef.current?.click()}
              disabled={photo.phase === "building"}
              aria-label="Chụp ảnh đề bài bằng máy ảnh"
            >
              Chụp ảnh
            </button>
            <button
              type="button"
              className="composer-photo-btn"
              onClick={() => uploadImageRef.current?.click()}
              disabled={photo.phase === "building"}
              aria-label="Tải ảnh đề bài từ máy"
            >
              Tải ảnh
            </button>
          </div>
          <button
            className="composer-send"
            onClick={onAnalyze}
            disabled={!canAnalyze}
            title="Phân tích đề bằng AI"
            aria-label="Phân tích đề bằng AI"
          >
            {analyzing ? <span className="composer-spin" /> : <IconSend size={17} />}
          </button>
        </div>
      </div>

      <PhotoProblemPanel
        state={photo}
        previewUrl={photoPreview}
        onRotate={() => {
          cancelRead();
          dispatchPhoto({ type: "rotate" });
        }}
        onReplace={() => uploadImageRef.current?.click()}
        onRemove={() => {
          cancelRead();
          dispatchPhoto({ type: "remove" });
        }}
        onRead={() => void onReadPhoto()}
        onEdit={(text) => dispatchPhoto({ type: "edit", text })}
        onConfirm={(value) => dispatchPhoto({ type: "confirm", value })}
        onBuild={() => void onBuildPhoto()}
      />

      {fileError && <div className="error-banner">{fileError}</div>}
      {serverStatus}
      {/* M18 §5 — HẾT LƯỢT THỬ KHÔNG PHẢI LÀ MỘT LỖI.
          Khách vừa chạy xong một mô phỏng thật; đây là lúc nói cho họ biết tài
          khoản mở thêm được gì, chứ không phải lúc dựng một băng đỏ. Mô phỏng
          vừa chạy KHÔNG bị xoá — nó vẫn nằm nguyên trong phiên. */}
      {analysisError && /lượt mô phỏng thử/.test(analysisError) ? (
        <div className="trial-gate">
          <strong>Em đã dùng hết lượt mô phỏng thử.</strong>
          <p>Đăng nhập để tiếp tục — tài khoản cho phép:</p>
          <ul>
            <li>lưu và mở lại mô phỏng đã làm</li>
            <li>vào lớp bằng mã giáo viên đưa</li>
            <li>nhận và làm bài thực hành</li>
          </ul>
          <div className="trial-gate-actions">
            <button type="button" className="btn-primary"
              onClick={() => useAuthStore.getState().openAuthGate("register")}>
              Tạo tài khoản
            </button>
            <button type="button" className="btn-utility"
              onClick={() => useAuthStore.getState().openAuthGate("login")}>
              Đăng nhập
            </button>
          </div>
        </div>
      ) : analysisError ? (
        <div className="error-banner">{analysisError}</div>
      ) : null}
    </div>
  );
}
