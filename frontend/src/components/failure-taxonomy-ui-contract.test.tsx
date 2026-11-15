import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { AxoClientError, analyzeViaServer } from "../llm/client";
import { describeComposerError, describeHomeRefusal } from "./ProblemInput";
import { UnsupportedNotice } from "./SimulationWorkspace";

describe("Stage P0 — Frontend Failure Taxonomy & HTTP 503 Consumer Contract", () => {
  it("describeHomeRefusal enforces HFOI-F6: UNKNOWN cause never blames problem or asks to add missing data", () => {
    const unverified = describeHomeRefusal({
      status: "unsupported",
      failure_category: "insufficient_specification",
      reason_code: "MISSING_DIMENSION",
      refusal_cause: "UNKNOWN",
      reason: "internal",
      learner_reason: "Hệ chưa xác định đủ dữ kiện từ đề.",
    } as any);
    expect(unverified.title).toBe("Hệ thống chưa xác định được duy nhất hình");
    expect(unverified.hint).not.toContain("bổ sung dữ kiện");
    expect(unverified.title).not.toContain("Đề bài chưa đủ dữ kiện");

    const sourceProved = describeHomeRefusal({
      status: "unsupported",
      failure_category: "insufficient_specification",
      reason_code: "MISSING_DIMENSION",
      refusal_cause: "SOURCE",
      reason: "internal",
      learner_reason: "Các dữ kiện đã nêu trong đề chưa xác định duy nhất đại lượng cần tính.",
    } as any);
    expect(sourceProved.title).toBe("Đề bài chưa đủ dữ kiện để dựng hình");
    expect(sourceProved.hint).toContain("bổ sung dữ kiện");
  });

  it("describeHomeRefusal separates NON_POSITIVE_LENGTH, Route-D SOURCE conflicts, and capability_gap", () => {
    const nonPos = describeHomeRefusal({
      status: "unsupported",
      failure_category: "geometry_generation_failed",
      reason_code: "NON_POSITIVE_LENGTH",
      refusal_cause: "SOURCE",
      reason: "AB = 0",
      learner_reason: "Số đo độ dài trong đề phải dương.",
    } as any);
    expect(nonPos.title).toBe("Số đo độ dài trong đề cần lớn hơn 0");
    expect(nonPos.hint).toContain("độ dài dương");

    const conflict = describeHomeRefusal({
      status: "unsupported",
      failure_category: "geometry_generation_failed",
      reason_code: "INCONSISTENT_FACTS",
      refusal_cause: "SOURCE",
      reason: "conflict",
      learner_reason: "Các dữ kiện trong đề mâu thuẫn nhau.",
    } as any);
    expect(conflict.title).toBe("Dữ kiện đề bài chưa nhất quán");

    const cap = describeHomeRefusal({
      status: "unsupported",
      failure_category: "capability_gap",
      reason_code: "MISSING_DIMENSION",
      refusal_cause: "UNKNOWN",
      reason: "deduction_gap",
      learner_reason:
        "Hệ đã đọc các giả thiết trong đề nhưng chưa có quy tắc suy diễn tất định cho tổ hợp quan hệ này, nên dừng lại thay vì dựng một hình gần đúng.",
    } as any);
    expect(cap.title).toBe("Axo chưa hỗ trợ phép dựng này");
    expect(cap.hint).not.toContain("bổ sung dữ kiện");
  });

  it("analyzeViaServer + describeComposerError handle HTTP 503 MISSING_API_KEY local_understanding without retries and honor rewrite_may_help", async () => {
    let calls = 0;
    const realFetch = globalThis.fetch;
    const msgUnsupported =
      "Đề dùng một phép dựng điểm mà hệ thống chưa hỗ trợ. Phần chưa đọc được: «Gọi M là điểm đối xứng của A qua C». Máy chủ chưa bật kết nối đọc đề bằng AI nên chưa xử lý thêm được bài này.";
    globalThis.fetch = (async () => {
      calls += 1;
      return new Response(
        JSON.stringify({
          error: msgUnsupported,
          reason_code: "MISSING_API_KEY",
          failure_kind: "INFRASTRUCTURE_FAILURE",
          failure_dimension: "INFRASTRUCTURE_AVAILABILITY",
          taxonomy_class: "INFRASTRUCTURE_UNAVAILABLE",
          local_understanding: {
            root_cause: "UNSUPPORTED_POINT_CONSTRUCTION",
            failure_dimension: "IMPLEMENTATION_CAPABILITY",
            taxonomy_class: "CAPABILITY_UNSUPPORTED",
            message: "Đề dùng một phép dựng điểm mà hệ thống chưa hỗ trợ.",
            unread_excerpts: ["Gọi M là điểm đối xứng của A qua C"],
            rewrite_may_help: false,
          },
        }),
        { status: 503 },
      );
    }) as typeof fetch;

    let caught: unknown;
    try {
      await analyzeViaServer({ type: "text", content: "Cho hình chóp S.ABCD..." });
    } catch (e) {
      caught = e;
    } finally {
      globalThis.fetch = realFetch;
    }

    expect(calls).toBe(1);
    expect(caught).toBeInstanceOf(AxoClientError);
    const contract = (caught as AxoClientError).toContract();
    expect(contract.localUnderstanding?.rewriteMayHelp).toBe(false);
    expect(contract.localUnderstanding?.taxonomyClass).toBe("CAPABILITY_UNSUPPORTED");

    const pres = describeComposerError(contract.message, null, contract);
    expect(pres?.title).toBe("Đề bài dùng dữ kiện hệ thống chưa hỗ trợ xử lý cục bộ");
    expect(pres?.description).toBe(msgUnsupported);
  });

  it("UnsupportedNotice renders specific titles ONLY when Route-D invalid data has refusal_cause === 'SOURCE'", () => {
    const sourceNonPos = renderToString(
      <UnsupportedNotice
        unsupported={{
          reason: "Số đo độ dài trong đề phải dương.",
          learner_reason: "Số đo độ dài trong đề phải dương.",
          failure_category: "geometry_generation_failed",
          reason_code: "NON_POSITIVE_LENGTH",
          refusal_cause: "SOURCE",
        }}
      />,
    ).replace(/<!--.*?-->/g, "");
    expect(sourceNonPos).toContain("SỐ ĐO KHÔNG DƯƠNG");
    expect(sourceNonPos).not.toContain('class="notes"');

    const unknownDegenerate = renderToString(
      <UnsupportedNotice
        unsupported={{
          reason: "Các dữ kiện trong đề chưa xác định được một hình hợp lệ.",
          learner_reason: "Các dữ kiện trong đề chưa xác định được một hình hợp lệ.",
          failure_category: "geometry_generation_failed",
          reason_code: "DEGENERATE_SOLID",
          refusal_cause: "UNKNOWN",
        }}
      />,
    ).replace(/<!--.*?-->/g, "");
    expect(unknownDegenerate).toContain("CHƯA DỰNG ĐƯỢC MÔ PHỎNG");
    expect(unknownDegenerate).not.toContain("HÌNH SUY BIẾN");
  });
});
