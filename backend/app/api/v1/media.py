from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.media import MediaSearchRequest, MediaSearchResponse
from app.services.media.factory import get_media_providers

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/search", response_model=MediaSearchResponse)
async def search_media(
    request: MediaSearchRequest,
    _: User = Depends(get_current_user),
):
    providers = get_media_providers()
    if not providers:
        raise HTTPException(
            status_code=503,
            detail="No stock media provider is configured. Add PEXELS_API_KEY or PIXABAY_API_KEY to backend/.env.",
        )

    results: list[dict] = []
    last_error: Exception | None = None

    for provider in providers:
        try:
            results.extend(
                await provider.search(
                    request.query,
                    request.media_type,
                    request.per_page,
                )
            )
            if len(results) >= request.per_page:
                break
        except Exception as exc:
            last_error = exc

    if not results and last_error:
        raise HTTPException(status_code=502, detail="Stock media search failed.")

    return MediaSearchResponse(
        query=request.query,
        media_type=request.media_type,
        results=results[:request.per_page],
    )
