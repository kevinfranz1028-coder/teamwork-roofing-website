import { askClaudeJSON } from '../../integrations/claude-client.js';
import { CONFIG } from '../../config/env.js';
import { GROWTH_STRATEGY_SYSTEM, engagementPrompt } from './prompts.js';

interface EngagementProtocol {
  prePostEngagement: {
    duration: string;
    actions: string[];
  };
  postPostEngagement: {
    firstHour: string[];
    ongoing: string[];
  };
  commentTemplates: {
    questionComments: string[];
    complimentComments: string[];
    debateComments: string[];
  };
  storyEngagement: {
    pollFrequency: string;
    questionBoxFrequency: string;
    dmTriggerFrequency: string;
  };
  communityActions: {
    accountsToEngageWith: string;
    engagementPerDay: string;
    hashtagStrategy: string;
  };
}

let cachedProtocol: EngagementProtocol | null = null;

export async function generateEngagementProtocol(): Promise<EngagementProtocol> {
  const result = await askClaudeJSON<EngagementProtocol>({
    systemPrompt: GROWTH_STRATEGY_SYSTEM,
    userPrompt: engagementPrompt(CONFIG.app.niche),
    maxTokens: 4096,
  });

  cachedProtocol = result;
  return result;
}

export function getEngagementProtocol(): EngagementProtocol | null {
  return cachedProtocol;
}

/**
 * Generate smart reply suggestions for a comment
 */
export async function generateCommentReply(
  comment: string,
  postContext: string
): Promise<{ reply: string; tone: string }> {
  return askClaudeJSON({
    systemPrompt: `You manage engagement for a "${CONFIG.app.niche}" Instagram page.
Write replies that are: warm, knowledgeable, encourage further engagement, and subtly drive saves/sends.
Never be salesy. Be genuinely helpful. Keep replies under 50 words.`,
    userPrompt: `Post context: ${postContext}
Comment: "${comment}"

Return JSON: { "reply": "your reply text", "tone": "helpful|humorous|empathetic|educational" }`,
    maxTokens: 256,
  });
}
