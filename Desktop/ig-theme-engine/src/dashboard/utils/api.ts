const STORAGE_KEY = 'planticu-api-key';

export function getApiKey(): string {
  return localStorage.getItem(STORAGE_KEY) || '';
}

export function setApiKey(key: string): void {
  localStorage.setItem(STORAGE_KEY, key);
}

export function clearApiKey(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const apiKey = getApiKey();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  return fetch(path, { ...options, headers });
}
