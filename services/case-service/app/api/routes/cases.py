from typing import Optional


from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_agent_or_above, require_supervisor_or_above
from app.models.case import CaseCategory, CasePriority, CaseStatus
from app.models.user import User
from app.schemas.case import CaseAssign, CaseCreate, CaseEscalate, CaseOut, CaseUpdate, NoteCreate
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("", response_model=CaseOut, status_code=201, summary="Create a new case")
@router.post("/", response_model=CaseOut, status_code=201, summary="Create a new case", include_in_schema=False)
async def create_case(
    body: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CaseService(db).create_case(body, current_user.id, current_user.id)


@router.get("", summary="List cases with filters")
@router.get("/", summary="List cases with filters", include_in_schema=False)
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[CaseStatus] = None,
    priority: Optional[CasePriority] = None,
    category: Optional[CaseCategory] = None,
    assigned_to: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Customers only see their own cases
    customer_id = None
    if current_user.role.value == "customer":
        customer_id = current_user.id

    return await CaseService(db).list_cases(
        page=page, page_size=page_size, status=status, priority=priority,
        category=category, customer_id=customer_id, assigned_to=assigned_to, search=search
    )


@router.get("/{case_id}", response_model=CaseOut, summary="Get case by ID")
async def get_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CaseService(db).get_case(case_id)


@router.patch("/{case_id}", response_model=CaseOut, summary="Update case")
async def update_case(
    case_id: str,
    body: CaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_agent_or_above),
):
    return await CaseService(db).update_case(case_id, body, current_user.id)


@router.post("/{case_id}/assign", response_model=CaseOut, summary="Assign case to agent")
async def assign_case(
    case_id: str,
    body: CaseAssign,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_supervisor_or_above),
):
    return await CaseService(db).assign_case(case_id, body, current_user.id)


@router.post("/{case_id}/escalate", response_model=CaseOut, summary="Escalate a case")
async def escalate_case(
    case_id: str,
    body: CaseEscalate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_agent_or_above),
):
    return await CaseService(db).escalate_case(case_id, body, current_user.id)


@router.post("/{case_id}/notes", summary="Add a note to a case")
async def add_note(
    case_id: str,
    body: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_agent_or_above),
):
    return await CaseService(db).add_note(case_id, body, current_user.id)


@router.get("/{case_id}/notes", summary="Get case notes")
async def get_notes(
    case_id: str,
    include_internal: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Customers can't see internal notes
    if current_user.role.value == "customer":
        include_internal = False
    return await CaseService(db).get_notes(case_id, include_internal)


@router.get("/{case_id}/timeline", summary="Get case timeline")
async def get_timeline(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CaseService(db).get_timeline(case_id)



# Add case search by keyword

# Add filter by assigned agent

# Validate UUID format in path param

# Add GET /cases/stats summary

# Add case source filter
