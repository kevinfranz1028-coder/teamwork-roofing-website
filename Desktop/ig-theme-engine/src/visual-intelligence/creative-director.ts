import { CONFIG } from '../config/env.js';
import { getActiveAISettings } from '../config/ai-settings.js';
import { getStyleAnchor } from './knowledge/style-anchors.js';
import { UNIVERSAL_NEVER, UNIVERSAL_ALWAYS, MODEL_TIPS } from './knowledge/model-rules.js';
import { MODEL_REGISTRY } from './models/model-registry.js';
import type { VisualBrief, VisualPlan, ImageModel } from './types.js';
import { logApiCost } from '../utils/cost-tracker.js';

const SYSTEM_PROMPT = `You are the Creative Director for an AI-powered Instagram plant care page called ThePlantICU. Your job is to plan the visual execution for each content segment.

You select the optimal AI image model for each segment and rewrite vague content descriptions into precise photographic prompts that a professional photographer would understand.

AVAILABLE IMAGE MODELS:
- flux-2-pro: Best for photorealistic plant photography, nature macro, atmospheric lighting. DEFAULT CHOICE.
- gpt-image-1.5: Best when text MUST appear in the image, or for complex multi-element compositions. Use sparingly.
- ideogram-3: Best for typography-first designs, posters, social cards. Use only when text IS the visual.

ABSOLUTE RULES — NEVER VIOLATE:
${UNIVERSAL_NEVER.map(r => '- ' + r).join('\n')}

ALWAYS DO:
${UNIVERSAL_ALWAYS.map(r => '- ' + r).join('\n')}

PROMPT WRITING STYLE:
You write as if briefing a professional photographer. Use specific technical language:
- Lens: "100mm f/2.8 macro lens" not "close-up"
- Lighting: "warm side-lit golden hour light raking across leaves" not "nice lighting"
- Depth: "shallow depth of field, f/2.8, subject tack sharp against creamy bokeh" not "blurry background"
- Color: "warm amber and deep forest green palette, Kodak Portra 400 color science" not "warm colors"
- Texture: "visible leaf venation, tiny water droplets on waxy surface" not "detailed leaf"

CRITICAL: If the content description mentions products, brands, clocks, timers, text, or before/after comparisons — REWRITE the visual to be purely photographic. Show the RESULT or the SUBJECT, never the product label.

For example:
- "Yellow sticky trap with brand name" → "Close-up of a yellow adhesive card inserted in dark potting soil among green pothos leaves, dozens of tiny dark fungus gnats stuck to the surface, macro lens, shallow focus"
- "Hour 24: Total annihilation" → "Clean healthy plant in terracotta pot, fresh dark soil surface with no visible pests, warm morning window light, sense of relief and renewal"
- "Mosquito Bits bag next to plant" → "Fine golden granules scattered across dark moist soil surface, macro close-up showing granule texture, a few green leaves soft in background"

Respond with a JSON array of VisualPlan objects, one per brief. No markdown, no backticks, just the JSON array.`;

/**
 * Send all visual briefs to Claude and get back a VisualPlan for each.
 */
export async function planVisualsBatch(briefs: VisualBrief[]): Promise<VisualPlan[]> {
  if (briefs.length === 0) return [];

  const anchor = getStyleAnchor();
  const settings = getActiveAISettings() as any;
  const defaultModel: ImageModel = settings?.default_image_model || 'flux-2-pro';
  const enableVideo = settings?.enable_video_generation ?? (process.env.ENABLE_VIDEO_GENERATION !== 'false');

  // Build the user message with all briefs
  const briefDescriptions = briefs.map((b, i) => (
    `[Segment ${i}] type=${b.segmentType}, content="${b.contentType}", text="${b.onScreenText.slice(0, 100)}", visual="${b.originalVisualDescription.slice(0, 200)}", mood="${b.brandContext.mood}"`
  )).join('\n');

  const userMessage = `Plan visuals for ${briefs.length} segments. Default model: ${defaultModel}. Video generation: ${enableVideo ? 'enabled' : 'disabled'}.
Photography anchors — Camera: ${anchor.cameraBody}, Lens: ${anchor.defaultLens}, Light: ${anchor.defaultLighting}, Color: ${anchor.defaultColorProfile}.

BRIEFS:
${briefDescriptions}

Return a JSON array of ${briefs.length} objects, each with: model, prompt, negativePrompt, aspectRatio, generateVideo, motionPrompt, lens, lighting, depthOfField, colorPalette.
For aspectRatio use "${briefs[0]?.contentType === 'carousel' ? '1:1' : '9:16'}".
Set generateVideo to ${enableVideo} for reel segments, false for carousel/story.`;

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': CONFIG.ai.apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: CONFIG.ai.model || 'claude-sonnet-4-5-20250929',
        max_tokens: 4000,
        system: SYSTEM_PROMPT,
        messages: [{ role: 'user', content: userMessage }],
      }),
    });

    if (!response.ok) {
      console.log(`    [Creative Director] Claude API error ${response.status}, using fallback plans`);
      return briefs.map(b => buildFallbackPlan(b, defaultModel, enableVideo));
    }

    const data = await response.json() as any;
    const text = data.content?.[0]?.text || '';

    // Log creative director cost
    const cdInputTokens = data.usage?.input_tokens || 0;
    const cdOutputTokens = data.usage?.output_tokens || 0;
    const cdCost = (cdInputTokens / 1_000_000) * 3 + (cdOutputTokens / 1_000_000) * 15;
    logApiCost({
      provider: 'anthropic',
      category: 'text',
      endpoint: 'messages.create (creative-director)',
      model: CONFIG.ai.model || 'claude-sonnet-4-5-20250929',
      description: `Creative Director: ${briefs.length} segments`,
      inputTokens: cdInputTokens,
      outputTokens: cdOutputTokens,
      estimatedCost: cdCost,
    });

    // Parse JSON array from response
    const jsonMatch = text.match(/\[[\s\S]*\]/);
    if (!jsonMatch) {
      console.log('    [Creative Director] Could not parse response, using fallback plans');
      return briefs.map(b => buildFallbackPlan(b, defaultModel, enableVideo));
    }

    const plans: VisualPlan[] = JSON.parse(jsonMatch[0]);

    console.log(`    [Creative Director] Claude returned ${plans.length} plans`);
    plans.forEach((p, i) => {
      console.log(`      Plan ${i}: model=${p.model}, generateVideo=${p.generateVideo}, prompt="${(p.prompt || '').slice(0, 60)}..."`);
    });

    // Validate and fill gaps
    return plans.map((plan, i) => ({
      model: plan.model || defaultModel,
      prompt: plan.prompt || briefs[i].originalVisualDescription,
      negativePrompt: plan.negativePrompt || anchor.imageNegativePrompt,
      aspectRatio: plan.aspectRatio || (briefs[i].contentType === 'carousel' ? '1:1' : '9:16'),
      generateVideo: plan.generateVideo ?? (enableVideo && briefs[i].contentType === 'reel'),
      motionPrompt: plan.motionPrompt || undefined,
      motionStyle: plan.motionStyle || undefined,
      lens: plan.lens || anchor.defaultLens,
      lighting: plan.lighting || anchor.defaultLighting,
      depthOfField: plan.depthOfField || 'shallow, f/2.8',
      colorPalette: plan.colorPalette || anchor.defaultColorProfile,
    }));
  } catch (err: any) {
    console.log(`    [Creative Director] Error: ${err.message?.slice(0, 100)}, using fallback plans`);
    return briefs.map(b => buildFallbackPlan(b, defaultModel, enableVideo));
  }
}

/**
 * Retry a single plan with quality feedback.
 */
export async function retryPlan(brief: VisualBrief, feedback: string): Promise<VisualPlan> {
  const anchor = getStyleAnchor();
  const settings = getActiveAISettings() as any;
  const defaultModel: ImageModel = settings?.default_image_model || 'flux-2-pro';

  console.log(`    [Creative Director] Retrying with feedback: ${feedback.slice(0, 80)}`);

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': CONFIG.ai.apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: CONFIG.ai.model || 'claude-sonnet-4-5-20250929',
        max_tokens: 1000,
        system: SYSTEM_PROMPT,
        messages: [{ role: 'user', content: `Replan ONE segment. Previous attempt failed quality check.

Segment: type=${brief.segmentType}, visual="${brief.originalVisualDescription.slice(0, 200)}"
Quality feedback: "${feedback}"

Write a BETTER prompt that avoids the issues. Return ONE JSON object (not array): {model, prompt, negativePrompt, aspectRatio, generateVideo, motionPrompt, lens, lighting, depthOfField, colorPalette}` }],
      }),
    });

    if (!response.ok) return buildFallbackPlan(brief, defaultModel, false);

    const data = await response.json() as any;
    const text = data.content?.[0]?.text || '';

    // Log retry cost
    const retryInputTokens = data.usage?.input_tokens || 0;
    const retryOutputTokens = data.usage?.output_tokens || 0;
    const retryCost = (retryInputTokens / 1_000_000) * 3 + (retryOutputTokens / 1_000_000) * 15;
    logApiCost({
      provider: 'anthropic',
      category: 'text',
      endpoint: 'messages.create (creative-director-retry)',
      model: CONFIG.ai.model || 'claude-sonnet-4-5-20250929',
      description: `Creative Director retry: ${brief.segmentType}`,
      inputTokens: retryInputTokens,
      outputTokens: retryOutputTokens,
      estimatedCost: retryCost,
    });

    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) return buildFallbackPlan(brief, defaultModel, false);

    const plan = JSON.parse(jsonMatch[0]);
    return {
      model: plan.model || defaultModel,
      prompt: plan.prompt || brief.originalVisualDescription,
      negativePrompt: plan.negativePrompt || anchor.imageNegativePrompt,
      aspectRatio: plan.aspectRatio || (brief.contentType === 'carousel' ? '1:1' : '9:16'),
      generateVideo: plan.generateVideo ?? false,
      motionPrompt: plan.motionPrompt,
      lens: plan.lens || anchor.defaultLens,
      lighting: plan.lighting || anchor.defaultLighting,
      depthOfField: plan.depthOfField || 'shallow, f/2.8',
      colorPalette: plan.colorPalette || anchor.defaultColorProfile,
    };
  } catch {
    return buildFallbackPlan(brief, defaultModel, false);
  }
}

function buildFallbackPlan(brief: VisualBrief, model: ImageModel, enableVideo: boolean): VisualPlan {
  const anchor = getStyleAnchor();
  return {
    model,
    prompt: `${anchor.imageStylePrefix}. ${brief.originalVisualDescription}. ${brief.brandContext.mood} mood`,
    negativePrompt: anchor.imageNegativePrompt,
    aspectRatio: brief.contentType === 'carousel' ? '1:1' : '9:16',
    generateVideo: enableVideo && brief.contentType === 'reel',
    lens: anchor.defaultLens,
    lighting: anchor.defaultLighting,
    depthOfField: 'shallow, f/2.8',
    colorPalette: anchor.defaultColorProfile,
  };
}
