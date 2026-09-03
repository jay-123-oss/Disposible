"""Template: SQLAlchemy ORM model (raw). Placeholders are substituted by PythonModelGenerator."""
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class __MODEL_NAME__(Base):
    """ORM model for the __MODULE_NAME__ domain entity."""

    __tablename__ = "__ROUTE__"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)