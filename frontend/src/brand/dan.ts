/**
 * Handsome Dan artwork (Problem 10). Web-ready copies of the finished assets from hw3/branding
 * (poses cropped from the student's Bulldog Intelligence sheet; six-frame run and sniff-walk cycles).
 *
 * - Poses keep the sheet's cream background (#F6EFE4), so they are always shown on cream "medallions"/panels.
 * - The paw print and Y crest had their cream keyed out (simple two-colour shapes) for use as small icons.
 * - Animation strips are transparent, 6 equal frames, 168 px tall (2x the size used in the chat).
 */
import neutral from "../assets/brand/dan/dan_neutral.webp";
import sitting from "../assets/brand/dan/dan_sitting.webp";
import sniffing from "../assets/brand/dan/dan_sniffing.webp";
import fetching from "../assets/brand/dan/dan_fetching.webp";
import foundIt from "../assets/brand/dan/dan_found_it.webp";
import cookiePopup from "../assets/brand/dan/dan_cookie_popup.webp";
import avatar from "../assets/brand/dan/dan_avatar.webp";
import pawPrint from "../assets/brand/dan/paw_print.webp";
import yCrest from "../assets/brand/dan/y_crest.webp";
import yCookie from "../assets/brand/dan/y_cookie.webp";
import runStrip from "../assets/brand/dan/dan_run_strip.webp";
import sniffStrip from "../assets/brand/dan/dan_sniff_walk_strip.webp";

export const DAN_CREAM = "#F6EFE4";

export const danPoses = {
  neutral: { src: neutral, width: 397, height: 438 },
  sitting: { src: sitting, width: 327, height: 420 },
  sniffing: { src: sniffing, width: 527, height: 360 },
  fetching: { src: fetching, width: 387, height: 378 },
  foundIt: { src: foundIt, width: 392, height: 407 },
  cookiePopup: { src: cookiePopup, width: 430, height: 337 },
} as const;
export type DanPose = keyof typeof danPoses;

export const danIcons = { avatar, pawPrint, yCrest, yCookie };

/** Frame-by-frame cycles. Speeds match the preview chosen in hw3 (run 0.6 s, sniff-walk 1.2 s per cycle). */
export const danSprites = {
  run: { src: runStrip, frames: 6, frameWidth: 339, frameHeight: 168, cycleMs: 600, still: "fetching" as DanPose },
  sniff: { src: sniffStrip, frames: 6, frameWidth: 344, frameHeight: 168, cycleMs: 1200, still: "sniffing" as DanPose },
} as const;
export type DanSprite = keyof typeof danSprites;

/** Start downloading the animation strips (called when the chat opens) so the first animation doesn't pop in late. */
let preloaded = false;
export function preloadDanSprites(onError?: (sprite: DanSprite) => void) {
  if (preloaded) return;
  preloaded = true;
  (Object.keys(danSprites) as DanSprite[]).forEach((key) => {
    const img = new Image();
    img.onerror = () => onError?.(key);
    img.src = danSprites[key].src;
  });
}
