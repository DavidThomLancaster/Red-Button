from dataclasses import dataclass

@dataclass
class ParamsDTO:
    trade: str
    name: str
    service_area: str
    limit: int
    page: int
