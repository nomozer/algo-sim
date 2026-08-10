import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { makeNetworkModule } from "./index";
import { NetworkWorkspace } from "./ui";

/**
 * M7.FREEZE: sau khi gỡ bố cục khỏi engine state, renderer 2D phải TỰ tính vị
 * trí và vẽ đúng như trước. Đây là bằng chứng "renderer chỉ đọc state ngữ nghĩa
 * rồi tự lo trình bày" — đúng thứ cho phép M8 gắn renderer 3D vào CÙNG module.
 */

const mod = makeNetworkModule();

const config = {
  nodes: [
    { id: "client", type: "client" as const },
    { id: "router", type: "router" as const },
    { id: "isp", type: "isp" as const },
    { id: "server", type: "server" as const },
  ],
  links: [
    ["client", "router"],
    ["router", "isp"],
    ["isp", "server"],
  ] as [string, string][],
  source: "client",
  destination: "server",
  notes: null,
};

describe("network renderer 2D — tự lo bố cục", () => {
  it("vẽ đủ nút, liên kết, gói tin; viewBox do renderer tính", () => {
    const state = mod.init(config);
    const html = renderToString(
      <NetworkWorkspace config={config} state={state} busy={false} dispatch={() => {}} />,
    );
    // viewBox lấy từ layout2d của renderer (4 nút trên route: 80*2 + 3*150 = 610)
    expect(html).toContain('viewBox="0 0 610 160"'); // W4B-2S: cao thêm 20 cho nhãn dưới hình
    // đủ 4 nút + nhãn loại
    for (const id of ["client", "router", "isp", "server"]) expect(html).toContain(id);
    expect(html).toContain("Máy khách");
    expect(html).toContain("Máy chủ");
    /* W4B-2S — ĐỔI TIỀN ĐỀ, có chủ đích.
       Bản cũ đếm "4 nút = 4 <circle>", tức khoá đúng cái lỗi wave này gỡ: mọi
       vai trò miền vẽ chung một hình tròn. Nay thiết bị là HÌNH THEO VAI TRÒ
       (`<path>` từ `nodeGlyph`), còn `<circle>` chỉ còn dành cho gói tin và
       vòng ngắm đích — nhờ vậy gói tin phân biệt được với thiết bị bằng HÌNH,
       không phải bằng màu. */
    expect(html.match(/<line/g) ?? []).toHaveLength(3);
    // 4 thiết bị × (1 outline + ≥0 chi tiết) ⇒ ít nhất 4 path.
    expect((html.match(/<path/g) ?? []).length).toBeGreaterThanOrEqual(4);
    // gói tin (1) + vòng ngắm đích (2) — KHÔNG còn vòng tròn nào là thiết bị.
    expect((html.match(/<circle/g) ?? []).length).toBe(3);
    // (SHELL-N) thuyết minh do khe của shell dựng — renderer chỉ lo BỐ CỤC
    expect(mod.narrate!(state, config)!.text).toContain("Tạo gói tin"); // bước 0
  });

  it("gói tin dịch chuyển theo bước — vị trí do renderer suy từ packetAt", () => {
    const s0 = mod.init(config);
    const s2 = mod.timeline!.goToStep(s0, 2); // gói tin ở "isp"
    const html0 = renderToString(
      <NetworkWorkspace config={config} state={s0} busy={false} dispatch={() => {}} />,
    );
    const html2 = renderToString(
      <NetworkWorkspace config={config} state={s2} busy={false} dispatch={() => {}} />,
    );
    expect(html0).not.toBe(html2); // cảnh đổi theo bước
    // (SHELL-N) thuyết minh bước 2 đến từ `narrate`, không từ renderer
    expect(mod.narrate!(s2, config)!.text).toContain("chuyển tới");
  });
});
