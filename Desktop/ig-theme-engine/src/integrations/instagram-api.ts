import axios from 'axios';
import { CONFIG } from '../config/env.js';

const BASE_URL = 'https://graph.facebook.com/v19.0';

interface MediaContainer {
  id: string;
}

interface PublishResult {
  id: string;
  permalink?: string;
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

  const params: Record<string, string> = {
    access_token: CONFIG.instagram.accessToken,
    caption,
  };

  if (mediaType === 'REELS' || videoUrl) {
    params.media_type = 'REELS';
    params.video_url = videoUrl!;
    if (coverUrl) params.cover_url = coverUrl;
  } else if (imageUrl) {
    params.image_url = imageUrl;
  }

  if (locationId) params.location_id = locationId;

  const response = await axios.post(
    `${BASE_URL}/${CONFIG.instagram.accountId}/media`,
    null,
    { params }
  );

  return { id: response.data.id };
}

/**
 * Step 1b: Create carousel item containers (no caption on individual items)
 */
export async function createCarouselItemContainer(options: {
  imageUrl?: string;
  videoUrl?: string;
  mediaType?: 'IMAGE' | 'VIDEO';
}): Promise<MediaContainer> {
  const params: Record<string, string> = {
    access_token: CONFIG.instagram.accessToken,
    is_carousel_item: 'true',
  };

  if (options.videoUrl) {
    params.media_type = 'VIDEO';
    params.video_url = options.videoUrl;
  } else if (options.imageUrl) {
    params.image_url = options.imageUrl;
  }

  const response = await axios.post(
    `${BASE_URL}/${CONFIG.instagram.accountId}/media`,
    null,
    { params }
  );

  return { id: response.data.id };
}

/**
 * Step 1c: Create carousel album container
 */
export async function createCarouselContainer(options: {
  childrenIds: string[];
  caption: string;
}): Promise<MediaContainer> {
  const response = await axios.post(
    `${BASE_URL}/${CONFIG.instagram.accountId}/media`,
    null,
    {
      params: {
        access_token: CONFIG.instagram.accessToken,
        media_type: 'CAROUSEL',
        children: options.childrenIds.join(','),
        caption: options.caption,
      },
    }
  );

  return { id: response.data.id };
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
  const response = await axios.post(
    `${BASE_URL}/${CONFIG.instagram.accountId}/media_publish`,
    null,
    {
      params: {
        creation_id: containerId,
        access_token: CONFIG.instagram.accessToken,
      },
    }
  );

  // Fetch the permalink
  const mediaInfo = await axios.get(`${BASE_URL}/${response.data.id}`, {
    params: {
      fields: 'permalink,id',
      access_token: CONFIG.instagram.accessToken,
    },
  });

  return {
    id: response.data.id,
    permalink: mediaInfo.data.permalink,
  };
}

// ─── High-Level Publishing Functions ───────────────────

/**
 * Publish a single image post
 */
export async function publishImagePost(imageUrl: string, caption: string): Promise<PublishResult> {
  const container = await createMediaContainer({ imageUrl, caption });
  return publishMedia(container.id);
}

/**
 * Publish a carousel post (multiple images)
 */
export async function publishCarouselPost(
  imageUrls: string[],
  caption: string
): Promise<PublishResult> {
  // Create individual item containers
  const childContainers = await Promise.all(
    imageUrls.map(url => createCarouselItemContainer({ imageUrl: url }))
  );

  // Create the carousel album container
  const carouselContainer = await createCarouselContainer({
    childrenIds: childContainers.map(c => c.id),
    caption,
  });

  return publishMedia(carouselContainer.id);
}

/**
 * Publish a reel
 */
export async function publishReel(
  videoUrl: string,
  caption: string,
  coverUrl?: string
): Promise<PublishResult> {
  const container = await createMediaContainer({
    videoUrl,
    caption,
    mediaType: 'REELS',
    coverUrl,
  });

  // Reels need time to process
  const ready = await waitForContainer(container.id);
  if (!ready) {
    throw new Error(`Reel container ${container.id} failed to process`);
  }

  return publishMedia(container.id);
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
