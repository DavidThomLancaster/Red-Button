# services/prompt_service.py
from typing import List, Dict, Optional
from Repositories.PromptRepository import PromptRepository
from shared.StorageRef import StorageRef, StorageMode

class PromptService:

    

    def __init__(self, prompt_repo: PromptRepository):
        self.prompt_repo = prompt_repo
        self.temp_reference_string = "HARDCODED IN PROMPT SERVICE"
        self.temp_prompt = """You are an expert at interpreting construction plan documents.

Your job is to review attached construction plan images and extract all relevant subcontractor trades involved.

Return ONLY a CSV with exactly 3 quoted fields per row:
"Trade Name","Pages Referenced","Details / Notes"

Each field must be wrapped in double quotes, even if it doesn’t contain commas.

Example:

"Trade Name","Pages Referenced","Details / Notes"
"Plumbing","12","Install fixtures and piping for restrooms"
"Electrical","8,22-24","Power and lighting for facility, coordinate with HVAC"
"Surveying","5","Benchmark layout and control points"
"Mechanical","60","Implied from pump station and control panel"

Now extract the trades from the following image(s):
"""

    def get_active_prompt(self) -> Optional[Dict]:
        return self.temp_prompt, StorageRef(location="HARDCODED IN PROMPT SERVICE", mode=StorageMode.LOCAL)
        return self.prompt_repo.get_active_prompt()

    def list_prompts(self) -> List[Dict]:
        return self.prompt_repo.list_prompts()

    def create_prompt(self, name: str, content: str, set_active: bool = False) -> str:
        prompt_id = self.prompt_repo.create_prompt(name, content)
        if set_active:
            self.prompt_repo.set_active_prompt(prompt_id)
        return prompt_id

    def update_prompt(self, prompt_id: str, new_content: str) -> str:
        old = self.prompt_repo.get_prompt_by_id(prompt_id)
        if not old:
            raise ValueError("Prompt not found")

        new_version = old["version"] + 1
        new_id = self.prompt_repo.create_prompt(
            name=old["name"],
            content=new_content,
            version=new_version,
            is_active=True
        )
        self.prompt_repo.set_active_prompt(new_id)
        return new_id
