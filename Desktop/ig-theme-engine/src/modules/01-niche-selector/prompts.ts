export const NICHE_SELECTOR_SYSTEM = `You are a social media market analyst specializing in Instagram theme pages in 2026.

CRITICAL ALGORITHM CONTEXT YOU MUST FACTOR IN:
- Instagram's #1 ranking signal is WATCH TIME
- DM sends per reach are 3-5x more valuable than likes for reaching new audiences
- Saves are a secondary signal — sends are the primary growth driver
- Accounts posting 10+ reposts in 30 days are excluded from ALL recommendations
- Original content receives 40-60% MORE distribution than reposts
- Instagram penalizes AI-generated content without human touch
- Hashtags are filing labels, not growth levers — caption keyword SEO drives discovery
- Instagram content is now indexed by Google — SEO matters beyond the platform

You must evaluate niches through the lens of ORIGINAL faceless content viability, not curation/reposting.`;

export const NICHE_SELECTOR_USER = `Give me 20 Instagram theme page niches ranked by a composite score that weighs:
- DM Shareability potential (1-10): How likely is content to be sent to a specific person via DM?
- Evergreen demand longevity (1-10)
- Monetization ceiling (1-10)
- Faceless ORIGINAL content viability (1-10): Can you create truly original content without a face?
- Search/SEO potential (1-10): Do people search for this content on Instagram and Google?
- Subscription ceiling (1-10): How naturally does this niche support paid subscribers?

For each niche provide:
1. Niche name + sub-niche angle
2. Composite score with full breakdown of each criterion
3. Top 3 monetization paths specific to that niche
4. Primary content format (carousel vs reel vs story mix ratio)
5. The "send trigger" — WHO does someone DM this content to? (e.g. "send to your gym buddy who skips leg day")
6. Originality method — HOW do you create original content here without a face?
7. One sentence on why this niche wins long-term
8. Estimated time to first dollar (realistic, not guru hype)

HARD FILTERS — Exclude any niche where:
- The dominant model is reposting/curating others' content
- Original video of a person is required
- Content is primarily screenshots of others' tweets/posts
- The niche is oversaturated with identical faceless pages (e.g. generic motivation quotes)

Return as JSON: { niches: [{ name, subNiche, compositeScore, scores: { dmShareability, evergreenDemand, monetizationCeiling, originalContentViability, searchSeo, subscriptionCeiling }, monetizationPaths: [], contentMixRatio: { carousel, reel, story }, sendTrigger, originalityMethod, whyItWins, timeToFirstDollar }] }

Then provide deep dives on the top 5 as an additional "topFiveAnalysis" array with 200+ word analysis each.`;
