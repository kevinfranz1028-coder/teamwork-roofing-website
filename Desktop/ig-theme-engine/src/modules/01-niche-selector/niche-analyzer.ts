import { askClaudeJSON } from '../../integrations/claude-client.js';
import { NICHE_SELECTOR_SYSTEM, NICHE_SELECTOR_USER } from './prompts.js';
import { getDb, insertRow } from '../../database/db.js';

interface NicheResult {
  name: string;
  subNiche: string;
  compositeScore: number;
  scores: {
    dmShareability: number;
    evergreenDemand: number;
    monetizationCeiling: number;
    originalContentViability: number;
    searchSeo: number;
    subscriptionCeiling: number;
  };
  monetizationPaths: string[];
  contentMixRatio: { carousel: number; reel: number; story: number };
  sendTrigger: string;
  originalityMethod: string;
  whyItWins: string;
  timeToFirstDollar: string;
}

interface NicheAnalysis {
  niches: NicheResult[];
  topFiveAnalysis: { name: string; analysis: string }[];
}

export async function analyzeNiches(): Promise<NicheAnalysis> {
  const result = await askClaudeJSON<NicheAnalysis>({
    systemPrompt: NICHE_SELECTOR_SYSTEM,
    userPrompt: NICHE_SELECTOR_USER,
    maxTokens: 16000,
  });

  // Store all niches in database
  for (const niche of result.niches) {
    insertRow('niches', {
      name: niche.name,
      sub_niche: niche.subNiche,
      composite_score: niche.compositeScore,
      shareability: niche.scores.dmShareability,
      evergreen_demand: niche.scores.evergreenDemand,
      monetization_ceiling: niche.scores.monetizationCeiling,
      faceless_viability: niche.scores.originalContentViability,
      originality_viability: niche.scores.originalContentViability,
      dm_shareability: niche.scores.dmShareability,
      search_seo_potential: niche.scores.searchSeo,
      subscription_ceiling: niche.scores.subscriptionCeiling,
      analysis_json: JSON.stringify(niche),
    });
  }

  return result;
}

export function selectNiche(nicheId: number): void {
  const db = getDb();
  db.prepare('UPDATE niches SET selected = 0').run();
  db.prepare('UPDATE niches SET selected = 1 WHERE id = ?').run(nicheId);
}
