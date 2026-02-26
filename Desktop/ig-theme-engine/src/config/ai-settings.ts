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
  default_image_model: string | null;
  default_video_model: string | null;
  enable_video_generation: number | null;
  video_motion_style: string | null;
  quality_gate_enabled: number | null;
  quality_gate_min_score: number | null;
  hook_visual_style: string | null;
  body_visual_style: string | null;
  cta_visual_style: string | null;
  camera_body: string | null;
  default_lens: string | null;
  default_lighting: string | null;
  default_color_profile: string | null;
  pexels_video_style_terms: string | null;
  pexels_photo_style_terms: string | null;
  pexels_exclude_terms: string | null;
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
