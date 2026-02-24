// Creative Director — Claude-powered AI brain that plans all visual generation
import type { VisualBrief, VisualPlan } from './types.js';
import { askClaudeJSON } from '../integrations/claude-client.js';
import { getTopPromptPatterns, getWorstPromptPatterns, getRulesForModel } from './prompt-engineer.js';
import { MODEL_REGISTRY } from './models/model-registry.js';
import { getStyleAnchor } from './knowledge/style-anchors.js';

const CREATIVE_DIRECTOR_SYSTEM = `You are the Creative Director for an Instagram content engine. Your job is to transform content script descriptions into production-ready visual generation instructions.

You have access to three image models and one video model:

IMAGE MODELS:
1. FLUX 2 Pro — Best for: photorealistic nature/plant photography, atmospheric scenes, macro close-ups, moody lighting. Weakness: text rendering is improved but not perfect. Cost: ~$0.03/megapixel. Speed: 6 seconds. Use this as DEFAULT for plant content.

2. GPT Image 1.5 — Best for: scenes requiring readable text, product photography with labels, infographic-style images, complex multi-element compositions. Weakness: slightly less "cinematic" than FLUX. Cost: $0.04-$0.08. Speed: 8-15 seconds. Use when TEXT MUST appear in the image OR when composition is very complex.

3. Ideogram 3.0 — Best for: typography-heavy designs, poster-style layouts, images where text IS the design element. Weakness: general photorealism not as strong. Cost: ~$0.05. Speed: 10 seconds. Use ONLY for typography-first designs.

VIDEO MODEL:
4. Kling 2.6 Pro (image-to-video) — Transforms a still image into 5-10 seconds of cinematic video with natural motion. Best for: bringing plant scenes to life (leaves swaying, water droplets, insects moving, light shifting). Cost: $0.07/sec without audio. Use for ALL reel segments.

ABSOLUTE RULES:
- NEVER include text, words, letters, numbers, labels, logos, or watermarks in image prompts
- NEVER ask for clocks, timers, watches, or time-display devices
- NEVER ask for product packaging with brand names
- NEVER ask for collages, split-screens, or multi-panel compositions
- NEVER ask for UI elements, buttons, or interface mockups
- ALL text goes in the HTML overlay layer, NEVER in the generated image
- Every image prompt MUST describe a SINGLE cohesive scene from ONE camera angle
- Every prompt MUST include: focal length, lighting direction, depth of field, color palette

PHOTOGRAPHIC LANGUAGE REQUIREMENTS:
Every image prompt must read like a professional photographer's shot list. Include:
- Camera/lens: "Canon R5, 100mm f/2.8 macro" or "Sony A7R V, 35mm f/1.4"
- Lighting: "soft north-facing window light" or "golden hour backlight" or "overcast diffused"
- Depth of field: "shallow focus, f/2.8 bokeh" or "deep focus, f/11"
- Color: "warm earth tones" or "cool blue-green palette" or "high contrast"
- Texture: describe surfaces specifically ("wet soil granules", "fuzzy leaf trichomes")
- Mood: "intimate", "dramatic", "clinical", "warm and inviting"

OUTPUT FORMAT:
For each visual element, return a JSON object:
{
  "model": "flux-2-pro" | "gpt-image-1.5" | "ideogram-3",
  "prompt": "the rewritten photographic prompt",
  "negative_prompt": "things to avoid",
  "aspect_ratio": "9:16" | "1:1" | "16:9",
  "generate_video": true | false,
  "video_prompt": "motion description for Kling (if generate_video is true)",
  "video_duration": 5 | 10,
  "rationale": "brief explanation of model choice and prompt strategy"
}`;

/**
 * Plan visuals for a single content segment.
 */
export async function planVisuals(brief: VisualBrief): Promise<VisualPlan> {
  const plans = await planVisualsBatch([brief]);
  return plans[0];
}

/**
 * Plan visuals for a batch of segments (carousel slides, reel segments, etc).
 * Sending them all at once lets Claude ensure visual CONSISTENCY across the set.
 */
export async function planVisualsBatch(briefs: VisualBrief[]): Promise<VisualPlan[]> {
  const anchor = getStyleAnchor();

  // Build context about what's worked/failed before
  const defaultModel = briefs[0]?.brandContext?.stylePrefix ? 'flux-2-pro' : 'flux-2-pro';
  const topPatterns = getTopPromptPatterns(defaultModel, 5);
  const worstPatterns = getWorstPromptPatterns(defaultModel, 5);

  let learningContext = '';
  if (topPatterns.length > 0) {
    learningContext += '\n\nHIGH-SCORING PROMPTS (use similar patterns):\n';
    for (const p of topPatterns) {
      learningContext += `- Score ${p.score}: "${p.prompt.slice(0, 150)}..."\n`;
    }
  }
  if (worstPatterns.length > 0) {
    learningContext += '\nLOW-SCORING PROMPTS (avoid these patterns):\n';
    for (const p of worstPatterns) {
      learningContext += `- Score ${p.score}: "${p.prompt.slice(0, 150)}..." Issues: ${p.issues}\n`;
    }
  }

  const enableVideo = process.env.ENABLE_VIDEO_GENERATION !== 'false';
  const contentType = briefs[0]?.contentType || 'carousel';

  const userPrompt = `Plan visuals for this ${contentType} (${briefs.length} segments).

BRAND STYLE:
- Style prefix: ${anchor.imageStylePrefix}
- Style suffix: ${anchor.imageStyleSuffix}
- Video motion: ${anchor.videoMotionStyle}
- Hook style: ${anchor.hookVisualStyle}
- Body style: ${anchor.bodyVisualStyle}
- CTA style: ${anchor.ctaVisualStyle}

VIDEO GENERATION: ${enableVideo ? 'ENABLED — generate video for reel segments' : 'DISABLED — stills only'}
${learningContext}

SEGMENTS TO PLAN:
${JSON.stringify(briefs.map((b, i) => ({
  index: i,
  type: b.segmentType,
  text: b.onScreenText,
  voiceover: b.voiceoverText || '',
  visual: b.originalVisualDescription,
})), null, 2)}

Return a JSON array of ${briefs.length} visual plans, one per segment, in the same order. Ensure visual consistency across all segments (similar color grading, lighting style, camera perspective).`;

  const result = await askClaudeJSON<VisualPlan[] | { plans: VisualPlan[] }>({
    systemPrompt: CREATIVE_DIRECTOR_SYSTEM,
    userPrompt,
    maxTokens: 4096,
    temperature: 0.4,
  });

  // Handle both array and wrapped formats
  const plans: any[] = Array.isArray(result) ? result : (result as any).plans || [];

  // Map to typed VisualPlan objects with sensible defaults
  return briefs.map((brief, i) => {
    const raw = plans[i] || {};
    return {
      model: raw.model || 'flux-2-pro',
      prompt: raw.prompt || brief.originalVisualDescription,
      negativePrompt: raw.negative_prompt || raw.negativePrompt || '',
      aspectRatio: raw.aspect_ratio || raw.aspectRatio || (brief.contentType === 'carousel' ? '1:1' : '9:16'),
      generateVideo: enableVideo && brief.contentType === 'reel' ? (raw.generate_video ?? raw.generateVideo ?? true) : false,
      videoPrompt: raw.video_prompt || raw.videoPrompt || undefined,
      videoDuration: raw.video_duration || raw.videoDuration || 5,
      rationale: raw.rationale || '',
    };
  });
}

/**
 * Retry with adjusted prompt after a quality gate failure.
 * Returns a new VisualPlan with refined prompt.
 */
export async function retryPlan(
  failedPlan: VisualPlan,
  qualityFeedback: string,
  brief: VisualBrief
): Promise<VisualPlan> {
  const userPrompt = `A previous image generation FAILED the quality gate.

FAILED PROMPT: "${failedPlan.prompt}"
MODEL USED: ${failedPlan.model}
QUALITY FEEDBACK: "${qualityFeedback}"

Original visual brief:
- Content type: ${brief.contentType}
- Segment type: ${brief.segmentType}
- On-screen text: "${brief.onScreenText}"
- Original description: "${brief.originalVisualDescription}"

Please generate a REVISED visual plan that addresses the quality feedback. You may switch models if appropriate.

Return a single JSON object (not an array).`;

  const result = await askClaudeJSON<any>({
    systemPrompt: CREATIVE_DIRECTOR_SYSTEM,
    userPrompt,
    maxTokens: 1024,
    temperature: 0.5,
  });

  return {
    model: result.model || failedPlan.model,
    prompt: result.prompt || failedPlan.prompt,
    negativePrompt: result.negative_prompt || result.negativePrompt || failedPlan.negativePrompt,
    aspectRatio: result.aspect_ratio || result.aspectRatio || failedPlan.aspectRatio,
    generateVideo: result.generate_video ?? result.generateVideo ?? failedPlan.generateVideo,
    videoPrompt: result.video_prompt || result.videoPrompt || failedPlan.videoPrompt,
    videoDuration: result.video_duration || result.videoDuration || failedPlan.videoDuration,
    rationale: result.rationale || 'retry after quality failure',
  };
}
