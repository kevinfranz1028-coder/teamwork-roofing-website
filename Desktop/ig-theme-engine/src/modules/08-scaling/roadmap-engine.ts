import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getDb } from '../../database/db.js';
import { CONFIG } from '../../config/env.js';
import { SCALING_SYSTEM, roadmapPrompt } from './prompts.js';

interface ScalingRoadmap {
  currentPhase: { name: string; number: number; description: string };
  nextMilestone: { followers: number; estimatedWeeks: number; keyActions: string[] };
  weeklyTargets: {
    postsPerWeek: number;
    reelsPerWeek: number;
    storiesPerDay: number;
    engagementMinutesPerDay: number;
    targetSendsPerPost: number;
  };
  growthLevers: Array<{
    lever: string;
    impact: string;
    effort: string;
    description: string;
    priority: number;
  }>;
  blockers: Array<{ blocker: string; solution: string }>;
  phaseRoadmap: Array<{
    phase: number;
    followerRange: string;
    duration: string;
    focus: string;
    keyMetrics: string[];
    milestoneActions: string[];
  }>;
  automationOpportunities: Array<{
    task: string;
    tool: string;
    timeSaved: string;
  }>;
}

export async function generateRoadmap(currentFollowers = 0): Promise<ScalingRoadmap> {
  const db = getDb();

  // Get latest weekly scorecard data
  const weeklyData = db.prepare(`
    SELECT * FROM weekly_scorecard ORDER BY created_at DESC LIMIT 4
  `).all();

  return askClaudeJSON<ScalingRoadmap>({
    systemPrompt: SCALING_SYSTEM,
    userPrompt: roadmapPrompt(CONFIG.app.niche, currentFollowers, weeklyData),
    maxTokens: 6000,
  });
}

export function getCurrentPhase(followerCount: number): {
  phase: number;
  name: string;
  nextTarget: number;
} {
  if (followerCount < 1000) return { phase: 1, name: 'Foundation', nextTarget: 1000 };
  if (followerCount < 5000) return { phase: 2, name: 'Traction', nextTarget: 5000 };
  if (followerCount < 25000) return { phase: 3, name: 'Growth', nextTarget: 25000 };
  if (followerCount < 100000) return { phase: 4, name: 'Scale', nextTarget: 100000 };
  return { phase: 5, name: 'Empire', nextTarget: 250000 };
}
