import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { displayBrand, pageTitle } from "./branding";
import { TEN_TRANG } from "./components/TopNav";
import { UnsupportedNotice } from "./components/SimulationWorkspace";

/**
 * Axo identity in the browser (run axo-postmerge-consolidation). The squash of the Hybrid /4 integration carried the
 * merge 75d88a31's "main's favicon removal is kept", so the tab showed the default icon; the tab title had never
 * left "AlgoSim". The favicon is the settled Axo mark: the same geometry as the header's `AxoMarkGeometry`.
 */
const read = (p: string) => readFileSync(new URL(p, import.meta.url), "utf8");
const paths = (svg: string) => [...svg.matchAll(/\bd="([^"]+)"/g)].map((m) => m[1].replace(/\s+/g, " ").trim());

describe("Axo branding in the browser", () => {
  it("index.html links the Axo favicon and names the tab Axo", () => {
    const html = read("../index.html");
    expect(html).toMatch(/<link rel="icon" type="image\/svg\+xml" href="\/favicon\.svg" \/>/);
    expect(html).toContain(`<title>${pageTitle(null)}</title>`);   // static title = what App sets on the home page
    expect(pageTitle(null).startsWith("Axo")).toBe(true);
    expect(html).not.toContain("AlgoSim");
    expect(html).not.toContain('href="data:,"');
  });

  it("the favicon is the header's Axo mark, not another icon", () => {
    const favicon = read("../public/favicon.svg");
    const icons = read("./components/icons.tsx");
    const mark = icons.slice(icons.indexOf("AxoMarkGeometry"), icons.indexOf("export const IconAxoLogo"));
    expect(paths(favicon)).toEqual(paths(mark));
    expect(favicon).toContain('transform="translate(18.0 59.5)"');
    expect(mark).toContain('transform="translate(18.0 59.5)"');
  });

  it("every page title names Axo", () => {
    expect(pageTitle(null)).toBe("Axo — Mô phỏng tương tác");
    expect(pageTitle(TEN_TRANG.library)).toBe("Thư viện | Axo");
    expect(pageTitle(TEN_TRANG.history)).toBe("Lịch sử | Axo");
    expect(pageTitle("Mô phỏng hình học 3D")).toBe("Mô phỏng hình học 3D | Axo");
  });

  it("learner-facing copy says Axo even when the server still writes the old name", () => {
    expect(displayBrand("AlgoSim chưa tạo được mô phỏng.")).toBe("Axo chưa tạo được mô phỏng.");
    const html = (u: Parameters<typeof UnsupportedNotice>[0]["unsupported"]) =>
      renderToString(<UnsupportedNotice unsupported={u} />);
    expect(html({ reason: "x",
      learner_reason: "Các dữ kiện mâu thuẫn nhau. AlgoSim dừng lại thay vì dựng một hình sai.",
      failure_category: "geometry_generation_failed" })).not.toContain("AlgoSim");
    expect(html({ reason: "x", failure_category: "out_of_scope" })).not.toContain("AlgoSim");
    expect(html({ reason: "AlgoSim chưa hỗ trợ." })).not.toContain("AlgoSim");
  });
});
