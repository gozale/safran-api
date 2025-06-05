from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
import base64

class PredictionInput(BaseModel):
    image_base64: str

class PredictionOutput(BaseModel):
    result: str

class PredictionRecord(BaseModel):
    id: int
    input_data: Dict
    output_data: Dict
    timestamp: datetime
    image_url: Optional[str] = None  # <-- new field

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_image(cls, prediction, include_image: bool = False):
        return cls(
            id=prediction.id,
            input_data=prediction.input_data,
            output_data=prediction.output_data,
            timestamp=prediction.timestamp,
            image_url=f"/predictions/{prediction.id}/image" if include_image else None
        )
