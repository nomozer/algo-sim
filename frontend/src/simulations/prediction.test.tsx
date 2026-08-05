import { describe, expect, it, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { PredictionBar } from "../components/PredictionBar";
import { makeAlgorithmModule } from "./domains/algorithm";
import { makeNetworkModule } from "./domains/network";
import { makeAndGateModule } from "./domains/logic";
import { registerAllSimulations } from "./index";
import { useAppStore } from "../state/store";
import type { AlgorithmSimState } from "./domains/algorithm";
import type { NetworkState } from "./domains/network/model";
import type { SimulationEnvelope } from "./types";

/**
 * M8-PRE-LIP — BẰNG CHỨNG TƯƠNG TÁC HỌC TẬP (không phải practice_activity đầy đủ).
 *
 * Chứng minh: CÙNG một optional capability (`predict?`) + CÙNG một UI dùng chung
 * (PredictionBar) phục vụ được HAI domain khác nhau, với vòng lặp:
 *   Quan sát → Dự đoán/Chọn → Nộp → ENGINE TẤT ĐỊNH chấm → phản hồi là dữ liệu
 *   → mô phỏng canonical KHÔNG ĐỔI.
 *
 * KHÔNG có LLM, KHÔNG có network call (test-setup.ts đã chặn fetch).
 */

registerAllSimulations();

const netMod = makeNetworkModule();
const algoMod = makeAlgorithmModule("find_max");

// client — router — server ; và client — switch — server (hai đường CÙNG dài 2 chặng)
const NET_CONFIG = {
  nodes: [
    { id: "pc", type: "client" as const },
    { id: "r1", type: "router" as const },
    { id: "sw", type: "switch" as const },
    { id: "srv", type: "server" as const },
  ],
  links: [
    ["pc", "r1"],
    ["r1", "srv"],
    ["pc", "sw"],
    ["sw", "srv"],
  ] as [string, string][],
  source: "pc",
  destination: "srv",
  notes: null,
};

const ALGO_CONFIG = {
  problem: { summary: "Tìm max", input: "dãy", output: "max" },
  algorithm_id: "find_max" as const,
  data: { array: [7.5, 9, 6] },
  data_generated: false,
  notes: null,
};

function netState(): NetworkState {
  const r = netMod.validateConfig(NET_CONFIG);
  if (!r.ok) throw new Error(r.error);
  return netMod.init(r.config);
}

function algoState(): AlgorithmSimState {
  const r = algoMod.validateConfig(ALGO_CONFIG);
  if (!r.ok) throw new Error(r.error);
  return algoMod.init(r.config);
}

// ── 1–2. NETWORK: chọn chặng kế tiếp ──────────────────────────────────────

describe("network — dự đoán chặng kế tiếp (BFS là ground truth)", () => {
  it("trước đây watch-only: nay CÓ challenge thật ở nút xuất phát", () => {
    const s = netState();
    const ch = netMod.predict!.challenge(s)!;
    expect(ch).not.toBeNull();
    expect(ch.question).toContain("chặng KẾ TIẾP");
    // lựa chọn = các nút NỐI TRỰC TIẾP với nút hiện tại
    expect(ch.options.map((o) => o.id).sort()).toEqual(["r1", "sw"]);
  });

  it("chọn ĐÚNG chặng chuẩn → correct", () => {
    const s = netState();
    const expected = s.route[1];
    const res = netMod.predict!.check(s, expected);
    expect(res.verdict).toBe("correct");
    expect(res.expectedId).toBe(expected);
  });

  it("chọn SAI → học sinh được phép sai; route canonical KHÔNG đổi; phát ngôn thận trọng", () => {
    const s = netState();
    const before = JSON.stringify(s);
    const canonical = s.route[1];
    const other = canonical === "r1" ? "sw" : "r1";

    const res = netMod.predict!.check(s, other);

    expect(res.verdict).toBe("incorrect");
    expect(res.expectedId).toBe(canonical);
    // CHỈ được nói "không phải chặng trên đường ngắn nhất engine BFS chọn"
    expect(res.message).toContain("đường đi ngắn nhất mà engine BFS đã tính");
    // TUYỆT ĐỐI không được tuyên bố đường đó là bất khả thi
    expect(res.message).not.toContain("không thể");
    // Ở topo này lối kia CŨNG ngắn nhất → phải nói rõ, không để hiểu nhầm
    expect(res.message).toContain("CŨNG cho một đường ngắn nhất");
    // canonical bất biến (check là hàm thuần)
    expect(JSON.stringify(s)).toBe(before);
    expect(s.route).toEqual(netState().route);
  });

  it("nút không nối trực tiếp → engine nói đúng điều nó chứng minh được", () => {
    const s = netState();
    const res = netMod.predict!.check(s, "srv"); // srv không kề pc
    expect(res.verdict).toBe("incorrect");
    expect(res.message).toContain("không nối trực tiếp");
  });

  it("đã tới đích → không còn gì để dự đoán (unsupported_to_verify)", () => {
    let s = netState();
    s = netMod.timeline!.goToStep(s, s.steps.length - 1);
    expect(netMod.predict!.challenge(s)).toBeNull();
    expect(netMod.predict!.check(s, "r1").verdict).toBe("unsupported_to_verify");
  });
});

// ── 3–4. ALGORITHM: dự đoán hệ quả của phép so sánh ───────────────────────

describe("algorithm — dự đoán bám TRACE THẬT", () => {
  it("ở điểm quyết định có challenge; ngoài điểm quyết định thì không", () => {
    const s = algoState();
    // bước 0 là khởi tạo (assign_var), chưa có so sánh → không hỏi
    expect(algoMod.predict!.challenge(s)).toBeNull();

    const atCompare = algoMod.timeline!.goToStep(s, 1) as AlgorithmSimState;
    const ch = algoMod.predict!.challenge(atCompare);
    expect(ch).not.toBeNull();
    expect(ch!.options.map((o) => o.id)).toEqual(["yes", "no"]);
  });

  it("đáp án đúng lấy từ SỰ KIỆN THẬT của bước kế tiếp (max 7.5 vs 9 → có cập nhật)", () => {
    const s = algoState();
    const at = algoMod.timeline!.goToStep(s, 1) as AlgorithmSimState;
    const trace = at.trace;
    const truth = trace.steps[2].events.some((e) => e.type === "assign_var");

    const good = algoMod.predict!.check(at, truth ? "yes" : "no");
    expect(good.verdict).toBe("correct");

    const bad = algoMod.predict!.check(at, truth ? "no" : "yes");
    expect(bad.verdict).toBe("incorrect");
    // phản hồi TẤT ĐỊNH, có bằng chứng trích từ trace
    expect(bad.expectedId).toBe(truth ? "yes" : "no");
    expect(bad.message.length).toBeGreaterThan(20);
  });

  it("dự đoán KHÔNG đụng canonical state/timeline", () => {
    const s = algoState();
    const at = algoMod.timeline!.goToStep(s, 1) as AlgorithmSimState;
    const before = JSON.stringify(at);
    algoMod.predict!.check(at, "yes");
    algoMod.predict!.check(at, "no");
    expect(JSON.stringify(at)).toBe(before);
  });
});

// ── 6. Module KHÔNG khai capability → không có affordance ─────────────────

describe("mặc định an toàn", () => {
  it("logic.and_gate không khai `predict` → không có capability", () => {
    expect(makeAndGateModule().predict).toBeUndefined();
  });
});

// ── 5 + 7 + 8. UI DÙNG CHUNG + store: canonical không đổi ─────────────────

function envelopeFor(id: string, config: unknown): SimulationEnvelope {
  return {
    status: "ok",
    simulation_id: id,
    domain: id.split(".")[0] as SimulationEnvelope["domain"],
    visual_mode: "2d",
    title: "t",
    description: null,
    config,
    notes: null,
  };
}

describe("PredictionBar — MỘT UI cho NHIỀU domain", () => {
  beforeEach(() => useAppStore.getState().reset());

  /* UI-CLARITY W1 — hợp đồng ĐỔI: mặc định THU GỌN.
     Trước W1 thanh dự đoán bày sẵn câu hỏi + lựa chọn + nút "Kiểm tra" ở mọi
     bước có điểm quyết định, chiếm 19% diện tích thẻ (161px, đo trong Chrome).
     Nay mặc định chỉ còn một control nhỏ; câu hỏi chỉ hiện khi học sinh mở. */

  it("W1: mặc định THU GỌN — chỉ một control, KHÔNG bày câu hỏi (network)", () => {
    const html = renderToString(
      <PredictionBar module={netMod as never} state={netState()} busy={false} />,
    );
    expect(html).toContain("predict-inline");
    expect(html).toContain("Dự đoán bước này");
    // câu hỏi và lựa chọn CHƯA được bày ra
    expect(html).not.toContain("chặng KẾ TIẾP");
    expect(html).not.toContain("Router (r1)");
    // thẻ lớn `.predict-bar` chưa tồn tại ở trạng thái thu gọn
    expect(html).not.toContain("predict-bar");
  });

  it("W1: mặc định THU GỌN — CÙNG component, cùng hành vi ở domain algorithm", () => {
    const at = algoMod.timeline!.goToStep(algoState(), 1);
    const html = renderToString(
      <PredictionBar module={algoMod as never} state={at} busy={false} />,
    );
    expect(html).toContain("predict-inline");
    expect(html).toContain("Dự đoán bước này");
    expect(html).not.toContain("predict-bar");
  });

  it("W1: KHÔNG còn nút nộp riêng — mỗi đáp án LÀ hành động kiểm tra", () => {
    // Bằng chứng ở mã nguồn: không nơi nào trong PredictionBar dựng nút "Kiểm tra"
    // nữa. Quét nguồn thay vì quét HTML đã render, vì trạng thái MỞ không đạt
    // được qua SSR (ARCHITECTURE_MAP §8 #13: guard phải soi mã, không soi HTML).
    // Bóc chú thích trước khi quét — cùng lý do `tokens.test.ts` phải làm vậy:
    // chú thích ở đây CÓ nhắc tên nút đã gỡ để giải thích lịch sử, quét cả chú
    // thích thì test tự bắt chính nó.
    const src = readFileSync(
      new URL("../components/PredictionBar.tsx", import.meta.url), "utf-8",
    ).replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
    expect(src).not.toContain("Kiểm tra");
    expect(src).toContain("submitPrediction(o.id)");
  });

  it("W1: tự chạy (busy) KHÔNG render gì — chiều cao thẻ không giật theo bước", () => {
    /* Không phải bước nào cũng có điểm quyết định. Nếu lúc tự chạy vẫn vẽ nút
       thu gọn thì nó xuất hiện/biến mất theo từng bước (0 ↔ 30px), tức đúng
       kiểu giật mà W1 sinh ra để bỏ. Đo trong Chrome trước W1: thẻ nhảy
       776px → 585px khi tự chạy. */
    const at = algoMod.timeline!.goToStep(algoState(), 1);
    const html = renderToString(
      <PredictionBar module={algoMod as never} state={at} busy={true} />,
    );
    expect(html).toBe("");
  });

  it("module KHÔNG khai predict (logic) → PredictionBar không render gì", () => {
    const logic = makeAndGateModule();
    const html = renderToString(
      <PredictionBar module={logic as never} state={logic.init({ inputA: 0, inputB: 0, notes: null })} busy={false} />,
    );
    expect(html).toBe("");
  });

  it("nộp dự đoán qua store: kết quả là DỮ LIỆU, engine state KHÔNG đổi", () => {
    useAppStore.getState().loadEnvelope(envelopeFor("network.packet_routing", NET_CONFIG));
    const engineBefore = JSON.stringify(useAppStore.getState().active!.state);

    const canonical = (useAppStore.getState().active!.state as NetworkState).route[1];
    useAppStore.getState().submitPrediction(canonical);

    const after = useAppStore.getState();
    expect(after.prediction!.verdict).toBe("correct");
    // canonical simulation BẤT BIẾN — dự đoán sống ở nhánh dữ liệu RIÊNG
    expect(JSON.stringify(after.active!.state)).toBe(engineBefore);
  });

  it("đổi bước → dự đoán cũ bị xoá (gắn với một thời điểm)", () => {
    useAppStore.getState().loadEnvelope(envelopeFor("network.packet_routing", NET_CONFIG));
    const canonical = (useAppStore.getState().active!.state as NetworkState).route[1];
    useAppStore.getState().submitPrediction(canonical);
    expect(useAppStore.getState().prediction).not.toBeNull();

    useAppStore.getState().nextStep();
    expect(useAppStore.getState().prediction).toBeNull();
  });

  it("module không khai predict → submitPrediction là NO-OP", () => {
    useAppStore.getState().loadEnvelope(envelopeFor("logic.and_gate", { inputA: 0, inputB: 0 }));
    useAppStore.getState().submitPrediction("yes");
    expect(useAppStore.getState().prediction).toBeNull();
  });
});
