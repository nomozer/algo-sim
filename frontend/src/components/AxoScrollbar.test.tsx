import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { readFileSync } from "node:fs";
import { AxoScrollbar } from "./AxoScrollbar";
import App from "../App";

describe("AxoScrollbar — Manus-style Floating Overlay Scrollbar Contracts", () => {
  it("khởi tạo không render HTML dư thừa khi không thể cuộn trong môi trường SSR", () => {
    const html = renderToString(<AxoScrollbar />);
    expect(html).toBe("");
  });

  it("App bao gồm component AxoScrollbar ở tầng trang", () => {
    const appHtml = renderToString(<App />);
    expect(appHtml).toContain('class="app-root');
    expect(appHtml).toContain('class="nav-bar"');
  });

  it("global.css định nghĩa các lớp css cho overlay scrollbar và ẩn thanh cuộn hệ thống", () => {
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toContain(".axo-scrollbar-track");
    expect(css).toContain(".axo-scrollbar-thumb");
    expect(css).toContain(".axo-scrollbar-thumb.is-visible");
    expect(css).toContain(".axo-custom-scroll");
    expect(css).toContain("scrollbar-width: none;");
  });

  it("global.css giữ bất biến scrollbar-gutter: stable trên html để thỏa mãn kiểm thử", () => {
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toMatch(/html\s*\{[^}]*scrollbar-gutter:\s*stable;/s);
    expect(css).toMatch(/html\s*\{[^}]*scrollbar-width:\s*none;/s);
  });
});
