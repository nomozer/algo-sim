import { useEffect, type CSSProperties } from "react";
import { getSimulation } from "../simulations/registry";
import type { PresentationEntry } from "../simulations/types";
import { useAppStore } from "../state/store";
import { challengeEntry, exploreEntry } from "./SimulationWorkspace";
import {
  IconNext,
  IconPause,
  IconPlay,
  IconPrev,
  IconReset,
  IconToEnd,
  IconToStart,
} from "./icons";

/**
 * W4B-3A — MỘT hình thức cho MỌI lối vào phụ.
 *
 * Trước wave này ba chỗ dựng nút mở (shell + hai renderer miền) và chúng đã trôi
 * khỏi nhau: shell dùng `is-active` + `aria-expanded`, hai miền dựng nút riêng
 * kèm icon rồi tự đổi nhãn. Gom về một component để "nút phụ" chỉ còn một định
 * nghĩa — đúng thứ `secondary-actions-w4b2w.test.ts` sinh ra để giữ.
 */
function SecondaryEntry({
  entry,
  open,
  onToggle,
  closeFallback,
}: {
  entry: PresentationEntry;
  open: boolean;
  onToggle: () => void;
  closeFallback: string;
}) {
  /* Bước này không dùng được ⇒ MỜ, không biến mất: nút nhảy vào/ra khỏi dải
     điều khiển mỗi lần bấm Tiến còn khó dùng hơn nút mờ (xem `PresentationEntry`).
     Đang MỞ thì không bao giờ khoá — nếu không học sinh mắc kẹt trong chế độ
     không có đường ra. */
  const disabled = entry.available === false && !open;
  /* W4B-3B — CHỮ ĐẦY ĐỦ KHÔNG MẤT, CHỈ THÔI CHIẾM CHỖ.
     Nhãn hiển thị rút gọn ("Khám phá"/"Thử thách") để dải điều khiển không
     xuống dòng ở 1366; tên khả truy cập vẫn là câu đầy đủ + câu mời-thử, nên
     bất biến "cổng tự mô tả" (PhET/CLT) giữ nguyên với cả chuột lẫn công nghệ
     hỗ trợ. Khung giải thích đầy đủ hiện ra KHI MỞ chế độ. */
  const full = [entry.label, entry.hint].filter(Boolean).join(" — ");
  return (
    <button
      type="button"
      className={`sim-secondary-action${open ? " is-active" : ""}`}
      onClick={onToggle}
      disabled={disabled}
      aria-expanded={open}
      title={open ? undefined : full}
      aria-label={open ? undefined : full}
    >
      {open ? (entry.closeLabel ?? closeFallback) : (entry.shortLabel ?? entry.label)}
    </button>
  );
}

/**
 * Thanh điều khiển đáy — CAPABILITY-DRIVEN (M2 #4):
 * - module có timeline → đủ bộ về-đầu / lùi / chạy-dừng / tiến / đến-cuối +
 *   seek + tốc độ + Đặt lại + phím tắt;
 * - module không có timeline (exploratory) → chỉ Đặt lại, không nút step giả.
 * M9-UX5: icon là component SVG (`icons.tsx`), không còn ký tự ⏮ ◀ ▶ ⏸ ⏭ ⟳.
 */
export function SimulationControls() {
  const active = useAppStore((s) => s.active);
  const playing = useAppStore((s) => s.playing);
  const speedMs = useAppStore((s) => s.speedMs);
  const nextStep = useAppStore((s) => s.nextStep);
  const prevStep = useAppStore((s) => s.prevStep);
  const toStart = useAppStore((s) => s.toStart);
  const toEnd = useAppStore((s) => s.toEnd);
  const goToStep = useAppStore((s) => s.goToStep);
  const resetSim = useAppStore((s) => s.resetSim);
  const setPlaying = useAppStore((s) => s.setPlaying);
  const setSpeedMs = useAppStore((s) => s.setSpeedMs);

  const mod = active ? getSimulation(active.moduleId) : undefined;
  const challengeOpen = useAppStore((s) => s.challengeOpen);
  const setChallengeOpen = useAppStore((s) => s.setChallengeOpen);
  const exploreOpen = useAppStore((s) => s.exploreOpen);
  const setExploreOpen = useAppStore((s) => s.setExploreOpen);
  const timeline = mod?.timeline;

  // Tự chạy: hẹn giờ gọi nextStep; store tự dừng khi hết timeline
  useEffect(() => {
    if (!playing || !timeline) return;
    const id = window.setInterval(() => useAppStore.getState().nextStep(), speedMs);
    return () => window.clearInterval(id);
  }, [playing, speedMs, timeline]);

  // Phím tắt ← → Space — chỉ khi có timeline
  useEffect(() => {
    if (!timeline) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return;
      // Phím tắt TOÀN CỤC không được cướp phím của một control đang focus.
      // Đã cháy HAI lần, cùng một nguyên nhân:
      //  1. node đầu vào A/B/C của boolean_dag (`role="button"`) — bấm Space
      //     vừa đổi giá trị đầu vào, VỪA bật Tự chạy;
      //  2. (W1) nút đáp án dự đoán — `<button>` THẬT, không có `role`, nên
      //     guard cũ không che: đo trong Chrome thấy Space làm `playing = true`
      //     và câu trả lời mất trắng.
      // Nên guard theo NĂNG LỰC "tự xử lý Enter/Space", không theo một thuộc
      // tính cụ thể: control gốc và control giả đều tự lo phím của mình.
      const target = e.target as Element | null;
      if (target?.closest?.('button, a[href], select, [role="button"]')) return;
      if (e.key === "ArrowRight") {
        e.preventDefault();
        useAppStore.getState().nextStep();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        useAppStore.getState().prevStep();
      } else if (e.key === " ") {
        e.preventDefault();
        const s = useAppStore.getState();
        s.setPlaying(!s.playing);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [timeline]);

  if (!active || !mod) return null;

  /* W4B-2Z §20/§23 — Thử thách là HÀNH ĐỘNG PHỤ NẰM CẠNH ĐIỀU KHIỂN, không phải
     một dải nội dung dưới mô hình. Đặt ở đây (thay vì trong `SimulationWorkspace`)
     vì đây đã là chỗ của "việc học sinh làm với mô phỏng" — gộp vào chứ KHÔNG
     đẻ thêm container để chứa nó. Năng lực `predict` và bên chấm `predict.check`
     không đổi một dòng; đây là dời TRÌNH BÀY.

     W4B-3A — nay đây là chủ sở hữu DUY NHẤT của lối vào phụ: cả Thử thách lẫn
     Khám phá. Trước wave này hai renderer miền tự dựng lấy nút "Thí nghiệm" của
     mình, nên cùng một vai trò có ba hiện thực và hai trong số đó nằm dưới mô
     hình như một dải nội dung. */
  /* Nhãn do MODULE cấp (dẫn xuất từ config đã validate), shell chỉ giữ câu mặc
     định cho module chưa khai — nhờ vậy bài tìm kiếm mời đúng việc của nó ("tự
     chọn nửa để tìm tiếp") mà shell không cần biết bài nào là bài nào.
     `null` ⇒ KHÔNG dựng nút: một lối vào dẫn tới màn hình trống thì tệ hơn là
     không có lối vào. */
  const challenge = challengeEntry(mod, active.state, active.config);
  const explore = exploreEntry(mod, active.state, active.config);

  const secondary = (
    <>
      {explore && (
        <SecondaryEntry
          open={exploreOpen}
          onToggle={() => setExploreOpen(!exploreOpen)}
          entry={explore}
          closeFallback="Đóng khám phá"
        />
      )}
      {challenge && (
        <SecondaryEntry
          open={challengeOpen}
          onToggle={() => setChallengeOpen(!challengeOpen)}
          entry={challenge}
          closeFallback="Đóng thử thách"
        />
      )}
    </>
  );

  // Capability-driven (không switch-case id): hiện nút bước KHI có timeline VÀ
  // thực sự có >1 bước để đi. Cảnh khám phá (1 khung) chỉ hiện Đặt lại —
  // không "step giả". Áp dụng cho cả generic exploratory lẫn module chuyên biệt.
  const hasSteps = timeline !== undefined && timeline.stepCount(active.state) > 1;
  if (!hasSteps) {
    return (
      /* W4B-3E — bài KHÁM PHÁ dùng CÙNG khuôn ba vùng, chỉ thiếu vùng transport.
         Câu "Mô phỏng khám phá — thao tác trực tiếp trên sân khấu." (50 ký tự)
         rời khỏi hàng: nó mô tả CÁCH DÙNG cả sân khấu chứ không phải một nút, và
         chữ dài thường trực là thứ ép dải điều khiển xuống dòng. Nó thành tên
         khả truy cập của chính dải — không mất với người đọc màn hình. */
      <div
        className="player-controls"
        role="group"
        aria-label="Mô phỏng khám phá — thao tác trực tiếp trên sân khấu"
      >
        <span className="control-zone control-zone-meta">
          <button className="btn-utility" onClick={resetSim} title="Dựng lại từ đầu">
            <IconReset size={14} />
            Đặt lại
          </button>
        </span>
        <span className="control-zone control-zone-aux">{secondary}</span>
      </div>
    );
  }

  const cursor = timeline.currentStep(active.state);
  const total = timeline.stepCount(active.state);
  const last = cursor >= total - 1;

  /* W4B-3E — BA VÙNG TƯỜNG MINH, KHÔNG PHẢI MỘT HÀNG PHẲNG.
   *
   * Đo được trước wave này (Chrome thật, `.player-controls`): ở 1920 có **2 dải**
   * con và một khoảng hở **633px** giữa hai phần tử CÙNG hàng (1536: 421px ·
   * 1366: 251px). Khoảng hở đó không do ai thiết kế — nó là CHỖ THỪA, sinh ra vì
   * `.speed-control` mang `margin-left:auto`: một THÀNH VIÊN tự quyết bố cục của
   * cả hàng, và mọi thứ đứng sau nó (phím tắt, Khám phá, Thử thách) bị đẩy theo.
   * Hở scale theo bề rộng màn hình chính là dấu hiệu của "phần còn lại", không
   * phải của một khoảng cách có chủ đích.
   *
   * Nay bố cục do BA VÙNG quyết, mỗi vùng là một nhóm có nghĩa:
   *   [lùi · CHẠY · tiến]   [đặt lại | bước x/y]   [tốc độ] [Khám phá] [Thử thách]
   * và đúng MỘT lệnh đẩy (`margin-left:auto`) đặt trên VÙNG cuối, không đặt trên
   * một thành viên. Thứ tự đọc = thứ tự ưu tiên: chạy > đặt lại/tiến độ > phụ.
   *
   * Gợi ý phím tắt rời khỏi hàng: nó là chữ dài thường trực, và chữ dài trong
   * dải điều khiển chính là thứ ép xuống dòng. Nội dung KHÔNG mất — nó thành
   * TÊN KHẢ TRUY CẬP của vùng transport, nên người dùng đọc màn hình vẫn nghe
   * được, còn bố cục thì không phải gánh.
   */
  return (
    <div className="player">
      <div className="player-controls">
        <span
          className="control-zone control-zone-primary"
          role="group"
          aria-label="Điều khiển bước — phím mũi tên trái/phải để lùi/tiến, phím Space để tự chạy"
        >
          <button className="btn-icon" onClick={toStart} disabled={cursor === 0} title="Về đầu">
            <IconToStart />
          </button>
          <button className="btn-icon" onClick={prevStep} disabled={cursor === 0} title="Lùi một bước">
            <IconPrev />
          </button>
          <button
            className="btn-primary btn-play"
            onClick={() => setPlaying(!playing)}
            disabled={last && !playing}
          >
            {playing ? <IconPause size={15} /> : <IconPlay size={15} />}
            {playing ? "Dừng" : "Tự chạy"}
          </button>
          <button className="btn-icon" onClick={nextStep} disabled={last} title="Tiến một bước">
            <IconNext />
          </button>
          <button className="btn-icon" onClick={toEnd} disabled={last} title="Đến cuối">
            <IconToEnd />
          </button>
        </span>

        <span className="control-zone control-zone-meta">
          <button className="btn-utility" onClick={resetSim} title="Dựng lại từ đầu">
            <IconReset size={14} />
            Đặt lại
          </button>
        </span>

        {/* TIẾN ĐỘ NẰM TRONG HÀNG, VÀ NÓ ĂN HẾT CHỖ THỪA.
         *
         * Đây là chỗ hai khiếu nại gặp nhau. Bản ba-vùng đầu tiên đã gỡ được
         * việc xuống dòng (2 dải → 1) nhưng khoảng hở còn TĂNG (633 → 796px
         * @1920): đẩy vùng phụ sang phải chỉ DỜI chỗ trống chứ không xoá nó.
         * Chỗ trống ấy vốn có thật — một dải 1920px chỉ có dăm cái nút.
         *
         * Nên giao nó cho thứ THẬT SỰ CẦN bề ngang: thanh tua. Nó vừa hết là
         * khoảng chết, vừa thôi đọc thành "một vạch tách rời" bên dưới — nó
         * nằm ngay giữa bộ điều khiển, đúng chỗ người ta tìm nó. */}
        {/* TIẾN ĐỘ = MỘT NHÓM, KHÔNG PHẢI HAI PHẦN TỬ RỜI.
         *
         * Số bước là NHÃN của thanh tua, nên nó đứng liền thanh tua chứ không
         * lang thang cạnh "Đặt lại". Trước wave này chúng ở hai vùng khác nhau,
         * nên mắt phải tự ghép "Bước 1/10" với cái track ở tận đâu.
         *
         * `--p` là phần trăm đã đi, dùng để tô phần đã qua. Nó DẪN XUẤT từ
         * cursor/total — trình bày thuần, không phải nguồn sự thật thứ hai. */}
        <span
          className="player-track"
          style={{ "--p": total > 1 ? (cursor / (total - 1)) * 100 : 0 } as CSSProperties}
        >
          <span className="step-indicator">
            Bước {cursor + 1}<span className="step-of"> / {total}</span>
          </span>
          <input
            className="player-progress"
            type="range"
            min={0}
            max={total - 1}
            value={cursor}
            onChange={(e) => goToStep(Number(e.target.value))}
            aria-label={`Tua đến bước — đang ở bước ${cursor + 1} trên ${total}`}
          />
        </span>

        <span className="control-zone control-zone-aux">
          <label className="speed-control">
            Tốc độ
            <input
              type="range"
              min={300}
              max={2500}
              step={100}
              value={2800 - speedMs}
              onChange={(e) => setSpeedMs(2800 - Number(e.target.value))}
            />
          </label>
          {secondary}
        </span>
      </div>
    </div>
  );
}
