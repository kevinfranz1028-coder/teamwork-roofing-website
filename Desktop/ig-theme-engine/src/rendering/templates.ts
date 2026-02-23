import type { RenderConfig, SlideContent, StorySlideContent } from './types.js';

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function baseStyles(config: RenderConfig): string {
  return `
    @import url('https://fonts.googleapis.com/css2?family=${encodeURIComponent(config.fonts.headline)}:wght@700;900&family=${encodeURIComponent(config.fonts.body)}:wght@400;600&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { overflow: hidden; }
  `;
}

// ─── Carousel Slide Templates ─────────────────────────

export function hookSlideHtml(slide: SlideContent, config: RenderConfig): string {
  return `<!DOCTYPE html>
<html><head><style>
  ${baseStyles(config)}
  body {
    width: 1080px; height: 1080px;
    background: linear-gradient(135deg, ${config.brandColors.primary}, ${config.brandColors.accent});
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    padding: 80px; font-family: '${config.fonts.headline}', sans-serif;
    color: #FFFFFF; text-align: center;
  }
  .headline {
    font-size: 72px; font-weight: 900; line-height: 1.15;
    text-shadow: 0 4px 20px rgba(0,0,0,0.3);
    max-width: 920px;
  }
  .subtitle {
    font-size: 28px; font-weight: 600; margin-top: 30px;
    font-family: '${config.fonts.body}', sans-serif;
    opacity: 0.9;
  }
  .swipe-hint {
    position: absolute; bottom: 50px; right: 60px;
    font-size: 20px; opacity: 0.7;
    font-family: '${config.fonts.body}', sans-serif;
  }
  .watermark {
    position: absolute; bottom: 24px; left: 40px;
    font-size: 16px; opacity: 0.5;
    font-family: '${config.fonts.body}', sans-serif;
  }
</style></head><body>
  <div class="headline">${escapeHtml(slide.headline)}</div>
  ${slide.bodyText ? `<div class="subtitle">${escapeHtml(slide.bodyText)}</div>` : ''}
  <div class="swipe-hint">Swipe &rarr;</div>
  <div class="watermark">${escapeHtml(config.handle)}</div>
</body></html>`;
}

export function valueSlideHtml(slide: SlideContent, config: RenderConfig): string {
  return `<!DOCTYPE html>
<html><head><style>
  ${baseStyles(config)}
  body {
    width: 1080px; height: 1080px;
    background: ${config.brandColors.background};
    display: flex; flex-direction: column; justify-content: center;
    padding: 80px 70px; font-family: '${config.fonts.body}', sans-serif;
    color: ${config.brandColors.text};
  }
  .slide-number {
    font-size: 48px; font-weight: 900; color: ${config.brandColors.accent};
    font-family: '${config.fonts.headline}', sans-serif;
    margin-bottom: 20px;
  }
  .headline {
    font-size: 52px; font-weight: 700; line-height: 1.2;
    font-family: '${config.fonts.headline}', sans-serif;
    margin-bottom: 28px; max-width: 900px;
  }
  .body-text {
    font-size: 30px; line-height: 1.55; opacity: 0.85;
    max-width: 900px;
  }
  .divider {
    width: 80px; height: 4px; background: ${config.brandColors.accent};
    margin: 24px 0;
  }
  .watermark {
    position: absolute; bottom: 24px; right: 40px;
    font-size: 16px; opacity: 0.4;
  }
</style></head><body>
  <div class="slide-number">${String(slide.slideNumber).padStart(2, '0')}</div>
  <div class="headline">${escapeHtml(slide.headline)}</div>
  <div class="divider"></div>
  <div class="body-text">${escapeHtml(slide.bodyText)}</div>
  <div class="watermark">${escapeHtml(config.handle)}</div>
</body></html>`;
}

export function ctaSlideHtml(slide: SlideContent, config: RenderConfig): string {
  return `<!DOCTYPE html>
<html><head><style>
  ${baseStyles(config)}
  body {
    width: 1080px; height: 1080px;
    background: linear-gradient(135deg, ${config.brandColors.accent}, ${config.brandColors.primary});
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    padding: 80px; font-family: '${config.fonts.headline}', sans-serif;
    color: #FFFFFF; text-align: center;
  }
  .headline {
    font-size: 58px; font-weight: 900; line-height: 1.2;
    margin-bottom: 40px; max-width: 900px;
  }
  .cta-button {
    background: #FFFFFF; color: ${config.brandColors.primary};
    padding: 24px 60px; border-radius: 50px;
    font-size: 32px; font-weight: 700;
    box-shadow: 0 8px 30px rgba(0,0,0,0.2);
  }
  .dm-keyword {
    margin-top: 30px; font-size: 26px; opacity: 0.9;
    font-family: '${config.fonts.body}', sans-serif;
  }
  .watermark {
    position: absolute; bottom: 24px; right: 40px;
    font-size: 16px; opacity: 0.5;
    font-family: '${config.fonts.body}', sans-serif;
  }
</style></head><body>
  <div class="headline">${escapeHtml(slide.headline)}</div>
  <div class="cta-button">${escapeHtml(slide.bodyText || 'DM Me Now')}</div>
  <div class="dm-keyword">${escapeHtml(slide.designNotes || '')}</div>
  <div class="watermark">${escapeHtml(config.handle)}</div>
</body></html>`;
}

// ─── Story Slide Templates ────────────────────────────

export function storySlideHtml(slide: StorySlideContent, config: RenderConfig): string {
  const interactiveHtml = getInteractiveElementHtml(slide, config);

  return `<!DOCTYPE html>
<html><head><style>
  ${baseStyles(config)}
  body {
    width: 1080px; height: 1920px;
    background: linear-gradient(180deg, ${config.brandColors.primary} 0%, ${config.brandColors.background} 100%);
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

export function reelOverlayHtml(text: string, config: RenderConfig): string {
  return `<!DOCTYPE html>
<html><head><style>
  ${baseStyles(config)}
  body {
    width: 1080px; height: 1920px;
    background: transparent;
    display: flex; flex-direction: column; justify-content: flex-end;
    padding: 0 60px 200px; font-family: '${config.fonts.headline}', sans-serif;
    color: #FFFFFF; text-align: left;
  }
  .overlay-text {
    font-size: 56px; font-weight: 900; line-height: 1.25;
    text-shadow: 0 3px 15px rgba(0,0,0,0.6), 0 1px 3px rgba(0,0,0,0.4);
    max-width: 900px;
    background: linear-gradient(transparent, rgba(0,0,0,0.4));
    padding: 40px; border-radius: 20px;
  }
</style></head><body>
  <div class="overlay-text">${escapeHtml(text)}</div>
</body></html>`;
}
