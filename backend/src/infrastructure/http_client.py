"""Real 1C HTTP client — async httpx with auth support.

Constitution I: No domain model imports; returns raw dicts.
Phase 6: Replaces mock_1c_adapter when a real 1C service is available.
"""

from datetime import date

import httpx

# Request timeout in seconds
_TIMEOUT = 30.0


async def fetch_1c_data(
    endpoint: str,
    register_name: str,
    date_from: date,
    date_to: date,
    auth_type: str = "none",
    auth_user: str | None = None,
    auth_password: str | None = None,
) -> list[dict]:
    """Fetch all records from 1C HTTP service in a single request.

    Args:
        endpoint: Base URL of the 1C HTTP service (e.g. "http://1c/base/hs/analytics/v1").
        register_name: Name of the 1C accumulation register.
        date_from: Start of the analysis period.
        date_to: End of the analysis period.
        auth_type: "none" or "basic".
        auth_user: Username for Basic auth.
        auth_password: Password for Basic auth.

    Returns:
        List of raw row dicts from the "data" key of the response.

    Raises:
        httpx.HTTPStatusError: For 4xx/5xx responses.
        httpx.TimeoutException: When the 1C service does not respond in time.
    """
    auth = _build_auth(auth_type, auth_user, auth_password)

    params: dict[str, str] = {
        "register_name": register_name,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{endpoint.rstrip('/')}/data",
            params=params,
            auth=auth,
        )
        response.raise_for_status()

    body = response.json()
    rows: list[dict] = body.get("data", [])
    return rows


async def test_connection(
    endpoint: str,
    register_name: str,
    auth_type: str = "none",
    auth_user: str | None = None,
    auth_password: str | None = None,
) -> dict:
    """Validate connectivity to 1C HTTP service.

    Returns a dict with keys: status ("ok" | "error"), message, response_time_ms.
    Never raises — all errors are captured and returned as status="error".
    """
    import time

    auth = _build_auth(auth_type, auth_user, auth_password)
    start = time.monotonic()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params: dict[str, str] = {
                "register_name": register_name,
            }
            response = await client.get(
                f"{endpoint.rstrip('/')}/data",
                params=params,
                auth=auth,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)

            if response.status_code == 401:
                return {
                    "status": "error",
                    "message": "Authentication failed: invalid credentials",
                    "response_time_ms": elapsed_ms,
                }
            if response.status_code == 404:
                return {
                    "status": "error",
                    "message": f"Register '{register_name}' not found in 1C configuration",
                    "response_time_ms": elapsed_ms,
                }
            if response.status_code >= 500:
                return {
                    "status": "error",
                    "message": f"1C service error: HTTP {response.status_code}",
                    "response_time_ms": elapsed_ms,
                }

            return {
                "status": "ok",
                "message": "Connection successful",
                "response_time_ms": elapsed_ms,
            }

    except httpx.TimeoutException:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "error",
            "message": "1C service unavailable: connection timeout",
            "response_time_ms": elapsed_ms,
        }
    except httpx.ConnectError:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "error",
            "message": f"Cannot connect to 1C service at {endpoint}",
            "response_time_ms": elapsed_ms,
        }
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "error",
            "message": f"Unexpected error: {exc}",
            "response_time_ms": elapsed_ms,
        }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_auth(
    auth_type: str,
    user: str | None,
    password: str | None,
) -> httpx.BasicAuth | None:
    """Build httpx auth object from DataSource.auth config."""
    if auth_type == "basic" and user and password:
        return httpx.BasicAuth(username=user, password=password)
    return None
