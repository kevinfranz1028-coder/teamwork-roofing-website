import React, { useEffect, useState } from 'react';

// ─── Types ──────────────────────────────────────────

interface OptionData {
  ideaId: number;
  scriptId: number;
  contentType: string;
  title: string;
  hook: string;
  sendTrigger: string;
  valueProp: string;
  emotionalTrigger: string;
  sendProbability: string;
  caption: string;
  hashtags: string[];
  dmTrigger: string;
  scriptJson: string;
  localPaths: string[];
  publicUrls: string[];
  ideaStatus: string;
}

type CardRenderState = 'idle' | 'rendering' | 'regenerating' | 'rendered' | 'posted' | 'scheduled' | 'error';

interface BatchData {
  batchId: string;
  status: string;
  selectedIdeaId: number | null;
  createdAt: string;
  options: OptionData[];
}

interface ScheduleItem {
  calendarId: number;
  scheduledDate: string;
  scheduledTime: string;
  contentType: string;
  status: string;
  scriptId: number;
  caption: string;
  hashtags: string[];
  scriptJson: string;
  dmTrigger: string;
  ideaId: number;
  title: string;
  hook: string;
  sendTrigger: string;
  sendProbability: string;
  localPaths: string[];
  publicUrls: string[];
}

interface QueueItem {
  id: number;
  idea_id: number;
  content_type: string;
  script_json: string;
  caption: string;
  hashtags: string;
  title: string;
  hook: string;
  idea_status: string;
  send_trigger: string;
  send_probability: string;
  dm_trigger_keyword: string;
  batch_id: string | null;
  local_paths: string[];
  public_urls: string[];
}

// ─── Helpers ────────────────────────────────────────

const typeColors: Record<string, string> = {
  carousel: 'bg-blue-600',
  reel: 'bg-pink-600',
  story: 'bg-orange-600',
  static: 'bg-green-600',
};

const probColors: Record<string, string> = {
  high: 'text-yellow-400',
  very_high: 'text-orange-400',
  extreme: 'text-red-400',
};

const toUrl = (p: string): string => {
  const assetsIdx = p.indexOf('data/assets/');
  if (assetsIdx !== -1) return '/' + p.slice(assetsIdx).replace('data/', '');
  return p;
};

const getAllSlides = (opt: { publicUrls: string[]; localPaths: string[] }): string[] => {
  const paths = opt.publicUrls && opt.publicUrls.length > 0 ? opt.publicUrls : opt.localPaths;
  if (!paths || paths.length === 0) return [];
  return paths.map(p => opt.publicUrls && opt.publicUrls.length > 0 ? p : toUrl(p));
};

const getThumbnail = (opt: { publicUrls: string[]; localPaths: string[] }): string | null => {
  const slides = getAllSlides(opt);
  return slides.length > 0 ? slides[0] : null;
};

const isVideo = (url: string): boolean => /\.(mp4|mov|webm)(\?|$)/i.test(url);

const handleDownload = (scriptId: number) => {
  window.open(`/api/download/${scriptId}`, '_blank');
};

function formatScheduleDate(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
}

// ─── Full-Screen Slide Preview Modal ────────────────

function SlidePreview({
  slides,
  startIndex,
  title,
  caption,
  hashtags,
  scriptId,
  onClose,
}: {
  slides: string[];
  startIndex: number;
  title: string;
  caption: string;
  hashtags: string[];
  scriptId?: number;
  onClose: () => void;
}) {
  const [current, setCurrent] = useState(startIndex);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight' && current < slides.length - 1) setCurrent(c => c + 1);
      if (e.key === 'ArrowLeft' && current > 0) setCurrent(c => c - 1);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [current, slides.length, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/95 flex flex-col items-center justify-center"
      onClick={onClose}
    >
      <div className="absolute top-4 right-4 flex items-center gap-2 z-10">
        {scriptId && (
          <button
            onClick={(e) => { e.stopPropagation(); handleDownload(scriptId); }}
            className="px-4 py-2 bg-cyan-900/60 hover:bg-cyan-800 border border-cyan-700 text-cyan-300 text-sm rounded-lg transition-colors"
          >
            Download
          </button>
        )}
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white text-2xl w-10 h-10 flex items-center justify-center"
        >
          X
        </button>
      </div>

      <div className="absolute top-4 left-1/2 -translate-x-1/2 text-gray-400 text-sm">
        Slide {current + 1} of {slides.length}
      </div>

      <div
        className="flex-1 flex items-center justify-center w-full px-16 py-12"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={() => setCurrent(c => Math.max(0, c - 1))}
          disabled={current === 0}
          className={`shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-2xl transition-colors ${
            current === 0
              ? 'text-gray-700 cursor-not-allowed'
              : 'text-gray-300 hover:text-white hover:bg-white/10'
          }`}
        >
          &lt;
        </button>

        <div className="flex-1 flex items-center justify-center mx-4 max-h-[80vh]">
          {isVideo(slides[current]) ? (
            <video
              src={slides[current]}
              controls
              autoPlay
              className="max-h-[80vh] max-w-full object-contain rounded-lg shadow-2xl"
            />
          ) : (
            <img
              src={slides[current]}
              alt={`${title} — Slide ${current + 1}`}
              className="max-h-[80vh] max-w-full object-contain rounded-lg shadow-2xl"
            />
          )}
        </div>

        <button
          onClick={() => setCurrent(c => Math.min(slides.length - 1, c + 1))}
          disabled={current === slides.length - 1}
          className={`shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-2xl transition-colors ${
            current === slides.length - 1
              ? 'text-gray-700 cursor-not-allowed'
              : 'text-gray-300 hover:text-white hover:bg-white/10'
          }`}
        >
          &gt;
        </button>
      </div>

      <div
        className="w-full px-8 pb-4 flex justify-center gap-2 overflow-x-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {slides.map((src, i) => (
          <button
            key={i}
            onClick={() => setCurrent(i)}
            className={`shrink-0 w-14 h-14 rounded-md overflow-hidden border-2 transition-all ${
              i === current ? 'border-purple-500 scale-110' : 'border-transparent opacity-50 hover:opacity-80'
            }`}
          >
            <img src={src} alt={`Thumb ${i + 1}`} className="w-full h-full object-cover" />
          </button>
        ))}
      </div>

      <div
        className="w-full max-w-2xl px-8 pb-6"
        onClick={(e) => e.stopPropagation()}
      >
        <details className="text-sm">
          <summary className="text-gray-500 cursor-pointer hover:text-gray-300 text-xs">
            Show caption preview
          </summary>
          <div className="mt-2 bg-gray-900/80 rounded-lg p-4 space-y-2 max-h-40 overflow-y-auto">
            <p className="text-gray-300 text-xs whitespace-pre-wrap">{caption}</p>
            {hashtags && hashtags.length > 0 && (
              <p className="text-blue-400 text-xs">
                {(Array.isArray(hashtags) ? hashtags : String(hashtags).split(/\s+/)).map(t => `#${t.replace(/#/g, '')}`).join(' ')}
              </p>
            )}
          </div>
        </details>
      </div>
    </div>
  );
}

// ─── Section 1: Content Options ─────────────────────

function ContentOptionsSection({
  onScheduled,
  onPublished,
}: {
  onScheduled: () => void;
  onPublished: () => void;
}) {
  const [batch, setBatch] = useState<BatchData | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [posting, setPosting] = useState<number | null>(null);
  const [scheduling, setScheduling] = useState<number | null>(null);
  const [cardState, setCardState] = useState<Record<number, { renderState: CardRenderState; message?: string }>>({});
  const [preview, setPreview] = useState<{ opt: OptionData; startIndex: number } | null>(null);

  const fetchLatest = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/options/latest');
      const data = await res.json();
      if (data && data.batchId) {
        setBatch(data);
        // Initialize card states from existing idea statuses
        const states: Record<number, { renderState: CardRenderState }> = {};
        for (const opt of data.options) {
          if (opt.ideaStatus === 'designed') {
            states[opt.scriptId] = { renderState: 'rendered' };
          } else if (opt.ideaStatus === 'published') {
            states[opt.scriptId] = { renderState: 'posted' };
          }
        }
        setCardState(prev => ({ ...prev, ...states }));
      } else {
        setBatch(null);
      }
    } catch {
      // Server not running
    }
    setLoading(false);
  };

  useEffect(() => { fetchLatest(); }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setCardState({});
    try {
      await fetch('/api/options/generate', { method: 'POST' });
      await fetchLatest();
    } catch (err) {
      console.error('Generate failed:', err);
    }
    setGenerating(false);
  };

  const handleApproveContent = async (scriptId: number) => {
    setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'rendering' } }));
    try {
      const res = await fetch(`/api/queue/${scriptId}/approve-content`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'rendered' } }));
        // Refresh batch to get updated URLs
        await fetchLatest();
      } else {
        setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'error', message: data.error || `Render failed (${res.status})` } }));
      }
    } catch (err: any) {
      setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'error', message: err?.message || 'Network error — check server logs' } }));
    }
  };

  const handlePostNow = async (scriptId: number) => {
    setPosting(scriptId);
    try {
      const res = await fetch(`/api/queue/${scriptId}/approve-and-post`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'posted', message: 'Posted to Instagram!' } }));
        onPublished();
      } else {
        setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'error', message: data.error || 'Post failed' } }));
      }
    } catch (err) {
      setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'error', message: 'Network error' } }));
    }
    setPosting(null);
  };

  const handleSchedule = async (scriptId: number) => {
    setScheduling(scriptId);
    try {
      const res = await fetch(`/api/queue/${scriptId}/approve-and-schedule`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'scheduled', message: `Scheduled: ${data.scheduledDate} at ${data.scheduledTime}` } }));
        onScheduled();
      }
    } catch (err) {
      console.error('Schedule failed:', err);
    }
    setScheduling(null);
  };

  const handleRegenerate = async (scriptId: number) => {
    setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'regenerating' } }));
    try {
      const res = await fetch(`/api/queue/${scriptId}/regenerate`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'rendered' } }));
        await fetchLatest();
      } else {
        setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'error', message: data.error || 'Regeneration failed' } }));
      }
    } catch (err: any) {
      setCardState(prev => ({ ...prev, [scriptId]: { renderState: 'error', message: err?.message || 'Network error' } }));
    }
  };

  const getCardRenderState = (opt: OptionData): CardRenderState => {
    return cardState[opt.scriptId]?.renderState || 'idle';
  };

  const isRendered = (opt: OptionData): boolean => {
    const state = getCardRenderState(opt);
    return state === 'rendered' || state === 'posted' || state === 'scheduled';
  };

  return (
    <div className="space-y-4">
      {preview && (
        <SlidePreview
          slides={getAllSlides(preview.opt)}
          startIndex={preview.startIndex}
          title={preview.opt.title}
          caption={preview.opt.caption || ''}
          hashtags={preview.opt.hashtags || []}
          scriptId={preview.opt.scriptId}
          onClose={() => setPreview(null)}
        />
      )}

      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Content Options</h2>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            generating
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : 'bg-purple-600 hover:bg-purple-500 text-white'
          }`}
        >
          {generating ? (
            <span className="flex items-center gap-2">
              <span className="inline-block w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
              Generating 5 Options...
            </span>
          ) : (
            'Generate New Options'
          )}
        </button>
      </div>

      {loading && !generating && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      )}

      {!loading && !batch && !generating && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-500">No content options generated yet</p>
          <p className="text-xs text-gray-600 mt-2">
            Click "Generate New Options" to create 5 content options to review
          </p>
        </div>
      )}

      {batch && (
        <>
          <div className="flex items-center gap-3 text-sm text-gray-500">
            <span>Batch: {batch.batchId.slice(0, 8)}</span>
            <span>|</span>
            <span>{batch.options.length} options</span>
            <span>|</span>
            <span className={batch.status === 'ready' ? 'text-green-400' : 'text-yellow-400'}>
              {batch.status}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {batch.options.map((opt, idx) => {
              const thumb = getThumbnail(opt);
              const slides = getAllSlides(opt);
              const isExpanded = expanded === opt.ideaId;
              const renderState = getCardRenderState(opt);
              const rendered = isRendered(opt);
              let script: any = {};
              try { script = JSON.parse(opt.scriptJson || '{}'); } catch {}

              return (
                <div
                  key={opt.ideaId}
                  className={`bg-gray-900 border rounded-xl overflow-hidden transition-all ${
                    renderState === 'posted'
                      ? 'border-green-500 ring-1 ring-green-500'
                      : renderState === 'scheduled'
                        ? 'border-blue-500 ring-1 ring-blue-500'
                        : renderState === 'error'
                          ? 'border-red-500/50'
                          : renderState === 'rendered'
                            ? 'border-emerald-500/50'
                            : 'border-gray-800 hover:border-gray-700'
                  }`}
                >
                  {/* Visual area: thumbnail if rendered, text summary if not */}
                  {rendered && thumb ? (
                    <div
                      className="relative aspect-square bg-gray-800 cursor-pointer group"
                      onClick={() => slides.length > 0 && setPreview({ opt, startIndex: 0 })}
                    >
                      {isVideo(thumb) ? (
                        <video src={thumb} muted playsInline className="w-full h-full object-cover" onMouseOver={e => (e.target as HTMLVideoElement).play()} onMouseOut={e => { const v = e.target as HTMLVideoElement; v.pause(); v.currentTime = 0; }} />
                      ) : (
                        <img src={thumb} alt={opt.title} className="w-full h-full object-cover" />
                      )}
                      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                        <span className="text-white text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 px-4 py-2 rounded-lg">
                          {isVideo(thumb) ? 'Preview Reel' : `Preview All ${slides.length} Slides`}
                        </span>
                      </div>
                      <span className={`absolute top-2 left-2 text-xs text-white px-2 py-0.5 rounded-full ${typeColors[opt.contentType] || 'bg-gray-600'}`}>
                        {opt.contentType}
                      </span>
                      {slides.length > 1 && (
                        <span className="absolute bottom-2 right-2 text-xs bg-gray-900/80 text-gray-300 px-2 py-0.5 rounded-full">
                          {slides.length} slides
                        </span>
                      )}
                      <span className="absolute top-2 right-2 text-xs bg-gray-900/80 text-gray-300 px-2 py-0.5 rounded-full">
                        #{idx + 1}
                      </span>
                    </div>
                  ) : (renderState === 'rendering' || renderState === 'regenerating') ? (
                    <div className="relative aspect-[4/3] bg-gray-800 flex flex-col items-center justify-center gap-3">
                      <span className="inline-block w-8 h-8 border-3 border-purple-400 border-t-transparent rounded-full animate-spin" />
                      <span className="text-sm text-purple-300">{renderState === 'regenerating' ? 'Re-rendering visuals...' : 'Rendering visuals...'}</span>
                      <span className={`absolute top-2 left-2 text-xs text-white px-2 py-0.5 rounded-full ${typeColors[opt.contentType] || 'bg-gray-600'}`}>
                        {opt.contentType}
                      </span>
                      <span className="absolute top-2 right-2 text-xs bg-gray-900/80 text-gray-300 px-2 py-0.5 rounded-full">
                        #{idx + 1}
                      </span>
                    </div>
                  ) : (
                    <div className="relative bg-gray-800/50 p-4 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs text-white px-2 py-0.5 rounded-full ${typeColors[opt.contentType] || 'bg-gray-600'}`}>
                          {opt.contentType}
                        </span>
                        <span className="text-xs bg-gray-900/80 text-gray-300 px-2 py-0.5 rounded-full">
                          #{idx + 1}
                        </span>
                      </div>
                      {opt.valueProp && (
                        <div>
                          <span className="text-[10px] text-gray-500 uppercase tracking-wider">Value Prop</span>
                          <p className="text-xs text-gray-300">{opt.valueProp}</p>
                        </div>
                      )}
                      {opt.emotionalTrigger && (
                        <div>
                          <span className="text-[10px] text-gray-500 uppercase tracking-wider">Emotional Trigger</span>
                          <p className="text-xs text-gray-300">{opt.emotionalTrigger}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Info */}
                  <div className="p-4 space-y-2">
                    <h3 className="font-medium text-sm leading-tight">{opt.title}</h3>
                    <p className="text-xs text-gray-400 line-clamp-2">{opt.hook}</p>

                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-gray-500">Send:</span>
                      <span className={probColors[opt.sendProbability] || 'text-gray-400'}>
                        {opt.sendProbability?.replace('_', ' ')}
                      </span>
                    </div>

                    {opt.sendTrigger && (
                      <p className="text-xs text-purple-300 italic">"{opt.sendTrigger}"</p>
                    )}

                    {/* Action buttons — vary by render state */}
                    {renderState === 'posted' ? (
                      <div className="pt-2">
                        <div className="w-full px-3 py-2 text-xs rounded-lg bg-green-900/40 border border-green-700 text-green-300 text-center font-medium">
                          {cardState[opt.scriptId]?.message || 'Posted to Instagram!'}
                        </div>
                      </div>
                    ) : renderState === 'scheduled' ? (
                      <div className="pt-2">
                        <div className="w-full px-3 py-2 text-xs rounded-lg bg-blue-900/40 border border-blue-700 text-blue-300 text-center font-medium">
                          {cardState[opt.scriptId]?.message || 'Scheduled'}
                        </div>
                      </div>
                    ) : renderState === 'error' ? (
                      <div className="pt-2 space-y-2">
                        <div className="w-full px-3 py-2 text-xs rounded-lg bg-red-900/40 border border-red-700 text-red-300 text-center">
                          {cardState[opt.scriptId]?.message || 'Error'}
                        </div>
                        <button
                          onClick={() => handleApproveContent(opt.scriptId)}
                          className="w-full px-3 py-2 text-xs rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white font-medium transition-colors"
                        >
                          Retry Approve Content
                        </button>
                      </div>
                    ) : (renderState === 'rendering' || renderState === 'regenerating') ? (
                      <div className="pt-2">
                        <button
                          disabled
                          className="w-full px-3 py-2 text-xs rounded-lg bg-gray-700 text-gray-400 cursor-not-allowed font-medium"
                        >
                          {renderState === 'regenerating' ? 'Re-rendering...' : 'Rendering...'}
                        </button>
                      </div>
                    ) : rendered ? (
                      <div className="pt-2 space-y-1.5">
                        <div className="flex gap-2">
                          {slides.length > 0 && (
                            <button
                              onClick={() => setPreview({ opt, startIndex: 0 })}
                              className="flex-1 px-3 py-1.5 bg-purple-900/40 hover:bg-purple-800/60 border border-purple-700 text-purple-300 text-xs rounded-lg transition-colors"
                            >
                              Preview Full Post
                            </button>
                          )}
                          <button
                            onClick={() => handleDownload(opt.scriptId)}
                            className="px-3 py-1.5 bg-cyan-900/40 hover:bg-cyan-800/60 border border-cyan-700 text-cyan-300 text-xs rounded-lg transition-colors"
                            title="Download"
                          >
                            Download
                          </button>
                          <button
                            onClick={() => setExpanded(isExpanded ? null : opt.ideaId)}
                            className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-xs rounded-lg transition-colors"
                          >
                            {isExpanded ? 'Less' : 'Info'}
                          </button>
                        </div>
                        <button
                          onClick={() => handlePostNow(opt.scriptId)}
                          disabled={posting === opt.scriptId}
                          className={`w-full px-3 py-2 text-xs rounded-lg transition-colors font-medium ${
                            posting === opt.scriptId
                              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                              : 'bg-green-700 hover:bg-green-600 text-white'
                          }`}
                        >
                          {posting === opt.scriptId ? 'Posting to Instagram...' : 'Post to Instagram'}
                        </button>
                        <button
                          onClick={() => handleSchedule(opt.scriptId)}
                          disabled={scheduling === opt.scriptId}
                          className={`w-full px-3 py-1.5 text-xs rounded-lg transition-colors ${
                            scheduling === opt.scriptId
                              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                              : 'bg-gray-800 hover:bg-gray-700 text-gray-400'
                          }`}
                        >
                          {scheduling === opt.scriptId ? 'Scheduling...' : 'Schedule for Later'}
                        </button>
                        <button
                          onClick={() => handleRegenerate(opt.scriptId)}
                          className="w-full px-3 py-1.5 text-xs rounded-lg transition-colors border border-gray-700 hover:border-gray-500 text-gray-400 hover:text-gray-200"
                        >
                          Regenerate Visuals
                        </button>
                      </div>
                    ) : (
                      <div className="pt-2 space-y-1.5">
                        <button
                          onClick={() => setExpanded(isExpanded ? null : opt.ideaId)}
                          className="w-full px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-xs rounded-lg transition-colors"
                        >
                          {isExpanded ? 'Less' : 'More Info'}
                        </button>
                        <button
                          onClick={() => handleApproveContent(opt.scriptId)}
                          className="w-full px-3 py-2 text-xs rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white font-medium transition-colors"
                        >
                          Approve Content
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Expanded details */}
                  {isExpanded && (
                    <div className="border-t border-gray-800 p-4 space-y-4">
                      {rendered && slides.length > 1 && (
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                            All Slides — click any to preview full-size
                          </p>
                          <div className="grid grid-cols-5 gap-1.5">
                            {slides.map((src, i) => (
                              <button
                                key={i}
                                onClick={() => setPreview({ opt, startIndex: i })}
                                className="relative aspect-square rounded-md overflow-hidden border border-gray-700 hover:border-purple-500 transition-colors group"
                              >
                                <img src={src} alt={`Slide ${i + 1}`} className="w-full h-full object-cover" />
                                <span className="absolute bottom-0 inset-x-0 bg-black/60 text-[10px] text-gray-300 text-center py-0.5">
                                  {i + 1}
                                </span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {opt.caption && (
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Caption</p>
                          <p className="text-xs text-gray-300 whitespace-pre-wrap">{opt.caption}</p>
                        </div>
                      )}

                      {script?.hook && opt.contentType === 'reel' && (
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Reel Script</p>
                          <div className="bg-gray-800 rounded-lg p-3 space-y-2">
                            <div>
                              <span className="text-xs text-pink-400">HOOK (0-1.7s):</span>
                              <p className="text-xs mt-0.5">{script.hook.onScreenText}</p>
                            </div>
                            {script.body?.map((seg: any, i: number) => (
                              <div key={i}>
                                <span className="text-xs text-gray-500">{seg.timestamp}s:</span>
                                <p className="text-xs mt-0.5">{seg.onScreenText}</p>
                              </div>
                            ))}
                            {script.cta && (
                              <div>
                                <span className="text-xs text-green-400">CTA:</span>
                                <p className="text-xs mt-0.5">{script.cta.onScreenText}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {opt.hashtags && opt.hashtags.length > 0 && (
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Hashtags</p>
                          <div className="flex flex-wrap gap-1">
                            {opt.hashtags.map((tag: string, i: number) => (
                              <span key={i} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                                #{tag.replace('#', '')}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {opt.dmTrigger && (
                        <div className="bg-purple-900/20 border border-purple-800 rounded-lg p-3">
                          <p className="text-xs text-purple-400">
                            DM Trigger: "{opt.dmTrigger}"
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Section 2: Upcoming Schedule ───────────────────

function UpcomingScheduleSection({
  schedule,
  onRefresh,
}: {
  schedule: ScheduleItem[];
  onRefresh: () => void;
}) {
  const [publishing, setPublishing] = useState<number | null>(null);
  const [removing, setRemoving] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const handlePublishNow = async (calendarId: number) => {
    setPublishing(calendarId);
    try {
      await fetch(`/api/schedule/${calendarId}/publish-now`, { method: 'POST' });
      onRefresh();
    } catch (err) {
      console.error('Publish failed:', err);
    }
    setPublishing(null);
  };

  const handleRemove = async (calendarId: number) => {
    setRemoving(calendarId);
    try {
      await fetch(`/api/schedule/${calendarId}/remove`, { method: 'POST' });
      onRefresh();
    } catch (err) {
      console.error('Remove failed:', err);
    }
    setRemoving(null);
  };

  // Group by date
  const grouped = schedule.reduce<Record<string, ScheduleItem[]>>((acc, item) => {
    const key = item.scheduledDate;
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});

  const sortedDates = Object.keys(grouped).sort();

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Upcoming Schedule</h2>

      {sortedDates.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
          <p className="text-gray-500">No content scheduled yet</p>
          <p className="text-xs text-gray-600 mt-1">Approve content above to auto-schedule it</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedDates.map(date => (
            <div key={date}>
              <h3 className="text-sm font-semibold text-gray-400 mb-2">
                {formatScheduleDate(date)}
              </h3>
              <div className="space-y-2">
                {grouped[date].map(item => {
                  const slides = getAllSlides(item);
                  const thumb = slides.length > 0 ? slides[0] : null;
                  const isExpanded = expandedId === item.calendarId;

                  return (
                    <div key={item.calendarId} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                      <div
                        className="p-3 flex items-center gap-3 cursor-pointer hover:bg-gray-800/50 transition-colors"
                        onClick={() => setExpandedId(isExpanded ? null : item.calendarId)}
                      >
                        {/* Thumbnail */}
                        {thumb && (
                          <img
                            src={thumb}
                            alt={item.title}
                            className="w-12 h-12 rounded-lg object-cover shrink-0"
                          />
                        )}

                        {/* Time badge */}
                        <span className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded-md font-mono shrink-0">
                          {item.scheduledTime}
                        </span>

                        {/* Type badge */}
                        <span className={`text-xs text-white px-2 py-0.5 rounded-full shrink-0 ${typeColors[item.contentType] || 'bg-gray-600'}`}>
                          {item.contentType}
                        </span>

                        {/* Title */}
                        <span className="text-sm font-medium flex-1 truncate">
                          {item.title || 'Untitled'}
                        </span>

                        {/* Actions */}
                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            onClick={(e) => { e.stopPropagation(); handlePublishNow(item.calendarId); }}
                            disabled={publishing === item.calendarId}
                            className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                              publishing === item.calendarId
                                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                : 'bg-green-700 hover:bg-green-600 text-white'
                            }`}
                          >
                            {publishing === item.calendarId ? 'Publishing...' : 'Publish Now'}
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleRemove(item.calendarId); }}
                            disabled={removing === item.calendarId}
                            className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                              removing === item.calendarId
                                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                : 'bg-red-900 hover:bg-red-800 text-red-200'
                            }`}
                          >
                            {removing === item.calendarId ? 'Removing...' : 'Remove'}
                          </button>
                          <span className="text-gray-500 text-sm">{isExpanded ? '\u25B2' : '\u25BC'}</span>
                        </div>
                      </div>

                      {/* Expanded details */}
                      {isExpanded && (
                        <div className="border-t border-gray-800 p-4 space-y-3">
                          {item.caption && (
                            <div>
                              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Caption</p>
                              <p className="text-xs text-gray-300 whitespace-pre-wrap">{item.caption}</p>
                            </div>
                          )}
                          {item.hashtags && item.hashtags.length > 0 && (
                            <div>
                              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Hashtags</p>
                              <div className="flex flex-wrap gap-1">
                                {item.hashtags.map((tag: string, i: number) => (
                                  <span key={i} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                                    #{tag.replace('#', '')}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          {slides.length > 1 && (
                            <div>
                              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Slides</p>
                              <div className="flex gap-1.5 overflow-x-auto">
                                {slides.map((src, i) => (
                                  <img
                                    key={i}
                                    src={src}
                                    alt={`Slide ${i + 1}`}
                                    className="w-16 h-16 rounded-md object-cover shrink-0 border border-gray-700"
                                  />
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Section 3: All Content (organized by status) ───

type FilterTab = 'all' | 'not_rendered' | 'rendered' | 'approved' | 'posted';

const filterTabs: { key: FilterTab; label: string; color: string }[] = [
  { key: 'all', label: 'All', color: 'text-white border-white' },
  { key: 'not_rendered', label: 'Not Rendered', color: 'text-yellow-400 border-yellow-400' },
  { key: 'rendered', label: 'Rendered', color: 'text-emerald-400 border-emerald-400' },
  { key: 'approved', label: 'Approved', color: 'text-blue-400 border-blue-400' },
  { key: 'posted', label: 'Posted', color: 'text-green-400 border-green-400' },
];

const statusBadge = (status: string): { label: string; className: string } => {
  switch (status) {
    case 'scripted': return { label: 'Not Rendered', className: 'bg-yellow-700/60 text-yellow-200' };
    case 'designed': return { label: 'Rendered', className: 'bg-emerald-700/60 text-emerald-200' };
    case 'approved': return { label: 'Approved', className: 'bg-blue-700/60 text-blue-200' };
    case 'published': return { label: 'Posted', className: 'bg-green-700/60 text-green-200' };
    default: return { label: status, className: 'bg-gray-700/60 text-gray-200' };
  }
};

function formatDateGroup(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Yesterday';
  if (diff < 7) return `${diff} days ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function AllContentSection({
  onScheduled,
  onPublished,
}: {
  onScheduled: () => void;
  onPublished: () => void;
}) {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [filter, setFilter] = useState<FilterTab>('all');
  const [expanded, setExpanded] = useState<number | null>(null);
  const [posting, setPosting] = useState<number | null>(null);
  const [scheduling, setScheduling] = useState<number | null>(null);
  const [rendering, setRendering] = useState<number | null>(null);
  const [cardStatus, setCardStatus] = useState<Record<number, { type: 'posted' | 'scheduled' | 'rendering' | 'regenerating' | 'error'; message: string }>>({});
  const [preview, setPreview] = useState<{ item: QueueItem; startIndex: number } | null>(null);

  const fetchQueue = async () => {
    try {
      const res = await fetch('/api/queue');
      const all = await res.json();
      setItems(all);
    } catch {
      // Server not running
    }
  };

  useEffect(() => { fetchQueue(); }, []);

  const handleApproveContent = async (scriptId: number) => {
    setRendering(scriptId);
    setCardStatus(prev => ({ ...prev, [scriptId]: { type: 'rendering', message: 'Rendering visuals...' } }));
    try {
      const res = await fetch(`/api/queue/${scriptId}/approve-content`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setCardStatus(prev => {
          const next = { ...prev };
          delete next[scriptId];
          return next;
        });
        fetchQueue();
      } else {
        setCardStatus(prev => ({ ...prev, [scriptId]: { type: 'error', message: data.error || `Render failed (${res.status})` } }));
      }
    } catch (err: any) {
      setCardStatus(prev => ({ ...prev, [scriptId]: { type: 'error', message: err?.message || 'Network error — check server logs' } }));
    }
    setRendering(null);
  };

  const handlePostNow = async (scriptId: number) => {
    setPosting(scriptId);
    try {
      const res = await fetch(`/api/queue/${scriptId}/approve-and-post`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setCardStatus(prev => ({ ...prev, [scriptId]: { type: 'posted', message: 'Posted to Instagram!' } }));
        onPublished();
        fetchQueue();
      } else {
        setCardStatus(prev => ({ ...prev, [scriptId]: { type: 'error', message: data.error || 'Post failed' } }));
      }
    } catch (err) {
      setCardStatus(prev => ({ ...prev, [scriptId]: { type: 'error', message: 'Network error' } }));
    }
    setPosting(null);
  };

  const handleSchedule = async (scriptId: number) => {
    setScheduling(scriptId);
    try {
      const res = await fetch(`/api/queue/${scriptId}/approve-and-schedule`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setCardStatus(prev => ({ ...prev, [scriptId]: { type: 'scheduled', message: `Scheduled: ${data.scheduledDate} at ${data.scheduledTime}` } }));
        onScheduled();
        fetchQueue();
      }
    } catch (err) {
      console.error('Schedule failed:', err);
    }
    setScheduling(null);
  };

  const handleReject = async (id: number) => {
    await fetch(`/api/queue/${id}/reject`, { method: 'POST' });
    fetchQueue();
  };

  const handleRegenerate = async (scriptId: number) => {
    setCardStatus(prev => ({ ...prev, [scriptId]: { type: 'regenerating', message: 'Re-rendering visuals...' } }));
    try {
      const res = await fetch(`/api/queue/${scriptId}/regenerate`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setCardStatus(prev => {
          const next = { ...prev };
          delete next[scriptId];
          return next;
        });
        fetchQueue();
      } else {
        setCardStatus(prev => ({ ...prev, [scriptId]: { type: 'error', message: data.error || 'Regeneration failed' } }));
      }
    } catch (err: any) {
      setCardStatus(prev => ({ ...prev, [scriptId]: { type: 'error', message: err?.message || 'Network error' } }));
    }
  };

  const getItemSlides = (item: QueueItem): string[] => {
    const paths = item.public_urls && item.public_urls.length > 0 ? item.public_urls : item.local_paths;
    if (!paths || paths.length === 0) return [];
    return paths.map(p => item.public_urls && item.public_urls.length > 0 ? p : toUrl(p));
  };

  if (items.length === 0) return null;

  // Filter items based on selected tab
  const filteredItems = items.filter(item => {
    switch (filter) {
      case 'not_rendered': return item.idea_status === 'scripted';
      case 'rendered': return item.idea_status === 'designed';
      case 'approved': return item.idea_status === 'approved';
      case 'posted': return item.idea_status === 'published';
      default: return true;
    }
  });

  // Sort by ID descending (newest first)
  const sortedItems = [...filteredItems].sort((a, b) => b.id - a.id);

  // Group by date (use batch_id date part or fallback to position)
  const grouped: { label: string; items: QueueItem[] }[] = [];
  const dateMap = new Map<string, QueueItem[]>();
  for (const item of sortedItems) {
    const dateKey = item.batch_id?.split('_')[0] || 'unknown';
    if (!dateMap.has(dateKey)) dateMap.set(dateKey, []);
    dateMap.get(dateKey)!.push(item);
  }
  for (const [dateKey, dateItems] of dateMap) {
    const label = dateKey !== 'unknown' ? formatDateGroup(dateKey) : 'Other';
    grouped.push({ label, items: dateItems });
  }

  // Count by status for tab badges
  const counts = {
    all: items.length,
    not_rendered: items.filter(i => i.idea_status === 'scripted').length,
    rendered: items.filter(i => i.idea_status === 'designed').length,
    approved: items.filter(i => i.idea_status === 'approved').length,
    posted: items.filter(i => i.idea_status === 'published').length,
  };

  return (
    <div className="space-y-4">
      {preview && (
        <SlidePreview
          slides={getItemSlides(preview.item)}
          startIndex={preview.startIndex}
          title={preview.item.title}
          caption={preview.item.caption || ''}
          hashtags={preview.item.hashtags ? (() => { try { const h = typeof preview.item.hashtags === 'string' ? JSON.parse(preview.item.hashtags) : preview.item.hashtags; return Array.isArray(h) ? h : String(h).split(/\s+/); } catch { return String(preview.item.hashtags).split(/\s+/); } })() : []}
          scriptId={preview.item.id}
          onClose={() => setPreview(null)}
        />
      )}

      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">All Content</h2>
        <span className="text-sm text-gray-500">{items.length} total</span>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {filterTabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-all whitespace-nowrap ${
              filter === tab.key
                ? `${tab.color} bg-gray-800 border-current font-medium`
                : 'text-gray-500 border-gray-800 hover:border-gray-600 hover:text-gray-300'
            }`}
          >
            {tab.label}
            {counts[tab.key] > 0 && (
              <span className={`ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] ${
                filter === tab.key ? 'bg-gray-700' : 'bg-gray-800'
              }`}>
                {counts[tab.key]}
              </span>
            )}
          </button>
        ))}
      </div>

      {filteredItems.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-sm">No content in this category</p>
        </div>
      ) : (
        grouped.map((group, gi) => (
          <div key={gi} className="space-y-3">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-medium text-gray-400">{group.label}</h3>
              <div className="flex-1 border-t border-gray-800" />
              <span className="text-xs text-gray-600">{group.items.length} items</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {group.items.map((item) => {
                const slides = getItemSlides(item);
                const thumb = slides.length > 0 ? slides[0] : null;
                const isExpanded = expanded === item.id;
                const status = cardStatus[item.id];
                const isDesigned = item.idea_status === 'designed' || item.idea_status === 'approved';
                const isScripted = item.idea_status === 'scripted';
                const isPublished = item.idea_status === 'published';
                const isRendering = status?.type === 'rendering' || status?.type === 'regenerating';
                const badge = statusBadge(item.idea_status);
                let script: any = {};
                try { script = JSON.parse(item.script_json || '{}'); } catch {}
                let hashtags: string[] = [];
                try { hashtags = item.hashtags ? (typeof item.hashtags === 'string' ? JSON.parse(item.hashtags) : item.hashtags) : []; } catch {}

                return (
                  <div
                    key={item.id}
                    className={`bg-gray-900 border rounded-xl overflow-hidden transition-all ${
                      isPublished
                        ? 'border-green-500/40'
                        : status?.type === 'posted'
                          ? 'border-green-500 ring-1 ring-green-500'
                          : status?.type === 'scheduled'
                            ? 'border-blue-500 ring-1 ring-blue-500'
                            : status?.type === 'error'
                              ? 'border-red-500/50'
                              : isDesigned
                                ? 'border-emerald-500/50'
                                : 'border-gray-800 hover:border-gray-700'
                    }`}
                  >
                    {/* Visual area */}
                    {(isDesigned || isPublished) && thumb ? (
                      <div
                        className="relative aspect-square bg-gray-800 cursor-pointer group"
                        onClick={() => slides.length > 0 && setPreview({ item, startIndex: 0 })}
                      >
                        {isVideo(thumb) ? (
                          <video src={thumb} muted playsInline className="w-full h-full object-cover" onMouseOver={e => (e.target as HTMLVideoElement).play()} onMouseOut={e => { const v = e.target as HTMLVideoElement; v.pause(); v.currentTime = 0; }} />
                        ) : (
                          <img src={thumb} alt={item.title} className="w-full h-full object-cover" />
                        )}
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                          <span className="text-white text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 px-4 py-2 rounded-lg">
                            {isVideo(thumb) ? 'Preview Reel' : (slides.length > 1 ? `Preview All ${slides.length} Slides` : 'Preview Post')}
                          </span>
                        </div>
                        <span className={`absolute top-2 left-2 text-xs text-white px-2 py-0.5 rounded-full ${typeColors[item.content_type] || 'bg-gray-600'}`}>
                          {item.content_type}
                        </span>
                        {slides.length > 1 && (
                          <span className="absolute bottom-2 right-2 text-xs bg-gray-900/80 text-gray-300 px-2 py-0.5 rounded-full">
                            {slides.length} slides
                          </span>
                        )}
                        <span className={`absolute top-2 right-2 text-xs px-2 py-0.5 rounded-full ${badge.className}`}>
                          {badge.label}
                        </span>
                      </div>
                    ) : isRendering ? (
                      <div className="relative aspect-[4/3] bg-gray-800 flex flex-col items-center justify-center gap-3">
                        <span className="inline-block w-8 h-8 border-3 border-purple-400 border-t-transparent rounded-full animate-spin" />
                        <span className="text-sm text-purple-300">{status?.type === 'regenerating' ? 'Re-rendering visuals...' : 'Rendering visuals...'}</span>
                        <span className={`absolute top-2 left-2 text-xs text-white px-2 py-0.5 rounded-full ${typeColors[item.content_type] || 'bg-gray-600'}`}>
                          {item.content_type}
                        </span>
                      </div>
                    ) : (
                      <div className="relative bg-gray-800/50 p-4 space-y-2">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs text-white px-2 py-0.5 rounded-full ${typeColors[item.content_type] || 'bg-gray-600'}`}>
                            {item.content_type}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${badge.className}`}>
                            {badge.label}
                          </span>
                        </div>
                        {item.send_trigger && (
                          <div>
                            <span className="text-[10px] text-gray-500 uppercase tracking-wider">Send Trigger</span>
                            <p className="text-xs text-gray-300">{item.send_trigger}</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Info */}
                    <div className="p-4 space-y-2">
                      <h3 className="font-medium text-sm leading-tight">{item.title || 'Untitled'}</h3>
                      {item.hook && <p className="text-xs text-gray-400 line-clamp-2">{item.hook}</p>}

                      {item.send_probability && (
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-gray-500">Send:</span>
                          <span className={probColors[item.send_probability] || 'text-gray-400'}>
                            {item.send_probability?.replace('_', ' ')}
                          </span>
                        </div>
                      )}

                      {/* Action buttons — vary by status */}
                      {isPublished ? (
                        <div className="pt-2 space-y-1.5">
                          <div className="w-full px-3 py-2 text-xs rounded-lg bg-green-900/40 border border-green-700 text-green-300 text-center font-medium">
                            Posted to Instagram
                          </div>
                          <div className="flex gap-2">
                            {slides.length > 0 && (
                              <button
                                onClick={() => setPreview({ item, startIndex: 0 })}
                                className="flex-1 px-3 py-1.5 bg-purple-900/40 hover:bg-purple-800/60 border border-purple-700 text-purple-300 text-xs rounded-lg transition-colors"
                              >
                                Preview
                              </button>
                            )}
                            <button
                              onClick={() => handleDownload(item.id)}
                              className="px-3 py-1.5 bg-cyan-900/40 hover:bg-cyan-800/60 border border-cyan-700 text-cyan-300 text-xs rounded-lg transition-colors"
                            >
                              Download
                            </button>
                          </div>
                        </div>
                      ) : status?.type === 'posted' ? (
                        <div className="pt-2">
                          <div className="w-full px-3 py-2 text-xs rounded-lg bg-green-900/40 border border-green-700 text-green-300 text-center font-medium">
                            {status.message}
                          </div>
                        </div>
                      ) : status?.type === 'scheduled' ? (
                        <div className="pt-2">
                          <div className="w-full px-3 py-2 text-xs rounded-lg bg-blue-900/40 border border-blue-700 text-blue-300 text-center font-medium">
                            {status.message}
                          </div>
                        </div>
                      ) : status?.type === 'error' ? (
                        <div className="pt-2 space-y-2">
                          <div className="w-full px-3 py-2 text-xs rounded-lg bg-red-900/40 border border-red-700 text-red-300 text-center">
                            {status.message}
                          </div>
                          {isScripted ? (
                            <button
                              onClick={() => handleApproveContent(item.id)}
                              className="w-full px-3 py-2 text-xs rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white font-medium transition-colors"
                            >
                              Retry Approve Content
                            </button>
                          ) : (
                            <button
                              onClick={() => handlePostNow(item.id)}
                              className="w-full px-3 py-2 text-xs rounded-lg bg-green-700 hover:bg-green-600 text-white font-medium transition-colors"
                            >
                              Retry Post to Instagram
                            </button>
                          )}
                        </div>
                      ) : isRendering ? (
                        <div className="pt-2">
                          <button
                            disabled
                            className="w-full px-3 py-2 text-xs rounded-lg bg-gray-700 text-gray-400 cursor-not-allowed font-medium"
                          >
                            {status?.type === 'regenerating' ? 'Re-rendering...' : 'Rendering...'}
                          </button>
                        </div>
                      ) : isScripted ? (
                        <div className="pt-2 space-y-1.5">
                          <button
                            onClick={() => setExpanded(isExpanded ? null : item.id)}
                            className="w-full px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-xs rounded-lg transition-colors"
                          >
                            {isExpanded ? 'Less' : 'More Info'}
                          </button>
                          <button
                            onClick={() => handleApproveContent(item.id)}
                            className="w-full px-3 py-2 text-xs rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white font-medium transition-colors"
                          >
                            Approve Content
                          </button>
                          <button
                            onClick={() => handleReject(item.id)}
                            className="w-full px-3 py-1.5 bg-red-900/60 hover:bg-red-800 text-red-300 text-xs rounded-lg transition-colors"
                          >
                            Reject
                          </button>
                        </div>
                      ) : (
                        <div className="pt-2 space-y-1.5">
                          <div className="flex gap-2">
                            {slides.length > 0 && (
                              <button
                                onClick={() => setPreview({ item, startIndex: 0 })}
                                className="flex-1 px-3 py-1.5 bg-purple-900/40 hover:bg-purple-800/60 border border-purple-700 text-purple-300 text-xs rounded-lg transition-colors"
                              >
                                Preview Full Post
                              </button>
                            )}
                            <button
                              onClick={() => handleDownload(item.id)}
                              className="px-3 py-1.5 bg-cyan-900/40 hover:bg-cyan-800/60 border border-cyan-700 text-cyan-300 text-xs rounded-lg transition-colors"
                              title="Download"
                            >
                              Download
                            </button>
                            <button
                              onClick={() => setExpanded(isExpanded ? null : item.id)}
                              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-xs rounded-lg transition-colors"
                            >
                              {isExpanded ? 'Less' : 'Info'}
                            </button>
                          </div>
                          <button
                            onClick={() => handlePostNow(item.id)}
                            disabled={posting === item.id}
                            className={`w-full px-3 py-2 text-xs rounded-lg transition-colors font-medium ${
                              posting === item.id
                                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                : 'bg-green-700 hover:bg-green-600 text-white'
                            }`}
                          >
                            {posting === item.id ? 'Posting to Instagram...' : 'Post to Instagram'}
                          </button>
                          <div className="flex gap-1.5">
                            <button
                              onClick={() => handleSchedule(item.id)}
                              disabled={scheduling === item.id}
                              className={`flex-1 px-3 py-1.5 text-xs rounded-lg transition-colors ${
                                scheduling === item.id
                                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                  : 'bg-gray-800 hover:bg-gray-700 text-gray-400'
                              }`}
                            >
                              {scheduling === item.id ? 'Scheduling...' : 'Schedule for Later'}
                            </button>
                            <button
                              onClick={() => handleReject(item.id)}
                              className="px-3 py-1.5 bg-red-900/60 hover:bg-red-800 text-red-300 text-xs rounded-lg transition-colors"
                            >
                              Reject
                            </button>
                          </div>
                          <button
                            onClick={() => handleRegenerate(item.id)}
                            className="w-full px-3 py-1.5 text-xs rounded-lg transition-colors border border-gray-700 hover:border-gray-500 text-gray-400 hover:text-gray-200"
                          >
                            Regenerate Visuals
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Expanded details */}
                    {isExpanded && (
                      <div className="border-t border-gray-800 p-4 space-y-4">
                        {slides.length > 1 && (
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                              All Slides — click any to preview full-size
                            </p>
                            <div className="grid grid-cols-5 gap-1.5">
                              {slides.map((src, i) => (
                                <button
                                  key={i}
                                  onClick={() => setPreview({ item, startIndex: i })}
                                  className="relative aspect-square rounded-md overflow-hidden border border-gray-700 hover:border-purple-500 transition-colors"
                                >
                                  <img src={src} alt={`Slide ${i + 1}`} className="w-full h-full object-cover" />
                                  <span className="absolute bottom-0 inset-x-0 bg-black/60 text-[10px] text-gray-300 text-center py-0.5">
                                    {i + 1}
                                  </span>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {item.caption && (
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Caption</p>
                            <p className="text-xs text-gray-300 whitespace-pre-wrap">{item.caption}</p>
                          </div>
                        )}

                        {script?.hook && item.content_type === 'reel' && (
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Reel Script</p>
                            <div className="bg-gray-800 rounded-lg p-3 space-y-2">
                              <div>
                                <span className="text-xs text-pink-400">HOOK (0-1.7s):</span>
                                <p className="text-xs mt-0.5">{script.hook.onScreenText}</p>
                              </div>
                              {script.body?.map((seg: any, i: number) => (
                                <div key={i}>
                                  <span className="text-xs text-gray-500">{seg.timestamp}s:</span>
                                  <p className="text-xs mt-0.5">{seg.onScreenText}</p>
                                </div>
                              ))}
                              {script.cta && (
                                <div>
                                  <span className="text-xs text-green-400">CTA:</span>
                                  <p className="text-xs mt-0.5">{script.cta.onScreenText}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {hashtags.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Hashtags</p>
                            <div className="flex flex-wrap gap-1">
                              {hashtags.map((tag: string, i: number) => (
                                <span key={i} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                                  #{tag.replace('#', '')}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {item.dm_trigger_keyword && (
                          <div className="bg-purple-900/20 border border-purple-800 rounded-lg p-3">
                            <p className="text-xs text-purple-400">
                              DM Trigger: "{item.dm_trigger_keyword}"
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

// ─── Main Content Page ──────────────────────────────

export default function Content() {
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);

  const fetchSchedule = async () => {
    try {
      const res = await fetch('/api/schedule');
      setSchedule(await res.json());
    } catch {
      // Server not running
    }
  };

  useEffect(() => { fetchSchedule(); }, []);

  const refreshAll = () => {
    fetchSchedule();
  };

  return (
    <div className="space-y-10">
      <ContentOptionsSection onScheduled={fetchSchedule} onPublished={refreshAll} />

      <div className="border-t border-gray-800" />

      <UpcomingScheduleSection schedule={schedule} onRefresh={fetchSchedule} />

      <div className="border-t border-gray-800" />

      <AllContentSection onScheduled={fetchSchedule} onPublished={refreshAll} />
    </div>
  );
}
