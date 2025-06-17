import httpx
from typing import Dict, Any
from src.core.exceptions import FrappeError
from src.core.logging import LoggerAdapter
from src.models.order import OrderDetails
from src.repositories.frappe_repository import FrappeRepository

class FrappeService:
    """Service for Frappe operations."""
    
    def __init__(self, base_url: str, api_key: str, api_secret: str):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def create_order(self, order_details: OrderDetails) -> dict:
        try:
            response = await self.client.post(
                "/api/resource/Sales Order",
                json={
                    "customer": order_details.customer_name,
                    "delivery_date": "2024-03-20",
                    "items": [
                        {
                            "item_code": item,
                            "qty": 1,
                            "rate": 100
                        } for item in order_details.items
                    ]
                },
                headers={
                    "Authorization": f"token {self.api_key}:{self.api_secret}"
                }
            )
            
            if response.status_code != 200:
                raise FrappeError(f"Failed to create order: {response.text}")
                
            return response.json()
            
        except Exception as e:
            raise FrappeError(f"Error creating order: {str(e)}")

    async def create_sales_order(self, order_details: OrderDetails) -> Dict[str, Any]:
        """Create a sales order in Frappe."""
        try:
            # Prepare the sales order data
            sales_order_data = {
                "doctype": "Sales Order",
                "customer": order_details.supplier,
                "items": [{
                    "item_code": order_details.item_name,
                    "qty": order_details.quantity,
                    "rate": order_details.price
                }],
                "status": "Draft"
            }
            
            self.logger.info(
                "Creating sales order",
                order_details=order_details.dict()
            )
            
            # Create the sales order
            result = await self.repository.create_sales_order(sales_order_data)
            
            self.logger.info(
                "Successfully created sales order",
                sales_order=result
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Unexpected error while creating sales order", error=str(e))
            raise FrappeError(
                "Unexpected error while creating sales order",
                details={"error": str(e)}
            ) 