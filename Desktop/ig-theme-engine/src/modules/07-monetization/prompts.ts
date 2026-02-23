export const MONETIZATION_SYSTEM = `You are an Instagram monetization strategist. You help theme page owners build sustainable revenue streams.

KEY PRINCIPLES:
- Revenue should come from multiple streams (never rely on one)
- Digital products have the highest margin
- Affiliate revenue scales with trust and specificity
- Subscriptions provide predictable income
- Sponsorships should be niche-aligned and rare (maintain trust)
- Email list is the most valuable long-term asset
- Monetize at 1K followers, not 10K — small audiences buy too`;

export function revenueStrategyPrompt(niche: string, followerCount: number, currentRevenue: any[]): string {
  return `Create a monetization roadmap for a "${niche}" Instagram theme page.

Current followers: ${followerCount}
Current revenue streams: ${currentRevenue.length > 0 ? JSON.stringify(currentRevenue) : 'None yet'}

Return JSON:
{
  "currentPhase": "early|growth|established",
  "immediateActions": [
    { "action": "what to do", "expectedRevenue": "$X/month", "timeToImplement": "X days", "difficulty": "easy|medium|hard" }
  ],
  "revenueStreams": [
    {
      "stream": "stream name",
      "type": "affiliate|digital_product|subscription|sponsorship|shoutout|service",
      "description": "how it works for this niche",
      "monthlyPotential": "$X-$Y",
      "followerThreshold": number,
      "setupSteps": ["step 1", "step 2"],
      "priority": 1
    }
  ],
  "digitalProductIdeas": [
    { "name": "product name", "type": "ebook|template|course|checklist|toolkit", "price": "$X", "description": "what it contains" }
  ],
  "affiliateOpportunities": [
    { "brand": "brand/product name", "commission": "X%", "relevance": "why it fits this niche", "integrationMethod": "how to promote naturally" }
  ],
  "milestones": [
    { "followers": number, "monthlyRevenue": "$X", "enabledStreams": ["stream names"] }
  ]
}`;
}
