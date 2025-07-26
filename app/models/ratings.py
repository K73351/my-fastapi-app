from app.backend.db import Base
from sqlalchemy import Column, Integer, Boolean, ForeignKey
from app.models import *


class Rating(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(Integer, default=None)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    is_active = Column(Boolean, default=True)