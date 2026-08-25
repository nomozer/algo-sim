import { Suspense, type ComponentType, type CSSProperties } from "react";
import { DOMAIN_BADGE, headerSubtitle } from "./header-identity";
import { getSimulation } from "../simulations/registry";
import {
  effectiveVisualMode,
  learnerFacingModes,
  rendererFor,
} from "../simulations/renderer";
import type {
  ExploreCapability,
  Narration,
  PresentationEntry,
  VisualMode,
  WorkspaceProps,
} from "../simulations/types";
import { rendererFitOf } from "../simulations/renderer-fit";
import { useAppStore } from "../state/store";
import { SimulationInspector } from "./SimulationInspector";
import { Scene3DSection } from "../simulations/domains/geometry/Scene3DSection";

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
  // (M20 W3) Cổng phạm vi sinh HAI hạng mục, và gộp chúng vào "ngoài danh mục"
  // là nói sai theo hai hướng ngược nhau:
  // - out_of_scope: đề thuộc MÔN KHÁC. "Danh mục sẽ được mở rộng dần" ở đây là
  //   một lời hứa sai — hệ sẽ không bao giờ thêm hoá học.
  // - not_simulation_suitable: chủ đề CÓ trong chương trình, chỉ là không có cơ
  //   chế để mô phỏng. Nói "ngoài danh mục" làm học sinh ngồi chờ một thứ không
  //   bao giờ tới, vì chẳng có gì để thêm vào.
  const outOfScope = unsupported.failure_category === "out_of_scope";
  const notSimulatable = unsupported.failure_category === "not_simulation_suitable";
  const eyebrow = insufficient ? "CHƯA ĐỦ DỮ KIỆN"
    : stageShortfall ? "CHƯA DỰNG ĐỦ CÁC BƯỚC"
    : incomplete ? "TÁCH THÀNH TỪNG YÊU CẦU"
    : outOfScope ? "THUỘC MÔN HỌC KHÁC"
    : notSimulatable ? "BÀI NÀY KHÔNG CẦN MÔ PHỎNG"
    : "NGOÀI DANH MỤC MÔ PHỎNG";
  const hint = insufficient
    ? "Bổ sung dữ liệu còn thiếu vào đề rồi gửi lại — dạng bài này hệ có mô phỏng."
    : stageShortfall
    ? "Nêu rõ từng bước cần làm rồi gửi lại — dạng bài nhiều bước này hệ có mô phỏng."
    : incomplete
    ? "Mỗi lần hỏi một yêu cầu (giữ nguyên dữ liệu) để xem đầy đủ từng bước của yêu cầu đó."
    : outOfScope
    ? "AlgoSim chỉ mô phỏng nội dung Tin học THPT — thử một bài về thuật toán, dữ liệu, mạng hoặc web."
    : notSimulatable
    ? "Nội dung này đọc hiểu là đủ. Muốn xem một quá trình chạy từng bước thì cần đề có dữ liệu và thao tác trên dữ liệu."
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

/* W13 — `challengeSurfaceVisible` / `challengeEntry` / `DEFAULT_CHALLENGE` ĐÃ GỠ.
 *
 * Ba hàm này trả lời "có bày bề mặt Thử thách không" và "cửa vào tên là gì".
 * Không còn Thử thách thì không còn câu hỏi nào để trả lời. Lối vào duy nhất
 * còn lại là Khám phá (`exploreEntry` bên dưới) — cùng khuôn hàm thuần, cùng lý
 * do phải thuần: `SimulationWorkspace` đọc store, mà zustand v5 dùng
 * `useSyncExternalStore` nên SSR luôn trả TRẠNG THÁI ĐẦU (`ARCHITECTURE_MAP §8`
 * #8). Test `renderToString(<SimulationWorkspace/>)` sau `loadEnvelope` sẽ thấy
 * empty-state, và mọi khẳng định kiểu "không chứa chuỗi X" sẽ XANH vì màn hình
 * rỗng — xanh vì lý do sai. Luật phải sống ở hàm thuần để kiểm được.
 */

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
 * W4B-4D — MÔ HÌNH ĐÃ RỜI KHỎI ĐỀ CHƯA.
 *
 * Hàm THUẦN, tách khỏi JSX vì đúng lý do đã ghi ở `interaction-policy.ts`: luật
 * chôn trong JSX là luật chỉ kiểm được bằng trình duyệt.
 *
 * So bằng GIÁ TRỊ (JSON) chứ không bằng tham chiếu: mọi `apply` đều dựng config
 * mới, nên so tham chiếu sẽ báo "đã đổi" ngay ở thao tác đầu tiên kể cả khi học
 * sinh vừa đặt lại đúng giá trị cũ. Module không khai `currentConfig` ⇒ `false`:
 * bài không đổi được tham số thì không lệch được.
 *
 * So theo ĐÚNG CÁC KHOÁ module khai, không so cả khối. Lý do cụ thể: `web` giữ
 * kiểu trong state chứ không trong config, nên nó phải dựng lại hình dạng config
 * — và nó không giữ `notes` của đề. So cả khối thì đề nào có `notes` cũng bị
 * báo "đã đổi" ngay khi vừa mở, tức nhãn kêu suốt và học sinh học cách phớt lờ
 * nó. Khoá module không nhắc tới là khoá học sinh không đổi được.
 */
export function specDrift<S>(
  mod: { currentConfig?: (state: S) => unknown },
  state: S,
  baseline: unknown,
): boolean {
  if (!mod.currentConfig) return false;
  try {
    const now = mod.currentConfig(state);
    if (typeof now !== "object" || now === null || typeof baseline !== "object" || baseline === null) {
      return JSON.stringify(now) !== JSON.stringify(baseline);
    }
    const base = baseline as Record<string, unknown>;
    return Object.entries(now as Record<string, unknown>)
      .some(([k, v]) => JSON.stringify(v) !== JSON.stringify(base[k]));
  } catch {
    return false; // config không serialize được ⇒ im lặng, không doạ học sinh
  }
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
  /* Cùng một cờ store như trước, chỉ đổi CHỖ dựng: nút "Giải thích" ở header nay
     thu/mở cột hai của thẻ thay vì bật/tắt một khay riêng của shell. */
  const rightOpen = useAppStore((s) => s.rightOpen);
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
  /* W4B-4D — mô hình đã rời khỏi đề chưa. So bằng GIÁ TRỊ với bản validate bất
     biến; module không khai `currentConfig` thì không có gì để lệch. */
  const driftedFromSpec = specDrift(mod, active.state, active.config);
  const Stage = rendererFor(mod, mode) as ComponentType<WorkspaceProps>;
  // M17-RC1 §E + W5Z — nhãn miền và luật phụ đề nay do `header-identity.ts` sở
  // hữu (hàm thuần ⇒ khoá được bằng test không cần DOM). Không đổi `mod.domain`.
  const subtitle = headerSubtitle(mod.title, active.envelope.title);

  /* W5Y — SÀN BỀ RỘNG SUY THEO TỪNG TARGET, KHÔNG PHẢI HẰNG SỐ.
   *
   * `semanticMaxWidth` = bố cục ở bề rộng vô hạn, tức mức nội dung THẬT SỰ dùng
   * được. Đặt nó làm SÀN: nội dung thích ứng (biểu đồ cột) có chỗ để giãn tới
   * trần mật độ, còn nội dung cố định (4 bit, một cổng AND) KHÔNG bị ép rộng ra
   * — thẻ `fit-content` ôm đúng nó. Đó là "khung theo cơ chế" mà M19 chốt, và là
   * thứ sàn phẳng 1040px của W5Q đã phá: nó ép mọi thẻ về 992px nên `decimal_to
   * _binary` thừa 716px chết (đo được, 6 target cùng bệnh).
   *
   * ⚠️ SÀN chứ không phải TRẦN. `074fea5` dùng đúng con số này làm `max-width`
   * và tính thiếu vài px padding ⇒ cắt mất cột cuối, phải revert. Sàn thì không
   * thể cắt: nội dung luôn được phép vượt qua nó. Cùng một dữ kiện, dùng đúng
   * chiều thì lớp lỗi ấy biến mất. */
  const stageMin = rendererFitOf(mod.id, active.state, mode).semanticMaxWidth;
  const cardStyle = stageMin
    ? ({ "--stage-min": `calc(${stageMin}px + 2 * var(--sp-lg) + 24px)` } as CSSProperties)
    : undefined;

  return (
    <section className="card card-elevated workspace-card" style={cardStyle}>
      <div className="workspace-header">
        <span className="eyebrow">{DOMAIN_BADGE[mod.domain]}</span>
        <h2 className="workspace-title">{active.envelope.title}</h2>
        {/* W5J — DÒNG NÀY NÓI VỀ BÀI HỌC, KHÔNG NÓI VỀ HỆ THỐNG.
            Trước đây nó ghép ba thứ khác loại: tên cơ chế · `interactionMode` ·
            `supportedVisualModes`. Chỉ mảnh ĐẦU có ích cho học sinh — đề nói
            "sổ điểm", cơ chế là "tìm giá trị lớn nhất", và bắc được cây cầu ấy
            chính là bước trừu tượng hoá cần dạy.
            Hai mảnh sau là taxonomy nội bộ rò lên bề mặt: "từng bước" nói lại
            đúng thứ khay điều khiển đã bày (Bước 1/13, thanh tua, nút Tiến), còn
            "2D" là NĂNG LỰC hệ thống — bài nào thật sự có hai cách xem thì đã có
            công tắc "Cách xem" riêng nói hộ.

            W5Z — VÀ KHI NÓ KHÔNG BẮC ĐƯỢC CÂY CẦU NÀO THÌ ĐỪNG DỰNG NÓ. Có đề mà
            đề bài CHÍNH LÀ tên cơ chế ("Cổng logic AND", "Mô hình màu RGB"): khi
            ấy dòng này lặp lại nguyên văn tiêu đề ngay bên dưới tiêu đề, đọc như
            lỗi hiển thị chứ không phải lời giảng. Ẩn nó là việc của SHELL, không
            phải của từng miền — nếu để miền tự lo thì đúng 24 module phải nhớ
            cùng một luật, và đó là cách bề mặt sinh ra "mỗi cái một kiểu". */}
        {subtitle && <span className="hint">{subtitle}</span>}
        {/* W4B-4D — KHI MÔ HÌNH ĐÃ RỜI KHỎI ĐỀ, PHẢI NÓI RA.
            Tiêu đề bên trên là ĐỀ BÀI, không phải mô hình. Từ khi đổi được tham
            số, hai thứ ấy tách nhau: đề viết "từ 8,0 trở lên" còn học sinh vừa
            kéo ngưỡng về 6 — và con số cuối đọc như đáp số của bài gốc. Nhãn
            này là chỗ DUY NHẤT nói ra chênh lệch đó, cho MỌI target, nên không
            miền nào phải tự nhớ. */}
        {driftedFromSpec && (
          <span className="spec-drift" title="Bấm Đặt lại để quay về đúng đề bài.">
            Đã đổi so với đề bài
          </span>
        )}
        {/* M8: toggle 2D/3D CHỈ khi module thật sự có ≥2 renderer — module 2D-only
            không thấy nút nào. Đổi mode = đổi component vẽ, engine state/timeline/
            prediction giữ nguyên. */}
        <VisualModeToggle modes={modes} mode={mode} onSelect={setVisualMode} />
      </div>
      {/* Suspense: renderer 3D được code-split (React.lazy) — chờ tải chunk
          Three.js thì hiện placeholder; renderer 2D đồng bộ, không suspend. */}
      {/* W5AC — GIẢI THÍCH LÀ CỘT HAI CỦA THẺ, KHÔNG PHẢI KHAY THỨ BA.
          Trước wave này nó là `aside.panel-right` rộng CỐ ĐỊNH 300px ở shell. Ba
          điều đo được nói rằng chỗ đó sai: (a) 300px hẹp hơn chính nội dung của
          nó — bảng chân trị 4 cột bị cụt; (b) nó giành đúng phần bề ngang mà sân
          khấu đang đói (thẻ kẹt 560–674px trong màn 1536); (c) nó là VÙNG THỨ BA
          cạnh sidebar + sân khấu, nên mắt phải nhảy qua một rãnh và một đường
          viền để nối cơ chế với biểu diễn hình thức của nó.
          Đặt cạnh nhau trong CÙNG một khung nhìn chính là bước bắc cầu cần dạy —
          và nhờ cột hai có nội dung thật, thẻ rộng ra bằng nội dung chứ không
          phải bằng khoảng trắng. */}
      <div className={`workspace-body${rightOpen ? " has-explain" : ""}`}>
        <Suspense fallback={<div className="empty-state">Đang tải chế độ hiển thị…</div>}>
          <Stage config={active.config} state={active.state} busy={playing} dispatch={dispatch} />
        </Suspense>
        {rightOpen && (
          <div className="workspace-explain">
            <SimulationInspector />
          </div>
        )}
      </div>
      {/* (SHELL-N) Thuyết minh: KHE của shell, chữ của module. Nằm NGOÀI renderer
          nên 2D và 3D tự nhiên kể cùng một câu — không còn hai dòng song song
          phải giữ đồng bộ bằng tay. */}
      <NarrationSlot narration={mod.narrate?.(active.state, active.config) ?? null} />
      {/* (5F) QUÁ TRÌNH DỰNG HÌNH 3D — vùng THÊM VÀO, không thay renderer nào.
          Chỉ hiện khi envelope mang `scene3d`, tức khi một chương trình hình
          học đã đi trọn chuỗi sinh → thẩm định → thực thi. Bài Tin học không có
          khoá ấy nên không thấy gì đổi; component tự trả `null`. */}
      <Scene3DSection scene={(active.envelope as { scene3d?: unknown }).scene3d} />
      {/* W13 — KHÔNG CÒN THANH DỰ ĐOÁN Ở ĐÂY.
          Chỗ này từng là `PredictionBar`: một câu hỏi + các lựa chọn + phán
          quyết đúng/sai, dựng khi module khai `predict`. Năng lực ấy đã gỡ hẳn —
          học sinh tác động lên mô hình qua Khám phá (`explore` → `apply`) và
          đọc hệ quả tất định, không ai chấm điểm. */}
    </section>
  );
}
