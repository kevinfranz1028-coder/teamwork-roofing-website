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
