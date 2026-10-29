from typing import Any

from app.services.media.factory import get_media_providers


VIDEO_HINTS = (
    "video", "footage", "walking", "moving", "driving", "aerial", "drone",
    "pouring", "flowing", "running", "working", "speaking", "people", "crowd",
    "demonstrat", "process", "action", "construction", "travel", "traffic",
)


def _score(item: dict[str, Any], query: str, target_ratio: float | None, used_ids: set[str]) -> float:
    score = 0.0
    haystack = " ".join(str(item.get(k) or "") for k in ("title", "description", "source")).lower()
    words = [w for w in query.lower().replace(",", " ").split() if len(w) > 2]
    score += sum(2.0 for word in words if word in haystack)

    item_id = str(item.get("id") or "")
    if item_id in used_ids:
        score -= 100.0

    width = item.get("width")
    height = item.get("height")
    if width and height and target_ratio:
        ratio = float(width) / float(height)
        score += max(0.0, 3.0 - abs(ratio - target_ratio) * 5.0)
        score += min(float(width) / 1000.0, 2.0)

    if item.get("type") == "video":
        score += 1.0
    return score


def _target_ratio(platform: str | None) -> float:
    value = (platform or "").lower()
    if "tiktok" in value or "reel" in value or "short" in value:
        return 9 / 16
    if "facebook" in value:
        return 4 / 5
    return 16 / 9


def _preferred_type(scene: Any) -> str:
    text = f"{scene.title or ''} {scene.visual_description or ''}".lower()
    return "video" if any(hint in text for hint in VIDEO_HINTS) else "image"


async def auto_select_scene_media(scene: Any, platform: str | None, used_keys: set[str]) -> dict[str, Any] | None:
    query = (scene.visual_description or scene.title or "").strip()
    if not query:
        return None

    providers = get_media_providers()
    if not providers:
        raise RuntimeError("No stock media provider is configured. Add PEXELS_API_KEY or PIXABAY_API_KEY to backend/.env.")

    preferred = _preferred_type(scene)
    target_ratio = _target_ratio(platform)
    candidates: list[dict[str, Any]] = []

    for media_type in (preferred, "image" if preferred == "video" else "video"):
        for provider in providers:
            try:
                results = await provider.search(query, media_type, 8)
                candidates.extend(results)
                if results:
                    break
            except Exception:
                continue
        if candidates:
            break

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: _score(item, query, target_ratio, {k.split(":", 1)[-1] for k in used_keys}),
        reverse=True,
    )
    chosen = candidates[0]
    key = f"{chosen.get('provider')}:{chosen.get('id')}"
    used_keys.add(key)
    chosen = dict(chosen)
    chosen["selection_source"] = "auto"
    chosen["manual_selection"] = False
    return chosen
