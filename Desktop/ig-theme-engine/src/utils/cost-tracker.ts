import { getDb } from '../database/db.js';

export interface CostEntry {
  provider: string;
  category: string;
  endpoint: string;
  model: string;
  description: string;
  inputTokens?: number;
  outputTokens?: number;
  estimatedCost: number;
  ideaId?: number;
  durationMs?: number;
  projectLabel?: string;
}

export function logApiCost(entry: CostEntry): void {
  try {
    const db = getDb();
    db.prepare(`
      INSERT INTO api_costs (endpoint, input_tokens, output_tokens, estimated_cost, provider, category, model, description, idea_id, duration_ms, project_label)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      entry.endpoint,
      entry.inputTokens ?? 0,
      entry.outputTokens ?? 0,
      entry.estimatedCost,
      entry.provider,
      entry.category,
      entry.model,
      entry.description,
      entry.ideaId ?? null,
      entry.durationMs ?? null,
      entry.projectLabel ?? null,
    );
  } catch (err: any) {
    console.warn(`[Cost Tracker] Failed to log cost: ${err.message}`);
  }
}
