// Brand-specific style anchors loaded from AI Settings with intelligent defaults
import type { StyleAnchor } from '../types.js';
import { getActiveAISettings } from '../../config/ai-settings.js';

const DEFAULT_STYLE_ANCHOR: StyleAnchor = {
  imageStylePrefix: 'Professional macro plant photography, Canon R5, 100mm f/2.8 macro lens, natural window light, shallow depth of field, editorial quality, Kodak Portra 400 color profile',
  imageStyleSuffix: 'rich greens and warm earth tones, clean composition, Instagram-ready, high resolution',
  imageNegativePrompt: 'text, words, letters, numbers, labels, logos, watermarks, clocks, watches, timers, collage, split screen, multiple panels, black bars, borders, frames, UI elements, buttons, cartoon, illustration, anime, low quality, blurry, distorted',
  videoMotionStyle: 'gentle organic motion, leaves subtly swaying, soft focus shifts, natural light breathing, cinematic 24fps, smooth dolly-in',
  hookVisualStyle: 'dramatic macro, extreme close-up, high contrast, rich texture detail, scroll-stopping impact',
  bodyVisualStyle: 'clear well-lit subject, moderate close-up, informative angle, clean background',
  ctaVisualStyle: 'warm soft light, hopeful mood, thriving healthy plant, inviting atmosphere',
};

export function getStyleAnchor(): StyleAnchor {
  const settings = getActiveAISettings();
  if (!settings) return DEFAULT_STYLE_ANCHOR;

  return {
    imageStylePrefix: settings.image_style_prefix || DEFAULT_STYLE_ANCHOR.imageStylePrefix,
    imageStyleSuffix: settings.image_style_suffix || DEFAULT_STYLE_ANCHOR.imageStyleSuffix,
    imageNegativePrompt: settings.image_negative_prompt || DEFAULT_STYLE_ANCHOR.imageNegativePrompt,
    videoMotionStyle: (settings as any).video_motion_style || DEFAULT_STYLE_ANCHOR.videoMotionStyle,
    hookVisualStyle: (settings as any).hook_visual_style || DEFAULT_STYLE_ANCHOR.hookVisualStyle,
    bodyVisualStyle: (settings as any).body_visual_style || DEFAULT_STYLE_ANCHOR.bodyVisualStyle,
    ctaVisualStyle: (settings as any).cta_visual_style || DEFAULT_STYLE_ANCHOR.ctaVisualStyle,
  };
}

export function getSegmentStyle(segmentType: 'hook' | 'body' | 'cta'): string {
  const anchor = getStyleAnchor();
  switch (segmentType) {
    case 'hook': return anchor.hookVisualStyle;
    case 'body': return anchor.bodyVisualStyle;
    case 'cta': return anchor.ctaVisualStyle;
    default: return anchor.bodyVisualStyle;
  }
}
