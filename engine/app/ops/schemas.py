"""Response models for the ops endpoints (contract §2), so /openapi.json and web's generated types are exact.

Engine shapes (Issue, ValidationResult, ConsistencyResult) are reused from Person 1's types, never copied.
"""
from pydantic import BaseModel


class OfficeOut(BaseModel):
    id: str
    name: str
    type: str
    taluk: str
    lat: float
    lng: float
