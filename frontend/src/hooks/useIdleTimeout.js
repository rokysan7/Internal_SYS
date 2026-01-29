import { useEffect, useRef, useCallback } from 'react';

const IDLE_EVENTS = [
  'mousemove',
  'keydown',
  'click',
  'scroll',
  'touchstart',
];

/**
 * Hook to detect user inactivity and trigger a callback after timeout
 * @param {Function} onIdle - Callback function when idle timeout is reached
 * @param {number} timeout - Timeout in milliseconds (default: 60 minutes)
 * @param {boolean} enabled - Whether the idle detection is enabled
 */
export default function useIdleTimeout(onIdle, timeout = 60 * 60 * 1000, enabled = true) {
  const timerRef = useRef(null);
  const onIdleRef = useRef(onIdle);

  // Keep callback reference updated
  useEffect(() => {
    onIdleRef.current = onIdle;
  }, [onIdle]);

  const resetTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    if (enabled) {
      timerRef.current = setTimeout(() => {
        onIdleRef.current?.();
      }, timeout);
    }
  }, [timeout, enabled]);

  useEffect(() => {
    if (!enabled) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    // Start initial timer
    resetTimer();

    // Add event listeners
    IDLE_EVENTS.forEach((event) => {
      window.addEventListener(event, resetTimer, { passive: true });
    });

    // Cleanup
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      IDLE_EVENTS.forEach((event) => {
        window.removeEventListener(event, resetTimer);
      });
    };
  }, [resetTimer, enabled]);

  return { resetTimer };
}
