import { getSetting } from '../../config/ai-settings.js';

// ─── Default Constants (exported for "Reset to Default" in dashboard) ────

export const DEFAULT_CONTENT_BUILDER_SYSTEM = `You are a faceless content production specialist for Instagram theme pages in 2026.

RULES:
- Zero face required in any content
- Every piece must be 100% original — zero reposts, zero screenshots, zero curated clips
- Hook must work in under 1.7 seconds (the scroll decision window)
- Written at 7th grade reading level for maximum reach
- 80% value content, 20% promotional maximum
- Original audio ALWAYS preferred over trending sounds
- Carousel text: max 10 words per headline, max 20 words body per slide
- Reel length: under 30 seconds for discovery, 30-90 for existing followers
- Caption must include natural SEO keywords (not stuffed)
- Max 5 hashtags, used for categorization only
- Every piece must answer: "Who would DM this to whom?"`;

export const DEFAULT_CAROUSEL_DESIGN_INSTRUCTION = `AI background image prompt — describe a SPECIFIC, CONCRETE scene that directly illustrates THIS slide's topic. Include: subject/object, setting, lighting direction, camera angle, color palette. Do NOT use generic/abstract imagery like "motivational background" or "professional setting". Every slide must have a unique scene tied to its headline. No text in the image.`;

export const DEFAULT_REEL_VISUAL_INSTRUCTION = `AI image generation prompt — describe a specific scene, subject, lighting, and camera angle that directly illustrates the message. NOT generic ("dramatic visual"), but concrete ("close-up of a cracked smartphone screen on a dark desk, harsh overhead light casting sharp shadows, 9:16 vertical"). Be concrete, not generic.`;

// ─── Dynamic Getters ─────────────────────────────────

export function getContentBuilderSystem(): string {
  return getSetting('content_builder_system', DEFAULT_CONTENT_BUILDER_SYSTEM);
}

// Kept for backward compatibility — re-exported as the dynamic version
export const CONTENT_BUILDER_SYSTEM = DEFAULT_CONTENT_BUILDER_SYSTEM;

export function carouselBuilderPrompt(
  idea: { title: string; hook: string; formatNotes: string; captionKeywords: string[] },
  brandSystem: any,
  slideCount: number
): string {
  const designInstruction = getSetting('carousel_design_instruction', DEFAULT_CAROUSEL_DESIGN_INSTRUCTION);

  return `Turn this idea into a complete production-ready Instagram carousel:

IDEA: "${idea.title}"
HOOK: "${idea.hook}"
FORMAT NOTES: ${idea.formatNotes}
TARGET SLIDE COUNT: ${slideCount}

BRAND SYSTEM:
${JSON.stringify(brandSystem, null, 2)}

Create the full carousel with:

slides: Array of ${slideCount} slides, each containing:
- slideNumber (1-${slideCount})
- type: "hook" | "value" | "cta"
- headline: Max 10 words, pattern interrupt on slide 1
- bodyText: Max 20 words supporting the headline (slides 2-${slideCount - 1})
- designNotes: ${designInstruction}
- textHierarchy: What's biggest, what's smallest

caption:
- hookLine: First line of caption (must create curiosity gap)
- body: Value content, max 120 words
- cta: Specific call to action — rotate between save, send, comment, follow
- seoKeywords: ${idea.captionKeywords.join(', ')} woven naturally into caption text
- hashtags: Max 5, specific to topic (not generic growth hashtags)

dmTrigger: A story companion keyword trigger — "DM me [WORD] for [specific value]"

originalityCheck: Confirm every element (text, concept, angle) is created from scratch for this page. Flag any element that could overlap with existing content.

Return as JSON.`;
}

export function reelBuilderPrompt(
  idea: { title: string; hook: string; formatNotes: string; captionKeywords: string[] },
  brandSystem: any
): string {
  const visualInstruction = getSetting('reel_visual_instruction', DEFAULT_REEL_VISUAL_INSTRUCTION);

  return `Turn this idea into a production-ready Instagram Reel for @ThePlantICU.

IDEA: "${idea.title}"
HOOK: "${idea.hook}"
FORMAT NOTES: ${idea.formatNotes}

THE PLANTICU REEL FORMULA:
This reel follows the "Plant ER" narrative arc: ALARM → DIAGNOSIS → TREATMENT → HOPE

Create the full Reel script:

hook (0-2 seconds): THE SCROLL-STOPPER
- onScreenText: Bold, alarming statement — open loop or shock. Max 8 words. Examples: "Your monstera is DROWNING" / "This is NOT underwatering" / "Your $200 plant has 48 hours"
- visual: ${visualInstruction} — HOOK FRAME style (maximum drama, macro of the problem)
- voiceoverScript: Match the text energy — short, punchy, concerned tone
- segmentType: "hook"

body (2-20 seconds): THE DIAGNOSIS & TREATMENT
- Array of 3-5 segments, each with:
  - timestamp: Start time in seconds
  - onScreenText: One clear instruction or insight per segment. Max 12 words.
  - voiceoverScript: Expand on the text — conversational, like explaining to a worried friend. 1-2 sentences per segment.
  - visual: ${visualInstruction} — BODY FRAME style (educational, step-by-step)
  - pacing: "fast" for alarm, "medium" for explanation, "slow" for important steps
  - segmentType: "body"
  - durationSeconds: 3-5 seconds per segment

cta (last 3-5 seconds): THE HOPE
- onScreenText: "Follow @ThePlantICU" or "Save this for next time" or specific DM trigger
- voiceoverScript: Warm, reassuring close — "Your plant's not dead yet. Follow for more rescues."
- visual: ${visualInstruction} — CTA FRAME style (recovered plant, hopeful, warm light)
- segmentType: "cta"

totalLength: Target 18-25 seconds (sweet spot for discovery reach)
audioMood: "Calm urgency — concerned but competent, like a nurse giving instructions. NOT dramatic/anxious. Reassuring expertise."

voiceoverText: Complete voiceover script as one continuous paragraph, natural speech patterns. This will be sent to OpenAI TTS.

caption:
- hookLine: First line creates curiosity gap (gets cut off in feed → drives tap-through)
- body: 60-100 words. Lead with the diagnosis, then treatment summary. Include 1 personal touch.
- cta: "Save this for your next plant emergency" or "Send to someone whose [plant] needs help" or DM trigger
- seoKeywords: ${idea.captionKeywords.join(', ')} woven naturally into caption text — never keyword-stuffed
- hashtags: Max 5, specific: #PlantICU #HouseplantRescue #PlantDiagnosis #[SpecificPlant] #[SpecificProblem]

dmTrigger: Keyword + value offer for the story companion. E.g., "DM me RESCUE for the free recovery checklist"

Return as JSON.`;
}
