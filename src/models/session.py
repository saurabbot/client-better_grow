from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    PDF = "pdf"
    SYSTEM = "system"

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class Message(BaseModel):
    """Represents a single message in a conversation."""
    id: str = Field(..., description="Unique message ID")
    content: str = Field(..., description="Message content")
    message_type: MessageType = Field(..., description="Type of message")
    direction: MessageDirection = Field(..., description="Message direction")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional message metadata")

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"

class Session(BaseModel):
    """Represents a WhatsApp conversation session."""
    session_id: str = Field(..., description="Unique session identifier")
    phone_number: str = Field(..., description="Customer's phone number")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Current session status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation timestamp")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    messages: List[Message] = Field(default_factory=list, description="Conversation messages")
    context: Dict[str, Any] = Field(default_factory=dict, description="Session context data")
    order_details: Optional[Dict[str, Any]] = Field(default=None, description="Extracted order details")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SessionCreate(BaseModel):
    """Model for creating a new session."""
    phone_number: str
    initial_message: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class SessionUpdate(BaseModel):
    """Model for updating session data."""
    status: Optional[SessionStatus] = None
    context: Optional[Dict[str, Any]] = None
    order_details: Optional[Dict[str, Any]] = None 