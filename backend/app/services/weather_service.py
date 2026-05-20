import logging
import ssl
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

SENIVERSE_DAILY_URL = "https://api.seniverse.com/v3/weather/daily.json"
_SSL_CONTEXT = ssl.create_default_context()
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = ssl.CERT_NONE


async def get_weather(destination: str, api_key: str) -> Optional[dict]:
    if not api_key:
        return None

    connector = aiohttp.TCPConnector(ssl=_SSL_CONTEXT)
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as client:
            async with client.get(
                SENIVERSE_DAILY_URL,
                params={
                    "key": api_key,
                    "location": destination,
                    "language": "zh-Hans",
                    "unit": "c",
                    "start": 0,
                    "days": 3,
                },
            ) as resp:
                if resp.status != 200:
                    logger.warning("Seniverse API returned %s", resp.status)
                    return None

                data = await resp.json()
    except Exception:
        logger.warning("Seniverse API call failed", exc_info=True)
        return None

    results = data.get("results") or []
    if not results:
        logger.warning("Seniverse API no results for %s", destination)
        return None

    result = results[0]
    location = result.get("location", {})
    daily = result.get("daily") or []

    return {
        "city": location.get("name", destination),
        "forecast": [
            {
                "date": d.get("date"),
                "temp_max": int(d.get("high", 0)),
                "temp_min": int(d.get("low", 0)),
                "text_day": d.get("text_day", ""),
                "text_night": d.get("text_night", ""),
                "humidity": int(d.get("humidity", 0)),
                "wind_dir": d.get("wind_direction", ""),
                "wind_scale": d.get("wind_scale", ""),
            }
            for d in daily
        ],
    }
