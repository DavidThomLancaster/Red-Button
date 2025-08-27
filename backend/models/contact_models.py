from pydantic import BaseModel, Field
from typing import Optional, List

class ContactSearchRequest(BaseModel):
    trade: Optional[str] = None
    name: Optional[str] = None
    service_area: Optional[str] = None
    limit: int = Field(default=25, gt=0, le=200)
    page: int = Field(default=1, gt=0)

class ContactOut(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    service_area: Optional[str] = None

class ContactSearchResponse(BaseModel):
    items: List[ContactOut]
    limit: int
    page: int
    count: int  # number of items in this page (or total if you later add count_total)

class CreateContactBody(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    service_area: Optional[str] = None
    trades: Optional[List[str]] = None
    id: Optional[str] = None  # optional; generated if not provided