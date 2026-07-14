import { useMemo } from "react";
import { DOMAIN_COLOR, DOMAIN_LABEL } from "../data/offline-catalog";
import { getSimulation } from "../simulations/registry";
import type { Domain } from "../simulations/types";
import type { HistoryItem } from "../state/history";
import { formatRelativeTime } from "./HomeView";
import { IconChevronRight, IconClose } from "./icons";
import { previewKindOf, SamplePreview } from "./SamplePreview";

/**
 * SessionCard (M9-UX4) — MỘT thẻ cho phiên học đã lưu, dùng chung bởi
 * "Tiếp tục học" (Home) và trang Lịch sử.
 *
 * Trước M9-UX4 hai chỗ này có hai kiểu thẻ riêng: Home có thẻ chữ-không-tranh,
 * Lịch sử có hàng rộng gần hết màn hình — và cả hai đều KHÔNG nói được điều học
 * sinh cần nhất ("mình học dở tới đâu"), trong khi Lịch sử còn in thẳng
 * `algorithm.bubble_sort` ra màn hình. Gộp về một thẻ: cùng ngôn ngữ thị giác với
 * thẻ gợi ý ở Home, và bớt được một component thay vì nuôi hai kiểu song song.
 */

/**
 * Tiến độ SUY TỪ ENGINE TẤT ĐỊNH, không lưu trong localStorage.
 *
 * Vì sao không persist `totalSteps`: `HistoryItem` là schema v1 đã nằm trong máy
 * người dùng; thêm trường bắt buộc + bump version sẽ **xoá sạch lịch sử đang có**
 * (entry version lạ bị bỏ qua êm). Envelope đã lưu là đủ để engine tự tính lại —
 * timeline vốn tất định, đó chính là lý do reopen zero-AI hoạt động (bất biến #17).
 *
 * Module KHÔNG khai `timeline` (exploratory, vd `logic.and_gate`) → trả null →
 * KHÔNG có thanh tiến độ. UI dẫn xuất từ capability, không bịa ra "1 bước".
 */
export function progressOf(item: HistoryItem): { cursor: number; total: number } | null {
  const mod = getSimulation(item.simulationId);
  if (!mod?.timeline) return null;
  try {
    const state = mod.init(item.envelope.config as never);
    const total = mod.timeline.stepCount(state as never);
    if (total <= 1) return null;
    const cursor = Math.min(Math.max(item.lastCursor ?? 0, 0), total - 1);
    return { cursor, total };
  } catch {
    // Envelope cũ/lạ không dựng được → im lặng bỏ tiến độ, KHÔNG làm hỏng thẻ.
    return null;
  }
}

export function SessionCard({
  item,
  onOpen,
  onRemove,
}: {
  item: HistoryItem;
  onOpen: () => void;
  /** Không truyền → không có nút xóa (Home không xóa, Lịch sử có). */
  onRemove?: () => void;
}) {
  const progress = useMemo(() => progressOf(item), [item]);
  const domain = item.domain as Domain;
  const domainLabel = DOMAIN_LABEL[domain] ?? item.domain;

  return (
    <div className="session-card">
      <button className="session-main" onClick={onOpen} title="Mở lại — không gọi AI">
        <SamplePreview kind={previewKindOf(item.simulationId)} />

        <span className="session-body">
          <strong className="session-title">{item.title}</strong>

          {/* Nhãn tiếng Việt — KHÔNG BAO GIỜ in simulation_id ra cho học sinh. */}
          <span className="session-meta">
            <span className="starter-dot" style={{ background: DOMAIN_COLOR[domain] }} />
            {domainLabel}
            {progress && <> · bước {progress.cursor + 1} / {progress.total}</>}
            {" · "}
            {formatRelativeTime(item.lastViewedAt)}
          </span>

          {progress && (
            <span
              className="session-bar"
              role="progressbar"
              aria-valuenow={progress.cursor + 1}
              aria-valuemin={1}
              aria-valuemax={progress.total}
            >
              <i style={{ width: `${((progress.cursor + 1) / progress.total) * 100}%` }} />
            </span>
          )}
        </span>

        <span className="session-go">
          Tiếp tục
          <IconChevronRight size={14} />
        </span>
      </button>

      {onRemove && (
        <button className="session-remove" onClick={onRemove} title="Xóa khỏi lịch sử">
          <IconClose size={15} />
        </button>
      )}
    </div>
  );
}
