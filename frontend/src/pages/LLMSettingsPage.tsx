import { useState, useEffect } from "react";
import { getLLMProviders, getLLMSettings, saveLLMSettings, api } from "../api";

interface Provider {
  value: string;
  label: string;
  model: string;
}

export function LLMSettingsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [apiKey, setApiKey] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [showApiKey, setShowApiKey] = useState(false);

  useEffect(() => {
    loadProviders();
    loadSettings();
  }, []);

  async function loadProviders() {
    try {
      const data = await getLLMProviders();
      setProviders(data);
    } catch (err) {
      setError("Failed to load providers");
    }
  }

  async function loadSettings() {
    try {
      const settings = await getLLMSettings();
      setSelectedProvider(settings.provider);
      setApiKey(settings.has_api_key ? "•••••••••" : "");
    } catch (err) {
      setError("Failed to load settings");
    }
  }

  async function handleTestConnection(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProvider || !apiKey.trim()) {
      setError("Please select a provider and enter an API key");
      return;
    }

    setTesting(true);
    setError("");
    setMessage("");

    try {
      const response = await api.post('/api/v1/llm/test', {
        provider: selectedProvider,
        api_key: apiKey
      });

      const result = await response.data;
      
      if (result.success) {
        setMessage(`✅ Connection test successful! Your ${selectedProvider === 'groq' ? 'Groq' : 'OpenAI'} API key is working correctly.`);
      } else {
        setError(`Test failed: ${result.error}`);
      }
    } catch (err: any) {
      const errorMessage = typeof err === 'string' ? err : 'Connection test failed';
      
      // Provide better error messages based on error type
      if (errorMessage && (errorMessage as string).includes('invalid_api_key') || (errorMessage as string).includes('Invalid API key')) {
        setError('Invalid API key. Please check your Groq API key and try again.');
      } else if (errorMessage && ((errorMessage as string).includes('rate') || (errorMessage as string).includes('quota'))) {
        setError('Rate limit exceeded. Please try again later.');
      } else if (errorMessage && ((errorMessage as string).includes('connection') || (errorMessage as string).includes('network'))) {
        setError('Connection error. Please check your internet connection and try again.');
      } else {
        setError(`Test failed: ${errorMessage}`);
      }
    } finally {
      setTesting(false);
      // Clear message after 3 seconds for better UX
      setTimeout(() => {
        setMessage("");
        setError("");
      }, 3000);
    }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProvider || !apiKey.trim()) {
      setError("Please select a provider and enter an API key");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      await saveLLMSettings(selectedProvider, apiKey);
      setMessage("✅ Settings saved successfully! Your configuration has been stored.");
      // Clear message after 5 seconds for better UX
      setTimeout(() => {
        setMessage("");
      }, 5000);
    } catch (err) {
      setError("Failed to save settings");
    } finally {
      setLoading(false);
    }
  }

  const selectedProviderData = providers.find(p => p.value === selectedProvider);

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">AI Model Settings</h1>
        <p className="mt-2 text-sm text-slate-400">
          Choose your preferred AI provider and enter your API key. Your selection will be used for generating investment reports.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
        <form onSubmit={handleSave} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              AI Provider
            </label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
            >
              <option value="">Select a provider...</option>
              {providers.map((provider) => (
                <option key={provider.value} value={provider.value}>
                  {provider.label} ({provider.model})
                </option>
              ))}
            </select>
          </div>

          <div className="relative">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              API Key
            </label>
            <div className="relative">
              <input
                type={showApiKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key..."
                className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2 top-1/2 text-slate-400 hover:text-slate-300"
                style={{ transform: 'translateY(-50%)' }}
              >
                {showApiKey ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 20 20">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 20 20">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {selectedProviderData && (
            <p className="mt-2 text-xs text-slate-500">
              Get your API key from the {selectedProviderData.label} developer console.
            </p>
          )}

          {message && (
            <div className="rounded border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
              {message}
            </div>
          )}

          {error && (
            <div className="rounded border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testing || !selectedProvider || !apiKey.trim()}
              className="flex-1 rounded border border-slate-600 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-700 disabled:opacity-50"
            >
              {testing ? "Testing..." : "Test Connection"}
            </button>
            
            <button
              type="submit"
              disabled={loading || testing}
              className="flex-1 rounded bg-indigo-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-600 disabled:opacity-50"
            >
              {loading ? "Saving..." : "Save Settings"}
            </button>
          </div>
        </form>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Provider Information</h2>
        <div className="space-y-4 text-sm">
          {providers.map((provider) => (
            <div key={provider.value} className="border-b border-slate-800 pb-3 last:border-0">
              <h3 className="font-medium text-white">{provider.label}</h3>
              <p className="text-slate-400 mt-1">Model: {provider.model}</p>
              <div className="mt-2 text-xs text-slate-500">
                {provider.value === "openai" && "OpenAI's GPT models provide excellent analysis quality. Free tier: 1M tokens/month."}
                {provider.value === "groq" && "Groq offers fast inference with Llama models. Free tier: 30 requests/minute."}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
