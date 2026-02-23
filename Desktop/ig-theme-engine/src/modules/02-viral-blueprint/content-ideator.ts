import { askClaudeJSON } from '../../integrations/claude-client.js';
import { VIRAL_BLUEPRINT_SYSTEM, viralBlueprintPrompt } from './prompts.js';
import { insertRow } from '../../database/db.js';

interface ContentIdea {
  type: 'carousel' | 'reel';
  title: string;
  hook: string;
  valueProposition: string;
  emotionalTrigger: string;
  sendTrigger: string;
  sendProbability: string;
  saveProbability: string;
  watchTimeStrategy: string;
  formatNotes: string;
  captionKeywords: string[];
  hashtagSuggestions: string[];
}

interface ViralBlueprint {
  ideas: ContentIdea[];
  viralFormulas: { name: string; description: string; whyItWorks: string }[];
  postingCadence: {
    postsPerWeek: number;
    reelsPerWeek: number;
    carouselsPerWeek: number;
    storiesPerDay: number;
    rationale: string;
  };
  contentSplit: {
    valueExamples: string[];
    promotionalExamples: string[];
  };
}

export async function generateViralBlueprint(niche: string, subNiche: string): Promise<ViralBlueprint> {
  const result = await askClaudeJSON<ViralBlueprint>({
    systemPrompt: VIRAL_BLUEPRINT_SYSTEM,
    userPrompt: viralBlueprintPrompt(niche, subNiche),
    maxTokens: 8192,
  });

  // Store all ideas in database
  for (const idea of result.ideas) {
    insertRow('content_ideas', {
      title: idea.title,
      content_type: idea.type,
      hook: idea.hook,
      value_proposition: idea.valueProposition,
      emotional_trigger: idea.emotionalTrigger,
      send_trigger: idea.sendTrigger,
      send_probability: idea.sendProbability,
      save_probability: idea.saveProbability,
      watch_time_strategy: idea.watchTimeStrategy,
      caption_seo_keywords: JSON.stringify(idea.captionKeywords),
      status: 'idea',
    });
  }

  return result;
}
