/**
 * Central branding configuration.
 *
 * Problem 10 filled the mascot slots with the Handsome Dan artwork (see brand/dan.ts for every asset and how the
 * cream-background poses are handled). Components still fall back to text/CSS placeholders if a slot is null.
 */
import { danIcons, danPoses } from "./dan.ts";

export interface BrandAssets {
  /** Large illustration beside the homepage hero text (shown inside a cream medallion). */
  hero: string | null;
  /** Small avatar shown in the chat widget header, launcher, and on assistant messages. */
  chatAvatar: string | null;
  /** Logo mark beside the wordmark in the header and footer. */
  logoMark: string | null;
}

export const brand = {
  name: "Campus Customs",
  tagline: "Yale-inspired apparel for students, alumni and fans.",
  assistantName: "Handsome Dan",
  assistantRole: "Campus Customs shopping assistant",
  mascotName: "Handsome Dan",
  mascot: {
    hero: danPoses.sitting.src,
    chatAvatar: danIcons.avatar,
    // The "CC" monogram stays as the logo: Dan is the store's personality, not its logo.
    logoMark: null,
  } satisfies BrandAssets as BrandAssets,
};
