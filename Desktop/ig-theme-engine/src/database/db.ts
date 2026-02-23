import Database from 'better-sqlite3';
import path from 'path';
import { SCHEMA } from './schema.js';
import { CONFIG } from '../config/env.js';

let db: Database.Database;

export function getDb(): Database.Database {
  if (!db) {
    const dbPath = path.join(CONFIG.paths.data, 'ig-engine.db');
    db = new Database(dbPath);
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
    db.exec(SCHEMA);
  }
  return db;
}

// Helper: insert and return the new row
export function insertRow(table: string, data: Record<string, any>) {
  const keys = Object.keys(data);
  const placeholders = keys.map(() => '?').join(', ');
  const stmt = getDb().prepare(
    `INSERT INTO ${table} (${keys.join(', ')}) VALUES (${placeholders})`
  );
  const result = stmt.run(...keys.map(k => data[k]));
  return result.lastInsertRowid;
}

// Helper: get rows with optional filter
export function getRows(table: string, where?: Record<string, any>, limit?: number) {
  let query = `SELECT * FROM ${table}`;
  const params: any[] = [];
  if (where) {
    const conditions = Object.entries(where).map(([k, v]) => {
      params.push(v);
      return `${k} = ?`;
    });
    query += ` WHERE ${conditions.join(' AND ')}`;
  }
  if (limit) query += ` LIMIT ${limit}`;
  return getDb().prepare(query).all(...params);
}
