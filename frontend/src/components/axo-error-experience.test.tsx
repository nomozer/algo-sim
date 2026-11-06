import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import { publicCatalog } from "../data/offline-catalog";
import { AxoClientError } from "../llm/client";
import { registerAllSimulations } from "../simulations";
import { useAppStore } from "../state/store";
import {
  AxoErrorExperience,
  classifyAxoErrorState,
  resolveLocationRoute,
} from "./AxoErrorExperience";
import { ErrorBoundary } from "./ErrorBoundary";
import { describeComposerError } from "./ProblemInput";
import { SessionCard } from "./SessionCard";
import { SimulationWorkspace } from "./SimulationWorkspace";

registerAllSimulations();

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

describe("AXO Error Experience & Unbreakable Escape Navigation (§7–§8)", () => {
  beforeEach(() => {
    registerAllSimulations();
    useAppStore.getState().reset();
    syncStoreForSSR();
  });

  it("1. Route Not Found (404): phân loại đúng URL không tồn tại và render minh họa 3D wireframe 404 riêng trong nền sáng Axo", () => {
    expect(resolveLocationRoute("/", "", "").kind).toBe("view");
    expect(resolveLocationRoute("/library", "", "")).toEqual({
      kind: "view",
      view: "library",
    });
    expect(resolveLocationRoute("/history", "", "")).toEqual({
      kind: "view",
      view: "history",
    });
    expect(resolveLocationRoute("/simulation/thiet-dien-chop", "", "")).toEqual({
      kind: "sample",
      sampleId: "thiet-dien-chop",
    });
    expect(resolveLocationRoute("/khong-ton-tai", "", "")).toEqual({
      kind: "not_found",
      requestedPath: "/khong-ton-tai",
    });
    expect(resolveLocationRoute("/simulation/khong-co-bai-nay", "", "")).toEqual({
      kind: "not_found",
      requestedPath: "/simulation/khong-co-bai-nay",
    });

    useAppStore.getState().syncLocationRoute("/khong-ton-tai", "", "");
    expect(useAppStore.getState().view).toBe("not_found");
    syncStoreForSSR();

    const html = renderToString(<App />);
    expect(html).toContain('data-error-kind="not_found"');
    expect(html).toContain('data-illustration="axo-404-polyhedron"');
    expect(html).toContain("404");
    expect(html).toContain('class="nav-bar"');
    expect(html).not.toContain("Quay lại");
    expect(html).toContain("Về trang chủ");
    expect(html).toContain("Mở Thư viện");
    expect(html).not.toContain("<canvas");
  });

  it("2. Simulation Render Failure: ErrorBoundary bắt lỗi render Scene3D, khôi phục thanh điều hướng trên cùng và ưu tiên nút 'Quay lại' thay vì 'Thử lại'", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    const sample = publicCatalog()[0]!;
    useAppStore.getState().openLibrary();
    useAppStore.getState().loadEnvelope(sample.envelope, sample.id);
    expect(useAppStore.getState().view).toBe("workspace");

    // Khi ErrorBoundary mien="main" bắt lỗi render trong workspace 3D:
    // 1) App nhận tín hiệu mainBoundaryCrashed để khôi phục <header class="nav-bar"> bên ngoài vùng crash
    // 2) Fallback render Category B (render_failure), KHÔNG giả mạo 404, KHÔNG lộ stack trace, KHÔNG đặt 'Thử lại' làm btn-primary
    let retried = false;
    const fallbackHtml = renderToString(
      <AxoErrorExperience
        kind="render_failure"
        onBack={() => useAppStore.getState().escapeFromError()}
        onGoHome={() => useAppStore.getState().goHome()}
        onOpenLibrary={() => useAppStore.getState().openLibrary()}
        onSecondaryRetry={() => {
          retried = true;
        }}
      />,
    );
    expect(fallbackHtml).toContain('data-error-kind="render_failure"');
    expect(fallbackHtml).toContain('data-illustration="axo-render-interrupted"');
    expect(fallbackHtml).not.toContain("404");
    expect(fallbackHtml).toMatch(/class="[^"]*btn-primary[^"]*"[^>]*>[\s\S]*?Quay lại/);
    expect(fallbackHtml).not.toMatch(/class="[^"]*btn-primary[^"]*"[^>]*>[\s\S]*?Thử lại/);
    expect(retried).toBe(false);

    // Kiểm tra ErrorBoundary gọi onCatch khi bắt ngoại lệ nhưng không lộ chi tiết kỹ thuật ra UI
    let caughtCount = 0;
    const boundary = new ErrorBoundary({
      mien: "main",
      onCatch: () => {
        caughtCount += 1;
      },
      children: null,
      fallback: () => (
        <AxoErrorExperience
          kind="render_failure"
          onBack={() => {}}
          onGoHome={() => {}}
          onOpenLibrary={() => {}}
        />
      ),
    });
    boundary.componentDidCatch(
      new Error("WebGLBuffer internal crash at Scene3D.ts:4421"),
      { componentStack: "\n    at Scene3DWorkspace" } as never,
    );
    boundary.state = { hong: true, soLanThuLai: 0 };
    expect(caughtCount).toBe(1);
    const renderedBoundary = renderToString(<>{boundary.render()}</>);
    expect(renderedBoundary).not.toContain("WebGLBuffer internal crash");
    expect(renderedBoundary).not.toContain("Scene3DWorkspace");
    spy.mockRestore();
  });

  it("3. Invalid / Unsupported Simulation: hợp đồng scene3d hỏng, mâu thuẫn toán học và phản hồi unsupported từ Backend phân loại vào Category C (không giả làm 404, không làm sập App)", () => {
    const sample = publicCatalog()[0]!;
    // Hợp đồng scene3d bị hỏng trong bản ghi hình học đang mở
    useAppStore.setState({
      view: "workspace",
      returnView: "history",
      hasInAppNavigation: true,
      active: {
        moduleId: "geometry.solid_mensuration",
        envelope: {
          ...sample.envelope,
          title: "Bản ghi kiểm thử thiếu hình 3D",
          scene3d: { malformed: true },
        } as unknown as typeof sample.envelope,
        config: sample.envelope.config,
        state: {},
      },
    });
    syncStoreForSSR();
    const appBrokenSceneHtml = renderToString(<App />);
    expect(appBrokenSceneHtml).toContain('data-error-kind="unsupported_simulation"');
    expect(appBrokenSceneHtml).toContain('data-illustration="axo-constraint-unclosed"');
    expect(appBrokenSceneHtml).not.toContain('data-error-kind="not_found"');
    expect(appBrokenSceneHtml).toContain("Quay lại");

    // Mâu thuẫn tọa độ toán học bị chặn bởi trình xác minh tất định ở Frontend
    const sampleScene3d = (sample.envelope as unknown as { scene3d: Record<string, unknown> }).scene3d;
    const contradictedScene = structuredClone(sampleScene3d);
    const objects = (contradictedScene.objects as Record<string, unknown>[]).map((obj) => {
      if (obj.id === "M" && obj.type === "point3") {
        return { ...obj, xyz: [9, 9, 9] };
      }
      return obj;
    });
    useAppStore.setState({
      view: "workspace",
      returnView: "library",
      active: {
        moduleId: "geometry.solid_mensuration",
        envelope: {
          ...sample.envelope,
          scene3d: { ...contradictedScene, objects },
        } as unknown as typeof sample.envelope,
        config: sample.envelope.config,
        state: {},
      },
    });
    syncStoreForSSR();
    const mathFailHtml = renderToString(<SimulationWorkspace />);
    expect(mathFailHtml).toContain("data-math-contradiction");
    expect(mathFailHtml).toContain('data-error-kind="unsupported_simulation"');

    // Phản hồi status: 'unsupported' từ Backend hiển thị trong SimulationWorkspace
    useAppStore.setState({
      view: "workspace",
      hasInAppNavigation: true,
      active: null,
      unsupported: {
        status: "unsupported",
        reason: "kỹ thuật nội bộ",
        learner_reason: "Đề bài còn thiếu độ dài cạnh bên nên hệ chưa thể dựng duy nhất.",
        failure_category: "insufficient_specification",
        refusal_cause: "SOURCE",
        error_code: "GIVEN_VALUE_NOT_IN_SOURCE",
      },
    });
    syncStoreForSSR();
    const refusalHtml = renderToString(<SimulationWorkspace />);
    expect(refusalHtml).toContain('data-error-kind="unsupported_simulation"');
    expect(refusalHtml).toContain("CHƯA ĐỦ DỮ KIỆN");
    expect(refusalHtml).toContain("thiếu độ dài cạnh bên");
    expect(refusalHtml).not.toContain("GIVEN_VALUE_NOT_IN_SOURCE");
    expect(refusalHtml).toContain("Quay lại");
  });

  it("4. Network / Data Loading Failure: phân loại từ hợp đồng lỗi có kiểu (AxoClientError), tuyệt đối không đoán từ chuỗi message", () => {
    const opaqueNetErr = new AxoClientError({
      kind: "network",
      code: "NETWORK_UNREACHABLE",
      message: "opaque_transport_token_without_keywords_991",
    });
    expect(
      classifyAxoErrorState({
        clientFailure: {
          kind: opaqueNetErr.kind,
          code: opaqueNetErr.code,
          message: opaqueNetErr.message,
        },
      }),
    ).toBe("network_failure");

    // Kể cả khi message không chứa chữ 'Không kết nối được máy chủ', describeComposerError vẫn nhận diện đúng lỗi mạng nhờ contract có kiểu
    const composerPres = describeComposerError(opaqueNetErr.message, null, {
      kind: opaqueNetErr.kind,
      code: opaqueNetErr.code,
      message: opaqueNetErr.message,
    });
    expect(composerPres?.title).toBe("Không kết nối được máy chủ");

    useAppStore.getState().reportNetworkFailure(opaqueNetErr);
    syncStoreForSSR();
    const netHtml = renderToString(<App />);
    expect(netHtml).toContain('data-error-kind="network_failure"');
    expect(netHtml).toContain('data-illustration="axo-network-link"');
    expect(netHtml).not.toContain('data-error-kind="not_found"');
    expect(netHtml).not.toContain("opaque_transport_token_without_keywords_991");
    expect(netHtml).toContain("Về trang chủ");
    expect(netHtml).toContain("Mở Thư viện");
  });

  it("5. Điều hướng thoát lỗi không bị kẹt và không tạo vòng lặp: deep-link fallback về Trang chủ, đi từ Thư viện quay lại đúng Thư viện", () => {
    // Kịch bản A: Deep-link trực tiếp vào URL không tồn tại (chưa có lịch sử điều hướng hợp lệ trong phiên)
    useAppStore.getState().syncLocationRoute("/duong-dan-hong", "", "");
    expect(useAppStore.getState().view).toBe("not_found");
    const escapedTargetA = useAppStore.getState().escapeFromError();
    expect(escapedTargetA).toBe("home");
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().routeFailure).toBeNull();
    expect(useAppStore.getState().active).toBeNull();

    // Kịch bản B: Người dùng đi từ Trang chủ -> Thư viện -> mở mô phỏng -> gặp lỗi -> bấm 'Quay lại'
    useAppStore.getState().reset();
    useAppStore.getState().openLibrary();
    const sample = publicCatalog()[0]!;
    useAppStore.getState().loadEnvelope(sample.envelope, sample.id);
    expect(useAppStore.getState().view).toBe("workspace");

    const escapedTargetB = useAppStore.getState().escapeFromError();
    expect(escapedTargetB).toBe("library");
    expect(useAppStore.getState().view).toBe("library");
    expect(useAppStore.getState().active).toBeNull();

    // Kịch bản C: Từ Thư viện nhảy vào đường dẫn 404 -> bấm 'Quay lại' trở về đúng Thư viện, bấm thêm lần nữa không quay ngược lại 404
    useAppStore.getState().syncLocationRoute("/khong-co-trang", "", "");
    expect(useAppStore.getState().view).toBe("not_found");
    const escapedTargetC = useAppStore.getState().escapeFromError();
    expect(escapedTargetC).toBe("library");
    expect(useAppStore.getState().view).toBe("library");
    const escapedAgain = useAppStore.getState().escapeFromError();
    expect(escapedAgain).not.toBe("not_found");
  });

  it("6. Minh họa lỗi tuân thủ prefers-reduced-motion và không dùng WebGL/canvas dễ gây lỗi lần hai", () => {
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toMatch(/@media\s*\(\s*prefers-reduced-motion:\s*reduce\s*\)[\s\S]*?\.axo-error-svg-float/);
  });

  it("7. Khóa hồi quy điều hướng nâng cao: App hiển thị được variant=refusal trên /workspace, ErrorBoundary gọi thuLai() ở mọi nút thoát, NOT_FOUND/HTTP_ERROR có mô tả kiểu hóa, và SessionCard chịu được bản ghi 3D hỏng", () => {
    // 7A: App.tsx gọi thuLai() trên cả onBack, onGoHome và onOpenLibrary để không kẹt khi resetKey giữ nguyên
    const appSrc = readFileSync(new URL("../App.tsx", import.meta.url), "utf8");
    expect(appSrc).toMatch(/onBack=\{\(\)\s*=>\s*\{[\s\S]*?escapeFromError\(\);[\s\S]*?thuLai\(\);/);
    expect(appSrc).toMatch(/onGoHome=\{\(\)\s*=>\s*\{[\s\S]*?goHome\(\);[\s\S]*?thuLai\(\);/);
    expect(appSrc).toMatch(/onOpenLibrary=\{\(\)\s*=>\s*\{[\s\S]*?openLibrary\(\);[\s\S]*?thuLai\(\);/);

    // 7B: Khi unsupported !== null và người dùng mở /workspace, <App /> mount được AxoErrorExperience(variant="refusal")
    useAppStore.getState().loadUnsupported({
      status: "unsupported",
      reason: "Đề bài thiếu giả thiết xác định vị trí điểm S.",
      failure_category: "ambiguous_input",
      error_code: "AMBIGUOUS_INPUT",
    });
    useAppStore.getState().syncLocationRoute("/workspace", "", "");
    syncStoreForSSR();
    expect(useAppStore.getState().view).toBe("workspace");
    const appRefusalHtml = renderToString(<App />);
    expect(appRefusalHtml).toContain('data-error-kind="unsupported_simulation"');
    expect(appRefusalHtml).toContain("is-refusal");

    // 7C: ProblemInput phân loại tường minh cả NOT_FOUND và HTTP_ERROR qua clientFailure
    expect(
      describeComposerError("404", null, {
        kind: "http",
        code: "NOT_FOUND",
        status: 404,
        message: "Tài nguyên phân tích không tồn tại.",
      })?.title,
    ).toBe("Không tìm thấy tài nguyên yêu cầu");
    expect(
      describeComposerError("500", null, {
        kind: "http",
        code: "HTTP_ERROR",
        status: 500,
        message: "Máy chủ gặp sự cố nội bộ.",
      })?.title,
    ).toBe("Máy chủ trả về lỗi khi phân tích");

    // 7D: SessionCard không crash HomeView/HistoryView khi localStorage chứa bản ghi hình học có scene3d hỏng
    const brokenEntry = {
      id: "broken-hist-1",
      title: "Bản ghi 3D lỗi cấu trúc",
      originalInput: "Cho hình chóp...",
      domain: "geometry",
      createdAt: "2026-11-01T10:00:00Z",
      envelope: {
        domain: "geometry",
        title: "Bản ghi 3D lỗi cấu trúc",
        scene3d: {
          free_objects: ["A"],
          objects: [{ id: "A", type: "point3", xyz: "not_a_tuple_crash" }],
          events: [{ step_index: 0, action: "INIT" }],
        },
      },
    };
    const cardHtml = renderToString(
      <SessionCard
        item={brokenEntry as unknown as Parameters<typeof SessionCard>[0]["item"]}
        onOpen={() => {}}
      />,
    );
    expect(cardHtml).toContain("Bản ghi 3D lỗi cấu trúc");
  });
});
