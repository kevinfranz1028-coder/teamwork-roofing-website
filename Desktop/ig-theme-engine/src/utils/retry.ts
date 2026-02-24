interface RetryOptions {
  maxAttempts: number;
  delayMs: number;
  backoffMultiplier: number;
  onRetry?: (attempt: number, error: Error) => void;
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = { maxAttempts: 3, delayMs: 1000, backoffMultiplier: 2 }
): Promise<T> {
  let lastError: Error;

  for (let attempt = 1; attempt <= options.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      lastError = err;
      if (attempt < options.maxAttempts) {
        const delay = options.delayMs * Math.pow(options.backoffMultiplier, attempt - 1);
        options.onRetry?.(attempt, err);
        console.warn(`Retry ${attempt}/${options.maxAttempts} after ${delay}ms: ${err.message}`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError!;
}

export async function withFallback<T>(
  primary: () => Promise<T>,
  fallback: () => Promise<T>,
  label: string = 'operation'
): Promise<T> {
  try {
    return await primary();
  } catch (err: any) {
    console.warn(`${label} primary failed (${err.message}), using fallback...`);
    return await fallback();
  }
}
