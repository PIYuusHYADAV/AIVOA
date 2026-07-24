import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, JSON
from app.db import Base


def gen_uuid():
    return str(uuid.uuid4())


class Complaint(Base):
  
    __tablename__ = "complaints"

    id = Column(String(36), primary_key=True, default=gen_uuid)

    
    complaint_source = Column(String(120))       
    customer_name = Column(String(200))

    
    product_name = Column(String(200))
    product_strength = Column(String(100))       
    batch_lot_number = Column(String(100))
    manufacturing_date = Column(String(30))        
    expiry_date = Column(String(30))
    quantity_affected = Column(String(50))         

    # 3. Complaint details
    complaint_type = Column(String(120))           
    complaint_date = Column(String(30))
    description = Column(Text)

    # 4. Initial assessment & priority
    severity = Column(String(30))                  
    priority = Column(String(30))                  

    # AI-derived fields (bonus features)
    ai_confidence = Column(JSON)                  
    ai_missing_fields = Column(JSON)               
    ai_root_cause = Column(Text)
    ai_capa = Column(Text)
    ai_summary = Column(Text)
    ai_duplicate_of = Column(String(36), nullable=True)  #
    ai_duplicate_score = Column(Float, nullable=True)

    status = Column(String(30), default="Pending Triage")
    raw_source_text = Column(Text)                

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
