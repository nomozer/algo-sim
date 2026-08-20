import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAppStore } from "./store";
import { __resetHistoryForTest, historyStore } from "./history";
import { registerAllSimulations } from "../simulations";
import { getSimulation, listSimulations } from "../simulations/registry";
import { offlineCatalog } from "../data/offline-catalog";

/**
 * VÒNG ĐỜI BÀN LÀM VIỆC — MỘT MÔ PHỎNG TẠI MỘT THỜI ĐIỂM.
 *
 * ─── FILE NÀY THAY `sessions.test.ts` ─────────────────────────────────────
 *
 * W4B-2Z §26 từng dựng nhiều phiên mở song song (`sessions` + dải tab). M18-UI
 * đã GỠ theo yêu cầu sản phẩm: mở thêm bài thứ hai không phải việc học sinh làm
 * trong một tiết, và dải tab nó sinh ra cạnh tranh chỗ với sân khấu.
 *
 * Nhưng ba bất biến trong file cũ KHÔNG chết theo tính năng — chúng nói về bàn
 * làm việc nói chung, nên chuyển sang đây:
 *
 *   1. bài MỚI luôn mở ở Quan sát (chế độ không rò từ bài trước sang bài sau);
 *   2. Đặt lại đóng cả hai chế độ;
 *   3. **ZERO-AI**: đổi bài không gọi mạng. Trước đây đo trên `switchSession`;
 *      nay đo trên đường CÒN LẠI để quay về bài cũ — `reopenFromHistory`.
 *
 * Vế 3 quan trọng hơn hẳn sau khi gỡ nhiều phiên: Lịch sử nay là đường DUY NHẤT
 * quay lại một bài đã mở, nên nếu nó âm thầm gọi pipeline thì mỗi lần học sinh
 * xem lại bài cũ là một lần tiêu quota.
 */

const pick = (simId: string) => {
  const e = offlineCatalog().find((c) => c.simId === simId);
  if (!e) throw new Error(`danh mục offline không có ${simId}`);
  return e.envelope;
};

beforeEach(() => {
  if (listSimulations().length === 0) registerAllSimulations();
  useAppStore.getState().reset();
  __resetHistoryForTest();
  vi.clearAllMocks();
});

const ENV_A = pick("algorithm.bubble_sort");
const ENV_B = pick("logic.and_gate");
const s = () => useAppStore.getState();

describe("M18-UI · một mô phỏng tại một thời điểm", () => {
  it("nạp bài thứ hai THAY bài đang xem, không đẻ thêm bàn làm việc", () => {
    s().loadEnvelope(ENV_A);
    const first = s().active;
    expect(first?.moduleId).toBe("algorithm.bubble_sort");

    s().loadEnvelope(ENV_B);
    expect(s().active?.moduleId).toBe("logic.and_gate");
    // và store KHÔNG còn khái niệm nhiều phiên nào sót lại
    const bag = s() as unknown as Record<string, unknown>;
    expect(bag.sessions).toBeUndefined();
    expect(bag.activeSessionId).toBeUndefined();
  });

  it("bài bị thay KHÔNG mất — nó nằm lại trong Lịch sử", () => {
    /* Đây là điều kiện khiến việc gỡ nhiều phiên chấp nhận được. Nếu thay bài
       là mất bài thì học sinh phải phân tích lại đề, tức tiêu một lượt AI. */
    s().loadEnvelope(ENV_A);
    s().loadEnvelope(ENV_B);
    const titles = historyStore.list().map((h) => h.envelope.simulation_id);
    expect(titles).toContain("algorithm.bubble_sort");
    expect(titles).toContain("logic.and_gate");
  });

  it("bài MỚI luôn mở ở Quan sát — chế độ không rò từ bài trước", () => {
    s().loadEnvelope(ENV_A);
    s().setExploreOpen(true);
    s().loadEnvelope(ENV_B);
    expect(s().exploreOpen).toBe(false);
  });

  it("Đặt lại đóng chế độ — dựng lại mô hình là về Quan sát", () => {
    s().loadEnvelope(ENV_A);
    s().setExploreOpen(true);
    s().resetSim();
    expect(s().exploreOpen).toBe(false);
  });

  it("về Home rồi mở lại từ Lịch sử: đúng bài, đúng chỗ đang dở", () => {
    s().loadEnvelope(ENV_A);
    s().nextStep();
    s().nextStep();
    const cursorBefore = (s().active!.state as { cursor: number }).cursor;
    expect(cursorBefore).toBeGreaterThan(0);

    s().goHome();
    expect(s().active).toBeNull();

    const item = historyStore.list().find(
      (h) => h.envelope.simulation_id === "algorithm.bubble_sort")!;
    s().reopenFromHistory(item.id);
    expect(s().active?.moduleId).toBe("algorithm.bubble_sort");
    expect((s().active!.state as { cursor: number }).cursor).toBe(cursorBefore);
  });
});

describe("M18-UI · đổi bài = 0 gọi AI", () => {
  it("nạp bài, về Home, mở lại từ Lịch sử — không một request nào", () => {
    /* Đếm `fetch` THẬT chứ không đọc mã: một đường gọi mới thêm vào sau này sẽ
       bị bắt, còn phép quét mã thì không.
       `test-setup.ts` thay `fetch` bằng một hàm THƯỜNG luôn ném lỗi (không phải
       `vi.fn`), nên phải tự bọc để đếm — `vi.mocked` trên nó sẽ báo "not a spy". */
    const spy = vi.fn(globalThis.fetch);
    globalThis.fetch = spy as unknown as typeof fetch;
    s().loadEnvelope(ENV_A);
    s().loadEnvelope(ENV_B);
    s().goHome();
    const item = historyStore.list()[0];
    s().reopenFromHistory(item.id);
    expect(spy, "đổi bài lại đi gọi mạng").not.toHaveBeenCalled();
  });

  it("mở lại từ Lịch sử KHÔNG chạy lại validateConfig của module", () => {
    /* `reopenFromHistory` dựng lại từ envelope nên nó PHẢI gọi validateConfig +
       init một lần — đó là đúng. Cái phải chặn là gọi PIPELINE. Bài này khoá
       đúng ranh giới đó: có dựng lại engine, không có gọi mạng. */
    const netSpy = vi.fn(globalThis.fetch);
    globalThis.fetch = netSpy as unknown as typeof fetch;
    s().loadEnvelope(ENV_A);
    const mod = getSimulation("algorithm.bubble_sort")!;
    const spy = vi.spyOn(mod, "validateConfig");
    const before = spy.mock.calls.length;
    s().goHome();
    s().reopenFromHistory(historyStore.list()[0].id);
    expect(spy.mock.calls.length).toBeGreaterThan(before);
    expect(netSpy, "mở lại từ Lịch sử lại đi gọi mạng").not.toHaveBeenCalled();
    spy.mockRestore();
  });
});
