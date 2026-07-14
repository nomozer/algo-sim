import { describe, expect, it } from "vitest";
import {
  createHistoryStore,
  HISTORY_MAX_ITEMS,
  HISTORY_SCHEMA_VERSION,
  historyIdOf,
  type StorageLike,
} from "./history";
import type { SimulationEnvelope } from "../simulations/types";

/**
 * M9-UX1 — LỊCH SỬ HỌC CỤC BỘ (localStorage), tách khỏi runtime state.
 *
 * Mục đích sản phẩm: học trên lớp → đóng trình duyệt → mở lại đúng mô phỏng
 * ĐÃ VALIDATE mà KHÔNG tốn thêm một lượt gọi AI nào. Vì vậy thứ được lưu là
 * envelope đã qua server-side validation (hợp đồng JSON an toàn) — không phải
 * đề gốc để chạy lại pipeline.
 *
 * Chính sách: schema có version; entry hỏng/bản cũ bị bỏ qua êm; tối đa
 * HISTORY_MAX_ITEMS (evict theo lastViewedAt cũ nhất); CHỈ lưu các trường
 * whitelist — không key/secret, không blob, không state tạm (prediction/
 * branch/camera).
 */

function fakeStorage(): StorageLike & { raw: Map<string, string> } {
  const raw = new Map<string, string>();
  return {
    raw,
    getItem: (k) => raw.get(k) ?? null,
    setItem: (k, v) => void raw.set(k, v),
    removeItem: (k) => void raw.delete(k),
  };
}

function envelope(id: string, config: unknown, title = "Bài mẫu"): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: id,
    domain: id.split(".")[0] as SimulationEnvelope["domain"],
    visual_mode: "2d",
    title,
    description: null,
    config,
    notes: null,
  };
}

const NET_CONFIG = {
  nodes: [
    { id: "pc", type: "client" },
    { id: "srv", type: "server" },
  ],
  links: [["pc", "srv"]],
  source: "pc",
  destination: "srv",
  notes: null,
};

describe("record + list", () => {
  it("(11) mô phỏng validate thành công → tạo history item đủ trường", () => {
    const store = createHistoryStore(fakeStorage());
    const item = store.record(envelope("network.packet_routing", NET_CONFIG), "đề gốc của em");

    const all = store.list();
    expect(all).toHaveLength(1);
    expect(all[0].id).toBe(item.id);
    expect(all[0].title).toBe("Bài mẫu");
    expect(all[0].simulationId).toBe("network.packet_routing");
    expect(all[0].originalInput).toBe("đề gốc của em");
    expect(all[0].schemaVersion).toBe(HISTORY_SCHEMA_VERSION);
    expect(all[0].envelope.config).toEqual(NET_CONFIG);
    expect(all[0].lastViewedAt).toBeGreaterThan(0);
  });

  it("(12) cùng envelope mở lại → KHÔNG nhân bản, chỉ touch lastViewedAt", () => {
    const store = createHistoryStore(fakeStorage());
    const a = store.record(envelope("network.packet_routing", NET_CONFIG), null);
    const b = store.record(envelope("network.packet_routing", NET_CONFIG), null);
    expect(b.id).toBe(a.id);
    expect(store.list()).toHaveLength(1);
    // id tất định từ simulation_id + config
    expect(historyIdOf(envelope("network.packet_routing", NET_CONFIG))).toBe(a.id);
  });

  it("config khác → item khác (không gộp nhầm hai bài)", () => {
    const store = createHistoryStore(fakeStorage());
    store.record(envelope("logic.and_gate", { inputA: 0, inputB: 0 }), null);
    store.record(envelope("logic.and_gate", { inputA: 1, inputB: 0 }), null);
    expect(store.list()).toHaveLength(2);
  });
});

describe("touch — tiến độ trình bày an toàn", () => {
  it("(16)(17) lưu lastCursor + visualMode; cập nhật được nhiều lần", () => {
    const store = createHistoryStore(fakeStorage());
    const item = store.record(envelope("network.packet_routing", NET_CONFIG), null);
    store.touch(item.id, { lastCursor: 2, visualMode: "3d" });
    const got = store.list()[0];
    expect(got.lastCursor).toBe(2);
    expect(got.visualMode).toBe("3d");
  });
});

describe("(18)(19) chống hỏng — corrupt & schema cũ bị bỏ qua êm", () => {
  it("JSON rác toàn cục → list() = [] (không ném)", () => {
    const storage = fakeStorage();
    const store = createHistoryStore(storage);
    storage.raw.set([...storage.raw.keys()][0] ?? "algosim.history.v1", "{không phải json");
    // ép ghi key đúng
    storage.setItem("algosim.history.v1", "{không phải json");
    expect(() => store.list()).not.toThrow();
    expect(store.list()).toEqual([]);
  });

  it("entry thiếu trường / schemaVersion lạ → bị lọc, entry tốt giữ nguyên", () => {
    const storage = fakeStorage();
    const store = createHistoryStore(storage);
    const good = store.record(envelope("network.packet_routing", NET_CONFIG), null);
    const arr = JSON.parse(storage.getItem("algosim.history.v1")!);
    arr.push({ id: "x", schemaVersion: 999, title: "bản tương lai" });
    arr.push({ hoàn: "toàn rác" });
    storage.setItem("algosim.history.v1", JSON.stringify(arr));

    const listed = store.list();
    expect(listed).toHaveLength(1);
    expect(listed[0].id).toBe(good.id);
  });
});

describe("(20)(21) xóa + hạn mức", () => {
  it("remove xóa đúng item; clear xóa hết", () => {
    const store = createHistoryStore(fakeStorage());
    const a = store.record(envelope("logic.and_gate", { inputA: 0, inputB: 0 }), null);
    store.record(envelope("logic.and_gate", { inputA: 1, inputB: 1 }), null);
    store.remove(a.id);
    expect(store.list()).toHaveLength(1);
    store.clear();
    expect(store.list()).toEqual([]);
  });

  it(`quá ${HISTORY_MAX_ITEMS} item → evict item xem lâu nhất`, () => {
    const store = createHistoryStore(fakeStorage());
    for (let i = 0; i < HISTORY_MAX_ITEMS + 3; i++) {
      store.record(envelope("logic.and_gate", { inputA: 0, inputB: 0, i }), null);
    }
    expect(store.list().length).toBe(HISTORY_MAX_ITEMS);
    // item đầu tiên (cũ nhất) đã bị evict
    expect(store.list().some((x) => (x.envelope.config as { i?: number }).i === 0)).toBe(false);
  });
});

describe("(22)(23)(24)(25) whitelist — không secret, không state tạm", () => {
  it("chuỗi persist chỉ chứa các trường whitelist; không api_key/prediction/branch/camera", () => {
    const storage = fakeStorage();
    const store = createHistoryStore(storage);
    // kẻ gọi cẩu thả đưa thừa trường vào envelope-like object → phải bị lọc
    const env = {
      ...envelope("network.packet_routing", NET_CONFIG),
      api_key: "LEAK",
      analysis: { roles: ["x"] },
    } as SimulationEnvelope & { api_key: string };
    store.record(env, null);
    store.touch(store.list()[0].id, { lastCursor: 1, visualMode: "2d" });

    const raw = storage.getItem("algosim.history.v1")!;
    expect(raw).not.toContain("LEAK");
    expect(raw).not.toContain("api_key");
    for (const forbidden of ["prediction", "branch", "camera", "webgl"]) {
      expect(raw.toLowerCase()).not.toContain(forbidden);
    }
    const item = JSON.parse(raw)[0];
    expect(Object.keys(item).sort()).toEqual(
      [
        "id",
        "schemaVersion",
        "title",
        "simulationId",
        "domain",
        "envelope",
        "originalInput",
        "createdAt",
        "updatedAt",
        "lastViewedAt",
        "lastCursor",
        "visualMode",
      ].sort(),
    );
  });
});

describe("(26) sống sót qua reload (instance mới, cùng storage)", () => {
  it("store mới đọc lại được item + tiến độ", () => {
    const storage = fakeStorage();
    const first = createHistoryStore(storage);
    const item = first.record(envelope("network.packet_routing", NET_CONFIG), "đề");
    first.touch(item.id, { lastCursor: 3, visualMode: "3d" });

    const reloaded = createHistoryStore(storage);
    const got = reloaded.list()[0];
    expect(got.id).toBe(item.id);
    expect(got.lastCursor).toBe(3);
    expect(got.visualMode).toBe("3d");
    expect(got.envelope.simulation_id).toBe("network.packet_routing");
  });
});
