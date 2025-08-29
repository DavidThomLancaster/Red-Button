import type { JobEmailBatchesDTO } from "../types"; // is it types?
import { apiFetch } from "./client";    

//const BASE = import.meta.env.VITE_API_BASE ?? "";
const BASE = import.meta.env.VITE_API_BASE;

export const getEmailBatchesApi = (token: string, jobId: string) => 
    apiFetch<JobEmailBatchesDTO>(`/jobs/${encodeURIComponent(jobId)}/email_batches`, {
    }, token);
// export async function getEmailBatchesApi(token: string, jobId: string): Promise<JobEmailBatchesDTO> {
//   const res = await fetch(`${BASE}/jobs/${jobId}/email_batches`, {
//     method: "GET",
//     headers: {
//       Authorization: token,                      // "Bearer …"
//       Accept: "application/json",
//     },
//   });
//   if (!res.ok) {
//     const text = await res.text().catch(() => "");
//     throw Object.assign(new Error(`Failed to load email batches (${res.status})`), {
//       status: res.status,
//       body: text,
//     });
//   }
//   return res.json();
// }
