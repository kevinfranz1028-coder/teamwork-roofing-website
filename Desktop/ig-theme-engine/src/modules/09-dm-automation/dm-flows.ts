import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getDb, insertRow, getRows } from '../../database/db.js';
import { CONFIG } from '../../config/env.js';
import { DM_AUTOMATION_SYSTEM, dmFlowPrompt, leadMagnetPrompt } from './prompts.js';

interface DMFlow {
  triggerKeyword: string;
  flowName: string;
  steps: Array<{
    stepNumber: number;
    delay: string;
    messageType: string;
    message: string;
    purpose: string;
    includesLink: boolean;
    linkUrl: string;
    capturesEmail: boolean;
  }>;
  emailCaptureStep: {
    stepNumber: number;
    method: string;
    incentive: string;
  };
  conversionGoal: string;
  expectedConversionRate: string;
  followUpSequence: Array<{
    day: number;
    message: string;
    purpose: string;
  }>;
}

interface LeadMagnet {
  name: string;
  type: string;
  description: string;
  dmKeyword: string;
  creationTime: string;
  conversionPotential: string;
  paidProductBridge: string;
}

export async function createDMFlow(triggerKeyword: string, valueOffer: string): Promise<DMFlow> {
  const flow = await askClaudeJSON<DMFlow>({
    systemPrompt: DM_AUTOMATION_SYSTEM,
    userPrompt: dmFlowPrompt(CONFIG.app.niche, triggerKeyword, valueOffer),
    maxTokens: 4096,
  });

  // Store in database
  insertRow('dm_flows', {
    trigger_keyword: flow.triggerKeyword,
    flow_name: flow.flowName,
    flow_steps_json: JSON.stringify(flow),
    is_active: 1,
  });

  return flow;
}

export async function generateLeadMagnets(): Promise<{ leadMagnets: LeadMagnet[] }> {
  return askClaudeJSON<{ leadMagnets: LeadMagnet[] }>({
    systemPrompt: DM_AUTOMATION_SYSTEM,
    userPrompt: leadMagnetPrompt(CONFIG.app.niche),
    maxTokens: 4096,
  });
}

export function getActiveDMFlows(): any[] {
  return getRows('dm_flows', { is_active: 1 });
}

export function getDMFlowByKeyword(keyword: string): any {
  const db = getDb();
  return db.prepare('SELECT * FROM dm_flows WHERE trigger_keyword = ? AND is_active = 1')
    .get(keyword.toLowerCase());
}

export function recordDMTrigger(flowId: number): void {
  const db = getDb();
  db.prepare('UPDATE dm_flows SET times_triggered = times_triggered + 1 WHERE id = ?').run(flowId);
}

export function recordDMConversion(flowId: number): void {
  const db = getDb();
  db.prepare('UPDATE dm_flows SET conversions = conversions + 1 WHERE id = ?').run(flowId);
}

// Email list management
export function addEmailSubscriber(email: string, source: string, leadMagnet?: string): void {
  const db = getDb();
  try {
    db.prepare('INSERT INTO email_list (email, source, lead_magnet) VALUES (?, ?, ?)')
      .run(email, source, leadMagnet || null);
  } catch {
    // Email already exists — ignore duplicate
  }
}

export function getEmailListStats(): { total: number; active: number; bySource: Record<string, number> } {
  const db = getDb();
  const total = db.prepare('SELECT COUNT(*) as count FROM email_list').get() as any;
  const active = db.prepare('SELECT COUNT(*) as count FROM email_list WHERE is_active = 1').get() as any;
  const sources = db.prepare('SELECT source, COUNT(*) as count FROM email_list GROUP BY source').all() as any[];

  const bySource: Record<string, number> = {};
  for (const s of sources) bySource[s.source] = s.count;

  return { total: total.count, active: active.count, bySource };
}
