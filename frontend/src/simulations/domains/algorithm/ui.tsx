import { useState } from "react";
import { ArrayView } from "../../../components/ArrayView";
import { VarsView } from "../../../components/VarsView";
import { PseudocodeView } from "../../../components/PseudocodeView";
import { AnalysisCard } from "../../../components/AnalysisCard";
import { fmt } from "../../../core/trace-builder";
import type { WorkspaceProps } from "../../types";
import { consequenceOf, decisionPointOf } from "./decision";
import { whatIfPolicyOf } from "./interaction-policy";
import { activeTrace, clampStep, type AlgorithmConfig, type AlgorithmSimState } from "./model";
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
  // Thí nghiệm (mode "challenge") do học sinh CHỦ ĐỘNG mở — state trình bày cục bộ.
  const [labOpen, setLabOpen] = useState(false);

  const dragAllowedByPolicy =
    policy.mode === "free" || policy.mode === "framed" || (policy.mode === "challenge" && labOpen);
  // R3.3a giữ nguyên: chỉ khi đang dừng, chưa ở nhánh, chưa hết bài.
  const canDrag = dragAllowedByPolicy && !busy && !state.branch && !last;

  const decision = decisionPointOf(state);
  const consequence = decision ? null : consequenceOf(state);
  const hold = insertionHold(state, clampStep(state, state.cursor));

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
            <span className="hold-note">đã rút khỏi dãy — ô trống ở vị trí {hold.gapIndex}</span>
          </div>
        )}
        <ArrayView
          step={step}
          labels={config.data.labels}
          interactive={canDrag}
          onSwap={(i, j) => dispatch({ type: "whatif_swap", i, j })}
          gapIndex={hold?.gapIndex ?? null}
        />
        {hold && (
          <p className="stage-legend">
            <span><i className="dot is-current" /> đang so sánh</span>
            <span><i className="dot is-done" /> phần đã sắp</span>
            <span><i className="dot is-gap" /> ô trống</span>
            <span><i className="dot is-idle" /> chưa sắp</span>
          </p>
        )}
      </div>

      {/* Dải nhân quả — cùng nguồn decision.ts với ô dự đoán (M9-S1 §4, §8). */}
      {decision && (
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
      {policy.mode === "challenge" && !labOpen && !state.branch && !last && (
        <div className="stack" style={{ gap: "var(--sp-xs)", alignItems: "flex-start" }}>
          {policy.challengeTeaser && <span className="hint">{policy.challengeTeaser}</span>}
          <button className="btn-utility" onClick={() => setLabOpen(true)}>
            <IconExperiment size={14} />
            {policy.challengeLabel}
          </button>
        </div>
      )}
      {policy.mode === "challenge" && labOpen && !state.branch && (
        <div className="notes" role="note">
          <IconExperiment size={14} /> {policy.framing}{" "}
          <button className="btn-utility" style={{ marginLeft: 8 }} onClick={() => setLabOpen(false)}>
            Đóng thí nghiệm
          </button>
        </div>
      )}

      {canDrag && policy.hint && <span className="hint">{policy.hint}</span>}
    </div>
  );
}

export function AlgorithmInspector({ config, state }: Props) {
  const trace = activeTrace(state);
  const step = trace.steps[clampStep(state, state.cursor)];
  return (
    <div className="stack" style={{ gap: "var(--sp-sm)" }}>
      <AnalysisCard analysis={config} />
      <VarsView step={step} />
      <PseudocodeView algorithmId={config.algorithm_id} currentLine={step.line} />
    </div>
  );
}
