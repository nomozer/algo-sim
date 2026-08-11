import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAppStore } from "./store";
import { __resetHistoryForTest } from "./history";
import { registerAllSimulations } from "../simulations";
import { getSimulation, listSimulations } from "../simulations/registry";
import { offlineCatalog } from "../data/offline-catalog";

/**
 * W4B-2Z §26–30 — NHIỀU MÔ PHỎNG MỞ CÙNG LÚC.
 *
 * Kịch bản người dùng đã nêu: đang dở bài A, mở bài B, quay lại A — A phải Ở
 * NGUYÊN CHỖ CŨ, kể cả những gì học sinh đã tự làm (what-if), không chỉ cursor.
 *
 * Hai bất biến bị khoá ở đây:
 *
 *   1. GIỮ NGUYÊN — chuyển phiên trả về ĐÚNG state cũ, không dựng lại.
 *      Nếu chuyển phiên mà chạy lại `init` thì mọi thao tác của học sinh biến
 *      mất trong im lặng; đó là lỗi, không phải "làm mới".
 *   2. ZERO-AI — chuyển phiên không gọi mạng. Kiểm bằng cách đếm `fetch` thật
 *      chứ không bằng đọc mã: guard `test-setup.ts` đã stub `fetch`, ta đếm nó.
 *
 * Vì sao KHÔNG dùng Lịch sử để làm việc này: `reopenFromHistory` dựng lại từ
 * envelope rồi tua tới `lastCursor` — đúng cho "mở lại bài cũ", SAI cho "quay
 * lại tab đang dở", vì nó bỏ mất state do học sinh tạo ra.
 */

/* Lấy envelope từ chính danh mục offline — tự bịa config thì test đo được cái
   khác với sản phẩm, và mọi thay đổi hợp đồng config sẽ không chạm tới nó. */
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

describe("W4B-2Z §26 · phiên đang mở là một khái niệm riêng", () => {
  it("nạp mô phỏng khi chưa chọn phiên ⇒ MỞ THÊM phiên, không đè", () => {
    s().loadEnvelope(ENV_A);
    expect(s().sessions).toHaveLength(1);
    s().newSession();
    expect(s().sessions).toHaveLength(1);   // "+ Mô phỏng mới" KHÔNG đóng A
    expect(s().active).toBeNull();          // nhưng bàn làm việc trống để soạn đề
    s().loadEnvelope(ENV_B);
    expect(s().sessions).toHaveLength(2);
    expect(s().sessions.map((x) => x.title)).toEqual([ENV_A.title, ENV_B.title]);
  });

  it("phân tích lại TRONG một phiên thì thay nội dung phiên đó, không đẻ phiên", () => {
    s().loadEnvelope(ENV_A);
    const id = s().activeSessionId;
    s().loadEnvelope(ENV_B);              // vẫn đang ở phiên A ⇒ thay chỗ
    expect(s().sessions).toHaveLength(1);
    expect(s().activeSessionId).toBe(id);
  });
});

describe("W4B-2Z §30 · A → B → A giữ nguyên chỗ đang dở", () => {
  it("cursor, what-if, cách xem và chế độ thử thách đều còn nguyên", () => {
    // ── A: đi vài bước + một thao tác what-if + bật thử thách ──
    s().loadEnvelope(ENV_A);
    const idA = s().activeSessionId!;
    s().nextStep();
    s().nextStep();
    s().setChallengeOpen(true);
    s().setExploreOpen(true);
    const stateA = s().active!.state;
    const configA = s().active!.config;
    const envelopeA = s().active!.envelope;

    // ── B: mở bài khác rồi ĐỔI state của nó ──
    s().newSession();
    s().loadEnvelope(ENV_B);
    const idB = s().activeSessionId!;
    s().dispatch({ type: "toggle", target: "inputA" } as never);
    const stateB = s().active!.state;
    expect(idB).not.toBe(idA);

    // ── quay lại A ──
    s().switchSession(idA);
    expect(s().activeSessionId).toBe(idA);
    // ĐỒNG NHẤT THAM CHIẾU: không dựng lại thì object phải là chính nó.
    expect(s().active!.state).toBe(stateA);
    expect(s().active!.config).toBe(configA);
    expect(s().active!.envelope).toBe(envelopeA);
    expect(s().challengeOpen).toBe(true);
    /* W4B-3A — CHÍNH SÁCH KHAI TƯỜNG MINH: Khám phá theo PHIÊN, y như Thử thách.
       Quay lại một bài đang dở mà chế độ tự đóng thì học sinh vừa kéo xong đã
       mất lối vào để kéo tiếp — "làm mới trong im lặng", đúng thứ §26 chặn. */
    expect(s().exploreOpen, "chế độ Khám phá không được khôi phục theo phiên").toBe(true);

    // ── quay lại B: B cũng còn nguyên ──
    s().switchSession(idB);
    expect(s().active!.state).toBe(stateB);
    expect(s().challengeOpen).toBe(false);
    // …và KHÔNG rò chế độ của A sang B.
    expect(s().exploreOpen, "chế độ Khám phá rò từ phiên A sang phiên B").toBe(false);
  });

  it("nạp bài MỚI luôn mở ở Quan sát — không thừa hưởng chế độ của bài trước", () => {
    s().loadEnvelope(ENV_A);
    s().setChallengeOpen(true);
    s().setExploreOpen(true);
    s().newSession();
    s().loadEnvelope(ENV_B);
    expect(s().challengeOpen).toBe(false);
    expect(s().exploreOpen).toBe(false);
  });

  it("Đặt lại đóng cả hai chế độ — dựng lại mô hình là về Quan sát", () => {
    s().loadEnvelope(ENV_A);
    s().setChallengeOpen(true);
    s().setExploreOpen(true);
    s().resetSim();
    expect(s().challengeOpen).toBe(false);
    expect(s().exploreOpen).toBe(false);
  });

  it("đóng A KHÔNG đụng B", () => {
    s().loadEnvelope(ENV_A);
    const idA = s().activeSessionId!;
    s().newSession();
    s().loadEnvelope(ENV_B);
    const idB = s().activeSessionId!;
    const stateB = s().active!.state;

    s().closeSession(idA);
    expect(s().sessions.map((x) => x.id)).toEqual([idB]);
    expect(s().active!.state).toBe(stateB);
  });

  it("đóng phiên CUỐI CÙNG thì về Home, không để lại bàn làm việc ma", () => {
    s().loadEnvelope(ENV_A);
    s().closeSession(s().activeSessionId!);
    expect(s().sessions).toEqual([]);
    expect(s().active).toBeNull();
    expect(s().view).toBe("home");
  });

  it("đóng phiên đang xem thì rơi về phiên còn lại, không về Home oan", () => {
    s().loadEnvelope(ENV_A);
    const idA = s().activeSessionId!;
    s().newSession();
    s().loadEnvelope(ENV_B);
    s().closeSession(s().activeSessionId!);
    expect(s().activeSessionId).toBe(idA);
    expect(s().view).toBe("workspace");
  });

  it("về Home rồi quay lại phiên: vẫn nguyên chỗ đang dở", () => {
    s().loadEnvelope(ENV_A);
    const idA = s().activeSessionId!;
    s().nextStep();
    const stateA = s().active!.state;
    s().goHome();
    expect(s().sessions).toHaveLength(1);   // Home KHÔNG đóng phiên
    s().switchSession(idA);
    expect(s().active!.state).toBe(stateA);
  });
});

describe("W4B-2Z §28 · chuyển phiên = 0 gọi AI", () => {
  it("switch/close/new không phát một request nào", () => {
    const spy = vi.spyOn(globalThis, "fetch");
    s().loadEnvelope(ENV_A);
    const idA = s().activeSessionId!;
    s().newSession();
    s().loadEnvelope(ENV_B);
    const idB = s().activeSessionId!;
    spy.mockClear();

    s().switchSession(idA);
    s().switchSession(idB);
    s().switchSession(idA);
    s().goHome();
    s().switchSession(idB);
    s().closeSession(idA);

    expect(spy, "chuyển phiên gọi mạng").not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it("chuyển phiên KHÔNG chạy lại validateConfig/init của module", () => {
    s().loadEnvelope(ENV_A);
    const idA = s().activeSessionId!;
    s().newSession();
    s().loadEnvelope(ENV_B);
    const idB = s().activeSessionId!;

    /* Đây là chỗ dễ trôi nhất: một bản "sửa cho gọn" hay gọi lại `loadEnvelope`
       khi chuyển phiên. Làm thế thì fetch vẫn 0 (envelope có sẵn) nhưng state
       BỊ DỰNG LẠI — học sinh mất what-if mà test mạng không thấy gì. Nên phải
       kiểm bằng chính module. */
    /* W4B-3A — theo dõi CẢ HAI module, không chỉ một.
       Tiêm lỗi (`switchSession` gọi `loadEnvelope`) cho thấy bản một-module có
       thể im lặng: tuỳ thứ tự chuyển, phiên được dựng lại có thể là bài KIA,
       nên spy đặt nhầm bài sẽ không nghe thấy gì. Guard chỉ chứng minh được
       điều nó nói khi phủ mọi module đang mở. */
    const spies = ["algorithm.bubble_sort", "logic.and_gate"].flatMap((id) => {
      const mod = getSimulation(id)!;
      return [vi.spyOn(mod, "init"), vi.spyOn(mod, "validateConfig")];
    });

    s().switchSession(idA);
    s().switchSession(idB);
    s().switchSession(idA);

    for (const spy of spies) expect(spy, "chuyển phiên đã dựng lại mô phỏng").not.toHaveBeenCalled();
    for (const spy of spies) spy.mockRestore();
  });
});
