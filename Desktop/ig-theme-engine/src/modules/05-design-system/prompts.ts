export const DESIGN_SYSTEM_PROMPT = `You are a brand design specialist for Instagram theme pages.

Create design specifications that are:
- Instantly recognizable in the feed (visual consistency)
- Optimized for mobile viewing (1080x1080 posts, 1080x1920 stories)
- High contrast for readability on small screens
- Accessible (WCAG AA minimum for text contrast)
- Consistent across carousels, reels, and stories`;

export function brandDesignPrompt(niche: string, brandVoice: string): string {
  return `Create a complete visual brand system for a "${niche}" Instagram theme page.

Brand voice: ${brandVoice}

Return JSON with:
{
  "colorPalette": {
    "primary": "#hex — main brand color, used for headlines and key elements",
    "secondary": "#hex — supporting color for backgrounds and accents",
    "accent": "#hex — highlight color for CTAs and emphasis",
    "background": "#hex — main background (dark preferred for modern feel)",
    "text": "#hex — primary text color",
    "textSecondary": "#hex — secondary/muted text"
  },
  "typography": {
    "headlineFont": "Font name — bold, high-impact",
    "bodyFont": "Font name — clean, readable",
    "accentFont": "Font name — for callouts and highlights",
    "headlineSize": "relative scale description",
    "bodySize": "relative scale description"
  },
  "layoutRules": {
    "carouselGrid": "layout description for carousel slides",
    "storyLayout": "layout description for stories",
    "textPlacement": "where text sits on slides",
    "whitespaceRule": "spacing guidelines",
    "imageStyle": "photography/illustration style"
  },
  "templateVariations": [
    { "name": "template name", "useCase": "when to use", "layout": "description" }
  ],
  "moodBoard": {
    "aesthetic": "overall visual mood",
    "keywords": ["visual", "descriptors"],
    "avoidStyles": ["styles to never use"]
  }
}`;
}

export function templatePrompt(slideData: { headline: string; bodyText?: string; type: string }, brand: any): string {
  return `Generate exact design specifications for this slide:

SLIDE DATA:
- Headline: "${slideData.headline}"
- Body: "${slideData.bodyText || 'none'}"
- Type: ${slideData.type}

BRAND SYSTEM:
${JSON.stringify(brand, null, 2)}

Return JSON with:
{
  "canvasSize": { "width": 1080, "height": 1080 },
  "background": { "type": "solid|gradient", "value": "color or gradient stops" },
  "elements": [
    {
      "type": "text|shape|icon",
      "content": "the actual text or shape description",
      "position": { "x": number, "y": number },
      "size": { "width": number, "height": number },
      "style": { "font": "name", "fontSize": number, "fontWeight": "bold|normal", "color": "#hex", "align": "left|center|right" }
    }
  ]
}`;
}
