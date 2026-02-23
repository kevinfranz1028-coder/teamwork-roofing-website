import { getDb } from '../database/db.js';
import { CONFIG } from './env.js';

export interface NicheConfig {
  id: number;
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
}

let cachedNiche: NicheConfig | null = null;

export function getActiveNiche(): NicheConfig | null {
  if (cachedNiche) return cachedNiche;

  const db = getDb();

  // Try selected niche from database first
  const selected = db.prepare('SELECT * FROM niches WHERE selected = 1').get() as any;
  if (selected) {
    const analysis = selected.analysis_json ? JSON.parse(selected.analysis_json) : {};
    cachedNiche = {
      id: selected.id,
      name: selected.name,
      subNiche: selected.sub_niche || '',
      compositeScore: selected.composite_score || 0,
      scores: {
        dmShareability: selected.dm_shareability || 0,
        evergreenDemand: selected.evergreen_demand || 0,
        monetizationCeiling: selected.monetization_ceiling || 0,
        originalContentViability: selected.originality_viability || 0,
        searchSeo: selected.search_seo_potential || 0,
        subscriptionCeiling: selected.subscription_ceiling || 0,
      },
      monetizationPaths: analysis.monetizationPaths || [],
      contentMixRatio: analysis.contentMixRatio || { carousel: 40, reel: 40, story: 20 },
      sendTrigger: analysis.sendTrigger || '',
      originalityMethod: analysis.originalityMethod || '',
    };
    return cachedNiche;
  }

  // Fallback to .env NICHE value
  if (CONFIG.app.niche) {
    const byName = db.prepare('SELECT * FROM niches WHERE name = ?').get(CONFIG.app.niche) as any;
    if (byName) {
      const analysis = byName.analysis_json ? JSON.parse(byName.analysis_json) : {};
      cachedNiche = {
        id: byName.id,
        name: byName.name,
        subNiche: byName.sub_niche || '',
        compositeScore: byName.composite_score || 0,
        scores: {
          dmShareability: byName.dm_shareability || 0,
          evergreenDemand: byName.evergreen_demand || 0,
          monetizationCeiling: byName.monetization_ceiling || 0,
          originalContentViability: byName.originality_viability || 0,
          searchSeo: byName.search_seo_potential || 0,
          subscriptionCeiling: byName.subscription_ceiling || 0,
        },
        monetizationPaths: analysis.monetizationPaths || [],
        contentMixRatio: analysis.contentMixRatio || { carousel: 40, reel: 40, story: 20 },
        sendTrigger: analysis.sendTrigger || '',
        originalityMethod: analysis.originalityMethod || '',
      };
      return cachedNiche;
    }
  }

  return null;
}

export function clearNicheCache(): void {
  cachedNiche = null;
}
