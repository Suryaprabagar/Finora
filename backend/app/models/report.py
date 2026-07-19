"""Report model for saved report metadata."""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid
from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    report_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # Types: income | expense | budget | cashflow | networth | investment | loan | asset | insurance
    period_start: Mapped[str] = mapped_column(String(20), nullable=False)  # YYYY-MM-DD
    period_end: Mapped[str] = mapped_column(String(20), nullable=False)   # YYYY-MM-DD
    format: Mapped[str] = mapped_column(String(10), default="pdf", nullable=False)  # pdf | csv | excel
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)  # pending | completed | failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
