const BASE = import.meta.env.VITE_API_BASE;
console.log("VITE_API_BASE =", BASE);

if (!BASE) {
  throw new Error("VITE_API_BASE is not set. Put it in a .env at project root and restart dev server.");
}

// This is the error class
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const apiFetch = async <T>(
  path: string,
  opts: RequestInit = {},
  token?: string
): Promise<T> => {
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(res.status, text || res.statusText);
  }
  // Handle 204
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
};
