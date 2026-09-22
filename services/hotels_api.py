import os
import time
import hashlib
import requests

from dotenv import load_dotenv


# ========================================
# ENVIRONMENT
# ========================================

load_dotenv()


HOTELBEDS_API_KEY = os.getenv(
    "HOTELBEDS_API_KEY"
)

HOTELBEDS_SECRET = os.getenv(
    "HOTELBEDS_SECRET"
)


# Hotelbeds Evaluation/Test environment
BASE_URL = (
    "https://api.test.hotelbeds.com"
)


# Destination resolver cache
_destination_cache = {}


# ========================================
# HOTELBEDS AUTHENTICATION
# ========================================

def generate_signature():
    """
    Generate Hotelbeds X-Signature.

    Formula:

    SHA256(
        API_KEY
        + SECRET
        + CURRENT_TIMESTAMP
    )
    """

    if not HOTELBEDS_API_KEY:
        raise ValueError(
            "HOTELBEDS_API_KEY is missing in .env"
        )

    if not HOTELBEDS_SECRET:
        raise ValueError(
            "HOTELBEDS_SECRET is missing in .env"
        )

    timestamp = str(
        int(time.time())
    )

    raw_string = (
        HOTELBEDS_API_KEY
        + HOTELBEDS_SECRET
        + timestamp
    )

    signature = hashlib.sha256(
        raw_string.encode("utf-8")
    ).hexdigest()

    return signature


def get_headers():
    """
    Common Hotelbeds authentication headers.
    """

    return {
        "Accept": "application/json",
        "Api-key": HOTELBEDS_API_KEY,
        "X-Signature": generate_signature()
    }


# ========================================
# HOTELBEDS CONNECTION TEST
# ========================================

def test_hotelbeds_connection():
    """
    Test Hotelbeds API credentials.
    """

    if not HOTELBEDS_API_KEY:
        return {
            "success": False,
            "error":
                "HOTELBEDS_API_KEY missing in .env"
        }

    if not HOTELBEDS_SECRET:
        return {
            "success": False,
            "error":
                "HOTELBEDS_SECRET missing in .env"
        }

    url = (
        f"{BASE_URL}"
        "/hotel-api/1.0/status"
    )

    try:

        response = requests.get(
            url,
            headers=get_headers(),
            timeout=15
        )

        return {
            "success": response.ok,
            "status_code":
                response.status_code,
            "response":
                response.text
        }

    except requests.RequestException as e:

        return {
            "success": False,
            "error": str(e)
        }


# ========================================
# HOTEL AVAILABILITY
# ========================================

def search_hotel_availability(
    check_in,
    check_out,
    adults=2,
    children=0,
    rooms=1,
    hotel_codes=None
):
    """
    Search Hotelbeds hotel availability
    and rates.

    hotel_codes:
        Optional list of Hotelbeds hotel IDs.

    Example:

        [137, 149, 186]
    """

    if not HOTELBEDS_API_KEY:

        return {
            "success": False,
            "error":
                "HOTELBEDS_API_KEY missing in .env",
            "hotels": []
        }


    if not HOTELBEDS_SECRET:

        return {
            "success": False,
            "error":
                "HOTELBEDS_SECRET missing in .env",
            "hotels": []
        }


    if not check_in or not check_out:

        return {
            "success": False,
            "error":
                "check_in and check_out are required.",
            "hotels": []
        }


    url = (
        f"{BASE_URL}"
        "/hotel-api/1.0/hotels"
    )


    payload = {

        "stay": {

            "checkIn":
                check_in,

            "checkOut":
                check_out

        },

        "occupancies": [

            {

                "rooms":
                    rooms,

                "adults":
                    adults,

                "children":
                    children

            }

        ]

    }


    # Add hotel codes only when provided
    if hotel_codes:

        payload["hotels"] = {

            "hotel":
                hotel_codes

        }


    try:

        response = requests.post(

            url,

            headers={

                **get_headers(),

                "Content-Type":
                    "application/json"

            },

            json=payload,

            timeout=30

        )

        response.raise_for_status()


        return {

            "success": True,

            "status_code":
                response.status_code,

            "data":
                response.json()

        }


    except requests.RequestException as e:

        return {

            "success": False,

            "status_code":
                getattr(

                    getattr(
                        e,
                        "response",
                        None
                    ),

                    "status_code",

                    None

                ),

            "error":
                str(e),

            "hotels": []

        }


# ========================================
# CLEAN HOTEL AVAILABILITY
# ========================================

def get_clean_hotel_availability(
    check_in,
    check_out,
    adults=2,
    children=0,
    rooms=1,
    hotel_codes=None
):
    """
    Convert raw Hotelbeds availability
    response into clean application data.
    """

    result = search_hotel_availability(

        check_in=check_in,

        check_out=check_out,

        adults=adults,

        children=children,

        rooms=rooms,

        hotel_codes=hotel_codes

    )


    if not result.get(
        "success"
    ):

        return result


    data = result.get(
        "data",
        {}
    )


    hotels_data = data.get(
        "hotels",
        {}
    )


    hotels = hotels_data.get(
        "hotels",
        []
    )


    clean_hotels = []


    for hotel in hotels:

        clean_rooms = []


        for room in hotel.get(
            "rooms",
            []
        ):

            clean_rates = []


            for rate in room.get(
                "rates",
                []
            ):

                cancellation = rate.get(

                    "cancellationPolicies",

                    []

                )


                clean_rates.append({

                    "rate_key":
                        rate.get(
                            "rateKey"
                        ),

                    "rate_type":
                        rate.get(
                            "rateType"
                        ),

                    "price":
                        rate.get(
                            "net"
                        ),

                    "currency":
                        hotels_data.get(

                            "currency",

                            hotel.get(
                                "currency"
                            )

                        ),

                    "board_code":
                        rate.get(
                            "boardCode"
                        ),

                    "board_name":
                        rate.get(
                            "boardName"
                        ),

                    "payment_type":
                        rate.get(
                            "paymentType"
                        ),

                    "rooms":
                        rate.get(
                            "rooms"
                        ),

                    "adults":
                        rate.get(
                            "adults"
                        ),

                    "children":
                        rate.get(
                            "children"
                        ),

                    "cancellation_policies":
                        cancellation

                })


            clean_rooms.append({

                "code":
                    room.get(
                        "code"
                    ),

                "name":
                    room.get(
                        "name"
                    ),

                "rates":
                    clean_rates

            })


        clean_hotels.append({

            "code":
                hotel.get(
                    "code"
                ),

            "name":
                hotel.get(
                    "name"
                ),

            "category_code":
                hotel.get(
                    "categoryCode"
                ),

            "category_name":
                hotel.get(
                    "categoryName"
                ),

            "destination_code":
                hotel.get(
                    "destinationCode"
                ),

            "destination_name":
                hotel.get(
                    "destinationName"
                ),

            "zone_name":
                hotel.get(
                    "zoneName"
                ),

            "latitude":
                hotel.get(
                    "latitude"
                ),

            "longitude":
                hotel.get(
                    "longitude"
                ),

            "min_rate":
                hotel.get(
                    "minRate"
                ),

            "max_rate":
                hotel.get(
                    "maxRate"
                ),

            "currency":
                hotel.get(
                    "currency"
                ),

            "rooms":
                clean_rooms

        })


    return {

        "success": True,

        "check_in":
            hotels_data.get(
                "checkIn"
            ),

        "check_out":
            hotels_data.get(
                "checkOut"
            ),

        "total":
            hotels_data.get(
                "total",
                len(clean_hotels)
            ),

        "hotels":
            clean_hotels

    }


# ========================================
# HOTEL CONTENT
# ========================================

def get_hotel_content(
    from_hotel=1,
    to_hotel=10,
    destination_code=None
):
    """
    Fetch hotel content/details from
    Hotelbeds Content API.

    destination_code can be used to
    restrict results to a destination.

    Example:

        BCN -> Barcelona
    """

    url = (
        f"{BASE_URL}"
        "/hotel-content-api/1.0/hotels"
    )


    params = {

        "fields":
            "all",

        "language":
            "ENG",

        "from":
            from_hotel,

        "to":
            to_hotel,

        "useSecondaryLanguage":
            "false"

    }


    if destination_code:

        params[
            "destinationCode"
        ] = str(
            destination_code
        ).strip().upper()


    try:

        response = requests.get(

            url,

            headers=get_headers(),

            params=params,

            timeout=30

        )

        response.raise_for_status()


        data = response.json()


        hotels = data.get(
            "hotels",
            []
        )


        return {

            "success": True,

            "status_code":
                response.status_code,

            "total":
                data.get(
                    "total",
                    len(hotels)
                ),

            "from":
                data.get(
                    "from"
                ),

            "to":
                data.get(
                    "to"
                ),

            "hotels":
                hotels

        }


    except requests.RequestException as e:

        return {

            "success": False,

            "status_code":
                getattr(

                    getattr(
                        e,
                        "response",
                        None
                    ),

                    "status_code",

                    None

                ),

            "error":
                str(e),

            "hotels": []

        }


# ========================================
# HOTEL SUMMARY
# ========================================

def get_hotel_summary(
    from_hotel=1,
    to_hotel=5
):
    """
    Return simplified hotel content.
    """

    result = get_hotel_content(

        from_hotel=
            from_hotel,

        to_hotel=
            to_hotel

    )


    if not result.get(
        "success"
    ):

        return result


    hotels = result.get(
        "hotels",
        []
    )


    summary = []


    for hotel in hotels:

        name = hotel.get(
            "name"
        )


        if isinstance(
            name,
            dict
        ):

            name = name.get(
                "content"
            )


        address = hotel.get(
            "address"
        )


        if isinstance(
            address,
            dict
        ):

            address = address.get(
                "content"
            )


        city = hotel.get(
            "city"
        )


        if isinstance(
            city,
            dict
        ):

            city = city.get(
                "content"
            )


        coordinates = hotel.get(
            "coordinates",
            {}
        )


        if not isinstance(
            coordinates,
            dict
        ):

            coordinates = {}


        summary.append({

            "code":
                hotel.get(
                    "code"
                ),

            "name":
                name,

            "category":
                hotel.get(
                    "categoryName"
                ),

            "destination":
                hotel.get(
                    "destinationName"
                ),

            "country":
                hotel.get(
                    "countryName"
                ),

            "city":
                city,

            "address":
                address,

            "latitude":
                coordinates.get(
                    "latitude"
                ),

            "longitude":
                coordinates.get(
                    "longitude"
                )

        })


    return {

        "success": True,

        "count":
            len(summary),

        "hotels":
            summary

    }


# ========================================
# DESTINATION NAME NORMALIZATION
# ========================================

def _normalize_destination_name(
    value
):
    """
    Normalize destination name for
    case-insensitive comparison.
    """

    if not value:

        return ""


    value = str(
        value
    ).strip().lower()


    return " ".join(
        value.split()
    )


# ========================================
# HOTEL DESTINATION RESOLVER
# ========================================

def search_hotel_destination(
    destination
):
    """
    Resolve a destination/city name to
    Hotelbeds Hotel Content destination code.

    Example:

        Barcelona -> BCN
        Paris -> PAR
        London -> LON

    Destination information is fetched
    dynamically from Hotelbeds Content API.
    No city-to-code mapping is hardcoded.
    """

    if not HOTELBEDS_API_KEY:
        return {
            "success": False,
            "error":
                "HOTELBEDS_API_KEY missing in .env"
        }

    if not HOTELBEDS_SECRET:
        return {
            "success": False,
            "error":
                "HOTELBEDS_SECRET missing in .env"
        }

    if not destination:
        return {
            "success": False,
            "error":
                "Destination is required."
        }

    destination = str(
        destination
    ).strip()

    if not destination:
        return {
            "success": False,
            "error":
                "Destination is required."
        }

    normalized_destination = (
        _normalize_destination_name(
            destination
        )
    )

    # ====================================
    # CACHE
    # ====================================

    if (
        normalized_destination
        in _destination_cache
    ):

        return {
            **_destination_cache[
                normalized_destination
            ],
            "cached": True
        }

    # ====================================
    # HOTEL CONTENT DESTINATION API
    # ====================================

    url = (
        f"{BASE_URL}"
        "/hotel-content-api/1.0/"
        "locations/destinations"
    )

    # Hotelbeds returned 7324 destinations
    # in your test.
    #
    # We fetch them in pages instead of
    # assuming the destination is inside
    # the first 1000 records.

    page_size = 1000

    current_from = 1

    total_destinations = None

    try:

        while True:

            current_to = (
                current_from
                + page_size
                - 1
            )

            params = {

                "fields":
                    "all",

                "language":
                    "ENG",

                "from":
                    current_from,

                "to":
                    current_to,

                "useSecondaryLanguage":
                    "false"

            }

            response = requests.get(

                url,

                headers=get_headers(),

                params=params,

                timeout=30

            )

            response.raise_for_status()

            data = response.json()

            destinations = data.get(
                "destinations",
                []
            )

            # =================================
            # TOTAL DESTINATIONS
            # =================================

            if total_destinations is None:

                total_destinations = data.get(
                    "total"
                )

            # =================================
            # SEARCH CURRENT PAGE
            # =================================

            for item in destinations:

                name = item.get(
                    "name"
                )

                if isinstance(
                    name,
                    dict
                ):

                    name = name.get(
                        "content"
                    )

                code = item.get(
                    "code"
                )

                if not name or not code:
                    continue

                normalized_name = (
                    _normalize_destination_name(
                        name
                    )
                )

                # -----------------------------
                # Exact match
                # -----------------------------

                if (
                    normalized_name
                    ==
                    normalized_destination
                ):

                    result = {

                        "success":
                            True,

                        "code":
                            str(
                                code
                            ).upper(),

                        "name":
                            name,

                        "country_code":
                            item.get(
                                "countryCode"
                            ),

                        "iso_code":
                            item.get(
                                "isoCode"
                            )

                    }

                    _destination_cache[
                        normalized_destination
                    ] = result

                    return result

            # =================================
            # STOP CONDITIONS
            # =================================

            received_count = len(
                destinations
            )

            if received_count == 0:
                break

            # If API tells us total,
            # stop after reaching it.
            if (
                total_destinations
                is not None
                and current_to
                >= int(
                    total_destinations
                )
            ):
                break

            # If fewer records than page size
            # were returned, we reached the end.
            if received_count < page_size:
                break

            current_from += page_size

        # ====================================
        # EXACT MATCH NOT FOUND
        # ====================================

        return {

            "success":
                False,

            "error":
                (
                    "Hotelbeds destination "
                    f"not found for "
                    f"'{destination}'."
                ),

            "destinations_checked":
                total_destinations
                or 0

        }

    except requests.RequestException as e:

        return {

            "success":
                False,

            "status_code":
                getattr(

                    getattr(
                        e,
                        "response",
                        None
                    ),

                    "status_code",

                    None

                ),

            "error":
                str(e)

        }


# ========================================
# BACKWARD COMPATIBILITY
# ========================================

def find_hotel_destination(
    destination_name
):
    """
    Backward-compatible wrapper for
    search_hotel_destination().
    """

    return search_hotel_destination(
        destination_name
    )


# ========================================
# HOTEL CODES BY COORDINATES
# ========================================

def get_hotel_codes_by_coordinates(
    latitude,
    longitude,
    radius_km=25
):
    """
    Find Hotelbeds hotels near a coordinate.

    Note:
    This function intentionally fetches only
    a limited content range.
    """

    content = get_hotel_content(

        from_hotel=1,

        to_hotel=100

    )


    if not content.get(
        "success"
    ):

        return {

            "success": False,

            "error":
                content.get(
                    "error",
                    "Could not fetch hotel content"
                ),

            "hotels": []

        }


    hotels = content.get(
        "hotels",
        []
    )


    nearby_hotels = []


    try:

        latitude = float(
            latitude
        )

        longitude = float(
            longitude
        )

        radius_km = float(
            radius_km
        )

    except (
        TypeError,
        ValueError
    ):

        return {

            "success": False,

            "error":
                "Invalid coordinates",

            "hotels": []

        }


    for hotel in hotels:

        coordinates = hotel.get(
            "coordinates",
            {}
        )


        if not isinstance(
            coordinates,
            dict
        ):

            continue


        hotel_lat = coordinates.get(
            "latitude"
        )

        hotel_lon = coordinates.get(
            "longitude"
        )


        if (
            hotel_lat is None
            or
            hotel_lon is None
        ):

            continue


        try:

            hotel_lat = float(
                hotel_lat
            )

            hotel_lon = float(
                hotel_lon
            )

        except (
            TypeError,
            ValueError
        ):

            continue


        # Approximate geographic distance

        lat_diff = (
            hotel_lat - latitude
        ) * 111


        lon_diff = (
            hotel_lon - longitude
        ) * 111 * 0.7


        distance_km = (
            lat_diff ** 2
            +
            lon_diff ** 2
        ) ** 0.5


        if distance_km > radius_km:

            continue


        name = hotel.get(
            "name"
        )


        if isinstance(
            name,
            dict
        ):

            name = name.get(
                "content"
            )


        address = hotel.get(
            "address"
        )


        if isinstance(
            address,
            dict
        ):

            address = address.get(
                "content"
            )


        nearby_hotels.append({

            "code":
                hotel.get(
                    "code"
                ),

            "name":
                name,

            "latitude":
                hotel_lat,

            "longitude":
                hotel_lon,

            "address":
                address,

            "distance_km":
                round(
                    distance_km,
                    2
                )

        })


    nearby_hotels.sort(

        key=lambda hotel:
        hotel.get(
            "distance_km",
            999
        )

    )


    return {

        "success": True,

        "count":
            len(
                nearby_hotels
            ),

        "hotels":
            nearby_hotels

    }


# ========================================
# LOCAL TESTING
# ========================================

if __name__ == "__main__":

    import json


    print(
        "\n"
        "========================================\n"
        "TravelBytes AI - Hotelbeds Test\n"
        "========================================\n"
    )


    # ------------------------------------
    # 1. Connection
    # ------------------------------------

    print(
        "\nTesting Hotelbeds connection...\n"
    )


    connection = (
        test_hotelbeds_connection()
    )


    print(
        json.dumps(
            connection,
            indent=2
        )
    )


    # ------------------------------------
    # 2. Destination Resolver
    # ------------------------------------

    print(
        "\nTesting destination resolver...\n"
    )


    destination = (
        search_hotel_destination(
            "Barcelona"
        )
    )


    print(
        json.dumps(
            destination,
            indent=2
        )
    )


    # ------------------------------------
    # 3. Hotel Content
    # ------------------------------------

    print(
        "\nTesting hotel content...\n"
    )


    content = get_hotel_content(

        from_hotel=1,

        to_hotel=10,

        destination_code="BCN"

    )


    print(
        json.dumps(
            {

                "success":
                    content.get(
                        "success"
                    ),

                "total":
                    content.get(
                        "total"
                    ),

                "count":
                    len(
                        content.get(
                            "hotels",
                            []
                        )
                    )

            },

            indent=2

        )
    )


    # ------------------------------------
    # 4. Availability
    # ------------------------------------

    if content.get(
        "success"
    ):

        hotels = content.get(
            "hotels",
            []
        )


        hotel_codes = []


        for hotel in hotels:

            code = hotel.get(
                "code"
            )


            if code is None:

                continue


            try:

                hotel_codes.append(
                    int(code)
                )

            except (
                TypeError,
                ValueError
            ):

                continue


        print(
            "\nHotel codes:\n"
        )


        print(
            hotel_codes
        )


        print(
            "\nTesting hotel availability...\n"
        )


        availability = (
            get_clean_hotel_availability(

                check_in=
                    "2026-09-20",

                check_out=
                    "2026-09-23",

                adults=2,

                children=0,

                rooms=1,

                hotel_codes=
                    hotel_codes

            )
        )


        print(

            json.dumps(

                {

                    "success":
                        availability.get(
                            "success"
                        ),

                    "total":
                        availability.get(
                            "total"
                        ),

                    "hotels":
                        availability.get(
                            "hotels",
                            []
                        )

                },

                indent=2

            )

        )


    print(
        "\n"
        "========================================\n"
        "Hotelbeds test completed.\n"
        "========================================\n"
    )