from flask import Flask, render_template, jsonify, request

import math

from dotenv import load_dotenv

load_dotenv()

from database import init_db, get_businesses

from recommendation import (
    recommend_places,
    generate_itinerary,
    recommend_businesses,
    adapt_places_for_weather,
    replan_itinerary_for_weather
)

from geocoding import get_coordinates

from weather import (
    get_weather,
    get_weather_description
)

from routing import get_route

from services.places_api import get_tourist_places

from services.ecosystem_api import get_live_ecosystem_places

from services.emergency_api import get_nearby_emergency_services

from services.hotels_api import (
    get_clean_hotel_availability,
    get_hotel_content,
    search_hotel_destination
)


# ========================================
# SHARED HELPERS
# ========================================

ECOSYSTEM_CATEGORIES = {
    "all",
    "hotels",
    "restaurants",
    "guides",
    "experiences"
}


def normalize_ecosystem_category(value):
    """Normalize frontend category/type names."""

    value = (value or "all").strip().lower()

    aliases = {
        "restaurant": "restaurants",
        "food": "restaurants",
        "guide": "guides",
        "local_guides": "guides",
        "experience": "experiences",
        "attractions": "experiences",
        "places": "experiences",
        "hotel": "hotels",
    }

    return aliases.get(value, value)


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """Return approximate straight-line distance in kilometres."""

    try:
        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)
    except (TypeError, ValueError):
        return None

    radius = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )

    return round(
        radius * 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        ),
        2
    )


def enrich_ecosystem_items(items, destination_coordinates):
    """Add useful UI fields without inventing missing live data."""

    latitude = destination_coordinates.get("latitude")
    longitude = destination_coordinates.get("longitude")

    enriched = []

    for item in items or []:
        item = dict(item)

        distance = haversine_distance_km(
            latitude,
            longitude,
            item.get("latitude"),
            item.get("longitude")
        )

        item["distance_km"] = distance
        item["data_source"] = item.get(
            "source",
            "OpenStreetMap"
        )
        item["live_data"] = bool(
            item.get("live", True)
        )

        enriched.append(item)

    enriched.sort(
        key=lambda x: (
            x.get("distance_km") is None,
            x.get("distance_km")
            if x.get("distance_km") is not None
            else float("inf")
        )
    )

    return enriched


app = Flask(__name__)


# ========================================
# HOME PAGE
# ========================================

@app.route("/")
def home():

    return render_template("index.html")


# ========================================
# HEALTH CHECK
# ========================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "success",
        "message": "TravelBytes AI backend is running!",
        "project": "TravelBytes AI",
        "modules": {
            "live_places": True,
            "weather": True,
            "routing": True,
            "dynamic_replanning": True,
            "live_ecosystem": True,
            "hotelbeds": True
        }
    })


# ========================================
# GEOCODING
# ========================================

@app.route("/api/geocode")
def geocode():

    city = request.args.get(
        "city",
        ""
    ).strip()

    if not city:

        return jsonify({
            "status": "error",
            "message": "City is required."
        }), 400

    coordinates = get_coordinates(city)

    if not coordinates:

        return jsonify({
            "status": "error",
            "message": (
                f"Could not find location for {city}."
            )
        }), 404

    return jsonify({
        "status": "success",
        "location": coordinates
    })


# ========================================
# ROUTING
# ========================================

@app.route("/api/route")
def route_api():

    try:

        start_latitude = float(
            request.args.get("start_lat")
        )

        start_longitude = float(
            request.args.get("start_lon")
        )

        end_latitude = float(
            request.args.get("end_lat")
        )

        end_longitude = float(
            request.args.get("end_lon")
        )

    except (TypeError, ValueError):

        return jsonify({
            "error": "Invalid coordinates"
        }), 400

    route = get_route(
        start_latitude,
        start_longitude,
        end_latitude,
        end_longitude
    )

    if not route:

        return jsonify({
            "error": "Route could not be calculated"
        }), 500

    return jsonify({

        "start": {
            "latitude": start_latitude,
            "longitude": start_longitude
        },

        "end": {
            "latitude": end_latitude,
            "longitude": end_longitude
        },

        "route": route

    })


# ========================================
# WEATHER
# ========================================

@app.route("/api/weather")
def weather():

    latitude = request.args.get("lat")
    longitude = request.args.get("lon")

    if not latitude or not longitude:

        return jsonify({
            "status": "error",
            "message": (
                "Latitude and longitude "
                "are required."
            )
        }), 400

    try:

        latitude = float(latitude)
        longitude = float(longitude)

    except ValueError:

        return jsonify({
            "status": "error",
            "message": "Invalid coordinates."
        }), 400

    weather_data = get_weather(
        latitude,
        longitude
    )

    if not weather_data:

        return jsonify({
            "status": "error",
            "message": (
                "Unable to fetch weather data."
            )
        }), 500

    current = weather_data.get(
        "current",
        {}
    )

    weather_code = current.get(
        "weather_code"
    )

    return jsonify({

        "status": "success",

        "weather": {

            "temperature": current.get(
                "temperature_2m"
            ),

            "wind_speed": current.get(
                "wind_speed_10m"
            ),

            "weather_code": weather_code,

            "description": get_weather_description(
                weather_code
            )

        },

        "daily": weather_data.get(
            "daily",
            {}
        )

    })
    
    
# ========================================
# LIVE EMERGENCY SERVICES
# ========================================

@app.route("/api/emergency")
def emergency_services():

    city = request.args.get(
        "city",
        ""
    ).strip()

    if not city:

        return jsonify({
            "status": "error",
            "message": "City is required."
        }), 400

    # ------------------------------------
    # GET DESTINATION COORDINATES
    # ------------------------------------

    coordinates = get_coordinates(city)

    if not coordinates:

        return jsonify({
            "status": "error",
            "message": (
                f"Could not find coordinates "
                f"for {city}."
            )
        }), 404

    latitude = coordinates.get(
        "latitude"
    )

    longitude = coordinates.get(
        "longitude"
    )

    if (
        latitude is None or
        longitude is None
    ):

        return jsonify({
            "status": "error",
            "message": (
                "Destination coordinates "
                "are unavailable."
            )
        }), 404

    # ------------------------------------
    # GET LIVE EMERGENCY SERVICES
    # ------------------------------------

    result = get_nearby_emergency_services(
        latitude,
        longitude,
        radius=10000,
        limit=30
    )

    if not result.get("success"):

        return jsonify({
            "status": "error",
            "message": (
                "Unable to fetch nearby "
                "emergency services."
            ),
            "error": result.get(
                "error"
            )
        }), 502

    return jsonify({

        "status": "success",

        "city": city,

        "coordinates": coordinates,

        "emergency_number": (
            result.get(
                "fallback_police_emergency"
            )
            or "112"
        ),

        "count": result.get(
            "count",
            0
        ),

        "services": result.get(
            "items",
            []
        ),

        "source": result.get(
            "source",
            "OpenStreetMap / Overpass"
        ),

        "live": result.get(
            "live",
            True
        )
    })


# ========================================
# LIVE TOURIST PLACES
# ========================================

@app.route("/api/places")
def places_api():

    city = request.args.get(
        "city",
        ""
    ).strip()

    if not city:

        return jsonify({
            "status": "error",
            "message": "City is required."
        }), 400

    # --------------------------------
    # GET DESTINATION COORDINATES
    # --------------------------------

    coordinates = get_coordinates(city)

    if not coordinates:

        return jsonify({
            "status": "error",
            "message": (
                f"Could not find coordinates "
                f"for {city}."
            )
        }), 404

    latitude = coordinates["latitude"]
    longitude = coordinates["longitude"]

    # --------------------------------
    # GET LIVE TOURIST PLACES
    # --------------------------------

    result = get_tourist_places(
        latitude,
        longitude
    )

    if not result.get("success"):

        return jsonify({

            "status": "error",

            "message": (
                "Unable to fetch tourism data."
            ),

            "error": result.get("error")

        }), 502

    return jsonify({

        "status": "success",

        "city": city,

        "coordinates": coordinates,

        "count": result.get(
            "count",
            0
        ),

        "places": result.get(
            "places",
            []
        )

    })


# ========================================
# LOCAL BUSINESS RECOMMENDATIONS
# ========================================

@app.route("/api/businesses")
def businesses():

    city = request.args.get(
        "city",
        ""
    ).strip()

    business_type = request.args.get(
        "type"
    )

    interests = request.args.get(
        "interests",
        ""
    ).strip()

    # --------------------------------
    # DATABASE BUSINESSES
    # --------------------------------

    business_list = get_businesses(
        city,
        business_type
    )

    if not business_list:

        return jsonify({

            "status": "success",

            "city": city,

            "type": business_type,

            "businesses": []

        })

    # --------------------------------
    # AI RANKING
    # --------------------------------

    recommended_businesses = recommend_businesses(
        business_list,
        interests
    )

    return jsonify({

        "status": "success",

        "city": city,

        "type": business_type,

        "interests": interests,

        "businesses": recommended_businesses

    })


# ========================================
# ADD ROUTE INFORMATION
# ========================================

def add_route_information(
    places,
    destination_latitude,
    destination_longitude,
    destination
):

    updated_places = []

    for place in places:

        # --------------------------------
        # USE LIVE API COORDINATES FIRST
        # --------------------------------

        place_latitude = place.get(
            "latitude"
        )

        place_longitude = place.get(
            "longitude"
        )

        # --------------------------------
        # FALLBACK TO GEOCODING
        # --------------------------------

        if (
            place_latitude is None
            or
            place_longitude is None
        ):

            place_name = place.get(
                "name",
                ""
            )

            search_location = (
                f"{place_name}, {destination}"
            )

            coordinates = get_coordinates(
                search_location
            )

            if coordinates:

                place_latitude = coordinates.get(
                    "latitude"
                )

                place_longitude = coordinates.get(
                    "longitude"
                )

        # --------------------------------
        # CALCULATE ROUTE
        # --------------------------------

        if (
            place_latitude is not None
            and
            place_longitude is not None
        ):

            route = get_route(

                destination_latitude,
                destination_longitude,

                place_latitude,
                place_longitude

            )

            if route:

                place["distance_km"] = (
                    route.get(
                        "distance_km"
                    )
                )

                place["travel_time_minutes"] = (
                    route.get(
                        "duration_minutes"
                    )
                )

            else:

                place["distance_km"] = None

                place["travel_time_minutes"] = None

        else:

            place["distance_km"] = None

            place["travel_time_minutes"] = None

        updated_places.append(
            place
        )

    return updated_places


# ========================================
# LIVE TOURISM ECOSYSTEM
# ========================================


def _get_ecosystem_response(city, category):
    """Shared implementation for ecosystem endpoints."""

    city = (city or "").strip()
    category = normalize_ecosystem_category(category)

    if not city:
        return {
            "status": "error",
            "message": "City is required."
        }, 400

    if category == "hotels":
        return {
            "status": "error",
            "message": (
                "Hotels use the Hotelbeds live API. "
                "Use /api/hotels for hotel availability."
            ),
            "category": "hotels"
        }, 400

    if category not in {
        "all",
        "restaurants",
        "guides",
        "experiences"
    }:
        return {
            "status": "error",
            "message": "Unsupported ecosystem category.",
            "supported_categories": [
                "all",
                "hotels",
                "restaurants",
                "guides",
                "experiences"
            ]
        }, 400

    coordinates = get_coordinates(city)

    if not coordinates:
        return {
            "status": "error",
            "message": f"Could not find destination: {city}"
        }, 404

    result = get_live_ecosystem_places(
        coordinates["latitude"],
        coordinates["longitude"],
        category=category
    )

    if not result.get("success"):
        return {
            "status": "error",
            "message": result.get(
                "error",
                "Unable to fetch ecosystem data."
            )
        }, 502

    items = enrich_ecosystem_items(
        result.get("items", []),
        coordinates
    )

    return {
        "status": "success",
        "city": city,
        "category": category,
        "coordinates": coordinates,
        "count": len(items),
        "items": items,
        "live": True,
        "source": "OpenStreetMap / Overpass"
    }, 200


@app.route("/api/ecosystem")
def ecosystem():

    city = request.args.get("city", "").strip()

    category = request.args.get(
        "category",
        request.args.get("type", "all")
    )

    response, status_code = _get_ecosystem_response(
        city,
        category
    )

    return jsonify(response), status_code


@app.route("/api/ecosystem/<category>")
def ecosystem_category(category):
    """Convenient route for dashboard category tabs."""

    city = request.args.get("city", "").strip()

    response, status_code = _get_ecosystem_response(
        city,
        category
    )

    return jsonify(response), status_code


# ========================================
# CREATE TRAVEL PLAN
# ========================================

@app.route(
    "/api/plan",
    methods=["POST"]
)
def create_plan():

    try:

        data = request.get_json() or {}

        destination = data.get(
            "destination",
            ""
        ).strip()

        duration = int(
            data.get(
                "duration",
                1
            )
        )

        budget = float(
            data.get(
                "budget",
                0
            )
        )

        interests = data.get(
            "interests",
            ""
        ).strip()

        # --------------------------------
        # VALIDATION
        # --------------------------------

        if not destination:

            return jsonify({
                "status": "error",
                "message": (
                    "Destination is required."
                )
            }), 400

        if duration <= 0:

            return jsonify({
                "status": "error",
                "message": (
                    "Duration must be greater than 0."
                )
            }), 400

        if budget <= 0:

            return jsonify({
                "status": "error",
                "message": (
                    "Budget must be greater than 0."
                )
            }), 400

        # --------------------------------
        # STEP 1:
        # GET DESTINATION COORDINATES
        # --------------------------------

        coordinates = get_coordinates(
            destination
        )

        if not coordinates:

            return jsonify({

                "status": "error",

                "message": (
                    f"Could not find coordinates "
                    f"for {destination}."
                )

            }), 404

        latitude = coordinates[
            "latitude"
        ]

        longitude = coordinates[
            "longitude"
        ]

        # --------------------------------
        # STEP 2:
        # GET LIVE TOURIST PLACES
        # --------------------------------

        places_result = get_tourist_places(

            latitude,
            longitude

        )

        if not places_result.get(
            "success"
        ):

            return jsonify({

                "status": "error",

                "message": (
                    "Live tourism data "
                    "is currently unavailable."
                ),

                "error": places_result.get(
                    "error"
                )

            }), 502

        places = places_result.get(
            "places",
            []
        )

        if not places:

            return jsonify({

                "status": "error",

                "message": (
                    f"No tourist places "
                    f"found for {destination}."
                )

            }), 404

        # --------------------------------
        # STEP 3:
        # GET WEATHER
        # --------------------------------

        weather_data = get_weather(

            latitude,
            longitude

        )

        weather = None

        if weather_data:

            current = weather_data.get(
                "current",
                {}
            )

            weather_code = current.get(
                "weather_code"
            )

            weather = {

                "temperature": current.get(
                    "temperature_2m"
                ),

                "wind_speed": current.get(
                    "wind_speed_10m"
                ),

                "weather_code": weather_code,

                "description": (
                    get_weather_description(
                        weather_code
                    )
                )

            }

        # --------------------------------
        # STEP 4:
        # DISTANCE + TRAVEL TIME
        # --------------------------------

        places = add_route_information(

            places,

            latitude,

            longitude,

            destination

        )

        # --------------------------------
        # STEP 5:
        # AI RECOMMENDATION
        # --------------------------------

        available_hours = 8

        recommended_places = recommend_places(

            places,

            interests,

            budget,

            available_hours,

            weather

        )

        # --------------------------------
        # STEP 6:
        # GENERATE ITINERARY
        # --------------------------------

        itinerary = generate_itinerary(

            recommended_places,

            duration,

            available_hours

        )

        # --------------------------------
        # STEP 7:
        # RESPONSE
        # --------------------------------

        return jsonify({

            "status": "success",

            "destination": destination,

            "duration": duration,

            "budget": budget,

            "interests": interests,

            "coordinates": {

                "latitude": latitude,

                "longitude": longitude

            },

            "weather": weather,

            "places": recommended_places,

            "itinerary": itinerary

        })

    except ValueError as e:

        return jsonify({

            "status": "error",

            "message": (
                "Invalid duration or budget."
            ),

            "error": str(e)

        }), 400

    except Exception as e:

        print(
            "PLAN ERROR:",
            e
        )

        return jsonify({

            "status": "error",

            "message": (
                "Could not create travel plan."
            ),

            "error": str(e)

        }), 500


# ========================================
# REPLAN TRIP
# ========================================

@app.route(
    "/api/replan",
    methods=["POST"]
)
def replan_trip():

    try:

        data = request.get_json() or {}

        destination = data.get(
            "destination",
            ""
        ).strip()

        duration = int(
            data.get(
                "duration",
                1
            )
        )

        budget = float(
            data.get(
                "budget",
                0
            )
        )

        interests = data.get(
            "interests",
            ""
        ).strip()

        previous_itinerary = data.get(
            "itinerary",
            []
        )

        # --------------------------------
        # VALIDATION
        # --------------------------------

        if not destination:

            return jsonify({

                "status": "error",

                "message": (
                    "Destination is required."
                )

            }), 400

        # --------------------------------
        # STEP 1:
        # DESTINATION COORDINATES
        # --------------------------------

        destination_location = get_coordinates(
            destination
        )

        if not destination_location:

            return jsonify({

                "status": "error",

                "message": (
                    "Could not find destination."
                )

            }), 404

        latitude = destination_location[
            "latitude"
        ]

        longitude = destination_location[
            "longitude"
        ]

        # --------------------------------
        # STEP 2:
        # LATEST WEATHER
        # --------------------------------

        weather_data = get_weather(

            latitude,
            longitude

        )

        if not weather_data:

            return jsonify({

                "status": "error",

                "message": (
                    "Weather data unavailable."
                )

            }), 503

        current = weather_data.get(
            "current",
            {}
        )

        weather_code = current.get(
            "weather_code"
        )

        current_weather = {

            "temperature": current.get(
                "temperature_2m"
            ),

            "wind_speed": current.get(
                "wind_speed_10m"
            ),

            "weather_code": weather_code,

            "description": (
                get_weather_description(
                    weather_code
                )
            )

        }

        # --------------------------------
        # STEP 3:
        # LIVE TOURIST PLACES
        # --------------------------------

        places_result = get_tourist_places(

            latitude,
            longitude

        )

        if not places_result.get(
            "success"
        ):

            return jsonify({

                "status": "error",

                "message": (
                    "Live tourism data "
                    "is currently unavailable."
                ),

                "error": places_result.get(
                    "error"
                )

            }), 502

        places = places_result.get(
            "places",
            []
        )

        if not places:

            return jsonify({

                "status": "error",

                "message": (
                    "No tourist places found."
                )

            }), 404

        # --------------------------------
        # STEP 4:
        # DISTANCE + TRAVEL TIME
        # --------------------------------

        places = add_route_information(

            places,

            latitude,

            longitude,

            destination

        )

        # --------------------------------
        # STEP 5:
        # WEATHER ADAPTATION
        # --------------------------------

        places = adapt_places_for_weather(

            places,

            current_weather

        )

        # --------------------------------
        # STEP 6:
        # AVAILABLE HOURS
        # --------------------------------

        available_hours = 8

        # --------------------------------
        # STEP 7:
        # RE-RANK PLACES
        # --------------------------------

        recommended_places = recommend_places(

            places,

            interests,

            budget,

            available_hours,

            current_weather

        )

        # --------------------------------
        # STEP 8:
        # ACTUAL REPLANNING
        # --------------------------------

        itinerary = replan_itinerary_for_weather(

            previous_itinerary,

            recommended_places,

            current_weather

        )

        # --------------------------------
        # STEP 9:
        # RESPONSE
        # --------------------------------

        return jsonify({

            "status": "success",

            "message": (
                "Trip replanned using "
                "latest conditions."
            ),

            "destination": destination,

            "duration": duration,

            "budget": budget,

            "interests": interests,

            "weather": current_weather,

            "places": recommended_places,

            "itinerary": itinerary

        })

    except ValueError as e:

        return jsonify({

            "status": "error",

            "message": (
                "Invalid duration or budget."
            ),

            "error": str(e)

        }), 400

    except Exception as e:

        print(
            "REPLAN ERROR:",
            e
        )

        return jsonify({

            "status": "error",

            "message": (
                "Could not replan the trip."
            ),

            "error": str(e)

        }), 500


# ========================================
# HOTEL AVAILABILITY
# ========================================

@app.route(
    "/api/hotels",
    methods=["POST"]
)
def hotels():

    try:

        data = request.get_json() or {}


        # ====================================
        # BASIC INPUT
        # ====================================

        destination = str(
            data.get(
                "destination",
                ""
            )
        ).strip()


        check_in = data.get(
            "check_in"
        )

        check_out = data.get(
            "check_out"
        )


        # ====================================
        # OCCUPANCY
        # ====================================

        try:

            adults = int(
                data.get(
                    "adults",
                    2
                )
            )

            children = int(
                data.get(
                    "children",
                    0
                )
            )

            rooms = int(
                data.get(
                    "rooms",
                    1
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({

                "status": "error",

                "message":
                    "Invalid hotel occupancy values."

            }), 400


        # ====================================
        # VALIDATION
        # ====================================

        if not destination:

            return jsonify({

                "status": "error",

                "message":
                    "Destination is required."

            }), 400


        if not check_in or not check_out:

            return jsonify({

                "status": "error",

                "message":
                    (
                        "Check-in and check-out "
                        "dates are required."
                    )

            }), 400


        if adults <= 0:

            return jsonify({

                "status": "error",

                "message":
                    "Adults must be greater than 0."

            }), 400


        if children < 0:

            return jsonify({

                "status": "error",

                "message":
                    "Children cannot be negative."

            }), 400


        if rooms <= 0:

            return jsonify({

                "status": "error",

                "message":
                    "Rooms must be greater than 0."

            }), 400


        # ====================================
        # DESTINATION RESOLUTION
        # ====================================
        # Frontend may send a previously resolved Hotelbeds code.
        # This avoids an unnecessary resolver request and is especially
        # useful with evaluation quotas. If no code is supplied, resolve
        # the destination normally.

        supplied_destination_code = str(
            data.get("destination_code", "")
        ).strip().upper()

        if supplied_destination_code:

            destination_code = supplied_destination_code

            destination_result = {
                "success": True,
                "code": destination_code,
                "name": destination,
                "country_code": None
            }

        else:

            destination_result = (
                search_hotel_destination(
                    destination
                )
            )

            if not destination_result.get(
                "success"
            ):

                return jsonify({

                    "status": "error",

                    "message":
                        destination_result.get(
                            "error",
                            (
                                "Unable to resolve "
                                "hotel destination."
                            )
                        ),

                    "destination":
                        destination

                }), 400

            destination_code = str(
                destination_result.get(
                    "code",
                    ""
                )
            ).strip().upper()


        if not destination_code:

            return jsonify({

                "status": "error",

                "message":
                    (
                        "Hotelbeds destination "
                        "code could not be resolved."
                    ),

                "destination":
                    destination

            }), 400


        # ====================================
        # FETCH HOTEL CONTENT
        # ====================================

        content_result = get_hotel_content(

            from_hotel=1,

            to_hotel=10,

            destination_code=
                destination_code

        )


        if not content_result.get(
            "success"
        ):

            return jsonify({

                "status": "error",

                "message":
                    content_result.get(
                        "error",
                        (
                            "Unable to fetch "
                            "hotel content."
                        )
                    )

            }), 502


        content_hotels = (
            content_result.get(
                "hotels",
                []
            )
        )


        if not content_hotels:

            return jsonify({

                "status": "success",

                "destination":
                    destination,

                "destination_code":
                    destination_code,

                "destination_name":
                    destination_result.get(
                        "name",
                        destination
                    ),

                "check_in":
                    check_in,

                "check_out":
                    check_out,

                "total": 0,

                "hotels": []

            })


        # ====================================
        # EXTRACT HOTEL CODES
        # ====================================

        hotel_codes = []


        for hotel in content_hotels:

            code = hotel.get(
                "code"
            )

            if code is None:
                continue

            try:

                code = int(
                    code
                )

            except (
                TypeError,
                ValueError
            ):

                continue


            hotel_codes.append(
                code
            )


        if not hotel_codes:

            return jsonify({

                "status": "success",

                "destination":
                    destination,

                "destination_code":
                    destination_code,

                "destination_name":
                    destination_result.get(
                        "name",
                        destination
                    ),

                "check_in":
                    check_in,

                "check_out":
                    check_out,

                "total": 0,

                "hotels": []

            })


        # ====================================
        # LIVE AVAILABILITY
        # ====================================

        availability_result = (
            get_clean_hotel_availability(

                check_in=check_in,

                check_out=check_out,

                adults=adults,

                children=children,

                rooms=rooms,

                hotel_codes=
                    hotel_codes

            )
        )


        if not availability_result.get(
            "success"
        ):

            return jsonify({

                "status": "error",

                "message":
                    availability_result.get(
                        "error",
                        (
                            "Unable to fetch "
                            "hotel availability."
                        )
                    )

            }), 502


        # ====================================
        # CONTENT LOOKUP
        # ====================================

        content_by_code = {}


        for hotel in content_hotels:

            code = hotel.get(
                "code"
            )

            if code is not None:

                content_by_code[
                    str(code)
                ] = hotel


        # ====================================
        # ENRICH HOTELS
        # ====================================

        enriched_hotels = []


        for hotel in (
            availability_result.get(
                "hotels",
                []
            )
        ):

            hotel_code = hotel.get(
                "code"
            )


            content = (
                content_by_code.get(
                    str(hotel_code),
                    {}
                )
            )


            # --------------------------------
            # NAME
            # --------------------------------

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


            content_name = (
                content.get(
                    "name"
                )
            )

            if isinstance(
                content_name,
                dict
            ):

                content_name = (
                    content_name.get(
                        "content"
                    )
                )


            if not name:

                name = content_name


            # --------------------------------
            # ADDRESS
            # --------------------------------

            address = (
                content.get(
                    "address"
                )
            )

            if isinstance(
                address,
                dict
            ):

                address = address.get(
                    "content"
                )


            # --------------------------------
            # CITY
            # --------------------------------

            city = (
                content.get(
                    "city"
                )
            )

            if isinstance(
                city,
                dict
            ):

                city = city.get(
                    "content"
                )


            # --------------------------------
            # COORDINATES
            # --------------------------------

            coordinates = (
                content.get(
                    "coordinates",
                    {}
                )
            )


            enriched_hotel = {

                **hotel,

                "name":
                    name,

                "address":
                    address,

                "city":
                    city,

                "country_code":
                    content.get(
                        "countryCode"
                    ),

                "destination_code":
                    (
                        hotel.get(
                            "destination_code"
                        )
                        or
                        content.get(
                            "destinationCode"
                        )
                        or
                        destination_code
                    ),

                "latitude":
                    (
                        hotel.get(
                            "latitude"
                        )
                        or
                        coordinates.get(
                            "latitude"
                        )
                    ),

                "longitude":
                    (
                        hotel.get(
                            "longitude"
                        )
                        or
                        coordinates.get(
                            "longitude"
                        )
                    ),

                "description":
                    content.get(
                        "description"
                    ),

                "category_code":
                    (
                        hotel.get(
                            "category_code"
                        )
                        or
                        content.get(
                            "categoryCode"
                        )
                    ),

                "category_name":
                    (
                        hotel.get(
                            "category_name"
                        )
                        or
                        content.get(
                            "categoryName"
                        )
                    )

            }


            enriched_hotels.append(
                enriched_hotel
            )


        # ====================================
        # FINAL RESPONSE
        # ====================================

        return jsonify({

            "status": "success",

            "destination":
                destination,

            "destination_code":
                destination_code,

            "destination_name":
                destination_result.get(
                    "name",
                    destination
                ),

            "country_code":
                destination_result.get(
                    "country_code"
                ),

            "check_in":
                availability_result.get(
                    "check_in"
                ),

            "check_out":
                availability_result.get(
                    "check_out"
                ),

            "total":
                availability_result.get(
                    "total",
                    len(enriched_hotels)
                ),

            "hotels":
                enriched_hotels

        })


    except Exception as e:

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 500


# ========================================
# HOTEL DESTINATION SEARCH
# ========================================

@app.route(
    "/api/hotel-destination"
)
def hotel_destination():

    destination = request.args.get(
        "destination",
        ""
    ).strip()

    if not destination:

        return jsonify({

            "success": False,

            "error": (
                "Destination is required"
            )

        }), 400

    result = search_hotel_destination(
        destination
    )

    return jsonify(result)


# ========================================
# API ERROR HANDLERS
# ========================================


@app.errorhandler(404)
def not_found(error):

    if request.path.startswith("/api/"):
        return jsonify({
            "status": "error",
            "message": "API endpoint not found.",
            "path": request.path
        }), 404

    return error


@app.errorhandler(405)
def method_not_allowed(error):

    if request.path.startswith("/api/"):
        return jsonify({
            "status": "error",
            "message": "HTTP method is not allowed for this endpoint.",
            "path": request.path
        }), 405

    return error


# ========================================
# START APPLICATION
# ========================================

if __name__ == "__main__":

    init_db()

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )