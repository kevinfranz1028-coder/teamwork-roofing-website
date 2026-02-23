import { getDb, insertRow } from '../database/db.js';

export interface BrandSystem {
  id?: number;
  name: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
  };
  fonts: {
    headline: string;
    body: string;
    accent: string;
  };
  voice: {
    tone: string;
    personality: string[];
    vocabulary: string[];
    avoidWords: string[];
  };
  visualStyle: {
    aesthetic: string;
    photoStyle: string;
    iconStyle: string;
    layoutPreference: string;
  };
  contentRules: {
    maxHeadlineWords: number;
    maxBodyWordsPerSlide: number;
    hashtagCount: number;
    emojiUsage: 'none' | 'minimal' | 'moderate' | 'heavy';
    ctaStyle: string;
  };
}

const DEFAULT_BRAND: BrandSystem = {
  name: 'Default Brand',
  colors: {
    primary: '#6C5CE7',
    secondary: '#A29BFE',
    accent: '#FD79A8',
    background: '#0A0A0F',
    text: '#FFFFFF',
  },
  fonts: {
    headline: 'Inter Bold',
    body: 'Inter Regular',
    accent: 'Space Grotesk',
  },
  voice: {
    tone: 'Knowledgeable but approachable — like a friend who happens to be an expert',
    personality: ['direct', 'helpful', 'slightly urgent', 'data-driven'],
    vocabulary: ['diagnose', 'rescue', 'revive', 'protocol', 'triage', 'recovery'],
    avoidWords: ['just', 'simply', 'easy', 'hack', 'guru', 'game-changer'],
  },
  visualStyle: {
    aesthetic: 'Clean clinical meets warm botanical',
    photoStyle: 'Close-up macro with natural light, human hands visible',
    iconStyle: 'Minimal line icons with brand accent color',
    layoutPreference: 'Left-aligned text, generous whitespace, strong visual hierarchy',
  },
  contentRules: {
    maxHeadlineWords: 10,
    maxBodyWordsPerSlide: 20,
    hashtagCount: 5,
    emojiUsage: 'minimal',
    ctaStyle: 'Rotate between save, send, comment, follow, DM trigger',
  },
};

let cachedBrand: BrandSystem | null = null;

export function getActiveBrand(): BrandSystem {
  if (cachedBrand) return cachedBrand;

  const db = getDb();
  const active = db.prepare('SELECT * FROM brand_system WHERE is_active = 1 ORDER BY id DESC LIMIT 1').get() as any;

  if (active) {
    cachedBrand = { id: active.id, ...JSON.parse(active.config_json) };
    return cachedBrand;
  }

  // Initialize with default brand
  const id = insertRow('brand_system', {
    name: DEFAULT_BRAND.name,
    config_json: JSON.stringify(DEFAULT_BRAND),
    is_active: 1,
  });

  cachedBrand = { id: Number(id), ...DEFAULT_BRAND };
  return cachedBrand;
}

export function updateBrand(updates: Partial<BrandSystem>): BrandSystem {
  const current = getActiveBrand();
  const updated = { ...current, ...updates };
  const db = getDb();
  db.prepare('UPDATE brand_system SET config_json = ?, name = ? WHERE id = ?')
    .run(JSON.stringify(updated), updated.name, current.id);
  cachedBrand = updated;
  return updated;
}

export function clearBrandCache(): void {
  cachedBrand = null;
}
