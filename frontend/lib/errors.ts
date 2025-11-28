/**
 * Error handling utilities for the frontend
 */

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network connection failed') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public field?: string
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Parse error from API response
 */
export async function parseAPIError(response: Response): Promise<APIError> {
  try {
    const data = await response.json();
    return new APIError(
      data.error || 'Request failed',
      response.status,
      data.detail
    );
  } catch {
    return new APIError(
      response.statusText || 'Request failed',
      response.status
    );
  }
}

/**
 * Get user-friendly error message
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof APIError) {
    if (error.statusCode === 404) {
      return 'Datos no encontrados. Por favor verifica el ticker.';
    }
    if (error.statusCode === 429) {
      return 'Demasiadas solicitudes. Por favor espera un momento.';
    }
    if (error.statusCode === 503) {
      return 'Servicio no disponible temporalmente. Intenta de nuevo.';
    }
    return error.detail || error.message;
  }

  if (error instanceof NetworkError) {
    return 'Error de conexión. Por favor verifica tu conexión a internet.';
  }

  if (error instanceof ValidationError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Ha ocurrido un error inesperado. Por favor intenta de nuevo.';
}

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      // Don't retry on client errors (4xx)
      if (error instanceof APIError && error.statusCode >= 400 && error.statusCode < 500) {
        throw error;
      }

      // Don't retry on last attempt
      if (attempt === maxRetries - 1) {
        break;
      }

      // Wait with exponential backoff
      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError!;
}

/**
 * Check if error is retryable
 */
export function isRetryableError(error: unknown): boolean {
  if (error instanceof APIError) {
    // Retry on server errors (5xx) and rate limits
    return error.statusCode >= 500 || error.statusCode === 429;
  }

  if (error instanceof NetworkError) {
    return true;
  }

  return false;
}
