import { v2 as cloudinary } from 'cloudinary';
import { CONFIG } from '../config/env.js';

let configured = false;

function ensureConfigured() {
  if (configured) return;
  cloudinary.config({
    cloud_name: CONFIG.cloudinary.cloudName,
    api_key: CONFIG.cloudinary.apiKey,
    api_secret: CONFIG.cloudinary.apiSecret,
  });
  configured = true;
}

/**
 * Upload an image file to Cloudinary and return the public URL.
 */
export async function uploadImage(localPath: string, folder = 'ig-engine'): Promise<string> {
  ensureConfigured();
  const result = await cloudinary.uploader.upload(localPath, {
    folder,
    resource_type: 'image',
  });
  return result.secure_url;
}

/**
 * Upload a video file to Cloudinary and return the public URL.
 */
export async function uploadVideo(localPath: string, folder = 'ig-engine'): Promise<string> {
  ensureConfigured();
  const result = await cloudinary.uploader.upload(localPath, {
    folder,
    resource_type: 'video',
  });
  return result.secure_url;
}

/**
 * Upload multiple images in parallel, return public URLs in order.
 */
export async function uploadImages(localPaths: string[], folder = 'ig-engine'): Promise<string[]> {
  return Promise.all(localPaths.map(p => uploadImage(p, folder)));
}
