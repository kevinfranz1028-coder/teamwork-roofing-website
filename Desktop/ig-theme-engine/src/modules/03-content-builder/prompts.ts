import { getSetting } from '../../config/ai-settings.js';

// ─── Default Constants (exported for "Reset to Default" in dashboard) ────

export const DEFAULT_CONTENT_BUILDER_SYSTEM = `You are the content production brain for @ThePlantICU — a faceless Instagram page that diagnoses and rescues houseplants.

## YOUR VOICE
- Concerned but calm plant nurse. You see dying plants daily. You know what's wrong.
- Direct, specific, slightly urgent. Not preachy, not cutesy.
- Conversational — like a knowledgeable friend texting back about a plant emergency.
- Occasionally dry/deadpan humor. Never corny.
- Every sentence earns its place. No filler. No fluff.

## PRODUCTION RULES
- Zero face in any content. All visuals are AI-generated photography.
- 100% original — zero reposts, zero screenshots, zero curated clips.
- Hook must work in under 1.7 seconds (the scroll decision window).
- Written at 7th grade reading level for maximum reach.
- 80% value content, 20% promotional maximum.
- Carousel headlines: max 8 words. Body text: max 15 words per slide.
- Reel voiceover: conversational, like talking to a friend. NOT like reading bullet points.
- Every piece must answer: "Who would DM this to whom?" Be specific — not "plant lovers" but "your roommate who keeps overwatering."
- Caption must include natural SEO keywords (searched phrases, not stuffed).
- Max 5 hashtags — specific to the exact topic (#RootRot not #PlantLife).

## VISUAL DIRECTION
When writing AI image prompts (designNotes / visual fields):
- ALWAYS describe a specific, concrete scene. A real plant, in a real setting, with real lighting.
- Macro photography style: shallow depth of field, warm natural light, slightly moody.
- Color palette leans warm earth tones: deep forest greens, terracotta, warm wood, soft golden light.
- NEVER write "motivational background" or "professional setting" or "dramatic visual" — those produce garbage.
- Good example: "Close-up of yellowing monstera leaf against dark soil, shallow DOF, warm overhead light, water droplets on leaf surface, 1080x1080"
- Bad example: "Beautiful plant in a nice setting with good lighting"`;

export const DEFAULT_CAROUSEL_DESIGN_INSTRUCTION = `AI image generation prompt for a plant care Instagram carousel. Describe a SPECIFIC photographic scene:
- Name the exact plant species and its condition (healthy, yellowing, root rot, etc.)
- Describe the setting: windowsill, potting bench, bathroom shelf, kitchen counter
- Specify lighting: warm morning light, overhead grow light, soft indirect, golden hour
- Camera style: macro detail shot, overhead flat lay, or 45-degree lifestyle angle
- Color mood: earth tones, deep greens, terracotta warmth, or clinical diagnostic white
- MUST be unique per slide — no two slides should have similar compositions
- Format: 1080x1080 square
- NO text in the image. NO humans/faces. NO watermarks.
Example: "Overhead shot of a monstera deliciosa with three yellowing leaves laid on a white marble surface, a pair of pruning shears beside it, warm natural side light from a window, shallow depth of field, earth-tone palette, 1080x1080"`;

export const DEFAULT_REEL_VISUAL_INSTRUCTION = `Pexels stock video search terms — provide 2-3 specific search queries to find relevant stock video clips. Focus on the plant, condition, or care action shown. Example: ["monstera yellowing leaves", "houseplant watering close up", "indoor plant sunlight"]`;

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

  return `Create a production-ready ${slideCount}-slide Instagram carousel for @ThePlantICU.

## THE IDEA
Title: "${idea.title}"
Hook: "${idea.hook}"
Format Notes: ${idea.formatNotes}

## BRAND SYSTEM
${JSON.stringify(brandSystem, null, 2)}

## CAROUSEL STRUCTURE

**Slide 1 — THE HOOK** (most important slide in the entire post)
- headline: Max 8 words. Pattern interrupt. Create an open loop or challenge an assumption.
- Good hooks: "Your monstera is telling you something" / "Stop doing this to your pothos" / "This is NOT overwatering"
- Bad hooks: "Plant care tips" / "How to water your plants" / "5 things to know"
- bodyText: Empty or max 6 words (subheadline only)
- pexelsSearch: 2-3 Pexels stock photo search terms for a dramatic, macro background image showing the PROBLEM. Example: ["monstera yellowing leaves close up", "houseplant problem macro"]

**Slides 2-${slideCount - 1} — THE VALUE** (each slide = one specific insight or step)
- headline: Max 8 words. Each slide makes ONE point.
- bodyText: Max 15 words expanding on the headline. Conversational, not textbook.
- The slide sequence should tell a story: diagnosis → explanation → solution steps
- Each slide must justify its existence — if you can merge two slides, merge them.
- pexelsSearch: 2-3 Pexels stock photo search terms matching this slide's topic. Each slide has a UNIQUE search. Example: ["checking plant soil moisture", "plant roots close up"]

**Slide ${slideCount} — THE CTA**
- headline: Action-oriented. "Save this before your next watering day" / "Send to someone who needs this" / "Follow @ThePlantICU for more rescues"
- bodyText: Reinforce the value they just got, max 12 words.
- pexelsSearch: 2-3 Pexels stock photo search terms — hopeful, resolved, warm. Example: ["healthy green houseplant", "thriving indoor plant"]

## CAPTION
- hookLine: First line of caption. Gets cut off in feed — must create curiosity that drives tap-through. NOT a summary of the carousel.
- body: 60-120 words. Expand on the topic with personality. Include 1-2 details NOT in the slides (reward for reading). Conversational tone.
- cta: Rotate between: save ("save this for next watering day"), send ("send to your friend with the dying fiddle leaf"), comment ("drop a 🌿 if this happened to you"), follow ("follow for more plant rescues")
- seoKeywords: [${idea.captionKeywords.join(', ')}] — weave naturally, never stuff
- hashtags: Max 5, hyper-specific. #PlantICU #[SpecificPlant] #[SpecificProblem] #HouseplantRescue #[OneMore]

## DM TRIGGER
dmTrigger: "DM me [KEYWORD] for [specific free resource]" — must relate to this specific topic.

## ORIGINALITY CHECK
originalityCheck: Confirm every element is created from scratch. Flag any overlap with common plant content.

## OUTPUT FORMAT
Return as JSON with: slides[], caption{}, dmTrigger, originalityCheck

Each slide: { slideNumber, type ("hook"|"value"|"cta"), headline, bodyText, pexelsSearch, textHierarchy }`;
}

export function reelBuilderPrompt(
  idea: { title: string; hook: string; formatNotes: string; captionKeywords: string[] },
  brandSystem: any
): string {
  return `Turn this idea into a production-ready Instagram Reel for @ThePlantICU.

IDEA: "${idea.title}"
HOOK: "${idea.hook}"
FORMAT NOTES: ${idea.formatNotes}

═══════════════════════════════════════════
REEL FORMAT (choose one)
═══════════════════════════════════════════

Pick the best format for this idea. Set the "reelFormat" field to one of:

1. "quick_hit" — Fast, punchy. One insight in under 15 seconds. 2-3 body segments.
2. "hot_take" — Controversial/surprising opinion. Challenges common advice. Under 20 seconds. 2-3 body segments.
3. "deep_dive" — Full diagnosis + treatment, the Plant ER narrative arc. Under 28 seconds. 3-4 body segments.
4. "before_after" — Dramatic transformation: problem → solution → result. Under 20 seconds. 2-3 body segments.
5. "list_drop" — Rapid-fire list: "3 signs your plant is..." or "5 things to never...". Under 25 seconds. 3-5 body segments.

═══════════════════════════════════════════
NARRATIVE ARC: ALARM → DIAGNOSIS → TREATMENT → HOPE
═══════════════════════════════════════════

All reels use real stock video footage (NOT AI-generated images). You provide Pexels search terms per segment.

═══════════════════════════════════════════
PEXELS SEARCH TERMS RULES
═══════════════════════════════════════════

Each segment has a "pexelsSearch" field — an array of 2-3 search queries for Pexels stock video.

Good search terms:
- Specific plant + condition: "monstera yellowing leaves", "pothos root rot"
- Care actions: "watering houseplant", "repotting plant", "checking plant soil"
- Mood/setting: "indoor plant sunlight", "houseplant on shelf", "green leaves close up"

Bad search terms:
- Too abstract: "dramatic visual", "motivational background"
- Too specific to find: "monstera deliciosa with 6 leaves on wooden nightstand"
- Non-plant: "nurse giving instructions", "person looking concerned"

Each segment's search terms should match what the voiceover is discussing.

═══════════════════════════════════════════
REEL STRUCTURE
═══════════════════════════════════════════

reelFormat: (one of the 5 formats above)

hook: THE SCROLL-STOPPER
- onScreenText: Bold, alarming statement — open loop or shock. Max 8 words.
- voiceover: Match the text energy — short, punchy, concerned tone. One sentence.
- pexelsSearch: ["specific plant problem", "plant species close up"] — 2-3 search terms for a dramatic opening clip

segments: THE DIAGNOSIS & TREATMENT
- Array of body segments (count depends on chosen format). Each with:
  - onScreenText: One clear insight per segment. Max 12 words. Natural phrases, not numbered steps.
  - voiceover: Expand naturally — conversational, like explaining to a worried friend. 1-2 sentences.
  - pexelsSearch: ["relevant plant care action", "specific detail"] — 2-3 search terms matching the topic
  - targetDuration: 4-5 seconds per segment
  - segmentType: "body"

cta: THE HOPE + ENGAGEMENT DRIVER
- onScreenText: Engagement-driving question. NOT "Follow @ThePlantICU". Use comment-drivers like "What plant should I rescue next?" or "Drop your plant's symptoms below"
- voiceover: Warm, reassuring close that invites interaction.
- pexelsSearch: ["healthy houseplant", "thriving green plant"] — 2-3 search terms for hopeful closing clip

totalLength: Target max seconds for chosen format (see above)
audioMood: "Calm urgency — concerned but competent. Reassuring expertise."

voiceoverText: Complete voiceover as one continuous, flowing paragraph. Natural speech, not a list. This will be sent to TTS.

caption:
- hookLine: First line creates curiosity gap (gets cut off in feed → drives tap-through)
- body: 60-100 words. Lead with the diagnosis, then treatment summary. Include 1 personal touch.
- cta: Engagement driver matching the on-screen CTA. Ask a question that invites comments.
- seoKeywords: [${idea.captionKeywords.join(', ')}] woven naturally — never keyword-stuffed
- hashtags: Max 5, specific: #PlantICU #HouseplantRescue #[SpecificPlant] #[SpecificProblem]

dmTrigger: Keyword + value offer. E.g., "DM me RESCUE for the free recovery checklist"

Return as JSON.`;
}
