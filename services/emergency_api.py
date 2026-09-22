import requests

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

USER_AGENT = "TravelBytesAI/1.0 (tourism project)"

EMERGENCY_QUERIES = {
    "police": 'nwr["amenity"="police"](around:{radius},{lat},{lon});',
    "fire": 'nwr["amenity"="fire_station"](around:{radius},{lat},{lon});',
    "hospital": 'nwr["amenity"="hospital"](around:{radius},{lat},{lon});',
    "ambulance": 'nwr["emergency"="ambulance_station"](around:{radius},{lat},{lon});',
}


def _coordinates(element):
    if element.get("type") == "node":
        return element.get("lat"), element.get("lon")
    center = element.get("center") or {}
    return center.get("lat"), center.get("lon")


def _clean_item(element, category):
    tags = element.get("tags") or {}
    name = " ".join(str(tags.get("name") or "").split()).strip()
    lat, lon = _coordinates(element)
    if not name or lat is None or lon is None:
        return None

    phone = tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile")
    address_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
    ]
    address = ", ".join(str(x).strip() for x in address_parts if x)

    return {
        "id": f"osm-emergency-{element.get('type')}-{element.get('id')}",
        "name": name,
        "category": category,
        "latitude": float(lat),
        "longitude": float(lon),
        "phone": phone,
        "address": address or tags.get("addr:full"),
        "website": tags.get("website") or tags.get("contact:website"),
        "opening_hours": tags.get("opening_hours"),
        "source": "OpenStreetMap",
        "live": True,
    }


def _fetch(query):
    for server in OVERPASS_SERVERS:
        try:
            response = requests.post(
                server,
                data={"data": query},
                headers={"User-Agent": USER_AGENT},
                timeout=(5, 25),
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            continue
    return None


def get_nearby_emergency_services(latitude, longitude, radius=10000, limit=30):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return {"success": False, "error": "Invalid coordinates.", "items": []}

    items = []
    seen = set()

    for category, clause in EMERGENCY_QUERIES.items():
        query = f"[out:json][timeout:25];({clause.format(radius=radius, lat=latitude, lon=longitude)});out center tags;"
        data = _fetch(query)
        if not data:
            continue

        for element in data.get("elements", []):
            item = _clean_item(element, category)
            if not item:
                continue
            key = (item["name"].lower(), round(item["latitude"], 5), round(item["longitude"], 5), category)
            if key in seen:
                continue
            seen.add(key)
            items.append(item)

    # Sort by approximate straight-line distance without adding another API call.
    def distance(item):
        from math import radians, sin, cos, sqrt, atan2
        phi1, phi2 = radians(latitude), radians(item["latitude"])
        dphi = radians(item["latitude"] - latitude)
        dlambda = radians(item["longitude"] - longitude)
        a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
        return 6371 * 2 * atan2(sqrt(a), sqrt(1 - a))

    for item in items:
        item["distance_km"] = round(distance(item), 2)

    items.sort(key=lambda item: item["distance_km"])

    return {
        "success": True,
        "count": min(len(items), limit),
        "items": items[:limit],
        "source": "OpenStreetMap / Overpass",
        "live": True,
        "fallback_police_emergency": "112",
    }
