# WhatsApp Session Service

A comprehensive session management service for tracking WhatsApp conversations in the Shipra Backend system.

## Overview

The Session Service provides conversation tracking, context management, and session lifecycle management for WhatsApp interactions. It automatically creates sessions for new conversations, tracks message history, and maintains conversation context for better customer service.

## Features

### 🎯 Core Features
- **Automatic Session Creation**: Creates sessions for new phone numbers
- **Message Tracking**: Tracks all inbound and outbound messages
- **Conversation History**: Maintains complete conversation history
- **Session Lifecycle**: Manages session states (active, completed, expired)
- **Context Management**: Stores conversation context and order details
- **Auto-expiration**: Automatically expires sessions after 24 hours of inactivity

### 📱 Message Types Supported
- **Text Messages**: Standard text conversations
- **Image Messages**: Image-based orders and queries
- **System Messages**: Error messages and notifications

### 🔄 Session States
- **ACTIVE**: Ongoing conversation
- **COMPLETED**: Finished conversation
- **EXPIRED**: Timed out due to inactivity

## Architecture

### Models

#### Session Model
```python
class Session(BaseModel):
    session_id: str                    # Unique session identifier
    phone_number: str                  # Customer's phone number
    status: SessionStatus              # Current session status
    created_at: datetime               # Session creation timestamp
    last_activity: datetime            # Last activity timestamp
    messages: List[Message]            # Conversation messages
    context: Dict[str, Any]            # Session context data
    order_details: Optional[Dict]      # Extracted order details
```

#### Message Model
```python
class Message(BaseModel):
    id: str                           # Unique message ID
    content: str                      # Message content
    message_type: MessageType         # Type of message (text/image/system)
    direction: MessageDirection       # Message direction (inbound/outbound)
    timestamp: datetime               # Message timestamp
    metadata: Dict[str, Any]          # Additional metadata
```

### Service Methods

#### Core Session Management
- `create_session(session_data)`: Create a new conversation session
- `get_session_by_phone(phone_number)`: Get active session by phone number
- `get_session_by_id(session_id)`: Get session by session ID
- `update_session(session_id, updates)`: Update session data
- `complete_session(session_id)`: Mark session as completed
- `expire_session(session_id)`: Mark session as expired

#### Message Management
- `add_message(phone_number, content, ...)`: Add message to session
- `get_conversation_history(phone_number, limit)`: Get conversation history
- `get_session_summary(session_id)`: Get session summary

#### Utility Methods
- `cleanup_expired_sessions()`: Clean up expired sessions
- `get_active_sessions_count()`: Get count of active sessions
- `get_all_sessions()`: Get all sessions (admin)

## API Endpoints

### Webhook Integration
The session service is automatically integrated into the WhatsApp webhook:

**POST** `/twilio-webhook-opt`
- Automatically creates/updates sessions for incoming messages
- Tracks both inbound and outbound messages
- Updates session with extracted order details

### Session Management Endpoints

**GET** `/session/{phone_number}`
```json
{
  "session": {
    "session_id": "uuid",
    "phone_number": "+1234567890",
    "status": "active",
    "created_at": "2024-01-01T10:00:00Z",
    "last_activity": "2024-01-01T10:30:00Z",
    "message_count": 6,
    "order_details": {...},
    "context": {...}
  },
  "conversation_history": [...],
  "message_count": 6
}
```

**GET** `/sessions/active`
```json
{
  "active_sessions": [...],
  "total_active": 5
}
```

**POST** `/session/{session_id}/complete`
```json
{
  "message": "Session completed successfully"
}
```

## Usage Examples

### Basic Session Creation
```python
from src.services.session_service import SessionService
from src.models.session import SessionCreate

session_service = SessionService()

# Create a new session
session_data = SessionCreate(
    phone_number="+1234567890",
    initial_message="Hi, I want to place an order",
    context={"customer_type": "new"}
)

session = session_service.create_session(session_data)
```

### Adding Messages
```python
# Add inbound message
session = session_service.add_message(
    phone_number="+1234567890",
    content="I need 5 units of Product A",
    message_type=MessageType.TEXT,
    direction=MessageDirection.INBOUND
)

# Add outbound response
session = session_service.add_message(
    phone_number="+1234567890",
    content="✅ Order received!",
    message_type=MessageType.TEXT,
    direction=MessageDirection.OUTBOUND
)
```

### Getting Conversation History
```python
history = session_service.get_conversation_history("+1234567890", limit=10)
for message in history:
    print(f"{message.direction}: {message.content}")
```

### Updating Session with Order Details
```python
from src.models.session import SessionUpdate

order_details = {
    "customer_name": "John Doe",
    "items": [{"name": "Product A", "quantity": 5}],
    "total_amount": 129.95
}

session_service.update_session(
    session.session_id,
    SessionUpdate(order_details=order_details)
)
```

## Integration with WhatsApp Webhook

The session service is automatically integrated into the WhatsApp webhook processing:

1. **Incoming Message**: Automatically creates or retrieves session
2. **Message Processing**: Adds inbound message to session
3. **Order Extraction**: Updates session with extracted order details
4. **Response**: Adds outbound response to session
5. **Error Handling**: Tracks error messages in session

### Example Webhook Flow
```
Customer sends: "I need 5 units of Product A"
↓
Session created/retrieved for phone number
↓
Inbound message added to session
↓
Order details extracted by OpenAI
↓
Session updated with order details
↓
Response sent: "✅ Order received: 5 units of Product A"
↓
Outbound message added to session
```

## Configuration

### Session Timeout
Sessions automatically expire after 24 hours of inactivity:
```python
session_service.session_timeout_hours = 24  # Configurable
```

### Cleanup
Expired sessions are automatically cleaned up:
```python
cleaned_count = session_service.cleanup_expired_sessions()
```

## Testing

Run the test script to see the session service in action:

```bash
python test_session_service.py
```

This will demonstrate:
- Session creation and management
- Message tracking
- Conversation history
- Session updates and completion
- Multiple phone number handling

## Benefits

### For Customer Service
- **Complete Conversation History**: See full context of customer interactions
- **Order Tracking**: Track order details throughout conversation
- **Context Awareness**: Maintain conversation context across messages
- **Error Tracking**: Track and analyze error patterns

### For Analytics
- **Session Metrics**: Track session duration, message counts
- **Customer Behavior**: Analyze conversation patterns
- **Order Processing**: Track order completion rates
- **Performance Monitoring**: Monitor response times and success rates

### For Development
- **Debugging**: Complete conversation logs for troubleshooting
- **Testing**: Easy to test conversation flows
- **Monitoring**: Track system performance and usage

## Future Enhancements

- **Database Persistence**: Store sessions in database for persistence
- **Redis Integration**: Use Redis for better performance
- **Analytics Dashboard**: Web interface for session management
- **Advanced Context**: AI-powered conversation context analysis
- **Multi-language Support**: Support for multiple languages
- **Session Templates**: Predefined conversation templates 