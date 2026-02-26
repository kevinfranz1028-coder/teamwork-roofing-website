import { getDb } from './db.js';

interface Migration {
  version: number;
  name: string;
  up: string;
}

const MIGRATIONS: Migration[] = [
  {
    version: 1,
    name: 'initial_schema',
    up: `-- Initial schema is applied via schema.ts on first init`,
  },
  {
    version: 2,
    name: 'add_api_cost_tracking',
    up: `
      CREATE TABLE IF NOT EXISTS api_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        endpoint TEXT NOT NULL,
        input_tokens INTEGER DEFAULT 0,
        output_tokens INTEGER DEFAULT 0,
        estimated_cost REAL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `,
  },
  {
    version: 3,
    name: 'add_content_versions',
    up: `
      ALTER TABLE content_scripts ADD COLUMN version INTEGER DEFAULT 1;
      ALTER TABLE content_scripts ADD COLUMN parent_script_id INTEGER REFERENCES content_scripts(id);
    `,
  },
  {
    version: 4,
    name: 'add_rendered_assets',
    up: `
      CREATE TABLE IF NOT EXISTS rendered_assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER REFERENCES content_scripts(id),
        content_type TEXT NOT NULL,
        local_paths TEXT NOT NULL,
        public_urls TEXT DEFAULT '[]',
        rendered_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `,
  },
  {
    version: 5,
    name: 'add_content_option_batches',
    up: `
      ALTER TABLE content_ideas ADD COLUMN batch_id TEXT;
      CREATE TABLE IF NOT EXISTS content_option_batches (
        id TEXT PRIMARY KEY,
        status TEXT DEFAULT 'generating' CHECK(status IN ('generating', 'ready', 'selected', 'expired')),
        option_count INTEGER DEFAULT 5,
        selected_idea_id INTEGER REFERENCES content_ideas(id),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `,
  },
  {
    version: 6,
    name: 'add_calendar_indexes',
    up: `
      CREATE INDEX IF NOT EXISTS idx_calendar_date_status ON content_calendar(scheduled_date, status);
      CREATE INDEX IF NOT EXISTS idx_calendar_script ON content_calendar(script_id);
    `,
  },
  {
    version: 7,
    name: 'add_creative_briefs',
    up: `
      CREATE TABLE IF NOT EXISTS creative_briefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        notes TEXT,
        competitor_links TEXT,
        content_angles TEXT,
        mood_themes TEXT,
        visual_style TEXT,
        target_emotions TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `,
  },
  {
    version: 8,
    name: 'add_ai_settings',
    up: `
      CREATE TABLE IF NOT EXISTS ai_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        content_builder_system TEXT,
        carousel_design_instruction TEXT,
        reel_visual_instruction TEXT,
        image_style_prefix TEXT,
        image_style_suffix TEXT,
        image_negative_prompt TEXT,
        temperature REAL DEFAULT 0.7,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `,
  },
  {
    version: 9,
    name: 'add_visual_quality_log',
    up: `
      CREATE TABLE IF NOT EXISTS visual_quality_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT NOT NULL,
        content_type TEXT NOT NULL,
        segment_type TEXT,
        prompt TEXT NOT NULL,
        quality_score INTEGER NOT NULL,
        issues TEXT,
        retry_count INTEGER DEFAULT 0,
        final_prompt TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
      CREATE INDEX IF NOT EXISTS idx_quality_log_model ON visual_quality_log(model);
      CREATE INDEX IF NOT EXISTS idx_quality_log_score ON visual_quality_log(quality_score);
    `,
  },
  {
    version: 10,
    name: 'add_visual_intelligence_ai_settings',
    up: `
      ALTER TABLE ai_settings ADD COLUMN default_image_model TEXT DEFAULT 'flux-2-pro';
      ALTER TABLE ai_settings ADD COLUMN default_video_model TEXT DEFAULT 'kling-2.6-pro';
      ALTER TABLE ai_settings ADD COLUMN enable_video_generation BOOLEAN DEFAULT 1;
      ALTER TABLE ai_settings ADD COLUMN video_motion_style TEXT;
      ALTER TABLE ai_settings ADD COLUMN quality_gate_enabled BOOLEAN DEFAULT 1;
      ALTER TABLE ai_settings ADD COLUMN quality_gate_min_score INTEGER DEFAULT 7;
      ALTER TABLE ai_settings ADD COLUMN hook_visual_style TEXT;
      ALTER TABLE ai_settings ADD COLUMN body_visual_style TEXT;
      ALTER TABLE ai_settings ADD COLUMN cta_visual_style TEXT;
      ALTER TABLE ai_settings ADD COLUMN camera_body TEXT DEFAULT 'Canon R5';
      ALTER TABLE ai_settings ADD COLUMN default_lens TEXT DEFAULT '100mm f/2.8L Macro IS';
      ALTER TABLE ai_settings ADD COLUMN default_lighting TEXT DEFAULT 'soft north-facing window light with warm fill';
      ALTER TABLE ai_settings ADD COLUMN default_color_profile TEXT DEFAULT 'Kodak Portra 400';
    `,
  },
  {
    version: 11,
    name: 'expand_api_costs',
    up: `
      ALTER TABLE api_costs ADD COLUMN provider TEXT;
      ALTER TABLE api_costs ADD COLUMN category TEXT;
      ALTER TABLE api_costs ADD COLUMN model TEXT;
      ALTER TABLE api_costs ADD COLUMN description TEXT;
      ALTER TABLE api_costs ADD COLUMN idea_id INTEGER;
      ALTER TABLE api_costs ADD COLUMN duration_ms INTEGER;
    `,
  },
  {
    version: 12,
    name: 'add_project_label_to_api_costs',
    up: `
      ALTER TABLE api_costs ADD COLUMN project_label TEXT;
      CREATE INDEX IF NOT EXISTS idx_api_costs_project ON api_costs(project_label);
    `,
  },
  {
    version: 13,
    name: 'add_pexels_clips',
    up: `
      CREATE TABLE IF NOT EXISTS pexels_clips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pexels_id INTEGER NOT NULL,
        media_type TEXT NOT NULL CHECK(media_type IN ('video', 'photo')),
        search_query TEXT,
        photographer TEXT,
        pexels_url TEXT,
        used_at TEXT DEFAULT (datetime('now')),
        script_id INTEGER,
        segment_index INTEGER
      );
      CREATE INDEX IF NOT EXISTS idx_pexels_clips_media_type ON pexels_clips(media_type);
      CREATE INDEX IF NOT EXISTS idx_pexels_clips_used_at ON pexels_clips(used_at);
      CREATE INDEX IF NOT EXISTS idx_pexels_clips_pexels_id ON pexels_clips(pexels_id);
    `,
  },
  {
    version: 14,
    name: 'add_pexels_style_settings',
    up: `
      ALTER TABLE ai_settings ADD COLUMN pexels_video_style_terms TEXT;
      ALTER TABLE ai_settings ADD COLUMN pexels_photo_style_terms TEXT;
      ALTER TABLE ai_settings ADD COLUMN pexels_exclude_terms TEXT;
    `,
  },
];

export function runMigrations(): void {
  const db = getDb();

  // Create migrations tracking table
  db.exec(`
    CREATE TABLE IF NOT EXISTS _migrations (
      version INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  const applied = db.prepare('SELECT version FROM _migrations').all() as { version: number }[];
  const appliedVersions = new Set(applied.map(m => m.version));

  for (const migration of MIGRATIONS) {
    if (appliedVersions.has(migration.version)) continue;
    if (migration.version === 1) {
      // Version 1 is the initial schema, just mark it as applied
      db.prepare('INSERT INTO _migrations (version, name) VALUES (?, ?)')
        .run(migration.version, migration.name);
      continue;
    }

    try {
      db.exec(migration.up);
      db.prepare('INSERT INTO _migrations (version, name) VALUES (?, ?)')
        .run(migration.version, migration.name);
      console.log(`Migration ${migration.version} (${migration.name}) applied.`);
    } catch (err: any) {
      // Skip if column/table already exists
      if (err.message.includes('duplicate column') || err.message.includes('already exists')) {
        db.prepare('INSERT INTO _migrations (version, name) VALUES (?, ?)')
          .run(migration.version, migration.name);
      } else {
        console.error(`Migration ${migration.version} failed:`, err.message);
      }
    }
  }
}
