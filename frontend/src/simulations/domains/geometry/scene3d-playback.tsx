import { useEffect, useRef, useState } from "react";
import {
  PLAYBACK_INTERVAL_MS,
  clampStep,
  focusAt,
  isFirstStep,
  isLastStep,
  nextStep,
  prefersReducedMotion,
  prevStep,
  stepCount,
  type Scene3D,
} from "./scene3d-model";
import { Scene3DWorkspace } from "./scene3d-view";
import { IconNext, IconPause, IconPlay, IconPrev } from "../../../components/icons";

/**
 * Trình PHÁT LẠI quá trình dựng hình — Phase 5E.
 *
 * ─── VÌ SAO TÁCH KHỎI `scene3d-view.tsx` ─────────────────────────────────
 *
 * Renderer là `display(scene, step)` và **không có nút nào** — có test cấm
 * `<button`/`<input` trong file ấy. Luật đó không phải "cấm mọi giao diện", nó
 * là *"khung 3D không được là chỗ dựng hình"*. Điều khiển thời gian là một việc
 * khác hẳn, nên nó ở một file khác.
 *
 * Ranh giới thật, và nó kiểm được: component này **chỉ phát ra một số nguyên**
 * `step`. Nó không đọc `scene.objects`, không tạo đối tượng, không đụng toạ độ.
 * `scene` đi vào và đi ra **nguyên vẹn cùng một tham chiếu**.
 *
 * ─── ĐIỀU NGƯỜI HỌC ĐƯỢC VÀ KHÔNG ĐƯỢC ĐIỀU KHIỂN ───────────────────────
 *
 *   ĐƯỢC     thời gian quan sát (bước) · góc nhìn (camera, do OrbitControls)
 *   KHÔNG    nội dung toán học — không kéo điểm, không đổi toạ độ, không dựng
 *
 * Hình chỉ có thể đến từ một chương trình đã qua thẩm định. Đó là toàn bộ khác
 * biệt giữa hệ này và một phần mềm vẽ hình.
 */

interface Props {
  scene: Scene3D;
  /** Bước khởi đầu — mặc định 0 để mô phỏng bắt đầu từ dữ kiện đề cho. */
  initialStep?: number;
}

export function Scene3DPlayer({ scene, initialStep = 0 }: Props) {
  const [step, setStep] = useState(() => clampStep(scene, initialStep));
  const [dangPhat, setDangPhat] = useState(false);
  const dongHo = useRef<ReturnType<typeof setInterval> | null>(null);
  const tong = stepCount(scene);
  const cuoi = isLastStep(scene, step);
  const dau = isFirstStep(scene, step);

  // TỰ ĐỘNG PHÁT là hoạt cảnh do JS phát — CSS `prefers-reduced-motion` không
  // chạm tới được. Người đã tắt chuyển động vẫn xem được, chỉ là bằng nút.
  const giamChuyenDong = prefersReducedMotion();

  useEffect(() => {
    if (!dangPhat) return undefined;
    dongHo.current = setInterval(() => {
      setStep((s) => {
        if (isLastStep(scene, s)) {
          setDangPhat(false);
          return s;
        }
        return nextStep(scene, s);
      });
    }, PLAYBACK_INTERVAL_MS);
    return () => {
      if (dongHo.current) clearInterval(dongHo.current);
      dongHo.current = null;
    };
  }, [dangPhat, scene]);

  const tieuDiem = focusAt(scene, step);

  return (
    <div className="geo3d-player">
      <Scene3DWorkspace scene={scene} step={step} />

      <div className="geo3d-controls" role="group" aria-label="Điều khiển bước dựng">
        <button
          type="button"
          className="geo3d-btn"
          onClick={() => setStep((s) => prevStep(scene, s))}
          disabled={dau}
          aria-label="Bước trước"
        >
          <IconPrev /> Bước trước
        </button>

        {!giamChuyenDong && (
          <button
            type="button"
            className="geo3d-btn"
            onClick={() => setDangPhat((p) => !p)}
            disabled={cuoi && !dangPhat}
            aria-label={dangPhat ? "Tạm dừng" : "Phát lại quá trình dựng"}
          >
            {dangPhat ? <IconPause /> : <IconPlay />}
            {dangPhat ? " Tạm dừng" : " Phát"}
          </button>
        )}

        <button
          type="button"
          className="geo3d-btn"
          onClick={() => setStep((s) => nextStep(scene, s))}
          disabled={cuoi}
          aria-label="Bước sau"
        >
          Bước sau <IconNext />
        </button>

        <label className="geo3d-scrub">
          <span className="geo3d-scrub-label">Bước</span>
          <input
            type="range"
            min={0}
            max={Math.max(0, tong - 1)}
            value={step}
            onChange={(e) => {
              setDangPhat(false);
              setStep(clampStep(scene, Number(e.target.value)));
            }}
            aria-label={`Chọn bước dựng, hiện ở bước ${step + 1} trên ${tong}`}
          />
        </label>
      </div>

      <dl className="geo3d-focus">
        <dt>Đang dựng</dt>
        <dd>{tieuDiem.created ?? "— (dữ kiện đề cho)"}</dd>
        <dt>Dựa trên</dt>
        <dd>{tieuDiem.depends.length ? tieuDiem.depends.join(", ") : "—"}</dd>
      </dl>
    </div>
  );
}
