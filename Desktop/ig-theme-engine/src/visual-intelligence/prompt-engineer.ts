// Prompt Engineer — Transforms raw visual descriptions into model-optimized photographic prompts
import type { ImageModel, VisualBrief, VisualPlan } from './types.js';
import { getStyleAnchor, getSegmentStyle } from './knowledge/style-anchors.js';
import { LENS_TYPES, LIGHTING, DEPTH_OF_FIELD, COLOR_PALETTES, FILM_STOCKS } from './knowledge/photography-vocabulary.js';
import { MODEL_RULES } from './knowledge/model-rules.js';
import { getDb } from '../database/db.js';

/**
 * Build a model-optimized prompt from a VisualPlan returned by the Creative Director.
 * This adds the style anchors, negative prompt, and segment-specific style.
 */
export function buildFinalPrompt(
  plan: VisualPlan,
  brief: VisualBrief
): { prompt: string; negativePrompt: string } {
  const anchor = getStyleAnchor();
  const segmentStyle = getSegmentStyle(brief.segmentType);

  // The Creative Director already rewrote the prompt in photographic language.
  // We enhance it with style prefix/suffix and segment mood.
  let prompt = plan.prompt;

  // Prepend style prefix if not already included
  if (anchor.imageStylePrefix && !prompt.includes(anchor.imageStylePrefix.slice(0, 30))) {
    prompt = `${anchor.imageStylePrefix}, ${prompt}`;
  }

  // Add segment-specific style
  if (segmentStyle && !prompt.includes(segmentStyle.slice(0, 20))) {
    prompt = `${prompt}, ${segmentStyle}`;
  }

  // Append style suffix
  if (anchor.imageStyleSuffix) {
    prompt = `${prompt}, ${anchor.imageStyleSuffix}`;
  }

  // Build negative prompt
  let negativePrompt = plan.negativePrompt || '';
  if (anchor.imageNegativePrompt) {
    negativePrompt = negativePrompt
      ? `${negativePrompt}, ${anchor.imageNegativePrompt}`
      : anchor.imageNegativePrompt;
  }

  return { prompt, negativePrompt };
}

/**
 * Build the video motion prompt from the Creative Director's plan.
 */
export function buildVideoPrompt(plan: VisualPlan): string {
  const anchor = getStyleAnchor();
  let motionPrompt = plan.videoPrompt || 'gentle organic motion, smooth cinematic 24fps';

  if (anchor.videoMotionStyle && !motionPrompt.includes(anchor.videoMotionStyle.slice(0, 20))) {
    motionPrompt = `${motionPrompt}, ${anchor.videoMotionStyle}`;
  }

  return motionPrompt;
}

/**
 * Get top-performing prompt patterns from the quality log for a given model.
 * Used by the Creative Director as context for better decisions.
 */
export function getTopPromptPatterns(model: string, limit: number = 10): { prompt: string; score: number }[] {
  try {
    const db = getDb();
    const rows = db.prepare(`
      SELECT prompt, quality_score as score
      FROM visual_quality_log
      WHERE model = ? AND quality_score >= 8
      ORDER BY quality_score DESC, created_at DESC
      LIMIT ?
    `).all(model, limit) as { prompt: string; score: number }[];
    return rows;
  } catch {
    return [];
  }
}

/**
 * Get worst-performing prompt patterns to avoid.
 */
export function getWorstPromptPatterns(model: string, limit: number = 10): { prompt: string; score: number; issues: string }[] {
  try {
    const db = getDb();
    const rows = db.prepare(`
      SELECT prompt, quality_score as score, issues
      FROM visual_quality_log
      WHERE model = ? AND quality_score <= 4
      ORDER BY quality_score ASC, created_at DESC
      LIMIT ?
    `).all(model, limit) as { prompt: string; score: number; issues: string }[];
    return rows;
  } catch {
    return [];
  }
}

/**
 * Get average quality score per model for performance tracking.
 */
export function getModelPerformanceStats(): { model: string; avgScore: number; totalGenerations: number }[] {
  try {
    const db = getDb();
    return db.prepare(`
      SELECT model, ROUND(AVG(quality_score), 1) as avgScore, COUNT(*) as totalGenerations
      FROM visual_quality_log
      GROUP BY model
      ORDER BY avgScore DESC
    `).all() as { model: string; avgScore: number; totalGenerations: number }[];
  } catch {
    return [];
  }
}

/**
 * Get the universal and model-specific rules as a formatted string for the Creative Director prompt.
 */
export function getRulesForModel(model: ImageModel): string {
  const universal = MODEL_RULES.universal;
  const specific = MODEL_RULES[model] || { additional: [] };

  let rules = 'ABSOLUTE RULES:\n';
  for (const rule of universal.never) rules += `- ${rule}\n`;
  rules += '\nALWAYS:\n';
  for (const rule of universal.always) rules += `- ${rule}\n`;
  rules += `\n${model.toUpperCase()} TIPS:\n`;
  for (const tip of specific.additional) rules += `- ${tip}\n`;

  return rules;
}
