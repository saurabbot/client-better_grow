from typing import Dict, Any
import json
from twilio.rest import Client
from src.core.logging import LoggerAdapter

class TwillioService:
    def __init__(self, account_sid: str, auth_token: str, logger: LoggerAdapter = None):
        self.client = Client(account_sid, auth_token)
        self.logger = logger

    def send_message(self, message: str, to: str):
        try:
            # Ensure both numbers have whatsapp: prefix for WhatsApp messages
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'
            from_number = 'whatsapp:+14155238886'  # Twilio WhatsApp Sandbox number

            response = self.client.messages.create(
                to=to,
                from_=from_number,
                body=message
            )
            if self.logger:
                self.logger.info("message_sent", message_id=response.sid, to=to)
            return response
        except Exception as e:
            if self.logger:
                self.logger.error("failed_to_send_message", error=str(e), to=to)
            raise
        
        