import os
import json
import base64
import aiohttp
from typing import Optional
from openai import AsyncOpenAI
from src.models.order import OrderDetails
from src.core.exceptions import OpenAIError
import structlog

class OpenAIService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.logger = structlog.get_logger(__name__)

    async def extract_order_details(self, text: str) -> Optional[OrderDetails]:
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Your a sales person at better grow in an FMCG company in dubai your job is to understand the text message might be english, arabi, malayalam and hindi and return the oder details in a json format only in english.Follow these rules while return the json
                        RULES:
                        1. only return a json
                        2. Json should include all data but should make sense for the other agent to process
                        
                        """
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=300
            )

            extracted_data = response.choices[0].message.content.strip()
            data = json.loads(extracted_data)
            print(data)
            return data
            
            # return OrderDetails(
            #     customer_name=data.get("customer_name", "Unknown Customer"),
            #     phone_number=data.get("phone_number", "+1234567890"),
            #     items=data.get("items", []),
            #     total_amount=data.get("total_amount", 0.0),
            #     delivery_address=data.get("delivery_address"),
            #     payment_method=data.get("payment_method"),
            #     order_notes=data.get("order_notes")
            # )

        except Exception as e:
            self.logger.error("Error in OpenAI API call", error=str(e))
            raise OpenAIError("Error in OpenAI API call", details={"error": str(e)})

    async def extract_order_from_image(self, image_url: str) -> Optional[OrderDetails]:
        try:
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            
            if not account_sid or not auth_token:
                raise OpenAIError("Twilio credentials not found in environment variables")

            auth = aiohttp.BasicAuth(account_sid, auth_token)
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, auth=auth) as response:
                    if response.status != 200:
                        self.logger.error("Failed to download image", 
                                        status=response.status,
                                        url=image_url)
                        raise OpenAIError(f"Failed to download image: {response.status}")
                    image_data = await response.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')

            messages = [
                {
                    "role": "system",
                    "content": """You work at an FMCG company and you take care of new orders and many salesmen send you whatsapp images of the things they need your job is to 
                    look at the image and extract the order details and return them in a json format.
                    RULES:
                        1. only return a json
                        2. Json should include all data but should make sense for the other agent to process
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this image and extract any order details you can find."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=300
            )

            extracted_data = response.choices[0].message.content.strip()
            print("Raw OpenAI content:", extracted_data)
            return extracted_data

        except Exception as e:
            self.logger.error("Error in OpenAI API call", 
                            error=str(e),
                            image_url=image_url)
            raise OpenAIError("Error in OpenAI API call", details={"error": str(e)})