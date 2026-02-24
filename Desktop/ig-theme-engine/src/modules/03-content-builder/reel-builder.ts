import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getContentBuilderSystem, reelBuilderPrompt } from './prompts.js';
import { insertRow } from '../../database/db.js';

interface ReelScript {
  hook: {
    onScreenText: string;
    visual: string;
    audio: string;
  };
  body: Array<{
    timestamp: number;
    onScreenText: string;
    voiceoverScript: string;
    visual: string;
    pacing: 'fast' | 'medium' | 'slow';
  }>;
  cta: {
    onScreenText: string;
    voiceover: string;
    visual: string;
  };
  totalLength: number;
  audioMood: string;
  captionKeywords: string[];
  hashtags: string[];
}

export async function buildReel(
  idea: { id: number; title: string; hook: string; formatNotes: string; captionKeywords: string[] },
  brandSystem: any
): Promise<ReelScript> {
  const result = await askClaudeJSON<ReelScript>({
    systemPrompt: getContentBuilderSystem(),
    userPrompt: reelBuilderPrompt(idea, brandSystem),
    maxTokens: 4096,
  });

  // Store the script in database
  insertRow('content_scripts', {
    idea_id: idea.id,
    content_type: 'reel',
    script_json: JSON.stringify(result),
    caption: result.captionKeywords.join(', '),
    caption_keywords: JSON.stringify(result.captionKeywords),
    hashtags: JSON.stringify(result.hashtags),
    cta_text: result.cta.onScreenText,
  });

  return result;
}
