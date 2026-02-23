import { askClaudeJSON } from '../../integrations/claude-client.js';
import { getActiveBrand, updateBrand } from '../../config/brand.js';
import { DESIGN_SYSTEM_PROMPT, brandDesignPrompt } from './prompts.js';

interface DesignSystem {
  colorPalette: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
    textSecondary: string;
  };
  typography: {
    headlineFont: string;
    bodyFont: string;
    accentFont: string;
    headlineSize: string;
    bodySize: string;
  };
  layoutRules: {
    carouselGrid: string;
    storyLayout: string;
    textPlacement: string;
    whitespaceRule: string;
    imageStyle: string;
  };
  templateVariations: Array<{ name: string; useCase: string; layout: string }>;
  moodBoard: {
    aesthetic: string;
    keywords: string[];
    avoidStyles: string[];
  };
}

export async function generateDesignSystem(niche: string): Promise<DesignSystem> {
  const brand = getActiveBrand();

  const result = await askClaudeJSON<DesignSystem>({
    systemPrompt: DESIGN_SYSTEM_PROMPT,
    userPrompt: brandDesignPrompt(niche, brand.voice.tone),
    maxTokens: 4096,
  });

  // Update the brand system with generated design
  updateBrand({
    colors: {
      primary: result.colorPalette.primary,
      secondary: result.colorPalette.secondary,
      accent: result.colorPalette.accent,
      background: result.colorPalette.background,
      text: result.colorPalette.text,
    },
    fonts: {
      headline: result.typography.headlineFont,
      body: result.typography.bodyFont,
      accent: result.typography.accentFont,
    },
  });

  return result;
}

export function getDesignDirection(): any {
  const brand = getActiveBrand();
  return {
    colors: brand.colors,
    fonts: brand.fonts,
    visualStyle: brand.visualStyle,
    contentRules: brand.contentRules,
  };
}
