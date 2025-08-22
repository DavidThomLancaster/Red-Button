import { apiFetch } from "./client";
//import type { Job } from "../types";
import type { Job, ContactMapPreview, GetJobResponse, SubmitPdfResponse } from "../types";



export const listJobsApi = (token: string) =>
  apiFetch<{ jobs: Job[] }>("/get_job", {}, token);

export const createJobApi = (token: string, name: string, notes?: string) =>
  apiFetch<{ job_id: string }>("/create_job", {
    method: "POST",
    body: JSON.stringify({ name, notes }),
  }, token);

export const deleteJobApi = (token: string, job_id: string) =>
  apiFetch<{ status: string; job_id: string }>(`/jobs/${encodeURIComponent(job_id)}`, {
    method: "DELETE",
  }, token);

export const getJobAPI = (token: string, jobId: string) =>
  apiFetch<GetJobResponse>(`/jobs/${encodeURIComponent(jobId)}`, {}, token);

// export const getContactsMapApi = (token: string, jobId: string) =>
//   apiFetch<{ status: string; job_id: string; ref: string; map: ContactsMap; contactsById: Record<string, ContactSummary> }>(
//     `/jobs/${encodeURIComponent(jobId)}/contacts-map`, {}, token
//   );

export const generateEmailsApi = (token: string, job_id: string) =>
  apiFetch<{ status: string; job_id: string }>(`/generate_emails/${encodeURIComponent(job_id)}`, {
    method: "POST",
  }, token);

const BASE = import.meta.env.VITE_API_BASE;

// TODO - Perhaps I should modify this to work with clients.ts like the other functions.
export async function submitPdfAPI(
  token: string,
  jobId: string,
  file: File
): Promise<SubmitPdfResponse> {
  const form = new FormData();
  form.append("job_id", jobId);          // <-- must match backend Form(...)
  form.append("pdf_file", file, file.name); // <-- must match backend File()

  const res = await fetch(`${BASE}/submit_pdf`, {
    method: "POST",
    headers: {
      // Don't set Content-Type; browser will add multipart boundary.
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      Accept: "application/json",
    },
    body: form,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err = new Error(text || `Failed to upload PDF (${res.status})`) as any;
    err.status = res.status;
    throw err;
  }
  return res.json();
}


// export async function submitPdfAPI(
//   token: string,
//   jobId: string,
//   file: File
// ): Promise<SubmitPdfResponse> {
//   const form = new FormData();
//   form.append("file", file, file.name); // backend field name "file"

//   const res = await fetch(`${BASE}/jobs/${encodeURIComponent(jobId)}/pdf`, {
//     method: "POST",
//     headers: {
//       // DON'T set Content-Type for FormData. Browser will set boundary.
//       ...(token ? { Authorization: `Bearer ${token}` } : {}),
//     },
//     body: form,
//   });

//   if (!res.ok) {
//     const text = await res.text().catch(() => "");
//     const err = new Error(text || `Failed to upload PDF (${res.status})`) as any;
//     err.status = res.status;
//     throw err;
//   }
//   return res.json();
// }