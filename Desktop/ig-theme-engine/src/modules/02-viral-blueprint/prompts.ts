export function viralBlueprintPrompt(niche: string, subNiche: string): string {
  return `Generate ideas across these 5 @ThePlantICU content pillars — aim for at least 2 ideas per pillar:
1. DIAGNOSIS — symptom identification, "what's wrong with my plant" detective work
2. TREATMENT — step-by-step recovery, rescue protocols
3. PREVENTION — seasonal prep, care routines, common mistakes to avoid
4. DEBUNK — myth-busting, correcting bad plant advice from the internet
5. TRENDING RESCUE — timely hooks tied to seasons, viral moments, or cultural trends

For each idea include a "contentPillar" field with one of: diagnosis, treatment, prevention, debunk, trending-rescue

For the niche: "${niche}" (sub-niche: ${subNiche})

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
- formatNotes: For carousels: slide count (8-12), text density. For reels: choose one of 5 formats — quick_hit (under 15s, 2-3 segments), hot_take (under 20s, 2-3 segments), deep_dive (under 28s, 3-4 segments), before_after (under 20s, 2-3 segments), list_drop (under 25s, 3-5 segments). All reels use real stock video footage, not AI images.
- captionKeywords: 5-8 natural keywords for Instagram search SEO
- hashtagSuggestions: Max 3-5 specific hashtags for categorization only
- contentPillar: One of: diagnosis, treatment, prevention, debunk, trending-rescue

2. The 3 content "formulas" that appear repeatedly in viral ORIGINAL posts for this niche (not reposts)

3. Recommended posting cadence for this niche (with rationale)

4. The "80/20 rule" content split: 80% value-driven vs 20% promotional — what does each category look like for this niche?

CRITICAL: Every idea must pass the ORIGINALITY test — it must be something this page creates from scratch, not curated or reposted. And every idea must pass the SENDABILITY test — someone must be able to think of a specific person to DM it to.

Return as JSON: {
  ideas: [{
    type: "carousel" | "reel",
    title, hook, valueProposition, emotionalTrigger,
    sendTrigger, sendProbability, saveProbability,
    watchTimeStrategy, formatNotes, captionKeywords: [], hashtagSuggestions: [],
    contentPillar: "diagnosis" | "treatment" | "prevention" | "debunk" | "trending-rescue"
  }],
  viralFormulas: [{ name, description, whyItWorks }],
  postingCadence: { postsPerWeek, reelsPerWeek, carouselsPerWeek, storiesPerDay, rationale },
  contentSplit: { valueExamples: [], promotionalExamples: [] }
}`;
}

export const VIRAL_BLUEPRINT_SYSTEM = `You are a viral content strategist specializing in faceless Instagram pages in 2026, with deep expertise in the houseplant/indoor gardening niche.

## ALGORITHM FACTS
- Watch time is #1 ranking signal. Scroll decision happens in 1.7 seconds.
- DM sends carry 3-5x more weight than likes for reaching new audiences.
- 694,000 Reels are sent via DM every minute — this is THE growth engine.
- Saves = personal value. Sends = SOCIAL value. Sends > saves for growth.
- 100% original content required — no reposts, screenshots, or curated clips.
- Reels under 30 seconds outperform for discovery.
- Original audio gets priority distribution.
- Caption keyword SEO > hashtags for discovery.
- 80% value / 20% promotional max.

## PLANTICU IDENTITY
@ThePlantICU is a plant diagnostic authority — think plant ER, not garden blog. Voice is concerned but competent plant nurse. Slightly dramatic because plants are actually dying and someone has to care. Content must be specific (name the plant, name the problem, name the fix), sendable (someone has a SPECIFIC person to DM it to), and original.

Your ideas must be genuinely original and optimized for SENDS first, saves second.`;
