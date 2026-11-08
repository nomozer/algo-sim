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
      { tx: -3.5, ty: -2.0, rot: -5.5 },
      { tx: 1.5, ty: 0, rot: 2.5 },
    ],
    open: [
      { tx: -22, ty: -26, rot: -8 },
      { tx: 14, ty: -26, rot: 8 },
    ],
  },
  3: {
    collapsed: [
      { tx: -5.5, ty: -3.0, rot: -8.0 },
      { tx: -1.5, ty: -1.5, rot: -2.0 },
      { tx: 2.5, ty: 0, rot: 4.0 },
    ],
    open: [
      { tx: -36, ty: -23, rot: -10 },
      { tx: -4, ty: -30, rot: 0 },
      { tx: 28, ty: -23, rot: 10 },
    ],
  },
  4: {
    collapsed: [
      { tx: -6.5, ty: -3.5, rot: -9.0 },
      { tx: -3.0, ty: -2.0, rot: -4.0 },
      { tx: 0.5, ty: -1.0, rot: 1.0 },
      { tx: 3.0, ty: 0, rot: 5.0 },
    ],
    open: [
      { tx: -50, ty: -21, rot: -12 },
      { tx: -20, ty: -28, rot: -4 },
      { tx: 10, ty: -28, rot: 4 },
      { tx: 40, ty: -21, rot: 12 },
    ],
  },
  5: {
    collapsed: [
      { tx: -7.5, ty: -4.0, rot: -10.0 },
      { tx: -4.5, ty: -3.0, rot: -6.0 },
      { tx: -1.5, ty: -2.0, rot: -2.0 },
      { tx: 1.0, ty: -1.0, rot: 2.0 },
      { tx: 3.5, ty: 0, rot: 5.5 },
    ],
    open: [
      { tx: -64, ty: -19, rot: -13 },
      { tx: -35, ty: -26, rot: -6.5 },
      { tx: -6, ty: -31, rot: 0 },
      { tx: 23, ty: -26, rot: 6.5 },
      { tx: 52, ty: -19, rot: 13 },
    ],
  },
};

export const MOBILE_STACK_POSES: Record<number, FanPose[]> = {
  1: [{ tx: 0, ty: 0, rot: 0 }],
  2: [
    { tx: -4.0, ty: -2.0, rot: -6.0 },
    { tx: 2.0, ty: 0, rot: 3.0 },
  ],
  3: [
    { tx: -6.0, ty: -3.0, rot: -8.0 },
    { tx: -1.5, ty: -1.5, rot: -2.0 },
    { tx: 3.0, ty: 0, rot: 4.5 },
  ],
  4: [
    { tx: -7.0, ty: -3.5, rot: -9.5 },
    { tx: -3.0, ty: -2.0, rot: -4.0 },
    { tx: 0.5, ty: -1.0, rot: 1.0 },
    { tx: 3.5, ty: 0, rot: 5.0 },
  ],
  5: [
    { tx: -8.0, ty: -4.0, rot: -10.5 },
    { tx: -4.5, ty: -3.0, rot: -6.0 },
    { tx: -1.5, ty: -2.0, rot: -2.0 },
    { tx: 1.5, ty: -1.0, rot: 2.0 },
    { tx: 4.0, ty: 0, rot: 5.5 },
  ],
};

export interface PhotoFanStackProps {
  photos: CapturedSessionPhoto[];
  isMobile: boolean;
  onOpenPhoto: (photoIndex: number) => void;
  onOpenMobileTray: () => void;
  disabled?: boolean;
  justShotPulse?: boolean;
}

export function PhotoFanStack({
  photos,
  isMobile,
  onOpenPhoto,
  onOpenMobileTray,
  disabled = false,
  justShotPulse = false,
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
        return;
      }
      if (!isMobile && photos.length > 1 && (e.key === "ArrowRight" || e.key === "ArrowLeft")) {
        const cards = Array.from(
          clusterRef.current?.querySelectorAll<HTMLButtonElement>(".fan-card") ?? [],
        );
        const currentIdx = cards.indexOf(document.activeElement as HTMLButtonElement);
        if (currentIdx !== -1 && cards.length > 1) {
          e.preventDefault();
          const nextIdx =
            e.key === "ArrowRight"
              ? (currentIdx + 1) % cards.length
              : (currentIdx - 1 + cards.length) % cards.length;
          cards[nextIdx]?.focus();
        }
      }
    },
    [clearLeaveTimer, fanOpen, isMobile, photos.length],
  );

  if (photos.length === 0) {
    return null;
  }

  const totalCount = photos.length;
  const startIndex = Math.max(0, totalCount - MAX_VISIBLE_FAN_CARDS);
  const visiblePhotos = photos.slice(startIndex);
  const visibleCount = visiblePhotos.length;

  if (totalCount === 1) {
    const single = photos[0];
    return (
      <div
        ref={clusterRef}
        id={isMobile ? "btn-photo-mobile-stack" : undefined}
        className={isMobile ? "photo-fan-cluster is-mobile" : "photo-fan-cluster"}
        data-photo-count="1"
        data-fan-open="false"
      >
        <div
          id="photo-fan-stack"
          className={
            isMobile
              ? `photo-fan-stack mobile-fan-stack-btn${justShotPulse ? " is-just-shot" : ""}`
              : `photo-fan-stack${justShotPulse ? " is-just-shot" : ""}`
          }
          data-fan-capable="false"
          data-photo-count="1"
        >
          <button
            id="btn-photo-fan-single"
            type="button"
            className={
              isMobile
                ? "fan-card fan-card-btn fan-card-single mobile-stack-card"
                : "fan-card fan-card-btn fan-card-single"
            }
            disabled={disabled}
            data-photo-index={0}
            aria-label="Xem ảnh vừa chụp (Ảnh 1)"
            style={
              {
                "--tx": "0px",
                "--ty": "0px",
                "--rot": "0deg",
                "--fan-tx": "0px",
                "--fan-ty": "0px",
                "--fan-rot": "0deg",
                "--z": 1,
                zIndex: 1,
              } as React.CSSProperties
            }
            onClick={() => {
              if (isMobile) {
                onOpenMobileTray();
              } else {
                onOpenPhoto(0);
              }
            }}
          >
            <img src={single.thumbUrl} alt="" draggable={false} />
          </button>
        </div>
      </div>
    );
  }

  const layoutSpec = FAN_LAYOUTS[visibleCount] ?? FAN_LAYOUTS[MAX_VISIBLE_FAN_CARDS];
  const mobilePoses = MOBILE_STACK_POSES[visibleCount] ?? MOBILE_STACK_POSES[MAX_VISIBLE_FAN_CARDS];
  const isSpread = !isMobile && fanOpen;
  const poses = isMobile ? mobilePoses : isSpread ? layoutSpec.open : layoutSpec.collapsed;

  return (
    <div
      ref={clusterRef}
      id={isMobile ? "btn-photo-mobile-stack" : undefined}
      className={
        isMobile
          ? "photo-fan-cluster is-mobile"
          : isSpread
            ? "photo-fan-cluster is-fan-open"
            : "photo-fan-cluster"
      }
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
        className={
          isMobile
            ? `photo-fan-stack mobile-fan-stack-btn${justShotPulse ? " is-just-shot" : ""}`
            : `photo-fan-stack${isSpread ? " is-fan-open" : ""}${justShotPulse ? " is-just-shot" : ""}`
        }
        data-fan-capable={isMobile ? "false" : "true"}
        data-photo-count={String(totalCount)}
        role="group"
        aria-label="Khay ảnh phiên chụp"
      >
        {!isMobile && (
          <>
            <span className="fan-hover-bridge-base" aria-hidden="true" />
            <span className="fan-hover-bridge-arc" aria-hidden="true" />
          </>
        )}
        {visiblePhotos.map((item, idx) => {
          const actualIndex = startIndex + idx;
          const pose = poses[idx] ?? { tx: 0, ty: 0, rot: 0 };
          const isTopCard = idx === visibleCount - 1;
          return (
            <button
              key={item.id}
              id={`btn-photo-fan-card-${actualIndex + 1}`}
              type="button"
              className={
                isMobile
                  ? `fan-card fan-card-btn mobile-stack-card${isTopCard ? " fan-card-top" : ""}`
                  : `fan-card fan-card-btn${isTopCard ? " fan-card-top" : ""}`
              }
              disabled={disabled}
              data-photo-index={actualIndex}
              aria-label={`Xem ảnh thứ ${actualIndex + 1}`}
              style={
                {
                  "--tx": `${pose.tx}px`,
                  "--ty": `${pose.ty}px`,
                  "--rot": `${pose.rot}deg`,
                  "--fan-tx": `${pose.tx}px`,
                  "--fan-ty": `${pose.ty}px`,
                  "--fan-rot": `${pose.rot}deg`,
                  "--z": idx + 1,
                  zIndex: idx + 1,
                } as React.CSSProperties
              }
              onClick={() => {
                if (isMobile) {
                  onOpenMobileTray();
                } else {
                  clearLeaveTimer();
                  setFanOpen(false);
                  onOpenPhoto(actualIndex);
                }
              }}
            >
              <img src={item.thumbUrl} alt="" draggable={false} />
            </button>
          );
        })}
      </div>
    </div>
  );
}
