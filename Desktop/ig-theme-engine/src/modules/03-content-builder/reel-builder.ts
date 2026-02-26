import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getContentBuilderSystem, reelBuilderPrompt } from './prompts.js';
import { insertRow } from '../../database/db.js';
import type { ReelScriptV2 } from '../../rendering/types.js';

export async function buildReel(
  idea: { id: number; title: string; hook: string; formatNotes: string; captionKeywords: string[] },
  brandSystem: any
): Promise<ReelScriptV2> {
  const result = await askClaudeJSON<ReelScriptV2>({
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
