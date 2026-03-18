"""Real 1C HTTP client — async httpx with auth support.

Constitution I: No domain model imports; returns raw dicts.
Phase 6: Replaces mock_1c_adapter when a real 1C service is available.
"""

import time
from datetime import date

import httpx
from loguru import logger

# Request timeout in seconds
_TIMEOUT = 30.0

# Max bytes of response body to print in debug logs (avoids flooding on large payloads)
_LOG_BODY_PREVIEW = 500


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
    url = f"{endpoint.rstrip('/')}/data"

    logger.debug(
        "1C fetch → GET {url} | params={params} | auth={auth_type} | timeout={timeout}s",
        url=url,
        params=params,
        auth_type=auth_type,
        timeout=_TIMEOUT,
    )

    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, params=params, auth=auth)
            elapsed_ms = int((time.monotonic() - t0) * 1000)

        logger.debug(
            "1C fetch ← {status} | {elapsed_ms}ms | content-type={ct} | body_size={size}B",
            status=response.status_code,
            elapsed_ms=elapsed_ms,
            ct=response.headers.get("content-type", "—"),
            size=len(response.content),
        )

        if response.status_code >= 400:
            preview = response.text[:_LOG_BODY_PREVIEW]
            logger.error(
                "1C fetch error {status} | url={url} | body_preview={preview}",
                status=response.status_code,
                url=str(response.url),
                preview=preview,
            )

        response.raise_for_status()

    except httpx.TimeoutException:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.error("1C fetch TIMEOUT after {elapsed_ms}ms | url={url}", elapsed_ms=elapsed_ms, url=url)
        raise
    except httpx.ConnectError as exc:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.error("1C fetch CONNECT ERROR after {elapsed_ms}ms | url={url} | {exc}", elapsed_ms=elapsed_ms, url=url, exc=exc)
        raise

    body = response.json()
    rows: list[dict] = body.get("data", [])

    logger.debug(
        "1C fetch parsed | rows={rows} | first_keys={keys}",
        rows=len(rows),
        keys=list(rows[0].keys()) if rows else [],
    )
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
    auth = _build_auth(auth_type, auth_user, auth_password)
    url = f"{endpoint.rstrip('/')}/data"
    params: dict[str, str] = {"register_name": register_name}

    logger.debug(
        "1C test → GET {url} | register={register} | auth={auth_type}",
        url=url,
        register=register_name,
        auth_type=auth_type,
    )

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, auth=auth)
            elapsed_ms = int((time.monotonic() - start) * 1000)

        logger.debug(
            "1C test ← {status} | {elapsed_ms}ms | body_preview={preview}",
            status=response.status_code,
            elapsed_ms=elapsed_ms,
            preview=response.text[:_LOG_BODY_PREVIEW],
        )

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
            preview = response.text[:_LOG_BODY_PREVIEW]
            logger.error("1C test server error {status} | {preview}", status=response.status_code, preview=preview)
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
        logger.warning("1C test TIMEOUT after {elapsed_ms}ms | url={url}", elapsed_ms=elapsed_ms, url=url)
        return {
            "status": "error",
            "message": "1C service unavailable: connection timeout",
            "response_time_ms": elapsed_ms,
        }
    except httpx.ConnectError as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.warning("1C test CONNECT ERROR | url={url} | {exc}", url=url, exc=exc)
        return {
            "status": "error",
            "message": f"Cannot connect to 1C service at {endpoint}",
            "response_time_ms": elapsed_ms,
        }
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.exception("1C test unexpected error | url={url}", url=url)
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
