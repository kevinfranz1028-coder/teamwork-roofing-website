import axios from 'axios';
import { writeFile } from 'fs/promises';
import path from 'path';
import { mkdirSync, existsSync, createWriteStream } from 'fs';
import { CONFIG } from '../config/env.js';
import { getDb } from '../database/db.js';
import { withRetry } from '../utils/retry.js';
import { logApiCost } from '../utils/cost-tracker.js';

const PEXELS_BASE = 'https://api.pexels.com';

function getHeaders() {
  const key = CONFIG.pexels?.apiKey;
  if (!key) throw new Error('PEXELS_API_KEY not set');
  return { Authorization: key };
}

// ─── Anti-Repetition: 30-day lookback ───

function getRecentlyUsedIds(mediaType: 'video' | 'photo', days = 30): Set<number> {
  const db = getDb();
  try {
    const rows = db.prepare(
      `SELECT pexels_id FROM pexels_clips
       WHERE media_type = ? AND used_at > datetime('now', ?)
       ORDER BY used_at DESC`
    ).all(mediaType, `-${days} days`) as { pexels_id: number }[];
    return new Set(rows.map(r => r.pexels_id));
  } catch {
    // Table may not exist yet before migration runs
    return new Set();
  }
}

function recordUsage(
  pexelsId: number,
  mediaType: 'video' | 'photo',
  searchQuery: string,
  photographer: string,
  pexelsUrl: string,
  scriptId?: number,
  segmentIndex?: number
): void {
  const db = getDb();
  try {
    db.prepare(
      `INSERT INTO pexels_clips (pexels_id, media_type, search_query, photographer, pexels_url, script_id, segment_index)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).run(pexelsId, mediaType, searchQuery, photographer, pexelsUrl, scriptId ?? null, segmentIndex ?? null);
  } catch {
    // Silently skip if table doesn't exist yet
  }
}

// ─── Video Search & Download ───

interface PexelsVideoFile {
  id: number;
  quality: string;
  file_type: string;
  width: number;
  height: number;
  link: string;
}

interface PexelsVideo {
  id: number;
  url: string;
  duration: number;
  user: { name: string };
  video_files: PexelsVideoFile[];
}

/**
 * Search Pexels for a video clip, download the best HD file.
 * Uses fallback chain: specific terms → generic plant terms → error.
 */
export async function findAndDownloadVideoClip(
  searchTerms: string[],
  outputDir: string,
  filename: string,
  minDuration = 3,
  maxDuration = 15,
  scriptId?: number,
  segmentIndex?: number
): Promise<{ path: string; pexelsId: number; photographer: string }> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const recentIds = getRecentlyUsedIds('video');
  const genericFallbacks = ['houseplant close up', 'green leaves nature', 'indoor plant care', 'plant watering'];

  // Build search chain: specific terms first, then generic fallbacks
  const searchChain = [...searchTerms, ...genericFallbacks];

  for (const query of searchChain) {
    try {
      const video = await searchVideoClip(query, minDuration, maxDuration, recentIds);
      if (!video) continue;

      const outputPath = path.join(outputDir, filename);
      await downloadVideoFile(video, outputPath);

      recordUsage(video.id, 'video', query, video.user.name, video.url, scriptId, segmentIndex);

      logApiCost({
        provider: 'pexels',
        category: 'video',
        endpoint: 'videos/search',
        model: 'pexels-stock',
        description: `Video clip: "${query}"`,
        estimatedCost: 0,
      });

      console.log(`    Pexels video: "${query}" → id=${video.id}, ${video.duration}s, by ${video.user.name}`);
      return { path: outputPath, pexelsId: video.id, photographer: video.user.name };
    } catch (err: any) {
      console.warn(`    Pexels video search "${query}" failed: ${err.message}`);
    }
  }

  throw new Error(`No suitable Pexels video found for terms: ${searchTerms.join(', ')}`);
}

async function searchVideoClip(
  query: string,
  minDuration: number,
  maxDuration: number,
  excludeIds: Set<number>
): Promise<PexelsVideo | null> {
  const response = await withRetry(
    () => axios.get(`${PEXELS_BASE}/videos/search`, {
      headers: getHeaders(),
      params: {
        query,
        per_page: 30,
        orientation: 'portrait',
        size: 'medium',
      },
    }),
    { maxAttempts: 2, delayMs: 1000, backoffMultiplier: 2 }
  );

  const videos: PexelsVideo[] = response.data.videos || [];

  // Filter by duration and exclude recently used
  const candidates = videos.filter(v =>
    v.duration >= minDuration &&
    v.duration <= maxDuration &&
    !excludeIds.has(v.id)
  );

  if (candidates.length === 0) return null;

  // Pick a random one from top results to add variety
  const pick = candidates[Math.floor(Math.random() * Math.min(candidates.length, 5))];
  return pick;
}

async function downloadVideoFile(video: PexelsVideo, outputPath: string): Promise<void> {
  // Prefer HD portrait video files
  const files = video.video_files
    .filter(f => f.file_type === 'video/mp4')
    .sort((a, b) => {
      // Prefer 1080 height (portrait), then by quality
      const aScore = a.height >= 1080 ? 2 : a.height >= 720 ? 1 : 0;
      const bScore = b.height >= 1080 ? 2 : b.height >= 720 ? 1 : 0;
      return bScore - aScore;
    });

  const file = files[0];
  if (!file) throw new Error(`No MP4 files for video ${video.id}`);

  const response = await axios.get(file.link, { responseType: 'arraybuffer' });
  await writeFile(outputPath, Buffer.from(response.data));
}

// ─── Photo Search & Download ───

interface PexelsPhotoSrc {
  original: string;
  large2x: string;
  large: string;
  medium: string;
}

interface PexelsPhoto {
  id: number;
  url: string;
  photographer: string;
  src: PexelsPhotoSrc;
}

/**
 * Search Pexels for a photo, download it.
 * Uses fallback chain: specific terms → generic plant terms → error.
 */
export async function findAndDownloadPhoto(
  searchTerms: string[],
  outputDir: string,
  filename: string,
  orientation: 'landscape' | 'portrait' | 'square' = 'square',
  scriptId?: number,
  segmentIndex?: number
): Promise<{ path: string; pexelsId: number; photographer: string }> {
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const recentIds = getRecentlyUsedIds('photo');
  const genericFallbacks = ['houseplant', 'green plant leaves', 'indoor garden', 'potted plant'];

  const searchChain = [...searchTerms, ...genericFallbacks];

  for (const query of searchChain) {
    try {
      const photo = await searchPhoto(query, orientation, recentIds);
      if (!photo) continue;

      const outputPath = path.join(outputDir, filename);
      await downloadPhotoFile(photo, outputPath);

      recordUsage(photo.id, 'photo', query, photo.photographer, photo.url, scriptId, segmentIndex);

      logApiCost({
        provider: 'pexels',
        category: 'image',
        endpoint: 'search',
        model: 'pexels-stock',
        description: `Photo: "${query}"`,
        estimatedCost: 0,
      });

      console.log(`    Pexels photo: "${query}" → id=${photo.id}, by ${photo.photographer}`);
      return { path: outputPath, pexelsId: photo.id, photographer: photo.photographer };
    } catch (err: any) {
      console.warn(`    Pexels photo search "${query}" failed: ${err.message}`);
    }
  }

  throw new Error(`No suitable Pexels photo found for terms: ${searchTerms.join(', ')}`);
}

async function searchPhoto(
  query: string,
  orientation: string,
  excludeIds: Set<number>
): Promise<PexelsPhoto | null> {
  const response = await withRetry(
    () => axios.get(`${PEXELS_BASE}/v1/search`, {
      headers: getHeaders(),
      params: {
        query,
        per_page: 30,
        orientation,
      },
    }),
    { maxAttempts: 2, delayMs: 1000, backoffMultiplier: 2 }
  );

  const photos: PexelsPhoto[] = response.data.photos || [];

  const candidates = photos.filter(p => !excludeIds.has(p.id));
  if (candidates.length === 0) return null;

  const pick = candidates[Math.floor(Math.random() * Math.min(candidates.length, 5))];
  return pick;
}

async function downloadPhotoFile(photo: PexelsPhoto, outputPath: string): Promise<void> {
  // Use large2x for high quality
  const url = photo.src.large2x || photo.src.large || photo.src.original;
  const response = await axios.get(url, { responseType: 'arraybuffer' });
  await writeFile(outputPath, Buffer.from(response.data));
}
