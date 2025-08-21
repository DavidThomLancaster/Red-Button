import { apiFetch } from "./client";

type AuthResponse =
  | { token: string }
  | { access_token: string; token_type?: string; expires_in?: number };

const extractToken = (r: AuthResponse) => ("token" in r ? r.token : r.access_token);

export const loginApi = async (email: string, password: string) => {
  const r = await apiFetch<AuthResponse>("/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return extractToken(r); // <-- always a string
};

export const registerApi = async (email: string, password: string) => {
  const r = await apiFetch<AuthResponse>("/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return extractToken(r); // or choose to return nothing & redirect to /login
};



// import { apiFetch } from "./client";

// export const loginApi = (email: string, password: string) =>
//   apiFetch<{ token: string }>("/login", {
//     method: "POST",
//     body: JSON.stringify({ email, password }),
//   });

// export const registerApi = (email: string, password: string) =>
//   apiFetch<{ token: string }>("/register", {
//     method: "POST",
//     body: JSON.stringify({ email, password }),
//   });
