import { useEffect, useMemo, useRef, useState } from "react";
import {
  geometryShapeLabel,
  LIBRARY_CATEGORY_ORDER,
  problemTextForSample,
  publicCatalog,
  type CatalogEntry,
  type LibraryCategory,
} from "../data/offline-catalog";
import type { Domain } from "../simulations/types";
import { resolveEffectiveWorkspaceTabs, useAppStore } from "../state/store";
import { findMatchingOpenSimulationTab } from "../state/workspace-tab-identity";
import { SamplePreview } from "./SamplePreview";
import { stepCountOfEnvelope } from "./SessionCard";
import { WorkspaceTabBar } from "./WorkspaceTabBar";
import { GeometryFamilyIcon, normalizeGeometryFamily } from "./geometry2d";

/**
 * Thư viện mô phỏng Axo V2.7 (Phase B — Full UI Replacement, P5).
 *
 * Chuyển nguyên vẹn cấu trúc `#view-library` từ `axo-unified-ui-v2-7-composer-validation-divider-review.html`:
 * - `.page-container#view-library`
 * - `.page-head-block`: tiêu đề `Thư viện mô phỏng`, `#library-count-readout`, mô tả phụ
 * - `.lib-toolbar`: `.lib-search-wrap` (`#library-search-input`, `#btn-library-search-clear`) +
 *   `.lib-cat-dropdown-wrap` (`#btn-library-category-dropdown`, `#library-category-menu`)
 * - `.lib-cards-grid` (`#library-cards-grid`): lưới `.lib-card` với SVG thumbnail đầy đủ chi tiết,
 *   nhãn loại hình, tiêu đề, đề bài và chân thẻ `{stepCount} bước dựng 3D` + `Mở mô phỏng →`.
 */

export const GROUP_ORDER: Domain[] = ["geometry"];

const PROBLEM_CATALOG_ORDER: readonly string[] = [
  "chop-thiet-dien-ba-diem",
  "lap-phuong-thiet-dien-bat-ky",
  "khoang-cach-diem-mat-phang-nghieng",
  "goc-nhi-dien-hai-mat-phang",
  "khoang-cach-hai-duong-cheo-nhau",
  "lang-tru-tam-giac-thiet-dien",
  "mat-cau-cat-mat-phang",
  "oxyz-giao-diem-duong-mat",
  "mat-phang-tiep-xuc-mat-cau",
  "hinh-non-cat-song-song-day",
  "chop-mat-cau-ngoai-tiep",
  "thiet-dien-chop",
  "cau-cat-mat-phang",
  "tru-thiet-dien-tron",
  "non-thiet-dien-truc",
  "mat-cheo-sac",
  "vuong-goc-chop",
  "mp-vuong-goc-duong",
  "the-tich-chop",
  "cau-the-tich",
  "tru-truc-xien",
  "non-duong-sinh",
];

export function LibraryView({
  initialSearch,
  initialCategory,
  initialCategoryMenuOpen = false,
}: {
  initialSearch?: string;
  initialCategory?: LibraryCategory;
  initialCategoryMenuOpen?: boolean;
} = {}) {
  const loadEnvelope = useAppStore((s) => s.loadEnvelope);
  const activateWorkspaceTab = useAppStore((s) => s.activateWorkspaceTab);
  const libraryTabOpen = useAppStore((s) => s.libraryTabOpen);
  const libraryUiState = useAppStore((s) => s.libraryUiState);
  const setLibraryUiState = useAppStore((s) => s.setLibraryUiState);
  const [query, setQueryState] = useState<string>(
    initialSearch !== undefined ? initialSearch : libraryUiState.search,
  );
  const [activeCat, setActiveCatState] = useState<LibraryCategory>(
    initialCategory !== undefined
      ? initialCategory
      : ((libraryUiState.category || "all") as LibraryCategory),
  );
  const [menuOpen, setMenuOpen] = useState(initialCategoryMenuOpen);
  const dropdownWrapRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialSearch === undefined && query !== libraryUiState.search) {
      setQueryState(libraryUiState.search);
    }
  }, [initialSearch, libraryUiState.search]);

  useEffect(() => {
    if (initialCategory === undefined) {
      const nextCat = (libraryUiState.category || "all") as LibraryCategory;
      if (activeCat !== nextCat) {
        setActiveCatState(nextCat);
      }
    }
  }, [initialCategory, libraryUiState.category]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || typeof window === "undefined") return;
    const savedTop = useAppStore.getState().libraryUiState.scrollTop;
    const scrollParent = el.closest(".app-single") as HTMLElement | null;
    if (savedTop > 0) {
      el.scrollTop = savedTop;
      if (scrollParent) {
        scrollParent.scrollTop = savedTop;
      }
      if (
        el.scrollHeight <= el.clientHeight &&
        document.documentElement.scrollHeight > window.innerHeight
      ) {
        try {
          window.scrollTo(0, savedTop);
        } catch {
          /* bỏ qua trong jsdom nếu scrollTo chưa được cài */
        }
      }
    }

    const onParentScroll = () => {
      if (scrollParent && scrollParent.scrollTop !== useAppStore.getState().libraryUiState.scrollTop) {
        setLibraryUiState({ scrollTop: scrollParent.scrollTop });
      }
    };
    const onWindowScroll = () => {
      if (el.scrollHeight <= el.clientHeight) {
        setLibraryUiState({ scrollTop: window.scrollY || document.documentElement.scrollTop || 0 });
      }
    };
    scrollParent?.addEventListener("scroll", onParentScroll, { passive: true });
    window.addEventListener("scroll", onWindowScroll, { passive: true });
    return () => {
      scrollParent?.removeEventListener("scroll", onParentScroll);
      window.removeEventListener("scroll", onWindowScroll);
    };
  }, [setLibraryUiState]);

  const setQuery = (next: string) => {
    setQueryState(next);
    setLibraryUiState({ search: next });
  };

  const setActiveCat = (next: LibraryCategory) => {
    setActiveCatState(next);
    setLibraryUiState({ category: next });
  };

  const entries = useMemo(() => {
    const raw = publicCatalog();
    return [...raw].sort((a, b) => {
      const ia = PROBLEM_CATALOG_ORDER.indexOf(a.id);
      const ib = PROBLEM_CATALOG_ORDER.indexOf(b.id);
      return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
    });
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    const onPointerDown = (e: MouseEvent) => {
      if (
        dropdownWrapRef.current &&
        e.target instanceof Node &&
        !dropdownWrapRef.current.contains(e.target)
      ) {
        setMenuOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [menuOpen]);

  const trimmedQuery = query.trim();
  const normalizedQuery = trimmedQuery.toLowerCase();

  const matchesQuery = (entry: CatalogEntry): boolean => {
    if (!normalizedQuery) return true;
    const cat = geometryShapeLabel(entry.id);
    const desc = problemTextForSample(entry.id);
    const haystack = `${entry.title} ${desc} ${cat}`.toLowerCase();
    return haystack.includes(normalizedQuery);
  };

  const countForCategory = (cat: LibraryCategory): number =>
    entries.filter((entry) => {
      const catMatch = cat === "all" || geometryShapeLabel(entry.id) === cat;
      return catMatch && matchesQuery(entry);
    }).length;

  const filtered = entries.filter((entry) => {
    const catMatch =
      activeCat === "all" || geometryShapeLabel(entry.id) === activeCat;
    return catMatch && matchesQuery(entry);
  });

  const activeCatName = activeCat === "all" ? "Tất cả" : activeCat;

  const openSample = (entry: CatalogEntry) => {
    const state = useAppStore.getState();
    const { tabs: effectiveTabs } = resolveEffectiveWorkspaceTabs({
      workspaceTabs: state.workspaceTabs,
      activeTabId: state.activeTabId,
      active: state.active,
      activeSampleId: state.activeSampleId,
      activeHistoryId: state.activeHistoryId,
    });
    const existingTab = findMatchingOpenSimulationTab(effectiveTabs, {
      tabId: `tab-sample-${entry.id}`,
      sampleId: entry.id,
      title: entry.title,
      problemStatement: problemTextForSample(entry.id) || entry.envelope.problem_statement || null,
      envelope: entry.envelope,
    });
    if (existingTab) {
      activateWorkspaceTab(existingTab.id);
      return;
    }
    loadEnvelope(entry.envelope, entry.id);
  };

  return (
    <>
      {libraryTabOpen ? <WorkspaceTabBar /> : null}
      <div
        ref={containerRef}
        className="page-container"
        id="view-library"
        onScroll={(e) => setLibraryUiState({ scrollTop: e.currentTarget.scrollTop })}
      >
      <div className="page-head-block">
        <div className="page-head-row">
          <h1 className="page-main-title">Thư viện mô phỏng</h1>
        </div>
        <p className="page-sub-desc">
          Khám phá các bài toán hình học không gian qua mô hình 3D tương tác và từng bước dựng hình.
        </p>
      </div>

      <div className="lib-toolbar">
        <div className="lib-search-wrap">
          <svg
            className="lib-search-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="M21 21l-4.3-4.3" />
          </svg>
          <input
            type="search"
            id="library-search-input"
            className="lib-search-input"
            placeholder="Tìm bài mô phỏng..."
            aria-label="Tìm kiếm bài mô phỏng"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            type="button"
            className={`lib-search-clear${trimmedQuery ? " visible" : ""}`}
            id="btn-library-search-clear"
            title="Xóa từ khóa tìm kiếm"
            aria-label="Xóa từ khóa tìm kiếm"
            onClick={() => setQuery("")}
          >
            ×
          </button>
        </div>

        <div
          className={`lib-cat-dropdown-wrap${menuOpen ? " is-open" : ""}`}
          id="library-category-dropdown-wrap"
          ref={dropdownWrapRef}
        >
          <button
            type="button"
            className={`btn-lib-cat-dropdown lib-cat-dropdown-btn${menuOpen ? " is-open" : ""}`}
            id="btn-library-category-dropdown"
            aria-haspopup="listbox"
            aria-expanded={menuOpen}
            aria-controls="library-category-menu"
            onClick={() => setMenuOpen((v) => !v)}
          >
            <span className="btn-lib-cat-left lib-cat-btn-label" id="library-category-btn-label">
              {activeCat !== "all" ? (
                <GeometryFamilyIcon
                  family={normalizeGeometryFamily(activeCat)}
                  size={16}
                  className="btn-lib-cat-family-icon"
                />
              ) : (
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                </svg>
              )}
              <strong id="library-category-selected-label">{activeCatName}</strong>
            </span>
            <svg
              className="btn-lib-cat-caret lib-cat-caret"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          <div
            className={`lib-cat-dropdown-menu${menuOpen ? " open" : ""}`}
            id="library-category-menu"
            role="listbox"
            aria-label="Lọc theo loại hình học"
          >
            {LIBRARY_CATEGORY_ORDER.map((cat) => {
              const isSelected = activeCat === cat;
              const label = cat === "all" ? "Tất cả" : cat;
              const count = countForCategory(cat);
              return (
                <button
                  key={cat}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  className={`lib-cat-menu-item${isSelected ? " active" : ""}`}
                  data-lib-cat={cat}
                  onClick={() => {
                    setActiveCat(cat);
                    setMenuOpen(false);
                  }}
                >
                  <span className="lib-cat-menu-item-left">
                    <span className="lib-cat-menu-check" aria-hidden="true">
                      <svg
                        viewBox="0 0 16 16"
                        width="12"
                        height="12"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <polyline points="3 8.5 6.5 12 13 4.5" />
                      </svg>
                    </span>
                    {cat !== "all" ? (
                      <GeometryFamilyIcon
                        family={normalizeGeometryFamily(cat)}
                        size={15}
                        className="lib-cat-menu-family-icon"
                      />
                    ) : null}
                    <span>{label}</span>
                  </span>
                  <span className="lib-cat-menu-count">{count}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="lib-filter-meta-row" id="library-filter-meta-row">
        <span className="lib-filter-count page-sub-desc" id="library-count-readout">
          {`${filtered.length} bài mô phỏng phù hợp`}
        </span>
        {activeCat !== "all" ? (
          <button
            type="button"
            className="btn-lib-filter-clear"
            id="btn-library-filter-clear"
            aria-label={`Bỏ lọc ${activeCatName}`}
            onClick={() => setActiveCat("all")}
          >
            <span>{`Bỏ lọc: ${activeCatName}`}</span>
            <span aria-hidden="true">×</span>
          </button>
        ) : null}
      </div>

      <div className="lib-cards-grid" id="library-cards-grid">
        {filtered.length === 0 ? (
          <div className="lib-empty-state">
            {trimmedQuery ? (
              <>Không tìm thấy bài mô phỏng nào khớp từ khóa &ldquo;{trimmedQuery}&rdquo;.</>
            ) : (
              "Chưa có bài mô phỏng nào trong nhóm hình này."
            )}
          </div>
        ) : (
          filtered.map((entry) => {
            const cat = geometryShapeLabel(entry.id);
            const desc =
              problemTextForSample(entry.id) ||
              entry.envelope.description ||
              entry.title;
            const stepCount = stepCountOfEnvelope(entry.envelope);
            return (
              <article
                key={entry.id}
                className="lib-card"
                data-lib-prob={entry.id}
                data-canonical-slug={entry.slug}
                role="button"
                tabIndex={0}
                onClick={() => openSample(entry)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    openSample(entry);
                  }
                }}
              >
                <div className="lib-card-thumb" aria-hidden="true">
                  <SamplePreview sampleId={entry.id} category={cat} />
                </div>
                <span className="lib-card-cat">{cat}</span>
                <h3 className="lib-card-title">{entry.title}</h3>
                <p className="lib-card-desc">{desc}</p>
                <div className="lib-card-foot">
                  <span>{stepCount} bước dựng 3D</span>
                  <span>Mở mô phỏng →</span>
                </div>
              </article>
            );
          })
        )}
      </div>
    </div>
    </>
  );
}
