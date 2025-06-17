from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class WebhookRequest(BaseModel):
    object: str = Field(..., description="Object type")
    entry: List[Dict[str, Any]] = Field(..., description="List of entries")
    messaging: Optional[List[Dict[str, Any]]] = Field(None, description="List of messaging events") 