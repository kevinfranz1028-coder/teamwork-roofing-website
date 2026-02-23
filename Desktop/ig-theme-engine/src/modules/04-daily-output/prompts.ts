import { CONFIG } from '../../config/env.js';

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
