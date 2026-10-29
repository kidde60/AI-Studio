from fastapi import HTTPException


def ai_failure(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)

    if status_code == 429:
        return HTTPException(
            status_code=503,
            detail="The AI service rate limit was reached. Please wait a moment and try again.",
        )
    if status_code == 503:
        return HTTPException(
            status_code=503,
            detail="The AI service is temporarily busy. Please wait a moment and try again.",
        )
    if status_code in {401, 403}:
        return HTTPException(
            status_code=502,
            detail="The AI service credentials were rejected. Check GEMINI_API_KEY in backend/.env.",
        )
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=502, detail=str(exc))

    return HTTPException(
        status_code=502,
        detail="The AI service could not complete this request. Please try again.",
    )
