import sharp from 'sharp';
import path from 'path';
import { existsSync, mkdirSync } from 'fs';
import { CONFIG } from '../config/env.js';

interface ImageSize {
  width: number;
  height: number;
}

const INSTAGRAM_SIZES: Record<string, ImageSize> = {
  post: { width: 1080, height: 1080 },
  portrait: { width: 1080, height: 1350 },
  story: { width: 1080, height: 1920 },
  reelCover: { width: 1080, height: 1920 },
};

/**
 * Resize an image to Instagram specifications
 */
export async function resizeForInstagram(
  inputPath: string,
  format: keyof typeof INSTAGRAM_SIZES,
  outputPath?: string
): Promise<string> {
  const size = INSTAGRAM_SIZES[format];
  if (!size) throw new Error(`Unknown format: ${format}`);

  const output = outputPath || generateOutputPath(inputPath, format);
  ensureDir(path.dirname(output));

  await sharp(inputPath)
    .resize(size.width, size.height, { fit: 'cover', position: 'center' })
    .jpeg({ quality: 95 })
    .toFile(output);

  return output;
}

/**
 * Create a solid color background image (for text-based slides)
 */
export async function createColorBackground(
  color: string,
  format: keyof typeof INSTAGRAM_SIZES,
  outputPath: string
): Promise<string> {
  const size = INSTAGRAM_SIZES[format] || INSTAGRAM_SIZES.post;
  ensureDir(path.dirname(outputPath));

  // Parse hex color
  const hex = color.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  await sharp({
    create: {
      width: size.width,
      height: size.height,
      channels: 3,
      background: { r, g, b },
    },
  })
    .jpeg({ quality: 95 })
    .toFile(outputPath);

  return outputPath;
}

/**
 * Optimize an image for web/Instagram upload (reduce file size)
 */
export async function optimizeImage(inputPath: string, outputPath?: string): Promise<string> {
  const output = outputPath || inputPath.replace(/\.\w+$/, '_optimized.jpg');
  ensureDir(path.dirname(output));

  await sharp(inputPath)
    .jpeg({ quality: 85, mozjpeg: true })
    .toFile(output);

  return output;
}

/**
 * Get image metadata (dimensions, format, size)
 */
export async function getImageInfo(imagePath: string): Promise<{
  width: number;
  height: number;
  format: string;
  size: number;
}> {
  const metadata = await sharp(imagePath).metadata();
  return {
    width: metadata.width || 0,
    height: metadata.height || 0,
    format: metadata.format || 'unknown',
    size: metadata.size || 0,
  };
}

/**
 * Composite text onto an image (basic overlay)
 */
export async function addTextOverlay(
  inputPath: string,
  text: string,
  outputPath: string,
  options?: {
    fontSize?: number;
    color?: string;
    position?: 'top' | 'center' | 'bottom';
  }
): Promise<string> {
  const fontSize = options?.fontSize || 48;
  const color = options?.color || '#FFFFFF';
  const position = options?.position || 'center';

  const metadata = await sharp(inputPath).metadata();
  const width = metadata.width || 1080;
  const height = metadata.height || 1080;

  const yPos = position === 'top' ? height * 0.15 : position === 'bottom' ? height * 0.8 : height * 0.5;

  const svgOverlay = `
    <svg width="${width}" height="${height}">
      <text x="50%" y="${yPos}" text-anchor="middle"
        font-family="Arial, Helvetica, sans-serif" font-size="${fontSize}" font-weight="bold"
        fill="${color}" stroke="rgba(0,0,0,0.3)" stroke-width="2">
        ${escapeXml(text)}
      </text>
    </svg>
  `;

  ensureDir(path.dirname(outputPath));

  await sharp(inputPath)
    .composite([{ input: Buffer.from(svgOverlay), gravity: 'center' }])
    .jpeg({ quality: 95 })
    .toFile(outputPath);

  return outputPath;
}

function generateOutputPath(inputPath: string, suffix: string): string {
  const ext = path.extname(inputPath);
  const base = path.basename(inputPath, ext);
  return path.join(CONFIG.paths.assets, `${base}_${suffix}${ext}`);
}

function ensureDir(dir: string) {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}
