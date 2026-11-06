import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../App";
import { publicCatalog } from "../data/offline-catalog";
import { registerAllSimulations } from "../simulations";
import { __resetHistoryForTest, historyStore } from "../state/history";
import { useAppStore } from "../state/store";
import { HistoryView } from "./HistoryView";
import { HomeView } from "./HomeView";
import { LibraryView } from "./LibraryView";
import { SamplePreview } from "./SamplePreview";
import {
  AxoWorkspaceV62,
  SimulationWorkspace,
  moTaBuocDungHienThi,
} from "./SimulationWorkspace";
import { AccountSettingsModal, AdminWorkspaceView, AuthPageView } from "./AuthGate";
import { useAuthStore } from "../state/auth";
import {
  anchorOfGeometryStep,
  geometryStepCount,
  geometryStepList,
  type Scene3D,
} from "../simulations/domains/geometry/scene3d-model";
import { buildObject3D } from "../simulations/domains/geometry/scene3d-view";
import { withSubEntities } from "../simulations/domains/geometry/scene3d-subentities";
import { veKhongGian } from "../simulations/domains/geometry/scene3d-chart";

registerAllSimulations();

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

describe("Axo V2.7 Phase B — Header Logo, Homepage, Library & History (P3–P8)", () => {
  beforeEach(() => {
    registerAllSimulations();
    __resetHistoryForTest();
    useAppStore.getState().reset();
    useAppStore.setState({ history: [] });
    syncStoreForSSR();
  });

  it("P3 & Phase C.1 P1: Logo Axo (#btn-brand-home) có đúng SVG 22x22, chữ Axo 15px, padding 0 và không đổi nền/scale khi hover hoặc active", () => {
    const html = renderToString(<App />);
    expect(html).toContain('id="btn-brand-home"');
    expect(html).toContain('class="axo-logo-svg" width="22" height="22"');
    expect(html).toContain('<span class="nav-wordmark-text">Axo</span>');

    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toMatch(/\.axo-logo-btn\s*\{[^}]*gap:\s*7px;[^}]*padding:\s*0;[^}]*border-radius:\s*0;[^}]*font-size:\s*15px;[^}]*background:\s*transparent;/s);
    expect(css).toMatch(/\.axo-logo-btn:hover,\s*\.axo-logo-btn:active\s*\{[^}]*background:\s*transparent;[^}]*transform:\s*none;/s);
    expect(css).toMatch(/\.axo-logo-svg\s*\{[^}]*width:\s*22px;[^}]*height:\s*22px;/s);
  });

  it("P4.1 & P4.2: Toàn bộ 11 mẫu hình học trong publicCatalog() render hình minh họa SVG đầy đủ chi tiết", () => {
    const catalog = publicCatalog();
    expect(catalog).toHaveLength(11);

    for (const entry of catalog) {
      const svgHtml = renderToString(<SamplePreview sampleId={entry.id} />);
      expect(svgHtml, `mẫu ${entry.id} thiếu viewBox chuẩn`).toContain('viewBox="0 0 180 110"');
      expect(svgHtml, `mẫu ${entry.id} thiếu điểm đánh dấu <circle`).toContain("<circle");
      expect(svgHtml, `mẫu ${entry.id} thiếu nhãn đỉnh <text`).toContain("<text");
    }
  });

  it("P4.3: Mục 'Tiếp tục học' ẩn khi chưa có lịch sử và hiển thị đầy đủ khi có lịch sử", () => {
    const emptyHomeHtml = renderToString(<HomeView />);
    expect(emptyHomeHtml).not.toContain('id="home-resume-section"');
    expect(emptyHomeHtml).not.toContain("Tiếp tục học");

    const sample = publicCatalog()[0];
    historyStore.record(sample.envelope, "Đề bài thử nghiệm");
    historyStore.touch(historyStore.list()[0].id, { lastCursor: 2 });
    useAppStore.setState({ history: historyStore.list() });
    syncStoreForSSR();

    const populatedHomeHtml = renderToString(<HomeView />);
    expect(populatedHomeHtml).toContain('id="home-resume-section"');
    expect(populatedHomeHtml).toContain("Tiếp tục học");
    expect(populatedHomeHtml).toContain('id="btn-home-to-history"');
    expect(populatedHomeHtml).toContain("Xem lịch sử →");
    expect(populatedHomeHtml).toContain('class="resume-home-card"');
    expect(populatedHomeHtml).toContain(sample.title);
    expect(populatedHomeHtml).toContain("Hình chóp");
    expect(populatedHomeHtml).toContain("Đang học: <strong>Bước 3/");
    expect(populatedHomeHtml).toContain('class="progress-fill"');
    expect(populatedHomeHtml).toContain('id="btn-home-resume-latest"');
    expect(populatedHomeHtml).toContain("Tiếp tục →");
  });

  it("P4.3 & P6.4: sanitizeEnvelope bảo toàn scene3d để mở lại bài từ Tiếp tục học / Lịch sử vào đúng Scene3D", () => {
    const sample = publicCatalog()[0];
    const sampleEnv = sample.envelope as { scene3d?: unknown };
    expect(sampleEnv.scene3d).toBeDefined();

    const recorded = historyStore.record(sample.envelope, null);
    const recordedEnv = recorded.envelope as { scene3d?: unknown };
    expect(recordedEnv.scene3d).toBeDefined();

    useAppStore.getState().loadEnvelope(recorded.envelope, sample.id, recorded.originalInput ?? undefined);
    const state = useAppStore.getState();
    expect(state.view).toBe("workspace");
    const activeEnv = state.active?.envelope as { scene3d?: unknown } | undefined;
    expect(activeEnv?.scene3d).toBeDefined();
  });

  it("P5: Trang Thư viện (#view-library) hiển thị đúng 11 bài mẫu, bộ đếm, ô tìm kiếm, lọc theo từ khóa và menu danh mục", () => {
    const libHtml = renderToString(<LibraryView />);
    expect(libHtml).toContain('id="view-library"');
    expect(libHtml).toContain("Thư viện mô phỏng");
    expect(libHtml).toContain('id="library-count-readout"');
    expect(libHtml).toContain("Hiển thị 11 / 11 bài mô phỏng");
    expect(libHtml).toContain('id="library-search-input"');
    expect(libHtml).toContain('id="btn-library-category-dropdown"');
    expect(libHtml).toContain('id="library-category-menu"');
    expect(libHtml).toContain("Tất cả");
    expect(libHtml).toContain("Hình chóp");
    expect(libHtml).toContain("Mặt cầu");
    expect(libHtml).toContain("Hình trụ");
    expect(libHtml).toContain("Hình nón");
    expect((libHtml.match(/class="lib-card"/g) ?? []).length).toBe(11);
    expect(libHtml).toContain("bước dựng 3D");
    expect(libHtml).toContain("Mở mô phỏng →");

    // Kiểm tra lọc theo danh mục Hình chóp (5 bài)
    const filteredCatHtml = renderToString(<LibraryView initialCategory="Hình chóp" />);
    expect(filteredCatHtml).toContain("Hiển thị 5 / 11 bài mô phỏng");
    expect((filteredCatHtml.match(/class="lib-card"/g) ?? []).length).toBe(5);

    // Kiểm tra tìm kiếm từ khóa "mặt cầu"
    const searchedHtml = renderToString(<LibraryView initialSearch="mặt cầu" />);
    expect(searchedHtml).toContain("Hiển thị 2 / 11 bài mô phỏng");

    // Kiểm tra trạng thái trống khi từ khóa không khớp
    const emptySearchHtml = renderToString(<LibraryView initialSearch="xyz-khong-ton-tai" />);
    expect(emptySearchHtml).toContain("Hiển thị 0 / 11 bài mô phỏng");
    expect(emptySearchHtml).toContain("Không tìm thấy bài mô phỏng nào khớp từ khóa");
  });

  it("P6: Trang Lịch sử (#view-history) hiển thị trạng thái trống, danh sách thẻ lịch sử và modal xác nhận xóa", () => {
    const emptyHistoryHtml = renderToString(<HistoryView />);
    expect(emptyHistoryHtml).toContain('id="view-history"');
    expect(emptyHistoryHtml).toContain("Lịch sử học");
    expect(emptyHistoryHtml).toContain("Chưa có bài hình học nào trong lịch sử học tập.");
    expect(emptyHistoryHtml).toContain('id="btn-history-clear-init"');
    expect(emptyHistoryHtml).toContain('disabled=""');
    expect(emptyHistoryHtml).toContain('id="history-clear-modal"');
    expect(emptyHistoryHtml).toContain("Xóa toàn bộ lịch sử học?");

    const catalog = publicCatalog();
    historyStore.record(catalog[0].envelope, null);
    historyStore.record(catalog[5].envelope, null);
    useAppStore.setState({ history: historyStore.list() });
    syncStoreForSSR();

    const populatedHistoryHtml = renderToString(<HistoryView initialClearModalOpen={true} />);
    expect((populatedHistoryHtml.match(/class="history-card"/g) ?? []).length).toBe(2);
    expect(populatedHistoryHtml).toContain(catalog[0].title);
    expect(populatedHistoryHtml).toContain(catalog[5].title);
    expect(populatedHistoryHtml).toContain("Tiếp tục →");
    expect(populatedHistoryHtml).toContain('class="btn-history-item-remove"');
    expect(populatedHistoryHtml).toContain('class="axo-modal-backdrop open" id="history-clear-modal"');
  });

  it("Phase C · P2: Nút xóa một mục (×) nằm ở góc trên bên phải bên trong .history-card, tách rời nút Tiếp tục → và có modal xác nhận riêng", () => {
    const sample = publicCatalog()[0];
    const recorded = historyStore.record(sample.envelope, null);
    useAppStore.setState({ history: historyStore.list() });
    syncStoreForSSR();

    const html = renderToString(<HistoryView />);
    expect(html).toContain('title="Xóa khỏi lịch sử"');
    expect(html).toContain(`aria-label="Xóa ${sample.title} khỏi lịch sử"`);
    // Nút xóa nằm trước khối nội dung trái, không còn nằm trong .history-card-actions cạnh nút Tiếp tục
    const removeIdx = html.indexOf('class="btn-history-item-remove"');
    const actionsIdx = html.indexOf('class="history-card-actions"');
    expect(removeIdx).toBeGreaterThan(-1);
    expect(actionsIdx).toBeGreaterThan(removeIdx);

    // Modal xác nhận xóa một mục (#history-delete-item-modal) hiển thị đúng tên bài sắp xóa
    const modalHtml = renderToString(
      <HistoryView initialDeleteItemId={recorded.id} />,
    );
    expect(modalHtml).toContain('class="axo-modal-backdrop open" id="history-delete-item-modal"');
    expect(modalHtml).toContain("Xóa khỏi lịch sử học tập?");
    expect(modalHtml).toContain('class="history-delete-target-title"');
    expect(modalHtml).toContain(sample.title);
    expect(modalHtml).toContain('id="btn-cancel-delete-item"');
    expect(modalHtml).toContain('id="btn-confirm-delete-item"');

    // Khi xóa thất bại, hiện thông báo lỗi (#history-delete-error-banner) và giữ nguyên bản ghi
    const errHtml = renderToString(
      <HistoryView initialDeleteError="Không thể xóa mục lịch sử lúc này." />,
    );
    expect(errHtml).toContain('id="history-delete-error-banner"');
    expect(errHtml).toContain('role="alert"');
    expect(errHtml).toContain("Không thể xóa mục lịch sử lúc này.");
    expect(historyStore.list()).toHaveLength(1);
  });

  it("Phase C · P3/P4/P5: Workspace V6.2 (AxoWorkspaceV62) dựng đầy đủ Header, Stage 3D thật, Playback P-A, Floating Toolbar 3D và Unified Study Dock", () => {
    const sample = publicCatalog()[0];
    const scene = (sample.envelope as { scene3d?: Scene3D }).scene3d!;
    expect(scene).toBeDefined();

    useAppStore.getState().loadEnvelope(sample.envelope, sample.id, sample.envelope.description ?? undefined);
    syncStoreForSSR();
    const wsHtml = renderToString(<SimulationWorkspace />);

    // 1. Workspace Header V2.7
    expect(wsHtml).toContain('class="axo-workspace-v62 axo-frame is-page-workspace"');
    expect(wsHtml).toContain('class="axo-header ws-axo-header"');
    expect(wsHtml).toContain('id="btn-brand-home"');
    expect(wsHtml).toContain('id="header-prob-div"');
    expect(wsHtml).toContain('id="top-prob-title"');
    expect(wsHtml).toContain(sample.title);
    expect(wsHtml).toContain('id="nav-home"');
    expect(wsHtml).toContain('id="nav-library"');
    expect(wsHtml).toContain('id="nav-history"');
    expect(wsHtml).toContain('id="btn-header-change-prob"');
    expect(wsHtml).toContain("Đổi đề toán");

    // 2. 3D Stage & Real Scene3DWorkspace
    expect(wsHtml).toContain('id="ws-body"');
    expect(wsHtml).toContain('id="stage-3d-box"');
    expect(wsHtml).toContain('id="stage-spatial-grid"');
    expect(wsHtml).toContain('class="ws-scene3d-host"');
    expect(wsHtml).toContain('id="btn-reopen-dock-capsule"');

    // 3. Playback P-A Capsule
    expect(wsHtml).toContain('id="playback-pa-box"');
    expect(wsHtml).toContain('id="playback-pa-capsule"');
    expect(wsHtml).toContain('id="pa-prev"');
    expect(wsHtml).toContain('id="pa-play"');
    expect(wsHtml).toContain('id="pa-next"');
    expect(wsHtml).toContain('id="pa-counter"');
    expect(wsHtml).toContain('id="pa-short-title"');
    expect(wsHtml).toContain('id="pa-pips-mount"');
    expect(wsHtml).toContain('id="pa-mode-toggle"');

    // 4. Floating Draggable 3D Toolbar & Display Popover (7 lớp chuẩn HTML V2.7, loại bỏ Explode)
    expect(wsHtml).toContain('id="floating-toolbar-3d"');
    expect(wsHtml).toContain('id="tb-display-pop"');
    expect(wsHtml).toContain('id="chk-shell"');
    expect(wsHtml).toContain('id="chk-labels"');
    expect(wsHtml).toContain('id="chk-plane"');
    expect(wsHtml).toContain('id="chk-section"');
    expect(wsHtml).toContain('id="chk-aux"');
    expect(wsHtml).toContain('id="chk-axes"');
    expect(wsHtml).toContain('id="chk-grid"');
    expect(wsHtml).not.toContain('id="chk-lengths"');
    expect(wsHtml).not.toContain('id="chk-angles"');
    expect(wsHtml).not.toContain('id="chk-dashed"');
    expect(wsHtml).not.toContain('id="btn-explode"');
    expect(wsHtml).not.toContain('id="p-dot-explode"');
    expect(wsHtml).toContain('id="btn-reset-display-opts"');
    expect(wsHtml).toContain('id="toolbar-3d-collapsed"');
    expect(wsHtml).toContain('id="btn-tb-expand"');
    expect(wsHtml).toContain('id="tb-preserved-dots"');
    expect(wsHtml).toContain('id="toolbar-3d-expanded"');
    expect(wsHtml).toContain('id="tb-drag-grip"');
    expect(wsHtml).toContain('id="btn-xray"');
    expect(wsHtml).toContain('id="btn-reset-pos"');
    expect(wsHtml).toContain('id="btn-display-pop"');
    expect(wsHtml).toContain('id="btn-tb-collapse"');

    // 5. Unified Study Dock (#ws-dock) — Phase C.1 P6.6: không còn nút trùng lặp #btn-toggle-prob-sec
    expect(wsHtml).toContain('id="ws-dock"');
    expect(wsHtml).not.toContain('id="btn-toggle-prob-sec"');
    expect(wsHtml).toContain('id="btn-collapse-dock"');
    expect(wsHtml).toContain('id="dock-prob-statement"');
    expect(wsHtml).toContain('id="dock-context-object-mount"');
    expect(wsHtml).toContain('id="dock-steps-counter"');
    expect(wsHtml).toContain('id="dock-steps-ul"');
    expect(wsHtml).toContain('id="dock-entities-pills"');

    // 6. Contextual Selected Object Card khi chọn một đối tượng thực tế của Scene3D
    const firstObjId = scene.objects[0]?.id ?? null;
    const selectedHtml = renderToString(
      <AxoWorkspaceV62
        scene={scene}
        de={sample.envelope.description}
        tieuDe={sample.title}
        initialSelectedId={firstObjId}
        initialDisplayPopOpen={true}
        initialPaExpanded={true}
      />,
    );
    expect(selectedHtml).toContain('class="context-object-card"');
    expect(selectedHtml).toContain('id="btn-clear-pick"');
    expect(selectedHtml).toContain("Chỉ xem phần này");
    expect(selectedHtml).toContain("Ẩn đối tượng");
    expect(selectedHtml).toContain('class="tb-display-popover tb-popover is-open"');
    expect(selectedHtml).toContain('tb-pop-header tb-pop-head');
    expect(selectedHtml).toContain('tb-pop-label tb-pop-row-text');
    expect(selectedHtml).toContain('class="playback-pa-capsule is-expanded mode-expanded"');
  });

  it("Phase C.3 · P5: Gom Logo Mark và Wordmark Axo thành nút #btn-brand-home duy nhất, tách rời hoàn toàn #top-prob-title trên cả Homepage và Workspace", () => {
    const homeHtml = renderToString(<App />);
    // Trên Homepage: #btn-brand-home bọc cả SVG logo mark 22x22 và chữ Axo theo chuẩn HTML V2.7
    expect(homeHtml).toMatch(
      /<button[^>]*id="btn-brand-home"[^>]*>\s*<svg[^>]*class="axo-logo-svg"[^>]*>.*?<\/svg>\s*<span class="nav-wordmark-text">Axo<\/span>\s*<\/button>/s,
    );

    const sample = publicCatalog()[0];
    useAppStore.getState().loadEnvelope(sample.envelope, sample.id, sample.envelope.description ?? undefined);
    syncStoreForSSR();
    const wsHtml = renderToString(<SimulationWorkspace />);

    // Trên Workspace: #btn-brand-home bọc cả SVG logo mark 22x22 và chữ Axo, còn #header-prob-div và #top-prob-title nằm ngoài button
    expect(wsHtml).toMatch(
      /<button[^>]*id="btn-brand-home"[^>]*>\s*<svg[^>]*class="axo-logo-svg"[^>]*>.*?<\/svg>\s*<span class="axo-brand-name nav-wordmark-text">Axo<\/span>\s*<\/button>\s*<div class="header-div" id="header-prob-div"/s,
    );
    expect(wsHtml).toContain('id="top-prob-title"');
    expect(wsHtml).not.toMatch(/<button[^>]*id="btn-brand-home"[^>]*>(?:(?!<\/button>).)*id="top-prob-title"/s);
  });

  it("Phase C.2 · P2, P3, P4, P5: Workspace V6.2 khôi phục nút & panel 'Tùy chỉnh hình' (#tb-geo-custom-pop), đủ 7 lớp hiển thị HTML V2.7 và sửa gutter mép phải", () => {
    const catalog = publicCatalog();
    const pyramidSample = catalog[0];
    const pyramidScene = (pyramidSample.envelope as unknown as { scene3d: Scene3D }).scene3d;

    const wsOpenGeoHtml = renderToString(
      <AxoWorkspaceV62
        scene={pyramidScene}
        de={pyramidSample.envelope.description}
        tieuDe={pyramidSample.title}
        initialGeoCustomOpen={true}
        initialDisplayPopOpen={true}
      />,
    );

    // P3: Nút #btn-geo-custom-pop và panel #tb-geo-custom-pop
    expect(wsOpenGeoHtml).toContain('id="btn-geo-custom-pop"');
    expect(wsOpenGeoHtml).toContain('id="tb-geo-custom-pop"');
    expect(wsOpenGeoHtml).toContain('id="geo-custom-pop-header"');
    expect(wsOpenGeoHtml).toContain('id="geo-custom-scene-chip"');
    expect(wsOpenGeoHtml).toContain(">Hình chóp<");
    expect(wsOpenGeoHtml).toContain('id="btn-reset-geo-custom"');
    expect(wsOpenGeoHtml).toContain('id="btn-close-geo-custom"');
    expect(wsOpenGeoHtml).toContain('id="slider-shell-opacity"');
    expect(wsOpenGeoHtml).toContain('id="slider-plane-opacity"');
    expect(wsOpenGeoHtml).toContain('id="p-dot-geo-custom"');

    // Kiểm tra scene Mặt cầu nhận diện đúng chip "Mặt cầu"
    const sphereSample = catalog.find((s) => s.id.includes("sphere") || s.title.toLowerCase().includes("cầu"));
    if (sphereSample) {
      const sphereScene = (sphereSample.envelope as unknown as { scene3d: Scene3D }).scene3d;
      const sphereHtml = renderToString(
        <AxoWorkspaceV62
          scene={sphereScene}
          de={sphereSample.envelope.description}
          tieuDe={sphereSample.title}
          initialGeoCustomOpen={true}
        />,
      );
      expect(sphereHtml).toContain(">Mặt cầu<");
      expect(sphereHtml).toContain('id="slider-sphere-radius"');
      expect(sphereHtml).toContain('id="slider-plane-height"');
    }

    // P4: Đủ 7 lớp chuẩn của HTML V2.7 + nút Khôi phục hiển thị
    expect(wsOpenGeoHtml).toContain('id="chk-shell"');
    expect(wsOpenGeoHtml).toContain('id="chk-labels"');
    expect(wsOpenGeoHtml).toContain('id="chk-plane"');
    expect(wsOpenGeoHtml).toContain('id="chk-section"');
    expect(wsOpenGeoHtml).toContain('id="chk-aux"');
    expect(wsOpenGeoHtml).toContain('id="chk-axes"');
    expect(wsOpenGeoHtml).toContain('id="chk-grid"');
    expect(wsOpenGeoHtml).toContain('id="btn-reset-display-opts"');
    expect(wsOpenGeoHtml).toContain('id="btn-reset-display-layers"');

    // P2 & P5: Kiểm tra luật CSS sửa scrollbar-gutter mép phải và Study Dock .dock-section trong suốt
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toMatch(/html:has\(\.axo-workspace-v62\)[^{]*\{[^}]*scrollbar-gutter:\s*auto;[^}]*overflow:\s*hidden;/s);
    expect(css).toMatch(/\.dock-section\s*\{[^}]*background:\s*transparent;[^}]*border:\s*none;/s);
  });

  it("Phase C.1 · P5: Phục hồi scene3d từ catalog khi bản ghi lịch sử thiếu scene3d và tuyệt đối không mở trình mô phỏng ngữ nghĩa cũ", () => {
    const sample = publicCatalog()[0];
    const strippedEnv = { ...sample.envelope } as Record<string, unknown>;
    delete strippedEnv.scene3d;

    useAppStore.getState().loadEnvelope(strippedEnv as unknown as typeof sample.envelope, sample.id, sample.envelope.description ?? undefined);
    syncStoreForSSR();
    const recoveredHtml = renderToString(<SimulationWorkspace />);
    expect(recoveredHtml).toContain('class="axo-workspace-v62 axo-frame is-page-workspace"');
    expect(recoveredHtml).toContain('id="stage-3d-box"');
    expect(recoveredHtml).not.toContain("MÔ PHỎNG THEO MÔ TẢ");

    // Khi một bản ghi hình học tùy chỉnh hoàn toàn không có scene3d và không khớp mẫu catalog,
    // hiển thị trạng thái trung thực trong khung Axo V2.7, tuyệt đối không mở giao diện cũ
    const customEnv = {
      ...sample.envelope,
      title: "Bài toán hình học chưa có dữ liệu 3D",
      config: { ...(sample.envelope.config as Record<string, unknown>), __unmatched_test: true },
    } as Record<string, unknown>;
    delete customEnv.scene3d;

    useAppStore.getState().loadEnvelope(customEnv as unknown as typeof sample.envelope, "custom-1", "Đề bài tùy chỉnh");
    syncStoreForSSR();
    const unavailableHtml = renderToString(<SimulationWorkspace />);
    expect(unavailableHtml).toContain('class="axo-workspace-v62 axo-frame is-page-workspace"');
    expect(unavailableHtml).toContain('id="ws-scene3d-unavailable-card"');
    expect(unavailableHtml).not.toContain("MÔ PHỎNG THEO MÔ TẢ");
  });

  it("Phase C.3 · P0–P4: Phục hồi hiển thị Scene3D (Trụ, Nón, Mặt cầu, Thiết diện bước cuối) và đồng bộ icon Thanh công cụ / Playback HTML V2.7", () => {
    const catalog = publicCatalog();

    // 1. Hình chóp (thiet-dien-chop) ở bước cuối cùng (Bước 11/11) phải giữ cả mặt phẳng cắt (MNP) lẫn thiết diện
    const pyramidSample = catalog.find((s) => s.id === "thiet-dien-chop") ?? catalog[0];
    const pyramidScene = withSubEntities(
      veKhongGian((pyramidSample.envelope as unknown as { scene3d: Scene3D }).scene3d),
    );
    const maxStepIdx = Math.max(0, geometryStepCount(pyramidScene) - 1);
    const maxAnchor = anchorOfGeometryStep(pyramidScene, maxStepIdx);
    const finalWsHtml = renderToString(
      <AxoWorkspaceV62
        scene={pyramidScene}
        de={pyramidSample.envelope.description}
        tieuDe={pyramidSample.title}
        initialStep={maxAnchor}
      />,
    );
    expect(finalWsHtml).toContain('data-entity-chip="mp"');
    expect(finalWsHtml).toContain(">(MNP)<");
    expect(finalWsHtml).toContain('data-entity-chip="thiet_dien"');

    // 2. Mặt cầu cắt bởi mặt phẳng (cau-cat-mat-phang) theo matphang.html: giữ vỏ cầu 3D bán trong suốt + xích đạo tham chiếu (sphere_reference) + giao tuyến (circle3), KHÔNG vẽ đường viền bao đen giả (sphere_silhouette)
    const sphereCutSample = catalog.find((s) => s.id === "cau-cat-mat-phang");
    expect(sphereCutSample).toBeDefined();
    if (sphereCutSample) {
      const sphereCutScene = withSubEntities(
        veKhongGian((sphereCutSample.envelope as unknown as { scene3d: Scene3D }).scene3d),
      );
      const ballObj = sphereCutScene.objects.find((o) => o.curved_kind === "ball");
      const circleObj = sphereCutScene.objects.find((o) => o.render === "circle");
      expect(ballObj).toBeDefined();
      expect(circleObj).toBeDefined();
      const builtBall = ballObj ? buildObject3D(ballObj, false) : null;
      const builtCircle = circleObj ? buildObject3D(circleObj, true) : null;
      let hasSilhouette = false;
      let hasSphereShell = false;
      let hasReferenceEquator = false;
      builtBall?.traverse((child) => {
        if (child.name.startsWith("sphere_silhouette:")) hasSilhouette = true;
        if ((child as { isMesh?: boolean }).isMesh && child.userData?.voKhoi) hasSphereShell = true;
        if (child.name.startsWith("sphere_reference:")) hasReferenceEquator = true;
      });
      expect(hasSilhouette).toBe(false);
      expect(hasSphereShell).toBe(true);
      expect(hasReferenceEquator).toBe(true);
      expect(builtCircle?.name.startsWith("circle:")).toBe(true);
    }

    // 3. Kiểm tra Playback P-A và Floating Toolbar SVG icons chuẩn HTML V2.7
    expect(finalWsHtml).toContain('class="stage-spatial-grid" id="stage-spatial-grid"');
    expect(finalWsHtml).toContain('class="pa-pips is-dense" id="pa-pips-mount"');
    expect(finalWsHtml).toContain('d="m15 18-6-6 6-6"');
    expect(finalWsHtml).toContain('d="m9 18 6-6-6-6"');
    expect(finalWsHtml).toContain('points="15 3 21 3 21 9"');
    expect(finalWsHtml).toContain('d="M12 3v18"');
    expect(finalWsHtml).not.toContain('id="btn-explode"');
  });

  it("Phase C.4 · P1–P3: Chuẩn hoá Playback Play/Pause, nút mở lại Study Dock (‹ Học tập) và các nút điều khiển theo HTML V2.7", () => {
    const catalog = publicCatalog();
    const sample = catalog.find((s) => s.id === "thiet-dien-chop") ?? catalog[0];
    const scene = withSubEntities(
      veKhongGian((sample.envelope as unknown as { scene3d: Scene3D }).scene3d),
    );
    const wsHtml = renderToString(
      <AxoWorkspaceV62
        scene={scene}
        de={sample.envelope.description}
        tieuDe={sample.title}
        initialStep={anchorOfGeometryStep(scene, 1)}
      />,
    );

    // P1: Playback Play button có class chuẩn `pa-btn play-btn pa-btn-play` và `#pa-play-icon` polygon chuẩn HTML V2.7
    expect(wsHtml).toContain('class="pa-btn play-btn pa-btn-play" id="pa-play"');
    expect(wsHtml).toContain('id="pa-play-icon"');
    expect(wsHtml).toContain('points="6 4 20 12 6 20 6 4"');

    // P2: Nút mở lại Study Dock dùng đúng `svg.reopen-chevron` + open book SVG + `#dock-trigger-badge`
    expect(wsHtml).toContain('id="btn-reopen-dock-capsule"');
    expect(wsHtml).toContain('class="reopen-chevron"');
    expect(wsHtml).toContain('d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"');
    expect(wsHtml).toContain('d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"');
    expect(wsHtml).toContain('class="dock-trigger-badge" id="dock-trigger-badge">1/10<');
    expect(wsHtml).not.toContain('class="dock-reopen-chevron"');

    // P3: Nút thu gọn Study Dock, thu gọn Floating Toolbar, và header Tùy chỉnh hình khớp HTML V2.7
    expect(wsHtml).toContain('class="dock-collapse-pill-btn" id="btn-collapse-dock"');
    expect(wsHtml).toContain('class="tb-collapse-btn" id="btn-tb-collapse"');
    expect(wsHtml).toContain('class="geo-custom-scene-chip" id="geo-custom-scene-chip"');
  });

  it("Phase D · P0–P6: Bảng Tùy chỉnh hình đặt trực tiếp trong #stage-3d-box, đầy đủ giao diện Xác thực, Tài khoản và Quản trị chuẩn HTML V2.7", () => {
    const catalog = publicCatalog();
    const sample = catalog.find((s) => s.id === "thiet-dien-chop") ?? catalog[0];
    const scene = withSubEntities(
      veKhongGian((sample.envelope as unknown as { scene3d: Scene3D }).scene3d),
    );
    const wsHtml = renderToString(
      <AxoWorkspaceV62
        scene={scene}
        de={sample.envelope.description}
        tieuDe={sample.title}
        initialStep={anchorOfGeometryStep(scene, 1)}
      />,
    );

    // P0: #tb-geo-custom-pop nằm trực tiếp trong #stage-3d-box (sau đóng #floating-toolbar-3d) để kéo tự do toàn stage
    const idxTbEnd = wsHtml.indexOf('id="tb-display-pop"');
    const idxGeoCustom = wsHtml.indexOf('id="tb-geo-custom-pop"');
    expect(idxTbEnd).toBeGreaterThan(-1);
    expect(idxGeoCustom).toBeGreaterThan(idxTbEnd);
    expect(wsHtml).toContain('id="geo-custom-pop-header"');

    // P1: Standalone Auth Views (#view-login, #view-register, #view-forgot, #view-reset)
    const loginHtml = renderToString(<AuthPageView mode="login" />);
    expect(loginHtml).toContain('id="view-login"');
    expect(loginHtml).toContain('data-auth-home="1"');
    expect(loginHtml).toContain('id="login-email-input"');
    expect(loginHtml).toContain('id="login-pw-input"');
    expect(loginHtml).toContain('id="btn-login-to-forgot"');
    expect(loginHtml).toContain('id="btn-login-to-register"');

    const regHtml = renderToString(<AuthPageView mode="register" />);
    expect(regHtml).toContain('id="view-register"');
    expect(regHtml).toContain('id="reg-name-input"');
    expect(regHtml).toContain('id="reg-email-input"');
    expect(regHtml).toContain('id="reg-pw-input"');
    expect(regHtml).toContain('id="reg-pw-confirm-input"');

    const forgotHtml = renderToString(<AuthPageView mode="forgot" />);
    expect(forgotHtml).toContain('id="view-forgot"');
    expect(forgotHtml).toContain('id="forgot-email-input"');
    expect(forgotHtml).toContain('id="btn-forgot-to-login"');

    const resetHtml = renderToString(<AuthPageView mode="reset" />);
    expect(resetHtml).toContain('id="view-reset"');
    expect(resetHtml).toContain('id="reset-pw-input"');
    expect(resetHtml).toContain('id="reset-pw-confirm-input"');

    // P1: Account Settings Modal (#user-account-settings-modal)
    useAuthStore.setState({
      user: {
        id: 1,
        email: "minhkhoa.11a1@thpt-chu-van-an.edu.vn",
        displayName: "Nguyễn Minh Khoa",
        role: "student",
        mustChangePassword: false,
      },
    });
    Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
    useAppStore.getState().openAccountModal("profile");
    syncStoreForSSR();

    const accModalHtml = renderToString(<AccountSettingsModal />);
    expect(accModalHtml).toContain('id="user-account-settings-modal"');
    expect(accModalHtml).toContain('id="tab-btn-acc-profile"');
    expect(accModalHtml).toContain('id="tab-btn-acc-security"');
    expect(accModalHtml).toContain('id="acc-modal-sec-profile"');
    expect(accModalHtml).toContain('id="acc-modal-sec-security"');
    expect(accModalHtml).toContain('class="axo-custom-select"');

    // P1: Admin Workspace (#view-admin) cho tài khoản admin
    useAuthStore.setState({
      user: {
        id: 99,
        email: "admin@axo.edu.vn",
        displayName: "Trần Quản Trị",
        role: "admin",
        mustChangePassword: false,
      },
    });
    Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());

    const adminHtml = renderToString(<AdminWorkspaceView />);
    expect(adminHtml).toContain('id="view-admin"');
    expect(adminHtml).toContain('id="admin-shell"');
    expect(adminHtml).toContain('id="admin-sidebar"');
    expect(adminHtml).toContain('data-admin-tab="overview"');
    expect(adminHtml).toContain('data-admin-tab="accounts"');
    expect(adminHtml).toContain('data-admin-tab="analytics"');
    expect(adminHtml).toContain('data-admin-tab="audit"');
    expect(adminHtml).toContain('id="admin-system-settings-modal"');
    expect(adminHtml).toContain('id="admin-create-user-modal"');
    expect(adminHtml).toContain('id="admin-bulk-import-modal"');
    expect(adminHtml).toContain('id="inp-bulk-file-upload"');
    expect(adminHtml).toContain('id="bulk-dropzone"');
    expect(adminHtml).toContain('id="btn-bulk-step1-download-template"');
    expect(adminHtml).toContain("3 cột bắt buộc");
    // Phase C.4 P0: Loại bỏ hoàn toàn 3 nút dữ liệu demo/test khỏi sản phẩm
    expect(adminHtml).not.toContain('id="btn-bulk-preset-sample3"');
    expect(adminHtml).not.toContain('id="btn-bulk-preset-100rows"');
    expect(adminHtml).not.toContain('id="btn-bulk-preset-mixed8"');
    expect(adminHtml).not.toContain("Tệp mẫu chuẩn (3 dòng)");
    expect(adminHtml).not.toContain("Danh sách trường (100 dòng)");
    expect(adminHtml).not.toContain("Tệp kiểm thử đủ 6 nhóm (8 dòng)");

    // Phase C.3 & Stage B Unified Sizing CSS contracts (Import Wizard 4-step bar, Header 3-col grid & --axo-header-h token, Homepage --axo-home-max-w & --axo-hero-title-size tokens, Composer 76px 3-line baseline, Playback P-A Compact vs Expanded)
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toMatch(/\.nav-bar\s*\{[^}]*display:\s*grid;[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+auto\s+minmax\(0,\s*1fr\);/s);
    expect(css).toContain("--axo-header-h: 46px;");
    expect(css).toContain("--axo-home-max-w: 820px;");
    expect(css).toContain("--axo-hero-title-size: 30px;");
    expect(css).toMatch(/\.composer-textarea\s*\{[^}]*min-height:\s*76px;[^}]*height:\s*76px;[^}]*max-height:\s*220px;/s);
    expect(css).toMatch(/\.bulk-stepper\s*\{[^}]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\);/s);
    expect(css).toMatch(/\.bulk-step-pill\s*\{[^}]*white-space:\s*nowrap;/s);
    expect(css).toMatch(/\.bulk-cat-grid\s*\{[^}]*grid-template-columns:\s*repeat\(3,\s*minmax\(0,\s*1fr\)\);/s);
    expect(css).toMatch(/\.playback-pa-capsule\.mode-compact:not\(\.is-expanded\)\s+\.pa-pips\s*\{[^}]*display:\s*none;/s);
    expect(css).toMatch(/\.pa-pips\.is-dense\s*\{[^}]*max-width:\s*120px;/s);

    useAuthStore.setState({ user: null });
    Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
    useAppStore.getState().closeAccountModal();
    syncStoreForSSR();
  });

  it("Finalization & Integration: moTaBuocDungHienThi diễn giải nhãn ký hiệu trần từ metadata SceneObject, reopenFromHistory bảo toàn bước dựng 3D và HomeView hiển thị từ chối kiểm chứng", () => {
    const catalog = publicCatalog();
    const sphereSample = catalog.find((e) => e.id === "cau-cat-mat-phang");
    const sectionSample = catalog.find((e) => e.id === "thiet-dien-chop");
    expect(sphereSample).toBeDefined();
    expect(sectionSample).toBeDefined();

    const sphereScene = withSubEntities(
      veKhongGian((sphereSample!.envelope as unknown as { scene3d: Scene3D }).scene3d),
    );
    const sphereSteps = geometryStepList(sphereScene);
    const sphereStepS = moTaBuocDungHienThi(sphereScene, sphereSteps[1]);
    const sphereStepP = moTaBuocDungHienThi(sphereScene, sphereSteps[2]);
    expect(sphereStepS.title).toBe("Khối cầu tâm I · (S)");
    expect(sphereStepP.title).toBe("Mặt phẳng cho bằng phương trình · (P)");

    const sectionScene = withSubEntities(
      veKhongGian((sectionSample!.envelope as unknown as { scene3d: Scene3D }).scene3d),
    );
    const sectionSteps = geometryStepList(sectionScene);
    const stepM = sectionSteps.find((s) => s.label === "M")!;
    const stepPlane = sectionSteps.find((s) => s.label === "(MNP)")!;
    const sectionStepM = moTaBuocDungHienThi(sectionScene, stepM);
    const sectionStepPlane = moTaBuocDungHienThi(sectionScene, stepPlane);
    expect(sectionStepM.title).toBe("Trung điểm của S và A · M");
    expect(sectionStepPlane.title).toBe("Mặt phẳng qua M, N, P · (MNP)");

    // Kiểm chứng reopenFromHistory không bị kẹp lastCursor 3D bởi timeline 2D
    useAppStore.getState().loadEnvelope(
      sectionSample!.envelope,
      sectionSample!.id,
      sectionSample!.envelope.description ?? undefined,
    );
    const saved = historyStore.list()[0];
    expect(saved).toBeDefined();
    historyStore.touch(saved.id, { lastCursor: 8 });
    expect(historyStore.list()[0].lastCursor).toBe(8);

    useAppStore.getState().goHome();
    useAppStore.getState().reopenFromHistory(saved.id);
    expect(historyStore.list()[0].lastCursor).toBe(8);
    expect(useAppStore.getState().activeSampleId).toBe(sectionSample!.id);

    // Kiểm chứng loadUnsupported không render thẻ lớn #home-composer-refusal dưới ô nhập (đã chuyển sang Toast) và HomeView không mount dải lớp học cũ
    useAppStore.getState().loadUnsupported({
      status: "unsupported",
      reason: "Đề bài không thuộc phạm vi hình học không gian THPT.",
      failure_category: "out_of_scope",
      error_code: "OUT_OF_SCOPE",
    });
    syncStoreForSSR();
    const homeWithRefusal = renderToString(<HomeView />);
    expect(homeWithRefusal).not.toContain('id="home-composer-refusal"');
    expect(homeWithRefusal).not.toContain("home-work-strip");

    useAppStore.getState().clearUnsupported();
    syncStoreForSSR();
    const homeCleared = renderToString(<HomeView />);
    expect(homeCleared).not.toContain('id="home-composer-refusal"');
  });
});
