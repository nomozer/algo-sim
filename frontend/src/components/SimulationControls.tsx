import { useEffect, useState, type CSSProperties } from "react";
import { getSimulation } from "../simulations/registry";
import { transportModeOf } from "../simulations/transport-policy";
import type { PresentationEntry } from "../simulations/types";
import { useAppStore } from "../state/store";
import { exploreEntry } from "./SimulationWorkspace";
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
  /* W5G — KHÔNG CÒN NÚT MỜ THƯỜNG TRỰC.
   *
   * Luật cũ: lối vào không dùng được thì render MỜ chứ không biến mất, để khay
   * khỏi nhấp nháy khi đi từng bước. Cái giá lớn hơn cái lợi: ở `binary_search`,
   * phần lớn trong 13 bước thuật toán không phải quyết định gì, nên "Thử thách"
   * ngồi mờ gần như suốt — một nút vĩnh viễn không bấm được, đặt NGANG HÀNG với
   * công cụ chính, không dạy gì cả.
   *
   * Nó cũng chọi với luận điểm: đây là hệ MÔ PHỎNG TƯƠNG TÁC, vòng lặp chính
   * phải là thao tác → hệ quả tất định. Để một lối vào chấm điểm đứng ngang hàng
   * thường trực chính là thứ W12 đo được (52/92 dòng đọc ra "một bài kiểm tra
   * chứ không phải một công cụ"). Phase B mới gỡ CÁI CHỐT, chưa gỡ THỨ BẬC.
   *
   * Nay: không có gì để cam kết ⇒ VẮNG MẶT. Có ⇒ HIỆN RA — và chính việc nút
   * xuất hiện trở thành tín hiệu dạy học ("bước này thuật toán phải quyết định
   * gì đó") thay vì là đồ đạc.
   *
   * ĐÁNH ĐỔI KHAI TƯỜNG MINH: khay có thể nhấp nháy khi đi từng bước. Chấp nhận
   * — một nút xuất hiện ĐÚNG LÚC mang nhiều thông tin hơn một nút luôn ở đó và
   * luôn mờ. Năng lực `predict`/`predict.check` KHÔNG đổi một dòng: trục "học
   * sinh được sai, chỉ engine phán sai" (`CORRECTNESS.md`) còn nguyên. Đây là
   * dời TRÌNH BÀY, không dời SỰ THẬT.
   *
   * `!open` là điều kiện bắt buộc: đang MỞ thì không bao giờ gỡ, nếu không học
   * sinh mắc kẹt trong một chế độ không có đường ra. */
  if (entry.available === false && !open) return null;
  /* W4B-3B — CHỮ ĐẦY ĐỦ KHÔNG MẤT, CHỈ THÔI CHIẾM CHỖ.
     Nhãn hiển thị rút gọn ("Khám phá"/"Thử thách") để dải điều khiển không
     xuống dòng ở 1366; tên khả truy cập vẫn là câu đầy đủ + câu mời-thử, nên
     bất biến "cổng tự mô tả" (PhET/CLT) giữ nguyên với cả chuột lẫn công nghệ
     hỗ trợ. Khung giải thích đầy đủ hiện ra KHI MỞ chế độ. */
  const full = [entry.label, entry.hint].filter(Boolean).join(" — ");
  /* W5G — `unavailableHint` KHÔNG còn được đọc ở đây, và đó là hệ quả đúng: lối
     vào không dùng được thì VẮNG MẶT, nên không còn nút mờ nào để giải thích.
     Thông tin "chưa tới lúc" nay do chính sự vắng mặt mang. */
  const describe = full;
  return (
    <button
      type="button"
      className={`sim-secondary-action${open ? " is-active" : ""}`}
      onClick={onToggle}
      aria-expanded={open}
      title={open ? undefined : describe}
      aria-label={open ? undefined : describe}
    >
      {open ? (entry.closeLabel ?? closeFallback) : (entry.shortLabel ?? entry.label)}
    </button>
  );
}

const SPEED_STEPS = [
  { label: "0.5x", ms: 1600 },
  { label: "1x", ms: 800 },
  { label: "1.5x", ms: 500 },
  { label: "2x", ms: 300 },
] as const;

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
  const exploreOpen = useAppStore((s) => s.exploreOpen);
  const setExploreOpen = useAppStore((s) => s.setExploreOpen);
  const timeline = mod?.timeline;
  /* W7 §7 — DÒNG THỜI GIAN TUỲ CHỌN: gập mặc định.
     Trạng thái TRÌNH BÀY thuần, sống trong component — mở/đóng nó KHÔNG được
     đụng tới state công cụ (§16: "tool state stays authoritative"). Đưa vào
     store là mở đường cho một lượt set() vô tình chạm vào `active`. */
  const [traceOpen, setTraceOpen] = useState(false);
  const [barCollapsed, setBarCollapsed] = useState(false);

  /* Đổi mô phỏng ⇒ gập lại. `SimulationControls` KHÔNG remount khi học sinh mở
     bài khác, nên nếu không có dòng này thì mở dòng thời gian ở bài A sẽ khiến
     bài B mở sẵn — trái đúng luật "mô phỏng mới mở ở chế độ quan sát" mà W6 đã
     chốt cho Thử thách/Khám phá.
     Đo được bằng `runtime-zero-ai-w7.mjs`: nạp base_conversion, mở trace, rồi
     nạp character_encoding thì nút "Xem cách thực hiện" biến mất vì dải đã ở
     trạng thái mở. */
  const activeModuleId = active?.moduleId;
  useEffect(() => { setTraceOpen(false); setBarCollapsed(false); }, [activeModuleId]);

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
      if ((e.target as HTMLElement | null)?.closest?.('button, [role="button"], input, select, textarea')) {
        return;
      }
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
  const explore = exploreEntry(mod, active.state, active.config);

  /* W13 — MỘT lối vào, không phải hai. Cạnh Khám phá từng có cửa "Thử thách"
     (mở thanh dự đoán có chấm điểm); năng lực đó đã gỡ, nên dải hành động phụ
     nay chỉ còn đúng một cửa và không còn phải giải thích cho học sinh hai chế
     độ khác loại nhau ở chỗ nào. */
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
    </>
  );

  // Capability-driven (không switch-case id): hiện nút bước KHI có timeline VÀ
  // thực sự có >1 bước để đi. Cảnh khám phá (1 khung) chỉ hiện Đặt lại —
  // không "step giả". Áp dụng cho cả generic exploratory lẫn module chuyên biệt.
  /* ── W7 §9 — CHẾ ĐỘ ĐẾN TỪ CHÍNH SÁCH, KHÔNG TỪ THUỘC TÍNH KĨ THUẬT ──────
   *
   * Trước wave này dòng dưới là toàn bộ phép phân loại:
   *     timeline !== undefined && timeline.stepCount(state) > 1
   * tức "có nhiều hơn một bước ⇒ hiện đủ bộ điều khiển". Đó đúng là kiểu suy
   * §9 cấm: `base_conversion` có 12 bước nên nó được một dòng thời gian đầy đủ,
   * dù sau W5 kết quả của nó đọc được ngay và trình tự chỉ còn để giải thích.
   *
   * Nay chế độ do `transport-policy.ts` khai theo CƠ CHẾ. `stepCount` vẫn được
   * dùng, nhưng chỉ để trả lời một câu hẹp hơn nhiều: "có gì để tua không" —
   * một dòng thời gian một bước thì không dựng nút bước dù chính sách nói gì.
   */
  const declaredMode = transportModeOf(active.moduleId);
  const stepsAvailable = timeline !== undefined && timeline.stepCount(active.state) > 1;
  /* Target chưa khai chính sách: lùi về hành vi cũ thay vì giấu mất điều khiển
     của một mô phỏng đang chạy được. Guard ở `experience-manifest.test.ts` đòi
     con số chưa-khai bằng 0, nên nhánh này là lưới an toàn, không phải mặc định
     được phép sống lâu. */
  const mode = declaredMode ?? (stepsAvailable ? "FULL_TRACE" : "RESET_ONLY");
  const showFullTransport = stepsAvailable
    && (mode === "FULL_TRACE" || (mode === "OPTIONAL_TRACE" && traceOpen));

  if (barCollapsed) {
    return (
      <div className="player player-floating-bar">
        <button
          type="button"
          className="btn-floating-toggle"
          onClick={() => setBarCollapsed(false)}
          title="Mở thanh điều khiển"
        >
          <IconPlay size={14} />
          <span>Hiện thanh điều khiển</span>
        </button>
      </div>
    );
  }

  if (!showFullTransport) {
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
          {/* W7 §7 — LỐI VÀO DÒNG THỜI GIAN, chỉ cho target CÔNG CỤ.
              RESET_ONLY không dựng nút này: cơ chế của nó không có tiến trình
              nào để xem, nên một nút "Xem cách thực hiện" ở đó là lời hứa suông. */}
          {mode === "OPTIONAL_TRACE" && stepsAvailable && (
            <button className="btn-utility" onClick={() => setTraceOpen(true)}
              title="Xem từng bước của phép biến đổi">
              Xem cách thực hiện
            </button>
          )}
        </span>
        <span className="control-zone control-zone-aux">
          {secondary}
          <button
            type="button"
            className="btn-utility"
            onClick={() => setBarCollapsed(true)}
            title="Thu nhỏ thanh điều khiển"
            style={{ padding: "4px 8px", fontSize: 11 }}
          >
            Ẩn thanh
          </button>
        </span>
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
          {/* Mở được thì phải đóng được — cùng luật với Thử thách ở W6. */}
          {mode === "OPTIONAL_TRACE" && (
            <button className="btn-utility" onClick={() => setTraceOpen(false)}
              title="Ẩn dòng thời gian, quay lại công cụ">
              Ẩn các bước
            </button>
          )}
          <div className="speed-control" role="group" aria-label="Tốc độ phát">
            <span className="speed-label">Tốc độ:</span>
            <div className="speed-pills">
              {SPEED_STEPS.map((s) => {
                const isActive = Math.abs(speedMs - s.ms) < 100;
                return (
                  <button
                    key={s.label}
                    type="button"
                    className={`btn-speed-pill${isActive ? " is-active" : ""}`}
                    onClick={() => setSpeedMs(s.ms)}
                    title={`Đặt tốc độ ${s.label}`}
                  >
                    {s.label}
                  </button>
                );
              })}
            </div>
          </div>
          {secondary}
          <button
            type="button"
            className="btn-utility"
            onClick={() => setBarCollapsed(true)}
            title="Thu nhỏ thanh điều khiển"
            style={{ padding: "4px 8px", fontSize: 11 }}
          >
            Ẩn thanh
          </button>
        </span>
      </div>
    </div>
  );
}
