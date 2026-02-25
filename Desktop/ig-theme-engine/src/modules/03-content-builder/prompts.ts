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

export const DEFAULT_REEL_VISUAL_INSTRUCTION = `Kling video generation prompt — describe a MOTION SEQUENCE, not a static image. This prompt drives Kling AI video (image-to-video), so describe what the camera DOES:

REQUIRED ELEMENTS:
- Camera motion: "camera slowly pushes in", "gentle drift to the right", "slow zoom into leaf surface", "camera pulls back to reveal"
- The specific plant, its condition, and what's visible at this camera distance
- Lighting direction and mood (consistent with the sceneSetup for this reel)
- Depth of field and focus behavior: "shallow DOF with background softly blurred", "focus racks from pot to leaf"
- Motion speed: use "slow", "gentle", "subtle" — Kling works best with slow, deliberate camera moves
- Format: 9:16 vertical

GOOD EXAMPLES:
- "Camera slowly pushes in toward a drooping pothos on a wooden nightstand, golden afternoon light from the left, shallow depth of field, the brown leaf tips gradually fill the frame, 9:16"
- "Gentle camera drift across the surface of a monstera leaf, revealing tiny brown spots and yellowing edges, soft overhead light, macro detail becoming visible, shallow DOF, 9:16"
- "Slow pull back from extreme close-up of mushy brown roots to reveal the full plant being held above its terracotta pot, warm overhead lighting, soil particles falling, 9:16"

BAD EXAMPLES:
- "Close-up of a dying plant" (no motion, no specifics)
- "Dramatic plant rescue scene with cinematic lighting" (abstract, no camera direction)
- "Beautiful monstera in a cozy room" (static description, no motion cue for Kling)

CONTINUITY RULE: This visual MUST be part of the same scene as all other segments in this reel. Same plant, same room, same lighting. The camera just moves to a different position or zoom level.`;

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
- designNotes: ${designInstruction} — dramatic, macro, the PROBLEM visible. Most impactful visual of the set.

**Slides 2-${slideCount - 1} — THE VALUE** (each slide = one specific insight or step)
- headline: Max 8 words. Each slide makes ONE point.
- bodyText: Max 15 words expanding on the headline. Conversational, not textbook.
- The slide sequence should tell a story: diagnosis → explanation → solution steps
- Each slide must justify its existence — if you can merge two slides, merge them.
- designNotes: ${designInstruction} — each slide has a UNIQUE scene. Show what you're describing.

**Slide ${slideCount} — THE CTA**
- headline: Action-oriented. "Save this before your next watering day" / "Send to someone who needs this" / "Follow @ThePlantICU for more rescues"
- bodyText: Reinforce the value they just got, max 12 words.
- designNotes: ${designInstruction} — hopeful, resolved, warm. The "after" to the hook's "before."

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

Each slide: { slideNumber, type ("hook"|"value"|"cta"), headline, bodyText, designNotes, textHierarchy }`;
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

## THE PLANTICU REEL FORMULA
This reel follows the "Plant ER" narrative arc: ALARM → DIAGNOSIS → TREATMENT → HOPE

## CRITICAL: ONE CONTINUOUS VISUAL JOURNEY
Your reel must feel like ONE continuous video, not a slideshow of unrelated images. Every viral plant reel uses this technique:

**THE SCENE:** Pick ONE specific plant, in ONE specific setting, with ONE consistent lighting setup. Every segment takes place in this same scene. The camera MOVES through the scene — it doesn't teleport to a new location.

**THE CAMERA PATH:** Describe the camera's journey through the scene:
- Hook: Wide establishing shot (the plant in its environment)
- Body segment 1: Camera moves closer, revealing the problem
- Body segment 2: Camera zooms to macro — extreme detail of the issue
- Body segment 3: Camera holds on the treatment action (hands working, but no face)
- Body segment 4 (if needed): Camera begins pulling back
- CTA: Camera returns to wide shot — same plant, same room, but the feeling has shifted from alarm to hope

**VISUAL CONTINUITY RULES:**
- ALL segments must reference the SAME plant species, pot, and setting
- Describe camera MOTION in every visual field: "camera slowly pushes in toward...", "camera drifts right to reveal...", "camera pulls back to show..."
- Adjacent segments should share visual elements — if segment 2 ends on a leaf close-up, segment 3 should start from a similar perspective
- Lighting stays consistent across all segments (same time of day, same direction)
- Maximum 4-5 unique Kling video clips for the entire reel (NOT one per segment)

**VISUAL DESCRIPTION FORMAT for Kling video generation:**
Each visual field is used as a Kling image-to-video prompt. Write them as MOTION descriptions:
- GOOD: "Camera slowly zooms into the base of the snake plant stem, revealing brown mushy tissue where it meets the soil, warm overhead light, shallow depth of field, 9:16"
- GOOD: "Slow camera drift across the leaf surface showing microscopic brown spots spreading, soft focus breathing effect, camera remains mostly static with gentle movement, 9:16"
- BAD: "Close-up of a snake plant with root rot" (no motion, no continuity, generic)
- BAD: "Dramatic plant emergency scene" (abstract, produces garbage)

Create the full Reel script:

### sceneSetup (NEW — required field)
Describe the ONE scene that the entire reel takes place in. This anchors visual continuity:
- plant: Exact species and its current condition
- setting: Specific location (bedroom nightstand, kitchen windowsill, bathroom shelf, etc.)
- lighting: Time of day, light direction, mood
- pot: Type and color
- props: Any visible items (watering can, soil bag, pruning shears, etc.)
- colorPalette: Dominant colors in the scene

Example: "A drooping pothos in a white ceramic pot on a wooden bedroom nightstand. Late afternoon golden light streaming from a window on the left. A small watering can and a moisture meter sit beside the pot. Warm earth tones — golden wood, white ceramic, deep green leaves with brown edges."

### hook (0-2 seconds): THE SCROLL-STOPPER
- onScreenText: Bold, alarming statement — open loop or shock. Max 8 words. Examples: "Your monstera is DROWNING" / "This is NOT underwatering" / "Your $200 plant has 48 hours"
- visual: ${visualInstruction} — WIDE establishing shot of the scene. The plant and its problem should be immediately visible. Include camera direction: "camera slowly pushes forward toward..."
- voiceoverScript: Match the text energy — short, punchy, concerned tone. Under 8 words.
- segmentType: "hook"
- durationSeconds: 2

### body (2-20 seconds): THE DIAGNOSIS & TREATMENT
Array of 3-4 segments (NOT 5-7 — fewer clips = better visual continuity). Each with:
- timestamp: Start time in seconds
- onScreenText: One clear point per segment. Max 10 words. Written as SUBTITLES, not headlines.
- voiceoverScript: 1-2 sentences, conversational. Like explaining to a worried friend.
- visual: ${visualInstruction} — MUST continue the camera journey from the previous segment. Describe the camera MOVEMENT, not just a static scene. Reference the same plant/setting from sceneSetup.
- pacing: "fast" for alarm segments, "medium" for explanation, "slow" for important steps
- segmentType: "body"
- durationSeconds: 3-5 seconds per segment

### cta (last 3-4 seconds): THE HOPE + ENGAGEMENT DRIVER
- onScreenText: Engagement-driving CTA that invites comments. NOT just "Follow @ThePlantICU".
  GOOD CTAs: "Tell me your plant — I'll diagnose it" / "Drop your plant's name, I'll tell you what's wrong" / "Which plant should I rescue next?" / "Send this to someone whose [plant] needs help"
  BAD CTAs: "Follow @ThePlantICU" / "Like and share" / "Follow for more"
  The CTA should drive COMMENTS and SENDS, not just follows. Comments boost reach. "Follow" CTAs are passive.
- voiceoverScript: Warm, reassuring close. "Your plant's not dead yet. Tell me what you're growing... I'll help." Conversational, inviting.
- visual: ${visualInstruction} — Camera pulls BACK to the wide establishing shot from the hook, but the mood has shifted — warmer, more hopeful. Same plant, same room. Include "@ThePlantICU" as a small watermark element.
- segmentType: "cta"
- durationSeconds: 4

### totalLength: Target 20-27 seconds (sweet spot: 22-25s)

### audioMood: "Calm urgency — concerned but competent, like a nurse giving instructions. NOT dramatic/anxious. Reassuring expertise."

## VOICEOVER PACING (CRITICAL)
voiceoverText: Write the COMPLETE voiceover as one continuous, natural paragraph. This goes directly to TTS.
- Use "..." for natural pauses between thoughts
- Vary sentence length: short punchy for urgency, longer flowing for explanation
- Hook VO: SHORT (under 8 words, said fast)
- Body VO: Breathe — 1-2 sentences per segment, don't cram
- CTA VO: Slow down — warm, reassuring, slightly slower pace
- Write like you're TALKING to a worried friend, not reading a teleprompter
- NEVER write stage directions like "(pause)" or "(concerned tone)" — TTS ignores them
- Good: "Your pothos... is telling you something. See these brown tips? That's not sunburn. That's salt buildup from tap water. Here's the fix... flush the soil with filtered water until it runs clear. Do this once a month. Your plant will bounce back in two weeks. Tell me what plant you're struggling with... I'll help."
- Bad: "Today we will discuss brown tips on pothos plants. The primary cause is mineral buildup. The recommended treatment is soil flushing."

### caption:
- hookLine: First line creates curiosity gap (gets cut off in feed → drives tap-through). NOT a summary.
- body: 60-100 words. Lead with the diagnosis, then treatment summary. Include 1 personal touch. Conversational.
- cta: Rotate between engagement drivers:
  - Comment trigger: "Drop a if this happened to you" / "Which plant should I rescue next?"
  - Send trigger: "Send to someone whose [plant] needs help" / "Tag your friend who overwaters everything"
  - Save trigger: "Save this for your next watering day"
  - DM trigger: "DM me [KEYWORD] for the free [resource]"
- seoKeywords: ${idea.captionKeywords.join(', ')} woven naturally into caption text — never keyword-stuffed
- hashtags: Max 5, specific: #PlantICU #HouseplantRescue #PlantDiagnosis #[SpecificPlant] #[SpecificProblem]

### dmTrigger: Keyword + value offer for the story companion. E.g., "DM me RESCUE for the free recovery checklist"

Return as JSON matching this exact structure. The sceneSetup field is required — it's what ensures visual continuity across the entire reel.`;
}
