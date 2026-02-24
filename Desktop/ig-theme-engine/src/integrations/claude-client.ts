import Anthropic from '@anthropic-ai/sdk';
import { CONFIG } from '../config/env.js';
import { getSetting } from '../config/ai-settings.js';
import { withRetry } from '../utils/retry.js';

const client = new Anthropic({ apiKey: CONFIG.ai.apiKey });

interface ClaudeRequest {
  systemPrompt: string;
  userPrompt: string;
  maxTokens?: number;
  temperature?: number;
}

interface ClaudeResponse {
  text: string;
  inputTokens: number;
  outputTokens: number;
  cost: number; // estimated USD
}

export async function askClaude(request: ClaudeRequest): Promise<ClaudeResponse> {
  return withRetry(async () => {
    const response = await client.messages.create({
      model: CONFIG.ai.model,
      max_tokens: request.maxTokens || 4096,
      temperature: request.temperature ?? getSetting('temperature', 0.7),
      system: request.systemPrompt,
      messages: [{ role: 'user', content: request.userPrompt }],
    });

    const text = response.content
      .filter((block): block is Anthropic.TextBlock => block.type === 'text')
      .map(block => block.text)
      .join('\n');

    // Approximate cost (Sonnet 4.5 pricing — verify current rates)
    const inputCost = (response.usage.input_tokens / 1_000_000) * 3;
    const outputCost = (response.usage.output_tokens / 1_000_000) * 15;

    return {
      text,
      inputTokens: response.usage.input_tokens,
      outputTokens: response.usage.output_tokens,
      cost: inputCost + outputCost,
    };
  }, {
    maxAttempts: 3,
    delayMs: 2000,
    backoffMultiplier: 2,
    onRetry: (attempt, err) => {
      console.warn(`Claude API retry ${attempt}: ${err.message}`);
    }
  });
}

// Attempt to repair truncated JSON by closing open brackets/braces
function repairJSON(text: string): string {
  let cleaned = text.trim();
  // Remove trailing commas before closing brackets
  cleaned = cleaned.replace(/,\s*$/, '');
  // Count open vs close brackets
  let braces = 0;
  let brackets = 0;
  let inString = false;
  let escape = false;
  for (const ch of cleaned) {
    if (escape) { escape = false; continue; }
    if (ch === '\\') { escape = true; continue; }
    if (ch === '"') { inString = !inString; continue; }
    if (inString) continue;
    if (ch === '{') braces++;
    if (ch === '}') braces--;
    if (ch === '[') brackets++;
    if (ch === ']') brackets--;
  }
  // Close any unclosed structures
  while (brackets > 0) { cleaned += ']'; brackets--; }
  while (braces > 0) { cleaned += '}'; braces--; }
  return cleaned;
}

// Structured output helper — asks Claude to respond in JSON
export async function askClaudeJSON<T>(request: ClaudeRequest): Promise<T> {
  const enhancedSystem = request.systemPrompt +
    '\n\nIMPORTANT: Respond with valid JSON only. No markdown, no backticks, no preamble. Just the JSON.';

  const response = await askClaude({ ...request, systemPrompt: enhancedSystem });

  // Strip markdown code fences if present (```json ... ``` or ``` ... ```)
  let text = response.text.trim();
  text = text.replace(/^```(?:json)?\s*\n?/i, '').replace(/\n?```\s*$/, '').trim();

  // Try direct parse first
  try {
    return JSON.parse(text) as T;
  } catch {
    // Try extracting JSON array or object
    const arrayMatch = text.match(/\[[\s\S]*\]/);
    const objMatch = text.match(/\{[\s\S]*\}/);
    // Prefer whichever starts first in the text
    const match = arrayMatch && objMatch
      ? (text.indexOf('[') < text.indexOf('{') ? arrayMatch : objMatch)
      : arrayMatch || objMatch;

    if (match) {
      try {
        return JSON.parse(match[0]) as T;
      } catch {
        const repaired = repairJSON(match[0]);
        try {
          return JSON.parse(repaired) as T;
        } catch {}
      }
    }
    // Last resort: try repairing the full text
    try {
      return JSON.parse(repairJSON(text)) as T;
    } catch {
      throw new Error(`Failed to parse Claude response as JSON: ${text.slice(0, 200)}`);
    }
  }
}
