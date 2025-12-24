"""Report generation routes"""
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.schemas import ReportRequest, ReportResponse
from app.services.gemini_service import GeminiService

router = APIRouter()


@router.post("/generate-report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """Generate a structured report based on chat history and sources"""
    try:
        print(f"Generate report request: type='{request.report_type}', store='{request.store_name}', history_length={len(request.chat_history)}")
        service = GeminiService()

        report_content = await service.generate_report(
            store_name=request.store_name,
            chat_history=request.chat_history,
            report_type=request.report_type
        )

        # Generate title based on report type
        report_titles = {
            "comprehensive": "Comprehensive Analysis Report",
            "summary": "Executive Summary",
            "faq": "Frequently Asked Questions",
            "briefing": "Briefing Document"
        }

        title = report_titles.get(request.report_type, "Report")

        print(f"Report generated successfully: {len(report_content)} characters")

        return ReportResponse(
            title=title,
            content=report_content,
            generated_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        import traceback
        error_detail = f"Generate report error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))
