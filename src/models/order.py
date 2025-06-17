from pydantic import BaseModel, Field
from typing import Optional, List

class OrderDetails(BaseModel):
    item_name: str = Field(..., description="Name of the item being ordered")
    quantity: int = Field(..., description="Quantity as a number")
    price: float = Field(..., description="Price per unit as a number")
    supplier: str = Field(..., description="Name of the supplier")