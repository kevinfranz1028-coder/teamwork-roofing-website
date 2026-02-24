import axios from 'axios';
import { CONFIG } from '../config/env.js';

/**
 * PLACEHOLDER — Not yet integrated. Requires Canva Connect API app approval.
 *
 * Canva's Connect API requires an approved app integration.
 * For most users, the workflow is:
 * 1. Engine generates design specs (colors, text, layout)
 * 2. User creates designs in Canva using the specs
 * 3. User exports images and feeds URLs back to the engine
 *
 * This module provides the API integration for automated flows
 * where a Canva app integration is available. Currently unused —
 * the rendering pipeline uses Puppeteer + Replicate instead.
 */

const CANVA_BASE_URL = 'https://api.canva.com/rest/v1';

interface CanvaDesign {
  id: string;
  title: string;
  url: string;
  thumbnail?: { url: string; width: number; height: number };
  created_at: string;
  updated_at: string;
}

interface CanvaExport {
  id: string;
  status: 'in_progress' | 'completed' | 'failed';
  urls?: string[];
}

// ─── Design Management ─────────────────────────────────

/**
 * Create a new design from a template or blank canvas
 * Requires Canva Connect API access token
 */
export async function createDesign(options: {
  title: string;
  designType: 'instagram_post' | 'instagram_story' | 'instagram_reel_cover';
  templateId?: string;
  accessToken: string;
}): Promise<CanvaDesign> {
  const designTypeMap: Record<string, { width: number; height: number }> = {
    instagram_post: { width: 1080, height: 1080 },
    instagram_story: { width: 1080, height: 1920 },
    instagram_reel_cover: { width: 1080, height: 1920 },
  };

  const dimensions = designTypeMap[options.designType];

  const response = await axios.post(
    `${CANVA_BASE_URL}/designs`,
    {
      design_type: { type: 'preset', name: 'custom' },
      title: options.title,
      ...(dimensions && { width: dimensions.width, height: dimensions.height }),
    },
    {
      headers: {
        Authorization: `Bearer ${options.accessToken}`,
        'Content-Type': 'application/json',
      },
    }
  );

  return response.data.design;
}

/**
 * Export a design as PNG/JPG images
 */
export async function exportDesign(options: {
  designId: string;
  format: 'png' | 'jpg' | 'pdf';
  accessToken: string;
}): Promise<CanvaExport> {
  const response = await axios.post(
    `${CANVA_BASE_URL}/designs/${options.designId}/exports`,
    {
      format: { type: options.format },
    },
    {
      headers: {
        Authorization: `Bearer ${options.accessToken}`,
        'Content-Type': 'application/json',
      },
    }
  );

  return response.data.export;
}

/**
 * Check export status and get download URLs
 */
export async function getExportStatus(options: {
  designId: string;
  exportId: string;
  accessToken: string;
}): Promise<CanvaExport> {
  const response = await axios.get(
    `${CANVA_BASE_URL}/designs/${options.designId}/exports/${options.exportId}`,
    {
      headers: {
        Authorization: `Bearer ${options.accessToken}`,
      },
    }
  );

  return response.data.export;
}

/**
 * Wait for export to complete and return download URLs
 */
export async function waitForExport(options: {
  designId: string;
  exportId: string;
  accessToken: string;
  maxWaitMs?: number;
}): Promise<string[]> {
  const start = Date.now();
  const maxWait = options.maxWaitMs || 60000;

  while (Date.now() - start < maxWait) {
    const status = await getExportStatus(options);
    if (status.status === 'completed' && status.urls) {
      return status.urls;
    }
    if (status.status === 'failed') {
      throw new Error(`Canva export ${options.exportId} failed`);
    }
    await new Promise(r => setTimeout(r, 3000));
  }

  throw new Error('Canva export timed out');
}

// ─── Design Spec Generator (No API needed) ─────────────

/**
 * Generate a design specification that can be used in Canva manually
 * or fed into any design tool. This works WITHOUT Canva API access.
 */
export interface DesignSpec {
  title: string;
  format: 'instagram_post' | 'instagram_story' | 'instagram_reel_cover';
  dimensions: { width: number; height: number };
  slides: Array<{
    slideNumber: number;
    headline: string;
    bodyText?: string;
    textPlacement: string;
    backgroundColor: string;
    textColor: string;
    accentColor: string;
    fontHeadline: string;
    fontBody: string;
    visualElements: string;
  }>;
}

export function generateDesignSpec(options: {
  title: string;
  format: 'instagram_post' | 'instagram_story' | 'instagram_reel_cover';
  slides: Array<{ headline: string; bodyText?: string; designNotes?: string }>;
  brand: {
    colors: { primary: string; secondary: string; accent: string; background: string; text: string };
    fonts: { headline: string; body: string };
  };
}): DesignSpec {
  const dimensionMap = {
    instagram_post: { width: 1080, height: 1080 },
    instagram_story: { width: 1080, height: 1920 },
    instagram_reel_cover: { width: 1080, height: 1920 },
  };

  return {
    title: options.title,
    format: options.format,
    dimensions: dimensionMap[options.format],
    slides: options.slides.map((slide, i) => ({
      slideNumber: i + 1,
      headline: slide.headline,
      bodyText: slide.bodyText,
      textPlacement: slide.designNotes || 'center',
      backgroundColor: i === 0 ? options.brand.colors.primary : options.brand.colors.background,
      textColor: options.brand.colors.text,
      accentColor: options.brand.colors.accent,
      fontHeadline: options.brand.fonts.headline,
      fontBody: options.brand.fonts.body,
      visualElements: slide.designNotes || '',
    })),
  };
}
