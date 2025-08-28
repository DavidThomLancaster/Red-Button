# TODO - Slice 8 - Define the DTOs for the email stuff
# api/schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime

EmailStatusL = Literal["draft","ready","mock_sent","failed"]

class EmailHeaderDTO(BaseModel):
    id: str
    batch_id: str
    job_id: str
    contact_id: str
    contact_name: str
    contact_email: EmailStr
    trade: Optional[str] = None
    subject: str
    status: EmailStatusL
    last_updated: datetime
    model_config = ConfigDict(from_attributes=True)

class EmailBatchDTO(BaseModel):
    id: str
    job_id: str
    template_version: str
    created_at: datetime
    page_spec: Optional[str] = None
    page_count: Optional[int] = None
    count_total: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class BatchWithHeadersDTO(BaseModel):
    batch: EmailBatchDTO
    emails: List[EmailHeaderDTO]

class JobEmailBatchesDTO(BaseModel):
    job_id: str
    batches: List[BatchWithHeadersDTO]
