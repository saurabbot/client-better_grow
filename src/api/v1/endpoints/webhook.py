from fastapi import APIRouter, Depends, Form, HTTPException
from src.core.container import Container
from src.models.webhook import WebhookRequest
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
    
@router.post("/twilio-webhook")
async def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None),
    MediaUrl1: str = Form(None),
    MediaContentType1: str = Form(None),
    container: Container = Depends(get_container)
):
    try:
        logger = container.logger.bind(endpoint="twilio_webhook")
        
        if NumMedia > 0:
            media_info = {
                "num_media": NumMedia,
                "media": []
            }
            
            if MediaUrl0 and MediaContentType0:
                media_info["media"].append({
                    "url": MediaUrl0,
                    "type": MediaContentType0
                })
                
                if MediaContentType0.startswith('image/'):
                    try:
                        order_details = await container.openai_service.extract_order_from_image(MediaUrl0)
                        if order_details:
                            confirmation_message = order_details
                            container.twillio_service.send_message(confirmation_message, to=From)
                        else:
                            container.twillio_service.send_message(
                                "I couldn't find any order details in the image. Please send your order details in text format.",
                                to=From
                            )
                    except Exception as e:
                        logger.error("failed_to_process_image", error=str(e))
                        container.twillio_service.send_message(
                            "I'm sorry, but I couldn't process the image. Please send your order details in text format.",
                            to=From
                        )
                else:
                    container.twillio_service.send_message(
                        "I can only process images and text messages for orders. Please send your order details in text format or as an image.",
                        to=From
                    )
                return {"status": "success", "message": "Media processed"}

        if Body:
            logger.info("twilio_webhook_received", from_number=From, body=Body)

            order_details = await container.openai_service.extract_order_details(Body)
            if not order_details:
                logger.warning("no_order_details_found", text=Body)
                container.twillio_service.send_message(
                    "I couldn't understand the order details. Please provide the order in a clear format like: 'I need to order 10 units of Product XYZ at $25.99 each from Supplier ABC'",
                    to=From
                )
                return {"status": "success", "message": "No order details found in message"}

            logger.info("order_details_extracted", details=order_details.dict())
            
            try:
                confirmation_message = f"""
                Thank you for your order! Here's a summary:
                - Item: {order_details.item_name}
                - Quantity: {order_details.quantity}
                - Price per unit: ${order_details.price:.2f}
                - Total amount: ${order_details.quantity * order_details.price:.2f}
                - Supplier: {order_details.supplier}
                
                Your order has been processed successfully.
                """
                container.twillio_service.send_message(confirmation_message, to=From)
                
            except Exception as e:
                logger.error("failed_to_create_order", error=str(e))
                container.twillio_service.send_message(
                    "I'm sorry, but there was an error processing your order. Please try again later or contact support.",
                    to=From
                )
                raise
            
            return {"status": "success"}
        else:
            logger.warning("no_text_content", from_number=From)
            container.twillio_service.send_message(
                "I can only process text messages for orders. Please send your order details in text format.",
                to=From
            )
            return {"status": "success", "message": "No text content found"}
        
    except BaseAppException as e:
        logger.error("application_error", error=str(e), exc_info=True)
        container.twillio_service.send_message(
            f"I'm sorry, but there was an error: {str(e)}",
            to=From
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("unexpected_error", error=str(e), exc_info=True)
        container.twillio_service.send_message(
            "I'm sorry, but there was an unexpected error. Please try again later or contact support.",
            to=From
        )
        raise HTTPException(status_code=500, detail="Internal server error")