from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = "userinfo"
    
    username = Column(String,primary_key=True, unique=True, nullable=False)
    password = Column(String, nullable=False)