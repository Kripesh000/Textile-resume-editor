from fastapi import APIRouter, Depends, HTTPException

from app.db_models.user import User
from app.schemas.ai import ImproviseRequest, ImproviseResponse
from app.services.ai_service import improvise
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/improvise", response_model=ImproviseResponse)
async def improvise_text(
    data: ImproviseRequest,
    user: User = Depends(get_current_user),
):
    try:
        result = await improvise(data.text, data.context.model_dump())
        return ImproviseResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
