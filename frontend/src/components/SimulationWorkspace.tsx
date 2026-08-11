import { Suspense, type ComponentType } from "react";
import { getSimulation } from "../simulations/registry";
import {
  effectiveVisualMode,
  learnerFacingModes,
  rendererFor,
} from "../simulations/renderer";
import type {
  ExploreCapability,
  Narration,
  PredictionCapability,
  PresentationEntry,
  VisualMode,
  WorkspaceProps,
} from "../simulations/types";
import { useAppStore } from "../state/store";
import { PredictionBar } from "./PredictionBar";

/**
 * M8: toggle 2D/3D — component THUẦN theo props (export để test SSR được:
 * store zustand trả initial state khi renderToString nên không test qua store).
 * Dưới 2 mode khả dụng → null: không affordance rỗng (triết lý M7.14D.1).
 */
export function VisualModeToggle({
  modes,
  mode,
  onSelect,
}: {
  modes: VisualMode[];
  mode: VisualMode;
  onSelect: (m: VisualMode) => void;
}) {
  if (modes.length < 2) return null;
  return (
    /* W4B-2V — ĐÂY LÀ "CÁCH XEM", KHÔNG PHẢI MỘT LỰA CHỌN KỸ THUẬT.
       Nhãn `2D`/`3D` trần đặt câu hỏi mà học sinh chưa có cơ sở trả lời ("nên
       hiểu bài này ở 2D hay 3D?"). Gọi đúng tên trách nhiệm — đổi CÁCH XEM một
       mô hình đã có sẵn biểu diễn chính — thì nó lùi về đúng vai phụ. */
    <span className="visual-mode-toggle" role="group" aria-label="Cách xem mô hình">
      <span className="visual-mode-label">Cách xem</span>
      {modes.map((m) => (
        <button
          key={m}
          type="button"
          className={`btn-utility${mode === m ? " is-active" : ""}`}
          onClick={() => onSelect(m)}
        >
          {m.toUpperCase()}
        </button>
      ))}
    </span>
  );
}

const MODE_LABEL: Record<string, string> = {
  progressive: "từng bước",
  exploratory: "khám phá",
  hybrid: "kết hợp",
};

/**
 * (M17 W0) Thông báo "ngoài danh mục" cho HỌC SINH — component THUẦN theo
 * props (export để test SSR như VisualModeToggle). Ưu tiên `learner_reason`
 * (server gắn ở biên API, không token kỹ thuật); `reason` kỹ thuật chỉ là
 * fallback tương thích ngược cho envelope cũ. Không bao giờ render
 * error_code / failure_category / JSON path.
 */
export function UnsupportedNotice({
  unsupported,
}: {
  unsupported: {
    reason: string;
    learner_reason?: string;
    failure_category?: string;
    /** (M17 W2B-PATCH) Mã chi tiết — dùng khi một `failure_category` gộp nhiều
     *  ca cần lời khuyên KHÁC NHAU. Không hiển thị cho học sinh. */
    error_code?: string;
  };
}) {
  // (M17-VR1) Đề THIẾU DỮ KIỆN khác hẳn đề NGOÀI DANH MỤC: chủ đề vẫn được hỗ
  // trợ, chỉ là em chưa cho đủ dữ liệu. Nói "ngoài danh mục" ở đây làm học sinh
  // tưởng hệ không mô phỏng được dạng bài đó — sai và làm nản.
  const insufficient = unsupported.failure_category === "insufficient_specification";
  // (M17 W2B-VR) Đề hỏi NHIỀU việc/nhiều truy vấn cùng lúc khác hẳn "thiếu dữ
  // kiện" và "ngoài danh mục": chủ đề được hỗ trợ, dữ liệu đủ, chỉ là mỗi lần
  // mô phỏng trình bày được một yêu cầu. Nói "ngoài danh mục" ở đây làm học
  // sinh tưởng hệ không làm được — sai.
  const incomplete = unsupported.failure_category === "semantic_incomplete";
  // (M17 W2B-PATCH) Trong CÙNG `semantic_incomplete` có HAI ca ngược nhau về
  // lời khuyên, nên tiêu đề/gợi ý phải đọc `error_code` (chi tiết hơn) trước:
  // - hỏi nhiều truy vấn độc lập → tách đề ra là ĐÚNG;
  // - đề MỘT truy vấn nhiều bước mà hệ dựng thiếu bước → tách ra VÔ ÍCH, phải
  //   nói rõ là chưa dựng đủ bước. Lỗi này do review ẢNH bắt được.
  const stageShortfall = unsupported.error_code === "pipeline_stage_incomplete";
  const eyebrow = insufficient ? "CHƯA ĐỦ DỮ KIỆN"
    : stageShortfall ? "CHƯA DỰNG ĐỦ CÁC BƯỚC"
    : incomplete ? "TÁCH THÀNH TỪNG YÊU CẦU"
    : "NGOÀI DANH MỤC MÔ PHỎNG";
  const hint = insufficient
    ? "Bổ sung dữ liệu còn thiếu vào đề rồi gửi lại — dạng bài này hệ có mô phỏng."
    : stageShortfall
    ? "Nêu rõ từng bước cần làm rồi gửi lại — dạng bài nhiều bước này hệ có mô phỏng."
    : incomplete
    ? "Mỗi lần hỏi một yêu cầu (giữ nguyên dữ liệu) để xem đầy đủ từng bước của yêu cầu đó."
    : "Danh mục mô phỏng sẽ được mở rộng dần (nhị phân, cổng logic, mạng máy tính...).";
  return (
    <section className="card">
      <span className="eyebrow">{eyebrow}</span>
      <p style={{ marginTop: "var(--sp-sm)" }}>
        {unsupported.learner_reason ?? unsupported.reason}
      </p>
      <p className="notes">{hint}</p>
    </section>
  );
}

/**
 * (SHELL-N) KHE THUYẾT MINH — component THUẦN theo props (export để test SSR).
 *
 * Đây là chỗ DUY NHẤT trong sản phẩm dựng thuyết minh bước hiện tại. Module chỉ
 * trả chuỗi qua `narrate()`; vị trí, nền, khoảng cách, biến thể "thao tác của
 * em" đều do shell quyết. `null` → không dựng gì (không để lại ô rỗng).
 *
 * `role="status"` + `aria-live="polite"`: đổi bước bằng nút hay bằng phím tắt
 * đều được đọc lên. Trước bản này không có vùng aria-live nào trong workspace —
 * người dùng đọc màn hình bấm "Tiến" không nghe thấy gì.
 */
export function NarrationSlot({ narration }: { narration: Narration | null }) {
  if (!narration) return null;
  return (
    <div
      className={`narration-bar${narration.fromLearner ? " is-user" : ""}`}
      role="status"
      aria-live="polite"
    >
      {narration.text}
    </div>
  );
}

/**
 * W4B-2U2 §13 — CÓ BÀY BỀ MẶT THỬ THÁCH KHÔNG. Hàm THUẦN, và nó phải thuần vì
 * một lý do đã có tiền lệ trong kho: `SimulationWorkspace` đọc store, mà zustand
 * v5 dùng `useSyncExternalStore` nên **SSR luôn trả trạng thái ĐẦU**
 * (`ARCHITECTURE_MAP §8` #8). Test `renderToString(<SimulationWorkspace/>)` sau
 * khi `loadEnvelope` sẽ thấy **empty-state**, và mọi khẳng định kiểu "không chứa
 * chuỗi X" sẽ XANH vì màn hình rỗng — xanh vì lý do sai.
 *
 * Cùng khuôn `commitmentSurfaceVisible` / `commitmentSurfaceKind`: luật sống ở
 * hàm thuần, production và test gọi CÙNG một nguồn.
 *
 * `predict` là NĂNG LỰC; `challengeOpen` là TRÌNH BÀY. Module tự bày cam kết
 * trên sân khấu (`presentedInStage`) thì shell không dựng bề mặt thứ hai.
 */
export function challengeSurfaceVisible<S>(
  mod: { predict?: { presentedInStage?: (state: S) => boolean } },
  state: S,
  challengeOpen: boolean,
): boolean {
  if (!mod.predict) return false;
  if (mod.predict.presentedInStage?.(state)) return false;
  return challengeOpen;
}

/**
 * Có dựng LỐI VÀO Thử thách không — dẫn xuất từ NĂNG LỰC, không từ tên bài.
 *
 * W4B-3A — SỬA MỘT LẦN LẪN LỘN CỬA VỚI PHÒNG.
 *
 * Bản trước trả `false` khi module tự bày cam kết trên sân khấu
 * (`presentedInStage`). Ý định đúng — không được có HAI bề mặt hỏi cùng một câu
 * — nhưng chỗ áp sai: nó tắt cả CÁI CỬA, không chỉ bề mặt thứ hai. Hệ quả đo
 * được ở 8 target thuật toán: đúng những bước có vùng cam kết thì shell không
 * dựng lối vào nào, nên `domains/algorithm/ui.tsx` phải tự dựng lấy một nút mở
 * — và nút tự dựng ấy CHÍNH LÀ dải `experimentTrigger` nằm dưới mô hình.
 *
 * Nay: cửa suy từ năng lực `predict` (một cửa, ở dải hành động phụ), còn
 * `presentedInStage` giữ nguyên trách nhiệm THẬT của nó ở
 * `challengeSurfaceVisible` — chặn `PredictionBar` khi sân khấu đã hỏi rồi.
 * Một cửa, nhiều nhất một bề mặt.
 */
export function challengeEntry<S>(
  mod: { predict?: PredictionCapability<S> },
  state: S,
  config: unknown,
): PresentationEntry | null {
  if (!mod.predict) return null;
  // Module chưa khai câu mời ⇒ câu mặc định của shell (tương thích ngược).
  if (!mod.predict.entry) return DEFAULT_CHALLENGE;
  return mod.predict.entry(state, config);
}

/** Câu mời mặc định khi module không khai `predict.entry`. */
export const DEFAULT_CHALLENGE: PresentationEntry = {
  label: "Thử thách: tự dự đoán bước này",
  shortLabel: "Thử thách",
  closeLabel: "Đóng thử thách",
};

/**
 * Có dựng LỐI VÀO Khám phá không — cũng dẫn xuất từ năng lực.
 *
 * Module không khai `explore` ⇒ không có lối vào (mặc định an toàn). Khai mà
 * `entry()` trả `null` ở trạng thái này ⇒ cũng không dựng: một lối vào rỗng
 * ("khám phá đi" ở bước cuối, khi không còn gì để đổi) tệ hơn là không có.
 */
export function exploreEntry<S>(
  mod: { explore?: ExploreCapability<S> },
  state: S,
  config: unknown,
): PresentationEntry | null {
  return mod.explore?.entry(state, config) ?? null;
}

/**
 * Vùng trung tâm — host sân khấu mô phỏng (M2 #1). KHÔNG giả định simulation
 * là thuật toán (M2 #2): mọi thứ domain-specific render qua module.Workspace
 * lấy từ registry.
 */
export function SimulationWorkspace() {
  const active = useAppStore((s) => s.active);
  const unsupported = useAppStore((s) => s.unsupported);
  const playing = useAppStore((s) => s.playing);
  const dispatch = useAppStore((s) => s.dispatch);
  const visualMode = useAppStore((s) => s.visualMode);
  const challengeOpen = useAppStore((s) => s.challengeOpen);
  const setVisualMode = useAppStore((s) => s.setVisualMode);

  if (unsupported) {
    return <UnsupportedNotice unsupported={unsupported} />;
  }

  if (!active) {
    return (
      <div className="empty-state" style={{ margin: "auto 0" }}>
        <p style={{ fontSize: 40, marginBottom: "var(--sp-sm)" }}>⧉</p>
        <p>
          Nhập một bài toán rồi bấm <strong>Phân tích đề bằng AI</strong>,
          <br />
          hoặc chọn một bài trong <strong>danh mục mô phỏng</strong> bên trái.
        </p>
      </div>
    );
  }

  const mod = getSimulation(active.moduleId);
  if (!mod) {
    return <div className="error-banner">Không tìm thấy module "{active.moduleId}".</div>;
  }

  // M8: renderer DẪN XUẤT TỪ CAPABILITY của module (không switch-case theo id).
  // Mode người dùng chọn nhưng module không đáp ứng → rơi an toàn về 2D.
  /* W4B-2V: công tắc dẫn xuất từ CÁCH XEM ĐƯỢC BÀY CHO HỌC SINH, không từ năng
     lực kỹ thuật. Một target dựng được 3D mà không có lý do sư phạm riêng thì
     `learnerFacingModes` trả rỗng ⇒ không công tắc nào được dựng. */
  const modes = learnerFacingModes(mod);
  const mode = effectiveVisualMode(mod, visualMode);
  const Stage = rendererFor(mod, mode) as ComponentType<WorkspaceProps>;
  // M17-RC1 §E — nhãn miền hiển thị cho HỌC SINH, không phải id kỹ thuật.
  // "GENERIC" vô nghĩa với người học (audit trình duyệt bắt được); các miền
  // khác đổi sang tiếng Việt cho nhất quán. Không đổi `mod.domain`.
  function domainBadge(domain: string): string {
    const VI: Record<string, string> = {
      generic: "MÔ PHỎNG THEO MÔ TẢ",
      algorithm: "THUẬT TOÁN",
      network: "MẠNG",
      tree: "CÂY",
      binary: "HỆ CƠ SỐ",
      logic: "LOGIC",
      database: "TRUY VẤN BẢNG",
    };
    return VI[domain] ?? domain.toUpperCase();
  }

  return (
    <section className="card card-elevated workspace-card">
      <div className="workspace-header">
        <span className="eyebrow">{domainBadge(mod.domain)}</span>
        <h2 className="workspace-title">{active.envelope.title}</h2>
        <span className="hint">
          {mod.title} · {MODE_LABEL[mod.interactionMode]} ·{" "}
          {mod.supportedVisualModes.join(" / ").toUpperCase()}
        </span>
        {/* M8: toggle 2D/3D CHỈ khi module thật sự có ≥2 renderer — module 2D-only
            không thấy nút nào. Đổi mode = đổi component vẽ, engine state/timeline/
            prediction giữ nguyên. */}
        <VisualModeToggle modes={modes} mode={mode} onSelect={setVisualMode} />
      </div>
      {/* Suspense: renderer 3D được code-split (React.lazy) — chờ tải chunk
          Three.js thì hiện placeholder; renderer 2D đồng bộ, không suspend. */}
      <Suspense fallback={<div className="empty-state">Đang tải chế độ hiển thị…</div>}>
        <Stage config={active.config} state={active.state} busy={playing} dispatch={dispatch} />
      </Suspense>
      {/* (SHELL-N) Thuyết minh: KHE của shell, chữ của module. Nằm NGOÀI renderer
          nên 2D và 3D tự nhiên kể cùng một câu — không còn hai dòng song song
          phải giữ đồng bộ bằng tay. */}
      <NarrationSlot narration={mod.narrate?.(active.state, active.config) ?? null} />
      {/* M8-PRE-LIP: một UI dự đoán DÙNG CHUNG — module không khai `predict` thì
          không render gì. M8: nằm NGOÀI renderer nên tự nhiên renderer-independent —
          2D hay 3D đều cùng PredictionBar này, không có bản 3D riêng. */}
      {/* `key` theo BƯỚC HIỆN TẠI (đọc qua hợp đồng `timeline`, không thò vào
          state của domain): mỗi bước là một lần mount mới, nên checkpoint LUÔN
          bắt đầu ở trạng thái thu gọn — kể cả khi học sinh rời bước rồi quay
          lại đúng bước đó. Không có nó thì "thu gọn mặc định" chỉ đúng ở lần
          gặp đầu tiên. */}
      {/* INTERACTION-FAMILY W1: module có thể khai rằng bước này ĐÃ được trình
          bày ngay trên sân khấu (vd cụm quét dãy dùng `ScanActionZone`). Khi đó
          shell không dựng UI dùng chung nữa — một cam kết, một hình thức. Module
          không khai thì hành vi giữ nguyên như cũ. */}
      {/* W4B-2U2 §13 — THỬ THÁCH LÀ CHẾ ĐỘ, KHÔNG PHẢI ĐỒ ĐẠC THƯỜNG TRỰC.
       *
       * Trước wave này, hễ module khai `predict` là thanh dự đoán nằm sẵn trong
       * Quan sát ở cả 11 target — nên sản phẩm đọc thành hỏi-đáp dù nó chưa bao
       * giờ chặn playback. Nay `challengeOpen` (trình bày thuần) quyết định BÀY
       * hay không; NĂNG LỰC `predict` và bên chấm `predict.check` không đổi một
       * dòng. Đây là dời TRÌNH BÀY, không dời SỰ THẬT. */}
      {challengeSurfaceVisible(mod, active.state, challengeOpen) && (
        <PredictionBar
          key={mod.timeline ? mod.timeline.currentStep(active.state) : "static"}
          module={mod}
          state={active.state}
          busy={playing}
        />
      )}

      {/* W4B-2Z §20/§23 — LỐI VÀO THỬ THÁCH ĐÃ RỜI KHỎI CỘT NỘI DUNG.
          Nó nay nằm trong dải điều khiển (`SimulationControls`) cùng hàng với
          transport, nên dưới mô hình bớt hẳn một dải toàn chiều ngang. Trước
          đây dù đã là nút nhỏ, nó vẫn CHIẾM một hàng riêng ngay dưới sân khấu —
          mắt vẫn đọc thành MÔ HÌNH → DẢI → DẢI. */}
    </section>
  );
}
