import React, { useEffect, useState } from 'react';

interface PipelineState {
  phase: string;
  lastRun: string | null;
  todaysPackage: any | null;
  errors: string[];
}

export default function PipelineStatus() {
  const [state, setState] = useState<PipelineState | null>(null);
  const [running, setRunning] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      setState(await res.json());
    } catch {
      // Server not running
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const triggerPipeline = async () => {
    setRunning(true);
    try {
      await fetch('/api/pipeline/run', { method: 'POST' });
      await fetchStatus();
    } finally {
      setRunning(false);
    }
  };

  const phaseColors: Record<string, string> = {
    idle: 'text-gray-400',
    generating: 'text-yellow-400',
    awaiting_approval: 'text-blue-400',
    publishing: 'text-green-400',
    analyzing: 'text-purple-400',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Pipeline Status</h2>
        <button
          onClick={triggerPipeline}
          disabled={running}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-sm font-medium transition-colors"
        >
          {running ? 'Generating...' : 'Run Daily Pipeline'}
        </button>
      </div>

      {state ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Phase Card */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Current Phase</p>
            <p className={`text-lg font-semibold capitalize ${phaseColors[state.phase] || 'text-gray-300'}`}>
              {state.phase.replace('_', ' ')}
            </p>
          </div>

          {/* Last Run Card */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Last Run</p>
            <p className="text-lg font-semibold">
              {state.lastRun
                ? new Date(state.lastRun).toLocaleString()
                : 'Never'}
            </p>
          </div>

          {/* Errors Card */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Errors</p>
            {state.errors.length > 0 ? (
              <div className="space-y-1">
                {state.errors.map((e, i) => (
                  <p key={i} className="text-sm text-red-400">{e}</p>
                ))}
              </div>
            ) : (
              <p className="text-lg font-semibold text-green-400">None</p>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-500">Connecting to server...</p>
          <p className="text-xs text-gray-600 mt-2">Make sure the API server is running on port 3847</p>
        </div>
      )}

      {/* Today's Package Preview */}
      {state?.todaysPackage && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4">Today's Content Package</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Carousel */}
            <div className="bg-gray-800 rounded-lg p-4">
              <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">Carousel</span>
              <p className="mt-2 font-medium">{state.todaysPackage.carousel?.idea?.title}</p>
              <p className="text-sm text-gray-400 mt-1">{state.todaysPackage.carousel?.idea?.sendTrigger}</p>
            </div>
            {/* Reel */}
            <div className="bg-gray-800 rounded-lg p-4">
              <span className="text-xs bg-pink-600 text-white px-2 py-0.5 rounded-full">Reel</span>
              <p className="mt-2 font-medium">{state.todaysPackage.reel?.idea?.title}</p>
              <p className="text-sm text-gray-400 mt-1">{state.todaysPackage.reel?.idea?.sendTrigger}</p>
            </div>
            {/* Stories */}
            <div className="bg-gray-800 rounded-lg p-4">
              <span className="text-xs bg-orange-600 text-white px-2 py-0.5 rounded-full">Stories</span>
              <p className="mt-2 font-medium">{state.todaysPackage.storySequence?.slides?.length || 0} slides</p>
              <p className="text-sm text-gray-400 mt-1">
                DM trigger: "{state.todaysPackage.storySequence?.dmTriggerKeyword}"
              </p>
            </div>
          </div>

          {/* Trend Alert */}
          {state.todaysPackage.trendAlert?.hasTrend && (
            <div className="mt-4 bg-yellow-900/30 border border-yellow-700 rounded-lg p-3">
              <p className="text-yellow-400 text-sm font-medium">
                TREND ALERT: {state.todaysPackage.trendAlert.topic}
              </p>
              <p className="text-yellow-600 text-xs mt-1">{state.todaysPackage.trendAlert.originalAngle}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
