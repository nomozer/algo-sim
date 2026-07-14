import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../App";
import { registerAllSimulations } from "../simulations";
import type { SimulationEnvelope } from "../simulations/types";
import type { NetworkState } from "../simulations/domains/network/model";
import { useAppStore } from "./store";
import { __resetHistoryForTest } from "./history";

/**
 * M9-UX1 — Home/Workspace/History là ba MẶT TRÌNH BÀY trên cùng một store:
 * - view là presentation state (như visualMode) — không đụng engine;
 * - lịch sử là DỮ LIỆU BỀN, tách khỏi runtime: goHome/reset không phá lịch sử;
 * - MỞ LẠI TỪ LỊCH SỬ KHÔNG GỌI AI: dùng envelope đã validate + module.init
 *   (test-setup chặn fetch → bất kỳ lệnh gọi /api nào cũng nổ ngay).
 */

registerAllSimulations();

const NET_CONFIG = {
  nodes: [
    { id: "pc", type: "client" },
    { id: "r1", type: "router" },
    { id: "srv", type: "server" },
  ],
  links: [
    ["pc", "r1"],
    ["r1", "srv"],
  ],
  source: "pc",
  destination: "srv",
  notes: null,
};

function envelope(): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: "network.packet_routing",
    domain: "network",
    visual_mode: "2d",
    title: "Đường đi của gói tin",
    description: null,
    config: NET_CONFIG,
    notes: null,
  };
}

beforeEach(() => {
  __resetHistoryForTest();
  useAppStore.getState().reset();
});

describe("view — Home là mặc định, workspace khi có mô phỏng", () => {
  it("(1) khởi đầu: view = home, không có mô phỏng", () => {
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().active).toBeNull();
  });

  it("(6) loadEnvelope → vào workspace", () => {
    useAppStore.getState().loadEnvelope(envelope());
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().active).not.toBeNull();
  });

  it("(10) goHome: về home, active dọn sạch nhưng LỊCH SỬ còn nguyên", () => {
    useAppStore.getState().loadEnvelope(envelope());
    useAppStore.getState().goHome();
    const s = useAppStore.getState();
    expect(s.view).toBe("home");
    expect(s.active).toBeNull();
    expect(s.history).toHaveLength(1);
    expect(s.history[0].title).toBe("Đường đi của gói tin");
  });

  it("reset() (dùng nội bộ) cũng KHÔNG xoá lịch sử bền", () => {
    useAppStore.getState().loadEnvelope(envelope());
    useAppStore.getState().reset();
    expect(useAppStore.getState().history).toHaveLength(1);
  });
});

describe("(9) MỞ LẠI TỪ LỊCH SỬ — zero-AI, khôi phục tiến độ", () => {
  it("luồng đầy đủ: load → bước 2 → 3D → goHome → reopen → đúng bài, đúng bước, đúng mode, 0 fetch", () => {
    const store = () => useAppStore.getState();

    // (1)-(4) nạp bài (tương đương sau khi AI đã phân tích MỘT lần) → có history
    store().loadEnvelope(envelope(), undefined, "Minh họa đường đi gói tin từ máy tính đến máy chủ");
    expect(store().history).toHaveLength(1);
    expect(store().history[0].originalInput).toContain("máy chủ");

    // (5) học tới bước 2 + chuyển 3D — tiến độ trình bày được ghi lại
    store().nextStep();
    store().nextStep();
    store().setVisualMode("3d");

    // (6) về Home — active bị dọn, lịch sử giữ tiến độ
    store().goHome();
    expect(store().history[0].lastCursor).toBe(2);
    expect(store().history[0].visualMode).toBe("3d");

    // (7)(8) mở lại từ lịch sử — KHÔNG /api/analyze (fetch guard sẽ nổ nếu có)
    store().reopenFromHistory(store().history[0].id);
    const s = store();
    expect(s.view).toBe("workspace");
    expect(s.active!.moduleId).toBe("network.packet_routing");
    // (14)(15) dùng đúng dữ liệu đã validate — config như cũ, title như cũ
    expect(s.active!.envelope.title).toBe("Đường đi của gói tin");
    expect((s.active!.state as NetworkState).route).toEqual(["pc", "r1", "srv"]);
    // (16)(17) khôi phục cursor + visual mode
    expect((s.active!.state as NetworkState).cursor).toBe(2);
    expect(s.visualMode).toBe("3d");
  });

  it("(12) mở lại không nhân bản item lịch sử", () => {
    const store = () => useAppStore.getState();
    store().loadEnvelope(envelope());
    store().goHome();
    store().reopenFromHistory(store().history[0].id);
    store().goHome();
    expect(store().history).toHaveLength(1);
  });

  it("id không tồn tại → no-op an toàn, ở lại home", () => {
    useAppStore.getState().goHome();
    useAppStore.getState().reopenFromHistory("khong-ton-tai");
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().active).toBeNull();
  });
});

describe("(23)(24) state tạm KHÔNG rơi vào lịch sử", () => {
  it("submitPrediction + what-if không đổi dữ liệu lịch sử đã lưu", () => {
    const store = () => useAppStore.getState();
    store().loadEnvelope(envelope());
    const before = JSON.stringify(store().history[0]);

    const canonical = (store().active!.state as NetworkState).route[1];
    store().submitPrediction(canonical);
    expect(store().prediction).not.toBeNull();

    expect(JSON.stringify(store().history[0])).toBe(before);
    // reopen sau đó cũng không mang theo prediction cũ
    store().goHome();
    store().reopenFromHistory(store().history[0].id);
    expect(store().prediction).toBeNull();
  });
});

describe("App SSR — Home sạch (không giả inspector/timeline rỗng)", () => {
  it("(1)-(5) trạng thái đầu: hero + composer là hành động chính; không player-controls, không panel Quan sát", () => {
    const html = renderToString(<App />);
    expect(html).toContain("Em muốn khám phá bài toán nào?");
    expect(html).toContain("Phân tích");
    expect(html).toContain("Gợi ý khám phá"); // starter chips
    expect(html).not.toContain("player-controls");
    expect(html).not.toContain("panel-right"); // không inspector rỗng
    expect(html).not.toContain("Tua đến bước"); // không timeline rỗng
  });
});
