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
