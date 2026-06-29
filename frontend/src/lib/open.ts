import { openUrl, openPath } from "@tauri-apps/plugin-opener";

/**
 * Open a URL in the user's default browser.
 *
 * A plain <a target="_blank"> does nothing inside the Tauri WebView, so external
 * links must go through the opener plugin. Falls back to window.open when running
 * in a normal browser (dev).
 */
export async function openExternal(url: string): Promise<void> {
  try {
    await openUrl(url);
  } catch {
    try {
      window.open(url, "_blank", "noopener,noreferrer");
    } catch {
      /* nothing else we can do */
    }
  }
}

/** Open a local file (e.g. a saved report) with the system's default app. */
export async function openLocalFile(path: string): Promise<void> {
  try {
    await openPath(path);
  } catch {
    /* nothing else we can do */
  }
}
