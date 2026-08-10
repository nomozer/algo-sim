import { useState } from "react";
import { ArrayView, arrayLegendItems } from "../../../components/ArrayView";
import { StageLegend } from "../../../components/StageLegend";
import { VarsView } from "../../../components/VarsView";
import { PseudocodeView } from "../../../components/PseudocodeView";
import { POSITION_VARS } from "../../../core/pseudocode";
import { AnalysisCard } from "../../../components/AnalysisCard";
import { fmt } from "../../../core/trace-builder";
import type { WorkspaceProps } from "../../types";
import {
  consequenceOf,
  decisionPointOf,
  scanInteractionOf,
  searchInteractionOf,
  searchSceneRegions,
  sortInteractionOf,
} from "./decision";
import { ScanActionZone } from "../../../components/ScanActionZone";
import { SearchActionZone, SearchStateView } from "../../../components/SearchActionZone";
import { SortActionZone } from "../../../components/SortActionZone";
import { useAppStore } from "../../../state/store";
import {
  commitmentSurfaceKind,
  commitmentSurfaceVisible,
  whatIfDragAllowed,
  whatIfPolicyOf,
} from "./interaction-policy";
import { activeTrace, clampStep, type AlgorithmConfig, type AlgorithmSimState } from "./model";
import {
  IconBack,
  IconInfo,
  IconCheck,
  IconExperiment,
  IconPredict,
  IconSearch,
} from "../../../components/icons";

/**
 * UI adapter của domain algorithm — nơi DUY NHẤT được biết trace/mảng/mã giả.
 * Chỉ đọc state + phát SimAction qua dispatch — không business logic (M2 #3).
 *
 * M9-S1:
 * - Kéo-thả what-if KHÔNG còn bật đồng loạt: bật/tắt theo `whatIfPolicyOf`
 *   (free/framed/challenge/hidden) — tương tác phải nhắm cơ chế ẩn.
 * - Mode "challenge": ẩn mặc định; học sinh chủ động mở THÍ NGHIỆM có khung
 *   (phá bất biến vùng-đã-duyệt / phá tiền điều kiện dãy-đã-sắp).
 * - Dải nhân quả (decision strip): ở điểm quyết định nêu "đang xét gì + phép
 *   so sánh nào"; ở bước hệ quả nêu câu nhân quả với số liệu thật — CÙNG nguồn
 *   `decision.ts` với ô dự đoán nên các biểu diễn không lệch nhau.
 */

/* ── SẮP XẾP CHÈN: GIÁ TRỊ ĐANG GIỮ + Ô TRỐNG (INSERT-HOLD) ──────────────
 *
 * Vì sao có khối này: audit cơ chế bắt được sân khấu hiện dãy `[3, 7, 7, 9, 8, 2]`
 * — số `7` xuất hiện HAI lần và giá trị đang chèn (`4`) biến mất khỏi dãy. Với
 * học sinh, đó đọc thành "thuật toán nhân bản phần tử rồi làm mất một phần tử".
 *
 * Sự thật của engine thì không như vậy, và engine ĐÃ ghi đủ:
 * - `vars.gia_tri_chen` = quân bài đang cầm trên tay;
 * - `snapshot.ids` là HOÁN VỊ định danh, và `setIdAt(j, keyId)` giữ định danh
 *   của quân bài đang cầm ĐÚNG tại Ô TRỐNG. Vị trí đó vẫn còn giá trị cũ trong
 *   `array` (bản sao còn sót của phần tử vừa dời sang phải) — nên nếu renderer
 *   chỉ đọc `array` thì thấy số lặp lại.
 *
 * Nên đây KHÔNG phải sửa engine: chỉ là renderer bắt đầu đọc `ids` — thứ engine
 * đã duy trì sẵn — để vẽ ô trống, và vẽ quân bài đang cầm ra khu vực riêng.
 */
interface InsertionHold {
  /** Giá trị đang cầm (đã rút khỏi dãy). */
  key: number;
  /** Vị trí ô trống trong dãy — chỗ giá trị vừa bị rút ra / vừa dời khỏi. */
  gapIndex: number;
}

export function insertionHold(state: AlgorithmSimState, cursor: number): InsertionHold | null {
  const trace = activeTrace(state);
  const step = trace.steps[cursor];
  if (!step) return null;
  // Bước CHÈN: quân bài đã đáp xuống → không còn cầm, không còn ô trống.
  if (step.events.some((e) => e.type === "insert")) return null;

  const key = step.snapshot.vars["gia_tri_chen"];
  if (typeof key !== "number") return null;

  // Đầu lượt: bước gần nhất có `assign_var gia_tri_chen`.
  let start = -1;
  for (let i = cursor; i >= 0; i -= 1) {
    if (trace.steps[i].events.some((e) => e.type === "assign_var" && e.name === "gia_tri_chen")) {
      start = i;
      break;
    }
  }
  if (start < 0) return null;

  // Vị trí rút quân bài: engine gửi kèm trong sự kiện của lượt này —
  // `compare.j` là chỉ số gốc của quân bài, `insert.index` dùng khi không phải dời.
  let pickIndex: number | null = null;
  for (let i = start; i < trace.steps.length; i += 1) {
    for (const ev of trace.steps[i].events) {
      if (ev.type === "compare") { pickIndex = ev.j; break; }
      if (ev.type === "insert") { pickIndex = ev.index; break; }
    }
    if (pickIndex !== null) break;
  }
  if (pickIndex === null) return null;

  const keyId = trace.steps[start].snapshot.ids[pickIndex];
  const gapIndex = step.snapshot.ids.indexOf(keyId);
  if (gapIndex < 0) return null;
  return { key, gapIndex };
}

type Props = WorkspaceProps<AlgorithmConfig, AlgorithmSimState>;

export function AlgorithmWorkspace({ config, state, busy, dispatch }: Props) {
  const trace = activeTrace(state);
  const step = trace.steps[clampStep(state, state.cursor)];
  const last = state.cursor >= trace.steps.length - 1;
  const doneEvent = step.events.find((e) => e.type === "done");

  const policy = whatIfPolicyOf(config.algorithm_id);
  // Thí nghiệm (mode "challenge") do học sinh CHỦ ĐỘNG mở — state trình bày cục bộ.
  const [labOpen, setLabOpen] = useState(false);

  /* W4B-2B §5 — CỔNG THÍ NGHIỆM, DẪN XUẤT TỪ POLICY, KHÔNG TỪ `algorithm_id`.
   *
   * `experimentGated` là cờ KHAI BÁO ở `interaction-policy.ts`. Ở đây chỉ đọc —
   * không có `if (moduleId === "algorithm.find_max")` nào trong shell, đúng
   * anti-pattern #2 (mọi quyết định suy từ capability/cấu trúc, không từ tên bài).
   *
   * Cổng áp cho HAI thứ, và đó là điểm mới của wave này:
   *  - kéo-thả (trước nay `mode: "challenge"` đã gác);
   *  - VÙNG CAM KẾT (`ScanActionZone`/`SortActionZone`) — trước nay render vô
   *    điều kiện mỗi khi bước là điểm quyết định.
   */
  const gated = policy.experimentGated === true;
  /** Bài nào có nút "Thí nghiệm": bài gác cổng, hoặc bài `challenge` sẵn có. */
  const hasExperiment = gated || policy.mode === "challenge";
  /**
   * Vùng cam kết chỉ ẩn ở bài ĐƯỢC GÁC. Bài khác giữ nguyên hành vi cũ —
   * đây là pilot hai bài, không phải rollout cả họ (§25).
   */
  const commitmentVisible = commitmentSurfaceVisible(policy, labOpen);

  const dragAllowedByPolicy =
    policy.mode === "hidden"
      ? false
      : policy.mode === "challenge" || gated
        ? labOpen
        : true;

  const decision = decisionPointOf(state);
  const consequence = decision ? null : consequenceOf(state);
  const hold = insertionHold(state, clampStep(state, state.cursor));
  const scan = scanInteractionOf(state);
  const search = searchInteractionOf(state);
  const sort = sortInteractionOf(state);

  /* Nhánh DỰ ĐOÁN (không phải state canonical) đọc/ghi qua store — đúng khuôn
     `PredictionBar` đã dùng từ M8-PRE-LIP: kết quả chấm sống ở `store.prediction`,
     `active.state` không hề bị đụng tới. */
  const prediction = useAppStore((s) => s.prediction);
  const submitPrediction = useAppStore((s) => s.submitPrediction);

  // Luật kéo-vs-cam-kết (W3B §15) sống ở `interaction-policy.ts` — hàm thuần,
  // kiểm được không cần trình duyệt. Ở đây chỉ cung cấp dữ kiện thời điểm.
  const canDrag = whatIfDragAllowed(state, {
    policyAllows: dragAllowedByPolicy,
    busy,
    last,
    answered: prediction !== null,
  });

  /* Đúng MỘT mô hình tương tác sống ở một bước (`stageInteractionsOf`), nên
     chọn ở đây thay vì dựng ba nhánh JSX song song. `chrome` dẫn xuất từ
     `gated` — capability, không phải tên bài. */
  const zoneProps = {
    answered: prediction !== null,
    busy,
    onAct: (actionId: string) => submitPrediction(actionId),
    feedback: prediction,
    showPrompt: !gated,
    chrome: (gated ? "tool" : "panel") as "tool" | "panel",
  };

  /* W4B-2I — HÀNH ĐỘNG VỀ ĐÚNG CHỖ NÓ TÁC ĐỘNG.
   *
   * Vùng bấm chỉ dựng khi vùng cam kết ĐANG được phép hiện: nó LÀ vùng cam kết,
   * chỉ khác hình thức. Dựng nó ở Quan sát sẽ là đúng thứ cổng sinh ra để chặn.
   *
   * `searchSceneRegions` trả `null` khi không gắn được (nửa rỗng, hai hành động
   * trùng cột) ⇒ hàng nút cũ quay lại nguyên vẹn cho bước đó. Không có trạng
   * thái lai nửa-vùng-nửa-nút. */
  const sceneRegions =
    search && commitmentVisible
      ? searchSceneRegions(search, config.data.array.length)
      : null;
  /* Hình thức bề mặt cam kết do HÀM THUẦN quyết, không do JSX — xem lý do ở
     `commitmentSurfaceKind` (một lần tiêm lỗi đã đi lọt vì luật nằm trong JSX). */
  const surface = commitmentSurfaceKind(commitmentVisible, sceneRegions !== null);

  const commitZone = !commitmentVisible
    ? null
    : scan
      ? <ScanActionZone model={scan} {...zoneProps} />
      : search
        ? <SearchActionZone model={search} {...zoneProps} actionsHidden={surface === "scene"} />
        : sort
          ? <SortActionZone model={sort} {...zoneProps} />
          : null;

  return (
    <div className="stack" style={{ gap: "var(--sp-md)" }}>
      {state.branch && (
        <div className="branch-banner">
          {/* Framing (vì sao thử) đã hiện TRƯỚC khi mở thí nghiệm — không lặp lại
              ở đây để banner gọn, chỉ nói em vừa làm gì + lối quay về. */}
          <span>
            <IconExperiment size={14} /> <strong>Nhánh thử nghiệm</strong> — em đã đổi chỗ vị trí thứ {state.branch.i + 1}{" "}
            và {state.branch.j + 1} tại bước {state.branch.fromStep + 1}. Dòng chính vẫn được giữ
            nguyên.
          </span>
          <button className="btn-utility" onClick={() => dispatch({ type: "exit_branch" })}>
            <IconBack size={14} />
            Quay về dòng chính
          </button>
        </div>
      )}

      <div className="sim-stage">
        {/* INSERT-HOLD: quân bài đang cầm nằm NGOÀI dãy, đúng như thao tác thật —
            và ô nó để lại trong dãy là ô TRỐNG, không phải một số lặp lại. */}
        {hold && (
          <div className="hold-tray">
            <span className="hold-label">Đang giữ</span>
            <span className="hold-value">{fmt(hold.key)}</span>
            {/* W4B-2D §4: `gapIndex` là chỉ số 0-based của engine; thuyết minh
                của chính bước này đã nói "ô trống lùi về vị trí j+1". In thô ở
                đây là hai số cho CÙNG một ô trên CÙNG một màn hình. */}
            <span className="hold-note">
              đã rút khỏi dãy — ô trống ở vị trí {hold.gapIndex + 1}
            </span>
          </div>
        )}
        <ArrayView
          step={step}
          labels={config.data.labels}
          interactive={canDrag}
          onSwap={(i, j) => dispatch({ type: "whatif_swap", i, j })}
          gapIndex={hold?.gapIndex ?? null}
          regions={sceneRegions}
          /* Cùng đường nộp với hàng nút: `submitPrediction` → `predict.check`.
             Sân khấu KHÔNG tự chấm, không có bên chấm thứ hai. */
          onRegionAct={(actionId) => submitPrediction(actionId)}
          regionsDisabled={busy || prediction !== null}
        />
        {/* Chú giải suy TỪ TRACE (không phải từ bước hiện tại) nên nó đứng yên
            suốt timeline. Trước W1 nó gắn với `hold` — tức chỉ hiện ở sắp xếp
            chèn, và biến mất ngay khi quân bài đáp xuống. */}
        <StageLegend
          items={arrayLegendItems(trace.steps, {
            algorithmId: config.algorithm_id,
            hasGap: hold !== null,
          })}
        />
      </div>

      {/* W4B-2V — TRẠNG THÁI QUAN SÁT ĐỨNG NGOÀI CỔNG.
          Điều kiện là `search` thuần, KHÔNG kèm `commitmentVisible`: cổng gác
          quyền hành động, không gác thông tin về cơ chế. */}
      {search && <SearchStateView model={search} relation={decision?.expression ?? null} />}

      {/* W4B-2V/C2 — MỘT KHỐI CAM KẾT, BỌC TRONG CÔNG CỤ KHI ĐÃ GÁC CỔNG.
       *
       * Trước đây ba họ dựng ba `<section className="action-zone">` rời, và
       * `.action-zone` là một THẺ: `background: canvas-soft` + `border` +
       * `padding md lg` + `flex-direction: column`, trên phần tử block ⇒ trải
       * gần hết bề ngang. Rút chữ ở wave trước làm nó NHỎ HƠN nhưng vẫn là một
       * tấm nội dung thứ hai. Đây mới là chỗ phải đổi.
       *
       * Ba mô hình loại trừ nhau (bất biến COMMITMENT_SURFACE_COUNT ≤ 1), nên
       * gom được thành một biểu thức — và nhờ vậy CHỈ MỘT chỗ quyết định
       * "chrome nào": bài gác cổng dùng chrome CÔNG CỤ, bài chưa gác giữ nguyên
       * thẻ cũ (chúng không có Thí nghiệm; vùng cam kết của chúng là một phần
       * thường trực của Quan sát).
       */}
      {commitZone && (gated ? (
        <div
          className="experiment-tool"
          role="group"
          /* `framing` không còn là một HÀNG chữ; nó thành TÊN KHẢ TRUY CẬP của
             công cụ. Người dùng đọc màn hình vẫn nghe được mục đích, người nhìn
             thì đọc thẳng nhãn nút — không ai phải đọc hai lần. */
          aria-label={policy.framing}
        >
          <IconExperiment size={14} />
          {commitZone}
          {canDrag && policy.hint && (
            /* §13 — phân biệt CAM KẾT ↔ WHAT-IF không được mất, nhưng cũng
               không được chiếm một hàng chữ full-width. Chip nhỏ, nội dung đầy
               đủ nằm ở `title` + `aria-label`. */
            <span className="experiment-tool-note" title={policy.hint} aria-label={policy.hint}>
              <IconInfo size={12} /> what-if
            </span>
          )}
          <button
            className="btn-utility experiment-tool-close"
            onClick={() => setLabOpen(false)}
            aria-label="Đóng thí nghiệm"
            aria-expanded
          >
            ×
          </button>
        </div>
      ) : commitZone)}

      {/* Dải nhân quả — cùng nguồn decision.ts với ô dự đoán (M9-S1 §4, §8).
          KHÔNG dựng khi đã có vùng hành động: `ScanActionZone` mang sẵn state
          line và phép so sánh, bày cả hai là lặp đúng thứ W1 vừa gỡ (test
          `ui-clarity-w1` bắt được ngay khi tôi thử).

          W4B-2B: điều kiện đọc VÙNG ĐANG HIỆN, không đọc "bước có phải điểm
          quyết định". Ở bài gác cổng, Quan sát ẩn vùng cam kết — nếu vẫn tắt dải
          này theo `scan !== null` thì học sinh mất luôn QUAN HỆ đang được xét
          ("Dũng — vị trí 4", "8 > 9 ?"), tức là cổng Thí nghiệm vô tình lấy đi
          một dữ kiện thuần quan sát. Quan hệ thuộc về Quan sát; chỉ NÚT CAM KẾT
          mới thuộc về Thí nghiệm. */}
      {/* W4B-2V — DẢI NHÂN QUẢ KHÔNG DỰNG CHO HỌ TÌM KIẾM NỮA.
          W4B-2D dùng `!(search && commitmentVisible)`, tức quan hệ hiện ở Quan
          sát rồi BIẾN MẤT khi mở Thí nghiệm — dải tắt, mà vùng cam kết không hề
          mang `expression`. Đó là cùng một lỗi ở chiều ngược lại: một dữ kiện
          quan sát bị buộc vào công tắc của cổng. Nay `SearchStateView` là chủ
          sở hữu DUY NHẤT của quan hệ ở họ này — luôn hiện, và không có hai kênh
          nói cùng một điều. Tiền đề cũng đã về đó, nên khối
          `SearchPrecondition` độc lập của W4B-2D không còn cần.
          Scan/sort giữ nguyên hành vi cũ. */}
      {decision && !(scan && commitmentVisible) && !search && !(sort && commitmentVisible) && (
        <div className="decision-strip">
          <span className="decision-consideration">
            <IconSearch size={14} />
            {decision.consideration}
          </span>
          <strong className="decision-expression">{decision.expression}</strong>
        </div>
      )}
      {consequence && (
        <div className="decision-strip is-consequence">
          <span>
            <IconPredict size={14} />
            {consequence}
          </span>
        </div>
      )}

      {/* (SHELL-N) Thuyết minh đã chuyển lên khe của shell — xem `narrate` ở
          `index.ts`. Renderer không còn dựng dòng này. */}

      {last && doneEvent && doneEvent.type === "done" && (
        <div className="result-banner">
          <IconCheck size={15} /> {doneEvent.result}
          {state.branch && (
            <span style={{ display: "block", fontWeight: 400, marginTop: 4 }}>
              (kết quả của nhánh thử nghiệm — dãy gốc: [
              {state.trace.steps[state.trace.steps.length - 1].snapshot.array.map(fmt).join("; ")}
              ])
            </span>
          )}
        </div>
      )}

      {/* Mode "challenge": nút mở thí nghiệm có khung — không kéo tự do mặc định.
          PhET/CLT: teaser hiện TRƯỚC nút để affordance tự giải thích (giảm tải
          "nút bí ẩn"), không lộ hệ quả — hệ quả để dành `framing` khi đã mở. */}
      {/* CỔNG THÍ NGHIỆM — §8.
          Teaser GIỮ NGUYÊN ở trạng thái chưa mở: đó là bất biến PhET/CLT có test
          riêng (`algorithm-ui.test.tsx` — "nút không còn bí ẩn"), và §8 đòi cổng
          phải DISCOVERABLE. Bỏ nó đi là đọc §7 quá rộng: thứ §7 cấm ở Quan sát là
          bề mặt CAM KẾT, không phải lời mời khám phá. */}
      {/* W4B-2V/C2 — CỔNG LÀ MỘT NÚT MÔ TẢ, KHÔNG KÈM HÀNG CHỮ RIÊNG.
          Nhãn nút đã tự nói năng lực ("Thí nghiệm: tự chọn nửa để tìm tiếp"),
          nên teaser không cần một hàng nữa; nó thành `title` — vẫn tới được
          chuột và công nghệ hỗ trợ, không tốn một dòng bố cục. Bất biến giữ
          nguyên: cổng phải TỰ MÔ TẢ, không được là nút bí ẩn. */}
      {hasExperiment && !labOpen && !state.branch && !last && (
        <button
          className="btn-utility experiment-trigger"
          onClick={() => setLabOpen(true)}
          title={policy.challengeTeaser}
          aria-expanded={false}
        >
          <IconExperiment size={14} />
          {policy.challengeLabel}
        </button>
      )}
      {/* Gợi ý kéo KHÔNG được mời làm việc đang bị khoá, và sau khi đã cam kết
          thì phải nói rõ kéo là THỬ NGHIỆM — khác hẳn việc vừa làm bằng nút. */}
      {canDrag && sort && prediction !== null && (
        <span className="hint">
          Em có thể kéo hai cột để THỬ một nhánh khác — đó là thí nghiệm, không
          phải bước của thuật toán.
        </span>
      )}
      {/* Bài CHƯA gác cổng không có công cụ để gắn chip what-if vào, nên giữ
          hàng gợi ý như cũ. Bài gác cổng đã có chip trong `.experiment-tool`. */}
      {canDrag && !sort && !gated && policy.hint && <span className="hint">{policy.hint}</span>}
    </div>
  );
}

export function AlgorithmInspector({ config, state }: Props) {
  const trace = activeTrace(state);
  const step = trace.steps[clampStep(state, state.cursor)];
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <AnalysisCard analysis={config} />
      {/* W4B-2B §9: panel chia mục rõ — "BIẾN" đứng cạnh "THUẬT TOÁN" của khối
          mã giả. Nhãn do `VarsView` dựng nên bước không có biến thì mất cả mục. */}
      {/* W4B-2D §4: chip vị trí đếm từ 1 để khớp mã giả 1-based ngay bên dưới —
          khai báo ở `POSITION_VARS`, không phải suy từ tên biến (xem chú thích
          tại nguồn: `program`/`scan` để ĐỀ BÀI đặt tên biến). */}
      <VarsView step={step} label="BIẾN" positionVars={POSITION_VARS[config.algorithm_id]} />
      <PseudocodeView algorithmId={config.algorithm_id} currentLine={step.line} />
    </div>
  );
}
