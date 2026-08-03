from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.user import User
from app.models.report import Report
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.report import ReportGenerateRequest, ReportResponse
import uuid
from datetime import datetime, timezone
import os

router = APIRouter()

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "generated_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

@router.post("/generate")
async def generate_report(data: ReportGenerateRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    file_name = f"{data.report_type}_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{data.format}"
    file_path = os.path.join(REPORTS_DIR, file_name)
    
    from app.core.planning.planning_service import PlanningService
    
    # Dummy report generation since we don't have weasyprint/openpyxl installed reliably here
    with open(file_path, "w") as f:
        f.write(f"Finora Report: {data.name}\nType: {data.report_type}\nPeriod: {data.period_start} to {data.period_end}\n\n")
        
        if data.report_type == "goals" or data.report_type == "planning":
            overview = await PlanningService.get_user_planning_overview(db, current_user.id)
            f.write(f"--- Financial Planning Summary ---\n")
            f.write(f"Total Managed Target: {overview['overview']['total_target']}\n")
            f.write(f"Current Funding: {overview['overview']['total_funding']}\n")
            f.write(f"Overall Progress: {overview['overview']['overall_progress']}%\n")
            f.write(f"Total Objectives: {overview['overview']['total_objectives']}\n")
            for obj in overview['objectives']:
                f.write(f"\nObjective: {obj['name']}\n")
                f.write(f"  Target: {obj['target_amount']}\n")
                f.write(f"  Funding: {obj['current_funding']}\n")
                f.write(f"  Health: {obj['health']}\n")
                f.write(f"  Priority Score: {obj['priority_score']}\n")
        
    report = Report(
        user_id=current_user.id,
        name=data.name,
        type=data.report_type,
        format=data.format,
        file_path=file_path,
        period_start=data.period_start,
        period_end=data.period_end
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return APIResponse(data=ReportResponse.model_validate(report).model_dump(), message="Report generated")

@router.get("")
async def list_reports(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Report).where(Report.user_id == current_user.id).order_by(desc(Report.created_at))
    )
    reports = result.scalars().all()
    return APIResponse(data=[ReportResponse.model_validate(r).model_dump() for r in reports])

@router.get("/{id}/download")
async def download_report(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Report).where(Report.id == id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
        
    return FileResponse(path=report.file_path, filename=f"{report.name}.{report.format}")

@router.delete("/{id}")
async def delete_report(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Report).where(Report.id == id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if os.path.exists(report.file_path):
        os.remove(report.file_path)
        
    await db.delete(report)
    await db.commit()
    return APIResponse(message="Report deleted")
