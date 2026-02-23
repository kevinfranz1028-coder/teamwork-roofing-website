import { askClaudeJSON } from '../../integrations/claude-client.js';
import { CONTENT_BUILDER_SYSTEM, carouselBuilderPrompt } from './prompts.js';
import { insertRow } from '../../database/db.js';
import { CONFIG } from '../../config/env.js';

interface CarouselScript {
  slides: Array<{
    slideNumber: number;
    type: 'hook' | 'value' | 'cta';
    headline: string;
    bodyText: string;
    designNotes: string;
    textHierarchy: string;
  }>;
  caption: {
    hookLine: string;
    body: string;
    cta: string;
    seoKeywords: string[];
    hashtags: string[];
  };
  dmTrigger: string;
  originalityCheck: string;
}

export async function buildCarousel(
  idea: { id: number; title: string; hook: string; formatNotes: string; captionKeywords: string[] },
  brandSystem: any
): Promise<CarouselScript> {
  const slideCount = CONFIG.content.carouselSlideCount;

  const result = await askClaudeJSON<CarouselScript>({
    systemPrompt: CONTENT_BUILDER_SYSTEM,
    userPrompt: carouselBuilderPrompt(idea, brandSystem, slideCount),
    maxTokens: 4096,
  });

  // Store the script in database
  insertRow('content_scripts', {
    idea_id: idea.id,
    content_type: 'carousel',
    script_json: JSON.stringify(result),
    caption: `${result.caption.hookLine}\n\n${result.caption.body}\n\n${result.caption.cta}`,
    caption_keywords: JSON.stringify(result.caption.seoKeywords),
    hashtags: JSON.stringify(result.caption.hashtags),
    cta_text: result.caption.cta,
    dm_trigger_keyword: result.dmTrigger,
    design_notes_json: JSON.stringify(result.slides.map(s => s.designNotes)),
  });

  return result;
}
