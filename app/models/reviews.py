from app.backend.db import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from app.models import *


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    rating_id = Column(Integer, ForeignKey('ratings.id'))
    comment = Column(String)
    comment_date = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)