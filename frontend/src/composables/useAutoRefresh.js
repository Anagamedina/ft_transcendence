// useAutoRefresh — runs `callback` every `intervalMs` while the tab is visible.
//
// Paused while the tab is hidden (no requests nobody will see) and run once
// as soon as it is visible again, so the data is not stale on return.
// Stops on unmount. If WebSockets arrive later, they replace this.
//
// REFRESH_MS (F30): the one refresh pace of the app. Every screen that shows
// sensors or alerts imports it, so admin and client change at the same rate
// and the pace is changed in this line only. Not an env variable: Vite fixes
// it at build time and it does not vary between environments.

import { onMounted, onBeforeUnmount } from "vue";

export const REFRESH_MS = 30_000;

export function useAutoRefresh(callback, intervalMs = REFRESH_MS) {
  let timer = null;

  function start() {
    stop();
    timer = setInterval(callback, intervalMs);
  }

  function stop() {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  }

  function onVisibilityChange() {
    if (document.hidden) {
      stop();
    } else {
      callback();
      start();
    }
  }

  onMounted(() => {
    if (!document.hidden) start();
    document.addEventListener("visibilitychange", onVisibilityChange);
  });

  onBeforeUnmount(() => {
    stop();
    document.removeEventListener("visibilitychange", onVisibilityChange);
  });

  return { start, stop };
}
