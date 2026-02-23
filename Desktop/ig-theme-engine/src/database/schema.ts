export const SCHEMA = `
  -- Niche analysis results
  CREATE TABLE IF NOT EXISTS niches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sub_niche TEXT,
    composite_score REAL,
    shareability INTEGER,
    evergreen_demand INTEGER,
    monetization_ceiling INTEGER,
    faceless_viability INTEGER,
    originality_viability INTEGER,
    dm_shareability INTEGER,
    search_seo_potential INTEGER,
    subscription_ceiling INTEGER,
    selected BOOLEAN DEFAULT 0,
    analysis_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  -- Content ideas (from Module 2 & 4)
  CREATE TABLE IF NOT EXISTS content_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK(content_type IN ('carousel', 'reel', 'story', 'static')),
    hook TEXT,
    value_proposition TEXT,
    emotional_trigger TEXT,
    send_trigger TEXT,
    send_probability TEXT CHECK(send_probability IN ('medium', 'high', 'very_high', 'extreme')),
    save_probability TEXT CHECK(save_probability IN ('medium', 'high', 'very_high', 'extreme')),
    watch_time_strategy TEXT,
    caption_seo_keywords TEXT,
    originality_score INTEGER,
    status TEXT DEFAULT 'idea' CHECK(status IN ('idea', 'scripted', 'designed', 'queued', 'approved', 'published', 'archived')),
    performance_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME
  );

  -- Fully scripted content (from Module 3)
  CREATE TABLE IF NOT EXISTS content_scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER REFERENCES content_ideas(id),
    content_type TEXT NOT NULL,
    script_json TEXT NOT NULL,
    caption TEXT,
    caption_keywords TEXT,
    hashtags TEXT,
    cta_text TEXT,
    dm_trigger_keyword TEXT,
    story_sequence_json TEXT,
    design_notes_json TEXT,
    originality_verified BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  -- Published content tracking
  CREATE TABLE IF NOT EXISTS published_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER REFERENCES content_scripts(id),
    platform TEXT NOT NULL CHECK(platform IN ('instagram', 'tiktok', 'youtube_shorts', 'pinterest')),
    platform_post_id TEXT,
    platform_post_url TEXT,
    published_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Performance metrics (updated by analytics loop)
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    sends INTEGER DEFAULT 0,
    watch_time_seconds REAL DEFAULT 0,
    retention_3s_pct REAL DEFAULT 0,
    follows_from_post INTEGER DEFAULT 0,
    profile_visits INTEGER DEFAULT 0,

    -- Computed scores
    sends_per_reach REAL DEFAULT 0,
    likes_per_reach REAL DEFAULT 0,
    engagement_rate REAL DEFAULT 0,

    last_analytics_update DATETIME
  );

  -- Brand system configuration
  CREATE TABLE IF NOT EXISTS brand_system (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    config_json TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  -- Content calendar (from Module 6)
  CREATE TABLE IF NOT EXISTS content_calendar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    content_type TEXT NOT NULL,
    content_pillar TEXT,
    script_id INTEGER REFERENCES content_scripts(id),
    status TEXT DEFAULT 'planned' CHECK(status IN ('planned', 'generated', 'approved', 'published', 'skipped')),
    notes TEXT
  );

  -- Revenue tracking (Module 7)
  CREATE TABLE IF NOT EXISTS revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    source TEXT NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  -- Weekly scorecard (Module 8)
  CREATE TABLE IF NOT EXISTS weekly_scorecard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE NOT NULL,
    followers_start INTEGER,
    followers_end INTEGER,
    posts_published INTEGER,
    total_reach INTEGER,
    total_sends INTEGER,
    avg_sends_per_reach REAL,
    total_saves INTEGER,
    avg_watch_time REAL,
    revenue_total REAL,
    email_subscribers_gained INTEGER,
    scorecard_json TEXT,
    status TEXT CHECK(status IN ('green', 'yellow', 'red')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  -- Email list (Module 9 - platform independence)
  CREATE TABLE IF NOT EXISTS email_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    source TEXT,
    lead_magnet TEXT,
    subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
  );

  -- DM automation flows (Module 9)
  CREATE TABLE IF NOT EXISTS dm_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_keyword TEXT NOT NULL,
    flow_name TEXT NOT NULL,
    flow_steps_json TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    times_triggered INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  -- Rendered assets (visual pipeline)
  CREATE TABLE IF NOT EXISTS rendered_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER REFERENCES content_scripts(id),
    content_type TEXT NOT NULL,
    local_paths TEXT NOT NULL,
    public_urls TEXT DEFAULT '[]',
    rendered_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  -- Cross-platform distribution log (Module 10)
  CREATE TABLE IF NOT EXISTS cross_platform_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_script_id INTEGER REFERENCES content_scripts(id),
    platform TEXT NOT NULL,
    adapted_script_json TEXT,
    published BOOLEAN DEFAULT 0,
    platform_post_url TEXT,
    published_at DATETIME
  );
`;
