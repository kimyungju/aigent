from pydantic import BaseModel, Field


class ProductQuery(BaseModel):
    """Input schema for the SearchProduct tool."""
    query: str = Field(description="The product search term")
    max_results: int = Field(default=3, description="Maximum number of results to return")


class Receipt(BaseModel):
    """Structured output schema for the agent's final response."""
    product_name: str = Field(description="Name of the recommended product")
    price: float = Field(description="Price of the product")
    currency: str = Field(default="USD", description="Currency code")
