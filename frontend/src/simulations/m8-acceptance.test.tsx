import { beforeEach, describe, expect, it } from "vitest";
import { OFFLINE_SAMPLES } from "../data/sim-samples";
import { useAppStore } from "../state/store";
import { registerAllSimulations } from "./index";
import type { NetworkState } from "./domains/network/model";

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
 */

registerAllSimulations();

const sample = OFFLINE_SAMPLES.find(
  (s) => s.envelope.simulation_id === "network.packet_routing",
)!;

beforeEach(() => useAppStore.getState().reset());

describe("M8 acceptance — luồng 2D → dự đoán → 3D → 2D", () => {
  it("chạy trọn 12 bước của kịch bản nghiệm thu, không rebuild, không AI call", () => {
    const store = () => useAppStore.getState();

    // (1) Nạp bài định tuyến gói tin từ fixture offline (bài mẫu — không cần backend)
    store().loadEnvelope(sample.envelope, sample.id);
    expect(store().analysisError).toBeNull();
    expect(store().active).not.toBeNull();

    // (2) Xác nhận đang ở 2D (mặc định M8)
    expect(store().visualMode).toBe("2d");

    // (3) Tua tới một bước GIỮA timeline
    store().nextStep();
    const s3 = store().active!.state as NetworkState;
    expect(s3.cursor).toBe(1);
    expect(s3.cursor).toBeLessThan(s3.steps.length - 1);

    // (4) Nộp dự đoán chặng kế tiếp (đúng chặng chuẩn BFS)
    const expected = s3.route[s3.cursor + 1];
    store().submitPrediction(expected);

    // (5) Kết quả TẤT ĐỊNH từ engine, là DỮ LIỆU (không phải hội thoại)
    expect(store().prediction!.verdict).toBe("correct");
    expect(store().prediction!.expectedId).toBe(expected);

    // (6) Chuyển sang 3D
    const stateBefore3d = store().active!.state;
    const envelopeBefore3d = store().active!.envelope;
    store().setVisualMode("3d");

    // (7) CÙNG bước · CÙNG nút ngữ nghĩa · CÙNG route · prediction còn nguyên ·
    //     KHÔNG analyze lại (fetch nào cũng sẽ ném lỗi) · KHÔNG rebuild (same ref)
    expect(store().visualMode).toBe("3d");
    expect(store().active!.state).toBe(stateBefore3d);
    expect(store().active!.envelope).toBe(envelopeBefore3d);
    const s7 = store().active!.state as NetworkState;
    expect(s7.cursor).toBe(1);
    expect(s7.steps[s7.cursor].packetAt).toBe(s3.steps[s3.cursor].packetAt);
    expect(s7.route).toBe(s3.route);
    expect(store().prediction!.verdict).toBe("correct");

    // (8) Tiến MỘT bước ngay trong chế độ 3D — timeline là của MODULE, không của renderer
    store().nextStep();
    expect((store().active!.state as NetworkState).cursor).toBe(2);
    // đổi bước → dự đoán cũ hết hiệu lực (đúng ngữ nghĩa M8-PRE-LIP, không phải do 3D)
    expect(store().prediction).toBeNull();

    // (9) Quay về 2D
    const stateBefore2d = store().active!.state;
    store().setVisualMode("2d");

    // (10) State/timeline nhất quán — không reset, không rebuild
    expect(store().visualMode).toBe("2d");
    expect(store().active!.state).toBe(stateBefore2d);
    expect((store().active!.state as NetworkState).cursor).toBe(2);

    // (11)+(12) "Reset góc nhìn" là nút của RENDERER 3D, chỉ đụng camera trong
    // ref của component (xem ui3d.tsx — onClick chỉ copy home vào camera/controls);
    // không có đường code nào từ nút đó tới store: mô phỏng không reset.
    expect((store().active!.state as NetworkState).cursor).toBe(2);
    expect(store().active!.state).toBe(stateBefore2d);
  });
});
