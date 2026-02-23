// Shared interfaces for the rendering pipeline

export interface SlideContent {
  slideNumber: number;
  headline: string;
  bodyText: string;
  designNotes?: string;
  type: 'hook' | 'value' | 'cta';
}

export interface CarouselScript {
  slides: SlideContent[];
  caption: string;
  hashtags: string[];
}

export interface StorySlideContent {
  slideNumber: number;
  text: string;
  interactiveElement?: 'poll' | 'question' | 'slider' | 'dm_trigger' | 'link' | 'none';
  interactiveData?: {
    question?: string;
    options?: string[];
    buttonText?: string;
    keyword?: string;
  };
  designNotes?: string;
}

export interface StoryScript {
  slides: StorySlideContent[];
  dmTriggerKeyword: string;
}

export interface ReelSegment {
  text: string;
  durationSeconds: number;
  visualDescription: string;
}

export interface ReelScript {
  hook: string;
  segments: ReelSegment[];
  cta: string;
  totalLength: number;
  voiceoverText: string;
}

export interface RenderConfig {
  brandColors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
  };
  fonts: {
    headline: string;
    body: string;
  };
  handle: string;
}

export interface RenderedAssets {
  scriptId: number;
  contentType: 'carousel' | 'reel' | 'story';
  localPaths: string[];
  publicUrls: string[];
  thumbnailUrl?: string;
}

export interface DailyRenderedPackage {
  date: string;
  carousel?: RenderedAssets;
  reel?: RenderedAssets;
  stories?: RenderedAssets;
}
