import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getContentBuilderSystem, reelBuilderPrompt } from './prompts.js';
import { insertRow } from '../../database/db.js';

interface ReelScript {
  hook: {
    onScreenText: string;
    visual: string;
    voiceoverScript: string;
  };
  body: Array<{
    timestamp: number;
    onScreenText: string;
    voiceoverScript: string;
    visual: string;
    pacing: 'fast' | 'medium' | 'slow';
    segmentType: string;
    durationSeconds: number;
  }>;
  cta: {
    onScreenText: string;
    voiceoverScript: string;
    visual: string;
  };
  voiceoverText: string;
  totalLength: number;
  audioMood: string;
  caption: {
    hookLine: string;
    body: string;
    cta: string;
    seoKeywords: string[];
    hashtags: string[];
  };
  dmTrigger: string;
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
  const caption = result.caption || {} as any;
  insertRow('content_scripts', {
    idea_id: idea.id,
    content_type: 'reel',
    script_json: JSON.stringify(result),
    caption: `${caption.hookLine || ''}\n\n${caption.body || ''}\n\n${caption.cta || ''}`,
    caption_keywords: JSON.stringify(caption.seoKeywords || []),
    hashtags: JSON.stringify(caption.hashtags || []),
    cta_text: result.cta?.onScreenText || '',
    dm_trigger_keyword: result.dmTrigger || '',
  });

  return result;
}
