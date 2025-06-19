import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from src.models.session import (
    Session, SessionCreate, SessionUpdate, SessionStatus,
    Message, MessageType, MessageDirection
)
from src.core.logging import LoggerAdapter
import structlog

class SessionService:
    
    def __init__(self, logger: LoggerAdapter = None):
        self.logger = logger or structlog.get_logger(__name__)
        self._sessions: Dict[str, Session] = {}
        self._phone_to_session: Dict[str, str] = {}  # phone_number -> session_id mapping
        self.session_timeout_hours = 24  # Sessions expire after 24 hours of inactivity
    
    def create_session(self, session_data: SessionCreate) -> Session:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        messages = []
        if session_data.initial_message:
            initial_message = Message(
                id=str(uuid.uuid4()),
                content=session_data.initial_message,
                message_type=MessageType.TEXT,
                direction=MessageDirection.INBOUND,
                timestamp=now
            )
            messages.append(initial_message)
        
        session = Session(
            session_id=session_id,
            phone_number=session_data.phone_number,
            status=SessionStatus.ACTIVE,
            created_at=now,
            last_activity=now,
            messages=messages,
            context=session_data.context or {}
        )
        
        self._sessions[session_id] = session
        self._phone_to_session[session_data.phone_number] = session_id
        
        self.logger.info(
            "session_created",
            session_id=session_id,
            phone_number=session_data.phone_number
        )
        
        return session
    
    def get_session_by_phone(self, phone_number: str) -> Optional[Session]:
        session_id = self._phone_to_session.get(phone_number)
        if not session_id:
            return None
        session = self._sessions.get(session_id)
        if not session or session.status != SessionStatus.ACTIVE:
            self._cleanup_session(session_id)
            return None
            
        # Check if session has expired
        if self._is_session_expired(session):
            self.expire_session(session_id)
            return None
            
        return session
    
    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by session ID."""
        session = self._sessions.get(session_id)
        if not session:
            return None
            
        # Check if session has expired
        if self._is_session_expired(session):
            self.expire_session(session_id)
            return None
            
        return session
    
    def add_message(self, phone_number: str, content: str, message_type: MessageType = MessageType.TEXT, 
                   direction: MessageDirection = MessageDirection.INBOUND, metadata: Dict[str, Any] = None) -> Session:
        """Add a message to an existing session or create a new one."""
        session = self.get_session_by_phone(phone_number)
        
        if not session:
            # Create new session
            session_data = SessionCreate(
                phone_number=phone_number,
                initial_message=content if direction == MessageDirection.INBOUND else None
            )
            session = self.create_session(session_data)
            
            # If this is an outbound message, add it to the new session
            if direction == MessageDirection.OUTBOUND:
                self._add_message_to_session(session, content, message_type, direction, metadata)
        else:
            # Add message to existing session
            self._add_message_to_session(session, content, message_type, direction, metadata)
        
        return session
    
    def _add_message_to_session(self, session: Session, content: str, message_type: MessageType,
                               direction: MessageDirection, metadata: Dict[str, Any] = None):
        """Add a message to an existing session."""
        message = Message(
            id=str(uuid.uuid4()),
            content=content,
            message_type=message_type,
            direction=direction,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        session.last_activity = datetime.utcnow()
        
        self.logger.info(
            "message_added_to_session",
            session_id=session.session_id,
            phone_number=session.phone_number,
            message_type=message_type.value,
            direction=direction.value
        )
    
    def update_session(self, session_id: str, updates: SessionUpdate) -> Optional[Session]:
        """Update session data."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        if updates.status:
            session.status = updates.status
        if updates.context:
            session.context.update(updates.context)
        if updates.order_details:
            session.order_details = updates.order_details
            
        session.last_activity = datetime.utcnow()
        
        self.logger.info(
            "session_updated",
            session_id=session_id,
            updates=updates.dict(exclude_none=True)
        )
        
        return session
    
    def complete_session(self, session_id: str) -> bool:
        """Mark a session as completed."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.status = SessionStatus.COMPLETED
        session.last_activity = datetime.utcnow()
        
        self.logger.info("session_completed", session_id=session_id)
        return True
    
    def expire_session(self, session_id: str) -> bool:
        """Mark a session as expired."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.status = SessionStatus.EXPIRED
        session.last_activity = datetime.utcnow()
        
        self.logger.info("session_expired", session_id=session_id)
        return True
    
    def _is_session_expired(self, session: Session) -> bool:
        """Check if a session has expired due to inactivity."""
        if session.status != SessionStatus.ACTIVE:
            return False
            
        timeout_delta = timedelta(hours=self.session_timeout_hours)
        return datetime.utcnow() - session.last_activity > timeout_delta
    
    def _cleanup_session(self, session_id: str):
        """Clean up expired session data."""
        session = self._sessions.get(session_id)
        if session:
            # Remove phone number mapping
            if session.phone_number in self._phone_to_session:
                del self._phone_to_session[session.phone_number]
            
            # Remove session
            del self._sessions[session_id]
    
    def get_conversation_history(self, phone_number: str, limit: int = 50) -> List[Message]:
        """Get conversation history for a phone number."""
        session = self.get_session_by_phone(phone_number)
        if not session:
            return []
        
        # Return last N messages
        return session.messages[-limit:] if len(session.messages) > limit else session.messages
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of session data."""
        session = self.get_session_by_id(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "phone_number": session.phone_number,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": len(session.messages),
            "order_details": session.order_details,
            "context": session.context
        }
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions and return count of cleaned sessions."""
        expired_sessions = []
        
        for session_id, session in self._sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self._cleanup_session(session_id)
        
        if expired_sessions:
            self.logger.info("expired_sessions_cleaned", count=len(expired_sessions))
        
        return len(expired_sessions)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        return len([s for s in self._sessions.values() if s.status == SessionStatus.ACTIVE])
    
    def get_all_sessions(self) -> List[Session]:
        """Get all sessions (for debugging/admin purposes)."""
        return list(self._sessions.values()) 