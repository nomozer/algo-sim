/**
 * Axo's DISPLAY identity — the one place the learner-facing product name lives (run axo-postmerge-consolidation).
 *
 * Technical names stay as they are (`algosim.*` storage keys, `AlgoSim backend`, cookie `algosim_session`, research
 * reports): they are contracts and history, not branding. Only what a learner reads goes through here.
 */
export const BRAND_NAME = "Axo";

/** Home page tab title — the same text as `frontend/index.html`'s `<title>` (chosen by the repository owner). */
export const HOME_TITLE = `${BRAND_NAME} — Mô phỏng tương tác`;

/** Browser tab title: "<page> | Axo", or the home title for the home page. */
export function pageTitle(page: string | null | undefined): string {
  return page ? `${page} | ${BRAND_NAME}` : HOME_TITLE;
}

/** Learner-facing copy that may still carry the pre-Axo name (server refusal texts, old cached envelopes). */
export function displayBrand(text: string): string {
  return text.replace(/\bAlgoSim\b/g, BRAND_NAME);
}
