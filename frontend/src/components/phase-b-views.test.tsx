import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import App from "../App";
import { offlineCatalog, publicCatalog } from "../data/offline-catalog";
import { registerAllSimulations } from "../simulations";
import {
  __resetHistoryForTest,
  INTERRUPTED_BY_RELOAD_REASON,
  historyStore,
  stripStatusPrefixesFromTitle,
} from "../state/history";
import {
  clearLearnerRecoverySnapshot,
  saveLearnerRecoverySnapshot,
} from "../state/learner-recovery-snapshot";
import {
  buildUnifiedProblemList,
  resolveWorkspaceTabGeometryFamily,
  useAppStore,
} from "../state/store";
import {
  GEOMETRY_SOLID_FAMILIES,
  GeometryFamilyIcon,
  resolveGeometrySolidFamily,
} from "./family-icons";
import { HistoryView } from "./HistoryView";
import { HomeView } from "./HomeView";
import { ProblemInput } from "./ProblemInput";
import {
  IconSidebarCollapsedTrigger,
  IconSidebarToggle,
  LeftSidebar,
  foldVietnamese,
  matchesSearchQuery,
} from "./LeftSidebar";
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
import { chonHuongNhin, khungNhinSuPham } from "../simulations/domains/geometry/scene3d-camera";
import { cauTrucSuPham } from "../simulations/domains/geometry/scene3d-semantic-policy";
import { withSubEntities } from "../simulations/domains/geometry/scene3d-subentities";
import { veKhongGian } from "../simulations/domains/geometry/scene3d-chart";
import { canSubmitComposer, validateComposerFile } from "../llm/input";

registerAllSimulations();

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
  Object.assign(useAuthStore.getInitialState(), useAuthStore.getState());
}

describe("Axo V2.7 Phase B — Header Logo, Homepage, Library & History (P3–P8)", () => {
  beforeEach(() => {
    registerAllSimulations();
    __resetHistoryForTest();
    clearLearnerRecoverySnapshot();
    useAppStore.getState().reset();
    useAppStore.setState({ history: [] });
    useAuthStore.setState({ user: null, resolved: false, error: null });
    syncStoreForSSR();
  });

  it("P3 & Phase C.1 P1: Logo Axo (#btn-brand-home) có đúng SVG 26x26 trên Header chính, chữ Axo, padding 0 và không đổi nền/scale khi hover hoặc active", () => {
    const html = renderToString(<App />);
    expect(html).toContain('id="btn-brand-home"');
    expect(html).toContain('class="axo-logo-svg" width="26" height="26"');
    expect(html).toContain('<span class="nav-wordmark-text">Axo</span>');

    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toMatch(/\.axo-logo-btn\s*\{[^}]*gap:\s*7px;[^}]*padding:\s*0;[^}]*border-radius:\s*0;[^}]*font-size:\s*15px;[^}]*background:\s*transparent;/s);
    expect(css).toMatch(/\.axo-logo-btn:hover,\s*\.axo-logo-btn:active\s*\{[^}]*background:\s*transparent;[^}]*transform:\s*none;/s);
    expect(css).toMatch(/\.axo-logo-svg\s*\{[^}]*width:\s*22px;[^}]*height:\s*22px;/s);
    expect(css).toMatch(/\.nav-bar\s+\.axo-logo-svg\s*\{[^}]*width:\s*var\(--axo-logo-size\);[^}]*height:\s*var\(--axo-logo-size\);/s);
  });

  it("P4.1 & P4.2: Toàn bộ 11 mẫu hình học trong publicCatalog() render hình minh họa SVG đầy đủ chi tiết", () => {
    const catalog = publicCatalog(); void catalog;
    expect(catalog).toHaveLength(11);

    for (const entry of catalog) {
      const svgHtml = renderToString(<SamplePreview sampleId={entry.id} />);
      expect(svgHtml, `mẫu ${entry.id} thiếu viewBox chuẩn`).toContain('viewBox="0 0 180 110"');
      expect(svgHtml, `mẫu ${entry.id} thiếu điểm đánh dấu <circle`).toContain("<circle");
      expect(svgHtml, `mẫu ${entry.id} thiếu nhãn đỉnh <text`).toContain("<text");
    }

    const expectedLabelsBySample: Record<string, string[]> = {
      "thiet-dien-chop": ["S", "A", "B", "C", "D", "M", "N", "P", "Q", "(MNP)"],
      "mat-cheo-sac": ["S", "A", "B", "C", "D", "(SAC)"],
      "vuong-goc-chop": ["S", "A", "B", "C", "D", "(SAB)"],
      "mp-vuong-goc-duong": ["S", "A", "B", "C", "D", "H", "(α)"],
      "the-tich-chop": ["S", "A", "B", "C", "D"],
      "cau-cat-mat-phang": ["I", "H", "M", "(P)"],
      "cau-the-tich": ["I", "A"],
      "tru-thiet-dien-tron": ["O", "O′", "M", "(α)"],
      "tru-truc-xien": ["O", "O′", "A"],
      "non-thiet-dien-truc": ["S", "O", "A", "B"],
      "non-duong-sinh": ["S", "O", "A"],
    };
    for (const [sampleId, labels] of Object.entries(expectedLabelsBySample)) {
      const svgHtml = renderToString(<SamplePreview sampleId={sampleId} />);
      for (const lbl of labels) {
        expect(svgHtml, `thumbnail ${sampleId} thiếu nhãn ${lbl}`).toContain(`>${lbl}<`);
      }
    }
    expect(renderToString(<SamplePreview sampleId="the-tich-chop" />)).not.toContain(">H<");
    if (false) {
    }
  });

  it("P4.3: Trang chủ tối giản chỉ hiển thị tiêu đề 'Em muốn dựng hình nào?' + Composer; Left Sidebar chuẩn Notion (3 trạng thái, không có mục Trang chủ, hiển thị trung thực Đang học & Gần đây)", () => {
    const emptyHomeHtml = renderToString(<HomeView />);
    expect(emptyHomeHtml).toContain("Em muốn dựng hình nào?");
    expect(emptyHomeHtml).not.toContain('id="home-starter-grid"');
    expect(emptyHomeHtml).not.toContain('id="home-resume-section"');
    expect(emptyHomeHtml).not.toContain("Gợi ý khám phá");
    expect(emptyHomeHtml).not.toContain("Tiếp tục học");

    useAppStore.getState().setGuestEnteredApp(true);
    useAuthStore.setState({ user: null, resolved: true });
    syncStoreForSSR();
    const emptyAppHtml = renderToString(<App />);
    expect(emptyAppHtml).toContain('id="left-sidebar"');
    expect(emptyAppHtml).toContain('data-sidebar-state="expanded"');
    expect(emptyAppHtml).not.toContain('id="nav-item-home"');
    expect(emptyAppHtml).toContain('id="btn-sidebar-search"');
    expect(emptyAppHtml).not.toContain('id="nav-item-search"');
    expect(emptyAppHtml).toContain('id="nav-item-new-problem"');
    expect(emptyAppHtml).toContain('id="sidebar-group-problems"');
    expect(emptyAppHtml).toContain("Chưa có bài toán nào.");
    expect(emptyAppHtml).not.toContain("Nguyễn Minh Khoa");

    // Trạng thái 2: Ẩn hoàn toàn (Collapsed)
    useAppStore.getState().setLeftRailCollapsed(true);
    syncStoreForSSR();
    const collapsedAppHtml = renderToString(<App />);
    expect(collapsedAppHtml).toContain('data-sidebar-state="collapsed"');
    expect(collapsedAppHtml).toContain('id="btn-sidebar-open-trigger"');
    expect(collapsedAppHtml).toContain("sb-collapsed-trigger-zone is-visible");

    // Trạng thái 3: Xem tạm khi di chuột (Hover Preview)
    useAppStore.getState().setLeftRailHoverPreview(true);
    syncStoreForSSR();
    const previewAppHtml = renderToString(<App />);
    expect(previewAppHtml).toContain('data-sidebar-state="hover-preview"');
    expect(previewAppHtml).toContain("axo-left-sidebar is-collapsed is-hover-preview");

    // Ghim mở cố định trở lại (Expanded)
    useAppStore.getState().setLeftRailCollapsed(false);
    syncStoreForSSR();

    const sample = publicCatalog()[0];
    historyStore.record(sample.envelope, "Đề bài thử nghiệm");
    historyStore.touch(historyStore.list()[0].id, { lastCursor: 2 });
    useAppStore.setState({ history: historyStore.list() });
    syncStoreForSSR();

    const populatedAppHtml = renderToString(<App />);
    expect(populatedAppHtml).toContain('id="sidebar-group-problems"');
    expect(populatedAppHtml).toContain(sample.title);
    expect(populatedAppHtml).toContain('data-processing-status="ready"');
    expect(populatedAppHtml).not.toContain('class="sb-item-sub"');
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

  it("P5: Trang Thư viện (#view-library) hiển thị đúng 11 bài mẫu, bộ đếm riêng gọn gàng, ô tìm kiếm, lọc theo từ khóa và menu danh mục", () => {
    const libHtml = renderToString(<LibraryView />);
    expect(libHtml).toContain('id="view-library"');
    expect(libHtml).toContain("Thư viện mô phỏng");
    expect(libHtml).toContain('id="library-filter-meta-row"');
    expect(libHtml).toContain('id="library-count-readout"');
    expect(libHtml).toContain("11 bài mô phỏng phù hợp");
    expect(libHtml).toContain('id="library-search-input"');
    expect(libHtml).toContain('placeholder="Tìm bài mô phỏng..."');
    expect(libHtml).toContain('id="btn-library-category-dropdown"');
    expect(libHtml).toContain('<strong id="library-category-selected-label">Tất cả</strong>');
    expect(libHtml).not.toContain("Loại hình học:");
    expect(libHtml).not.toContain('id="btn-library-filter-clear"');
    expect(libHtml).toContain('id="library-category-menu"');
    expect(libHtml).toContain("Tất cả");
    expect(libHtml).toContain("Hình chóp");
    expect(libHtml).toContain("Mặt cầu");
    expect(libHtml).toContain("Hình trụ");
    expect(libHtml).toContain("Hình nón");
    expect((libHtml.match(/class="lib-card"/g) ?? []).length).toBe(11);
    expect(libHtml).toContain("bước dựng 3D");
    expect(libHtml).toContain("Mở mô phỏng →");

    // Kiểm tra lọc theo danh mục Hình chóp (5 bài — bài oxyz-giao-diem-duong-mat thuộc danh mục Tọa độ Oxyz, không phải Hình chóp) + nút bỏ lọc nhanh
    const filteredCatHtml = renderToString(<LibraryView initialCategory="Hình chóp" />);
    expect(filteredCatHtml).toContain('<strong id="library-category-selected-label">Hình chóp</strong>');
    expect(filteredCatHtml).toContain("5 bài mô phỏng phù hợp");
    expect(filteredCatHtml).toContain('id="btn-library-filter-clear"');
    expect((filteredCatHtml.match(/class="lib-card"/g) ?? []).length).toBe(5);

    const oxyzCatHtml = renderToString(<LibraryView initialCategory="Tọa độ Oxyz" />);
    expect(oxyzCatHtml).toContain('<strong id="library-category-selected-label">Tọa độ Oxyz</strong>');
    expect(oxyzCatHtml).toContain("1 bài mô phỏng phù hợp");

    // Kiểm tra kết hợp tìm kiếm + lọc nhóm hình
    const combinedHtml = renderToString(
      <LibraryView initialCategory="Hình chóp" initialSearch="thiết diện" />,
    );
    expect(combinedHtml).toContain("1 bài mô phỏng phù hợp");
    expect((combinedHtml.match(/class="lib-card"/g) ?? []).length).toBe(1);

    // Kiểm tra tìm kiếm từ khóa "mặt cầu"
    const searchedHtml = renderToString(<LibraryView initialSearch="mặt cầu" />);
    expect(searchedHtml).toContain("3 bài mô phỏng phù hợp");

    // Kiểm tra trạng thái trống khi từ khóa không khớp
    const emptySearchHtml = renderToString(<LibraryView initialSearch="xyz-khong-ton-tai" />);
    expect(emptySearchHtml).toContain("0 bài mô phỏng phù hợp");
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

    const catalog = publicCatalog(); void catalog;
    historyStore.record(catalog[0].envelope, null);
    historyStore.record(catalog[6].envelope, null);
    useAppStore.setState({ history: historyStore.list() });
    syncStoreForSSR();

    const populatedHistoryHtml = renderToString(<HistoryView initialClearModalOpen={true} />);
    expect((populatedHistoryHtml.match(/class="history-card"/g) ?? []).length).toBe(2);
    expect(populatedHistoryHtml).toContain(catalog[0].title);
    expect(populatedHistoryHtml).toContain(catalog[6].title);
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

    // 1. Workspace Header (Ramp-style Compact Tab Bar: [‹] [›] | [icon + Tên bài toán] [+])
    expect(wsHtml).toContain('class="axo-workspace-v62 axo-frame is-page-workspace"');
    expect(wsHtml).toContain('class="axo-header ws-axo-header"');
    expect(wsHtml).not.toContain('id="btn-brand-home"');
    expect(wsHtml).toContain('id="btn-ws-back"');
    expect(wsHtml).toContain('id="btn-ws-forward"');
    expect(wsHtml).toContain('id="header-prob-div"');
    expect(wsHtml).toContain('class="ws-tabbar-strip"');
    expect(wsHtml).toContain('id="ws-active-problem-tab"');
    expect(wsHtml).toContain('id="top-prob-title"');
    expect(wsHtml).toContain(sample.title);
    expect(wsHtml).not.toContain('class="nav-n1-capsule axo-nav-capsule"');
    expect(wsHtml).not.toContain("Đổi đề toán");
    expect(wsHtml).not.toContain("Bài mới");
    expect(wsHtml).toContain('id="btn-header-change-prob"');

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
    expect(selectedHtml).not.toContain("Chỉ xem phần này");
    expect(selectedHtml).not.toContain("Ẩn đối tượng");
    expect(selectedHtml).toContain('class="tb-display-popover tb-popover is-open"');
    expect(selectedHtml).toContain('tb-pop-header tb-pop-head');
    expect(selectedHtml).toContain('tb-pop-label tb-pop-row-text');
    expect(selectedHtml).toContain('class="playback-pa-capsule is-expanded mode-expanded"');
  });

  it("Phase C.3 · P5: Homepage giữ #btn-brand-home (Logo + chữ Axo); Workspace dùng thanh tab compact kiểu Ramp [‹] [›] | [icon + Tên bài toán ×] [+] hỗ trợ đầy đủ 10 kịch bản đa tab, đóng tab và điều hướng", () => {
    const homeHtml = renderToString(<App />);
    // Trên Homepage: #btn-brand-home bọc cả SVG logo mark 22x22 và chữ Axo theo chuẩn HTML V2.7
    expect(homeHtml).toMatch(
      /<button[^>]*id="btn-brand-home"[^>]*>\s*<svg[^>]*class="axo-logo-svg"[^>]*>.*?<\/svg>\s*<span class="nav-wordmark-text">Axo<\/span>\s*<\/button>/s,
    );

    const catalog = publicCatalog();
    const sample1 = catalog[0];
    const sample2 = catalog[1];
    const sample3 = catalog[2];

    // Kịch bản 1: Mở bài A
    useAppStore.getState().loadEnvelope(sample1.envelope, sample1.id, sample1.envelope.description ?? undefined);
    syncStoreForSSR();
    const tabAId = `tab-sample-${sample1.id}`;
    expect(useAppStore.getState().activeTabId).toBe(tabAId);
    expect(useAppStore.getState().workspaceTabs[0]?.problemId).toBe(sample1.id);
    expect(useAppStore.getState().workspaceTabs[0]?.sessionId).toBeTruthy();

    const wsHtml = renderToString(<SimulationWorkspace />);
    // Trên Workspace: không hiện logo Axo; cụm trái là #btn-ws-back + #btn-ws-forward, kế tiếp là #header-prob-div, tab bài toán có nút đóng × và nút + sát ngay sau tab cuối
    expect(wsHtml).not.toContain('id="btn-brand-home"');
    expect(wsHtml).toMatch(
      /<button[^>]*id="btn-ws-back"[^>]*>.*?<\/button>\s*<button[^>]*id="btn-ws-forward"[^>]*>.*?<\/button>\s*<\/div>\s*<div class="header-div ws-tabbar-div" id="header-prob-div"/s,
    );
    expect(wsHtml).toContain('id="top-prob-title"');
    expect(wsHtml).toContain(`data-close-tab="${tabAId}"`);

    // Kịch bản 7: Bấm + mở tab Bài toán mới, sau đó đóng tab nháp khi chưa gửi đề → quay về bài A
    useAppStore.getState().openDraftWorkspaceTab();
    syncStoreForSSR();
    const draftWsHtml = renderToString(<SimulationWorkspace />);
    expect(draftWsHtml).toContain("Bài toán mới");
    expect(draftWsHtml).toContain('id="ws-draft-body"');
    expect(draftWsHtml).not.toContain('role="tablist"');
    expect(draftWsHtml).not.toContain('data-close-tab="tab-draft-new"');

    useAppStore.getState().closeWorkspaceTab("tab-draft-new");
    syncStoreForSSR();
    expect(useAppStore.getState().activeTabId).toBe(tabAId);
    expect(useAppStore.getState().workspaceTabs.map((t) => t.id)).toEqual([tabAId]);

    // Kịch bản 2: Bấm + và mở bài B → thay tab nháp thành tab bài B và giữ nguyên tab bài A
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore.getState().loadEnvelope(sample2.envelope, sample2.id, sample2.envelope.description ?? undefined);
    syncStoreForSSR();
    const tabBId = `tab-sample-${sample2.id}`;
    const multiTabHtml = renderToString(<SimulationWorkspace />);
    expect(multiTabHtml).toContain(`data-tab-id="${tabAId}"`);
    expect(multiTabHtml).toContain(`data-tab-id="${tabBId}"`);
    expect(multiTabHtml).toContain(`data-close-tab="${tabAId}"`);
    expect(multiTabHtml).toContain(`data-close-tab="${tabBId}"`);
    expect(useAppStore.getState().workspaceTabs.length).toBe(2);
    expect(useAppStore.getState().activeTabId).toBe(tabBId);

    // Kịch bản 3 & 10: Chuyển qua lại giữa A và B ở bước dựng trung gian — không trộn trạng thái giữa các tab
    useAppStore.getState().activateWorkspaceTab(tabAId);
    syncStoreForSSR();
    expect(useAppStore.getState().activeTabId).toBe(tabAId);
    expect(useAppStore.getState().activeSampleId).toBe(sample1.id);

    const sceneA = withSubEntities(veKhongGian((sample1.envelope as unknown as { scene3d: Scene3D }).scene3d));
    const stepAAnchor = anchorOfGeometryStep(sceneA, 3);
    const firstEntityA = sceneA.objects[0]?.id ?? null;
    const defaultDisplay = {
      showShell: true,
      showVertexLabels: true,
      showPlane: true,
      showSection: true,
      showAxes: false,
      showDimensionLabels: true,
      showRightAngles: true,
      showDashedHidden: true,
      auxiliaryShown: true,
      gridShown: false,
      xray: false,
      shellOpacityPct: 26,
      planeOpacityPct: 38,
    };
    saveLearnerRecoverySnapshot({
      problemKey: `sample:${sample1.id}`,
      stepIndex: stepAAnchor,
      selectedId: firstEntityA,
      dockCollapsed: false,
      mobileViewMode: "dock_open",
      display: { ...defaultDisplay, xray: true },
      camera: { position: [9.5, 8.2, 11.4], target: [0.5, 0.2, 1.1] },
    });

    const sceneB = withSubEntities(veKhongGian((sample2.envelope as unknown as { scene3d: Scene3D }).scene3d));
    const stepBAnchor = anchorOfGeometryStep(sceneB, 1);
    saveLearnerRecoverySnapshot({
      problemKey: `sample:${sample2.id}`,
      stepIndex: stepBAnchor,
      selectedId: null,
      dockCollapsed: false,
      mobileViewMode: "dock_open",
      display: defaultDisplay,
      camera: { position: [5.1, 6.0, 4.8], target: [0, 0, 0] },
    });

    useAppStore.getState().activateWorkspaceTab(tabBId);
    syncStoreForSSR();
    const htmlTabB = renderToString(<SimulationWorkspace />);
    expect(htmlTabB).toContain(sample2.title.replaceAll("'", "&#x27;"));
    expect(htmlTabB).toContain("Bước 2/");

    useAppStore.getState().activateWorkspaceTab(tabAId);
    syncStoreForSSR();
    const htmlTabA = renderToString(<SimulationWorkspace />);
    expect(htmlTabA).toContain(sample1.title);
    expect(htmlTabA).toContain("Bước 4/");

    // Kịch bản 9: Tạo nhiều tab liên tiếp (thêm bài C)
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore.getState().loadEnvelope(sample3.envelope, sample3.id, sample3.envelope.description ?? undefined);
    syncStoreForSSR();
    const tabCId = `tab-sample-${sample3.id}`;
    expect(useAppStore.getState().workspaceTabs.map((t) => t.id)).toEqual([tabAId, tabBId, tabCId]);
    expect(useAppStore.getState().activeTabId).toBe(tabCId);

    // Kịch bản 4: Đóng tab không active (đóng C khi B đang active, hoặc đóng A khi B đang active)
    useAppStore.getState().activateWorkspaceTab(tabBId);
    useAppStore.getState().closeWorkspaceTab(tabCId);
    expect(useAppStore.getState().workspaceTabs.map((t) => t.id)).toEqual([tabAId, tabBId]);
    expect(useAppStore.getState().activeTabId).toBe(tabBId);

    useAppStore.getState().closeWorkspaceTab(tabAId);
    expect(useAppStore.getState().workspaceTabs.map((t) => t.id)).toEqual([tabBId]);
    expect(useAppStore.getState().activeTabId).toBe(tabBId);
    expect(useAppStore.getState().activeSampleId).toBe(sample2.id);

    // Kịch bản 5: Mở lại A, đứng ở A rồi đóng A khi B đang tồn tại → tự chuyển sang B
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore.getState().loadEnvelope(sample1.envelope, sample1.id, sample1.envelope.description ?? undefined);
    expect(useAppStore.getState().activeTabId).toBe(tabAId);
    useAppStore.getState().closeWorkspaceTab(tabAId);
    expect(useAppStore.getState().workspaceTabs.map((t) => t.id)).toEqual([tabBId]);
    expect(useAppStore.getState().activeTabId).toBe(tabBId);
    expect(useAppStore.getState().activeSampleId).toBe(sample2.id);

    // Kịch bản 8: Quay về Trang chủ rồi mở lại / dùng ‹ › không làm mất tab đang mở
    useAppStore.getState().workspaceGoBack();
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().workspaceTabs.map((t) => t.id)).toEqual([tabBId]);
    useAppStore.getState().workspaceGoForward();
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().activeTabId).toBe(tabBId);

    // Kịch bản 6: Đóng tab cuối cùng → tự động quay về Trang chủ sạch sẽ, không để Workspace 0 tab
    useAppStore.getState().closeWorkspaceTab(tabBId);
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().workspaceTabs).toEqual([]);
    expect(useAppStore.getState().activeTabId).toBeNull();
    expect(useAppStore.getState().active).toBeNull();

    // Kiểm tra vào thẳng URL /simulation/<slug> vẫn luôn có gốc Trang chủ trong workspaceNavStack để nút ‹ không bị khóa
    useAppStore.getState().syncLocationRoute(`/simulation/${sample1.id}`);
    syncStoreForSSR();
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().workspaceNavIndex).toBeGreaterThan(0);
    const directUrlHtml = renderToString(<SimulationWorkspace />);
    expect(directUrlHtml).not.toMatch(/<button[^>]*id="btn-ws-back"[^>]*disabled/);
    useAppStore.getState().workspaceGoBack();
    expect(useAppStore.getState().view).toBe("home");
  });

  it("Phase C.2 · P2, P3, P4, P5: Workspace V6.2 khôi phục nút & panel 'Tùy chỉnh hình' (#tb-geo-custom-pop), đủ 7 lớp hiển thị HTML V2.7 và sửa gutter mép phải", () => {
    const catalog = publicCatalog(); void catalog;
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
      expect(sphereHtml).toContain('id="slider-shell-opacity"');
      expect(sphereHtml).toContain('id="slider-plane-opacity"');
      expect(sphereHtml).not.toContain('id="geo-custom-experiment-group"');
      expect(sphereHtml).not.toContain('id="slider-sphere-radius"');
      expect(sphereHtml).not.toContain('id="slider-plane-height"');
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
    const catalog = publicCatalog(); void catalog;

    // 1. Hình chóp (thiet-dien-chop) ở bước cuối cùng (Bước 11/11) phải giữ cả mặt phẳng cắt (MNP) lẫn thiết diện
    const pyramidSample = offlineCatalog().find((s) => s.id === "thiet-dien-chop") ?? catalog[0];
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
    const sphereCutSample = offlineCatalog().find((s) => s.id === "cau-cat-mat-phang");
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
    expect(finalWsHtml).toContain('points="12 3 21 8 12 13 3 8 12 3"');
    expect(finalWsHtml).not.toContain('id="btn-explode"');
  });

  it("Phase C.4 · P1–P3: Chuẩn hoá Playback Play/Pause, nút mở lại Study Dock (‹ Học tập) và các nút điều khiển theo HTML V2.7", () => {
    const catalog = publicCatalog(); void catalog;
    const sample = offlineCatalog().find((s) => s.id === "thiet-dien-chop") ?? catalog[0];
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
    const catalog = publicCatalog(); void catalog;
    const sample = offlineCatalog().find((s) => s.id === "thiet-dien-chop") ?? catalog[0];
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

    const forgotHtml = renderToString(
      <AuthPageView mode="forgot" initialEmailRecoveryAvailable={true} />,
    );
    expect(forgotHtml).toContain('id="view-forgot"');
    expect(forgotHtml).toContain('id="forgot-email-input"');
    expect(forgotHtml).toContain('id="btn-forgot-to-login"');

    const forgotDisabledHtml = renderToString(
      <AuthPageView mode="forgot" initialEmailRecoveryAvailable={false} />,
    );
    expect(forgotDisabledHtml).toContain('id="view-forgot"');
    expect(forgotDisabledHtml).toContain('id="forgot-unavailable-note"');
    expect(forgotDisabledHtml).not.toContain('id="forgot-email-input"');
    expect(forgotDisabledHtml).toContain('id="btn-forgot-to-login"');

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
    expect(css).toContain("--axo-header-h: 58px;");
    expect(css).toContain("--axo-header-max-w: 1280px;");
    expect(css).toContain("--axo-ws-header-h: 38px;");
    expect(css).toContain("--axo-header-btn-h: 32px;");
    expect(css).toContain("--axo-header-btn-font: 13.5px;");
    expect(css).not.toMatch(/\.nav-bar\s+\.btn-auth-ghost[^{]*\{\s*display:\s*none;/s);
    expect(css).toContain("--axo-home-max-w: 820px;");
    expect(css).toContain("--axo-hero-title-size: 42px;");
    expect(css).toMatch(/\.composer-textarea\s*\{[^}]*min-height:\s*48px;[^}]*height:\s*48px;[^}]*max-height:\s*192px;/s);
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
    const catalog = publicCatalog(); void catalog;
    const sphereSample = offlineCatalog().find((e) => e.id === "cau-cat-mat-phang");
    const sectionSample = offlineCatalog().find((e) => e.id === "thiet-dien-chop");
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

  it("Trang giới thiệu sản phẩm Axo (LandingView) tách biệt với Màn hình nhập đề toán (HomeView) và liên kết đầy đủ luồng điều hướng", () => {
    useAppStore.getState().openLanding();
    syncStoreForSSR();
    expect(useAppStore.getState().view).toBe("landing");

    const landingHtml = renderToString(<App />);
    const landingPlainText = landingHtml.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");
    expect(landingHtml).toContain('id="view-landing"');
    expect(landingHtml).toContain('id="landing-header"');
    expect(landingHtml).toContain('id="btn-landing-header-library"');
    expect(landingHtml).toContain('id="btn-landing-header-start"');
    expect(landingHtml).toContain('id="landing-hero"');
    expect(landingHtml).toContain('id="btn-landing-hero-start"');
    expect(landingHtml).toContain('id="about-axo"');
    expect(landingHtml).toContain('id="btn-landing-about-workspace"');
    expect(landingHtml).toContain('id="cach-hoat-dong"');
    expect(landingHtml).toContain('id="bai-mau"');
    expect(landingHtml).toContain('id="btn-landing-samples-library"');
    expect(landingHtml).toContain('id="landing-footer"');
    expect(landingHtml).toContain('id="btn-landing-footer-library"');
    expect(landingPlainText).toContain("Hình học không gian, dễ hình dung hơn.");
    expect(landingHtml).toContain("Bắt đầu dựng hình");
    expect(landingHtml).not.toContain("Nơi đề bài tiếng Việt hóa thành");
    expect(landingHtml).not.toContain('id="left-sidebar"');

    // Điều hướng URL /gioi-thieu -> view === "landing"
    useAppStore.getState().syncLocationRoute("/gioi-thieu");
    expect(useAppStore.getState().view).toBe("landing");

    // Quay về Màn hình nhập đề toán -> có LeftSidebar + Composer gọn kiểu Gemini
    useAppStore.getState().goHome();
    syncStoreForSSR();
    expect(useAppStore.getState().view).toBe("home");
    const homeHtml = renderToString(<App />);
    expect(homeHtml).toContain('id="left-sidebar"');
    expect(homeHtml).toContain('id="composer-main-row"');
    expect(homeHtml).not.toContain('id="btn-home-to-landing"');
  });

  it("UI Refinement V3: Cấu trúc Sidebar mới, Thu gọn độc lập ĐANG HỌC/GẦN ĐÂY, Account Footer & Auth-Aware Routing", () => {
    // 1. Khi Guest đã xác thực trạng thái (resolved: true, user: null) truy cập / -> vào thẳng LandingView công khai, không có LeftSidebar
    useAuthStore.setState({ user: null, resolved: true });
    useAppStore.getState().syncLocationRoute("/");
    syncStoreForSSR();
    const guestRootHtml = renderToString(<App />);
    expect(guestRootHtml).toContain('id="view-landing"');
    expect(guestRootHtml).not.toContain('id="left-sidebar"');

    // 2. Khi Student đã đăng nhập truy cập / hoặc /app -> vào thẳng HomeView / Workspace + LeftSidebar + Account Footer
    useAuthStore.setState({
      user: {
        id: 101,
        email: "hocsinh@axo.vn",
        displayName: "Nguyễn Minh Anh",
        role: "student",
        mustChangePassword: false,
      },
      resolved: true,
    });
    useAppStore.getState().syncLocationRoute("/");
    syncStoreForSSR();
    const studentHomeHtml = renderToString(<App />);
    expect(studentHomeHtml).toContain('id="left-sidebar"');
    expect(studentHomeHtml).toContain('id="composer-main-row"');
    expect(studentHomeHtml).toContain('id="sb-user-account-btn"');
    expect(studentHomeHtml).toContain("Nguyễn Minh Anh");
    expect(studentHomeHtml).toContain("Học sinh");
    expect(studentHomeHtml).not.toContain('id="sb-guest-auth-row"');
    expect(studentHomeHtml).not.toContain('id="nav-item-landing"');
    expect(studentHomeHtml).not.toContain("Giới thiệu Axo");

    // 3. Kiểm tra Header Sidebar có icon Search + Collapse và thứ tự Primary Navigation: Bài toán mới -> Thư viện mô phỏng nằm trên BÀI TOÁN (không có dòng Tìm bài toán và đã bỏ mục Lịch sử riêng theo V9 Phase 3)
    expect(studentHomeHtml).not.toContain('id="nav-item-search"');
    expect(studentHomeHtml).not.toContain('id="nav-item-history"');
    const idxHeaderSearch = studentHomeHtml.indexOf('id="btn-sidebar-search"');
    const idxHeaderCollapse = studentHomeHtml.indexOf('id="btn-sidebar-collapse"');
    const idxNew = studentHomeHtml.indexOf('id="nav-item-new-problem"');
    const idxLibrary = studentHomeHtml.indexOf('id="nav-item-library"');
    const idxProblemsGroup = studentHomeHtml.indexOf('id="sidebar-group-problems"');
    const idxFooter = studentHomeHtml.indexOf('id="sb-footer"');
    expect(idxHeaderSearch).toBeGreaterThan(0);
    expect(idxHeaderCollapse).toBeGreaterThan(idxHeaderSearch);
    expect(idxNew).toBeGreaterThan(idxHeaderCollapse);
    expect(idxLibrary).toBeGreaterThan(idxNew);
    expect(idxProblemsGroup).toBeGreaterThan(idxLibrary);
    expect(idxFooter).toBeGreaterThan(idxProblemsGroup);

    // 4. Kiểm tra thu gọn/mở rộng nhóm BÀI TOÁN mà không đóng tab hay mất dữ liệu
    const sample1 = offlineCatalog()[0]!;
    const sample2 = offlineCatalog()[1]!;
    useAppStore.getState().loadEnvelope(sample1.envelope, sample1.id);
    useAppStore.getState().loadEnvelope(sample2.envelope, sample2.id);
    expect(useAppStore.getState().workspaceTabs).toHaveLength(2);

    expect(useAppStore.getState().leftRailProblemGroupCollapsed).toBe(false);
    useAppStore.getState().toggleLeftRailProblemGroup();
    syncStoreForSSR();
    expect(useAppStore.getState().leftRailProblemGroupCollapsed).toBe(true);
    expect(useAppStore.getState().workspaceTabs).toHaveLength(2);
    const collapsedHtml = renderToString(<App />);
    expect(collapsedHtml).toContain('id="sidebar-group-problems" data-group-collapsed="true"');

    useAppStore.getState().toggleLeftRailProblemGroup();
    syncStoreForSSR();
    expect(useAppStore.getState().leftRailProblemGroupCollapsed).toBe(false);
    expect(useAppStore.getState().workspaceTabs).toHaveLength(2);
  });

  it("UI Refinement V4 & V5: Composer 660px, Search icon trên Header Sidebar, Tìm kiếm tiếng Việt có dấu/không dấu và Scrollbar ẩn/hiện khi hover .sb-scroll-region", () => {
    const globalCss = readFileSync(
      new URL("../styles/global.css", import.meta.url),
      "utf-8",
    );

    // 1. Composer V9.4.1: responsive max-width 680px via --axo-composer-max-w
    expect(globalCss).toContain("--axo-composer-max-w: 680px;");
    expect(globalCss).toContain("width: min(100%, var(--axo-composer-max-w, 680px));");
    expect(globalCss).toContain("max-width: var(--axo-composer-max-w, 680px);");

    // 2. Scrollable region .sb-scroll-region tuân thủ hợp đồng thanh cuộn hiển thị W6B (scrollbar-gutter: auto, không ẩn thumb transparent)
    expect(globalCss).toMatch(/\.sb-scroll-region\s*\{[^}]*overflow-y:\s*auto;[^}]*scrollbar-gutter:\s*auto;/s);

    // 3. Gemini Search Modal CSS light mode
    expect(globalCss).toContain(".axo-search-backdrop");
    expect(globalCss).toContain(".axo-search-modal");

    // 4. Kiểm tra Header Sidebar có #btn-sidebar-search + #btn-sidebar-collapse và không còn #nav-item-search hay #sb-search-box-wrap
    useAuthStore.setState({
      user: {
        id: 104,
        email: "hocsinh@axo.vn",
        displayName: "Nguyễn Minh Anh",
        role: "student",
        mustChangePassword: false,
      },
      resolved: true,
    });
    useAppStore.getState().syncLocationRoute("/");
    syncStoreForSSR();
    const html = renderToString(<App />);
    expect(html).toContain('id="btn-sidebar-search"');
    expect(html).toContain('id="btn-sidebar-collapse"');
    expect(html).toContain('class="sb-top-actions"');
    expect(html).not.toContain('id="nav-item-search"');
    expect(html).not.toContain('id="sb-search-box-wrap"');

    // 5. Tìm kiếm tiếng Việt có dấu và không dấu (foldVietnamese & matchesSearchQuery)
    expect(foldVietnamese("Hình chóp S.ABCD có đáy là hình vuông")).toBe(
      "hinh chop s.abcd co day la hinh vuong",
    );
    expect(
      matchesSearchQuery(
        "hinh chop vuong",
        "Hình chóp S.ABCD",
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a",
      ),
    ).toBe(true);
    expect(
      matchesSearchQuery(
        "duong thang vuong goc",
        "Chứng minh đường thẳng vuông góc mặt phẳng",
      ),
    ).toBe(true);
    expect(
      matchesSearchQuery(
        "khong ton tai xyz123",
        "Hình chóp S.ABCD",
        "Lăng trụ tam giác đều",
      ),
    ).toBe(false);
  });

  it("UI Refinement V5: Danh sách BÀI TOÁN hợp nhất khử trùng lặp, Bộ lọc Tất cả/Đang mở/Gần đây, Ghim/Đổi tên/Xóa và phân biệt Xóa bài toán với Đóng tab", () => {
    const pub = publicCatalog();
    const pubCountBefore = pub.length;
    const sample1 = offlineCatalog()[0]!;
    const sample2 = offlineCatalog()[1]!;
    const sample3 = offlineCatalog()[2]!;

    // 1. Cùng một bài toán vừa mở tab vừa có trong history -> chỉ hiện 1 lần trong BÀI TOÁN
    useAppStore.getState().loadEnvelope(sample1.envelope, sample1.id);
    useAppStore.getState().loadEnvelope(sample2.envelope, sample2.id);
    // sample3 chỉ ghi vào history, không mở tab
    historyStore.record(sample3.envelope, sample3.id);
    useAppStore.setState({ history: historyStore.list() });

    const state1 = useAppStore.getState();
    const listAll1 = buildUnifiedProblemList({
      effectiveTabs: state1.workspaceTabs,
      effectiveActiveTabId: state1.activeTabId,
      view: state1.view,
      history: state1.history,
      filter: "all",
    });
    expect(listAll1.map((x) => x.canonicalId)).toHaveLength(3);
    expect(new Set(listAll1.map((x) => x.canonicalId)).size).toBe(3);

    // 2. Hai bài toán khác nhau có cùng tiêu đề -> cả hai đều xuất hiện (không khử trùng theo title)
    const customEnvA = {
      ...sample1.envelope,
      title: "Bài tập tự luyện trùng tên",
      problem_statement: "Cho hình chóp S.ABC có đáy đều cạnh a.",
    };
    const customEnvB = {
      ...sample2.envelope,
      title: "Bài tập tự luyện trùng tên",
      problem_statement: "Cho hình chóp S.ABCD có đáy hình chữ nhật.",
    };
    historyStore.record(customEnvA, null, "a-dup-title-1");
    historyStore.record(customEnvB, null, "a-dup-title-2");
    useAppStore.setState({ history: historyStore.list() });

    const state2 = useAppStore.getState();
    const listWithDupTitles = buildUnifiedProblemList({
      effectiveTabs: state2.workspaceTabs,
      effectiveActiveTabId: state2.activeTabId,
      view: state2.view,
      history: state2.history,
      filter: "all",
    });
    const dupTitleMatches = listWithDupTitles.filter(
      (x) => x.title === "Bài tập tự luyện trùng tên",
    );
    expect(dupTitleMatches).toHaveLength(2);
    expect(dupTitleMatches.map((x) => x.canonicalId).sort()).toEqual([
      "a-dup-title-1",
      "a-dup-title-2",
    ]);

    // 3. Bộ lọc V6: "ready" hiện cả bài đã dựng xong đang mở tab lẫn bài đã dựng xong trong lịch sử
    const listReadyOnly = buildUnifiedProblemList({
      effectiveTabs: state2.workspaceTabs,
      effectiveActiveTabId: state2.activeTabId,
      view: state2.view,
      history: state2.history,
      filter: "ready",
    });
    expect(listReadyOnly.every((x) => x.processingStatus === "ready")).toBe(true);
    expect(listReadyOnly).toHaveLength(5);

    // 4. Ghim / Bỏ ghim: bài được ghim lên đầu danh sách "Tất cả" và lưu bền trong historyStore
    const targetPinId = "a-dup-title-1";
    useAppStore.getState().togglePinProblem(targetPinId);
    const stateAfterPin = useAppStore.getState();
    const listAfterPin = buildUnifiedProblemList({
      effectiveTabs: stateAfterPin.workspaceTabs,
      effectiveActiveTabId: stateAfterPin.activeTabId,
      view: stateAfterPin.view,
      history: stateAfterPin.history,
      filter: "all",
    });
    expect(listAfterPin[0]?.canonicalId).toBe(targetPinId);
    expect(listAfterPin[0]?.pinned).toBe(true);
    expect(historyStore.list().find((x) => x.id === targetPinId)?.pinned).toBe(true);

    // Bỏ ghim
    useAppStore.getState().togglePinProblem(targetPinId);
    expect(historyStore.list().find((x) => x.id === targetPinId)?.pinned).toBe(false);

    // 5. Đổi tên: cập nhật đồng bộ Sidebar, HistoryStore và Tab đang mở mà KHÔNG sửa problem_statement, config hay publicCatalog
    const openTab1 = useAppStore.getState().workspaceTabs[0]!;
    const openProblemId = openTab1.historyId!;
    const originalStatement = openTab1.active?.envelope.problem_statement;
    const originalConfig = JSON.stringify(openTab1.active?.envelope.config);

    const renamedOk = useAppStore
      .getState()
      .renameProblem(openProblemId, "Chóp S.ABCD — Ôn thi HK1");
    expect(renamedOk).toBe(true);

    const updatedTab1 = useAppStore
      .getState()
      .workspaceTabs.find((t) => t.id === openTab1.id)!;
    expect(updatedTab1.title).toBe("Chóp S.ABCD — Ôn thi HK1");
    expect(updatedTab1.active?.envelope.problem_statement).toBe(originalStatement);
    expect(JSON.stringify(updatedTab1.active?.envelope.config)).toBe(originalConfig);
    expect(historyStore.list().find((x) => x.id === openProblemId)?.title).toBe(
      "Chóp S.ABCD — Ôn thi HK1",
    );

    // Không cho phép đổi tên rỗng
    expect(useAppStore.getState().renameProblem(openProblemId, "   ")).toBe(
      false,
    );

    // 6. Phân biệt Đóng tab (closeWorkspaceTab) và Xóa bài toán (deleteProblem)
    // Đóng tab: tab đóng nhưng bài vẫn còn trong historyStore và bộ lọc "all"
    useAppStore.getState().closeWorkspaceTab(openTab1.id);
    expect(
      useAppStore.getState().workspaceTabs.some((t) => t.id === openTab1.id),
    ).toBe(false);
    expect(historyStore.list().find((x) => x.id === openProblemId)).toBeDefined();

    // Mở lại bài toán đó rồi thực hiện Xóa bài toán (deleteProblem): vừa xóa khỏi historyStore vừa đóng tab đang mở
    useAppStore.getState().loadEnvelope(sample1.envelope, sample1.id);
    expect(
      useAppStore
        .getState()
        .workspaceTabs.some((t) => t.historyId === openProblemId),
    ).toBe(true);

    useAppStore.getState().deleteProblem(openProblemId);
    expect(historyStore.list().find((x) => x.id === openProblemId)).toBeUndefined();
    expect(
      useAppStore
        .getState()
        .workspaceTabs.some((t) => t.historyId === openProblemId),
    ).toBe(false);

    // Không ảnh hưởng danh mục công khai (publicCatalog)
    expect(publicCatalog()).toHaveLength(pubCountBefore);
  });

  it("UI Refinement V6: Phân loại đúng 4 trạng thái xử lý (Tất cả / Sẵn sàng / Cần chú ý / Đang tiến hành), danh sách 1 dòng gọn gàng và icon square-pen + sidebar toggle Option A", () => {
    useAppStore.getState().reset();
    historyStore.clear();
    useAuthStore.setState({
      user: {
        id: 106,
        email: "hocsinh@axo.vn",
        displayName: "Nguyễn Minh Anh",
        role: "student",
        mustChangePassword: false,
      },
      resolved: true,
    });

    const sample1 = offlineCatalog()[0]!;
    const sample2 = offlineCatalog()[1]!;

    // 1. Bài đã hoàn tất xử lý và đang mở ở Bước 3/12 -> phải là "ready", KHÔNG phải "in_progress"
    useAppStore.getState().loadEnvelope(sample1.envelope, sample1.id);
    const openTab = useAppStore.getState().workspaceTabs[0]!;
    useAppStore.getState().setTabStepProgress(openTab.id, 3, 12);

    // 2. Bài đã hoàn tất xử lý và chỉ nằm trong lịch sử (đã đóng tab) -> cũng là "ready"
    historyStore.record(sample2.envelope, sample2.id);
    useAppStore.setState({ history: historyStore.list() });

    // 3. Một bài đang thực sự chạy phân tích (in_progress) ở background dù người dùng đang mở tab khác
    const inFlightId = "attempt-v6-in-progress-1";
    useAppStore
      .getState()
      .startProblemProcessing(
        inFlightId,
        "Cho hình chóp S.ABCD có SA vuông góc đáy, tính thể tích.",
      );

    // 4. Một bài bị từ chối kiểm chứng / thiếu dữ kiện -> "needs_attention"
    const failedId = "attempt-v6-failed-1";
    useAppStore
      .getState()
      .startProblemProcessing(
        failedId,
        "Cho hình chóp S.ABC có đáy là tam giác, tính thể tích.",
      );
    useAppStore.getState().failProblemProcessing(failedId, {
      problemStatement: "Cho hình chóp S.ABC có đáy là tam giác, tính thể tích.",
      reasonCode: "MISSING_DIMENSION",
      reasonMessage: "Đề bài thiếu kích thước độ dài cạnh hoặc chiều cao.",
      unsupported: {
        status: "unsupported",
        reason: "Đề bài thiếu kích thước độ dài cạnh hoặc chiều cao.",
        failure_category: "insufficient_specification",
        error_code: "MISSING_DIMENSION",
      },
    });

    // 5. Mở thêm 1 tab nháp chưa gửi (tab-draft-new) -> xuất hiện ở "all", KHÔNG xuất hiện ở ready / needs_attention / in_progress
    useAppStore.getState().openDraftWorkspaceTab();

    const s = useAppStore.getState();
    const listAll = buildUnifiedProblemList({
      effectiveTabs: s.workspaceTabs,
      effectiveActiveTabId: s.activeTabId,
      view: s.view,
      history: s.history,
      filter: "all",
      processingRecords: s.problemProcessingRecords,
      analyzing: s.analyzing,
      activeProblemText: s.problemText,
    });
    const listReady = buildUnifiedProblemList({
      effectiveTabs: s.workspaceTabs,
      effectiveActiveTabId: s.activeTabId,
      view: s.view,
      history: s.history,
      filter: "ready",
      processingRecords: s.problemProcessingRecords,
      analyzing: s.analyzing,
      activeProblemText: s.problemText,
    });
    const listNeedsAttention = buildUnifiedProblemList({
      effectiveTabs: s.workspaceTabs,
      effectiveActiveTabId: s.activeTabId,
      view: s.view,
      history: s.history,
      filter: "needs_attention",
      processingRecords: s.problemProcessingRecords,
      analyzing: s.analyzing,
      activeProblemText: s.problemText,
    });
    const listInProgress = buildUnifiedProblemList({
      effectiveTabs: s.workspaceTabs,
      effectiveActiveTabId: s.activeTabId,
      view: s.view,
      history: s.history,
      filter: "in_progress",
      processingRecords: s.problemProcessingRecords,
      analyzing: s.analyzing,
      activeProblemText: s.problemText,
    });

    // Kiểm tra số lượng và phân loại chính xác: Sidebar mặc định ("all") chỉ hiển thị bài toán READY hợp lệ
    expect(listAll.map((x) => x.canonicalId)).toHaveLength(2);
    expect(listReady.map((x) => x.canonicalId)).toHaveLength(2);
    expect(listReady.some((x) => x.openTab?.id === openTab.id)).toBe(true);
    expect(listNeedsAttention.map((x) => x.canonicalId)).toEqual([failedId]);
    expect(listInProgress.map((x) => x.canonicalId)).toEqual([inFlightId]);
    // Tab đang xem ở Bước 3/12 tuyệt đối KHÔNG nằm trong "in_progress"
    expect(listInProgress.some((x) => x.openTab?.id === openTab.id)).toBe(false);
    // Bản nháp chưa gửi ("tab-draft-new") tuyệt đối KHÔNG xuất hiện trong danh sách bài toán BÀI TOÁN
    expect(listAll.some((x) => x.canonicalId === "tab-draft-new")).toBe(false);
    expect(listReady.some((x) => x.canonicalId === "tab-draft-new")).toBe(false);
    expect(listNeedsAttention.some((x) => x.canonicalId === "tab-draft-new")).toBe(false);
    expect(listInProgress.some((x) => x.canonicalId === "tab-draft-new")).toBe(false);

    // 6. Khi bài đang chạy hoàn tất xử lý -> tự động rời "in_progress" và chuyển sang "ready"
    useAppStore
      .getState()
      .loadEnvelope(
        sample1.envelope,
        undefined,
        "Cho hình chóp S.ABCD có SA vuông góc đáy, tính thể tích.",
        inFlightId,
      );
    const sAfterComplete = useAppStore.getState();
    const listInProgressAfter = buildUnifiedProblemList({
      effectiveTabs: sAfterComplete.workspaceTabs,
      effectiveActiveTabId: sAfterComplete.activeTabId,
      view: sAfterComplete.view,
      history: sAfterComplete.history,
      filter: "in_progress",
      processingRecords: sAfterComplete.problemProcessingRecords,
      analyzing: sAfterComplete.analyzing,
      activeProblemText: sAfterComplete.problemText,
    });
    expect(listInProgressAfter).toHaveLength(0);

    // 7. Kiểm tra DOM render của LeftSidebar: danh sách bài toán chỉ 1 dòng (không có .sb-item-sub), có icon square-pen và icon đóng/mở Option A
    syncStoreForSSR();
    const appHtml = renderToString(<App />);
    expect(appHtml).not.toContain('class="sb-item-sub"');
    expect(appHtml).toContain('class="sb-nav-icon is-new-problem-icon"');
    expect(appHtml).toContain('class="sb-toggle-layout-icon"');
    expect(appHtml).toContain('title="Ẩn thanh bên"');
    expect(appHtml).toContain('title="Hiện thanh bên"');
  });

  it("UI Refinement V7: Phân loại 7 họ khối hình học (pyramid/cube/prism/sphere/cylinder/cone/neutral), đồng bộ Sidebar + Workspace Tabs + Search Popup, phân biệt 2 icon Header, Composer 1 dòng/đa dòng/mở rộng, nền Gemini Light Mode và khôi phục trạng thái sau khi tải lại trang", () => {
    useAppStore.getState().reset();
    historyStore.clear();
    historyStore.clearProcessingRecords();
    useAuthStore.setState({
      user: {
        id: 107,
        email: "hocsinh@axo.vn",
        displayName: "Nguyễn Minh Anh",
        role: "student",
        mustChangePassword: false,
      },
      resolved: true,
    });

    // 1. Kiểm tra phân loại tất định resolveGeometrySolidFamily & render GeometryFamilyIcon cho cả 7 họ
    expect(GEOMETRY_SOLID_FAMILIES).toEqual([
      "pyramid",
      "cube",
      "prism",
      "sphere",
      "cylinder",
      "cone",
      "neutral",
    ]);

    const allSamples = offlineCatalog();
    const cubeSample =
      allSamples.find(
        (s) =>
          s.id.includes("lap-phuong") ||
          s.slug.includes("lap-phuong") ||
          s.title.toLowerCase().includes("lập phương"),
      ) ?? allSamples[0]!;
    const pyramidSample = allSamples.find((s) => s.id === "thiet-dien-chop") ?? allSamples[0]!;
    const sphereSample = allSamples.find((s) => s.id === "cau-cat-mat-phang")!;
    const cylinderSample = allSamples.find((s) => s.id === "tru-thiet-dien-tron")!;
    const coneSample = allSamples.find((s) => s.id === "non-thiet-dien-truc")!;
    const oxyzSample = allSamples.find((s) => s.id.startsWith("oxyz-"));

    expect(
      resolveGeometrySolidFamily({
        envelope: cubeSample.envelope,
        sampleId: "thiet-dien-lap-phuong",
        title: "Thiết diện lục giác đều của hình lập phương ABCD.A'B'C'D'",
      }),
    ).toBe("cube");
    expect(
      resolveGeometrySolidFamily({
        sampleId: "thiet-dien-lap-phuong",
      }),
    ).toBe("cube");
    expect(
      resolveGeometrySolidFamily({
        envelope: pyramidSample.envelope,
        sampleId: pyramidSample.id,
      }),
    ).toBe("pyramid");
    expect(
      resolveGeometrySolidFamily({
        problemStatement: "Cho hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác vuông cân tại A.",
      }),
    ).toBe("prism");
    expect(
      resolveGeometrySolidFamily({
        envelope: sphereSample.envelope,
        sampleId: sphereSample.id,
      }),
    ).toBe("sphere");
    expect(
      resolveGeometrySolidFamily({
        envelope: cylinderSample.envelope,
        sampleId: cylinderSample.id,
      }),
    ).toBe("cylinder");
    expect(
      resolveGeometrySolidFamily({
        envelope: coneSample.envelope,
        sampleId: coneSample.id,
      }),
    ).toBe("cone");
    if (oxyzSample) {
      expect(
        resolveGeometrySolidFamily({
          envelope: oxyzSample.envelope,
          sampleId: oxyzSample.id,
        }),
      ).toBe("neutral");
    }
    // Từ "thiết diện" đứng một mình hoặc đề chưa rõ khối không bao giờ tự gán thành "pyramid"
    expect(
      resolveGeometrySolidFamily({
        title: "Bài toán tìm diện tích thiết diện cắt bởi mặt phẳng (P)",
        problemStatement: "Xác định thiết diện tạo bởi mặt phẳng (P).",
      }),
    ).toBe("neutral");
    expect(resolveGeometrySolidFamily(null)).toBe("neutral");

    for (const fam of GEOMETRY_SOLID_FAMILIES) {
      const iconSvg = renderToString(<GeometryFamilyIcon family={fam} />);
      expect(iconSvg).toContain(`data-geometry-icon="${fam}"`);
      expect(iconSvg).toContain(`class="axo-geo-family-icon is-${fam}"`);
      expect(iconSvg).toContain('stroke-width="1.5"');
    }

    // 2. Kiểm tra đồng bộ icon hình học giữa Sidebar, Workspace Tabs và Search Popup
    useAppStore
      .getState()
      .loadEnvelope(
        cubeSample.envelope,
        cubeSample.id,
        "Cho hình lập phương ABCD.A'B'C'D' cạnh a. Tìm thiết diện lục giác đều.",
      );
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore
      .getState()
      .loadEnvelope(
        pyramidSample.envelope,
        pyramidSample.id,
        pyramidSample.envelope.description ?? undefined,
      );
    useAppStore.getState().openDraftWorkspaceTab();
    useAppStore
      .getState()
      .loadEnvelope(
        sphereSample.envelope,
        sphereSample.id,
        sphereSample.envelope.description ?? undefined,
      );
    useAppStore.getState().setLeftRailSearchOpen(true);
    syncStoreForSSR();

    const wsTabs = useAppStore.getState().workspaceTabs;
    expect(wsTabs).toHaveLength(3);
    expect(resolveWorkspaceTabGeometryFamily(wsTabs[0])).toBe("cube");
    expect(resolveWorkspaceTabGeometryFamily(wsTabs[1])).toBe("pyramid");
    expect(resolveWorkspaceTabGeometryFamily(wsTabs[2])).toBe("sphere");

    const wsAndSidebarHtml = renderToString(<App />);
    // Trong Sidebar: có đủ data-geometry-family="cube", "pyramid", "sphere"
    expect(wsAndSidebarHtml).toContain('data-geometry-family="cube"');
    expect(wsAndSidebarHtml).toContain('data-geometry-family="pyramid"');
    expect(wsAndSidebarHtml).toContain('data-geometry-family="sphere"');
    expect(wsAndSidebarHtml).toContain('data-geometry-icon="cube"');
    expect(wsAndSidebarHtml).toContain('data-geometry-icon="pyramid"');
    expect(wsAndSidebarHtml).toContain('data-geometry-icon="sphere"');
    // Trong Search Popup (#axo-search-modal): cũng kết xuất đúng data-geometry-family
    expect(wsAndSidebarHtml).toContain('id="axo-search-modal"');
    expect(wsAndSidebarHtml).toMatch(
      /data-geometry-family="cube"[^>]*class="axo-search-result-item/,
    );

    useAppStore.getState().setLeftRailSearchOpen(false);
    syncStoreForSSR();

    // 3. Cùng icon panel cho cả hai trạng thái sidebar.
    const toggleSvg = renderToString(<IconSidebarToggle />);
    const collapsedTriggerSvg = renderToString(<IconSidebarCollapsedTrigger />);
    expect(toggleSvg).toContain('class="sb-toggle-layout-icon"');
    expect(toggleSvg).toContain("<rect");
    expect(collapsedTriggerSvg).toBe(toggleSvg);
    expect(collapsedTriggerSvg).toContain('d="M6.25 6.75v6.5"');
    expect(collapsedTriggerSvg).not.toContain('d="M7.5 3.5v13"');

    // 4. Kiểm tra CSS & hợp đồng định vị V7 cho Filter Popover, 3-dot Menu, Composer 1 dòng / đa dòng / mở rộng, nút + xoay 45 độ và nền Gemini Light Mode
    const leftSidebarSrc = readFileSync(
      new URL("./LeftSidebar.tsx", import.meta.url),
      "utf-8",
    );
    // Filter popover mở ngay bên dưới nút lọc (triggerRect.bottom + 4, placement: "bottom" | "top", không dùng sidebarRight + 6)
    expect(leftSidebarSrc).toContain("triggerRect.bottom + 4");
    expect(leftSidebarSrc).not.toContain("sidebarRight + 6");
    // 3-dot menu mở bên dưới nút ⋮ và neo cạnh trái theo btnRect.left - 4 để vươn sang phải vượt ra ngoài Sidebar
    expect(leftSidebarSrc).toContain("btnRect.left - 4");
    expect(leftSidebarSrc).toContain("btnRect.bottom + 4");

    const globalCss = readFileSync(
      new URL("../styles/global.css", import.meta.url),
      "utf-8",
    );
    expect(globalCss).toMatch(
      /\.sb-filter-popover\s*\{[^}]*position:\s*fixed;[^}]*z-index:\s*132;[^}]*min-width:\s*192px;/s,
    );
    expect(globalCss).toMatch(
      /\.sb-action-menu-popover\s*\{[^}]*position:\s*fixed;[^}]*z-index:\s*135;[^}]*min-width:\s*176px;/s,
    );
    // Nút + chuyển thành dấu × sắc nét (không dùng transform scale/skew gây méo nét) và nền trắng trung tính Axo
    expect(globalCss).toMatch(
      /\.btn-plus-trigger\.is-open\s+svg\s*\{[^}]*transform:\s*none;/s,
    );
    expect(globalCss).toMatch(
      /#view-home\.is-minimal-home[^{]*\{[^}]*background-color:\s*(?:var\(--canvas,\s*#ffffff\)|#ffffff);[^}]*background-image:\s*none;/s,
    );

    // Kiểm tra trạng thái Composer hai tầng (V9.4 Claude-inspired) trống/1 dòng vs đa dòng trên HomeView
    useAppStore.getState().goHome();
    useAppStore.getState().setProblemText("");
    syncStoreForSSR();
    const homeSingleLineHtml = renderToString(<HomeView />);
    expect(homeSingleLineHtml).toContain('id="home-composer-box"');
    expect(homeSingleLineHtml).toContain('data-composer-layout="two-tier"');
    expect(homeSingleLineHtml).toContain('data-composer-multiline="false"');
    expect(homeSingleLineHtml).toContain('data-composer-expanded="false"');
    expect(homeSingleLineHtml).not.toContain('id="btn-composer-expand"');

    // Khi có ký tự xuống dòng (Shift+Enter) -> xuất hiện nút #btn-composer-expand ở góc trên phải
    useAppStore
      .getState()
      .setProblemText("Cho hình lập phương ABCD.A'B'C'D' cạnh a.\nTìm thiết diện qua M, N, P.");
    syncStoreForSSR();
    const homeMultiLineHtml = renderToString(<HomeView />);
    expect(homeMultiLineHtml).toContain('data-composer-layout="two-tier"');
    expect(homeMultiLineHtml).toContain('data-composer-multiline="true"');
    expect(homeMultiLineHtml).toContain('id="btn-composer-expand"');
    expect(homeMultiLineHtml).toContain('aria-label="Mở rộng khung nhập"');

    // 5. Kiểm tra Phase 7: Bền vững trạng thái xử lý & khôi phục an toàn sau khi tải lại trang (reload recovery)
    expect(
      stripStatusPrefixesFromTitle("[Đang tiến hành] Cần chú ý: Hình chóp S.ABCD"),
    ).toBe("Hình chóp S.ABCD");

    useAppStore
      .getState()
      .startProblemProcessing(
        "attempt-v7-inflight-reload",
        "Cho hình trụ có bán kính đáy r và chiều cao h.",
      );
    useAppStore
      .getState()
      .startProblemProcessing(
        "attempt-v7-failed-persist",
        "Cho hình nón có đường sinh l, tính thể tích.",
      );
    useAppStore.getState().failProblemProcessing("attempt-v7-failed-persist", {
      problemStatement: "Cho hình nón có đường sinh l, tính thể tích.",
      reasonCode: "MISSING_DIMENSION",
      reasonMessage: "Đề bài thiếu bán kính đáy hoặc chiều cao của hình nón.",
    });

    // Mô phỏng tải lại trang (reload): đọc lại từ storage với recoverReloadInterrupted = true
    useAppStore.getState().hydrateProblemProcessingAfterReload();
    const afterReload = useAppStore.getState();
    expect(afterReload.analyzing).toBe(false);
    // Bản ghi đang chạy dở khi reload không bao giờ bị treo spinner vô tận mà chuyển sang needs_attention với lý do rõ ràng
    const recoveredInflight =
      afterReload.problemProcessingRecords["attempt-v7-inflight-reload"];
    expect(recoveredInflight).toBeDefined();
    expect(recoveredInflight?.status).toBe("needs_attention");
    expect(recoveredInflight?.reasonCode).toBe("INTERRUPTED_BY_RELOAD");
    expect(recoveredInflight?.reasonMessage).toBe(INTERRUPTED_BY_RELOAD_REASON);

    // Bản ghi needs_attention trước đó vẫn được bảo toàn nguyên vẹn sau khi reload
    const recoveredFailed =
      afterReload.problemProcessingRecords["attempt-v7-failed-persist"];
    expect(recoveredFailed).toBeDefined();
    expect(recoveredFailed?.status).toBe("needs_attention");
    expect(recoveredFailed?.reasonCode).toBe("MISSING_DIMENSION");
  });

  it("UI Refinement V8: Rollback nền trắng trung tính Axo, Filter Popover vươn phải (bottom-start), Composer đa dòng tự co giãn chiều cao sát nội dung, Icon mở rộng không cắt nét, Menu tải tệp tối gọn kiểu Gemini và khôi phục kết nối gián đoạn khi reload", () => {
    useAppStore.getState().reset();
    historyStore.clear();
    historyStore.clearProcessingRecords();
    historyStore.clearDraftText();
    useAuthStore.setState({
      user: {
        id: 108,
        email: "hocsinh@axo.vn",
        displayName: "Nguyễn Minh Anh",
        role: "student",
        mustChangePassword: false,
      },
      resolved: true,
    });

    const globalCss = readFileSync(
      new URL("../styles/global.css", import.meta.url),
      "utf-8",
    );
    const leftSidebarSrc = readFileSync(
      new URL("./LeftSidebar.tsx", import.meta.url),
      "utf-8",
    );
    const problemInputSrc = readFileSync(
      new URL("./ProblemInput.tsx", import.meta.url),
      "utf-8",
    );
    const homeViewSrc = readFileSync(
      new URL("./HomeView.tsx", import.meta.url),
      "utf-8",
    );

    // 1. Phase 1: Rollback nền trắng trung tính chuẩn Axo (bỏ radial-gradient xanh Gemini Light Mode V7)
    expect(homeViewSrc).not.toContain("gemini-light-home");
    expect(homeViewSrc).not.toContain('data-bg-mode="gemini-light"');
    expect(globalCss).not.toContain("rgba(211, 227, 253");
    expect(globalCss).toMatch(
      /#view-home,\s*#view-home\.is-minimal-home,\s*(?:\.app-main,\s*)?\.axo-body\.ws-draft-body,\s*\.axo-body\.ws-draft-body\s+#view-home\.is-minimal-home\s*\{[^}]*background-color:\s*(?:var\(--canvas,\s*#ffffff\)|#ffffff);[^}]*background-image:\s*none;/s,
    );

    // 2. Phase 5 & Phase 6: Filter Popover mở bên dưới nút lọc theo hướng bottom-start và vươn sang phải vượt ra ngoài Sidebar; giữ nguyên 3-dot menu
    expect(leftSidebarSrc).toContain('placement: shouldFlipUp ? "top-start" : "bottom-start"');
    expect(leftSidebarSrc).toContain(
      "Math.max(8, Math.min(vw - popoverWidth - 8, triggerRect.left))",
    );
    expect(leftSidebarSrc).not.toContain("sidebarRight - popoverWidth");
    expect(leftSidebarSrc).not.toContain("triggerRect.right - popoverWidth");
    expect(leftSidebarSrc).toContain("btnRect.left - 4");
    expect(leftSidebarSrc).toContain("btnRect.bottom + 4");

    // 3. V9.4 Two-tier Composer tự co giãn chiều cao sát nội dung (48px mặc định, 48..192px auto-grow, 216..312px expanded)
    expect(problemInputSrc).toContain('el.style.height = "48px";');
    expect(problemInputSrc).toContain("Math.min(Math.max(measured, 48), 192)");
    expect(problemInputSrc).toContain("Math.min(Math.max(measured, 216), 312)");
    expect(globalCss).toMatch(
      /\.home-composer-box\s+\.composer-textarea\s*\{[^}]*min-height:\s*48px;[^}]*height:\s*48px;[^}]*max-height:\s*192px;/s,
    );
    expect(globalCss).toMatch(
      /\.home-composer-box\.is-expanded\s+\.composer-textarea\s*\{[^}]*min-height:\s*216px;[^}]*max-height:\s*312px;/s,
    );

    // 4. Phase 3: Icon mở rộng / thu gọn (#btn-composer-expand) 15x15 viewBox="0 0 24 24", overflow: "visible", không viền, hai mũi tên chéo hướng ra ngoài / vào trong
    expect(problemInputSrc).toContain('data-expand-icon="expand"');
    expect(problemInputSrc).toContain('data-expand-icon="collapse"');
    expect(problemInputSrc).toContain('<polyline points="15 3 21 3 21 9" />');
    expect(problemInputSrc).toContain('<polyline points="9 21 3 21 3 15" />');
    expect(problemInputSrc).toContain('<polyline points="4 14 10 14 10 20" />');
    expect(problemInputSrc).toContain('<polyline points="20 10 14 10 14 4" />');
    expect(globalCss).toMatch(
      /\.btn-composer-expand\s*\{[^}]*width:\s*28px;[^}]*height:\s*28px;[^}]*border:\s*none;/s,
    );

    // 5. Phase 4: Nút + / × (#btn-composer-plus) tách biệt focus chuột vs :focus-visible bàn phím và Menu tải tệp nổi kiểu Claude Light Mode (#plus-popover-menu) có icon kẹp giấy (paperclip)
    expect(problemInputSrc).toContain('data-icon-state="plus"');
    expect(problemInputSrc).toContain('data-icon-state="close"');
    expect(problemInputSrc).toContain('data-icon="paperclip"');
    expect(problemInputSrc).toContain(
      'd="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"',
    );
    expect(globalCss).toMatch(
      /\.composer-plus-btn:focus:not\(:focus-visible\)\s*\{[^}]*outline:\s*none;[^}]*box-shadow:\s*none;/s,
    );
    expect(globalCss).toMatch(
      /\.composer-plus-btn:focus-visible\s*\{[^}]*outline:\s*2px\s+solid\s+#2563eb;[^}]*outline-offset:\s*2px;/s,
    );
    expect(globalCss).toMatch(
      /#plus-popover-menu\.plus-popover-menu\s*\{[^}]*border-radius:\s*12px;[^}]*background:\s*var\(--surface,\s*#ffffff\);[^}]*color:\s*#1f1e1d;/s,
    );

    // Kiểm tra SSR render của HomeView ở trạng thái multiline có đúng icon expand và menu upload paperclip
    useAppStore.getState().goHome();
    useAppStore
      .getState()
      .setProblemText("Cho hình chóp S.ABCD có đáy là hình vuông cạnh a.\nSA vuông góc với đáy.");
    syncStoreForSSR();
    const homeV8Html = renderToString(<HomeView />);
    expect(homeV8Html).toContain('data-composer-layout="two-tier"');
    expect(homeV8Html).toContain('data-composer-multiline="true"');
    expect(homeV8Html).toContain('data-expand-icon="expand"');
    expect(homeV8Html).toContain('data-icon-state="plus"');
    expect(homeV8Html).toContain('data-icon="paperclip"');
    expect(homeV8Html).toContain("Tải tệp từ thiết bị");

    // 6. Phase 4.6: Đính kèm tệp hợp lệ (PDF/DOCX/PNG) khi chưa nhập chữ vẫn cho phép gửi (canSubmitComposer = true)
    const pdfCheck = validateComposerFile({
      name: "de-thi-hk1-hinh-khong-gian.pdf",
      size: 24576,
      type: "application/pdf",
    });
    expect(pdfCheck.ok).toBe(true);
    expect(canSubmitComposer("", 1, false)).toBe(true);
    expect(canSubmitComposer("   ", 1, false)).toBe(true);
    expect(canSubmitComposer("", 0, false)).toBe(false);

    // 7. Phase 7.1 & 7.2: Phân biệt rõ kết nối bị ngắt khi tải lại trang (CONNECTION_INTERRUPTED) với lỗi đề bài (PROBLEM_ERROR), bảo toàn bản nháp và khôi phục đề bài khi bấm vào mục Cần chú ý
    expect(INTERRUPTED_BY_RELOAD_REASON).toBe(
      "Kết nối xử lý bị ngắt khi tải lại trang (chưa xác nhận trạng thái máy chủ)",
    );

    const reloadAttemptId = "attempt-v8-reload-interrupted";
    const reloadStatement =
      "Cho hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều cạnh a, AA' = a√3. Tính thể tích.";
    const errorAttemptId = "attempt-v8-problem-error";
    const errorStatement = "Cho hình chóp S.ABC, tính thể tích.";

    useAppStore.getState().setProblemText("");
    historyStore.clearDraftText();
    useAppStore.getState().startProblemProcessing(errorAttemptId, errorStatement);
    useAppStore.getState().failProblemProcessing(errorAttemptId, {
      problemStatement: errorStatement,
      reasonCode: "MISSING_DIMENSION",
      reasonMessage: "Đề bài thiếu kích thước độ dài cạnh hoặc chiều cao.",
    });
    historyStore.clearDraftText();
    useAppStore.getState().startProblemProcessing(reloadAttemptId, reloadStatement);

    // Mô phỏng reload khi reloadAttemptId đang in_progress và ô nhập / draft trống
    historyStore.clearDraftText();
    useAppStore.setState({ problemText: "" });
    useAppStore.getState().hydrateProblemProcessingAfterReload();

    const stateAfterReload = useAppStore.getState();
    const interruptedRec = stateAfterReload.problemProcessingRecords[reloadAttemptId];
    const problemErrorRec = stateAfterReload.problemProcessingRecords[errorAttemptId];

    expect(interruptedRec).toBeDefined();
    expect(interruptedRec?.status).toBe("needs_attention");
    expect(interruptedRec?.reasonCode).toBe("INTERRUPTED_BY_RELOAD");
    expect(interruptedRec?.reasonMessage).toBe(INTERRUPTED_BY_RELOAD_REASON);
    expect(interruptedRec?.interruptedByReload).toBe(true);
    expect(interruptedRec?.failureKind).toBe("CONNECTION_INTERRUPTED");
    expect(interruptedRec?.problemStatement).toBe(reloadStatement);

    expect(problemErrorRec).toBeDefined();
    expect(problemErrorRec?.status).toBe("needs_attention");
    expect(problemErrorRec?.reasonCode).toBe("MISSING_DIMENSION");
    expect(problemErrorRec?.interruptedByReload).toBe(false);
    expect(problemErrorRec?.failureKind).toBe("PROBLEM_ERROR");

    // Bản nháp và problemText tự động được khôi phục từ bài bị ngắt kết nối khi reload
    expect(historyStore.readDraftText()).toBe(reloadStatement);
    expect(stateAfterReload.problemText).toBe(reloadStatement);

    // Khi người dùng bấm vào một mục Cần chú ý khác trong Sidebar (selectSidebarProblem / openProblemAttempt), nội dung đề của mục đó được nạp lại vào Composer để chỉnh sửa & gửi lại ngay
    useAppStore.getState().selectSidebarProblem(errorAttemptId);
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().problemText).toBe(errorStatement);
    expect(historyStore.readDraftText()).toBe(errorStatement);
  });

  it("UI Refinement V9: Nền trắng trung tính pre-V7, Menu + Light Mode 2 hành động (Tải tệp + Chụp ảnh), loại bỏ mục Lịch sử riêng & hợp nhất vào BÀI TOÁN, khử trùng lặp nút mở/đóng Sidebar và đồng bộ UI 4 vai trò (Guest/Student/Teacher/Admin)", () => {
    useAppStore.getState().reset();
    historyStore.clear();
    historyStore.clearProcessingRecords();
    historyStore.clearDraftText();

    const globalCss = readFileSync(
      new URL("../styles/global.css", import.meta.url),
      "utf-8",
    );
    const leftSidebarSrc = readFileSync(
      new URL("./LeftSidebar.tsx", import.meta.url),
      "utf-8",
    );
    const topNavSrc = readFileSync(
      new URL("./TopNav.tsx", import.meta.url),
      "utf-8",
    );
    const problemInputSrc = readFileSync(
      new URL("./ProblemInput.tsx", import.meta.url),
      "utf-8",
    );

    // 1. Phase 1: Nền trắng trung tính từ baseline pre-V7 (#ffffff / var(--canvas, #ffffff), không gradient xanh)
    expect(globalCss).toMatch(
      /#view-home,\s*#view-home\.is-minimal-home,\s*(?:\.app-main,\s*)?\.axo-body\.ws-draft-body,\s*\.axo-body\.ws-draft-body\s+#view-home\.is-minimal-home\s*\{[^}]*background-color:\s*(?:var\(--canvas,\s*#ffffff\)|#ffffff);[^}]*background-image:\s*none;/s,
    );

    // 2. Phase 2: Menu tải tệp (#plus-popover-menu) đồng bộ Claude Light Mode (#ffffff, chữ #1f1e1d) và phân giải đúng hành động theo thiết bị (Desktop: Tải tệp + Chụp màn hình; Mobile: Tải tệp + Chụp ảnh đề bài)
    expect(problemInputSrc).toContain("const showCameraEntry = menuCaps.showCamera;");
    expect(globalCss).toMatch(
      /#plus-popover-menu\.plus-popover-menu\s*\{[^}]*width:\s*224px;[^}]*border-radius:\s*12px;[^}]*background:\s*var\(--surface,\s*#ffffff\);[^}]*color:\s*#1f1e1d;/s,
    );
    expect(globalCss).toMatch(
      /#plus-popover-menu\.plus-popover-menu\s+\.plus-menu-item\s+svg,\s*\.plus-menu-item-icon\s+svg\s*\{[^}]*width:\s*18px;[^}]*height:\s*18px;[^}]*color:\s*#3d3d3a;[^}]*stroke:\s*#3d3d3a;/s,
    );

    const homeHtml = renderToString(<HomeView />);
    expect(homeHtml).toContain('id="plus-popover-menu"');
    expect(homeHtml).toContain('id="menu-item-upload-file"');
    expect(homeHtml).toContain("Tải tệp từ thiết bị");
    expect(homeHtml).toContain('data-icon="paperclip"');
    const mobileCameraMenuHtml = renderToString(
      <ProblemInput
        initialPlusMenuOpen
        deviceSignals={{
          userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
          maxTouchPoints: 5,
          anyCoarsePointer: true,
        }}
      />,
    );
    expect(mobileCameraMenuHtml).toContain('id="menu-item-camera"');
    expect(mobileCameraMenuHtml).toContain("Chụp ảnh đề bài");
    expect(mobileCameraMenuHtml).toContain('data-testid="btn-plus-camera"');
    expect(mobileCameraMenuHtml).toContain('<circle cx="12" cy="13" r="3.75"></circle>');

    // 3. Phase 3: Loại bỏ mục Lịch sử riêng (#nav-item-history) khỏi LeftSidebar & TopNav, chuyển hướng sạch /history -> home và bảo toàn 100% historyStore trong BÀI TOÁN + #axo-search-modal
    expect(leftSidebarSrc).not.toContain('id="nav-item-history"');
    expect(topNavSrc).not.toContain('id="btn-acc-open-history"');
    expect(topNavSrc).not.toContain('view: "history"');

    const sampleA = offlineCatalog()[0]!;
    const sampleB = offlineCatalog()[1]!;
    useAppStore.getState().loadEnvelope(sampleA.envelope, sampleA.id);
    const savedHistoryA = historyStore.list()[0]!;
    historyStore.touch(savedHistoryA.id, { lastCursor: 5 });
    // Đóng tab sampleA để sampleA trở thành bài đã đóng tab nằm trong historyStore
    const openTabA = useAppStore.getState().workspaceTabs[0]!;
    useAppStore.getState().closeWorkspaceTab(openTabA.id);
    expect(useAppStore.getState().workspaceTabs).toHaveLength(0);

    // Ghi thêm sampleB đang mở tab
    useAppStore.getState().loadEnvelope(sampleB.envelope, sampleB.id);
    useAppStore.setState({ history: historyStore.list() });

    // Điều hướng /history hoặc gọi openHistory() -> chuyển sạch về view === "home", không rơi vào not_found hay trang lịch sử riêng
    useAppStore.getState().syncLocationRoute("/history");
    expect(useAppStore.getState().view).toBe("home");
    expect(useAppStore.getState().navHistoryMode).toBe("replace");

    useAppStore.getState().openLibrary();
    expect(useAppStore.getState().view).toBe("library");
    useAppStore.getState().openHistory();
    expect(useAppStore.getState().view).toBe("home");

    // Danh sách BÀI TOÁN hợp nhất và Search Popup chứa cả bài đang mở tab (sampleB) lẫn bài đã đóng tab trong historyStore (sampleA)
    const unifiedV9 = buildUnifiedProblemList({
      effectiveTabs: useAppStore.getState().workspaceTabs,
      effectiveActiveTabId: useAppStore.getState().activeTabId,
      view: useAppStore.getState().view,
      history: useAppStore.getState().history,
      filter: "all",
    });
    expect(unifiedV9.some((x) => x.canonicalId === savedHistoryA.id)).toBe(true);
    expect(unifiedV9.some((x) => x.openTab?.problemId === sampleB.id)).toBe(true);

    // Bấm lại vào bài đã đóng tab (savedHistoryA) từ BÀI TOÁN -> mở lại đúng bài và bảo toàn bước dựng lastCursor = 5 mà không nhân bản tab
    useAppStore.getState().selectSidebarProblem(savedHistoryA.id);
    expect(useAppStore.getState().view).toBe("workspace");
    expect(useAppStore.getState().activeSampleId).toBe(sampleA.id);
    expect(historyStore.list().find((x) => x.id === savedHistoryA.id)?.lastCursor).toBe(5);
    expect(useAppStore.getState().workspaceTabs).toHaveLength(2);

    // 4. Phase 4: Nhất quán nút đóng/mở Sidebar (expanded / collapsed / hover-preview / mobile) — không bao giờ hiện 2 nút trùng chức năng
    useAuthStore.setState({ user: null, resolved: true });
    useAppStore.getState().goHome();
    useAppStore.getState().setLeftRailCollapsed(false);
    useAppStore.getState().setLeftRailHoverPreview(false);
    syncStoreForSSR();
    const expandedHtml = renderToString(<App />);
    expect(expandedHtml).toContain('data-sidebar-state="expanded"');
    expect(expandedHtml).toContain('id="btn-sidebar-collapse"');
    expect(expandedHtml).toContain('title="Ẩn thanh bên"');
    expect(expandedHtml).toMatch(
      /<button[^>]*id="btn-sidebar-open-trigger"[^>]*aria-hidden="true"/,
    );

    useAppStore.getState().setLeftRailCollapsed(true);
    useAppStore.getState().setLeftRailHoverPreview(false);
    syncStoreForSSR();
    const collapsedHtml = renderToString(<App />);
    expect(collapsedHtml).toContain('data-sidebar-state="collapsed"');
    expect(collapsedHtml).toMatch(
      /<button[^>]*id="btn-sidebar-open-trigger"[^>]*tabindex="0"/,
    );
    expect(collapsedHtml).not.toMatch(
      /<button[^>]*id="btn-sidebar-open-trigger"[^>]*aria-hidden="true"/,
    );

    useAppStore.getState().setLeftRailHoverPreview(true);
    syncStoreForSSR();
    const hoverPreviewHtml = renderToString(<App />);
    expect(hoverPreviewHtml).toContain('data-sidebar-state="hover-preview"');
    expect(hoverPreviewHtml).toContain('title="Ghim mở thanh bên"');
    expect(hoverPreviewHtml).toContain("sb-collapsed-trigger-zone is-visible is-preview-open");
    expect(hoverPreviewHtml).toMatch(
      /<button[^>]*id="btn-sidebar-open-trigger"[^>]*aria-hidden="true"/,
    );
    expect(globalCss).toMatch(
      /\.sb-collapsed-trigger-zone\.is-visible\.is-preview-open\s*\{[^}]*opacity:\s*0\s*!important;[^}]*pointer-events:\s*none\s*!important;[^}]*visibility:\s*hidden\s*!important;/s,
    );

    // Mobile drawer open -> .app-root.is-mobile-sidebar-open và ẩn #btn-mobile-open-sidebar / #btn-mobile-open-ws
    useAppStore.getState().setLeftRailCollapsed(false);
    useAppStore.getState().setLeftRailHoverPreview(false);
    useAppStore.getState().setLeftRailMobileOpen(true);
    syncStoreForSSR();
    const mobileDrawerOpenHtml = renderToString(<App />);
    expect(mobileDrawerOpenHtml).toContain("is-mobile-sidebar-open");
    expect(mobileDrawerOpenHtml).toMatch(
      /<button[^>]*id="btn-mobile-open-sidebar"[^>]*class="[^"]*is-hidden-when-drawer-open[^"]*"[^>]*aria-hidden="true"/,
    );
    useAppStore.getState().setLeftRailMobileOpen(false);
    syncStoreForSSR();

    // 5. Phase 5 & Phase 6 (cập nhật V9.2): Kiểm tra UI tài khoản 4 vai trò (Guest / Student / Teacher / Admin)
    // 5a. Guest: nút icon hình người #btn-header-guest-account + #header-guest-popover ở Header và nút đơn #sb-guest-account-btn ("Đăng nhập") ở Sidebar Footer
    const guestAppHtml = renderToString(<App />);
    expect(guestAppHtml).toContain('id="header-guest-actions"');
    expect(guestAppHtml).toContain('id="btn-header-guest-account"');
    expect(guestAppHtml).toContain('id="header-guest-popover"');
    expect(guestAppHtml).toContain('id="btn-open-login"');
    expect(guestAppHtml).toContain('id="btn-open-signup"');
    expect(guestAppHtml).toContain('class="sb-account-anchor"');
    expect(guestAppHtml).toContain('id="sb-guest-account-btn"');
    expect(guestAppHtml).toContain('class="sb-guest-login-btn"');
    expect(guestAppHtml).toContain('class="sb-guest-login-icon"');
    expect(guestAppHtml).toContain('<span class="sb-guest-login-label">Đăng nhập</span>');
    expect(guestAppHtml).not.toContain('id="sb-guest-account-popover"');
    expect(guestAppHtml).not.toContain('id="btn-sb-guest-login"');
    expect(guestAppHtml).not.toContain('id="btn-sb-guest-signup"');
    expect(guestAppHtml).not.toContain("Đăng nhập · Đăng ký");

    // 5b. Student: hiển thị "Học sinh", không hiện nhóm Quản lý lớp học hay Quản trị
    useAuthStore.setState({
      user: {
        id: 201,
        email: "hocsinh.v9@axo.vn",
        displayName: "Lê Minh Khoa",
        role: "student",
        mustChangePassword: false,
      },
      resolved: true,
    });
    syncStoreForSSR();
    const studentV9Html = renderToString(<App />);
    expect(studentV9Html).toContain('id="sb-user-account-btn"');
    expect(studentV9Html).toContain("Lê Minh Khoa");
    expect(studentV9Html).toContain("Học sinh");
    expect(studentV9Html).not.toContain('id="sidebar-group-teacher"');
    expect(studentV9Html).not.toContain('id="nav-item-admin"');

    // 5c. Teacher: hiển thị "Giáo viên" và dùng chung Sidebar học tập như Học sinh (không còn #sidebar-group-teacher)
    useAuthStore.setState({
      user: {
        id: 202,
        email: "giaovien.v9@axo.vn",
        displayName: "Thầy Trần Quốc Tuấn",
        role: "teacher",
        mustChangePassword: false,
      },
      resolved: true,
    });
    syncStoreForSSR();
    const teacherV9Html = renderToString(<App />);
    expect(teacherV9Html).toContain("Thầy Trần Quốc Tuấn");
    expect(teacherV9Html).toContain("Giáo viên");
    expect(teacherV9Html).toContain('id="nav-item-new-problem"');
    expect(teacherV9Html).toContain('id="nav-item-library"');
    expect(teacherV9Html).toContain('id="sidebar-group-problems"');
    expect(teacherV9Html).not.toContain('id="sidebar-group-teacher"');
    expect(teacherV9Html).not.toContain('id="nav-item-classes"');
    expect(teacherV9Html).not.toContain('id="nav-item-assignments"');
    expect(teacherV9Html).not.toContain('id="nav-item-monitor"');

    // 5d. Admin: hiển thị "Quản trị viên", có #nav-item-admin, #btn-sb-acc-admin và nút #btn-admin-back-workspace trong AdminWorkspaceView
    useAuthStore.setState({
      user: {
        id: 203,
        email: "admin.v9@axo.vn",
        displayName: "Quản Trị Hệ Thống",
        role: "admin",
        mustChangePassword: false,
      },
      resolved: true,
    });
    syncStoreForSSR();
    const adminHomeV9Html = renderToString(<App />);
    expect(adminHomeV9Html).toContain("Quản Trị Hệ Thống");
    expect(adminHomeV9Html).toContain("Quản trị viên");
    expect(adminHomeV9Html).toContain('id="nav-item-admin"');
    expect(topNavSrc).toContain('id="btn-acc-open-admin"');
    expect(leftSidebarSrc).toContain('id="btn-sb-acc-admin"');

    const adminWorkspaceV9Html = renderToString(<AdminWorkspaceView />);
    expect(adminWorkspaceV9Html).toContain('id="view-admin"');
    expect(adminWorkspaceV9Html).toContain('id="btn-admin-back-workspace"');
    expect(adminWorkspaceV9Html).toContain("Về không gian học");
    expect(adminWorkspaceV9Html).toContain("Quản Trị Hệ Thống");
    expect(adminWorkspaceV9Html).toContain("Quản trị viên");
  });

  it("AXO UI Refinement V9.1: Hover Preview popover interaction, frameless .sb-open-trigger-btn, mobile responsive rules, và 4 geometry families camera framing", () => {
    const leftSidebarSrc = readFileSync(new URL("./LeftSidebar.tsx", import.meta.url), "utf8");
    const globalCss = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    const scene3dViewSrc = readFileSync(
      new URL("../simulations/domains/geometry/scene3d-view.tsx", import.meta.url),
      "utf8",
    );

    // 1. V9.1 Phase 1.3 — Hover Preview & Popover Interaction (updated for V9.2 single-click guest login button)
    expect(leftSidebarSrc).toContain("const isPointerInsidePreviewRef = useRef(false);");
    expect(leftSidebarSrc).toContain(
      "if (actionMenuState || filterMenuOpen || accountMenuOpen) return;",
    );
    expect(leftSidebarSrc).toMatch(
      /id="sb-problem-filter-popover"[\s\S]*?onMouseEnter=\{handlePanelMouseEnter\}[\s\S]*?onMouseLeave=\{handlePreviewZoneMouseLeave\}/,
    );
    expect(leftSidebarSrc).toMatch(
      /id="sb-problem-action-menu"[\s\S]*?onMouseEnter=\{handlePanelMouseEnter\}[\s\S]*?onMouseLeave=\{handlePreviewZoneMouseLeave\}/,
    );

    // 2. V9.1 Phase 1.2 & Phase 4 — Frameless Collapsed Trigger & Mobile Responsive Polish
    expect(globalCss).toMatch(
      /\.sb-open-trigger-btn\s*\{[^}]*border-color:\s*transparent\s*!important;[^}]*box-shadow:\s*none\s*!important;/s,
    );
    expect(globalCss).toMatch(
      /@media\s*\(max-width:\s*767px\)\s*\{[\s\S]*?\.page-stack,\s*\.observe-bar,\s*\.inline-form,\s*\.lib-toolbar,\s*\.lib-cat-pills,\s*\.admin-shell/s,
    );

    // 3. V9.1 Phase 2 & 3 — 4 Geometry Families camera framing & resize preservation
    expect(scene3dViewSrc).toContain("daGiacNghienCuuRaw.length >= 3 ? daGiacNghienCuuRaw : neoGonMp");
    expect(scene3dViewSrc).toContain("if (maxAbsNdc <= 0.96) return;");

    const targetSampleIds = [
      "chop-thiet-dien-ba-diem",
      "lap-phuong-thiet-dien-bat-ky",
      "mat-phang-tiep-xuc-mat-cau",
      "hinh-non-cat-song-song-day",
    ] as const;

    const pub = publicCatalog();
    for (const sampleId of targetSampleIds) {
      const entry = pub.find((e) => e.id === sampleId);
      expect(entry).toBeDefined();
      const rawScene = (entry!.envelope as unknown as { scene3d: Scene3D }).scene3d;
      const scene = withSubEntities(veKhongGian(rawScene));
      const stepCount = geometryStepCount(scene);
      expect(stepCount).toBeGreaterThanOrEqual(4);

      const ct = cauTrucSuPham(scene.objects);
      expect(ct.diem.length).toBeGreaterThan(0);
      expect(ct.canh.length).toBeGreaterThan(0);

      const huong = chonHuongNhin(ct.diem, ct.canh, ct.mat, ct.tuyChon);
      expect(Math.hypot(...huong)).toBeGreaterThan(0);

      const knExpanded = khungNhinSuPham(ct.diem, ct.canh, ct.mat, 50, 1170 / 806, huong);
      const knCollapsed = khungNhinSuPham(ct.diem, ct.canh, ct.mat, 50, 1440 / 806, huong);
      expect(knExpanded).not.toBeNull();
      expect(knCollapsed).not.toBeNull();
      // Target point is identical across aspect ratios
      expect(knExpanded!.nhinVao).toEqual(knCollapsed!.nhinVao);

      if (sampleId === "mat-phang-tiep-xuc-mat-cau") {
        expect(ct.tuyChon.matTiepDienCau).toHaveLength(1);
        expect(ct.tuyChon.matTrongTam ?? []).toHaveLength(0);
      }
    }
  });

  it("AXO UI Refinement V9.2: Guest Account Footer 1-click Login recovery, Auth Loading skeleton, Composer smooth 28px/24px height & paste multiline, và Compact Light Mode Upload Menu", () => {
    const leftSidebarSrc = readFileSync(new URL("./LeftSidebar.tsx", import.meta.url), "utf8");
    const problemInputSrc = readFileSync(new URL("./ProblemInput.tsx", import.meta.url), "utf8");
    const globalCss = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");

    // 1. Auth Loading (!user && !authResolved) -> #sb-auth-loading-row (0 flash of Guest "Đăng nhập")
    useAuthStore.setState({ user: null, resolved: false });
    syncStoreForSSR();
    const loadingSidebarHtml = renderToString(<LeftSidebar />);
    expect(loadingSidebarHtml).toContain('id="sb-auth-loading-row"');
    expect(loadingSidebarHtml).toContain('aria-busy="true"');
    expect(loadingSidebarHtml).not.toContain('id="sb-guest-account-btn"');

    // 2. Guest (!user && authResolved) -> ONLY [Icon] Đăng nhập, 1-click setView("login")
    useAuthStore.setState({ user: null, resolved: true });
    syncStoreForSSR();
    const guestSidebarHtml = renderToString(<LeftSidebar />);
    expect(guestSidebarHtml).toContain('id="sb-guest-account-btn"');
    expect(guestSidebarHtml).toContain('class="sb-guest-login-btn"');
    expect(guestSidebarHtml).toContain('<span class="sb-guest-login-label">Đăng nhập</span>');
    expect(guestSidebarHtml).not.toContain('id="sb-guest-account-popover"');
    expect(guestSidebarHtml).not.toContain("Đăng nhập · Đăng ký");
    expect(guestSidebarHtml).not.toContain('<span class="sb-user-name">Tài khoản</span>');
    expect(leftSidebarSrc).toMatch(
      /id="sb-guest-account-btn"[\s\S]*?onClick=\{\(\)\s*=>\s*\{\s*setView\("login"\);\s*closeMobileIfOpen\(\);\s*\}\}/,
    );

    // 3. V9.4 Claude-inspired two-tier Composer (min-height: 118px, border-radius: 20px), explicit pixel heights & onPaste multiline transition
    expect(globalCss).toMatch(
      /\.home-composer-box\s*\{[^}]*min-height:\s*118px;[^}]*border-radius:\s*20px;/s,
    );
    expect(problemInputSrc).toContain('el.style.height = "48px";');
    expect(problemInputSrc).toContain("Math.min(Math.max(measured, 48), 192)");
    expect(problemInputSrc).toContain("Math.min(Math.max(measured, 216), 312)");
    expect(problemInputSrc).toContain("onPaste={onPasteText}");

    // 4. V9.4.2 Floating Upward-Preferred Claude Light Mode Upload Menu (#plus-popover-menu: 224px width, 36px item height, 12px radius)
    expect(globalCss).toMatch(
      /#plus-popover-menu\.plus-popover-menu\s*\{[^}]*bottom:\s*calc\(100%\s*\+\s*8px\);[^}]*width:\s*224px;[^}]*padding:\s*5px;[^}]*gap:\s*2px;[^}]*border-radius:\s*12px;/s,
    );
    expect(globalCss).toMatch(
      /#plus-popover-menu\.plus-popover-menu\s+\.plus-menu-item\s*\{[^}]*min-height:\s*36px;[^}]*height:\s*36px;/s,
    );
    const plusOpenHtml = renderToString(<ProblemInput initialPlusMenuOpen />);
    expect(plusOpenHtml).toContain('id="plus-popover-menu"');
    expect(plusOpenHtml).toContain('id="menu-item-upload-file"');
    expect(plusOpenHtml).toContain("Tải tệp từ thiết bị");
    expect(plusOpenHtml).toContain('id="menu-item-screen-capture"');
    expect(plusOpenHtml).toContain("Chụp màn hình");
  });

  it("AXO UI Refinement V9.3/V9.4: Architecture Cleanup (gỡ bỏ Lớp học / Bài thực hành / Theo dõi lớp / LiveSession), đồng nhất Sidebar Học sinh & Giáo viên, và Composer hai tầng V9.4", () => {
    const leftSidebarSrc = readFileSync(new URL("./LeftSidebar.tsx", import.meta.url), "utf8");
    const globalCss = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");

    // 1. Không còn cụm Quản lý lớp học trong LeftSidebar
    expect(leftSidebarSrc).not.toContain("sidebar-group-teacher");
    expect(leftSidebarSrc).not.toContain("nav-item-classes");
    expect(leftSidebarSrc).not.toContain("nav-item-assignments");
    expect(leftSidebarSrc).not.toContain("nav-item-monitor");

    // 2. Giáo viên dùng chung Sidebar học tập như Học sinh nhưng giữ nguyên tên & vai trò "Giáo viên" ở Footer
    useAuthStore.setState({
      user: {
        id: 302,
        email: "giaovien.v93@axo.vn",
        displayName: "Thầy Trần Quốc Tuấn",
        role: "teacher",
        mustChangePassword: false,
      },
      resolved: true,
    });
    syncStoreForSSR();
    const teacherSidebarHtml = renderToString(<LeftSidebar />);
    expect(teacherSidebarHtml).toContain('id="nav-item-new-problem"');
    expect(teacherSidebarHtml).toContain('id="nav-item-library"');
    expect(teacherSidebarHtml).toContain('id="sidebar-group-problems"');
    expect(teacherSidebarHtml).toContain("Thầy Trần Quốc Tuấn");
    expect(teacherSidebarHtml).toContain("Giáo viên");
    expect(teacherSidebarHtml).not.toContain("sidebar-group-teacher");

    // 3. Sticky #sb-footer và Composer hai tầng V9.4 (min-height: 118px, border-radius: 20px, không còn .is-singleline)
    expect(globalCss).toMatch(/#sb-footer,\s*\.sb-footer\s*\{[^}]*position:\s*sticky;[^}]*bottom:\s*0;/s);
    expect(globalCss).not.toContain(".is-singleline");
    expect(globalCss).toMatch(
      /\.home-composer-box\s*\{[^}]*min-height:\s*118px;[^}]*border-radius:\s*20px;/s,
    );
  });
});
