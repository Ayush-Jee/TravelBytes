import requests


OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


def get_route(
    start_latitude,
    start_longitude,
    end_latitude,
    end_longitude
):
    """
    Get road distance and travel time
    between two coordinates using OSRM.
    """

    coordinates = (
        f"{start_longitude},{start_latitude};"
        f"{end_longitude},{end_latitude}"
    )

    url = f"{OSRM_URL}/{coordinates}"

    params = {
        "overview": "false"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            return None

        routes = data.get(
            "routes",
            []
        )

        if not routes:
            return None

        route = routes[0]

        distance_meters = route.get(
            "distance",
            0
        )

        duration_seconds = route.get(
            "duration",
            0
        )

        return {
            "distance_km": round(
                distance_meters / 1000,
                2
            ),

            "duration_minutes": round(
                duration_seconds / 60,
                1
            )
        }

    except requests.RequestException:
        return None