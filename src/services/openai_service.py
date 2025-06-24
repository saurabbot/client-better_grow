import os
import json
import base64
import aiohttp
import io
import tempfile
from typing import Optional
from openai import AsyncOpenAI
from src.models.order import OrderDetails
from src.core.exceptions import OpenAIError
import structlog
from langchain_community.document_loaders import PyPDFLoader
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

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
                        "content":  """You are a sales agent at Better Grow FMCG company in Dubai. Your job is to process customer order messages that may be in English, Arabic, Malayalam, or Hindi, and return order details in a standardized English string format.
Rules:

Return only a string - no explanations, confirmations, or additional text
Each item must be on a new line in this exact format: Item: [Product Name], Rate: [Price], UOM: [Unit], Qty: [Quantity]
Number each item (1., 2., 3., etc.)
Include customer name on a separate line after all items
Include any special instructions on the final line
Always extract specific product names, sizes, and variants mentioned
If price is not mentioned, use "Standard Rate"
Use appropriate UOM abbreviations:

CTN (Cartons), PKT (Packets), KG (Kilograms), GM (Grams)
LTR (Liters), BTL (Bottles), PCS (Pieces), BOX (Boxes)


Convert any quantity mentioned in local languages to numbers
Standardize product names (e.g., "Badam" → "Almond", "Kaju" → "Cashew")
Convert currency symbols to appropriate format (₹, AED, etc.)

Example Input: "Need 1 carton walnut at 20 rupees, 3 packets almonds, and 22 cashew packets for Empire Restaurant"
Example Output:
1. Item: Walnut, Rate: ₹20, UOM: CTN, Qty: 1
2. Item: Almond, Rate: Standard Rate, UOM: PKT, Qty: 3
3. Item: Cashew, Rate: Standard Rate, UOM: PKT, Qty: 22
Customer Name: Empire Restaurant
Please order at standard rates
Language Hints:

Arabic: Numbers may be written in Arabic numerals
Malayalam/Hindi: Common product names (badam=almond, kaju=cashew, pista=pistachio)
Always convert to English product names in output

Process any order message following this exact format with no additional commentary.
                        
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
            return extracted_data
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
                    look at the image and extract the order details in a standardized string format only in english.
                    Rules:

Return only a string - no explanations, confirmations, or additional text
Each item must be on a new line in this exact format: Item: [Product Name], Rate: [Price], UOM: [Unit], Qty: [Quantity]
Number each item (1., 2., 3., etc.)
Include customer name on a separate line after all items
Include any special instructions on the final line
Always extract specific product names, sizes, and variants mentioned
If price is not mentioned, use "Standard Rate"
Use appropriate UOM abbreviations:

CTN (Cartons), PKT (Packets), KG (Kilograms), GM (Grams)
LTR (Liters), BTL (Bottles), PCS (Pieces), BOX (Boxes)


Convert any quantity mentioned in local languages to numbers
Standardize product names (e.g., "Badam" → "Almond", "Kaju" → "Cashew")
Convert currency symbols to appropriate format (₹, AED, etc.)

Example Input: "Need 1 carton walnut at 20 rupees, 3 packets almonds, and 22 cashew packets for Empire Restaurant"
Example Output:
1. Item: Walnut, Rate: ₹20, UOM: CTN, Qty: 1
2. Item: Almond, Rate: Standard Rate, UOM: PKT, Qty: 3
3. Item: Cashew, Rate: Standard Rate, UOM: PKT, Qty: 22
Customer Name: Empire Restaurant
Please order at standard rates
Language Hints:

Arabic: Numbers may be written in Arabic numerals
Malayalam/Hindi: Common product names (badam=almond, kaju=cashew, pista=pistachio)
Always convert to English product names in output

Process any order message following this exact format with no additional commentary.
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
    async def transcribe_audio(self, audio_url: str) -> Optional[str]:
        try:
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            
            if not account_sid or not auth_token:
                raise OpenAIError("Twilio credentials not found in environment variables")
            auth = aiohttp.BasicAuth(account_sid, auth_token)
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url, auth=auth) as response:
                    if response.status != 200:
                        self.logger.error("Failed to download audio", 
                                        status=response.status,
                                        url=audio_url)
                        raise OpenAIError(f"Failed to download audio: {response.status}")
                    audio_data = await response.read()

            # Transcribe audio using OpenAI Whisper
            # Note: Don't specify language parameter for auto-detection
            transcription = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.wav", audio_data, "audio/wav")
                # Removed language="auto" - Whisper will auto-detect language
            )

            transcribed_text = transcription.text
            self.logger.info("Audio transcribed successfully", 
                           audio_url=audio_url, 
                           transcription_length=len(transcribed_text),
                           transcription=transcribed_text)
            
            return transcribed_text

        except Exception as e:
            self.logger.error("Error in audio transcription", 
                            error=str(e),
                            audio_url=audio_url)
            raise OpenAIError("Error in audio transcription", details={"error": str(e)})

    async def extract_order_from_audio(self, audio_url: str) -> Optional[OrderDetails]:
        """Extract order details from audio by first transcribing it."""
        try:
            # Step 1: Transcribe the audio
            transcribed_text = await self.transcribe_audio(audio_url)
            
            if not transcribed_text:
                self.logger.warning("No transcription obtained from audio", audio_url=audio_url)
                return None
            
            self.logger.info("Audio transcribed", 
                           audio_url=audio_url, 
                           transcription=transcribed_text)
            
            # Step 2: Extract order details from transcribed text
            order_details = await self.extract_order_details(transcribed_text)
            
            return order_details

        except Exception as e:
            self.logger.error("Error in audio order extraction", 
                            error=str(e),
                            audio_url=audio_url)
            raise OpenAIError("Error in audio order extraction", details={"error": str(e)})

    async def extract_text_with_ocr(self, pdf_data: bytes) -> str:
        """Extract text from PDF using OCR (for scanned/image-based PDFs)."""
        images = convert_from_bytes(pdf_data)
        extracted_text = ""
        for img in images:
            text = pytesseract.image_to_string(img)
            extracted_text += text + "\n"
        return extracted_text

    async def extract_order_from_pdf(self, pdf_url: str) -> Optional[OrderDetails]:
        """Extract order details from PDF using LangChain's PyPDFLoader and OCR fallback."""
        try:
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            
            if not account_sid or not auth_token:
                raise OpenAIError("Twilio credentials not found in environment variables")

            auth = aiohttp.BasicAuth(account_sid, auth_token)
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url, auth=auth) as response:
                    if response.status != 200:
                        self.logger.error("Failed to download PDF", 
                                        status=response.status,
                                        url=pdf_url)
                        raise OpenAIError(f"Failed to download PDF: {response.status}")
                    pdf_data = await response.read()

            # Use LangChain's PyPDFLoader for better text extraction
            try:
                # Create a temporary file to save the PDF
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(pdf_data)
                    temp_file_path = temp_file.name
                
                # Use LangChain's PyPDFLoader
                loader = PyPDFLoader(temp_file_path)
                documents = loader.load()
                
                # Extract text from all pages
                extracted_text = ""
                for doc in documents:
                    if doc.page_content:
                        extracted_text += doc.page_content + "\n"
                
                # Clean up temporary file
                os.unlink(temp_file_path)
                
                self.logger.info("PDF text extracted successfully using LangChain", 
                               pdf_url=pdf_url,
                               text_length=len(extracted_text),
                               pages=len(documents))
                
                # OCR fallback if no text extracted
                if not extracted_text.strip():
                    self.logger.warning("No text extracted from PDF, attempting OCR", pdf_url=pdf_url)
                    extracted_text = await self.extract_text_with_ocr(pdf_data)
                    if not extracted_text.strip():
                        return {
                            "message": "The PDF appears to be empty or contains no extractable text, even with OCR. Please send your order as text or image.",
                            "pdf_url": pdf_url,
                            "status": "no_text_extracted"
                        }
                
                # Process the extracted text with the existing order extraction method
                order_details = await self.extract_order_details(extracted_text)
                
                if order_details:
                    self.logger.info("Order details extracted from PDF text", 
                                   pdf_url=pdf_url,
                                   order_details=order_details)
                    return order_details
                else:
                    return {
                        "message": "I couldn't detect any order details in the PDF content. Please ensure the PDF contains clear order information or send your order as text.",
                        "pdf_url": pdf_url,
                        "extracted_text": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
                        "status": "no_order_found"
                    }
                    
            except Exception as pdf_error:
                self.logger.error("Error extracting text from PDF using LangChain", 
                                error=str(pdf_error),
                                pdf_url=pdf_url)
                return {
                    "message": "Sorry, I couldn't read the PDF file. It might be corrupted, password-protected, or in an unsupported format. Please send your order as text or image.",
                    "pdf_url": pdf_url,
                    "status": "pdf_extraction_failed"
                }

        except Exception as e:
            self.logger.error("Error in PDF order extraction", 
                            error=str(e),
                            pdf_url=pdf_url)
            raise OpenAIError("Error in PDF order extraction", details={"error": str(e)})
