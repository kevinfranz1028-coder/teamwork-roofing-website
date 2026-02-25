import type { RenderConfig, SlideContent, StorySlideContent } from './types.js';

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function hexToRgb(hex: string): string {
  const h = hex.replace('#', '');
  return `${parseInt(h.substring(0, 2), 16)},${parseInt(h.substring(2, 4), 16)},${parseInt(h.substring(4, 6), 16)}`;
}

function baseStyles(config: RenderConfig): string {
  return `
    @import url('https://fonts.googleapis.com/css2?family=${encodeURIComponent(config.fonts.headline)}:wght@700;900&family=${encodeURIComponent(config.fonts.body)}:wght@400;600&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { overflow: hidden; }
  `;
}

// ─── Carousel Slide Templates ─────────────────────────

export function hookSlideHtml(slide: SlideContent, config: RenderConfig, backgroundImageUrl?: string): string {
  const bgStyle = backgroundImageUrl
    ? `background: url('${backgroundImageUrl}') center/cover no-repeat;`
    : `background: linear-gradient(135deg, ${config.brandColors.primary}, ${config.brandColors.accent});`;

  return `<!DOCTYPE html>
<html><head><style>
  ${baseStyles(config)}
  body {
    width: 1080px; height: 1080px;
    ${bgStyle}
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    padding: 80px; font-family: '${config.fonts.headline}', sans-serif;
    color: #FFFFFF; text-align: center;
    position: relative;
  }
  ${backgroundImageUrl ? `.overlay {
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.45);
    z-index: 1;
  }` : ''}
  .content { position: relative; z-index: 2; }
  .headline {
    font-size: 72px; font-weight: 900; line-height: 1.15;
    text-shadow: 0 4px 20px rgba(0,0,0,0.5);
    max-width: 920px;
  }
  .subtitle {
    font-size: 28px; font-weight: 600; margin-top: 30px;
    font-family: '${config.fonts.body}', sans-serif;
    opacity: 0.9; text-shadow: 0 2px 8px rgba(0,0,0,0.4);
  }
  .swipe-hint {
    position: absolute; bottom: 50px; right: 60px;
    font-size: 20px; opacity: 0.7;
    font-family: '${config.fonts.body}', sans-serif;
    z-index: 2; text-shadow: 0 1px 4px rgba(0,0,0,0.5);
  }
  .watermark {
    position: absolute; bottom: 24px; left: 40px;
    font-size: 16px; opacity: 0.5;
    font-family: '${config.fonts.body}', sans-serif;
    z-index: 2; text-shadow: 0 1px 4px rgba(0,0,0,0.5);
  }
</style></head><body>
  ${backgroundImageUrl ? '<div class="overlay"></div>' : ''}
  <div class="content">
    <div class="headline">${escapeHtml(slide.headline)}</div>
    ${slide.bodyText ? `<div class="subtitle">${escapeHtml(slide.bodyText)}</div>` : ''}
  </div>
  <div class="swipe-hint">Swipe &rarr;</div>
  <div class="watermark">${escapeHtml(config.handle)}</div>
</body></html>`;
}

export function valueSlideHtml(slide: SlideContent, config: RenderConfig, backgroundImageUrl?: string): string {
  const bgStyle = backgroundImageUrl
    ? `background: url('${backgroundImageUrl}') center/cover no-repeat;`
    : `background: ${config.brandColors.background};`;
  const textColor = backgroundImageUrl ? '#FFFFFF' : config.brandColors.text;

  return `<!DOCTYPE html>
<html><head><style>
  ${baseStyles(config)}
  body {
    width: 1080px; height: 1080px;
    ${bgStyle}
    display: flex; flex-direction: column; justify-content: center;
    padding: 80px 70px; font-family: '${config.fonts.body}', sans-serif;
    color: ${textColor};
    position: relative;
  }
  ${backgroundImageUrl ? `.overlay {
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(to bottom, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.7) 100%);
    z-index: 1;
  }` : ''}
  .content { position: relative; z-index: 2; }
  .slide-number {
    font-size: 48px; font-weight: 900;
    color: ${backgroundImageUrl ? '#FFFFFF' : config.brandColors.accent};
    font-family: '${config.fonts.headline}', sans-serif;
    margin-bottom: 20px;
    ${backgroundImageUrl ? 'text-shadow: 0 2px 10px rgba(0,0,0,0.5);' : ''}
  }
  .headline {
    font-size: 52px; font-weight: 700; line-height: 1.2;
    font-family: '${config.fonts.headline}', sans-serif;
    margin-bottom: 28px; max-width: 900px;
    ${backgroundImageUrl ? 'text-shadow: 0 3px 15px rgba(0,0,0,0.5);' : ''}
  }
  .body-text {
    font-size: 30px; line-height: 1.55; opacity: 0.85;
    max-width: 900px;
    ${backgroundImageUrl ? 'text-shadow: 0 2px 8px rgba(0,0,0,0.4);' : ''}
  }
  .divider {
    width: 80px; height: 4px;
    background: ${backgroundImageUrl ? 'rgba(255,255,255,0.6)' : config.brandColors.accent};
    margin: 24px 0;
  }
  .watermark {
    position: absolute; bottom: 24px; right: 40px;
    font-size: 16px; opacity: 0.4;
    z-index: 2;
    ${backgroundImageUrl ? 'text-shadow: 0 1px 4px rgba(0,0,0,0.5);' : ''}
  }
</style></head><body>
  ${backgroundImageUrl ? '<div class="overlay"></div>' : ''}
  <div class="content">
    <div class="slide-number">${String(slide.slideNumber).padStart(2, '0')}</div>
    <div class="headline">${escapeHtml(slide.headline)}</div>
    <div class="divider"></div>
    <div class="body-text">${escapeHtml(slide.bodyText)}</div>
  </div>
  <div class="watermark">${escapeHtml(config.handle)}</div>
</body></html>`;
}

export function ctaSlideHtml(slide: SlideContent, config: RenderConfig, backgroundImageUrl?: string): string {
  const bgStyle = backgroundImageUrl
    ? `background: url('${backgroundImageUrl}') center/cover no-repeat;`
    : `background: linear-gradient(135deg, ${config.brandColors.accent}, ${config.brandColors.primary});`;

  return `<!DOCTYPE html>
<html><head><style>
  ${baseStyles(config)}
  body {
    width: 1080px; height: 1080px;
    ${bgStyle}
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    padding: 80px; font-family: '${config.fonts.headline}', sans-serif;
    color: #FFFFFF; text-align: center;
    position: relative;
  }
  ${backgroundImageUrl ? `.overlay {
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(${hexToRgb(config.brandColors.primary)}, 0.6);
    z-index: 1;
  }` : ''}
  .content { position: relative; z-index: 2; }
  .headline {
    font-size: 58px; font-weight: 900; line-height: 1.2;
    margin-bottom: 40px; max-width: 900px;
    text-shadow: 0 3px 15px rgba(0,0,0,0.5);
  }
  .cta-button {
    background: #FFFFFF; color: ${config.brandColors.primary};
    padding: 24px 60px; border-radius: 50px;
    font-size: 32px; font-weight: 700;
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
  }
  .dm-keyword {
    margin-top: 30px; font-size: 26px; opacity: 0.9;
    font-family: '${config.fonts.body}', sans-serif;
    text-shadow: 0 2px 8px rgba(0,0,0,0.4);
  }
  .watermark {
    position: absolute; bottom: 24px; right: 40px;
    font-size: 16px; opacity: 0.5;
    font-family: '${config.fonts.body}', sans-serif;
    z-index: 2; text-shadow: 0 1px 4px rgba(0,0,0,0.5);
  }
</style></head><body>
  ${backgroundImageUrl ? '<div class="overlay"></div>' : ''}
  <div class="content">
    <div class="headline">${escapeHtml(slide.headline)}</div>
    <div class="cta-button">${escapeHtml(slide.bodyText || 'DM Me Now')}</div>
    ${!backgroundImageUrl && slide.designNotes ? `<div class="dm-keyword">${escapeHtml(slide.designNotes)}</div>` : ''}
  </div>
  <div class="watermark">${escapeHtml(config.handle)}</div>
</body></html>`;
}

// ─── Story Slide Templates ────────────────────────────

export function storySlideHtml(slide: StorySlideContent, config: RenderConfig, bgUrl?: string): string {
  const interactiveHtml = getInteractiveElementHtml(slide, config);
  const bgStyle = bgUrl
    ? `background: url('${bgUrl}') center/cover no-repeat;`
    : `background: linear-gradient(180deg, ${config.brandColors.primary} 0%, ${config.brandColors.background} 100%);`;

  return `<!DOCTYPE html>
<html><head><style>
  ${baseStyles(config)}
  body {
    width: 1080px; height: 1920px;
    ${bgStyle}
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    padding: 120px 70px; font-family: '${config.fonts.body}', sans-serif;
    color: ${config.brandColors.text}; text-align: center;
  }
  .story-text {
    font-size: 48px; font-weight: 700; line-height: 1.35;
    font-family: '${config.fonts.headline}', sans-serif;
    max-width: 940px; margin-bottom: 60px;
    color: #FFFFFF; text-shadow: 0 2px 10px rgba(0,0,0,0.2);
  }
  .interactive-container {
    width: 100%; max-width: 800px;
  }
  .poll-option {
    background: rgba(255,255,255,0.15); backdrop-filter: blur(10px);
    border: 2px solid rgba(255,255,255,0.3); border-radius: 16px;
    padding: 24px 40px; margin: 12px 0; font-size: 30px; font-weight: 600;
    color: #FFFFFF; text-align: center;
  }
  .question-box {
    background: rgba(255,255,255,0.1); border: 2px solid rgba(255,255,255,0.3);
    border-radius: 20px; padding: 40px;
    font-size: 26px; color: rgba(255,255,255,0.6);
    text-align: center;
  }
  .slider-track {
    width: 100%; height: 8px; background: rgba(255,255,255,0.2);
    border-radius: 4px; position: relative; margin: 30px 0;
  }
  .slider-emoji {
    position: absolute; top: -20px; left: 60%;
    font-size: 48px;
  }
  .dm-trigger-btn {
    background: ${config.brandColors.accent}; color: #FFFFFF;
    padding: 28px 60px; border-radius: 50px;
    font-size: 34px; font-weight: 700;
    box-shadow: 0 6px 25px rgba(0,0,0,0.25);
  }
  .dm-hint {
    margin-top: 20px; font-size: 22px; opacity: 0.7;
  }
  .watermark {
    position: absolute; bottom: 40px; left: 50%;
    transform: translateX(-50%); font-size: 16px; opacity: 0.4;
    color: #FFFFFF;
  }
</style></head><body>
  <div class="story-text">${escapeHtml(slide.text)}</div>
  <div class="interactive-container">${interactiveHtml}</div>
  <div class="watermark">${escapeHtml(config.handle)}</div>
</body></html>`;
}

function getInteractiveElementHtml(slide: StorySlideContent, config: RenderConfig): string {
  switch (slide.interactiveElement) {
    case 'poll':
      return (slide.interactiveData?.options || ['Yes', 'No'])
        .map(opt => `<div class="poll-option">${escapeHtml(opt)}</div>`)
        .join('');
    case 'question':
      return `<div class="question-box">${escapeHtml(slide.interactiveData?.question || 'Type your answer...')}</div>`;
    case 'slider':
      return `
        <div class="slider-track">
          <div class="slider-emoji">🔥</div>
        </div>`;
    case 'dm_trigger':
      return `
        <div class="dm-trigger-btn">${escapeHtml(slide.interactiveData?.buttonText || 'DM Me')}</div>
        <div class="dm-hint">DM "${escapeHtml(slide.interactiveData?.keyword || 'SEND')}" to get it free</div>`;
    default:
      return '';
  }
}

// ─── Reel Text Overlay Template ───────────────────────

export function reelOverlayHtml(
  text: string,
  segmentType: 'hook' | 'body' | 'cta' = 'body',
  segmentIndex: number = 0,
  totalSegments: number = 1,
  brandHandle: string = '@ThePlantICU'
): string {
  const fontSize = segmentType === 'hook' ? '42px' : segmentType === 'cta' ? '36px' : '32px';
  const fontWeight = segmentType === 'hook' ? '800' : '600';
  const maxWidth = segmentType === 'hook' ? '85%' : '80%';
  const bottomOffset = segmentType === 'cta' ? '18%' : '12%';

  return `<!DOCTYPE html>
<html>
<head>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      width: 1080px;
      height: 1920px;
      background: transparent;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      align-items: center;
      font-family: 'Inter', -apple-system, sans-serif;
      overflow: hidden;
    }

    .gradient-overlay {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 40%;
      background: linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.4) 60%, rgba(0,0,0,0.7) 100%);
      pointer-events: none;
    }

    .subtitle {
      position: absolute;
      bottom: ${bottomOffset};
      left: 50%;
      transform: translateX(-50%);
      max-width: ${maxWidth};
      text-align: center;
      color: white;
      font-size: ${fontSize};
      font-weight: ${fontWeight};
      line-height: 1.3;
      text-shadow:
        0 2px 8px rgba(0,0,0,0.8),
        0 1px 3px rgba(0,0,0,0.9);
      letter-spacing: -0.02em;
      word-wrap: break-word;
    }

    .watermark {
      position: absolute;
      top: 48px;
      right: 36px;
      color: rgba(255,255,255,0.7);
      font-size: 22px;
      font-weight: 600;
      text-shadow: 0 1px 4px rgba(0,0,0,0.6);
      letter-spacing: 0.01em;
    }
  </style>
</head>
<body>
  <div class="gradient-overlay"></div>
  ${text ? `<div class="subtitle">${escapeHtml(text)}</div>` : ''}
  ${segmentType === 'cta' || segmentIndex === 0 ? `<div class="watermark">${escapeHtml(brandHandle)}</div>` : ''}
</body>
</html>`;
}
