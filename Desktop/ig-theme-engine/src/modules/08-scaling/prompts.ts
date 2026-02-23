export const SCALING_SYSTEM = `You are a growth strategist for Instagram theme page businesses. You help page owners scale from 0 to 100K+ followers with a clear, phase-based roadmap.

SCALING PHASES:
- Phase 1 (0-1K): Foundation — brand, content system, first 100 true fans
- Phase 2 (1K-5K): Traction — viral content discovery, first revenue
- Phase 3 (5K-25K): Growth — consistency compounding, multiple revenue streams
- Phase 4 (25K-100K): Scale — team, automation, cross-platform, product launches
- Phase 5 (100K+): Empire — brand deals, product ecosystem, platform independence`;

export function roadmapPrompt(niche: string, currentFollowers: number, weeklyData: any): string {
  return `Create a detailed scaling roadmap for a "${niche}" Instagram theme page.

Current followers: ${currentFollowers}
Recent performance: ${JSON.stringify(weeklyData)}

Return JSON:
{
  "currentPhase": { "name": "phase name", "number": 1, "description": "where you are" },
  "nextMilestone": { "followers": number, "estimatedWeeks": number, "keyActions": ["action 1"] },
  "weeklyTargets": {
    "postsPerWeek": number,
    "reelsPerWeek": number,
    "storiesPerDay": number,
    "engagementMinutesPerDay": number,
    "targetSendsPerPost": number
  },
  "growthLevers": [
    { "lever": "name", "impact": "high|medium|low", "effort": "high|medium|low", "description": "how to execute", "priority": 1 }
  ],
  "blockers": [
    { "blocker": "what's holding growth back", "solution": "how to fix it" }
  ],
  "phaseRoadmap": [
    { "phase": 1, "followerRange": "0-1K", "duration": "X weeks", "focus": "main focus", "keyMetrics": ["metric"], "milestoneActions": ["action"] }
  ],
  "automationOpportunities": [
    { "task": "what to automate", "tool": "recommended tool", "timeSaved": "hours/week" }
  ]
}`;
}
