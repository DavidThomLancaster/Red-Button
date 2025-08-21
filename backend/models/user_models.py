from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, List, Literal


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class CreateJobRequest(BaseModel):
    name: str
    notes: Optional[str] = None
 
# class GetJobsRequest(BaseModel):
#     # 
#     pass

# ----------------
class PatchOp(BaseModel):
    op: Literal["add_contact", "remove_contact"]
    trade: str
    block: int
    contact_id: str

class PatchOpsReq(BaseModel):
    base_ref: str
    ops: List[PatchOp]
# ----------------

class EvidenceBlock(BaseModel):
    note: str = ""
    pages: List[str] = Field(default_factory=list)
    contacts: List[str] = Field(default_factory=list)
    original_name: Optional[str] = None

ContactsMap = Dict[str, List[EvidenceBlock]]

class JobMeta(BaseModel):
    processing_steps: List[str] = Field(default_factory=list)
    job: Dict[str, str] = Field(default_factory=dict)

class ContactSummary(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    service_area: Optional[str] = None

class GetMapResp(BaseModel):
    status: Literal["OK"]
    job_id: str
    ref: str
    map: ContactsMap
    contactsById: Dict[str, ContactSummary]
    metadata: Optional[JobMeta] = None


# class EvidenceBlock(BaseModel):
#     note: str
#     pages: List[str] = Field(default_factory=list)
#     contacts: List[str] = Field(default_factory=list)   # IDs only

# ContactsMap = Dict[str, List[EvidenceBlock]]

# class ContactSummary(BaseModel):
#     id: str
#     name: str
#     email: Optional[str] = None
#     company: Optional[str] = None
#     trade: Optional[str] = None
#     tags: Optional[List[str]] = None

# class GetMapResp(BaseModel):
#     status: str = "OK"
#     job_id: str
#     ref: str
#     map: ContactsMap
#     contactsById: Dict[str, ContactSummary]
#     metadata: Optional[dict] = None

# class GetMapResp(BaseModel):
#     status: str = "OK"
#     job_id: str
#     ref: str
#     map: ContactsMap
#     contactsById: Dict[str, ContactSummary]


