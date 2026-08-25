interface ApiErrorBody {
  detail?: unknown;
  error?: unknown;
  [key: string]: unknown;
}

interface ApiErrorLike {
  status?: number;
  error?: ApiErrorBody | string | null;
}

export function adminApiErrorMessage(error: unknown, fallback: string): string {
  const response = error as ApiErrorLike;
  const body = response?.error;
  if (typeof body === 'string' && body.trim()) {
    return body;
  }
  if (body && typeof body === 'object') {
    for (const value of [body.detail, body.error, ...Object.values(body)]) {
      if (typeof value === 'string' && value.trim()) {
        return value;
      }
      if (Array.isArray(value)) {
        const message = value.find(item => typeof item === 'string');
        if (typeof message === 'string' && message.trim()) {
          return message;
        }
      }
    }
  }
  if (response?.status === 403) {
    return 'El backend rechazó la operación por falta de autoridad.';
  }
  return fallback;
}
