import axios from 'axios';
import { CONFIG } from '../config/env.js';
import { withRetry } from '../utils/retry.js';

const BASE_URL = 'https://graph.facebook.com/v22.0';

interface MediaContainer {
  id: string;
}

interface PublishResult {
  id: string;
  permalink?: string;
}

/** Helper: POST to Graph API using form-encoded body instead of query params */
async function graphPost(url: string, data: Record<string, string>): Promise<any> {
  const response = await axios.post(url, new URLSearchParams(data), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data;
}

// ─── Single Image / Reel Publishing ────────────────────

/**
 * Step 1: Create a media container (upload media to IG)
 * For images: provide imageUrl
 * For reels: provide videoUrl
 */
export async function createMediaContainer(options: {
  imageUrl?: string;
  videoUrl?: string;
  caption: string;
  mediaType?: 'IMAGE' | 'VIDEO' | 'REELS' | 'CAROUSEL_ALBUM';
  coverUrl?: string;
  locationId?: string;
}): Promise<MediaContainer> {
  const { imageUrl, videoUrl, caption, mediaType, coverUrl, locationId } = options;

  const data: Record<string, string> = {
    access_token: CONFIG.instagram.accessToken,
    caption,
  };

  if (mediaType === 'REELS' || videoUrl) {
    data.media_type = 'REELS';
    data.video_url = videoUrl!;
    if (coverUrl) data.cover_url = coverUrl;
  } else if (imageUrl) {
    data.image_url = imageUrl;
  }

  if (locationId) data.location_id = locationId;

  const result = await graphPost(
    `${BASE_URL}/${CONFIG.instagram.accountId}/media`,
    data
  );

  return { id: result.id };
}

/**
 * Step 1b: Create carousel item containers (no caption on individual items)
 */
export async function createCarouselItemContainer(options: {
  imageUrl?: string;
  videoUrl?: string;
  mediaType?: 'IMAGE' | 'VIDEO';
}): Promise<MediaContainer> {
  const data: Record<string, string> = {
    access_token: CONFIG.instagram.accessToken,
    is_carousel_item: 'true',
  };

  if (options.videoUrl) {
    data.media_type = 'VIDEO';
    data.video_url = options.videoUrl;
  } else if (options.imageUrl) {
    data.image_url = options.imageUrl;
  }

  const result = await graphPost(
    `${BASE_URL}/${CONFIG.instagram.accountId}/media`,
    data
  );

  return { id: result.id };
}

/**
 * Step 1c: Create carousel album container
 */
export async function createCarouselContainer(options: {
  childrenIds: string[];
  caption: string;
}): Promise<MediaContainer> {
  const result = await graphPost(
    `${BASE_URL}/${CONFIG.instagram.accountId}/media`,
    {
      access_token: CONFIG.instagram.accessToken,
      media_type: 'CAROUSEL',
      children: options.childrenIds.join(','),
      caption: options.caption,
    }
  );

  return { id: result.id };
}

/**
 * Step 2: Check media container status (for async uploads like video/reels)
 */
export async function checkContainerStatus(containerId: string): Promise<string> {
  const response = await axios.get(`${BASE_URL}/${containerId}`, {
    params: {
      fields: 'status_code,status',
      access_token: CONFIG.instagram.accessToken,
    },
  });
  return response.data.status_code; // FINISHED, IN_PROGRESS, ERROR
}

/**
 * Wait for a container to finish processing (reels/video)
 */
export async function waitForContainer(containerId: string, maxWaitMs = 120000): Promise<boolean> {
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    const status = await checkContainerStatus(containerId);
    if (status === 'FINISHED') return true;
    if (status === 'ERROR') return false;
    await new Promise(r => setTimeout(r, 5000)); // poll every 5s
  }
  return false;
}

/**
 * Step 3: Publish the media container
 */
export async function publishMedia(containerId: string): Promise<PublishResult> {
  const result = await graphPost(
    `${BASE_URL}/${CONFIG.instagram.accountId}/media_publish`,
    {
      creation_id: containerId,
      access_token: CONFIG.instagram.accessToken,
    }
  );

  // Fetch the permalink
  const mediaInfo = await axios.get(`${BASE_URL}/${result.id}`, {
    params: {
      fields: 'permalink,id',
      access_token: CONFIG.instagram.accessToken,
    },
  });

  return {
    id: result.id,
    permalink: mediaInfo.data.permalink,
  };
}

// ─── High-Level Publishing Functions ───────────────────

/**
 * Publish a single image post
 */
export async function publishImagePost(imageUrl: string, caption: string): Promise<PublishResult> {
  const container = await withRetry(
    () => createMediaContainer({ imageUrl, caption }),
    { maxAttempts: 3, delayMs: 2000, backoffMultiplier: 2 }
  );
  return withRetry(
    () => publishMedia(container.id),
    { maxAttempts: 2, delayMs: 5000, backoffMultiplier: 1 }
  );
}

/**
 * Publish a carousel post (multiple images)
 */
export async function publishCarouselPost(
  imageUrls: string[],
  caption: string
): Promise<PublishResult> {
  // Create individual item containers with retry
  const childContainers: MediaContainer[] = [];
  for (const url of imageUrls) {
    const container = await withRetry(
      () => createCarouselItemContainer({ imageUrl: url }),
      { maxAttempts: 3, delayMs: 2000, backoffMultiplier: 2 }
    );
    childContainers.push(container);
  }

  // Create the carousel album container with retry
  const carouselContainer = await withRetry(
    () => createCarouselContainer({
      childrenIds: childContainers.map(c => c.id),
      caption,
    }),
    { maxAttempts: 3, delayMs: 3000, backoffMultiplier: 2 }
  );

  // Publish with retry
  return withRetry(
    () => publishMedia(carouselContainer.id),
    { maxAttempts: 2, delayMs: 5000, backoffMultiplier: 1 }
  );
}

/**
 * Publish a reel
 */
export async function publishReel(
  videoUrl: string,
  caption: string,
  coverUrl?: string
): Promise<PublishResult> {
  const container = await withRetry(
    () => createMediaContainer({
      videoUrl,
      caption,
      mediaType: 'REELS',
      coverUrl,
    }),
    { maxAttempts: 3, delayMs: 2000, backoffMultiplier: 2 }
  );

  // Reels need time to process
  const ready = await waitForContainer(container.id);
  if (!ready) {
    throw new Error(`Reel container ${container.id} failed to process`);
  }

  return withRetry(
    () => publishMedia(container.id),
    { maxAttempts: 2, delayMs: 5000, backoffMultiplier: 1 }
  );
}

// ─── Account Info & Insights ───────────────────────────

export async function getAccountInfo(): Promise<any> {
  const response = await axios.get(`${BASE_URL}/${CONFIG.instagram.accountId}`, {
    params: {
      fields: 'username,name,biography,followers_count,follows_count,media_count,profile_picture_url',
      access_token: CONFIG.instagram.accessToken,
    },
  });
  return response.data;
}

export async function getMediaInsights(mediaId: string): Promise<any> {
  const response = await axios.get(`${BASE_URL}/${mediaId}/insights`, {
    params: {
      metric: 'impressions,reach,saved,shares,total_interactions,video_views',
      access_token: CONFIG.instagram.accessToken,
    },
  });
  return response.data.data;
}

export async function getRecentMedia(limit = 25): Promise<any[]> {
  const response = await axios.get(`${BASE_URL}/${CONFIG.instagram.accountId}/media`, {
    params: {
      fields: 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count',
      limit,
      access_token: CONFIG.instagram.accessToken,
    },
  });
  return response.data.data;
}

// ─── Token Management ──────────────────────────────────

/**
 * Exchange short-lived token for long-lived token (60 days)
 */
export async function getLongLivedToken(shortLivedToken: string): Promise<{ token: string; expiresIn: number }> {
  const response = await axios.get(`${BASE_URL}/oauth/access_token`, {
    params: {
      grant_type: 'fb_exchange_token',
      client_id: CONFIG.instagram.appId,
      client_secret: CONFIG.instagram.appSecret,
      fb_exchange_token: shortLivedToken,
    },
  });
  return {
    token: response.data.access_token,
    expiresIn: response.data.expires_in,
  };
}

/**
 * Refresh a long-lived token (before it expires)
 */
export async function refreshLongLivedToken(token: string): Promise<{ token: string; expiresIn: number }> {
  const response = await axios.get(`${BASE_URL}/oauth/access_token`, {
    params: {
      grant_type: 'fb_exchange_token',
      client_id: CONFIG.instagram.appId,
      client_secret: CONFIG.instagram.appSecret,
      fb_exchange_token: token,
    },
  });
  return {
    token: response.data.access_token,
    expiresIn: response.data.expires_in,
  };
}

/**
 * Check token health and auto-refresh if expiring within 14 days.
 * Writes the new token back to .env if refreshed.
 */
export async function checkAndRefreshToken(): Promise<{ daysLeft: number; refreshed: boolean }> {
  const response = await axios.get(`${BASE_URL}/debug_token`, {
    params: {
      input_token: CONFIG.instagram.accessToken,
      access_token: CONFIG.instagram.accessToken,
    },
  });

  const expiresAt = response.data.data?.expires_at;
  if (!expiresAt) return { daysLeft: -1, refreshed: false };

  const daysLeft = Math.floor((expiresAt * 1000 - Date.now()) / (1000 * 60 * 60 * 24));

  if (daysLeft < 14) {
    console.log(`Instagram token expires in ${daysLeft} days. Attempting refresh...`);
    const result = await refreshLongLivedToken(CONFIG.instagram.accessToken);

    // Write new token to .env file
    const fs = await import('fs');
    const envPath = '.env';
    let envContent = fs.readFileSync(envPath, 'utf-8');
    envContent = envContent.replace(
      /INSTAGRAM_ACCESS_TOKEN=.*/,
      `INSTAGRAM_ACCESS_TOKEN=${result.token}`
    );
    fs.writeFileSync(envPath, envContent);

    console.log('Instagram token refreshed and saved to .env');
    return { daysLeft, refreshed: true };
  }

  return { daysLeft, refreshed: false };
}

/**
 * Test that a media container can be created (dry-run — does NOT publish).
 * Instagram auto-cleans unpublished containers after 24 hours.
 */
export async function testMediaContainer(imageUrl: string): Promise<{ success: boolean; containerId?: string; error?: string }> {
  try {
    const result = await graphPost(
      `${BASE_URL}/${CONFIG.instagram.accountId}/media`,
      {
        image_url: imageUrl,
        caption: 'TEST — DO NOT PUBLISH',
        access_token: CONFIG.instagram.accessToken,
      }
    );
    return { success: true, containerId: result.id };
  } catch (err: any) {
    return { success: false, error: err.response?.data?.error?.message || err.message };
  }
}
