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
import type { InteractionState } from "./interaction-state";
import { Scene3DWorkspace } from "./scene3d-view";
import { IconNext, IconPause, IconPlay, IconPrev, IconReset } from "../../../components/icons";

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
  /**
   * CHẾ ĐỘ ĐIỀU KHIỂN NGOÀI. Vắng ⇒ component tự giữ bước, y như trước.
   *
   * Có `interaction` thì bước sống ở **một chỗ duy nhất** — `InteractionState`
   * của khối thăm dò — cùng chỗ với `selected_id`. Hai bản `step` là chỗ cây
   * và khung nhìn sẽ chỉ về hai bước khác nhau, và §10 cấm timeline thứ hai.
   */
  interaction?: InteractionState;
  onInteraction?: (s: InteractionState) => void;
  onSelect?: (id: string | null) => void;
  /** Chuyển tiếp tới khung nhìn: tăng để yêu cầu đặt lại camera cho vừa hình. */
  fitToken?: number;
}

export function Scene3DPlayer({
  scene, initialStep = 0, interaction, onInteraction, onSelect, fitToken = 0,
}: Props) {
  const [stepTrong, setStepTrong] = useState(() => clampStep(scene, initialStep));
  const beNgoai = interaction !== undefined;
  const step = beNgoai ? interaction!.current_step : stepTrong;
  /* ── NHỊP PHÁT ĐỌC TRẠNG THÁI MỚI NHẤT, KHÔNG ĐỌC BẢN LÚC TẠO NHỊP ──────
   *
   * `setInterval` sống qua nhiều lần render. Bản trước gọi một `setStep` đóng
   * gói `step` và `interaction` của lần render tạo nhịp, nên ở chế độ điều
   * khiển ngoài (khối thăm dò) mỗi nhịp tính lại cùng một "bước sau" và ghi đè
   * `InteractionState` bằng bản cũ: bấm Phát một lần thì kẹt ở bước 1 mãi, và
   * mọi lựa chọn người dùng làm trong lúc phát bị xoá (đo w10 trên trình
   * duyệt thật). Ref giữ bản mới nhất cho mọi lời gọi. */
  const moiNhat = useRef({ step, interaction, onInteraction });
  moiNhat.current = { step, interaction, onInteraction };
  const datTrangThai = (buoc: number, boChon = false) => {
    const moi = clampStep(scene, buoc);
    const hienTai = moiNhat.current;
    if (beNgoai) {
      const ke = {
        ...hienTai.interaction!,
        current_step: moi,
        ...(boChon ? { selected_id: null } : {}),
      };
      moiNhat.current = { ...hienTai, step: moi, interaction: ke };
      hienTai.onInteraction?.(ke);
    } else {
      moiNhat.current = { ...hienTai, step: moi };
      setStepTrong(moi);
    }
  };
  const setStep = (f: number | ((s: number) => number)) =>
    datTrangThai(typeof f === "function" ? f(moiNhat.current.step) : f);
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
      const s = moiNhat.current.step;
      if (isLastStep(scene, s)) {
        setDangPhat(false);
        return;
      }
      const ke = nextStep(scene, s);
      datTrangThai(ke);
      // Dừng NGAY khi bước cuối hiện ra — không chờ thêm một nhịp rỗng.
      if (isLastStep(scene, ke)) setDangPhat(false);
    }, PLAYBACK_INTERVAL_MS);
    return () => {
      if (dongHo.current) clearInterval(dongHo.current);
      dongHo.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dangPhat, scene]);

  /* Ở bước cuối, Phát không còn gì để phát: nút thành XEM LẠI — về bước 0,
   * bỏ chọn (nên tô sáng causal cũng hết), rồi phát. Trước w10 nút này bị vô
   * hiệu và cách duy nhất là kéo thanh bước về đầu. */
  const xemLai = () => {
    datTrangThai(0, true);
    setDangPhat(true);
  };

  const tieuDiem = focusAt(scene, step);

  /* ── ID LÀ ĐỊNH DANH MÁY, KHÔNG PHẢI TÊN ────────────────────────────────
   *
   * `focusAt` trả về **id** — đúng, vì trace nói bằng id. Nhưng dải này là bề
   * mặt học sinh, và in id thẳng ra là cách `Đang dựng the_tich_sabcd` /
   * `Dựa trên S_ABCD` lên tới màn hình (`GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_
   * AUDIT §4`). Tra ngược sang siêu dữ liệu backend đã phát.
   *
   * Hai vai, hai cách gọi: *"Đang dựng"* nói MỘT vật nên dùng câu đầy đủ
   * (*"Trung điểm của A và B"*); *"Dựa trên"* là một DANH SÁCH nên dùng ký
   * hiệu (*"A, B"*) — câu đầy đủ nối bằng dấu phẩy sẽ dài hơn cả khung.
   *
   * Id KHÔNG có vật tương ứng trong cảnh ⇒ coi như **không có gì để nói**, chứ
   * không in id ra. Envelope lưu trước 2026-09-02 mang `object: "system"` ở
   * bước `INIT` — một sentinel của trace, không phải một vật — và in nó ra cho
   * ra dòng *"Đang dựng system"*. Backend nay phát `null` ở đó; nhánh này giữ
   * cho những bản ghi cũ vẫn đọc được. */
  const vat = (id: string) => scene.objects.find((o) => o.id === id) ?? null;
  const tenDayDu = (id: string) => vat(id)?.label ?? null;
  const tenNgan = (id: string) => {
    const o = vat(id);
    return o ? o.reference ?? o.notation ?? o.label : null;
  };

  return (
    <div className="geo3d-player">
      <Scene3DWorkspace
        scene={scene}
        step={step}
        interaction={interaction}
        onSelect={onSelect}
        fitToken={fitToken}
      />

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

        {!giamChuyenDong && (cuoi && !dangPhat ? (
          <button
            type="button"
            className="geo3d-btn"
            onClick={xemLai}
            aria-label="Xem lại quá trình dựng"
          >
            <IconReset /> Xem lại
          </button>
        ) : (
          <button
            type="button"
            className="geo3d-btn"
            onClick={() => setDangPhat((p) => !p)}
            aria-label={dangPhat ? "Tạm dừng" : "Phát lại quá trình dựng"}
          >
            {dangPhat ? <IconPause /> : <IconPlay />}
            {dangPhat ? " Tạm dừng" : " Phát"}
          </button>
        ))}

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
        <dd>
          {(tieuDiem.created && tenDayDu(tieuDiem.created))
            || "— (dữ kiện đề cho)"}
        </dd>
        <dt>Dựa trên</dt>
        <dd>
          {tieuDiem.depends
            .map(tenNgan)
            .filter((t): t is string => !!t)
            .join(", ") || "—"}
        </dd>
      </dl>
    </div>
  );
}
