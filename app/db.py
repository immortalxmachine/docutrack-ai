"""
Database layer (SQLAlchemy 2.0).

Two tables model an extracted invoice and its line items. The connection string
comes from DATABASE_URL, so the same code runs against PostgreSQL (production /
docker-compose) or a local SQLite file (zero-setup dev and tests). Foreign keys
and a cascade keep line items tied to their invoice.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str | None] = mapped_column(String(64))
    invoice_date: Mapped[str | None] = mapped_column(String(32))
    currency: Mapped[str | None] = mapped_column(String(8))
    shipper_name: Mapped[str] = mapped_column(String(256))
    shipper_country: Mapped[str | None] = mapped_column(String(128))
    consignee_name: Mapped[str] = mapped_column(String(256))
    consignee_country: Mapped[str | None] = mapped_column(String(128))
    declared_value: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    line_items: Mapped[list["LineItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )


class LineItem(Base):
    __tablename__ = "line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(String(512))
    hs_code: Mapped[str | None] = mapped_column(String(32), index=True)
    quantity: Mapped[float | None] = mapped_column(Float)
    unit_price: Mapped[float | None] = mapped_column(Float)
    amount: Mapped[float | None] = mapped_column(Float)

    invoice: Mapped["Invoice"] = relationship(back_populates="line_items")


# ---------------------------------------------------------------------------
# Engine / session management
# ---------------------------------------------------------------------------
_engine = None
_SessionLocal = None


def _make_engine(url: str):
    # SQLite needs the parent directory to exist and a thread flag for FastAPI.
    if url.startswith("sqlite"):
        path = url.split("///", 1)[-1]
        if path and path not in (":memory:",):
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


def init_db(url: str | None = None):
    """Create the engine, session factory and tables. Idempotent."""
    global _engine, _SessionLocal
    url = url or get_settings().database_url
    _engine = _make_engine(url)
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)
    return _engine


def get_session():
    """Return a new session, initialising the engine on first use."""
    if _SessionLocal is None:
        init_db()
    return _SessionLocal()
