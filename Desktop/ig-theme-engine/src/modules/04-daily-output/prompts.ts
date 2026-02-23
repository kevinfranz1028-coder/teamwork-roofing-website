import { CONFIG } from '../../config/env.js';

export interface CreativeBrief {
  id: number;
  title: string;
  notes: string | null;
  competitor_links: string | null;
  content_angles: string | null;
  mood_themes: string | null;
  visual_style: string | null;
  target_emotions: string | null;
  is_active: number;
}

export function formatBriefContext(brief: CreativeBrief | null): string {
  if (!brief) return '';

  const sections: string[] = ['\n\n── CREATIVE BRIEF ──'];

  if (brief.title) sections.push(`Brief: ${brief.title}`);

  if (brief.notes) sections.push(`\nInspiration & Notes:\n${brief.notes}`);

  if (brief.competitor_links) {
    try {
      const links = JSON.parse(brief.competitor_links) as string[];
      if (links.length > 0) sections.push(`\nCompetitor References: ${links.join(', ')}`);
    } catch { /* ignore parse errors */ }
  }

  if (brief.content_angles) {
    try {
      const angles = JSON.parse(brief.content_angles) as string[];
      if (angles.length > 0) sections.push(`\nContent Angles to Explore: ${angles.join(', ')}`);
    } catch { /* ignore parse errors */ }
  }

  if (brief.mood_themes) sections.push(`\nMood & Themes: ${brief.mood_themes}`);
  if (brief.visual_style) sections.push(`\nVisual Style Direction: ${brief.visual_style}`);
  if (brief.target_emotions) sections.push(`\nTarget Emotions: ${brief.target_emotions}`);

  sections.push('── END BRIEF ──');
  return sections.join('\n');
}

export const DAILY_ENGINE_SYSTEM = (niche: string, performanceContext: string) => `You are the autonomous content operator for a "${niche}" Instagram theme page.

YOUR PRIME DIRECTIVES:
1. Every piece of content must be 100% ORIGINAL — never repost, never curate
2. Optimize for DM SENDS first (3-5x more valuable than likes for growth)
3. Hook in under 1.7 seconds (the scroll decision window)
4. Watch time is the #1 ranking factor — design for completion
5. Caption SEO keywords > hashtags for discovery
6. Include Story sequence with interactive elements + DM trigger
7. 80% value / 20% promotional max
8. Original audio preferred over trending sounds
${performanceContext}`;

export const DAILY_ENGINE_USER = (date: string, niche: string) => `Generate today's complete Daily Content Package.

Date: ${date}
Niche: ${niche}
Posting Schedule: ${CONFIG.app.postingSchedule.join(', ')}

Deliver ALL of the following as a single JSON object:

1. trendAlert: Is there a trending topic worth hijacking today? If yes, provide the original angle (30%+ new content). If no, set hasTrend to false.

2. carousel: Full carousel with:
   - idea (title, hook, sendTrigger, whyItWillPerform)
   - slides (${CONFIG.content.carouselSlideCount} slides, each with slideNumber, type, headline, bodyText, designNotes)
   - caption (hookLine, body under 120 words, cta, seoKeywords array, hashtags array max 5)

3. reel: Full reel script with:
   - idea (title, hook, sendTrigger, whyItWillPerform)
   - hook (onScreenText, visual, audio — under 1.7 seconds)
   - body (array of timestamped segments with text, voiceover, visuals)
   - cta (onScreenText, voiceover)
   - totalLength (target under ${CONFIG.content.reelMaxLength} seconds)
   - audioMood, caption (same structure as carousel caption)

4. storySequence: 6-8 story slides including:
   - At least 2 interactive elements (poll, question, slider)
   - Final slide must be a DM trigger: "DM me [KEYWORD] for [VALUE]"
   - Provide dmTriggerKeyword and dmTriggerValue

5. designDirection: Today's color palette (hex codes), font pairing, mood

Return as a single JSON object with all 5 sections.`;

export const OPTIONS_ENGINE_USER = (niche: string, slideCount: number) => `Generate exactly 5 diverse content ideas for a "${niche}" Instagram theme page. Each idea should have a different angle and format mix.

Return a JSON object with an "options" array of 5 items. Each item must have:
- title: string (compelling, specific title)
- content_type: "carousel" or "reel"
- hook: string (under 1.7 seconds, scroll-stopping)
- value_proposition: string (what the viewer learns or feels)
- emotional_trigger: string (curiosity, fear, aspiration, humor, relatability)
- send_trigger: string (why someone would DM this to a friend)
- send_probability: "high" | "very_high" | "extreme"
- save_probability: "high" | "very_high" | "extreme"
- caption_seo_keywords: string[] (5-8 SEO keywords)
- formatNotes: string (AI image style guidance — describe the visual mood, lighting, color palette for background images. E.g. "soft morning light, dewy leaves, warm green tones" or "dramatic dark background with spotlight on subject")

REQUIRED MIX — follow this exactly:
- Option 1: Educational how-to carousel (${slideCount} slides teaching a step-by-step process)
- Option 2: Diagnosis/identification carousel (${slideCount} slides — "signs your plant has X" or "how to tell if...")
- Option 3: Listicle or before/after transformation carousel (${slideCount} slides)
- Option 4: Reel with shock/curiosity hook (15-30 seconds, visual reveal or time-lapse)
- Option 5: Community/relatability carousel OR reel (memes, "every plant parent knows...", relatable moments)

Make each idea HIGHLY SPECIFIC — not generic. Use real plant names, real problems, real scenarios. Every idea must be 100% original content, never repost.

Return ONLY the JSON object: { "options": [...] }`;
