import logging
import ssl
from typing import List, Optional

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)

AMAP_GEO_URL = "https://restapi.amap.com/v3/geocode/geo"

_SSL_CONTEXT = ssl.create_default_context()
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = ssl.CERT_NONE

_cache: dict = {}


async def geocode(address: str, city: str = "") -> Optional[dict]:
    """Geocode an address to lat/lng using AMap API. Returns {lat, lng} or None."""
    api_key = settings.amap_api_key
    if not api_key:
        return None

    cache_key = f"{address}|{city}"
    if cache_key in _cache:
        return _cache[cache_key]

    connector = aiohttp.TCPConnector(ssl=_SSL_CONTEXT)
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as client:
            async with client.get(AMAP_GEO_URL, params={
                "key": api_key,
                "address": address,
                "city": city,
            }) as resp:
                if resp.status != 200:
                    logger.warning("AMap geocode returned %s for %s", resp.status, address)
                    return None
                data = await resp.json()
    except Exception:
        logger.warning("AMap geocode failed for %s", address, exc_info=True)
        return None

    geocodes: List[dict] = data.get("geocodes", [])
    if not geocodes:
        return None

    location_str = geocodes[0].get("location", "")
    if not location_str:
        return None

    try:
        lng_str, lat_str = location_str.split(",")
        result = {"lng": float(lng_str), "lat": float(lat_str)}
        _cache[cache_key] = result
        return result
    except (ValueError, TypeError):
        return None


async def enrich_trip_geolocations(trip_data: dict) -> dict:
    """Enrich trip activities with geo coordinates via AMap geocoding."""
    if not settings.amap_api_key:
        return trip_data

    destination = trip_data.get("destination", "")

    for day in trip_data.get("days", []):
        for activity in day.get("activities", []):
            name = activity.get("name", "")
            if not name:
                continue

            query = f"{name}"
            loc = await geocode(query, destination)
            if loc:
                activity["location"] = loc

    return trip_data
