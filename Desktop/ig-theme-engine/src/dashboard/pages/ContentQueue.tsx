import React, { useEffect, useState } from 'react';

interface QueueItem {
  id: number;
  idea_id: number;
  content_type: string;
  script_json: string;
  caption: string;
  hashtags: string;
  title: string;
  idea_status: string;
  send_trigger: string;
  dm_trigger_keyword: string;
}

export default function ContentQueue() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);

  const fetchQueue = async () => {
    try {
      const res = await fetch('/api/queue');
      setItems(await res.json());
    } catch {
      // Server not running
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleApprove = async (id: number) => {
    await fetch(`/api/queue/${id}/approve`, { method: 'POST' });
    fetchQueue();
  };

  const handleReject = async (id: number) => {
    await fetch(`/api/queue/${id}/reject`, { method: 'POST' });
    fetchQueue();
  };

  const typeColors: Record<string, string> = {
    carousel: 'bg-blue-600',
    reel: 'bg-pink-600',
    story: 'bg-orange-600',
    static: 'bg-green-600',
  };

  const statusColors: Record<string, string> = {
    scripted: 'text-yellow-400',
    approved: 'text-green-400',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Content Queue</h2>
        <span className="text-sm text-gray-500">{items.length} items</span>
      </div>

      {items.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-500">No content in queue</p>
          <p className="text-xs text-gray-600 mt-2">Run the daily pipeline to generate content</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            let script: any = {};
            try { script = JSON.parse(item.script_json); } catch {}

            return (
              <div key={item.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                {/* Header Row */}
                <div
                  className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-800/50 transition-colors"
                  onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                >
                  <div className="flex items-center gap-3">
                    <span className={`text-xs text-white px-2 py-0.5 rounded-full ${typeColors[item.content_type] || 'bg-gray-600'}`}>
                      {item.content_type}
                    </span>
                    <span className="font-medium">{item.title || script?.idea?.title || 'Untitled'}</span>
                    <span className={`text-xs ${statusColors[item.idea_status] || 'text-gray-400'}`}>
                      {item.idea_status}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {item.idea_status === 'scripted' && (
                      <>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleApprove(item.id); }}
                          className="px-3 py-1 bg-green-700 hover:bg-green-600 text-sm rounded-lg transition-colors"
                        >
                          Approve
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleReject(item.id); }}
                          className="px-3 py-1 bg-red-900 hover:bg-red-800 text-sm rounded-lg transition-colors"
                        >
                          Reject
                        </button>
                      </>
                    )}
                    <span className="text-gray-500 text-sm">{expanded === item.id ? '▲' : '▼'}</span>
                  </div>
                </div>

                {/* Expanded Content */}
                {expanded === item.id && (
                  <div className="border-t border-gray-800 p-4 space-y-4">
                    {/* Send Trigger */}
                    {item.send_trigger && (
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Send Trigger</p>
                        <p className="text-sm text-purple-300">{item.send_trigger}</p>
                      </div>
                    )}

                    {/* Caption */}
                    {item.caption && (
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Caption</p>
                        <p className="text-sm text-gray-300 whitespace-pre-wrap">{item.caption}</p>
                      </div>
                    )}

                    {/* Slides (for carousels) */}
                    {script?.slides && (
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Slides ({script.slides.length})</p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                          {script.slides.map((slide: any, i: number) => (
                            <div key={i} className="bg-gray-800 rounded-lg p-3">
                              <p className="text-xs text-gray-500">Slide {slide.slideNumber || i + 1}</p>
                              <p className="text-sm font-medium mt-1">{slide.headline}</p>
                              {slide.bodyText && <p className="text-xs text-gray-400 mt-1">{slide.bodyText}</p>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Reel Script (for reels) */}
                    {script?.hook && item.content_type === 'reel' && (
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Reel Script</p>
                        <div className="bg-gray-800 rounded-lg p-3 space-y-2">
                          <div>
                            <span className="text-xs text-pink-400">HOOK (0-1.7s):</span>
                            <p className="text-sm">{script.hook.onScreenText}</p>
                          </div>
                          {script.body?.map((seg: any, i: number) => (
                            <div key={i}>
                              <span className="text-xs text-gray-500">{seg.timestamp}s:</span>
                              <p className="text-sm">{seg.onScreenText}</p>
                              {seg.voiceoverScript && (
                                <p className="text-xs text-gray-400 italic">VO: {seg.voiceoverScript}</p>
                              )}
                            </div>
                          ))}
                          {script.cta && (
                            <div>
                              <span className="text-xs text-green-400">CTA:</span>
                              <p className="text-sm">{script.cta.onScreenText}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Hashtags */}
                    {item.hashtags && (
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Hashtags</p>
                        <div className="flex flex-wrap gap-1">
                          {JSON.parse(item.hashtags).map((tag: string, i: number) => (
                            <span key={i} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                              #{tag.replace('#', '')}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* DM Trigger */}
                    {item.dm_trigger_keyword && (
                      <div className="bg-purple-900/20 border border-purple-800 rounded-lg p-3">
                        <p className="text-xs text-purple-400">DM Trigger Keyword: "{item.dm_trigger_keyword}"</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
