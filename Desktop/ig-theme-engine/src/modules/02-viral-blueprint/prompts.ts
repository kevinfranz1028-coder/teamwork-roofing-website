export function viralBlueprintPrompt(niche: string, subNiche: string): string {
  return `For the niche: "${niche}" (sub-niche: ${subNiche})

Analyze the content patterns of top-performing ORIGINAL theme pages in this space and give me:

1. 15 viral content ideas broken into:
   - 8 carousel concepts (optimized for dwell time + saves)
   - 7 reel concepts (optimized for sends/DM shares + watch time)

For EACH idea include:
- hook: First line/frame — must stop the scroll in under 1.7 seconds
- valueProposition: Why will they send/save this?
- emotionalTrigger: (curiosity, fear, aspiration, validation, shock, humor, relatability)
- sendTrigger: Exactly WHO would someone DM this to? What would their message say? If you can't answer this clearly, rework the idea.
- sendProbability: (high / very_high / extreme)
- saveProbability: (high / very_high / extreme)
- watchTimeStrategy: How does this hold attention through completion?
- formatNotes: For carousels: slide count (8-12), text density. For reels: length in seconds (under 30 for discovery), text overlay style
- captionKeywords: 5-8 natural keywords for Instagram search SEO
- hashtagSuggestions: Max 3-5 specific hashtags for categorization only

2. The 3 content "formulas" that appear repeatedly in viral ORIGINAL posts for this niche (not reposts)

3. Recommended posting cadence for this niche (with rationale)

4. The "80/20 rule" content split: 80% value-driven vs 20% promotional — what does each category look like for this niche?

CRITICAL: Every idea must pass the ORIGINALITY test — it must be something this page creates from scratch, not curated or reposted. And every idea must pass the SENDABILITY test — someone must be able to think of a specific person to DM it to.

Return as JSON: {
  ideas: [{
    type: "carousel" | "reel",
    title, hook, valueProposition, emotionalTrigger,
    sendTrigger, sendProbability, saveProbability,
    watchTimeStrategy, formatNotes, captionKeywords: [], hashtagSuggestions: []
  }],
  viralFormulas: [{ name, description, whyItWorks }],
  postingCadence: { postsPerWeek, reelsPerWeek, carouselsPerWeek, storiesPerDay, rationale },
  contentSplit: { valueExamples: [], promotionalExamples: [] }
}`;
}

export const VIRAL_BLUEPRINT_SYSTEM = `You are a viral content strategist with deep knowledge of Instagram's 2026 algorithm.

KEY ALGORITHM FACTS YOU MUST USE:
- Watch time is the #1 ranking signal. Users decide to scroll in 1.7 seconds.
- DM sends carry 3-5x more weight than likes for reaching new audiences.
- 694,000 Reels are sent via DM every minute — this is the growth engine.
- Saves indicate personal value, but sends indicate SOCIAL value — sends > saves.
- Content must be 100% original — no reposts, no screenshots, no curated clips.
- Reels under 30 seconds outperform for discovery. 30-90 seconds for existing followers.
- Carousels with 8-12 slides outperform shorter ones (more dwell time).
- Original audio gets priority distribution over trending sounds.
- Caption keyword SEO drives more discovery than hashtags.
- Instagram penalizes overly promotional content — 80% value / 20% promotional max.

Your content ideas must be genuinely original and optimized for SENDS first, saves second.`;
