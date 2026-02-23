export const GROWTH_STRATEGY_SYSTEM = `You are an Instagram growth strategist specializing in the 2026 algorithm.

KEY PRINCIPLES:
- DM sends are the #1 growth lever (3-5x more valuable than likes)
- Watch time is the #1 ranking signal
- Consistency beats intensity — missing days hurts more than posting extra
- Engagement in first 30 minutes determines reach
- Stories maintain existing audience; posts/reels grow new audience
- Comment replies within 1 hour boost post in algorithm
- Cross-engagement with similar accounts signals community relevance`;

export function contentCalendarPrompt(niche: string, contentPillars: string[], postsPerWeek: number): string {
  return `Create a 4-week content calendar for a "${niche}" Instagram theme page.

Content pillars: ${contentPillars.join(', ')}
Posts per week: ${postsPerWeek}
Format: Rotate between carousels and reels, with daily stories

Return JSON:
{
  "weeks": [
    {
      "weekNumber": 1,
      "theme": "weekly theme",
      "days": [
        {
          "day": "Monday",
          "postType": "carousel|reel|rest",
          "pillar": "which content pillar",
          "ideaTitle": "content idea title",
          "postingTime": "HH:MM",
          "storyCount": 6,
          "storyTheme": "story theme for the day",
          "engagementFocus": "what engagement tactic to use"
        }
      ]
    }
  ],
  "pillarRotation": "explanation of how pillars rotate",
  "restDayStrategy": "what to do on non-posting days"
}`;
}

export function engagementPrompt(niche: string): string {
  return `Create a daily engagement protocol for a "${niche}" Instagram theme page.

Return JSON:
{
  "prePostEngagement": {
    "duration": "minutes before posting",
    "actions": ["specific engagement actions"]
  },
  "postPostEngagement": {
    "firstHour": ["actions in first 60 minutes after posting"],
    "ongoing": ["actions throughout the day"]
  },
  "commentTemplates": {
    "questionComments": ["template replies for questions"],
    "complimentComments": ["template replies for compliments"],
    "debateComments": ["template replies for disagreements"]
  },
  "storyEngagement": {
    "pollFrequency": "how often to use polls",
    "questionBoxFrequency": "how often",
    "dmTriggerFrequency": "how often"
  },
  "communityActions": {
    "accountsToEngageWith": "criteria for finding accounts",
    "engagementPerDay": "number of meaningful interactions",
    "hashtagStrategy": "how to find content to engage with"
  }
}`;
}
