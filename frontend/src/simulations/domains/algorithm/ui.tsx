import { ArrayView, arrayLegendItems } from "../../../components/ArrayView";
import { StageLegend } from "../../../components/StageLegend";
import { VarsView } from "../../../components/VarsView";
import { PseudocodeView } from "../../../components/PseudocodeView";
import { POSITION_VARS } from "../../../core/pseudocode";
import { AnalysisCard } from "../../../components/AnalysisCard";
import { fmt } from "../../../core/trace-builder";
import type { WorkspaceProps } from "../../types";
import {
  accumulatorViewOf,
  consequenceOf,
  decisionPointOf,
  scanInteractionOf,
  searchInteractionOf,
  sortInteractionOf,
} from "./decision";
import { ScanActionZone } from "../../../components/ScanActionZone";
import { SearchStateView } from "../../../components/SearchStateView";
import { SortActionZone } from "../../../components/SortActionZone";
import {
  CONDITION_OPS,
  CONDITION_OP_LABEL,
  hasCondition,
  thresholdRange,
} from "./condition-param";
import {
  whatIfDragAllowed,
  whatIfPolicyOf,
} from "./interaction-policy";
import { activeTrace, clampStep, type AlgorithmConfig, type AlgorithmSimState } from "./model";
import { toolAffordanceOpen } from "../../tool-affordance";
import {
  IconBack,
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

  /* W4B-3A — CỜ CHẾ ĐỘ SỐNG Ở STORE, LỐI VÀO DO SHELL DỰNG.
   *
   * Trước wave đó nó là `useState` cục bộ tên `labOpen` và nút mở do chính file
   * này dựng — nên dưới sân khấu luôn thừa một dải `experimentTrigger`, và
   * chuyển phiên là mất chế độ đang mở.
   *
   * Nay cờ sống ở store (mù domain, theo phiên) và lối vào do
   * `SimulationControls` dựng. Chỗ này chỉ ĐỌC — đúng phân vai: shell sở hữu
   * "có mở không", renderer miền sở hữu "mở ra thì thấy bộ điều khiển gì".
   *
   * W13 — trước đây có cờ thứ hai (`challengeOpen`) cho chế độ Thử thách, tách
   * ra vì Thử thách đưa cam kết qua `predict.check` để engine PHÁN đúng/sai còn
   * Khám phá đưa thao tác qua `module.apply` và không phán gì. Thử thách đã gỡ,
   * nên chỉ còn một cờ và không còn hai loại thao tác để lẫn với nhau.
   */

  /* W13 — DẢI DỮ KIỆN CƠ CHẾ LÀ THƯỜNG TRỰC.
   *
   * `commitmentSurfaceVisible(policy, challengeOpen)` từng giấu dải này sau cổng
   * Thử thách, vì hồi đó nó CHỞ HAI NÚT CAM KẾT — bày sẵn thì màn mặc định đọc
   * thành một câu hỏi. Nay nút đã gỡ, thứ còn lại thuần tuý là *engine đang so
   * cặp nào, giá trị bao nhiêu, cần sắp theo chiều nào*.
   *
   * Thông tin ấy KHÔNG được giấu: nó là trạng thái cơ chế, và
   * `SIMULATION_SURFACE_COMPOSITION_CONTRACT §EXPLAIN` đòi đóng panel lại thì
   * học sinh vẫn phải nhận ra "cái gì đang hoạt động · vừa đổi gì". Giấu nó đi
   * là bắt học sinh xem một hoạt hình không giải thích được.
   */

  /* W4B-3A — KÉO THUỘC VỀ KHÁM PHÁ, KHÔNG THUỘC VỀ THỬ THÁCH.
   *
   * `mode` giữ nguyên trách nhiệm cũ: nó trả lời "kéo ở bài này có nhắm cơ chế
   * không" (`hidden` = trang trí ⇒ không bày, bất kể chế độ nào đang mở). Chỗ
   * ĐẶT thì nay là chế độ Khám phá — nơi thao tác đi qua `apply` và không ai
   * chấm điểm.
   *
   * Hành vi ship KHÔNG đổi: cả 9 bài đều `experimentGated`, nên trước wave này
   * kéo cũng đã nằm sau một cổng; nay cổng đó có tên đúng và có chủ sở hữu
   * dùng chung.
   */
  /* W12 §6 (Policy B) — kéo KHÔNG còn đòi mở Khám phá trước.
     Trước wave này cổng là `exploreOpen`, nên affordance chính của họ thuật
     toán nằm sau một nút mà học sinh phải biết bấm; đo được 52/92 dòng ma trận
     bề rộng đọc ra "không có affordance". Nay điều kiện là THỬ THÁCH ĐANG ĐÓNG:
     công cụ dùng được ngay, và chỉ nhường chỗ khi có một câu hỏi đang chờ. */
  /* W12 §6 (Policy B) — cùng luật, cùng chủ sở hữu với miền mạng.
     `mode: "hidden"` vẫn thắng tuyệt đối: ở `sum_if`/`count_if` kéo là trang
     trí (thuật toán không đổi chỗ gì), nên công cụ của hai bài đó là ĐIỀU KIỆN,
     không phải cột. */
  const dragAllowedByPolicy = policy.mode === "hidden"
    ? false
    : toolAffordanceOpen({ busy });

  const decision = decisionPointOf(state);
  const consequence = decision ? null : consequenceOf(state);
  const hold = insertionHold(state, clampStep(state, state.cursor));
  const scan = scanInteractionOf(state);
  const accumulator = accumulatorViewOf(state);
  const search = searchInteractionOf(state);
  const sort = sortInteractionOf(state);

  // Luật kéo (W3B §15) sống ở `interaction-policy.ts` — hàm thuần, kiểm được
  // không cần trình duyệt. Ở đây chỉ cung cấp dữ kiện thời điểm.
  const canDrag = whatIfDragAllowed(state, {
    policyAllows: dragAllowedByPolicy,
    busy,
    last,
  });

  /* W13 — DẢI DỮ KIỆN, KHÔNG CÒN VÙNG CAM KẾT.
   *
   * Đúng MỘT mô hình tương tác sống ở một bước (`stageInteractionsOf`), nên chọn
   * ở đây thay vì dựng ba nhánh JSX song song.
   *
   * Ba component này trước đây chở *tiêu đề + chip dữ kiện + hai nút cam kết +
   * dòng phán quyết*. Nay chỉ còn nửa đầu, nên `answered`/`onAct`/`feedback`/
   * `showPrompt` đều hết đối tượng. `chrome` ở lại vì nó là HÌNH HỌC (thẻ có nền
   * hay một hàng inline), không phải ngữ nghĩa. */
  const stripProps = { chrome: "panel" as const };

  /* Họ TÌM KIẾM không có mặt ở đây, và đó là kết quả chứ không phải sót:
     `SearchActionZone` sau khi gỡ nút thì RỖNG — W4B-2V đã dời toàn bộ dữ kiện
     quan sát của họ này sang `SearchStateView` (dựng riêng bên dưới), nên phần
     còn lại của nó thuần tuý là quyền hành động được chấm. Component đã xoá. */
  const factStrip = scan
    ? <ScanActionZone model={scan} {...stripProps} />
    : sort
      ? <SortActionZone model={sort} {...stripProps} />
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
        {/* W4B-2U2 §12 — BIẾN TÍCH LUỸ SỐNG TRÊN SÂN KHẤU.
            Trước wave này nó chỉ nằm trong vùng hành động, nên chuyển tiếp
            `4 → 5` phải đọc chữ mới biết (TRANSITION = TEXT_ONLY trong audit).
            Giá trị "trước" lấy từ bước ĐÃ QUA — lịch sử, không phải bước sau,
            nên không lộ đáp án của điểm quyết định đang hỏi. */}
        {accumulator && (
          <div className={`acc-badge${accumulator.changed ? " is-changed" : ""}`}>
            <span className="acc-label">{accumulator.label}</span>
            {accumulator.changed && accumulator.previous !== null && (
              <>
                <span className="acc-prev">{accumulator.previous}</span>
                <span className="acc-arrow" aria-hidden="true">→</span>
              </>
            )}
            <strong className="acc-value">{accumulator.value}</strong>
          </div>
        )}
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
          Nguyên tắc ấy nay áp cho MỌI dải: cổng từng gác quyền hành động, không
          gác thông tin về cơ chế — và W13 gỡ nốt cổng. */}
      {search && <SearchStateView model={search} relation={decision?.expression ?? null} />}

      {/* W13 — DẢI DỮ KIỆN CƠ CHẾ, THƯỜNG TRỰC, KHÔNG BỌC TRONG KHAY NÀO.
       *
       * Trước đây khối này bị bọc trong `.experiment-tool` kèm một nút `×` đóng
       * Thử thách, vì nó CHỞ CAM KẾT — mà cam kết thì phải có đường thoát. Nay
       * nó chỉ nói *engine đang so cặp nào*, tức trạng thái cơ chế: không có gì
       * để thoát, và một cái khay có nút đóng quanh nó chỉ dạy học sinh rằng
       * thông tin này là tuỳ chọn.
       *
       * Ba mô hình loại trừ nhau (bất biến COMMITMENT_SURFACE_COUNT ≤ 1) nên vẫn
       * là một biểu thức, một chỗ quyết định hình thức. */}
      {factStrip}

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
      {/* W13 — ĐIỀU KIỆN NAY ĐỌC "DẢI DỮ KIỆN CÓ ĐANG DỰNG KHÔNG", hết phụ thuộc
          vào cổng. Trước đây nó là `!(scan && commitmentVisible)`, tức cùng một
          quan hệ lúc hiện lúc không tuỳ theo Thí nghiệm đang mở hay đóng — một
          dữ kiện thuần quan sát bị buộc vào công tắc của cổng. Cổng đã gỡ, nên
          luật còn đúng một câu: dải nhân quả KHÔNG dựng khi đã có bề mặt khác
          nói cùng điều đó (`ScanActionZone`/`SortActionZone` mang sẵn phép so
          sánh; `SearchStateView` là chủ sở hữu quan hệ ở họ tìm kiếm). Không bao
          giờ hai kênh nói một điều. */}
      {decision && !scan && !search && !sort && (
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

      {/* W4B-3A — CỔNG ĐÃ RỜI KHỎI ĐÂY.
       *
       * Trước wave này chính chỗ này dựng nút "Thí nghiệm: …" và nó là dải
       * `experimentTrigger` mà bốn lượt đo bố cục đều bắt được: dưới sân khấu
       * xếp `legend → narration → experimentTrigger` (bandCount 3 ở cả 8 target
       * thuật toán, cả bốn bề rộng).
       *
       * Nút KHÔNG bị xoá, nó ĐỔI CHỦ: `SimulationControls` dựng nó trong dải
       * hành động phụ cạnh transport, nhãn vẫn là nhãn của bài này (module cấp
       * qua `predict.entry` / `explore.entry`, dẫn xuất từ `algorithm_id`). Bất
       * biến PhET/CLT giữ nguyên — cổng vẫn TỰ MÔ TẢ, teaser vẫn đi kèm, chỉ
       * không còn chiếm một dải toàn chiều ngang dưới mô hình.
       */}
      {/* W13 — MỘT hàng gợi ý, không còn hai.
       *
       * Trước đây chỗ này có hai `.hint` loại trừ nhau: một câu cho trạng thái
       * "đã cam kết xong, kéo giờ là thí nghiệm", một câu cho "chỉ mở Khám phá".
       * Phân biệt ấy chỉ tồn tại vì kéo phải sống cạnh một hành động ĐƯỢC CHẤM;
       * bỏ chấm thì kéo luôn mang đúng một nghĩa — thử một nhánh khác và xem hệ
       * quả — nên một câu là đủ, và nó do policy của bài cấp. */}
      {canDrag && policy.hint && <span className="hint">{policy.hint}</span>}

      {/* W4B-4D — KHÁM PHÁ CỦA HỌ CÓ-ĐIỀU-KIỆN LÀ ĐỔI CHÍNH ĐIỀU KIỆN.
          Chỉ dựng khi bài THẬT SỰ có điều kiện (`count_if`/`sum_if`), nên đây
          không phải một khung tương tác dùng chung áp lên mọi bài. */}
      {/* W12 §6/§19 — LẦN THỨ BA của cùng một mẫu hỏng, nên sửa ở cùng chủ sở
          hữu. `sum_if`/`count_if` là BOUNDED_PARAMETER_TOOL: công cụ của chúng
          KHÔNG phải cột kéo (`mode: "hidden"` — thứ tự dãy không đổi kết quả)
          mà chính là thanh điều kiện này. Để nó sau `exploreOpen` nghĩa là hai
          bài ấy mở ra không có công cụ nào — đúng thứ ma trận bề rộng đo được. */}
      {toolAffordanceOpen({ busy }) && hasCondition(config) && (
        <ConditionBar config={config} state={state} busy={busy} dispatch={dispatch} />
      )}
    </div>
  );
}

/**
 * W4B-4D — THANH ĐIỀU KIỆN. Hai control, đúng hai thứ engine đọc: phép so sánh
 * và ngưỡng. Không ô nhập biểu thức, không AND/OR — miền đóng nằm ở
 * `condition-param.ts`, đây chỉ bày đúng miền đó ra.
 */
function ConditionBar({ config, state, busy, dispatch }: Pick<Props, "config" | "state" | "busy" | "dispatch">) {
  /* ĐỌC ĐIỀU KIỆN TỪ ENGINE, KHÔNG TỪ ĐỀ GỐC.
   *
   * `config` (prop) là config ĐÃ VALIDATE của envelope và nó ĐÔNG CỨNG có chủ
   * đích: `store.dispatch` chỉ thay `active.state`, còn `active.config` giữ
   * nguyên để `specDrift` biết mô hình đã rời khỏi đề chưa. Nhưng `set_param`
   * ghi điều kiện mới vào `state.config`, và ĐÓ mới là thứ engine dùng để chấm.
   *
   * Trước bản vá, hai nguồn ấy lệch nhau ngay khi học sinh đổi phép so sánh:
   *
   *   học sinh chọn ">"  → engine dùng ">"  → ô chọn NHẢY VỀ ">=" của đề gốc
   *   thử thách hỏi "80 có được cộng vào tổng không?"
   *   màn hình nói  "Phép so sánh: lớn hơn hoặc bằng · Ngưỡng 80"
   *   engine chấm   80 > 80 = Sai  →  ai trả lời "Cộng vào tổng" bị chấm SAI
   *
   * Tức học sinh bị chấm theo một giá trị KHÔNG NHÌN THẤY ĐƯỢC, trong khi thứ
   * nhìn thấy được lại nói ngược lại. Engine là nơi duy nhất có thẩm quyền phán
   * đúng/sai (`CORRECTNESS.md`), nên bề mặt điều khiển phải soi đúng engine. */
  const cond = state.config.data.condition!;
  const range = thresholdRange(state.config.data.array);
  void config;
  if (!range) return null;
  const set = (name: string, value: number | string) =>
    dispatch({ type: "set_param", name, value });
  return (
    <div className="param-bar" role="group" aria-label="Đổi điều kiện lọc">
      <label>
        Phép so sánh
        <select value={cond.op} disabled={busy}
          onChange={(e) => set("condition.op", e.target.value)}>
          {CONDITION_OPS.map((op) => (
            <option key={op} value={op}>{CONDITION_OP_LABEL[op]}</option>
          ))}
        </select>
      </label>
      <label>
        Ngưỡng <strong>{fmt(cond.value)}</strong>
        {/* Miền = khoảng giá trị của CHÍNH DÃY: ngoài khoảng thì kết quả bão hoà
            và mọi lần kéo tiếp đều cho một câu trả lời. */}
        <input type="range" min={range.min} max={range.max} step={1} value={cond.value}
          disabled={busy} aria-label="Ngưỡng của điều kiện"
          onChange={(e) => set("condition.value", Number(e.target.value))} />
      </label>
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
