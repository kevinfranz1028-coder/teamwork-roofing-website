export function carouselBuilderPrompt(
  idea: { title: string; hook: string; formatNotes: string; captionKeywords: string[] },
  brandSystem: any,
  slideCount: number
): string {
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
- designNotes: Text placement, emphasis, any visual element suggestions
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
  return `Turn this idea into a complete production-ready Instagram Reel script:

IDEA: "${idea.title}"
HOOK: "${idea.hook}"
FORMAT NOTES: ${idea.formatNotes}

Create the full Reel script with:

hook (0-1.7 seconds): THE MOST IMPORTANT PART
- onScreenText: Exact text overlay — must create open loop
- visual: What the viewer sees (stock footage keyword or graphic description)
- audio: Voiceover line OR sound effect — must be original audio, NOT a trending sound

body (1.7-25 seconds):
- Array of segments, each with:
  - timestamp: Start time in seconds
  - onScreenText: Text overlay for this segment
  - voiceoverScript: Exact words if using voiceover (OR "text-only" if no VO)
  - visual: Stock footage keywords or graphic description
  - pacing: "fast" | "medium" | "slow"

cta (last 3-5 seconds):
- onScreenText: Specific call to action
- voiceover: Closing line
- visual: Description

totalLength: Target length in seconds (under 30 for max discovery)
audioMood: Overall audio direction — MUST be original (not trending)
captionKeywords: Woven naturally into caption
hashtags: Max 5

Return as JSON.`;
}

export const CONTENT_BUILDER_SYSTEM = `You are a faceless content production specialist for Instagram theme pages in 2026.

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
