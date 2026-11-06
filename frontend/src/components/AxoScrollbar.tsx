import React, { useEffect, useRef, useState, useCallback } from "react";

interface AxoScrollbarProps {
  /**
   * Target scroll container. If null or undefined, defaults to `window` (page-level).
   */
  targetRef?: React.RefObject<HTMLElement | null>;
  className?: string;
}

/**
 * AXO V2.7 — Manus-style Auto-hiding Floating Overlay Scrollbar
 *
 * Requirements fulfilled:
 * 1. Idle state: Invisible (opacity: 0), no empty white gutter, no content layout shift.
 * 2. Scrolling state: Appears right at the edge (opacity: 1), clear thumb, does not push or shrink content.
 * 3. Idle after scrolling: Smoothly fades out (transition 0.3s) after 800ms debounce.
 * 4. Dragging state: Dragging thumb scrolls smoothly; does not auto-hide while dragging; ends cleanly without jump.
 * 5. Respects `prefers-reduced-motion` (instant opacity without transition).
 * 6. Preserves 100% native scrolling (mouse wheel, touch, keyboard arrow keys, PageUp/PageDown, Space).
 */
export function AxoScrollbar({ targetRef, className = "" }: AxoScrollbarProps) {
  const [visible, setVisible] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [thumbHeight, setThumbHeight] = useState(36);
  const [thumbTop, setThumbTop] = useState(0);
  const [canScroll, setCanScroll] = useState(false);

  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dragStartRef = useRef<{ startY: number; startScrollTop: number } | null>(null);
  const isDraggingRef = useRef(false);

  const getScrollMetrics = useCallback(() => {
    if (targetRef && targetRef.current) {
      const el = targetRef.current;
      return {
        scrollTop: el.scrollTop,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
      };
    }
    const doc = document.documentElement;
    return {
      scrollTop: window.scrollY || doc.scrollTop,
      scrollHeight: doc.scrollHeight,
      clientHeight: window.innerHeight || doc.clientHeight,
    };
  }, [targetRef]);

  const updateThumb = useCallback(() => {
    const { scrollTop, scrollHeight, clientHeight } = getScrollMetrics();
    const isScrollable = scrollHeight > clientHeight + 2;
    setCanScroll(isScrollable);

    if (!isScrollable) {
      return;
    }

    const minThumbH = 36;
    const computedHeight = Math.max(minThumbH, (clientHeight / scrollHeight) * clientHeight);
    const maxScroll = scrollHeight - clientHeight;
    const maxThumbTop = clientHeight - computedHeight;
    const computedTop = maxScroll > 0 ? (scrollTop / maxScroll) * maxThumbTop : 0;

    setThumbHeight(Math.round(computedHeight));
    setThumbTop(Math.round(computedTop));
  }, [getScrollMetrics]);

  const showThumb = useCallback(() => {
    updateThumb();
    setVisible(true);

    if (hideTimerRef.current) {
      clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }

    if (!isDraggingRef.current) {
      hideTimerRef.current = setTimeout(() => {
        setVisible(false);
      }, 800);
    }
  }, [updateThumb]);

  // Scroll and resize listener
  useEffect(() => {
    const isWindow = !targetRef || !targetRef.current;
    const scrollTarget = isWindow ? window : targetRef?.current;
    if (!scrollTarget) return;

    updateThumb();

    const handleScroll = () => {
      showThumb();
    };

    const handleResize = () => {
      updateThumb();
    };

    scrollTarget.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", handleResize);

    // ResizeObserver for dynamic container contents
    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(() => {
        updateThumb();
      });
      if (isWindow && document.body) {
        ro.observe(document.body);
      } else if (targetRef?.current) {
        ro.observe(targetRef.current);
      }
    }

    return () => {
      scrollTarget.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
      if (ro) ro.disconnect();
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    };
  }, [targetRef, showThumb, updateThumb]);

  // Thumb drag handling
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const { scrollTop } = getScrollMetrics();
    dragStartRef.current = {
      startY: e.clientY,
      startScrollTop: scrollTop,
    };
    isDraggingRef.current = true;
    setDragging(true);
    setVisible(true);

    if (hideTimerRef.current) {
      clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }

    const onMouseMove = (ev: MouseEvent) => {
      if (!dragStartRef.current) return;
      const deltaY = ev.clientY - dragStartRef.current.startY;
      const { scrollHeight, clientHeight } = getScrollMetrics();
      const minThumbH = 36;
      const computedHeight = Math.max(minThumbH, (clientHeight / scrollHeight) * clientHeight);
      const maxThumbTop = clientHeight - computedHeight;
      const maxScroll = scrollHeight - clientHeight;

      if (maxThumbTop > 0) {
        const scrollDelta = (deltaY / maxThumbTop) * maxScroll;
        const newScrollTop = Math.max(0, Math.min(maxScroll, dragStartRef.current.startScrollTop + scrollDelta));

        if (targetRef && targetRef.current) {
          targetRef.current.scrollTop = newScrollTop;
        } else {
          window.scrollTo(0, newScrollTop);
        }
      }
    };

    const onMouseUp = () => {
      isDraggingRef.current = false;
      dragStartRef.current = null;
      setDragging(false);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);

      hideTimerRef.current = setTimeout(() => {
        setVisible(false);
      }, 800);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  };

  const handleMouseEnter = () => {
    if (canScroll) {
      setVisible(true);
      if (hideTimerRef.current) {
        clearTimeout(hideTimerRef.current);
        hideTimerRef.current = null;
      }
    }
  };

  const handleMouseLeave = () => {
    if (!isDraggingRef.current && canScroll) {
      hideTimerRef.current = setTimeout(() => {
        setVisible(false);
      }, 800);
    }
  };

  if (!canScroll) {
    return null;
  }

  const isContainer = Boolean(targetRef && targetRef.current);

  return (
    <aside
      className={`axo-scrollbar-track${isContainer ? " is-container" : ""}${className ? ` ${className}` : ""}`}
      aria-hidden="true"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div
        className={`axo-scrollbar-thumb${visible ? " is-visible" : ""}${dragging ? " is-dragging" : ""}`}
        style={{
          height: `${thumbHeight}px`,
          transform: `translateY(${thumbTop}px)`,
        }}
        onMouseDown={handleMouseDown}
        role="scrollbar"
        aria-valuenow={thumbTop}
        aria-orientation="vertical"
      />
    </aside>
  );
}
