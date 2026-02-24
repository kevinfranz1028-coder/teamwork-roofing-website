import React, { useState, useEffect } from 'react';
import PipelineStatus from './pages/PipelineStatus.js';
import Content from './pages/Content.js';
import Analytics from './pages/Analytics.js';
import Scorecard from './pages/Scorecard.js';
import Revenue from './pages/Revenue.js';
import BuildChecklist from './pages/BuildChecklist.js';
import CreativeBrief from './pages/CreativeBrief.js';
import AISettings from './pages/AISettings.js';
import BuildDoc from './pages/BuildDoc.js';
import { getApiKey, setApiKey, clearApiKey, apiFetch } from './utils/api.js';

const tabs = [
  { id: 'status', label: 'Pipeline' },
  { id: 'content', label: 'Content' },
  { id: 'brief', label: 'Brief' },
  { id: 'ai-settings', label: 'AI Settings' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'scorecard', label: 'Scorecard' },
  { id: 'revenue', label: 'Revenue' },
  { id: 'checklist', label: 'Build Checklist' },
  { id: 'build-doc', label: 'Build Doc' },
] as const;

type TabId = (typeof tabs)[number]['id'];

function LoginScreen({ onLogin }: { onLogin: () => void }) {
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setApiKey(key);
    try {
      const res = await apiFetch('/api/status');
      if (res.status === 401) {
        clearApiKey();
        setError('Invalid API key');
      } else {
        onLogin();
      }
    } catch {
      setError('Cannot connect to server');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold mb-1">
          <span className="text-green-400">ThePlant</span><span className="text-green-600">ICU</span>
        </h1>
        <p className="text-gray-500 text-sm mb-6">Content Engine — Enter your API key to continue</p>
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="API Key"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-green-500 mb-4"
            autoFocus
          />
          {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
          <button
            type="submit"
            disabled={loading || !key}
            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-700 text-white font-medium py-3 rounded-lg transition-colors"
          >
            {loading ? 'Verifying...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('status');
  const [authed, setAuthed] = useState<boolean | null>(null); // null = checking

  useEffect(() => {
    // Check if auth is required
    apiFetch('/api/status')
      .then(res => {
        if (res.status === 401) {
          setAuthed(false);
        } else {
          setAuthed(true);
        }
      })
      .catch(() => setAuthed(true)); // If server unreachable, show dashboard anyway
  }, []);

  if (authed === null) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!authed) {
    return <LoginScreen onLogin={() => setAuthed(true)} />;
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">
            <span className="text-green-400">ThePlant</span><span className="text-green-600">ICU</span>
            <span className="text-gray-500 font-normal text-sm ml-2">Content Engine</span>
          </h1>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">v1.0.0</span>
            {getApiKey() && (
              <button
                onClick={() => { clearApiKey(); setAuthed(false); }}
                className="text-xs text-gray-500 hover:text-red-400 transition-colors"
              >
                Sign Out
              </button>
            )}
          </div>
        </div>
        {/* Tab Navigation */}
        <nav className="max-w-7xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-gray-950 text-green-400 border-t-2 border-green-400'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'status' && <PipelineStatus />}
        {activeTab === 'content' && <Content />}
        {activeTab === 'brief' && <CreativeBrief />}
        {activeTab === 'ai-settings' && <AISettings />}
        {activeTab === 'analytics' && <Analytics />}
        {activeTab === 'scorecard' && <Scorecard />}
        {activeTab === 'revenue' && <Revenue />}
        {activeTab === 'checklist' && <BuildChecklist />}
        {activeTab === 'build-doc' && <BuildDoc />}
      </main>
    </div>
  );
}
