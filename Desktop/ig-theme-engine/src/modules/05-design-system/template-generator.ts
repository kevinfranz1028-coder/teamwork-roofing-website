import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getActiveBrand } from '../../config/brand.js';
import { DESIGN_SYSTEM_PROMPT, templatePrompt } from './prompts.js';

interface SlideTemplate {
  canvasSize: { width: number; height: number };
  background: { type: string; value: string };
  elements: Array<{
    type: 'text' | 'shape' | 'icon';
    content: string;
    position: { x: number; y: number };
    size: { width: number; height: number };
    style: {
      font?: string;
      fontSize?: number;
      fontWeight?: string;
      color?: string;
      align?: string;
    };
  }>;
}

interface CarouselTemplate {
  slides: SlideTemplate[];
}

export async function generateCarouselTemplate(
  slides: Array<{ headline: string; bodyText?: string; type: string }>
): Promise<CarouselTemplate> {
  const brand = getActiveBrand();
  const templates: SlideTemplate[] = [];

  for (const slide of slides) {
    const template = await askClaudeJSON<SlideTemplate>({
      systemPrompt: DESIGN_SYSTEM_PROMPT,
      userPrompt: templatePrompt(slide, {
        colors: brand.colors,
        fonts: brand.fonts,
        visualStyle: brand.visualStyle,
      }),
      maxTokens: 1024,
    });
    templates.push(template);
  }

  return { slides: templates };
}

/**
 * Generate a quick design spec without API call
 * Uses brand system defaults for consistent output
 */
export function generateQuickTemplate(
  slides: Array<{ headline: string; bodyText?: string; type: string }>
): CarouselTemplate {
  const brand = getActiveBrand();

  return {
    slides: slides.map((slide, i) => ({
      canvasSize: { width: 1080, height: 1080 },
      background: {
        type: 'solid',
        value: i === 0 ? brand.colors.primary : brand.colors.background,
      },
      elements: [
        {
          type: 'text' as const,
          content: slide.headline,
          position: { x: 80, y: i === 0 ? 400 : 120 },
          size: { width: 920, height: 200 },
          style: {
            font: brand.fonts.headline,
            fontSize: i === 0 ? 64 : 48,
            fontWeight: 'bold',
            color: brand.colors.text,
            align: 'left',
          },
        },
        ...(slide.bodyText
          ? [
              {
                type: 'text' as const,
                content: slide.bodyText,
                position: { x: 80, y: i === 0 ? 620 : 360 },
                size: { width: 920, height: 300 },
                style: {
                  font: brand.fonts.body,
                  fontSize: 28,
                  fontWeight: 'normal',
                  color: brand.colors.text,
                  align: 'left',
                },
              },
            ]
          : []),
        ...(slide.type === 'cta'
          ? [
              {
                type: 'shape' as const,
                content: 'rounded_rectangle',
                position: { x: 80, y: 800 },
                size: { width: 400, height: 80 },
                style: { color: brand.colors.accent },
              },
            ]
          : []),
      ],
    })),
  };
}
