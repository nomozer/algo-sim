import { beforeEach, describe, expect, it } from "vitest";
import { OFFLINE_SAMPLES } from "../data/sim-samples";
import { useAppStore } from "../state/store";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";
import { representationPolicyOf } from "./renderer";
import type { EncapState } from "./domains/network/encap-model";

/**
 * M8 — KỊCH BẢN NGHIỆM THU (plan §15) chạy như integration test.
 *
 * Các action của store CHÍNH LÀ handler của các nút UI (Next/Prev = nextStep/
 * prevStep, toggle 2D/3D = setVisualMode, "Kiểm tra" = submitPrediction), nên
 * chuỗi dưới đây là đúng luồng người dùng bấm — chỉ thiếu con mắt nhìn WebGL
 * (phần đó nghiệm thu bằng browser thật, ngoài vitest).
 *
 * Bất biến xuyên suốt: 0 network call (fetch bị test-setup chặn — analyze KHÔNG
 * hề chạy lại), engine state chỉ đổi khi CHÍNH người dùng bấm bước.
 *
 * ── W4B-2R: ĐỔI BÀI LÀM CHỨNG, và vì sao ────────────────────────────────────
 * Bản cũ dùng `network.packet_routing`. Wave này xếp nó `2D_ONLY` (module tự
 * khai `architectural_poc` — Z chỉ là bố cục), nên bài đó KHÔNG còn 3D.
 *
 * Nguy hiểm ở chỗ test cũ vẫn **XANH** sau khi 3D bị gỡ: `setVisualMode("3d")`
 * chỉ ghi một cờ trình bày ở store, còn `effectiveVisualMode` mới là chỗ rơi về
 * "2d" lúc render. Tức nó "nghiệm thu 3D" trên một bài không có 3D — xanh vì lý
 * do sai, đúng họ với anti-pattern #8.
 *
 * Nay bài làm chứng **DẪN XUẤT TỪ CHÍNH SÁCH** chứ không viết cứng: lấy target
 * duy nhất có `2d_and_3d_justified`. Gỡ 3D khỏi nó thì test đỏ ngay ở bước chọn
 * bài, chứ không âm thầm nghiệm thu một cái toggle không tồn tại.
 */

registerAllSimulations();

/** Bài làm chứng = target THẬT SỰ có hai biểu diễn, hỏi registry chứ không đoán. */
const witnessId = listSimulations()
  .map((m) => m.id)
  .find((id) => representationPolicyOf(getSimulation(id)!) === "2d_and_3d_justified");

const sample = OFFLINE_SAMPLES.find((s) => s.envelope.simulation_id === witnessId);

beforeEach(() => useAppStore.getState().reset());

describe("M8 acceptance — luồng 2D → dự đoán → 3D → 2D", () => {
  it("có ĐÚNG một bài làm chứng 2D+3D, và nó có mẫu offline để chạy kịch bản", () => {
    expect(witnessId, "không target nào còn hai biểu diễn ⇒ kịch bản M8 vô nghĩa")
      .toBe("network.protocol_encapsulation");
    expect(sample, `thiếu mẫu offline cho ${witnessId}`).toBeTruthy();
  });

  it("chạy trọn kịch bản nghiệm thu, không rebuild, không AI call", () => {
    const store = () => useAppStore.getState();
    const mod = getSimulation(witnessId!)!;

    // (1) Nạp bài từ fixture offline (bài mẫu — không cần backend)
    store().loadEnvelope(sample!.envelope, sample!.id);
    expect(store().analysisError).toBeNull();
    expect(store().active).not.toBeNull();

    // (2) Xác nhận đang ở 2D (mặc định M8)
    expect(store().visualMode).toBe("2d");

    // (3) Tua tới một bước GIỮA timeline
    store().nextStep();
    const s3 = store().active!.state as EncapState;
    expect(s3.cursor).toBe(1);
    expect(s3.cursor).toBeLessThan(s3.steps.length - 1);

    // (4)(5) Nộp dự đoán — engine chấm, kết quả là DỮ LIỆU (không phải hội thoại)
    const challenge = mod.predict!.challenge(store().active!.state);
    expect(challenge, "bài làm chứng phải có nhịp dự đoán ở bước này").toBeTruthy();
    store().submitPrediction(challenge!.options[0].id);
    expect(store().prediction).not.toBeNull();
    const verdictBefore3d = store().prediction!.verdict;

    // (6) Chuyển sang 3D
    const stateBefore3d = store().active!.state;
    const envelopeBefore3d = store().active!.envelope;
    store().setVisualMode("3d");

    // (7) CÙNG bước · CÙNG state (same ref) · prediction còn nguyên ·
    //     KHÔNG analyze lại (fetch nào cũng sẽ ném lỗi) · KHÔNG rebuild
    expect(store().visualMode).toBe("3d");
    expect(store().active!.state).toBe(stateBefore3d);
    expect(store().active!.envelope).toBe(envelopeBefore3d);
    const s7 = store().active!.state as EncapState;
    expect(s7.cursor).toBe(1);
    expect(s7.layers).toBe(s3.layers);
    expect(store().prediction!.verdict).toBe(verdictBefore3d);

    // (8) Tiến MỘT bước ngay trong chế độ 3D — timeline là của MODULE, không của renderer
    store().nextStep();
    expect((store().active!.state as EncapState).cursor).toBe(2);
    // đổi bước → dự đoán cũ hết hiệu lực (ngữ nghĩa M8-PRE-LIP, không phải do 3D)
    expect(store().prediction).toBeNull();

    // (9)(10) Quay về 2D — state/timeline nhất quán, không reset, không rebuild
    const stateBefore2d = store().active!.state;
    store().setVisualMode("2d");
    expect(store().visualMode).toBe("2d");
    expect(store().active!.state).toBe(stateBefore2d);
    expect((store().active!.state as EncapState).cursor).toBe(2);

    // (11)(12) "Reset góc nhìn" là nút của RENDERER 3D, chỉ đụng camera trong ref
    // của component; không có đường code nào từ nút đó tới store.
    expect(store().active!.state).toBe(stateBefore2d);
  });
});
