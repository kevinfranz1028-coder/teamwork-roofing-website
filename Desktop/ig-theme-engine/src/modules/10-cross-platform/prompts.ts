export const CROSS_PLATFORM_SYSTEM = `You are a cross-platform content strategist. You adapt Instagram content for other platforms while maintaining the original's impact.

PLATFORM DIFFERENCES:
- TikTok: More casual, trending sounds OK, vertical video preferred, hook in first 1 second
- YouTube Shorts: Up to 60 seconds, searchable titles matter, more educational tone
- Pinterest: Vertical images, keyword-rich descriptions, evergreen focus, 1000x1500 pins
- Twitter/X: Thread format for carousels, short-form video clips, conversation-starting hooks

RULES:
- Never post identical content across platforms
- Adapt the format AND the framing for each platform's culture
- Respect each platform's native content style
- Stagger posting times (don't dump everywhere at once)`;

export function adaptContentPrompt(
  originalScript: any,
  originalPlatform: string,
  targetPlatform: string
): string {
  return `Adapt this ${originalPlatform} content for ${targetPlatform}.

ORIGINAL CONTENT:
${JSON.stringify(originalScript, null, 2)}

ADAPTATION RULES for ${targetPlatform}:
${getPlatformRules(targetPlatform)}

Return JSON:
{
  "platform": "${targetPlatform}",
  "adaptedFormat": "the format on this platform (e.g., 'short video', 'pin', 'thread')",
  "title": "platform-optimized title",
  "hook": "platform-specific hook text",
  "body": "adapted body content",
  "caption": "platform-specific caption",
  "hashtags": ["platform-appropriate hashtags"],
  "keywords": ["SEO keywords for this platform"],
  "schedulingNote": "best time/day to post this on ${targetPlatform}",
  "adaptationNotes": "what was changed and why"
}`;
}

function getPlatformRules(platform: string): string {
  const rules: Record<string, string> = {
    tiktok: `- Hook must land in first 1 second (faster than Instagram)
- Trending sounds are acceptable here (unlike IG)
- More casual, less polished tone
- Text overlays should be larger (smaller screens)
- End with a question or controversial take for comments
- 15-30 seconds optimal for discovery`,

    youtube_shorts: `- Title must be searchable (SEO matters more here)
- Can be up to 60 seconds
- More educational/informative tone
- Subscribe CTA is standard
- Thumbnail frame matters (auto-selected)
- Description should include keywords`,

    pinterest: `- Vertical image format (1000x1500)
- Keyword-rich description (Pinterest is a search engine)
- Evergreen content performs best
- Link to website/landing page
- Create multiple pins per piece of content
- Board organization matters for SEO`,

    twitter: `- Thread format for carousel content
- First tweet must hook independently
- Include a visual (image or short clip)
- End thread with CTA to follow
- More conversational, opinion-driven tone
- Quote tweets and engagement drive reach`,
  };

  return rules[platform] || 'Adapt to platform-native format and culture.';
}
