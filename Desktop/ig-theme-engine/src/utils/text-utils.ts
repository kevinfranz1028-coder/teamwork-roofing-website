/**
 * Truncate text to a max length, adding ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3).trimEnd() + '...';
}

/**
 * Count words in a string
 */
export function wordCount(text: string): number {
  return text.split(/\s+/).filter(w => w.length > 0).length;
}

/**
 * Build a caption from parts, respecting Instagram's 2200 char limit
 */
export function buildCaption(parts: {
  hookLine: string;
  body: string;
  cta: string;
  seoKeywords?: string[];
  hashtags?: string[];
}): string {
  const sections = [
    parts.hookLine,
    '',
    parts.body,
    '',
    parts.cta,
  ];

  if (parts.hashtags && parts.hashtags.length > 0) {
    sections.push('');
    sections.push(
      parts.hashtags
        .slice(0, 5)
        .map(h => (h.startsWith('#') ? h : `#${h}`))
        .join(' ')
    );
  }

  const caption = sections.join('\n');

  // Instagram caption limit
  if (caption.length > 2200) {
    return caption.slice(0, 2197) + '...';
  }

  return caption;
}

/**
 * Extract hashtags from text
 */
export function extractHashtags(text: string): string[] {
  const matches = text.match(/#[\w]+/g);
  return matches || [];
}

/**
 * Remove hashtags from text
 */
export function stripHashtags(text: string): string {
  return text.replace(/#[\w]+/g, '').replace(/\s+/g, ' ').trim();
}

/**
 * Convert text to URL-safe slug
 */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim();
}

/**
 * Estimate reading time in seconds
 */
export function readingTimeSeconds(text: string): number {
  const words = wordCount(text);
  const wordsPerSecond = 3.5; // average reading speed
  return Math.ceil(words / wordsPerSecond);
}

/**
 * Check if text is within Instagram caption SEO best practices
 */
export function captionHealthCheck(caption: string): {
  length: number;
  maxLength: number;
  wordCount: number;
  hashtagCount: number;
  hasHook: boolean;
  hasCta: boolean;
  issues: string[];
} {
  const hashtags = extractHashtags(caption);
  const words = wordCount(caption);
  const issues: string[] = [];

  if (caption.length > 2200) issues.push('Caption exceeds 2200 character limit');
  if (hashtags.length > 5) issues.push('More than 5 hashtags (use 3-5 max)');
  if (words < 20) issues.push('Caption is very short — add more value');
  if (words > 300) issues.push('Caption may be too long for engagement');
  if (!caption.includes('?') && !caption.toLowerCase().includes('dm') && !caption.toLowerCase().includes('save')) {
    issues.push('No clear CTA detected');
  }

  return {
    length: caption.length,
    maxLength: 2200,
    wordCount: words,
    hashtagCount: hashtags.length,
    hasHook: caption.split('\n')[0]!.length > 10,
    hasCta: caption.toLowerCase().includes('dm') || caption.toLowerCase().includes('save') || caption.toLowerCase().includes('follow') || caption.includes('?'),
    issues,
  };
}
