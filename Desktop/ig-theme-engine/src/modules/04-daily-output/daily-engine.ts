import { askClaudeJSON } from '../../integrations/claude-client.js';
import { CONFIG } from '../../config/env.js';
import { getDb, insertRow } from '../../database/db.js';
import { format } from 'date-fns';

interface DailyPackage {
  date: string;
  trendAlert: { hasTrend: boolean; topic?: string; originalAngle?: string; urgency?: string };
  carousel: {
    idea: { title: string; hook: string; sendTrigger: string; whyItWillPerform: string };
    slides: Array<{ slideNumber: number; type: string; headline: string; bodyText: string; designNotes: string }>;
    caption: { hookLine: string; body: string; cta: string; seoKeywords: string[]; hashtags: string[] };
  };
  reel: {
    idea: { title: string; hook: string; sendTrigger: string; whyItWillPerform: string };
    hook: { onScreenText: string; visual: string; audio: string };
    body: Array<{ timestamp: number; onScreenText: string; voiceoverScript: string; visual: string }>;
    cta: { onScreenText: string; voiceover: string };
    totalLength: number;
    audioMood: string;
    caption: { hookLine: string; body: string; cta: string; seoKeywords: string[]; hashtags: string[] };
  };
  storySequence: {
    slides: Array<{
      slideNumber: number;
      type: 'content' | 'poll' | 'question' | 'slider' | 'dm_trigger';
      content: string;
      interactiveElement?: { type: string; options?: string[]; question?: string };
    }>;
    dmTriggerKeyword: string;
    dmTriggerValue: string;
  };
  designDirection: {
    colorPalette: { primary: string; secondary: string; accent: string; background: string };
    fontPairing: { headline: string; body: string };
    mood: string;
  };
}

export async function generateDailyPackage(): Promise<DailyPackage> {
  const today = format(new Date(), 'yyyy-MM-dd');
  const niche = CONFIG.app.niche;

  // Get recent performance data to inform today's content
  const db = getDb();
  const recentPerformance = db.prepare(`
    SELECT cs.content_type, avg(pc.sends_per_reach) as avg_sends, avg(pc.engagement_rate) as avg_engagement
    FROM published_content pc
    JOIN content_scripts cs ON pc.script_id = cs.id
    WHERE pc.published_at > datetime('now', '-14 days')
    GROUP BY cs.content_type
  `).all();

  const recentTopPerformers = db.prepare(`
    SELECT pc.*, cs.script_json
    FROM published_content pc
    JOIN content_scripts cs ON pc.script_id = cs.id
    WHERE pc.published_at > datetime('now', '-30 days')
    ORDER BY pc.sends_per_reach DESC
    LIMIT 3
  `).all();

  const performanceContext = recentPerformance.length > 0
    ? `\n\nRECENT PERFORMANCE DATA (last 14 days):\n${JSON.stringify(recentPerformance, null, 2)}\n\nTOP 3 PERFORMERS BY SENDS (last 30 days):\n${JSON.stringify(recentTopPerformers.map((p: any) => ({ sends_per_reach: p.sends_per_reach, engagement_rate: p.engagement_rate, content_type: p.content_type })), null, 2)}`
    : '\n\nNo performance data yet — this is early stage. Prioritize high-shareability content to build initial audience.';

  const result = await askClaudeJSON<DailyPackage>({
    systemPrompt: `You are the autonomous content operator for a "${niche}" Instagram theme page.

YOUR PRIME DIRECTIVES:
1. Every piece of content must be 100% ORIGINAL — never repost, never curate
2. Optimize for DM SENDS first (3-5x more valuable than likes for growth)
3. Hook in under 1.7 seconds (the scroll decision window)
4. Watch time is the #1 ranking factor — design for completion
5. Caption SEO keywords > hashtags for discovery
6. Include Story sequence with interactive elements + DM trigger
7. 80% value / 20% promotional max
8. Original audio preferred over trending sounds
${performanceContext}`,

    userPrompt: `Generate today's complete Daily Content Package.

Date: ${today}
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

Return as a single JSON object with all 5 sections.`,
    maxTokens: 6000,
  });

  // Store the generated content in the database
  const ideaId = insertRow('content_ideas', {
    title: result.carousel.idea.title,
    content_type: 'carousel',
    hook: result.carousel.idea.hook,
    send_trigger: result.carousel.idea.sendTrigger,
    caption_seo_keywords: JSON.stringify(result.carousel.caption.seoKeywords),
    status: 'scripted',
  });

  insertRow('content_scripts', {
    idea_id: ideaId,
    content_type: 'carousel',
    script_json: JSON.stringify(result.carousel),
    caption: `${result.carousel.caption.hookLine}\n\n${result.carousel.caption.body}\n\n${result.carousel.caption.cta}`,
    caption_keywords: JSON.stringify(result.carousel.caption.seoKeywords),
    hashtags: JSON.stringify(result.carousel.caption.hashtags),
    cta_text: result.carousel.caption.cta,
    dm_trigger_keyword: result.storySequence.dmTriggerKeyword,
    story_sequence_json: JSON.stringify(result.storySequence),
    design_notes_json: JSON.stringify(result.designDirection),
  });

  // Same for reel
  const reelIdeaId = insertRow('content_ideas', {
    title: result.reel.idea.title,
    content_type: 'reel',
    hook: result.reel.idea.hook,
    send_trigger: result.reel.idea.sendTrigger,
    status: 'scripted',
  });

  insertRow('content_scripts', {
    idea_id: reelIdeaId,
    content_type: 'reel',
    script_json: JSON.stringify(result.reel),
    caption: `${result.reel.caption.hookLine}\n\n${result.reel.caption.body}\n\n${result.reel.caption.cta}`,
    caption_keywords: JSON.stringify(result.reel.caption.seoKeywords),
    hashtags: JSON.stringify(result.reel.caption.hashtags),
    dm_trigger_keyword: result.storySequence.dmTriggerKeyword,
    story_sequence_json: JSON.stringify(result.storySequence),
    design_notes_json: JSON.stringify(result.designDirection),
  });

  return result;
}
