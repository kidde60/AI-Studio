from app.core.config import get_settings
from .base import MediaProvider
from .pexels_provider import PexelsMediaProvider
from .pixabay_provider import PixabayMediaProvider


def get_media_providers() -> list[MediaProvider]:
    settings = get_settings()
    providers: list[MediaProvider] = []

    if settings.pexels_api_key:
        providers.append(PexelsMediaProvider(settings.pexels_api_key))

    if settings.pixabay_api_key:
        providers.append(PixabayMediaProvider(settings.pixabay_api_key))

    return providers
