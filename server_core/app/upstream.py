"""Predictable upstream contracts; upstream bodies and URLs are never returned to clients."""
import httpx


class UpstreamError(Exception):
    def __init__(self, service: str, status_code: int = 502):
        self.service = service
        self.status_code = status_code
        super().__init__(f"{service} is temporarily unavailable. Please try again.")


async def checked_post(client: httpx.AsyncClient, service: str, url: str, *, timeout: float, **kwargs):
    try:
        response = await client.post(url, timeout=timeout, **kwargs)
    except httpx.TimeoutException as exc:
        raise UpstreamError(service, 504) from exc
    except httpx.RequestError as exc:
        raise UpstreamError(service, 503) from exc
    if response.status_code != 200 or len(response.content) > 1024 * 1024:
        raise UpstreamError(service, 502)
    try:
        data = response.json()
    except ValueError as exc:
        raise UpstreamError(service, 502) from exc
    if not isinstance(data, dict):
        raise UpstreamError(service, 502)
    return data
