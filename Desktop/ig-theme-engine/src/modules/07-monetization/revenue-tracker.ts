import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getDb, getRows } from '../../database/db.js';
import { CONFIG } from '../../config/env.js';
import { MONETIZATION_SYSTEM, revenueStrategyPrompt } from './prompts.js';

interface RevenueStrategy {
  currentPhase: string;
  immediateActions: Array<{
    action: string;
    expectedRevenue: string;
    timeToImplement: string;
    difficulty: string;
  }>;
  revenueStreams: Array<{
    stream: string;
    type: string;
    description: string;
    monthlyPotential: string;
    followerThreshold: number;
    setupSteps: string[];
    priority: number;
  }>;
  digitalProductIdeas: Array<{
    name: string;
    type: string;
    price: string;
    description: string;
  }>;
  affiliateOpportunities: Array<{
    brand: string;
    commission: string;
    relevance: string;
    integrationMethod: string;
  }>;
  milestones: Array<{
    followers: number;
    monthlyRevenue: string;
    enabledStreams: string[];
  }>;
}

export async function generateRevenueStrategy(followerCount = 0): Promise<RevenueStrategy> {
  const currentRevenue = getRows('revenue') as any[];

  const bySource = currentRevenue.reduce((acc: Record<string, number>, r: any) => {
    acc[r.source] = (acc[r.source] || 0) + r.amount;
    return acc;
  }, {});

  const revenueSummary = Object.entries(bySource).map(([source, total]) => ({
    source,
    total,
  }));

  return askClaudeJSON<RevenueStrategy>({
    systemPrompt: MONETIZATION_SYSTEM,
    userPrompt: revenueStrategyPrompt(CONFIG.app.niche, followerCount, revenueSummary),
    maxTokens: 6000,
  });
}

export function getRevenueOverview(): {
  total: number;
  thisMonth: number;
  lastMonth: number;
  bySource: Record<string, number>;
  recentEntries: any[];
} {
  const db = getDb();

  const total = db.prepare('SELECT COALESCE(SUM(amount), 0) as total FROM revenue').get() as any;
  const thisMonth = db.prepare(
    "SELECT COALESCE(SUM(amount), 0) as total FROM revenue WHERE date >= date('now', 'start of month')"
  ).get() as any;
  const lastMonth = db.prepare(
    "SELECT COALESCE(SUM(amount), 0) as total FROM revenue WHERE date >= date('now', 'start of month', '-1 month') AND date < date('now', 'start of month')"
  ).get() as any;

  const sources = db.prepare(
    'SELECT source, SUM(amount) as total FROM revenue GROUP BY source ORDER BY total DESC'
  ).all() as any[];

  const bySource: Record<string, number> = {};
  for (const s of sources) bySource[s.source] = s.total;

  const recentEntries = db.prepare(
    'SELECT * FROM revenue ORDER BY date DESC LIMIT 20'
  ).all();

  return {
    total: total.total,
    thisMonth: thisMonth.total,
    lastMonth: lastMonth.total,
    bySource,
    recentEntries,
  };
}
