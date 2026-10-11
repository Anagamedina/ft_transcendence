// useAutoRefresh — runs `callback` every `intervalMs` while the tab is visible.
//
// Paused while the tab is hidden (no requests nobody will see) and run once
// as soon as it is visible again, so the data is not stale on return.
// Stops on unmount. If WebSockets arrive later, they replace this.

import { onMounted, onBeforeUnmount } from 'vue'

export function useAutoRefresh(callback, intervalMs = 30000) {
  let timer = null

  function start() {
    stop()
    timer = setInterval(callback, intervalMs)
  }

  function stop() {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  }

  function onVisibilityChange() {
    if (document.hidden) {
      stop()
    } else {
      callback()
      start()
    }
  }

  onMounted(() => {
    if (!document.hidden) start()
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onBeforeUnmount(() => {
    stop()
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return { start, stop }
}
