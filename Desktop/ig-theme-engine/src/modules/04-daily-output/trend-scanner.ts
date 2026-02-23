import { askClaudeJSON } from '../../integrations/claude-client.js';
import { CONFIG } from '../../config/env.js';

interface TrendAlert {
  hasTrend: boolean;
  trends: Array<{
    topic: string;
    relevance: 'high' | 'medium' | 'low';
    originalAngle: string;
    urgency: 'post_today' | 'post_this_week' | 'monitor';
    contentType: 'carousel' | 'reel' | 'story';
    hookIdea: string;
    whyItMatters: string;
  }>;
}

/**
 * Scan for trending topics relevant to the niche
 * Uses Claude's knowledge to identify seasonal, cultural, and evergreen trends
 */
export async function scanTrends(): Promise<TrendAlert> {
  const today = new Date();
  const month = today.toLocaleString('en-US', { month: 'long' });
  const dayOfWeek = today.toLocaleString('en-US', { weekday: 'long' });

  return askClaudeJSON<TrendAlert>({
    systemPrompt: `You are a trend analyst for a "${CONFIG.app.niche}" Instagram theme page. Identify timely content opportunities.

Consider:
- Seasonal relevance (current month: ${month})
- Day of week patterns (today: ${dayOfWeek})
- Recurring cultural moments and awareness days
- Evergreen topics with seasonal spikes
- Platform-wide Instagram trends that can be adapted to this niche
- News/events that create content opportunities

IMPORTANT: Only suggest trends where the page can create 100% ORIGINAL content with a unique angle (30%+ new perspective). Never suggest reposting or riding someone else's content.`,

    userPrompt: `Scan for trending topics relevant to the "${CONFIG.app.niche}" niche for today (${today.toISOString().split('T')[0]}).

Return JSON:
{
  "hasTrend": true/false,
  "trends": [
    {
      "topic": "the trending topic",
      "relevance": "high|medium|low",
      "originalAngle": "the unique angle this page should take",
      "urgency": "post_today|post_this_week|monitor",
      "contentType": "carousel|reel|story",
      "hookIdea": "specific hook for this trend",
      "whyItMatters": "why the audience cares"
    }
  ]
}

If no relevant trends exist today, return hasTrend: false with an empty trends array. Don't force it.`,
    maxTokens: 2048,
  });
}
