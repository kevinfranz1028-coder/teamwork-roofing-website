import type { VisualBrief, VisualPlan, ImageModel } from './types.js';
import { SEGMENT_STYLE_HINTS, CONTENT_TYPE_HINTS } from './knowledge/prompt-templates.js';
import { getStyleAnchor } from './knowledge/style-anchors.js';

/**
 * Build the full photographic prompt for an image generation model.
 * Combines the Creative Director's plan with style anchors and model-specific formatting.
 */
export function buildFinalPrompt(plan: VisualPlan, brief: VisualBrief): string {
  const anchor = getStyleAnchor();
  const parts: string[] = [];

  // Model-specific style prefix
  if (plan.model === 'flux-2-pro') {
    parts.push(anchor.imageStylePrefix);
  } else if (plan.model === 'gpt-image-1.5') {
    parts.push('Professional photorealistic photography');
  } else if (plan.model === 'ideogram-3') {
    parts.push('Professional graphic design layout');
  }

  // Core scene description from Creative Director
  parts.push(plan.prompt);

  // Technical photography details
  if (plan.lens) parts.push(plan.lens);
  if (plan.lighting) parts.push(plan.lighting);
  if (plan.depthOfField) parts.push(plan.depthOfField);
  if (plan.colorPalette) parts.push(plan.colorPalette);

  // Segment style hint
  const segHint = SEGMENT_STYLE_HINTS[brief.segmentType];
  if (segHint) parts.push(segHint);

  // Model-specific suffix
  if (plan.model === 'flux-2-pro') {
    parts.push(`shot on ${anchor.cameraBody}, ${anchor.defaultColorProfile}`);
  }

  return parts.filter(Boolean).join('. ');
}

/**
 * Build a negative prompt string.
 */
export function buildNegativePrompt(plan: VisualPlan): string {
  const anchor = getStyleAnchor();
  const base = anchor.imageNegativePrompt;
  if (plan.negativePrompt && plan.negativePrompt !== base) {
    return `${base}, ${plan.negativePrompt}`;
  }
  return base;
}

/**
 * Build a motion prompt for video generation from an image.
 */
export function buildMotionPrompt(plan: VisualPlan, brief: VisualBrief): string {
  const anchor = getStyleAnchor();

  if (plan.motionPrompt) return plan.motionPrompt;

  const segmentMotion: Record<string, string> = {
    hook: 'slow dramatic push-in zoom toward subject, increasing tension, slight parallax depth shift',
    body: 'gentle lateral drift with subtle focus breathing, natural ambient movement like leaves swaying',
    cta: 'slow pull-back reveal with warm light intensifying, hopeful upward tilt',
  };

  const motion = segmentMotion[brief.segmentType] || anchor.videoMotionStyle;
  return `${motion}. Photorealistic cinematic motion, 24fps, no morphing or warping of subject.`;
}
