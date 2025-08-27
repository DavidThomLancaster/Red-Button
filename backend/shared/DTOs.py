from dataclasses import dataclass
from typing import Optional, List

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