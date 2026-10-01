from fastapi import APIRouter

from app.agents.report.pdf import export_pdf
from app.models.schemas import Sitrep

router = APIRouter(prefix="/agents/report", tags=["report"])


@router.post("/pdf")
async def regenerate_pdf(sitrep: Sitrep) -> dict:
    filename = export_pdf(sitrep)
    return {"pdf_url": f"/static/pdf/{filename}"}
