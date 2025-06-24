from fastapi import APIRouter, Depends, Form, HTTPException
from src.core.container import Container
from src.models.webhook import WebhookRequest
from src.models.session import MessageType, MessageDirection, SessionUpdate
from src.core.exceptions import BaseAppException
from src.services.openai_service import OpenAIService
from src.services.frappe_service import FrappeService
from src.services.twillio_service import TwillioService
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)

def get_container() -> Container:
    return Container()

@router.post("/webhook")
async def webhook(
    request: WebhookRequest,
    container: Container = Depends(get_container)
):
    try:
        logger = container.logger.bind(endpoint="webhook")
        logger.info("webhook_received", request=request.dict())
        
        if not request.entry:
            raise HTTPException(status_code=400, detail="No entries found in webhook request")
            
        for entry in request.entry:
            if not entry.get("messaging"):
                continue
                
            for message in entry["messaging"]:
                if not message.get("message", {}).get("text"):
                    continue
                    
                text = message["message"]["text"]
                logger.info("processing_message", text=text)
                
                order_details = await container.openai_service.extract_order_details(text)
                if not order_details:
                    logger.warning("no_order_details_found", text=text)
                    continue
                    
                logger.info("order_details_extracted", details=order_details.dict())
                
        return {"status": "success"}
        
    except BaseAppException as e:
        logger.error("application_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") 

@router.post("/twilio-webhook-opt")
async def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None),
    MediaUrl1: str = Form(None),  # Optional, can add more if needed
    MediaContentType1: str = Form(None),
    container=Depends(get_container)
):
    log = container.logger.bind(endpoint="twilio_webhook", sender=From)
    
    try:
        text_message = Body.strip() if Body else None
        image_url = None
        audio_url = None
        pdf_url = None

        if NumMedia > 0 and MediaContentType0:
            if MediaContentType0.startswith("image/"):
                image_url = MediaUrl0
            elif MediaContentType0.startswith("audio/"):
                audio_url = MediaUrl0
            elif MediaContentType0 == "application/pdf":
                pdf_url = MediaUrl0

        # TEXT HANDLING
        if text_message:
            try:
                # Add inbound message to session
                session = container.session_service.add_message(
                    phone_number=From,
                    content=text_message,
                    message_type=MessageType.TEXT,
                    direction=MessageDirection.INBOUND
                )
                
                # Extract order details
                order_json = await container.openai_service.extract_order_details(text_message)
                print(order_json, 'BEeep')
                
                
                # Update session with order details
                # if order_json:
                #     container.session_service.update_session(
                #         session.session_id,
                #         SessionUpdate(order_details=order_json)
                #     )
                
                # Prepare confirmation message
                confirmation_message = f"✅ Order received:\n{order_json}"
                
                # Send response
                container.twillio_service.send_message(confirmation_message, to=From)
                
                # # Add outbound message to session
                # container.session_service.add_message(
                #     phone_number=From,
                #     content=confirmation_message,
                #     message_type=MessageType.TEXT,
                #     direction=MessageDirection.OUTBOUND
                # )
                
                # log.info("order_processed_from_text", 
                #         session_id=session.session_id,
                #         order=order_json)
                        
            except Exception as e:
                log.error("failed_to_process_text_order", error=str(e))
                error_message = "⚠️ There was an error processing your order. Please try again later."
                container.twillio_service.send_message(error_message, to=From)
                
                # Add error message to session
                container.session_service.add_message(
                    phone_number=From,
                    content=error_message,
                    message_type=MessageType.TEXT,
                    direction=MessageDirection.OUTBOUND,
                    metadata={"error": str(e)}
                )
                raise

        # IMAGE HANDLING
        elif image_url:
            try:
                # Add inbound image message to session
                session = container.session_service.add_message(
                    phone_number=From,
                    content=f"Image: {image_url}",
                    message_type=MessageType.IMAGE,
                    direction=MessageDirection.INBOUND,
                    metadata={"image_url": image_url, "content_type": MediaContentType0}
                )
                
                order_details = await container.openai_service.extract_order_from_image(image_url)
                if order_details:
                    # Update session with order details
                    # container.session_service.update_session(
                    #     session.session_id,
                    #     SessionUpdate(order_details=order_details)
                    # )
                    
                    confirmation_message = f"✅ Order received: {order_details}"
                    container.twillio_service.send_message(confirmation_message, to=From)
                    
                    # Add outbound message to session
                    # container.session_service.add_message(
                    #     phone_number=From,
                    #     content=confirmation_message,
                    #     message_type=MessageType.TEXT,
                    #     direction=MessageDirection.OUTBOUND
                    # )
                    
                    log.info("order_processed_from_image", 
                            session_id=session.session_id,
                            order=order_details)
                else:
                    no_order_message = "I couldn't detect any order details in the image. Please send your order as text."
                    container.twillio_service.send_message(no_order_message, to=From)
                    
                    # Add outbound message to session
                    container.session_service.add_message(
                        phone_number=From,
                        content=no_order_message,
                        message_type=MessageType.TEXT,
                        direction=MessageDirection.OUTBOUND
                    )
            
                    
            except Exception as e:
                log.error("failed_to_process_image_order", error=str(e))
                error_message = "⚠️ Sorry, we couldn't process the image. Please try again with a clearer photo or send it as text."
                container.twillio_service.send_message(error_message, to=From)
                
                container.session_service.add_message(
                    phone_number=From,
                    content=error_message,
                    message_type=MessageType.TEXT,
                    direction=MessageDirection.OUTBOUND,
                    metadata={"error": str(e)}
                )

        elif audio_url:
            try:
                # Add inbound audio message to session
                # session = container.session_service.add_message(
                #     phone_number=From,
                #     content=f"Audio: {audio_url}",
                #     message_type=MessageType.AUDIO,
                #     direction=MessageDirection.INBOUND,
                #     metadata={"audio_url": audio_url, "content_type": MediaContentType0}
                # )
                
                # Extract order details from audio
                order_details = await container.openai_service.extract_order_from_audio(audio_url)
                
                if order_details:
                    # Update session with order details
                    # container.session_service.update_session(
                    #     session.session_id,
                    #     SessionUpdate(order_details=order_details)
                    # )
                    
                    confirmation_message = f"✅ Order received: {order_details}"
                    container.twillio_service.send_message(confirmation_message, to=From)
                    
                    # # Add outbound message to session
                    # container.session_service.add_message(
                    #     phone_number=From,
                    #     content=confirmation_message,
                    #     message_type=MessageType.TEXT,
                    #     direction=MessageDirection.OUTBOUND
                    # )
                    
                    # log.info("order_processed_from_audio", 
                    #         session_id=session.session_id,
                    #         order=order_details)
                else:
                    no_order_message = "I couldn't detect any order details in the audio. Please send your order as text or try speaking more clearly."
                    container.twillio_service.send_message(no_order_message, to=From)
                    
                    # Add outbound message to session
                    container.session_service.add_message(
                        phone_number=From,
                        content=no_order_message,
                        message_type=MessageType.TEXT,
                        direction=MessageDirection.OUTBOUND
                    )
                    
            except Exception as e:
                log.error("failed_to_process_audio_order", error=str(e))
                error_message = "⚠️ Sorry, we couldn't process the audio. Please try again with clearer speech or send your order as text."
                container.twillio_service.send_message(error_message, to=From)
                
                # Add error message to session
                container.session_service.add_message(
                    phone_number=From,
                    content=error_message,
                    message_type=MessageType.TEXT,
                    direction=MessageDirection.OUTBOUND,
                    metadata={"error": str(e)}
                )

        # PDF HANDLING
        elif pdf_url:
            try:
                # Add inbound PDF message to session
                session = container.session_service.add_message(
                    phone_number=From,
                    content=f"PDF: {pdf_url}",
                    message_type=MessageType.PDF,
                    direction=MessageDirection.INBOUND,
                    metadata={"pdf_url": pdf_url, "content_type": MediaContentType0}
                )
                
                # Extract order details from PDF
                order_details = await container.openai_service.extract_order_from_pdf(pdf_url)
                confirmation_message = f"✅ Order received: {order_details}"
                container.twillio_service.send_message(confirmation_message, to=From)
                
                # if order_details and isinstance(order_details, dict) and order_details.get("status"):
                #     # PDF was processed but had issues (no text, no order found, etc.)
                #     no_order_message = order_details.get("message", "I couldn't detect any order details in the PDF. Please send your order as text or ensure the PDF contains clear order information.")
                #     container.twillio_service.send_message(no_order_message, to=From)
                    
                #     # Add outbound message to session
                #     container.session_service.add_message(
                #         phone_number=From,
                #         content=no_order_message,
                #         message_type=MessageType.TEXT,
                #         direction=MessageDirection.OUTBOUND
                #     )
                    
                #     log.info("pdf_processed_with_issues", 
                #             session_id=session.session_id,
                #             status=order_details.get("status"))
                # elif order_details:
                #     # Successfully extracted order details
                #     # Update session with order details
                #     container.session_service.update_session(
                #         session.session_id,
                #         SessionUpdate(order_details=order_details)
                #     )
                    
                #     confirmation_message = f"📄 Order from PDF: {order_details}"
                #     container.twillio_service.send_message(confirmation_message, to=From)
                    
                #     # Add outbound message to session
                #     container.session_service.add_message(
                #         phone_number=From,
                #         content=confirmation_message,
                #         message_type=MessageType.TEXT,
                #         direction=MessageDirection.OUTBOUND
                #     )
                    
                #     log.info("order_processed_from_pdf", 
                #             session_id=session.session_id,
                #             order=order_details)
                # else:
                #     # No order details found
                #     no_order_message = "I couldn't detect any order details in the PDF. Please send your order as text or ensure the PDF contains clear order information."
                #     container.twillio_service.send_message(no_order_message, to=From)
                    
                #     # Add outbound message to session
                #     container.session_service.add_message(
                #         phone_number=From,
                #         content=no_order_message,
                #         message_type=MessageType.TEXT,
                #         direction=MessageDirection.OUTBOUND
                #     )
                    
            except Exception as e:
                log.error("failed_to_process_pdf_order", error=str(e))
                error_message = "⚠️ Sorry, we couldn't process the PDF. Please try again with a different file or send your order as text."
                container.twillio_service.send_message(error_message, to=From)
                
                # Add error message to session
                container.session_service.add_message(
                    phone_number=From,
                    content=error_message,
                    message_type=MessageType.TEXT,
                    direction=MessageDirection.OUTBOUND,
                    metadata={"error": str(e)}
                )
        else:
            
            help_message = "Please send your order as text, image, audio, or PDF."
            container.twillio_service.send_message(help_message, to=From)
            
            # Add help message to session
            container.session_service.add_message(
                phone_number=From,
                content=help_message,
                message_type=MessageType.TEXT,
                direction=MessageDirection.OUTBOUND
            )
            log.warning("empty_or_unsupported_input")

        return {"success": True}

    except Exception as err:
        log.error("unexpected_error", error=str(err), exec_info=True)
        error_message = "❌ Internal error. Please try again later or contact support."
        container.twillio_service.send_message(error_message, to=From)
        
        # Add error message to session
        container.session_service.add_message(
            phone_number=From,
            content=error_message,
            message_type=MessageType.TEXT,
            direction=MessageDirection.OUTBOUND,
            metadata={"error": str(err)}
        )
        raise HTTPException(status_code=500, detail="Internal server error")

# New endpoint to get session information
@router.get("/session/{phone_number}")
async def get_session_info(
    phone_number: str,
    container: Container = Depends(get_container)
):
    """Get session information and conversation history for a phone number."""
    try:
        session = container.session_service.get_session_by_phone(phone_number)
        if not session:
            return {"message": "No active session found", "session": None}
        history = container.session_service.get_conversation_history(phone_number)
        return {
            "session": container.session_service.get_session_summary(session.session_id),
            "conversation_history": [msg.dict() for msg in history],
            "message_count": len(history)
        }
    except Exception as e:
        logger.error("failed_to_get_session", phone_number=phone_number, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get session information")

# New endpoint to get all active sessions (admin endpoint)
@router.get("/sessions/active")
async def get_active_sessions(
    container: Container = Depends(get_container)
):
    """Get all active sessions (admin endpoint)."""
    try:
        sessions = container.session_service.get_all_sessions()
        active_sessions = [s for s in sessions if s.status.value == "active"]
        
        return {
            "active_sessions": [container.session_service.get_session_summary(s.session_id) for s in active_sessions],
            "total_active": len(active_sessions)
        }
        
    except Exception as e:
        logger.error("failed_to_get_active_sessions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get active sessions")

# New endpoint to complete a session
@router.post("/session/{session_id}/complete")
async def complete_session(
    session_id: str,
    container: Container = Depends(get_container)
):
    try:
        success = container.session_service.complete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session completed successfully"}
        
    except Exception as e:
        logger.error("failed_to_complete_session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to complete session")
