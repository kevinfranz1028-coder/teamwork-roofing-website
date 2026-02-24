import { getDb } from '../database/db.js';

interface AISettings {
  id: number;
  name: string;
  content_builder_system: string | null;
  carousel_design_instruction: string | null;
  reel_visual_instruction: string | null;
  image_style_prefix: string | null;
  image_style_suffix: string | null;
  image_negative_prompt: string | null;
  temperature: number;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export function getActiveAISettings(): AISettings | null {
  const db = getDb();
  const row = db.prepare(
    'SELECT * FROM ai_settings WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1'
  ).get() as AISettings | undefined;
  return row || null;
}

export function getSetting<T>(key: keyof AISettings, defaultValue: T): T {
  const settings = getActiveAISettings();
  if (!settings) return defaultValue;
  const value = settings[key];
  if (value === null || value === undefined) return defaultValue;
  return value as unknown as T;
}
