import httpx

DEFAULT_TIMEOUT = httpx.Timeout(20.0, connect=10.0)


def new_client() -> httpx.AsyncClient:
    """Every agent opens/closes its own short-lived client per request instead of
    sharing one long-lived client — simpler lifecycle, and one agent's slow
    upstream can't starve a connection pool the others depend on."""
    return httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, headers={"User-Agent": "def-space-dashboard/1.0"})
