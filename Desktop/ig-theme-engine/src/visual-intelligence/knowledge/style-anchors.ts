import type { StyleAnchor } from '../types.js';
import { getActiveAISettings } from '../../config/ai-settings.js';

const DEFAULT_ANCHOR: StyleAnchor = {
  imageStylePrefix: 'Professional macro plant photography, Canon R5, 100mm f/2.8L Macro IS, natural window light, shallow depth of field, editorial quality, Kodak Portra 400 color science',
  imageNegativePrompt: 'text, words, letters, numbers, labels, logos, watermarks, clocks, watches, timers, collage, split screen, multiple panels, black bars, UI elements, cartoon, illustration, low quality, blurry, deformed',
  videoMotionStyle: 'gentle organic motion, leaves subtly swaying, soft focus shift, natural light breathing, cinematic 24fps',
  hookVisualStyle: 'dramatic macro, extreme close-up, high contrast, scroll-stopping, shallow depth of field',
  bodyVisualStyle: 'clear well-lit subject, moderate close-up, informative angle, clean composition',
  ctaVisualStyle: 'warm golden light, hopeful mood, thriving healthy plant, soft bokeh background',
  cameraBody: 'Canon R5',
  defaultLens: '100mm f/2.8L Macro IS',
  defaultLighting: 'soft north-facing window light with warm fill',
  defaultColorProfile: 'Kodak Portra 400',
};

export function getStyleAnchor(): StyleAnchor {
  const settings = getActiveAISettings() as any;
  if (!settings) return DEFAULT_ANCHOR;

  return {
    imageStylePrefix: settings.image_style_prefix || DEFAULT_ANCHOR.imageStylePrefix,
    imageNegativePrompt: settings.image_negative_prompt || DEFAULT_ANCHOR.imageNegativePrompt,
    videoMotionStyle: settings.video_motion_style || DEFAULT_ANCHOR.videoMotionStyle,
    hookVisualStyle: settings.hook_visual_style || DEFAULT_ANCHOR.hookVisualStyle,
    bodyVisualStyle: settings.body_visual_style || DEFAULT_ANCHOR.bodyVisualStyle,
    ctaVisualStyle: settings.cta_visual_style || DEFAULT_ANCHOR.ctaVisualStyle,
    cameraBody: settings.camera_body || DEFAULT_ANCHOR.cameraBody,
    defaultLens: settings.default_lens || DEFAULT_ANCHOR.defaultLens,
    defaultLighting: settings.default_lighting || DEFAULT_ANCHOR.defaultLighting,
    defaultColorProfile: settings.default_color_profile || DEFAULT_ANCHOR.defaultColorProfile,
  };
}
