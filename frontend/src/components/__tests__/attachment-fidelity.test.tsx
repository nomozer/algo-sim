import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { ProblemInput, computePlusPopoverPosition } from "../ProblemInput";

describe("attachment fidelity", () => {
  it("renders a document name above its format label", () => {
    const file = new File(["doc"], "de-bai.docx", { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
    const html = renderToString(<ProblemInput initialAttachments={[{ id: "one", file, name: file.name, size: file.size, sizeFormatted: "3 B", ext: ".docx", kind: "document", status: "ready" }]} />);
    expect(html).toContain('class="file-card-format"');
    expect(html.indexOf('class="file-card-name-row"')).toBeLessThan(html.indexOf('class="file-card-format"'));
  });

  it("opens above the trigger when space is available even over composer content", () => {
    const pos = computePlusPopoverPosition({ triggerRect: {top:400,bottom:436,left:200,right:236,width:36,height:36}, menuWidth:224, menuHeight:86, viewportWidth:1000, viewportHeight:800, avoidRects:[{top:300,bottom:390,left:180,right:500}] });
    expect(pos.placement).toBe("top");
  });
});
