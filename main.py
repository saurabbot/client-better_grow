from fastapi import FastAPI, HTTPException, Request
from loguru import logger
import os
from dotenv import load_dotenv
from services.openai_service import OpenAIService
from services.frappe_service import FrappeService
from models.webhook import WebhookRequest
from models.order import OrderDetails

load_dotenv()
logger.add("app.log", rotation="500 MB")
app = FastAPI(title="WhatsApp Order Processor")
openai_service = OpenAIService()
frappe_service = FrappeService()
@app.post("/webhook")
async def webhook(request: Request):
    try:
        webhook_data = await request.json()
        logger.info(f"Received webhook data: {webhook_data}")
        message = webhook_data.get("message", {}).get("text", "")
        if not message:
            raise HTTPException(status_code=400, detail="No message found in webhook data")
        order_details = await openai_service.extract_order_details(message)
        logger.info(f"Extracted order details: {order_details}")
        sales_order = await frappe_service.create_sales_order(order_details)
        logger.info(f"Created sales order: {sales_order}")
        return {
            "status": "success",
            "message": "Order processed successfully",
            "sales_order": sales_order
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port) 