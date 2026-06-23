export type ApiErrorField = {
  field: string;
  code: string;
  message: string;
};

export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    fields?: ApiErrorField[];
  };
};

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public body: ApiErrorBody["error"],
  ) {
    super(body.message);
  }
}

export class SessionExpiredError extends Error {
  constructor() {
    super("Your session has expired. Please sign in again.");
  }
}

export class RateLimitError extends Error {
  constructor(public retryAfter: string | null) {
    super("Too many requests. Please try again later.");
  }
}

export function mapFieldErrors(
  fields: ApiErrorField[] | undefined,
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const f of fields ?? []) {
    out[f.field] = f.message;
  }
  return out;
}
