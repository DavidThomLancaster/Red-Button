// api/contactsMap.ts
import { apiFetch } from "./client";

export type EvidenceBlock = { note: string; pages: string[]; contacts: string[] };
export type ContactsMap = Record<string, EvidenceBlock[]>;
export type ContactSummary = { id: string; name: string; email?: string; company?: string; trade?: string; tags?: string[] };

export const getContactsMapApi = (token: string, jobId: string) =>
  apiFetch<{ status: string; job_id: string; ref: string; map: ContactsMap; contactsById: Record<string, ContactSummary> }>(
    `/jobs/${encodeURIComponent(jobId)}/contacts-map`, {}, token
  );

export const putContactsMapApi = (token: string, jobId: string, base_ref: string, map: ContactsMap) =>
  apiFetch<{ status: string; ref: string }>(
    `/jobs/${encodeURIComponent(jobId)}/contacts-map`,
    { method: "PUT", body: JSON.stringify({ base_ref, map }) },
    token
  );

export const patchContactsMapOpsApi = (
  token: string,
  jobId: string,
  base_ref: string,
  ops: Array<{ op: "add_contact" | "remove_contact"; trade: string; block: number; contact_id: string }>
) =>
  apiFetch<{ status: string; ref: string; map: ContactsMap; contactsById: Record<string, ContactSummary> }>(
    `/jobs/${encodeURIComponent(jobId)}/contacts-map`,
    { method: "PATCH", body: JSON.stringify({ base_ref, ops }) },
    token
  );
