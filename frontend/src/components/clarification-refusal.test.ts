import { describe, expect, it } from "vitest";
import type { AnalysisUnsupported } from "../core/types";
import { docPhanHoiPhanTich } from "../llm/client";
import { describeHomeRefusal } from "./ProblemInput";
import live from "./__fixtures__/live-missing-dimension-refusal.response.json";

// Real /api/analyze response of /10 case N01 ("Vẽ hình chóp S.ABC có đáy là tam giác đều.", local-only, AxoV9): the
// backend refuses AMBIGUOUS_FACT with a verified `route-d-clarification/1` (MISSING_DATA) but labels the envelope
// `capability_gap`; /10 showed "Axo chưa hỗ trợ phép dựng này" instead of the clarification question.
describe("missing-data refusal surfaces the verified clarification question", () => {
  it("shows the server's question, not 'chưa hỗ trợ'", () => {
    const view = docPhanHoiPhanTich(live) as AnalysisUnsupported;
    expect(view.clarification?.question).toMatch(/nói rõ các số đo/);
    const shown = describeHomeRefusal(view);
    expect(shown.title).toBe("Đề bài cần thêm dữ kiện để dựng hình");
    expect(shown.body).toBe(view.clarification!.question);
    expect(JSON.stringify(shown)).not.toMatch(/chưa hỗ trợ|AMBIGUOUS_FACT|capability_gap|MISSING_DATA/);
  });

  it("an ambiguity clarification gets its own title", () => {
    const base = docPhanHoiPhanTich(live) as AnalysisUnsupported;
    const view = { ...base, clarification: { ...base.clarification!, kind: "ambiguous", nlu_class: "AMBIGUOUS" } } as AnalysisUnsupported;
    expect(describeHomeRefusal(view).title).toBe("Đề bài có chỗ cần viết rõ hơn");
  });

  it("without a clarification a real capability gap keeps its message", () => {
    const base = docPhanHoiPhanTich(live) as AnalysisUnsupported;
    const { clarification: _c, ...rest } = base;
    expect(describeHomeRefusal(rest as AnalysisUnsupported).title).toBe("Axo chưa hỗ trợ phép dựng này");
  });

  it("an 'unsupported' clarification (no question) is not shown as a question", () => {
    const base = docPhanHoiPhanTich(live) as AnalysisUnsupported;
    const view = { ...base, clarification: { ...base.clarification!, kind: "unsupported", nlu_class: "VALID_BUT_UNSUPPORTED", question: null } } as AnalysisUnsupported;
    expect(describeHomeRefusal(view).title).toBe("Axo chưa hỗ trợ phép dựng này");
  });
});
