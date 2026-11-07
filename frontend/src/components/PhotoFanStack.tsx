import { useCallback, useEffect, useRef, useState } from "react";

export interface CapturedSessionPhoto {
  id: string;
  file: File;
  fullUrl: string;
  thumbUrl: string;
  width: number;
  height: number;
  createdAt: number;
}

export const MAX_VISIBLE_FAN_CARDS = 5;
export const FAN_LEAVE_DELAY_MS = 140;

export interface FanPose {
  tx: number;
  ty: number;
  rot: number;
}

export const FAN_LAYOUTS: Record<number, { collapsed: FanPose[]; open: FanPose[] }> = {
  1: {
    collapsed: [{ tx: 0, ty: 0, rot: 0 }],
    open: [{ tx: 0, ty: 0, rot: 0 }],
  },
  2: {
    collapsed: [
      { tx: -4, ty: -2, rot: -6 },
      { tx: 2, ty: 0, rot: 3 },
    ],
    open: [
      { tx: -26, ty: -8, rot: -11 },
      { tx: 24, ty: -6, rot: 9 },
    ],
  },
  3: {
    collapsed: [
      { tx: -6, ty: -3, rot: -8 },
      { tx: -1, ty: -2, rot: -2 },
      { tx: 4, ty: 0, rot: 5 },
    ],
    open: [
      { tx: -46, ty: -5, rot: -16 },
      { tx: 0, ty: -14, rot: 0 },
      { tx: 46, ty: -5, rot: 16 },
    ],
  },
  4: {
    collapsed: [
      { tx: -7, ty: -3, rot: -9 },
      { tx: -2, ty: -2, rot: -3 },
      { tx: 2, ty: -1, rot: 2 },
      { tx: 5, ty: 0, rot: 6 },
    ],
    open: [
      { tx: -64, ty: -2, rot: -20 },
      { tx: -22, ty: -13, rot: -7 },
      { tx: 22, ty: -13, rot: 7 },
      { tx: 64, ty: -2, rot: 20 },
    ],
  },
  5: {
    collapsed: [
      { tx: -8, ty: -4, rot: -10 },
      { tx: -4, ty: -3, rot: -5 },
      { tx: 0, ty: -2, rot: 0 },
      { tx: 3, ty: -1, rot: 4 },
      { tx: 6, ty: 0, rot: 7 },
    ],
    open: [
      { tx: -80, ty: 2, rot: -22 },
      { tx: -40, ty: -10, rot: -11 },
      { tx: 0, ty: -16, rot: 0 },
      { tx: 40, ty: -10, rot: 11 },
      { tx: 80, ty: 2, rot: 22 },
    ],
  },
};

export interface PhotoFanStackProps {
  photos: CapturedSessionPhoto[];
  isMobile: boolean;
  onOpenPhoto: (photoIndex: number) => void;
  onOpenMobileTray: () => void;
  disabled?: boolean;
}

export function PhotoFanStack({
  photos,
  isMobile,
  onOpenPhoto,
  onOpenMobileTray,
  disabled = false,
}: PhotoFanStackProps) {
  const [fanOpen, setFanOpen] = useState(false);
  const leaveTimerRef = useRef<number | null>(null);
  const clusterRef = useRef<HTMLDivElement | null>(null);

  const clearLeaveTimer = useCallback(() => {
    if (leaveTimerRef.current !== null) {
      window.clearTimeout(leaveTimerRef.current);
      leaveTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      clearLeaveTimer();
    };
  }, [clearLeaveTimer]);

  useEffect(() => {
    if (photos.length < 2 && fanOpen) {
      setFanOpen(false);
    }
  }, [photos.length, fanOpen]);

  const handleMouseEnter = useCallback(() => {
    if (isMobile || photos.length < 2 || disabled) return;
    clearLeaveTimer();
    setFanOpen(true);
  }, [clearLeaveTimer, disabled, isMobile, photos.length]);

  const handleMouseLeave = useCallback(() => {
    if (isMobile) return;
    clearLeaveTimer();
    leaveTimerRef.current = window.setTimeout(() => {
      setFanOpen(false);
      leaveTimerRef.current = null;
    }, FAN_LEAVE_DELAY_MS);
  }, [clearLeaveTimer, isMobile]);

  const handleFocusCapture = useCallback(() => {
    if (isMobile || photos.length < 2 || disabled) return;
    clearLeaveTimer();
    setFanOpen(true);
  }, [clearLeaveTimer, disabled, isMobile, photos.length]);

  const handleBlurCapture = useCallback(
    (e: React.FocusEvent<HTMLDivElement>) => {
      if (isMobile) return;
      const nextTarget = e.relatedTarget as Node | null;
      if (nextTarget && clusterRef.current?.contains(nextTarget)) {
        return;
      }
      clearLeaveTimer();
      setFanOpen(false);
    },
    [clearLeaveTimer, isMobile],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape" && fanOpen) {
        e.stopPropagation();
        clearLeaveTimer();
        setFanOpen(false);
      }
    },
    [clearLeaveTimer, fanOpen],
  );

  if (photos.length === 0) {
    return null;
  }

  const totalCount = photos.length;
  const startIndex = Math.max(0, totalCount - MAX_VISIBLE_FAN_CARDS);
  const visiblePhotos = photos.slice(startIndex);
  const visibleCount = visiblePhotos.length;
  const overflowCount = Math.max(0, totalCount - MAX_VISIBLE_FAN_CARDS);

  if (totalCount === 1) {
    const single = photos[0];
    return (
      <div
        ref={clusterRef}
        className="photo-fan-cluster"
        data-photo-count="1"
        data-fan-open="false"
      >
        <div id="photo-fan-stack" className="photo-fan-stack">
          <button
            id="btn-photo-fan-single"
            type="button"
            className="fan-card fan-card-single"
            disabled={disabled}
            aria-label="Xem ảnh vừa chụp (Ảnh 1)"
            onClick={() => {
              if (isMobile) {
                onOpenMobileTray();
              } else {
                onOpenPhoto(0);
              }
            }}
          >
            <img src={single.thumbUrl} alt="Ảnh đề 1" draggable={false} />
          </button>
        </div>
      </div>
    );
  }

  const layoutSpec = FAN_LAYOUTS[visibleCount] ?? FAN_LAYOUTS[MAX_VISIBLE_FAN_CARDS];
  const isSpread = !isMobile && fanOpen;
  const poses = isSpread ? layoutSpec.open : layoutSpec.collapsed;

  return (
    <div
      ref={clusterRef}
      className={isSpread ? "photo-fan-cluster is-fan-open" : "photo-fan-cluster"}
      data-photo-count={String(totalCount)}
      data-fan-open={isSpread ? "true" : "false"}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocusCapture={handleFocusCapture}
      onBlurCapture={handleBlurCapture}
      onKeyDown={handleKeyDown}
    >
      <div
        id="photo-fan-stack"
        className={isSpread ? "photo-fan-stack is-fan-open" : "photo-fan-stack"}
        role="group"
        aria-label="Tệp ảnh vừa chụp trong phiên"
      >
        {visiblePhotos.map((item, idx) => {
          const actualIndex = startIndex + idx;
          const pose = poses[idx] ?? { tx: 0, ty: 0, rot: 0 };
          const isTopCard = idx === visibleCount - 1;
          return (
            <button
              key={item.id}
              id={`btn-photo-fan-card-${actualIndex + 1}`}
              type="button"
              className={isTopCard ? "fan-card fan-card-top" : "fan-card"}
              disabled={disabled}
              data-photo-index={actualIndex}
              aria-label={`Xem ảnh ${actualIndex + 1}`}
              style={
                {
                  "--fan-tx": `${pose.tx}px`,
                  "--fan-ty": `${pose.ty}px`,
                  "--fan-rot": `${pose.rot}deg`,
                  zIndex: idx + 1,
                } as React.CSSProperties
              }
              onClick={() => {
                if (isMobile) {
                  onOpenMobileTray();
                } else {
                  onOpenPhoto(actualIndex);
                }
              }}
            >
              <img src={item.thumbUrl} alt={`Ảnh đề ${actualIndex + 1}`} draggable={false} />
              <span className="fan-card-order-badge" aria-hidden="true">
                {actualIndex + 1}
              </span>
              {isTopCard && overflowCount > 0 && (
                <span
                  id="photo-fan-overflow-badge"
                  className="fan-overflow-badge"
                  aria-label={`Còn ${overflowCount} ảnh khác`}
                >
                  +{overflowCount}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
