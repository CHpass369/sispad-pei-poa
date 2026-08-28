interface ApiErrorBody {
  detail?: unknown;
  error?: unknown;
  [key: string]: unknown;
}

interface ApiErrorLike {
  status?: number;
  message?: unknown;
  error?: ApiErrorBody | string | null;
}

/** Angular's own transport message; never useful to show to an operator. */
const RAW_TRANSPORT_MESSAGE = /^Http failure /;

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
  // `ErrorInterceptor` is registered globally, so components never see a raw
  // HttpErrorResponse: the body is already flattened into `{message, status}`
  // and `error` is gone. Without this branch every backend reason below 403
  // was replaced by the caller's generic fallback.
  if (
    typeof response?.message === 'string'
    && response.message.trim()
    && !RAW_TRANSPORT_MESSAGE.test(response.message)
  ) {
    return response.message;
  }
  if (response?.status === 403) {
    return 'El backend rechazó la operación por falta de autoridad.';
  }
  return fallback;
}
