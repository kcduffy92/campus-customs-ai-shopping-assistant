import { useEffect, useState, type CSSProperties, type SyntheticEvent } from "react";
import { danPoses, danSprites, type DanPose, type DanSprite } from "../brand/dan.ts";

/** True when the shopper's system asks for reduced motion (kept in sync if the setting changes). */
export function usePrefersReducedMotion(): boolean {
  const query = "(prefers-reduced-motion: reduce)";
  const [reduced, setReduced] = useState(() => typeof window !== "undefined" && window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const update = () => setReduced(mq.matches);
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return reduced;
}

/** onError for small decorative Dan icons (paw, crest, cookie): hide a failed image instead of showing a broken icon. */
export function hideBrokenImage(e: SyntheticEvent<HTMLImageElement>) {
  e.currentTarget.style.display = "none";
}

interface PoseProps {
  pose: DanPose;
  /** Rendered height in CSS pixels. Never larger than the artwork's own height, so Dan is never blurry. */
  height: number;
  className?: string;
  /** Decorative by default (the text next to Dan carries the meaning). */
  alt?: string;
  /** Load immediately (above-the-fold art such as the homepage hero) instead of lazily. */
  eager?: boolean;
}

/** A single Handsome Dan pose. If the image fails to load it simply disappears; nothing else depends on it. */
export function DanPoseImage({ pose, height, className = "", alt = "", eager = false }: PoseProps) {
  const [failed, setFailed] = useState(false);
  const art = danPoses[pose];
  const h = Math.min(height, art.height);
  if (failed) return null;
  return (
    <img
      className={`dan-pose ${className}`}
      src={art.src}
      alt={alt}
      width={Math.round((art.width * h) / art.height)}
      height={h}
      loading={eager ? "eager" : "lazy"}
      decoding="async"
      draggable={false}
      onError={() => setFailed(true)}
    />
  );
}

/**
 * A round cream "medallion" holding a pose. The poses keep the sheet's cream background, so placing them on a
 * matching cream disc (with a thin gold ring) avoids hard rectangles on Yale-blue or white backgrounds.
 */
export function DanMedallion({ pose, size, className = "", alt = "" }: { pose: DanPose; size: number; className?: string; alt?: string }) {
  return (
    <span className={`dan-medallion ${className}`} style={{ width: size, height: size }}>
      <DanPoseImage pose={pose} height={Math.round(size * 0.82)} alt={alt} />
    </span>
  );
}

/** Strips that already failed this session, so later activity changes go straight to the still pose. */
const failedStrips = new Set<string>();

interface SpriteProps {
  sprite: DanSprite;
  height: number;
  className?: string;
  /** Set when the sprite strip failed to preload: show the matching still pose instead. */
  stripFailed?: boolean;
}

/**
 * Frame-by-frame animation from a 6-frame strip (CSS steps()). With reduced motion, or if the strip failed to load,
 * the matching still pose is shown instead (sniff-walk -> sniffing, run -> fetching).
 */
export function DanAnimation({ sprite, height, className = "", stripFailed = false }: SpriteProps) {
  const reduced = usePrefersReducedMotion();
  const s = danSprites[sprite];
  const [loadFailed, setLoadFailed] = useState(() => failedStrips.has(s.src));
  useEffect(() => {
    // A CSS background image fails silently, so check the strip once and fall back to the still pose if it's missing.
    if (failedStrips.has(s.src)) return;
    const probe = new Image();
    probe.onerror = () => {
      failedStrips.add(s.src);
      setLoadFailed(true);
    };
    probe.src = s.src;
  }, [s.src]);
  if (reduced || stripFailed || loadFailed) {
    return <DanPoseImage pose={s.still} height={height} className={`dan-still ${className}`} />;
  }
  const width = Math.round((s.frameWidth * height) / s.frameHeight);
  const style = {
    "--dan-w": `${width}px`,
    "--dan-h": `${height}px`,
    "--dan-frames": s.frames,
    "--dan-cycle": `${s.cycleMs}ms`,
    backgroundImage: `url(${s.src})`,
  } as CSSProperties;
  return <span className={`dan-sprite ${className}`} style={style} aria-hidden="true" />;
}


export type DanActivityMode = "idle" | "sniff" | "run";

/**
 * Map a REAL progress stage from the backend (Problem 9 status events) to what Dan is doing. Nothing is inferred:
 * - "searching" / "inventory": search_products or check_inventory is actually running -> sniff-walking.
 * - "reviewing": a tool has finished and the answer is being prepared from its results -> running ("fetching").
 * - "thinking" or no event yet: the model is deciding / replying, no tool running -> neutral Dan, standing.
 */
export function danModeForStage(stage: string | undefined | null): DanActivityMode {
  if (stage === "searching" || stage === "inventory") return "sniff";
  if (stage === "reviewing") return "run";
  return "idle";
}

/**
 * Dan inside the "assistant is working" bubble. Keyed by mode, so the animation only (re)starts when the activity
 * actually changes (two inventory events in a row keep the same sniff-walk running), and each change eases in.
 */
export function DanActivity({ mode, height = 64 }: { mode: DanActivityMode; height?: number }) {
  return (
    <span className="dan-activity" data-mode={mode} key={mode} aria-hidden="true">
      {mode === "sniff" ? (
        <DanAnimation sprite="sniff" height={height} />
      ) : mode === "run" ? (
        <DanAnimation sprite="run" height={height} />
      ) : (
        // Still poses have a cream background, so the idle Dan sits in a small cream medallion.
        <DanMedallion pose="neutral" size={Math.round(height * 0.9)} className="dan-activity__idle" />
      )}
    </span>
  );
}

/**
 * The celebratory moment: cookie pop-up Dan with how many products were found. Shown only under a LIVE reply that
 * came back with product cards (never for restored history or small talk). Pops in once, then stays still.
 */
export function DanFoundIt({ count }: { count: number }) {
  return (
    <div className="dan-found" role="status">
      <span className="dan-found__art">
        <DanPoseImage pose="cookiePopup" height={52} />
      </span>
      <span className="dan-found__text">
        Fetched {count} {count === 1 ? "style" : "styles"} for you
      </span>
    </div>
  );
}