import React, { useEffect, useState } from 'react';

interface AISetting {
  id: number;
  name: string;
  content_builder_system: string | null;
  carousel_design_instruction: string | null;
  reel_visual_instruction: string | null;
  image_style_prefix: string | null;
  image_style_suffix: string | null;
  image_negative_prompt: string | null;
  temperature: number;
  is_active: number;
  created_at: string;
  updated_at: string;
}

interface AISettingsForm {
  name: string;
  content_builder_system: string;
  carousel_design_instruction: string;
  reel_visual_instruction: string;
  image_style_prefix: string;
  image_style_suffix: string;
  image_negative_prompt: string;
  temperature: number;
}

interface Defaults {
  content_builder_system: string;
  carousel_design_instruction: string;
  reel_visual_instruction: string;
  temperature: number;
}

const emptyForm: AISettingsForm = {
  name: '',
  content_builder_system: '',
  carousel_design_instruction: '',
  reel_visual_instruction: '',
  image_style_prefix: '',
  image_style_suffix: '',
  image_negative_prompt: '',
  temperature: 0.7,
};

function parseSettingToForm(s: AISetting): AISettingsForm {
  return {
    name: s.name,
    content_builder_system: s.content_builder_system || '',
    carousel_design_instruction: s.carousel_design_instruction || '',
    reel_visual_instruction: s.reel_visual_instruction || '',
    image_style_prefix: s.image_style_prefix || '',
    image_style_suffix: s.image_style_suffix || '',
    image_negative_prompt: s.image_negative_prompt || '',
    temperature: s.temperature,
  };
}

export default function AISettings() {
  const [settings, setSettings] = useState<AISetting[]>([]);
  const [defaults, setDefaults] = useState<Defaults | null>(null);
  const [form, setForm] = useState<AISettingsForm>({ ...emptyForm });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  const loadSettings = async () => {
    const res = await fetch('/api/ai-settings');
    const data = await res.json();
    setSettings(data);
  };

  const loadDefaults = async () => {
    const res = await fetch('/api/ai-settings/defaults');
    const data = await res.json();
    setDefaults(data);
  };

  useEffect(() => { loadSettings(); loadDefaults(); }, []);

  const activeSetting = settings.find(s => s.is_active);
  const pastSettings = settings.filter(s => !s.is_active);

  const handleSave = async () => {
    setSaving(true);
    if (editingId) {
      await fetch(`/api/ai-settings/${editingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
    } else {
      await fetch('/api/ai-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
    }
    setShowForm(false);
    setEditingId(null);
    setForm({ ...emptyForm });
    setSaving(false);
    loadSettings();
  };

  const handleActivate = async (id: number) => {
    await fetch(`/api/ai-settings/${id}/activate`, { method: 'POST' });
    loadSettings();
  };

  const handleDelete = async (id: number) => {
    await fetch(`/api/ai-settings/${id}`, { method: 'DELETE' });
    loadSettings();
  };

  const startEdit = (s: AISetting) => {
    setForm(parseSettingToForm(s));
    setEditingId(s.id);
    setShowForm(true);
  };

  const startNew = () => {
    setForm({ ...emptyForm });
    setEditingId(null);
    setShowForm(true);
  };

  const resetField = (field: keyof Defaults) => {
    if (defaults) {
      setForm({ ...form, [field]: defaults[field] });
    }
  };

  const formatDate = (d: string) => new Date(d + 'Z').toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">AI Settings</h2>
          <p className="text-gray-400 text-sm mt-1">
            Tune AI prompts, image generation style, and model parameters — no code changes needed
          </p>
        </div>
        {!showForm && (
          <button
            onClick={startNew}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium transition-colors"
          >
            + New Profile
          </button>
        )}
      </div>

      {/* Active Profile Card */}
      {activeSetting && !showForm && (
        <div className="bg-gray-900 border border-green-700/50 rounded-xl p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold">{activeSetting.name}</h3>
              <span className="px-2 py-0.5 text-xs font-medium bg-green-600/20 text-green-400 rounded-full">
                Active
              </span>
            </div>
            <button
              onClick={() => startEdit(activeSetting)}
              className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              Edit
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {activeSetting.content_builder_system && (
              <div className="md:col-span-2">
                <span className="text-gray-500 text-xs uppercase tracking-wide">System Prompt</span>
                <p className="text-gray-300 mt-1 whitespace-pre-wrap font-mono text-xs bg-gray-800 rounded-lg p-3 max-h-32 overflow-y-auto">
                  {activeSetting.content_builder_system}
                </p>
              </div>
            )}
            {activeSetting.image_style_prefix && (
              <div>
                <span className="text-gray-500 text-xs uppercase tracking-wide">Style Prefix</span>
                <p className="text-gray-300 mt-1">{activeSetting.image_style_prefix}</p>
              </div>
            )}
            {activeSetting.image_style_suffix && (
              <div>
                <span className="text-gray-500 text-xs uppercase tracking-wide">Style Suffix</span>
                <p className="text-gray-300 mt-1">{activeSetting.image_style_suffix}</p>
              </div>
            )}
            {activeSetting.image_negative_prompt && (
              <div>
                <span className="text-gray-500 text-xs uppercase tracking-wide">Negative Prompt</span>
                <p className="text-gray-300 mt-1">{activeSetting.image_negative_prompt}</p>
              </div>
            )}
            <div>
              <span className="text-gray-500 text-xs uppercase tracking-wide">Temperature</span>
              <p className="text-gray-300 mt-1">{activeSetting.temperature}</p>
            </div>
          </div>
          <p className="text-gray-600 text-xs mt-4">Created {formatDate(activeSetting.created_at)}</p>
        </div>
      )}

      {/* No Active Profile */}
      {!activeSetting && !showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-400">No active AI settings profile. Create one to customize AI behavior.</p>
        </div>
      )}

      {/* Settings Editor Form */}
      {showForm && (
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-6">
          <h3 className="text-lg font-semibold">
            {editingId ? 'Edit AI Profile' : 'New AI Settings Profile'}
          </h3>

          {/* Profile Name */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Profile Name</label>
            <input
              type="text"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="Cinematic Style v1"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
            />
          </div>

          {/* Section 1: Claude Personality */}
          <div className="border-t border-gray-800 pt-5">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wide">Claude Personality</h4>
              <button
                onClick={() => resetField('content_builder_system')}
                className="text-xs text-purple-400 hover:text-purple-300"
              >
                Reset to Default
              </button>
            </div>
            <label className="block text-sm text-gray-400 mb-1">System Prompt</label>
            <textarea
              value={form.content_builder_system}
              onChange={e => setForm({ ...form, content_builder_system: e.target.value })}
              placeholder="Leave blank to use the default system prompt..."
              rows={15}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-purple-500 resize-y"
            />
            <p className="text-gray-600 text-xs mt-1">
              The personality and rules that guide Claude when generating content scripts. Leave blank to use the built-in default.
            </p>
          </div>

          {/* Section 2: Image Prompt Instructions */}
          <div className="border-t border-gray-800 pt-5">
            <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wide mb-3">Image Prompt Instructions</h4>

            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm text-gray-400">Carousel Design Instruction</label>
                  <button
                    onClick={() => resetField('carousel_design_instruction')}
                    className="text-xs text-purple-400 hover:text-purple-300"
                  >
                    Reset to Default
                  </button>
                </div>
                <textarea
                  value={form.carousel_design_instruction}
                  onChange={e => setForm({ ...form, carousel_design_instruction: e.target.value })}
                  placeholder="Leave blank for default..."
                  rows={6}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500 resize-y"
                />
                <p className="text-gray-600 text-xs mt-1">
                  Tells Claude how to write the designNotes field for each carousel slide.
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm text-gray-400">Reel Visual Instruction</label>
                  <button
                    onClick={() => resetField('reel_visual_instruction')}
                    className="text-xs text-purple-400 hover:text-purple-300"
                  >
                    Reset to Default
                  </button>
                </div>
                <textarea
                  value={form.reel_visual_instruction}
                  onChange={e => setForm({ ...form, reel_visual_instruction: e.target.value })}
                  placeholder="Leave blank for default..."
                  rows={6}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500 resize-y"
                />
                <p className="text-gray-600 text-xs mt-1">
                  Tells Claude how to write the visual field for reel hook, body segments, and CTA.
                </p>
              </div>
            </div>
          </div>

          {/* Section 3: Image Generation Style */}
          <div className="border-t border-gray-800 pt-5">
            <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wide mb-3">Image Generation Style</h4>
            <p className="text-gray-600 text-xs mb-4">
              These are injected into the prompt sent to Flux Schnell (Replicate). They wrap around Claude's visual description.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Style Prefix</label>
                <input
                  type="text"
                  value={form.image_style_prefix}
                  onChange={e => setForm({ ...form, image_style_prefix: e.target.value })}
                  placeholder="cinematic, 8k, dramatic lighting, high detail"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
                />
                <p className="text-gray-600 text-xs mt-1">Prepended to every image generation prompt.</p>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Style Suffix</label>
                <input
                  type="text"
                  value={form.image_style_suffix}
                  onChange={e => setForm({ ...form, image_style_suffix: e.target.value })}
                  placeholder="sharp focus, professional photography, no text"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
                />
                <p className="text-gray-600 text-xs mt-1">Appended to every image generation prompt.</p>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Negative Prompt</label>
                <input
                  type="text"
                  value={form.image_negative_prompt}
                  onChange={e => setForm({ ...form, image_negative_prompt: e.target.value })}
                  placeholder="blurry, low quality, text, watermark, deformed"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
                />
                <p className="text-gray-600 text-xs mt-1">Added as "Do not include: ..." at the end of the prompt.</p>
              </div>
            </div>
          </div>

          {/* Section 4: Model Parameters */}
          <div className="border-t border-gray-800 pt-5">
            <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wide mb-3">Model Parameters</h4>

            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Temperature: <span className="text-purple-400 font-medium">{form.temperature}</span>
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={form.temperature}
                onChange={e => setForm({ ...form, temperature: parseFloat(e.target.value) })}
                className="w-full accent-purple-500"
              />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>0.0 (Focused)</span>
                <span>1.0 (Creative)</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={handleSave}
              disabled={!form.name.trim() || saving}
              className="px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
            >
              {saving ? 'Saving...' : editingId ? 'Save Changes' : 'Create Profile'}
            </button>
            <button
              onClick={() => { setShowForm(false); setEditingId(null); setForm({ ...emptyForm }); }}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Past Profiles */}
      {pastSettings.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-3">Past Profiles</h3>
          <div className="space-y-2">
            {pastSettings.map(s => (
              <div key={s.id} className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 flex items-center justify-between">
                <div>
                  <span className="font-medium text-sm">{s.name}</span>
                  <span className="text-gray-500 text-xs ml-2">{formatDate(s.created_at)}</span>
                  <span className="text-gray-500 text-xs ml-2">— temp {s.temperature}</span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleActivate(s.id)}
                    className="px-3 py-1 text-xs bg-green-600/20 text-green-400 hover:bg-green-600/30 rounded-lg transition-colors"
                  >
                    Activate
                  </button>
                  <button
                    onClick={() => startEdit(s)}
                    className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(s.id)}
                    className="px-3 py-1 text-xs bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded-lg transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
