from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Finding

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/findings/{finding_id}", response_class=HTMLResponse)
def finding_detail(finding_id: str, request: Request, db: Session = Depends(get_db)):
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    return templates.TemplateResponse(request=request, name="detail.html", context={"finding": finding})
