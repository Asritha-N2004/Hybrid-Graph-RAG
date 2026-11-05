from typing import Literal
from pydantic import BaseModel, Field, model_validator

class Product(BaseModel):
    id: str = Field(pattern=r'^[A-Za-z0-9_-]{1,64}$')
    name: str = Field(min_length=1, max_length=200)
    brand_id: str
    brand: str
    category_id: str
    category: str
    domain: str
    description: str = Field(max_length=10000)
    price: float | None = Field(default=None, ge=0)
    currency: str = 'USD'
    specifications: dict[str, str | int | float | bool] = Field(default_factory=dict)
    features: list[str] = Field(default_factory=list)
    compatibility: list[str] = Field(default_factory=list)
    synthetic: bool = True

class Query(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=30)
    method: Literal['hybrid','vector','keyword','graph'] = 'hybrid'
    category: str | None = None

class Compare(BaseModel):
    product_ids: list[str] = Field(min_length=2, max_length=8)

class Settings(BaseModel):
    vector_weight: float = Field(default=.4, ge=0, le=1)
    keyword_weight: float = Field(default=.25, ge=0, le=1)
    graph_weight: float = Field(default=.25, ge=0, le=1)
    metadata_weight: float = Field(default=.1, ge=0, le=1)
    top_k: int = Field(default=5, ge=1, le=30)
    retry_limit: int = Field(default=1, ge=0, le=3)
    @model_validator(mode='after')
    def weights(self):
        if abs(self.vector_weight+self.keyword_weight+self.graph_weight+self.metadata_weight-1)>0.0001:
            raise ValueError('Retrieval weights must sum to 1')
        return self
