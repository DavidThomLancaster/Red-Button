// TODO - Need a function that calls the new backend endpoint to get contacts based on parameters
console.log("hello world")

export type ContactSearchReq = {
  trade?: string | null;
  name?: string | null;
  service_area?: string | null;
  limit?: number;
  page?: number;
};

export type ContactOut = {
  id: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  service_area?: string | null;
};

export type ContactSearchResp = {
  items: ContactOut[];
  limit: number;
  page: number;
  count: number; // count of items in this page
};

export type CreateContactReq = {
  name: string;
  email?: string | null;
  phone?: string | null;
  service_area?: string | null;
  trades?: string[];
};

export async function searchContactsApi(
  token: string,
  jobId: string,
  body: ContactSearchReq
): Promise<ContactSearchResp> {
  const res = await fetch(`${import.meta.env.VITE_API_BASE}/jobs/${jobId}/contacts/search`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Search failed ${res.status}: ${text}`);
  }
  return res.json();
}

const BASE = import.meta.env.VITE_API_BASE;

export async function searchMyContactsApi(
  token: string,
  body: ContactSearchReq
): Promise<ContactSearchResp> {
  const jobId = "my-contacts"; // placeholder, not used in backend for my contacts
  const res = await fetch(`${BASE}/jobs/${jobId}/contacts/search`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function createMyContactApi(
  token: string,
  body: CreateContactReq
): Promise<ContactOut> {
  const res = await fetch(`${import.meta.env.VITE_API_BASE}/my/contacts`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Create failed: ${res.status}`);
  }
  return res.json();
}
