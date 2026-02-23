import dotenv from 'dotenv';
import path from 'path';

dotenv.config();

export const CONFIG = {
  ai: {
    apiKey: process.env.ANTHROPIC_API_KEY!,
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-5-20250929',
  },
  instagram: {
    appId: process.env.META_APP_ID || '',
    appSecret: process.env.META_APP_SECRET || '',
    accountId: process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID || '',
    accessToken: process.env.INSTAGRAM_ACCESS_TOKEN || '',
  },
  buffer: {
    accessToken: process.env.BUFFER_ACCESS_TOKEN || '',
  },
  app: {
    niche: process.env.NICHE || '',
    postingSchedule: (process.env.POSTING_SCHEDULE || '9:00,12:00,18:00').split(','),
    timezone: process.env.TIMEZONE || 'America/Chicago',
    dailyTriggerTime: process.env.DAILY_TRIGGER_TIME || '06:00',
    dashboardPort: parseInt(process.env.DASHBOARD_PORT || '3847'),
  },
  content: {
    carouselSlideCount: parseInt(process.env.CAROUSEL_SLIDE_COUNT || '10'),
    reelMaxLength: parseInt(process.env.REEL_MAX_LENGTH_SECONDS || '30'),
    hashtagCount: parseInt(process.env.HASHTAG_COUNT || '5'),
  },
  cloudinary: {
    cloudName: process.env.CLOUDINARY_CLOUD_NAME || '',
    apiKey: process.env.CLOUDINARY_API_KEY || '',
    apiSecret: process.env.CLOUDINARY_API_SECRET || '',
  },
  replicate: {
    apiToken: process.env.REPLICATE_API_TOKEN || '',
  },
  openaiTts: {
    apiKey: process.env.OPENAI_API_KEY || '',
  },
  pipeline: {
    autoPublish: process.env.AUTO_PUBLISH === 'true',
    autoRender: process.env.AUTO_RENDER === 'true',
    renderReels: process.env.RENDER_REELS !== 'false', // default true
  },
  paths: {
    data: path.resolve('data'),
    contentQueue: path.resolve('data/content-queue'),
    published: path.resolve('data/published'),
    assets: path.resolve('data/assets'),
    analytics: path.resolve('data/analytics'),
  }
} as const;
