import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getContentBuilderSystem } from './prompts.js';

interface StorySequence {
  slides: Array<{
    slideNumber: number;
    type: 'content' | 'poll' | 'question' | 'slider' | 'dm_trigger';
    content: string;
    interactiveElement?: {
      type: string;
      options?: string[];
      question?: string;
    };
  }>;
  dmTriggerKeyword: string;
  dmTriggerValue: string;
}

export async function buildStorySequence(
  topic: string,
  niche: string,
  dmKeyword: string,
  dmValue: string
): Promise<StorySequence> {
  return askClaudeJSON<StorySequence>({
    systemPrompt: getContentBuilderSystem(),
    userPrompt: `Create a 6-8 slide Instagram Story sequence for the "${niche}" niche.

Topic: ${topic}

Requirements:
- At least 2 interactive elements (poll, question box, slider)
- Build narrative tension across slides
- Final slide MUST be a DM trigger: "DM me '${dmKeyword}' for ${dmValue}"
- Each slide should be viewable in 5-7 seconds
- Use casual, conversational tone

Return as JSON with: slides (array of { slideNumber, type, content, interactiveElement? }), dmTriggerKeyword, dmTriggerValue`,
    maxTokens: 2048,
  });
}
