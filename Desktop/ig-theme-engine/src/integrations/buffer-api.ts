import axios from 'axios';
import { CONFIG } from '../config/env.js';

const BASE_URL = 'https://api.bufferapp.com/1';

interface BufferProfile {
  id: string;
  service: string;
  serviceUsername: string;
  formatted_username: string;
}

interface BufferPostResult {
  success: boolean;
  buffer_count: number;
  buffer_percentage: number;
  updates: Array<{
    id: string;
    created_at: number;
    status: string;
    text: string;
    scheduled_at?: number;
  }>;
}

// ─── Profile Management ────────────────────────────────

/**
 * Get all connected social media profiles
 */
export async function getProfiles(): Promise<BufferProfile[]> {
  const response = await axios.get(`${BASE_URL}/profiles.json`, {
    params: { access_token: CONFIG.buffer.accessToken },
  });
  return response.data;
}

/**
 * Get the Instagram profile from Buffer
 */
export async function getInstagramProfile(): Promise<BufferProfile | null> {
  const profiles = await getProfiles();
  return profiles.find(p => p.service === 'instagram') || null;
}

// ─── Post Scheduling ───────────────────────────────────

/**
 * Create a new post (add to Buffer queue)
 * Set scheduled_at for specific time, or omit to add to the next queue slot
 */
export async function createPost(options: {
  profileIds: string[];
  text: string;
  mediaUrls?: string[];
  scheduledAt?: Date;
  repost?: boolean;
}): Promise<BufferPostResult> {
  const params: Record<string, any> = {
    access_token: CONFIG.buffer.accessToken,
    text: options.text,
    profile_ids: options.profileIds,
    now: false,
  };

  if (options.mediaUrls && options.mediaUrls.length > 0) {
    params['media[photo]'] = options.mediaUrls[0];
    if (options.mediaUrls.length > 1) {
      // Buffer supports multiple images for carousel-like posts
      options.mediaUrls.forEach((url, i) => {
        params[`media[photos][${i}]`] = url;
      });
    }
  }

  if (options.scheduledAt) {
    params.scheduled_at = options.scheduledAt.toISOString();
  }

  const response = await axios.post(`${BASE_URL}/updates/create.json`, null, {
    params,
  });

  return response.data;
}

/**
 * Schedule a post for a specific time
 */
export async function schedulePost(options: {
  text: string;
  mediaUrls?: string[];
  scheduledAt: Date;
}): Promise<BufferPostResult> {
  const profile = await getInstagramProfile();
  if (!profile) {
    throw new Error('No Instagram profile connected in Buffer');
  }

  return createPost({
    profileIds: [profile.id],
    text: options.text,
    mediaUrls: options.mediaUrls,
    scheduledAt: options.scheduledAt,
  });
}

/**
 * Add post to the next available queue slot
 */
export async function addToQueue(options: {
  text: string;
  mediaUrls?: string[];
}): Promise<BufferPostResult> {
  const profile = await getInstagramProfile();
  if (!profile) {
    throw new Error('No Instagram profile connected in Buffer');
  }

  return createPost({
    profileIds: [profile.id],
    text: options.text,
    mediaUrls: options.mediaUrls,
  });
}

// ─── Queue Management ──────────────────────────────────

/**
 * Get pending posts in the queue for a profile
 */
export async function getQueuedPosts(profileId: string): Promise<any[]> {
  const response = await axios.get(`${BASE_URL}/profiles/${profileId}/updates/pending.json`, {
    params: { access_token: CONFIG.buffer.accessToken },
  });
  return response.data.updates;
}

/**
 * Get sent/published posts for a profile
 */
export async function getSentPosts(profileId: string, page = 1, count = 20): Promise<any[]> {
  const response = await axios.get(`${BASE_URL}/profiles/${profileId}/updates/sent.json`, {
    params: {
      access_token: CONFIG.buffer.accessToken,
      page,
      count,
    },
  });
  return response.data.updates;
}

/**
 * Delete a queued post
 */
export async function deletePost(updateId: string): Promise<boolean> {
  const response = await axios.post(`${BASE_URL}/updates/${updateId}/destroy.json`, null, {
    params: { access_token: CONFIG.buffer.accessToken },
  });
  return response.data.success;
}

/**
 * Move a post to the top of the queue
 */
export async function moveToTop(updateId: string): Promise<boolean> {
  const response = await axios.post(`${BASE_URL}/updates/${updateId}/move_to_top.json`, null, {
    params: { access_token: CONFIG.buffer.accessToken },
  });
  return response.data.success;
}

// ─── Posting Schedule ──────────────────────────────────

/**
 * Get the posting schedule for a profile
 */
export async function getPostingSchedule(profileId: string): Promise<any> {
  const response = await axios.get(`${BASE_URL}/profiles/${profileId}/schedules.json`, {
    params: { access_token: CONFIG.buffer.accessToken },
  });
  return response.data;
}

/**
 * Update the posting schedule
 */
export async function updatePostingSchedule(
  profileId: string,
  schedules: Array<{ days: string[]; times: string[] }>
): Promise<any> {
  const response = await axios.post(
    `${BASE_URL}/profiles/${profileId}/schedules/update.json`,
    null,
    {
      params: {
        access_token: CONFIG.buffer.accessToken,
        schedules,
      },
    }
  );
  return response.data;
}
