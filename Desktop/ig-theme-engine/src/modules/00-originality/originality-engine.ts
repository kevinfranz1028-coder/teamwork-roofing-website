import { askClaudeJSON } from '../../integrations/claude-client.js';

export interface OriginalityStrategy {
  primaryMethod: string;
  description: string;
  contentFormats: {
    carousels: string;
    reels: string;
    stories: string;
  };
  audioStrategy: string;
  visualStrategy: string;
  transformationRules: string[];
  redLines: string[];
}

export async function generateOriginalityStrategy(niche: string): Promise<OriginalityStrategy> {
  return askClaudeJSON<OriginalityStrategy>({
    systemPrompt: `You are an Instagram content strategist specializing in original faceless content creation.

CRITICAL CONTEXT — Instagram 2026 Algorithm:
- Accounts posting 10+ reposts in 30 days are EXCLUDED from all recommendations
- Instagram uses visual fingerprinting: content with 70%+ similarity to existing content is flagged
- AI-generated content without human touch is downranked
- Original audio receives distribution priority over trending sounds
- Adam Mosseri's Dec 2025 memo prioritizes "raw, real human content"

Your job: Design an originality architecture that ensures every piece of content this page produces is genuinely original and will never trigger the aggregator penalty.`,

    userPrompt: `Design a complete Originality Architecture for a faceless Instagram theme page in the "${niche}" niche.

This must answer:
1. What is the PRIMARY method for creating original content at scale without showing a face?
2. How does each format (carousel, reel, story) stay original?
3. What is the audio strategy? (Original voiceover, original sound design, etc.)
4. What is the visual strategy? (Original graphics, unique data visualizations, custom templates, etc.)
5. What are the transformation rules — the specific checklist that ensures every piece hits 30%+ originality?
6. What are the absolute red lines — things this page must NEVER do?

Return as a JSON object with keys: primaryMethod, description, contentFormats (object with carousels, reels, stories), audioStrategy, visualStrategy, transformationRules (array), redLines (array).`
  });
}
