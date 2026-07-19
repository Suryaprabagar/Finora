"""Report schemas."""
import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class ReportGenerateRequest(BaseModel):
    report_type: str
    period_start: str  # YYYY-MM-DD
    period_end: str    # YYYY-MM-DD
    format: str = "pdf"  # pdf | csv | excel
    name: Optional[str] = None


class ReportResponse(BaseModel):
    id: uuid.UUID
    name: str
    report_type: str
    period_start: str
    period_end: str
    format: str
    status: str
    file_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
