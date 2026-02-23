import { appendFileSync, mkdirSync, existsSync } from 'fs';
import path from 'path';
import { CONFIG } from '../config/env.js';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LOG_COLORS: Record<LogLevel, string> = {
  debug: '\x1b[90m',  // gray
  info: '\x1b[36m',   // cyan
  warn: '\x1b[33m',   // yellow
  error: '\x1b[31m',  // red
};

const RESET = '\x1b[0m';

const logDir = path.join(CONFIG.paths.data, 'logs');

function ensureLogDir() {
  if (!existsSync(logDir)) {
    mkdirSync(logDir, { recursive: true });
  }
}

function timestamp(): string {
  return new Date().toISOString();
}

function formatMessage(level: LogLevel, module: string, message: string, data?: any): string {
  const ts = timestamp();
  const dataStr = data ? ` ${JSON.stringify(data)}` : '';
  return `[${ts}] [${level.toUpperCase()}] [${module}] ${message}${dataStr}`;
}

function log(level: LogLevel, module: string, message: string, data?: any) {
  const formatted = formatMessage(level, module, message, data);

  // Console output with color
  const color = LOG_COLORS[level];
  console.log(`${color}${formatted}${RESET}`);

  // File output (no color codes)
  try {
    ensureLogDir();
    const logFile = path.join(logDir, `${new Date().toISOString().split('T')[0]}.log`);
    appendFileSync(logFile, formatted + '\n');
  } catch {
    // Don't crash if logging fails
  }
}

export const logger = {
  debug: (module: string, message: string, data?: any) => log('debug', module, message, data),
  info: (module: string, message: string, data?: any) => log('info', module, message, data),
  warn: (module: string, message: string, data?: any) => log('warn', module, message, data),
  error: (module: string, message: string, data?: any) => log('error', module, message, data),

  // Track API costs
  apiCall: (endpoint: string, inputTokens: number, outputTokens: number, cost: number) => {
    log('info', 'API', `${endpoint} — ${inputTokens}in/${outputTokens}out — $${cost.toFixed(4)}`);
  },

  // Track pipeline events
  pipeline: (event: string, details?: any) => {
    log('info', 'PIPELINE', event, details);
  },
};
