export type Job = {
  job_id: string;
  name: string;
  // status?: string;
  // created_at?: string;

  // ⬇ add these optionals if they aren't there yet
  notes?: string | null;
  status?: string | null;
  created_at?: string | null;
  pdf_ref?: StorageRef | null;
  images_ref?: StorageRef | null;
  prompt_ref?: StorageRef | null;
  contact_map_ref?: StorageRef | null;
};


export interface StorageRef { mode: "local" | "s3"; location: string }

export interface ContactMapTradePreview {
  trade: string;
  pages: number[];
  notes?: string;
  suggested_contact_id?: string | null;
  confidence?: number;
}

export interface ContactMapPreview {
  generated_at: string;
  trades: ContactMapTradePreview[];
}

export interface GetJobResponse {
  job: Job;
  contact_map_preview?: ContactMapPreview | null;
}

export interface SubmitPdfResponse {
  status?: string;
  pdf_ref?: { mode: "local" | "s3"; location: string } | null;
  images_ref?: { mode: "local" | "s3"; location: string } | null;
  contact_map_ref?: { mode: "local" | "s3"; location: string } | null;

  // If your backend returns a preview immediately:
  preliminary_contact_map?: ContactMapPreview | null;

  // Or if you decide to return it directly under a different name:
  contact_map_preview?: ContactMapPreview | null;
}

// export interface SubmitPdfResponse {
//   pdf_ref?: StorageRef | null;
//   images_ref?: StorageRef | null;
//   contact_map_ref?: StorageRef | null;
//   preliminary_contact_map?: ContactMapPreview | null;
//   status?: string;
// }

//--------------------------------
// --- emails DTOs from your GET /jobs/{jobId}/email_batches ---
export type EmailStatus = "draft" | "ready" | "mock_sent" | "failed";

export interface EmailHeaderDTO {
  id: string;
  batch_id: string;
  job_id: string;
  contact_id: string;
  contact_name: string;
  contact_email: string;
  trade?: string | null;
  subject: string;
  status: EmailStatus;
  last_updated: string; // ISO
}

export interface EmailBatchDTO {
  id: string;
  job_id: string;
  template_version: string;
  created_at: string;    // ISO
  page_spec?: string | null;
  page_count?: number | null;
  count_total?: number | null;
}

export interface BatchWithHeadersDTO {
  batch: EmailBatchDTO;
  emails: EmailHeaderDTO[];
}

export interface JobEmailBatchesDTO {
  job_id: string;
  batches: BatchWithHeadersDTO[];
}

