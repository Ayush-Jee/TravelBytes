import time
import requests


# ============================================================
# TRAVELBYTES AI - LIVE PLACES API
# OpenStreetMap + Overpass + Nominatim
# ============================================================

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"

DEFAULT_RADIUS = 8000
MAX_RESULTS = 60

USER_AGENT = "TravelBytesAI/1.0 (tourism project)"

# Small in-memory cache.
# This reduces repeated requests to public OSM services.
CACHE_TTL_SECONDS = 600
_PLACES_CACHE = {}


# ============================================================
# TOURISM QUERY GROUPS
# ============================================================

TOURISM_QUERY_GROUPS = [

    # Group 1: common tourism places
    [
        'nwr["tourism"="attraction"](around:{radius},{lat},{lon});',
        'nwr["tourism"="museum"](around:{radius},{lat},{lon});',
        'nwr["tourism"="gallery"](around:{radius},{lat},{lon});',
        'nwr["tourism"="viewpoint"](around:{radius},{lat},{lon});',
        'nwr["tourism"="theme_park"](around:{radius},{lat},{lon});',
        'nwr["tourism"="zoo"](around:{radius},{lat},{lon});',
        'nwr["tourism"="aquarium"](around:{radius},{lat},{lon});',
    ],

    # Group 2: heritage / historic / outdoor
    [
        'nwr["historic"="monument"](around:{radius},{lat},{lon});',
        'nwr["historic"="castle"](around:{radius},{lat},{lon});',
        'nwr["historic"="palace"](around:{radius},{lat},{lon});',
        'nwr["historic"="fort"](around:{radius},{lat},{lon});',
        'nwr["historic"="archaeological_site"](around:{radius},{lat},{lon});',
        'nwr["leisure"="park"](around:{radius},{lat},{lon});',
    ],
]


# ============================================================
# NOMINATIM FALLBACK TYPES
# ============================================================

NOMINATIM_TYPES = [
    "museum",
    "tourist attraction",
    "palace",
    "fort",
    "monument",
    "park",
    "zoo",
    "gallery",
]


# ============================================================
# FILTERS
# ============================================================

UNWANTED_NAME_WORDS = {
    "pharmacy",
    "restaurant",
    "bar",
    "cafe",
    "hotel",
    "hostel",
    "shop",
    "store",
    "supermarket",
    "market",
    "bakery",
}

UNWANTED_HISTORIC = {
    "tomb",
    "memorial",
    "wayside_cross",
    "fountain",
    "city_gate",
}


# ============================================================
# CACHE
# ============================================================

def _cache_key(latitude, longitude, radius, limit):
    return (
        round(float(latitude), 4),
        round(float(longitude), 4),
        round(float(radius)),
        int(limit),
    )


def _get_cached_places(latitude, longitude, radius, limit):
    key = _cache_key(latitude, longitude, radius, limit)

    cached = _PLACES_CACHE.get(key)

    if not cached:
        return None

    timestamp = cached.get("timestamp", 0)

    if time.time() - timestamp > CACHE_TTL_SECONDS:
        _PLACES_CACHE.pop(key, None)
        return None

    return cached.get("data")


def _save_cached_places(latitude, longitude, radius, limit, data):
    key = _cache_key(latitude, longitude, radius, limit)

    _PLACES_CACHE[key] = {
        "timestamp": time.time(),
        "data": data,
    }


# ============================================================
# COORDINATES
# ============================================================

def _coordinates(element):

    if element.get("type") == "node":
        return (
            element.get("lat"),
            element.get("lon"),
        )

    center = element.get("center") or {}

    return (
        center.get("lat"),
        center.get("lon"),
    )


# ============================================================
# NAME CLEANING
# ============================================================

def _clean_name(name):
    return " ".join(
        str(name or "").split()
    ).strip()


# ============================================================
# BASE PLACE OBJECT
# ============================================================

def _base_item(
    name,
    latitude,
    longitude,
    category="Tourism",
    tags=None,
    source="OpenStreetMap",
):

    tags = tags or {}

    lower_name = name.lower()

    # Remove obvious non-tourism places.
    if any(
        word in lower_name
        for word in UNWANTED_NAME_WORDS
    ):
        return None

    historic = str(
        tags.get("historic") or ""
    ).lower()

    if historic in UNWANTED_HISTORIC:
        return None

    tag_values = []

    for key in (
        "tourism",
        "historic",
        "leisure",
        "amenity",
        "cuisine",
    ):

        value = tags.get(key)

        if value:
            tag_values.append(
                str(value).replace("_", " ")
            )

    tourism_type = str(
        tags.get("tourism") or ""
    ).lower()

    indoor = tourism_type in {
        "museum",
        "gallery",
        "aquarium",
    }

    address_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
    ]

    address = ", ".join(
        str(x).strip()
        for x in address_parts
        if x
    )

    return {
        "id": (
            f"osm-"
            f"{source.lower().replace(' ', '-')}-"
            f"{round(float(latitude), 6)}-"
            f"{round(float(longitude), 6)}"
        ),

        "name": name,

        "city": tags.get("addr:city"),

        "category": str(
            category
        ).replace("_", " ").title(),

        # Unknown cost MUST remain unknown.
        "cost": None,

        # OSM generally doesn't provide reliable visit duration.
        "duration": 2,

        # Don't invent ratings.
        "rating": None,

        "indoor": indoor,

        "tags": ",".join(tag_values),

        "latitude": latitude,
        "longitude": longitude,

        "website": (
            tags.get("website")
            or tags.get("contact:website")
        ),

        "address": (
            address
            or tags.get("addr:full")
            or tags.get("display_name")
        ),

        "opening_hours": tags.get(
            "opening_hours"
        ),

        "description": tags.get(
            "description"
        ),

        "source": source,

        "live": True,
    }


# ============================================================
# CLEAN OVERPASS ELEMENT
# ============================================================

def _clean_element(element):

    tags = element.get("tags") or {}

    name = _clean_name(
        tags.get("name")
    )

    if not name:
        return None

    latitude, longitude = _coordinates(
        element
    )

    if (
        latitude is None
        or longitude is None
    ):
        return None

    category = (
        tags.get("tourism")
        or tags.get("historic")
        or tags.get("leisure")
        or tags.get("attraction")
        or "tourism"
    )

    return _base_item(
        name,
        latitude,
        longitude,
        category,
        tags,
        "OpenStreetMap",
    )


# ============================================================
# BUILD OVERPASS QUERY
# ============================================================

def _build_query(
    latitude,
    longitude,
    radius,
    query_group,
    timeout_seconds,
):

    clauses = "".join(
        q.format(
            radius=radius,
            lat=latitude,
            lon=longitude,
        )
        for q in query_group
    )

    return (
        f"[out:json]"
        f"[timeout:{timeout_seconds}];"
        f"({clauses});"
        f"out center tags;"
    )


# ============================================================
# SINGLE OVERPASS REQUEST
# ============================================================

def _request_single_overpass(
    server,
    query,
    timeout_seconds,
):

    try:

        response = requests.post(
            server,

            data={
                "data": query
            },

            headers={
                "User-Agent": USER_AGENT
            },

            timeout=(
                5,
                timeout_seconds,
            ),
        )

        response.raise_for_status()

        return response.json(), None

    except (
        requests.Timeout,
        requests.ConnectionError,
        requests.RequestException,
        ValueError,
    ) as exc:

        return None, (
            f"{server}: {exc}"
        )


# ============================================================
# OVERPASS REQUEST WITH SERVER FALLBACK
# ============================================================

def _request_overpass(
    query,
    timeout_seconds,
):

    errors = []

    for server in OVERPASS_SERVERS:

        data, error = (
            _request_single_overpass(
                server,
                query,
                timeout_seconds,
            )
        )

        if data is not None:

            return data, errors

        if error:
            errors.append(error)

        # Small delay before trying next
        # public server.
        time.sleep(0.2)

    return None, errors


# ============================================================
# DEDUPLICATE + SORT
# ============================================================

def _dedupe_and_sort(
    places,
    limit,
):

    seen = set()
    unique = []

    for place in places:

        try:

            key = (
                place["name"]
                .strip()
                .lower(),

                round(
                    float(
                        place["latitude"]
                    ),
                    5,
                ),

                round(
                    float(
                        place["longitude"]
                    ),
                    5,
                ),
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            continue

        if key in seen:
            continue

        seen.add(key)
        unique.append(place)

    # Prefer richer OSM records.
    unique.sort(
        key=lambda item: (
            -sum(
                bool(
                    item.get(field)
                )
                for field in (
                    "website",
                    "address",
                    "opening_hours",
                    "description",
                )
            ),

            item["name"].lower(),
        )
    )

    return unique[:int(limit)]


# ============================================================
# REVERSE GEOCODING
# ============================================================

def _reverse_city(
    latitude,
    longitude,
):

    try:

        response = requests.get(
            NOMINATIM_REVERSE_URL,

            params={
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "zoom": 10,
                "addressdetails": 1,
            },

            headers={
                "User-Agent": USER_AGENT
            },

            timeout=(
                5,
                8,
            ),
        )

        response.raise_for_status()

        address = (
            response.json().get(
                "address"
            )
            or {}
        )

        return (
            address.get("city")
            or address.get("town")
            or address.get("municipality")
            or address.get("county")
        )

    except (
        requests.Timeout,
        requests.ConnectionError,
        requests.RequestException,
        ValueError,
    ):

        return None


# ============================================================
# NOMINATIM FALLBACK
# ============================================================

def _nominatim_fallback(
    city,
    latitude,
    longitude,
    limit,
):

    if not city:
        return None

    places = []
    errors = []

    for place_type in NOMINATIM_TYPES:

        try:

            response = requests.get(
                NOMINATIM_URL,

                params={
                    "q": (
                        f"{place_type}, "
                        f"{city}"
                    ),

                    "format": "jsonv2",

                    "limit": 8,

                    "addressdetails": 1,

                    "dedupe": 1,

                    "extratags": 1,

                    "namedetails": 1,
                },

                headers={
                    "User-Agent": USER_AGENT
                },

                timeout=(
                    5,
                    10,
                ),
            )

            response.raise_for_status()

            results = response.json()

            for item in results:

                namedetails = (
                    item.get(
                        "namedetails"
                    )
                    or {}
                )

                display_name = (
                    item.get(
                        "display_name"
                    )
                    or ""
                )

                name = _clean_name(
                    namedetails.get("name")
                    or display_name.split(
                        ","
                    )[0]
                )

                if not name:
                    continue

                lat = item.get("lat")
                lon = item.get("lon")

                if (
                    lat is None
                    or lon is None
                ):
                    continue

                extra = (
                    item.get(
                        "extratags"
                    )
                    or {}
                )

                tags = {
                    "display_name":
                        display_name,

                    "tourism":
                        extra.get(
                            "tourism"
                        ),

                    "historic":
                        extra.get(
                            "historic"
                        ),

                    "website":
                        extra.get(
                            "website"
                        )
                        or extra.get(
                            "contact:website"
                        ),

                    "opening_hours":
                        extra.get(
                            "opening_hours"
                        ),

                    "description":
                        extra.get(
                            "description"
                        ),
                }

                place = _base_item(
                    name,
                    float(lat),
                    float(lon),
                    place_type,
                    tags,
                    "OpenStreetMap / Nominatim",
                )

                if place:
                    places.append(place)

            # Respect public Nominatim usage.
            time.sleep(1.0)

            if (
                len(
                    _dedupe_and_sort(
                        places,
                        limit,
                    )
                )
                >= limit
            ):
                break

        except (
            requests.Timeout,
            requests.ConnectionError,
            requests.RequestException,
            ValueError,
        ) as exc:

            errors.append(
                f"Nominatim "
                f"{place_type}: {exc}"
            )

    result = _dedupe_and_sort(
        places,
        limit,
    )

    if result:

        return {
            "success": True,
            "count": len(result),
            "places": result,

            "source":
                "OpenStreetMap / Nominatim fallback",

            "live": True,

            "fallback": True,

            "radius_km": None,
        }

    return {
        "success": False,

        "error":
            "Live OpenStreetMap tourism data "
            "is temporarily unavailable.",

        "details": errors[-3:],

        "places": [],

        "count": 0,

        "source":
            "OpenStreetMap",

        "live": False,
    }


# ============================================================
# MAIN FUNCTION
# ============================================================

def get_tourist_places(
    latitude,
    longitude,
    radius=DEFAULT_RADIUS,
    limit=MAX_RESULTS,
    city=None,
):

    """
    Fetch live tourism places.

    Flow:

    1. Check local short-term cache.
    2. Try smaller Overpass queries.
    3. Try multiple Overpass servers.
    4. If Overpass fails, use Nominatim.
    5. Return only live OSM data.
    """

    try:

        latitude = float(latitude)
        longitude = float(longitude)

    except (
        TypeError,
        ValueError,
    ):

        return {
            "success": False,
            "error":
                "Invalid latitude or longitude.",
            "places": [],
            "count": 0,
        }

    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    cached = _get_cached_places(
        latitude,
        longitude,
        radius,
        limit,
    )

    if cached:

        cached_copy = dict(cached)

        cached_copy["cached"] = True

        return cached_copy

    # --------------------------------------------------------
    # OVERPASS
    # --------------------------------------------------------

    attempts = [
        (
            min(
                float(radius),
                5000,
            ),
            10,
        ),

        (
            3000,
            8,
        ),
    ]

    errors = []

    collected_places = []

    for (
        attempt_radius,
        timeout_seconds,
    ) in attempts:

        for query_group in (
            TOURISM_QUERY_GROUPS
        ):

            query = _build_query(
                latitude,
                longitude,
                attempt_radius,
                query_group,
                timeout_seconds,
            )

            data, request_errors = (
                _request_overpass(
                    query,
                    timeout_seconds,
                )
            )

            if request_errors:

                errors.extend(
                    request_errors
                )

            if not data:

                continue

            elements = data.get(
                "elements",
                [],
            )

            for element in elements:

                place = _clean_element(
                    element
                )

                if place:

                    collected_places.append(
                        place
                    )

            collected_places = (
                _dedupe_and_sort(
                    collected_places,
                    limit,
                )
            )

            # If enough places have been
            # received, stop calling public APIs.
            if len(
                collected_places
            ) >= min(
                limit,
                20,
            ):

                result = {
                    "success": True,

                    "count":
                        len(
                            collected_places
                        ),

                    "places":
                        collected_places,

                    "source":
                        "OpenStreetMap / Overpass",

                    "live": True,

                    "fallback": False,

                    "cached": False,

                    "radius_km":
                        round(
                            attempt_radius / 1000,
                            1,
                        ),
                }

                _save_cached_places(
                    latitude,
                    longitude,
                    radius,
                    limit,
                    result,
                )

                return result

    # --------------------------------------------------------
    # PARTIAL OVERPASS RESULT
    # --------------------------------------------------------

    if collected_places:

        result = {
            "success": True,

            "count":
                len(
                    collected_places
                ),

            "places":
                collected_places,

            "source":
                "OpenStreetMap / Overpass",

            "live": True,

            "fallback": False,

            "cached": False,

            "partial": True,

            "radius_km":
                round(
                    min(
                        float(radius),
                        5000,
                    ) / 1000,
                    1,
                ),
        }

        _save_cached_places(
            latitude,
            longitude,
            radius,
            limit,
            result,
        )

        return result

    # --------------------------------------------------------
    # NOMINATIM FALLBACK
    # --------------------------------------------------------

    fallback_city = (
        city
        or _reverse_city(
            latitude,
            longitude,
        )
    )

    if fallback_city:

        fallback = (
            _nominatim_fallback(
                fallback_city,
                latitude,
                longitude,
                limit,
            )
        )

        if fallback.get(
            "success"
        ):

            _save_cached_places(
                latitude,
                longitude,
                radius,
                limit,
                fallback,
            )

            return fallback

    # --------------------------------------------------------
    # FINAL FAILURE
    # --------------------------------------------------------

    return {
        "success": False,

        "error":
            "Live OpenStreetMap tourism data "
            "is temporarily unavailable. "
            "Please try again shortly.",

        "details":
            errors[-3:],

        "places": [],

        "count": 0,

        "source":
            "OpenStreetMap",

        "live": False,

        "fallback": False,
    }