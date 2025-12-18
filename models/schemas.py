from pydantic import BaseModel
from typing import Dict, Any

class Command(BaseModel):
    action: str
    payload: Dict[str, Any]
