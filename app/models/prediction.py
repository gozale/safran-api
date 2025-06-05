from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
from sqlalchemy import LargeBinary

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    input_data = Column(JSON)
    output_data = Column(JSON)
    image_data = Column(LargeBinary)  # <-- Add this line
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")