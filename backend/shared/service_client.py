"""
Typed HTTP client for inter-service communication.
Each service uses this to call other services with retries and timeouts.
"""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class ServiceClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=3.0),
                limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
    )
    async def get(self, path: str, params: dict | None = None) -> dict:
        client = await self._get_client()
        r = await client.get(path, params=params)
        r.raise_for_status()
        return r.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
    )
    async def post(self, path: str, json: dict | None = None) -> dict:
        client = await self._get_client()
        r = await client.post(path, json=json)
        r.raise_for_status()
        return r.json()

    async def health(self) -> bool:
        try:
            client = await self._get_client()
            r = await client.get("/health")
            return r.status_code == 200
        except Exception:
            return False


class ServiceRegistry:
    """Registry of all downstream service clients."""

    def __init__(
        self,
        auth_url: str = "http://localhost:8001",
        article_url: str = "http://localhost:8002",
        video_url: str = "http://localhost:8003",
        analytics_url: str = "http://localhost:8004",
        search_url: str = "http://localhost:8005",
        notification_url: str = "http://localhost:8006",
    ):
        self.auth = ServiceClient(auth_url)
        self.articles = ServiceClient(article_url)
        self.video = ServiceClient(video_url, timeout=120.0)
        self.analytics = ServiceClient(analytics_url)
        self.search = ServiceClient(search_url)
        self.notifications = ServiceClient(notification_url)

    async def close_all(self):
        for client in [self.auth, self.articles, self.video, self.analytics, self.search, self.notifications]:
            await client.close()

    async def health_all(self) -> dict[str, bool]:
        import asyncio
        names = ["auth", "articles", "video", "analytics", "search", "notifications"]
        clients = [self.auth, self.articles, self.video, self.analytics, self.search, self.notifications]
        results = await asyncio.gather(*[c.health() for c in clients], return_exceptions=True)
        return {name: (r is True) for name, r in zip(names, results)}
