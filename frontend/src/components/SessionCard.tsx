import {
  canonicalSlugForSampleId,
  geometryCategoryForItem,
  recoverCatalogScene3D,
  resolveGeometrySampleId,
} from "../data/offline-catalog";
import {
  geometryStepCount,
  hopLeScene3D,
  type Scene3D,
} from "../simulations/domains/geometry/scene3d-model";
import { buildPedagogicalConstructionPlan } from "../simulations/domains/geometry/scene3d-semantic-policy";
import { withSubEntities } from "../simulations/domains/geometry/scene3d-subentities";
import { getSimulation } from "../simulations/registry";
import type { SimulationEnvelope } from "../simulations/types";
import type { HistoryItem } from "../state/history";
import { SamplePreview } from "./SamplePreview";

export interface ProgressStats {
  step: number;
  total: number;
  pct: number;
  label: string;
}

const _pedStepCountCache = new WeakMap<Scene3D, { sig: string; count: number }>();

function pedStepSig(scene: Scene3D): string {
  return `${scene.objects.length}:${scene.events.length}:${scene.objects.map((o) => o.id).join(",")}`;
}

export function stepCountOfEnvelope(envelope: SimulationEnvelope): number {
  try {
    const env3d = recoverCatalogScene3D(envelope);
    const scene3d = (env3d as { scene3d?: unknown }).scene3d;
    if (hopLeScene3D(scene3d)) {
      const sig = pedStepSig(scene3d);
      const cached = _pedStepCountCache.get(scene3d);
      let pedCount = cached && cached.sig === sig ? cached.count : undefined;
      if (pedCount === undefined) {
        pedCount = buildPedagogicalConstructionPlan(withSubEntities(scene3d)).steps.length;
        _pedStepCountCache.set(scene3d, { sig, count: pedCount });
      }
      if (pedCount > 0) return pedCount;
      const count3d = geometryStepCount(scene3d);
      if (count3d > 0) return count3d;
    }
  } catch {
    /* bản ghi lịch sử có dữ liệu 3D hỏng không được làm sập thẻ danh sách Trang chủ / Lịch sử */
  }
  const mod = getSimulation(envelope.simulation_id);
  if (mod && mod.timeline) {
    const check = mod.validateConfig(envelope.config);
    if (check.ok) {
      try {
        const total = mod.timeline.stepCount(mod.init(check.config));
        if (total > 0) return total;
      } catch {
        /* fallback bên dưới */
      }
    }
  }
  const cfg = envelope.config as { view_steps?: unknown[] } | null | undefined;
  if (cfg && Array.isArray(cfg.view_steps) && cfg.view_steps.length > 0) {
    return cfg.view_steps.length;
  }
  return 4;
}

export function progressStatsOf(item: HistoryItem): ProgressStats {
  const total = Math.max(1, stepCountOfEnvelope(item.envelope));
  const rawStep = item.lastCursor !== null ? item.lastCursor + 1 : 1;
  const step = Math.min(Math.max(1, rawStep), total);
  const pct = Math.min(100, Math.max(0, Math.round((step / total) * 100)));
  return {
    step,
    total,
    pct,
    label: `Bước ${step}/${total}`,
  };
}

/**
 * Tương thích hàm cũ — trả nhãn tiến độ dạng "Bước X/Y" hoặc null khi <= 1 bước.
 */
export function progressOf(item: HistoryItem): string | null {
  const mod = getSimulation(item.simulationId);
  if (!mod || !mod.timeline) return null;
  const check = mod.validateConfig(item.envelope.config);
  if (!check.ok) return null;
  let total: number;
  try {
    total = mod.timeline.stepCount(mod.init(check.config));
  } catch {
    return null;
  }
  if (total <= 1) return null;
  const step = Math.min(Math.max(0, item.lastCursor ?? 0) + 1, total);
  return `Bước ${step}/${total}`;
}

export function SessionCard({
  item,
  onOpen,
  onRemove,
  deleting = false,
  variant = "home",
}: {
  item: HistoryItem;
  onOpen: () => void;
  onRemove?: () => void;
  deleting?: boolean;
  variant?: "home" | "history";
}) {
  const sampleId = resolveGeometrySampleId(item);
  const category = geometryCategoryForItem(item);
  const stats = progressStatsOf(item);

  if (variant === "history") {
    return (
      <article
        className="history-card"
        data-history-prob={sampleId ?? item.id}
        data-canonical-slug={canonicalSlugForSampleId(sampleId ?? item.id)}
      >
        {onRemove && (
          <button
            type="button"
            className="btn-history-item-remove"
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            disabled={deleting}
            aria-label={`Xóa ${item.title} khỏi lịch sử`}
            title="Xóa khỏi lịch sử"
          >
            <svg
              viewBox="0 0 16 16"
              width="14"
              height="14"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        )}
        <div className="resume-home-left">
          <div className="resume-mini-thumb" aria-hidden="true">
            <SamplePreview sampleId={sampleId} category={category} />
          </div>
          <div className="resume-info">
            <div className="resume-title" title={item.title}>{item.title}</div>
            <div className="resume-meta-row">
              <span>
                Loại bài: <strong>{category}</strong>
              </span>
              <span>·</span>
              <span>{stats.label}</span>
              <div className="progress-track" aria-label={`Tiến độ ${stats.pct}%`}>
                <div className="progress-fill" style={{ width: `${stats.pct}%` }} />
              </div>
              <span>{stats.pct}%</span>
            </div>
          </div>
        </div>
        <div className="history-card-actions">
          <button
            type="button"
            className="btn-resume-session"
            data-resume-prob={sampleId ?? item.id}
            onClick={onOpen}
          >
            Tiếp tục →
          </button>
        </div>
      </article>
    );
  }

  return (
    <div
      className="resume-home-card"
      id="home-resume-card-container"
    >
      <div className="resume-home-left">
        <div className="resume-mini-thumb" id="home-resume-thumb" aria-hidden="true">
          <SamplePreview sampleId={sampleId} category={category} />
        </div>
        <div className="resume-info">
          <div className="resume-title" id="home-resume-title">
            {item.title}
          </div>
          <div className="resume-meta-row" id="home-resume-meta">
            <span>{category}</span>
            <span>·</span>
            <span>
              Đang học: <strong>{stats.label}</strong>
            </span>
            <div className="progress-track" aria-hidden="true">
              <div className="progress-fill" style={{ width: `${stats.pct}%` }} />
            </div>
          </div>
        </div>
      </div>
      <button
        type="button"
        className="btn-resume-session"
        id="btn-home-resume-latest"
        onClick={onOpen}
      >
        Tiếp tục →
      </button>
    </div>
  );
}
