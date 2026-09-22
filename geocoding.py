import requests


OPEN_METEO_URL = "https://geocoding-api.open-meteo.com/v1/search"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": "TravelBytesAI/1.0 (tourism project)"
}


def get_coordinates(city):
    """
    Converts a city or tourist place name into
    latitude and longitude.

    Strategy:
    1. Try OpenStreetMap Nominatim first.
       This is useful for tourist places / POIs.
    2. If not found, try Open-Meteo.
       This is useful for cities and general locations.
    """

    if not city:
        return None

    city = city.strip()

    # -------------------------------------------------
    # STEP 1: OpenStreetMap Nominatim
    # -------------------------------------------------

    try:

        params = {
            "q": city,
            "format": "json",
            "limit": 1
        }

        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data:

            location = data[0]

            return {
                "name": location.get("display_name"),
                "latitude": float(location["lat"]),
                "longitude": float(location["lon"]),
                "country": None,
                "admin1": None
            }

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError
    ):
        pass


    # -------------------------------------------------
    # STEP 2: Open-Meteo Geocoding
    # -------------------------------------------------

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    try:

        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        if not results:
            return None

        location = results[0]

        return {
            "name": location.get("name"),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "country": location.get("country"),
            "admin1": location.get("admin1")
        }

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError
    ):
        return None