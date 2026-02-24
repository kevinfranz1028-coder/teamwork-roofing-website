import chalk from 'chalk';
import { getDb } from './database/db.js';
import { CONFIG } from './config/env.js';

async function smokeTest() {
  const results: Array<{ test: string; status: 'pass' | 'fail' | 'skip'; message: string }> = [];

  function log(test: string, status: 'pass' | 'fail' | 'skip', message: string) {
    results.push({ test, status, message });
    const icon = status === 'pass' ? chalk.green('✓') : status === 'fail' ? chalk.red('✗') : chalk.yellow('○');
    console.log(`${icon} ${test}: ${message}`);
  }

  console.log(chalk.cyan('\n═══ THEPLANTICU SMOKE TEST ═══\n'));

  // 1. Database
  try {
    const db = getDb();
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all() as any[];
    const tableNames = tables.map((t: any) => t.name);
    const required = ['niches', 'content_ideas', 'content_scripts', 'published_content', 'revenue', 'dm_flows', 'email_list', 'brand_system', 'content_calendar', 'weekly_scorecard', 'cross_platform_log', 'creative_briefs', 'ai_settings', 'rendered_assets'];
    const missing = required.filter(t => !tableNames.includes(t));
    if (missing.length === 0) {
      log('Database', 'pass', `${tableNames.length} tables found, all ${required.length} required tables present`);
    } else {
      log('Database', 'fail', `Missing tables: ${missing.join(', ')}`);
    }
  } catch (err: any) {
    log('Database', 'fail', err.message);
  }

  // 2. Anthropic API Key
  if (CONFIG.ai.apiKey && CONFIG.ai.apiKey !== 'your_anthropic_api_key_here') {
    try {
      const { askClaude } = await import('./integrations/claude-client.js');
      const response = await askClaude({
        systemPrompt: 'Respond with exactly: OK',
        userPrompt: 'Say OK',
        maxTokens: 10,
      });
      log('Claude API', 'pass', `Connected. Model: ${CONFIG.ai.model}`);
    } catch (err: any) {
      log('Claude API', 'fail', err.message);
    }
  } else {
    log('Claude API', 'skip', 'ANTHROPIC_API_KEY not configured');
  }

  // 3. Instagram Token
  if (CONFIG.instagram.accessToken && CONFIG.instagram.accountId) {
    try {
      const axios = (await import('axios')).default;
      const response = await axios.get(`https://graph.facebook.com/v22.0/${CONFIG.instagram.accountId}`, {
        params: { fields: 'id,username', access_token: CONFIG.instagram.accessToken }
      });
      log('Instagram API', 'pass', `Account: @${response.data.username}`);
    } catch (err: any) {
      log('Instagram API', 'fail', err.response?.data?.error?.message || err.message);
    }
  } else {
    log('Instagram API', 'skip', 'Instagram credentials not configured');
  }

  // 4. Replicate
  if (CONFIG.replicate?.apiToken) {
    log('Replicate API', 'pass', 'API token configured');
  } else {
    log('Replicate API', 'skip', 'REPLICATE_API_TOKEN not configured');
  }

  // 5. Cloudinary
  if (CONFIG.cloudinary?.cloudName && CONFIG.cloudinary?.apiKey) {
    log('Cloudinary', 'pass', `Cloud: ${CONFIG.cloudinary.cloudName}`);
  } else {
    log('Cloudinary', 'skip', 'Cloudinary credentials not configured');
  }

  // 6. OpenAI TTS
  if (CONFIG.openaiTts?.apiKey) {
    log('OpenAI TTS', 'pass', 'API key configured');
  } else {
    log('OpenAI TTS', 'skip', 'OPENAI_API_KEY not configured (reels will use silent audio)');
  }

  // 7. Puppeteer
  try {
    const puppeteer = await import('puppeteer');
    const browser = await puppeteer.default.launch({ headless: true });
    await browser.close();
    log('Puppeteer', 'pass', 'Headless Chrome available');
  } catch (err: any) {
    log('Puppeteer', 'fail', `${err.message}. Run: npm install puppeteer`);
  }

  // 8. ffmpeg
  try {
    const { execSync } = await import('child_process');
    const version = execSync('ffmpeg -version').toString().split('\n')[0];
    log('ffmpeg', 'pass', version);
  } catch {
    log('ffmpeg', 'fail', 'Not installed. Required for reel rendering.');
  }

  // Summary
  console.log(chalk.cyan('\n═══ RESULTS ═══'));
  const passed = results.filter(r => r.status === 'pass').length;
  const failed = results.filter(r => r.status === 'fail').length;
  const skipped = results.filter(r => r.status === 'skip').length;
  console.log(`${chalk.green(`${passed} passed`)} | ${chalk.red(`${failed} failed`)} | ${chalk.yellow(`${skipped} skipped`)}\n`);

  if (failed > 0) {
    console.log(chalk.red('Fix the failed items above before running the pipeline.\n'));
  }
}

smokeTest();
