from dataclasses import dataclass
from typing import Optional, List, Literal
from enum import Enum
from datetime import datetime

@dataclass
class ParamsDTO:
    user_id: str
    trade: str
    name: str
    service_area: str
    limit: int
    page: int

@dataclass(frozen=True)
class ContactDTO:
    user_id: str                      # owner of this personal contact
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    service_area: Optional[str] = None
    trades: Optional[List[str]] = None
    id: Optional[str] = None          # optional; generated if not provided

class EmailStatus(str, Enum):
    draft = "draft"
    ready = "ready"
    mock_sent = "mock_sent"
    failed = "failed"

@dataclass(frozen=True)
class EmailBatchRecord:
    id: str
    job_id: str
    template_version: str
    created_at: datetime
    page_spec: Optional[str] = None
    page_count: Optional[int] = None

@dataclass(frozen=True)
class EmailHeaderRecord:
    id: str
    batch_id: str
    job_id: str
    contact_id: str
    contact_name: str
    contact_email: str
    trade: Optional[str]
    subject: str
    status: EmailStatus
    last_updated: datetime

@dataclass(frozen=True)
class BatchWithEmailHeaders:   # domain aggregate
    batch: EmailBatchRecord
    emails: List[EmailHeaderRecord]

@dataclass(frozen=True)
class EmailDetailsRecord:
    id: str
    batch_id: str
    job_id: str
    contact_id: str
    to_email: str
    body: str
    subject: str
    status: str
    attempts: int
    sent_at: Optional[datetime] = None
    last_error: Optional[str] = None

