# TODO...
from Repositories.ContactRepository import ContactRepository
from typing import Dict, List
import json
from shared.ParamsDTO import ParamsDTO

class ContactService:
    def __init__(self, contact_repository: ContactRepository):
        self.contact_repo = contact_repository

    
    def get_contact_ids_for_trade(self, trade_canonical: str, limit: int | None = None) -> List[str]:
        """
        Return a list of contact IDs that match a canonical trade name.
        Keep it simple (exact match on canonical name). Add fuzzy later if needed.
        """
        return self.contact_repo.find_contact_ids_by_trade(trade_canonical, limit=limit)
    
    # TODO Slice 7 - function to get contacts by parameters
    def get_contacts_by_parameters(self, params_dto: ParamsDTO) -> List[dict]: 
        items = self.contact_repo.find_contacts_by_parameters(params_dto)
        return {
            "items": items,
            "limit": params_dto.limit,
            "page": params_dto.page,
            "count": len(items),
        }

