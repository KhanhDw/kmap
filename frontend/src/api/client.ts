const API_URL = import.meta.env.VITE_API_URL ?? "/api/v1";

export type ApiError = { code: string; message: string };

function isErrorEnvelope(body: unknown): body is { error: ApiError } {
  if (typeof body !== "object" || body === null || !("error" in body)) {
    return false;
  }

  const error = body.error;
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof error.code === "string" &&
    "message" in error &&
    typeof error.message === "string"
  );
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { Accept: "application/json" },
    credentials: "include",
  });

  const body: unknown = await response.json();
  if (!response.ok) {
    const apiError = isErrorEnvelope(body)
      ? body.error
      : { code: "unknown_error", message: `HTTP ${response.status}` };
    throw new Error(apiError.message);
  }

  return body as T;
}
