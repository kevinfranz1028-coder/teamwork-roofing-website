import React, { useState } from 'react';
import PipelineStatus from './pages/PipelineStatus.js';
import ContentQueue from './pages/ContentQueue.js';
import Analytics from './pages/Analytics.js';
import Scorecard from './pages/Scorecard.js';
import Revenue from './pages/Revenue.js';
import BuildChecklist from './pages/BuildChecklist.js';

const tabs = [
  { id: 'status', label: 'Pipeline' },
  { id: 'queue', label: 'Content Queue' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'scorecard', label: 'Scorecard' },
  { id: 'revenue', label: 'Revenue' },
  { id: 'checklist', label: 'Build Checklist' },
] as const;

type TabId = (typeof tabs)[number]['id'];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('status');

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">
            <span className="text-purple-400">IG</span> Theme Engine
          </h1>
          <span className="text-xs text-gray-500">v1.0.0</span>
        </div>
        {/* Tab Navigation */}
        <nav className="max-w-7xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-gray-950 text-purple-400 border-t-2 border-purple-400'
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
        {activeTab === 'queue' && <ContentQueue />}
        {activeTab === 'analytics' && <Analytics />}
        {activeTab === 'scorecard' && <Scorecard />}
        {activeTab === 'revenue' && <Revenue />}
        {activeTab === 'checklist' && <BuildChecklist />}
      </main>
    </div>
  );
}
