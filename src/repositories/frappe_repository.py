from typing import Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.exceptions import FrappeError
from src.core.logging import LoggerAdapter

class FrappeRepository:
    """Repository for Frappe API interactions."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_secret: str,
        logger: LoggerAdapter
    ):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"token {api_key}:{api_secret}",
            "Content-Type": "application/json"
        }
        self.logger = logger.bind(component="frappe_repository")
        self.client = httpx.AsyncClient(base_url=base_url)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def create_sales_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a sales order in Frappe."""
        try:
            response = await self.client.post(
                "/api/resource/Sales Order",
                json=data,
                headers=self.headers
            )
            
            if response.status_code != 200:
                self.logger.error(
                    "Failed to create sales order",
                    status_code=response.status_code,
                    response=response.text
                )
                raise FrappeError(f"Failed to create sales order: {response.text}")
            
            return response.json()
            
        except httpx.RequestError as e:
            self.logger.error("Network error while creating sales order", error=str(e))
            raise FrappeError(f"Network error while creating sales order: {str(e)}")
        except Exception as e:
            self.logger.error("Unexpected error while creating sales order", error=str(e))
            raise FrappeError(f"Error creating sales order: {str(e)}") 