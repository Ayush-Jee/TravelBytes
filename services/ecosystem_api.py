import requests

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

CATEGORY_QUERIES = {
    "restaurants": [
        'nwr["amenity"="restaurant"](around:{radius},{lat},{lon});',
        'nwr["amenity"="cafe"](around:{radius},{lat},{lon});',
        'nwr["amenity"="fast_food"](around:{radius},{lat},{lon});',
    ],
    "guides": [
        'nwr["office"="guide"](around:{radius},{lat},{lon});',
        'nwr["guide"](around:{radius},{lat},{lon});',
    ],
    "experiences": [
        'nwr["tourism"="attraction"](around:{radius},{lat},{lon});',
        'nwr["tourism"="museum"](around:{radius},{lat},{lon});',
        'nwr["tourism"="gallery"](around:{radius},{lat},{lon});',
        'nwr["tourism"="viewpoint"](around:{radius},{lat},{lon});',
        'nwr["tourism"="theme_park"](around:{radius},{lat},{lon});',
        'nwr["tourism"="zoo"](around:{radius},{lat},{lon});',
        'nwr["leisure"="water_park"](around:{radius},{lat},{lon});',
        'nwr["leisure"="park"](around:{radius},{lat},{lon});',
    ],
}


def _element_coordinates(element):
    if element.get("type") == "node":
        return element.get("lat"), element.get("lon")

    center = element.get("center") or {}
    return center.get("lat"), center.get("lon")


def _clean_element(element, category):
    tags = element.get("tags") or {}
    name = (tags.get("name") or "").strip()
    if not name:
        return None

    lat, lon = _element_coordinates(element)
    if lat is None or lon is None:
        return None

    if category == "restaurants":
        subtype = tags.get("amenity", "restaurant")
        display_type = subtype.replace("_", " ").title()
    elif category == "guides":
        display_type = "Local Guide"
        if tags.get("guide"):
            display_type = f"{tags.get('guide').replace('_', ' ').title()} Guide"
    else:
        display_type = (
            tags.get("tourism")
            or tags.get("leisure")
            or tags.get("attraction")
            or "Experience"
        ).replace("_", " ").title()

    address_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
    ]
    address = ", ".join(x for x in address_parts if x)

    return {
        "id": f"osm-{element.get('type')}-{element.get('id')}",
        "name": name,
        "type": category,
        "subcategory": display_type,
        "location": address or tags.get("addr:full") or "Location available on map",
        "latitude": lat,
        "longitude": lon,
        "website": tags.get("website") or tags.get("contact:website"),
        "phone": tags.get("phone") or tags.get("contact:phone"),
        "opening_hours": tags.get("opening_hours"),
        "cuisine": tags.get("cuisine"),
        "source": "OpenStreetMap",
        "live": True,
    }


def get_live_ecosystem_places(latitude, longitude, category="all", radius=8000, limit=40):
    category = (category or "all").lower().strip()

    if category == "all":
        categories = ["restaurants", "guides", "experiences"]
    elif category in CATEGORY_QUERIES:
        categories = [category]
    else:
        return {"success": False, "error": "Unsupported ecosystem category."}

    collected = []
    seen = set()

    for selected_category in categories:
        clauses = "".join(
            q.format(radius=radius, lat=latitude, lon=longitude)
            for q in CATEGORY_QUERIES[selected_category]
        )

        query = f"[out:json][timeout:25];({clauses});out center tags;"
        data = None
        last_error = None

        for server in OVERPASS_SERVERS:
            try:
                response = requests.post(
                    server,
                    data=query,
                    headers={"User-Agent": "TravelBytesAI/1.0 tourism project"},
                    timeout=35,
                )
                response.raise_for_status()
                data = response.json()
                break
            except requests.RequestException as exc:
                last_error = str(exc)

        if data is None:
            continue

        for element in data.get("elements", []):
            item = _clean_element(element, selected_category)
            if not item:
                continue

            key = (
                item["name"].lower(),
                round(float(item["latitude"]), 5),
                round(float(item["longitude"]), 5),
            )
            if key in seen:
                continue
            seen.add(key)
            collected.append(item)

    return {
        "success": True,
        "category": category,
        "count": min(len(collected), limit),
        "items": collected[:limit],
    }