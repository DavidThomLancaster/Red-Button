import type { JobEmailBatchesDTO, EmailDetailsDTO } from "../types";
const BASE = import.meta.env.VITE_API_BASE ?? "";

const auth = (t: string) => (t?.startsWith("Bearer ") ? t : `Bearer ${t}`);

async function handle(res: Response) {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err: any = new Error(text || `HTTP ${res.status}`);
    err.status = res.status;
    err.body = text;
    throw err;
  }
  return res.json();
}

export async function getEmailBatchesApi(token: string, jobId: string): Promise<JobEmailBatchesDTO> {
  const r = await fetch(`${BASE}/jobs/${jobId}/email_batches`, {
    headers: { Authorization: auth(token), Accept: "application/json" },
  });
  return handle(r);
}

// matches your existing handler path:
export async function getEmailDetailsApi(token: string, jobId: string, emailId: string): Promise<EmailDetailsDTO> {
  const r = await fetch(`${BASE}/get_email_details/job/${jobId}/email/${emailId}`, {
    headers: { Authorization: auth(token), Accept: "application/json" },
  });
  return handle(r);
}

// PATCH update (subject/body/to_email/status)
export async function patchEmailApi(
  token: string,
  jobId: string,
  emailId: string,
  patch: Partial<Pick<EmailDetailsDTO, "subject"|"body"|"to_email"|"status">>
): Promise<EmailDetailsDTO> {
  const r = await fetch(`${BASE}/jobs/${jobId}/emails/${emailId}`, {
    method: "PATCH",
    headers: { Authorization: auth(token), "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(patch),
  });
  return handle(r);
}

// Delete ONE email (tries REST; falls back to your older POST if needed)
export async function deleteEmailApi(token: string, jobId: string, emailId: string): Promise<void> {
  let r = await fetch(`${BASE}/jobs/${jobId}/emails/${emailId}`, {
    method: "DELETE",
    headers: { Authorization: auth(token) },
  });
  if (r.status === 404 || r.status === 405) {
    r = await fetch(`${BASE}/delete_email/job/${jobId}/email/${emailId}`, {
      method: "POST",
      headers: { Authorization: auth(token) },
    });
  }
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    const err: any = new Error(text || `HTTP ${r.status}`);
    err.status = r.status;
    throw err;
  }
}

// Delete ENTIRE batch (adjust path to your handler)
export async function deleteEmailBatchApi(token: string, jobId: string, batchId: string): Promise<void> {
  const r = await fetch(`${BASE}/delete_email_batch/job/${jobId}/batch/${batchId}`, {
    method: "DELETE",
    headers: { Authorization: auth(token) },
  });
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    const err: any = new Error(text || `HTTP ${r.status}`);
    err.status = r.status;
    throw err;
  }
}


// import type { JobEmailBatchesDTO } from "../types"; // is it types?
// import { apiFetch } from "./client";    

// //const BASE = import.meta.env.VITE_API_BASE ?? "";
// const BASE = import.meta.env.VITE_API_BASE;

// export const getEmailBatchesApi = (token: string, jobId: string) => 
//     apiFetch<JobEmailBatchesDTO>(`/jobs/${encodeURIComponent(jobId)}/email_batches`, {
//     }, token);
